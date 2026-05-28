import json
import logging
import re
import asyncio
from uuid import UUID
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.models.project import Project
from app.models.document import Document
from app.models.sprint import Sprint
from app.models.sprint_task import SprintTask
from app.models.solution import Solution
from app.models.problem_statement import ProblemStatement
from app.models.session import Session
from app.core.maturity import get_maturity_config, MaturityLevel
from app.services.claude_service import ClaudeService
from app.ai.prompts.docs.sprint_prompts import build_sprint_prompts_prompt, build_sprint_prompts_disk_prompt
from app.services.project_dir_service import ProjectDirService
from app.ai.provider import get_ai_provider, AIProvider
import os

logger = logging.getLogger(__name__)


ROADMAP_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "sprints": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "sprint_number": {"type": "INTEGER"},
                    "name": {"type": "STRING"},
                    "description": {"type": "STRING"},
                    "tasks": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "task_number": {"type": "INTEGER"},
                                "name": {"type": "STRING"},
                                "description": {"type": "STRING"}
                            },
                            "required": ["task_number", "name", "description"]
                        }
                    }
                },
                "required": ["sprint_number", "name", "description", "tasks"]
            }
        },
        "total_tasks": {"type": "INTEGER"},
        "total_sprints": {"type": "INTEGER"}
    },
    "required": ["sprints", "total_tasks", "total_sprints"]
}

TASK_DETAIL_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "prompt": {"type": "STRING"},
        "test_command": {"type": "STRING"},
        "expected_test_count": {"type": "INTEGER"}
    },
    "required": ["prompt", "test_command", "expected_test_count"]
}

SPRINT_SCHEMA = ROADMAP_SCHEMA


class SprintGenerationService:
    active_tasks = {}

    @classmethod
    def cancel_generation(cls, project_id: str) -> bool:
        task = cls.active_tasks.get(project_id)
        if task:
            logger.info(f"Cancelling active sprint generation task for project {project_id}")
            task.cancel()
        
        from app.services.claude_service import ClaudeService
        ClaudeService.terminate_process(project_id)
        return task is not None

    def __init__(self, db: AsyncSession | None = None, ai_provider: AIProvider | None = None):
        self.db = db
        self.ai = ai_provider or get_ai_provider()

    def _dump_project_docs_to_disk(self, project: Project) -> str:
        project_dir = ProjectDirService.get_project_dir(str(project.id), project.name)
        docs_dir = os.path.join(project_dir, "docs")
        os.makedirs(docs_dir, exist_ok=True)
        
        for doc in project.documents:
            filename = f"{doc.doc_type}.md"
            filepath = os.path.join(docs_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(doc.content)
                
        return project_dir

    async def _get_project_with_relations(self, project_id: UUID, user_id: UUID) -> Project:
        stmt = (
            select(Project)
            .where(Project.id == project_id, Project.user_id == user_id)
            .options(
                selectinload(Project.documents),
                selectinload(Project.solution).selectinload(Solution.problem_statement).selectinload(ProblemStatement.session),
                selectinload(Project.solution).selectinload(Solution.evaluation)
            )
        )
        res = await self.db.execute(stmt)
        project = res.scalars().first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project

    def _build_roadmap_prompt(self, project: Project, context: dict) -> str:
        # Pre-load documents from project.documents
        docs_context = ""
        for doc in project.documents:
            docs_context += f'\n<file path="docs/{doc.doc_type}.md">\n{doc.content}\n</file>\n'

        tech_stack_str = ', '.join(context['solution']['tech_stack']) if isinstance(context['solution']['tech_stack'], list) else str(context['solution']['tech_stack'])
        
        prompt = f"""You are an expert software architect generating a high-level sprint and task breakdown for an application.

Here are the project specification documents:
{docs_context}

PROJECT CONTEXT:
- Name: {context['solution']['title']}
- Industry: {context['session']['industry']}
- Location: {context['session'].get('location', 'Not available')}
- Maturity Level: {context['session']['maturity_level']}
- Tech Stack: {tech_stack_str}

OUTPUT FORMAT: Return ONLY valid JSON matching the requested schema. No markdown code fences, no explanation.

CRITICAL RULES FOR ROADMAP:
1. Generate 2-4 sprints with 2-4 tasks each based on the provided documents.
2. Sprints and tasks must be ordered logically, such that early tasks lay the foundation for subsequent tasks.
3. Sprint 1, Task 1 MUST ALWAYS be project scaffolding: setting up folders, package configurations, base entry files, and a hello world health check endpoint.
4. Each task should have a clear name and a concise description of what needs to be implemented.
"""
        return prompt

    def _build_task_detail_prompt(self, project: Project, context: dict, roadmap_structure: dict, sprint_num: int, task_num: int, task_name: str, task_desc: str) -> str:
        # Pre-load documents from project.documents
        docs_context = ""
        for doc in project.documents:
            docs_context += f'\n<file path="docs/{doc.doc_type}.md">\n{doc.content}\n</file>\n'

        tech_stack_str = ', '.join(context['solution']['tech_stack']) if isinstance(context['solution']['tech_stack'], list) else str(context['solution']['tech_stack'])
        
        # Build a list of preceding tasks so the model knows the chronological context of files already created/modified
        preceding_tasks = []
        for sprint in roadmap_structure.get("sprints", []):
            for task in sprint.get("tasks", []):
                if (sprint["sprint_number"] < sprint_num) or (sprint["sprint_number"] == sprint_num and task["task_number"] < task_num):
                    preceding_tasks.append(f"Sprint {sprint['sprint_number']} Task {task['task_number']}: {task['name']} - {task.get('description', '')}")

        preceding_tasks_str = "\n".join(preceding_tasks) if preceding_tasks else "None (This is the first task. The directory is completely empty)."

        prompt = f"""You are an expert software architect writing a highly detailed, self-contained coding instruction prompt for a task to be executed by an AI coding agent.

Here are the project specification documents:
{docs_context}

PROJECT CONTEXT:
- Name: {context['solution']['title']}
- Tech Stack: {tech_stack_str}

CHRONOLOGICAL ROADMAP CONTEXT:
We are generating the detailed coding prompt for:
- Current Sprint: {sprint_num}
- Current Task Number: {task_num}
- Current Task Name: {task_name}
- Current Task Description: {task_desc}

PRECEDING TASKS (Chronologically implemented before this task):
{preceding_tasks_str}

OUTPUT FORMAT: Return ONLY valid JSON matching the requested schema. No markdown code fences, no explanation.

CRITICAL RULES FOR THE CODING INSTRUCTION PROMPT:
1. The prompt must be COMPLETELY SELF-CONTAINED. The AI agent executing it has ZERO memory of previous tasks. It can only read the codebase files that exist on disk (which were created/modified by the PRECEDING TASKS listed above).
2. The prompt must specify EXACT file paths to create or modify (e.g. `backend/app/api/v1/users.py`, `frontend/src/components/UserList.tsx`).
3. The prompt must include complete code specifications (e.g. exact endpoint paths, parameters, schemas, model fields) and step-by-step instructions.
4. The prompt must include complete test cases with exact test file paths and test run commands (e.g. pytest, vitest).
5. If this is Sprint 1 Task 1, it must instruct the agent to bootstrap/scaffold the entire directory structure, package configuration files (e.g. package.json, requirements.txt, tsconfig.json), and set up a hello world health check endpoint with a passing test.
6. The test command must be specific and executable (e.g., "cd backend && python -m pytest tests/test_health.py -v").
7. Ensure the prompt word count is detailed (around 150-250 words) to ensure the coding agent has all the details needed to write correct code.
8. IMPORTANT: If using Fastify for the Node.js/TypeScript backend, ensure that any generated tests include `beforeAll(async () => {{ await app.ready(); }});` before making requests using supertest. Fastify plugin registration is asynchronous; making requests before the application is fully ready causes Jest to hang indefinitely due to unclosed active handles.
9. IMPORTANT: If using Gradle/Kotlin for the Android SDK, ensure that any build.gradle.kts files include explicit versions for external plugins in the `plugins` block (e.g. `id("com.android.library") version "8.5.1"` and `id("org.jetbrains.kotlin.android") version "1.9.22"`). Also, if executing gradle commands from a subdirectory, use `../gradlew` rather than `./gradlew` to correctly reference the wrapper in the project root.
"""
        return prompt

    def _build_prompt_with_docs(self, project: Project, context: dict) -> str:
        # Keep this wrapper method for backward compatibility in any direct tests
        return self._build_roadmap_prompt(project, context)

    async def _save_sprints(self, project_id: UUID, data: dict) -> list[Sprint]:
        # Clear existing sprints and tasks to allow regeneration
        stmt_existing_sprints = select(Sprint).where(Sprint.project_id == project_id)
        res_existing_sprints = await self.db.execute(stmt_existing_sprints)
        existing_sprints = res_existing_sprints.scalars().all()
        for s in existing_sprints:
            await self.db.delete(s)

        created_sprints = []
        for sprint_data in data.get("sprints", []):
            sprint = Sprint(
                project_id=project_id,
                sprint_number=sprint_data["sprint_number"],
                name=sprint_data["name"],
                description=sprint_data.get("description"),
                status="pending"
            )
            self.db.add(sprint)
            await self.db.flush()

            for task_data in sprint_data.get("tasks", []):
                from app.services.prompt_validator import PromptValidator
                val_res = PromptValidator.validate_prompt(task_data["prompt"])
                
                task = SprintTask(
                    sprint_id=sprint.id,
                    task_number=task_data["task_number"],
                    name=task_data["name"],
                    prompt=task_data["prompt"],
                    status="pending",
                    test_command=task_data.get("test_command"),
                    test_count=task_data.get("expected_test_count") or 0,
                    tests_passed=0,
                    tests_failed=0,
                    retry_count=0,
                    validation_results=val_res
                )
                self.db.add(task)
            
            created_sprints.append(sprint)

        return created_sprints

    async def generate_sprints(self, project_id: UUID, user_id: UUID) -> list[Sprint]:
        # 1. Fetch project with solution, problem, evaluation, session data
        project = await self._get_project_with_relations(project_id, user_id)
        
        # 2. Build context
        solution = project.solution
        problem = solution.problem_statement
        session = problem.session

        try:
            mat_level = MaturityLevel(project.maturity_level)
        except ValueError:
            mat_level = MaturityLevel.MVP
        
        maturity_config = get_maturity_config(mat_level)

        context = {
            "solution": {
                "title": solution.title,
                "description": solution.description,
                "mechanism": solution.mechanism,
                "tech_stack": solution.tech_stack or [],
                "target_user": solution.target_user,
                "revenue_model": solution.revenue_model
            },
            "problem": {
                "title": problem.title,
                "description": problem.description,
                "target_user": problem.target_user,
                "core_pain": problem.core_pain,
                "market_context": problem.market_context
            },
            "session": {
                "industry": session.industry,
                "location": session.location,
                "maturity_level": session.maturity_level,
                "tech_stack_preferences": session.tech_stack_preferences or []
            },
            "maturity_config": maturity_config.model_dump() if hasattr(maturity_config, "model_dump") else maturity_config.dict()
        }

        # 3. Dump docs to project directory and build the roadmap prompt pointing to files
        self._dump_project_docs_to_disk(project)
        roadmap_prompt = self._build_roadmap_prompt(project, context)

        current_task = asyncio.current_task()
        SprintGenerationService.active_tasks[str(project_id)] = current_task

        try:
            # 4. Call Gemini Provider to generate the high-level roadmap structure
            system_prompt = "You are an expert software architect. Output ONLY valid JSON matching the roadmap schema."
            roadmap_response = await self.ai.generate(
                prompt=roadmap_prompt,
                system_prompt=system_prompt,
                response_schema=ROADMAP_SCHEMA
            )

            # 5. Parse roadmap JSON response
            roadmap_data = self._parse_sprint_json(roadmap_response)

            # 6. Detailed Task Generation: Call Gemini for each task to generate prompts, test commands, expected counts
            sprint_data = {
                "sprints": [],
                "total_tasks": roadmap_data.get("total_tasks", 0),
                "total_sprints": roadmap_data.get("total_sprints", 0),
                "estimated_total_tests": 0
            }

            estimated_total_tests = 0
            for sprint in roadmap_data.get("sprints", []):
                new_sprint = {
                    "sprint_number": sprint["sprint_number"],
                    "name": sprint["name"],
                    "description": sprint.get("description"),
                    "tasks": []
                }
                for task in sprint.get("tasks", []):
                    task_detail_prompt = self._build_task_detail_prompt(
                        project, context, roadmap_data,
                        sprint["sprint_number"], task["task_number"],
                        task["name"], task.get("description", "")
                    )
                    # Throttle requests to stay well within free tier RPM limits
                    await asyncio.sleep(2.0)
                    task_detail_response = await self.ai.generate(
                        prompt=task_detail_prompt,
                        system_prompt="You are an expert software architect. Output ONLY valid JSON matching the task detail schema.",
                        response_schema=TASK_DETAIL_SCHEMA
                    )
                    task_detail_data = self._parse_sprint_json(task_detail_response)
                    
                    prompt_val = task_detail_data.get("prompt")
                    test_command_val = task_detail_data.get("test_command")
                    expected_test_count_val = task_detail_data.get("expected_test_count") or 0
                    
                    if not prompt_val and "sprints" in task_detail_data:
                        for s_data in task_detail_data.get("sprints", []):
                            if s_data.get("sprint_number") == sprint["sprint_number"]:
                                for t_data in s_data.get("tasks", []):
                                    if t_data.get("task_number") == task["task_number"]:
                                        prompt_val = t_data.get("prompt")
                                        test_command_val = t_data.get("test_command")
                                        expected_test_count_val = t_data.get("expected_test_count") or 0
                                        break
                                break
                    
                    if not prompt_val:
                        prompt_val = "Default task instruction prompt detailing files and test command."
                    
                    new_task = {
                        "task_number": task["task_number"],
                        "name": task["name"],
                        "prompt": prompt_val,
                        "test_command": test_command_val,
                        "expected_test_count": expected_test_count_val
                    }
                    new_sprint["tasks"].append(new_task)
                    estimated_total_tests += new_task["expected_test_count"]
                
                sprint_data["sprints"].append(new_sprint)
            
            sprint_data["estimated_total_tests"] = estimated_total_tests

            # 7. Save to database
            await self._save_sprints(project_id, sprint_data)

            # 8. Update project status to "doc_review"
            project.status = "doc_review"
            await self.db.commit()
        except asyncio.CancelledError:
            logger.info(f"Sprint generation cancelled for project {project_id}")
            raise
        except Exception as e:
            logger.error(f"Sprint generation failed: {e}")
            if "exhausted" in str(e).lower() or "rate limit" in str(e).lower() or "quota" in str(e).lower():
                raise HTTPException(429, detail=f"Sprint generation rate limited: {str(e)}")
            raise HTTPException(500, detail=f"Sprint generation failed: {str(e)}")
        finally:
            SprintGenerationService.active_tasks.pop(str(project_id), None)

        # Reload sprints with tasks to return full objects
        stmt_reload = (
            select(Sprint)
            .where(Sprint.project_id == project.id)
            .options(selectinload(Sprint.tasks))
            .order_by(Sprint.sprint_number.asc())
        )
        res_reload = await self.db.execute(stmt_reload)
        return res_reload.scalars().all()

    async def generate_sprints_stream(self, project_id: UUID, user_id: UUID):
        current_task = asyncio.current_task()
        SprintGenerationService.active_tasks[str(project_id)] = current_task

        try:
            # 1. Preparing
            yield {"status": "preparing", "message": "Gathering project documents..."}
            project = await self._get_project_with_relations(project_id, user_id)
            
            solution = project.solution
            problem = solution.problem_statement
            session = problem.session

            try:
                mat_level = MaturityLevel(project.maturity_level)
            except ValueError:
                mat_level = MaturityLevel.MVP
            
            maturity_config = get_maturity_config(mat_level)

            context = {
                "solution": {
                    "title": solution.title,
                    "description": solution.description,
                    "mechanism": solution.mechanism,
                    "tech_stack": solution.tech_stack or [],
                    "target_user": solution.target_user,
                    "revenue_model": solution.revenue_model
                },
                "problem": {
                    "title": problem.title,
                    "description": problem.description,
                    "target_user": problem.target_user,
                    "core_pain": problem.core_pain,
                    "market_context": problem.market_context
                },
                "session": {
                    "industry": session.industry,
                    "location": session.location,
                    "maturity_level": session.maturity_level,
                    "tech_stack_preferences": session.tech_stack_preferences or []
                },
                "maturity_config": maturity_config.model_dump() if hasattr(maturity_config, "model_dump") else maturity_config.dict()
            }

            # 2. Generating Roadmap
            yield {"status": "generating_roadmap", "message": "Gemini AI is generating the high-level roadmap..."}
            self._dump_project_docs_to_disk(project)
            roadmap_prompt = self._build_roadmap_prompt(project, context)
            
            system_prompt = "You are an expert software architect. Output ONLY valid JSON matching the roadmap schema."
            roadmap_response = await self.ai.generate(
                prompt=roadmap_prompt,
                system_prompt=system_prompt,
                response_schema=ROADMAP_SCHEMA
            )

            roadmap_data = self._parse_sprint_json(roadmap_response)

            # 3. Generating Task Details
            sprint_data = {
                "sprints": [],
                "total_tasks": roadmap_data.get("total_tasks", 0),
                "total_sprints": roadmap_data.get("total_sprints", 0),
                "estimated_total_tests": 0
            }

            total_tasks_count = sum(len(s.get("tasks", [])) for s in roadmap_data.get("sprints", []))
            current_task_idx = 0

            estimated_total_tests = 0
            for sprint in roadmap_data.get("sprints", []):
                new_sprint = {
                    "sprint_number": sprint["sprint_number"],
                    "name": sprint["name"],
                    "description": sprint.get("description"),
                    "tasks": []
                }
                for task in sprint.get("tasks", []):
                    current_task_idx += 1
                    yield {
                        "status": "generating_tasks", 
                        "message": f"Gemini AI is detailing task {current_task_idx} of {total_tasks_count}: {task['name']}..."
                    }
                    
                    task_detail_prompt = self._build_task_detail_prompt(
                        project, context, roadmap_data,
                        sprint["sprint_number"], task["task_number"],
                        task["name"], task.get("description", "")
                    )
                    # Throttle requests to stay well within free tier RPM limits
                    await asyncio.sleep(2.0)
                    task_detail_response = await self.ai.generate(
                        prompt=task_detail_prompt,
                        system_prompt="You are an expert software architect. Output ONLY valid JSON matching the task detail schema.",
                        response_schema=TASK_DETAIL_SCHEMA
                    )
                    task_detail_data = self._parse_sprint_json(task_detail_response)
                    
                    prompt_val = task_detail_data.get("prompt")
                    test_command_val = task_detail_data.get("test_command")
                    expected_test_count_val = task_detail_data.get("expected_test_count") or 0
                    
                    if not prompt_val and "sprints" in task_detail_data:
                        for s_data in task_detail_data.get("sprints", []):
                            if s_data.get("sprint_number") == sprint["sprint_number"]:
                                for t_data in s_data.get("tasks", []):
                                    if t_data.get("task_number") == task["task_number"]:
                                        prompt_val = t_data.get("prompt")
                                        test_command_val = t_data.get("test_command")
                                        expected_test_count_val = t_data.get("expected_test_count") or 0
                                        break
                                break
                    
                    if not prompt_val:
                        prompt_val = "Default task instruction prompt detailing files and test command."
                    
                    new_task = {
                        "task_number": task["task_number"],
                        "name": task["name"],
                        "prompt": prompt_val,
                        "test_command": test_command_val,
                        "expected_test_count": expected_test_count_val
                    }
                    new_sprint["tasks"].append(new_task)
                    estimated_total_tests += new_task["expected_test_count"]
                
                sprint_data["sprints"].append(new_sprint)
            
            sprint_data["estimated_total_tests"] = estimated_total_tests

            # 4. Saving
            yield {"status": "saving", "message": "Saving sprints and tasks to the database..."}
            await self._save_sprints(project_id, sprint_data)
            
            project.status = "doc_review"
            await self.db.commit()

            sprint_count = len(sprint_data.get("sprints", []))
            task_count = sum(len(s.get("tasks", [])) for s in sprint_data.get("sprints", []))

            yield {
                "status": "complete",
                "message": f"Generated {sprint_count} sprints with {task_count} tasks",
                "sprint_count": sprint_count,
                "task_count": task_count
            }
        except asyncio.CancelledError:
            logger.info(f"Sprint generation stream cancelled for project {project_id}")
            raise
        except Exception as e:
            logger.error(f"Sprint generation failed in stream: {e}")
            if "exhausted" in str(e).lower() or "rate limit" in str(e).lower() or "quota" in str(e).lower():
                raise HTTPException(429, detail=f"Sprint generation rate limited: {str(e)}")
            raise HTTPException(500, detail=f"Sprint generation failed: {str(e)}")
        finally:
            SprintGenerationService.active_tasks.pop(str(project_id), None)

    def _parse_sprint_json(self, output: str) -> dict:
        """
        Parse JSON from Gemini's/Claude's output.
        Handle cases where they wrap JSON in markdown fences or include raw control characters.
        """
        import json
        import re
        
        # Strip markdown code fences if present
        cleaned = output.strip()
        cleaned = re.sub(r'^```(?:json)?\s*\n?', '', cleaned)
        cleaned = re.sub(r'\n?```\s*$', '', cleaned)
        cleaned = cleaned.strip()
        
        # Helper to escape unescaped control characters inside JSON string literals
        def escape_raw_control_chars(s: str) -> str:
            result = []
            in_string = False
            escaped = False
            for char in s:
                if char == '"' and not escaped:
                    in_string = not in_string
                    result.append(char)
                elif char == '\\' and in_string:
                    escaped = not escaped
                    result.append(char)
                else:
                    if in_string:
                        if char == '\n':
                            result.append('\\n')
                        elif char == '\r':
                            result.append('\\r')
                        elif char == '\t':
                            result.append('\\t')
                        else:
                            result.append(char)
                    else:
                        result.append(char)
                    escaped = False
            return "".join(result)

        cleaned = escape_raw_control_chars(cleaned)

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            # Try to find JSON object in the output
            match = re.search(r'\{[\s\S]*\}', cleaned)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError as inner_e:
                    raise ValueError(f"Failed to parse sprint JSON: {inner_e}. Cleaned output: {cleaned[:200]}...")
            raise ValueError(f"Failed to parse sprint JSON from Claude/Gemini output: {e}")

    async def get_sprints(self, project_id: UUID, user_id: UUID) -> list[Sprint]:
        """Get all sprints with tasks for a project"""
        # First verify project belongs to user
        stmt_proj = select(Project).where(Project.id == project_id, Project.user_id == user_id)
        proj_res = await self.db.execute(stmt_proj)
        if not proj_res.scalars().first():
            raise HTTPException(status_code=404, detail="Project not found")

        stmt = (
            select(Sprint)
            .where(Sprint.project_id == project_id)
            .options(selectinload(Sprint.tasks))
            .order_by(Sprint.sprint_number.asc())
        )
        res = await self.db.execute(stmt)
        return res.scalars().all()

    async def get_task(self, task_id: UUID, user_id: UUID) -> SprintTask:
        """Get a single task with its prompt"""
        stmt = (
            select(SprintTask)
            .join(Sprint, SprintTask.sprint_id == Sprint.id)
            .join(Project, Sprint.project_id == Project.id)
            .where(SprintTask.id == task_id, Project.user_id == user_id)
        )
        res = await self.db.execute(stmt)
        task = res.scalars().first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task
