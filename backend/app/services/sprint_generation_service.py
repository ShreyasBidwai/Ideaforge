import json
import logging
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
from app.ai.provider import AIProvider
from app.ai.prompts.docs.sprint_prompts import build_sprint_prompts_prompt

logger = logging.getLogger(__name__)

class SprintGenerationService:
    def __init__(self, ai_provider: AIProvider, db: AsyncSession):
        self.ai = ai_provider
        self.db = db

    async def generate_sprints(self, project_id: UUID, user_id: UUID) -> list[Sprint]:
        """
        1. Fetch project and its generated documents
        2. Build context with solution, problem, session data
        3. Call Gemini AI with all docs as context
        4. Parse sprint + task structure from JSON response
        5. Create Sprint records with SprintTask children
        6. Each SprintTask stores the full prompt text
        7. Update project status to "doc_review"
        8. Return created sprints
        """
        # Fetch project with documents, solution, problem statement, session, evaluation
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

        # Find specific documents
        arch_doc = ""
        prd_doc = ""
        trd_doc = ""
        for doc in project.documents:
            if doc.doc_type == "architecture":
                arch_doc = doc.content
            elif doc.doc_type == "prd":
                prd_doc = doc.content
            elif doc.doc_type == "trd":
                trd_doc = doc.content

        # Build context
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

        # Build prompt
        system_prompt, user_prompt = build_sprint_prompts_prompt(context, arch_doc, prd_doc, trd_doc)

        # Call Gemini AI
        response_text = await self.ai.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            response_schema={
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
                                            "prompt": {"type": "STRING"},
                                            "test_command": {"type": "STRING"},
                                            "expected_test_count": {"type": "INTEGER"},
                                            "estimated_tokens": {"type": "INTEGER"}
                                        },
                                        "required": ["task_number", "name", "prompt", "test_command"]
                                    }
                                }
                            },
                            "required": ["sprint_number", "name", "tasks"]
                        }
                    },
                    "total_tasks": {"type": "INTEGER"},
                    "total_sprints": {"type": "INTEGER"},
                    "estimated_total_tests": {"type": "INTEGER"}
                },
                "required": ["sprints"]
            }
        )

        try:
            data = json.loads(response_text)
        except Exception as e:
            logger.error(f"Failed to parse JSON response from Gemini: {response_text}")
            raise HTTPException(status_code=500, detail="Failed to parse sprint breakdown JSON response from Gemini.")

        # Clear existing sprints and tasks to allow regeneration
        stmt_existing_sprints = select(Sprint).where(Sprint.project_id == project.id)
        res_existing_sprints = await self.db.execute(stmt_existing_sprints)
        existing_sprints = res_existing_sprints.scalars().all()
        for s in existing_sprints:
            await self.db.delete(s)

        created_sprints = []
        for sprint_data in data.get("sprints", []):
            sprint = Sprint(
                project_id=project.id,
                sprint_number=sprint_data["sprint_number"],
                name=sprint_data["name"],
                description=sprint_data.get("description"),
                status="pending"
            )
            self.db.add(sprint)
            # Flush so we get sprint.id
            await self.db.flush()

            for task_data in sprint_data.get("tasks", []):
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
                    retry_count=0
                )
                self.db.add(task)
            
            created_sprints.append(sprint)

        project.status = "doc_review"
        await self.db.commit()

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
        yield {"status": "analyzing", "message": "Analyzing documentation..."}
        
        # Fetch project with documents, solution, problem statement, session, evaluation
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

        yield {"status": "generating", "message": "Generating sprint breakdown and task prompts..."}

        # Find specific documents
        arch_doc = ""
        prd_doc = ""
        trd_doc = ""
        for doc in project.documents:
            if doc.doc_type == "architecture":
                arch_doc = doc.content
            elif doc.doc_type == "prd":
                prd_doc = doc.content
            elif doc.doc_type == "trd":
                trd_doc = doc.content

        # Build context
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

        # Build prompt
        system_prompt, user_prompt = build_sprint_prompts_prompt(context, arch_doc, prd_doc, trd_doc)

        # Call Gemini AI
        response_text = await self.ai.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            response_schema={
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
                                            "prompt": {"type": "STRING"},
                                            "test_command": {"type": "STRING"},
                                            "expected_test_count": {"type": "INTEGER"},
                                            "estimated_tokens": {"type": "INTEGER"}
                                        },
                                        "required": ["task_number", "name", "prompt", "test_command"]
                                    }
                                }
                            },
                            "required": ["sprint_number", "name", "tasks"]
                        }
                    },
                    "total_tasks": {"type": "INTEGER"},
                    "total_sprints": {"type": "INTEGER"},
                    "estimated_total_tests": {"type": "INTEGER"}
                },
                "required": ["sprints"]
            }
        )

        try:
            data = json.loads(response_text)
        except Exception as e:
            logger.error(f"Failed to parse JSON response from Gemini: {response_text}")
            raise HTTPException(status_code=500, detail="Failed to parse sprint breakdown JSON response from Gemini.")

        # Clear existing sprints and tasks to allow regeneration
        stmt_existing_sprints = select(Sprint).where(Sprint.project_id == project.id)
        res_existing_sprints = await self.db.execute(stmt_existing_sprints)
        existing_sprints = res_existing_sprints.scalars().all()
        for s in existing_sprints:
            await self.db.delete(s)

        sprint_count = 0
        task_count = 0
        for sprint_data in data.get("sprints", []):
            sprint_count += 1
            sprint = Sprint(
                project_id=project.id,
                sprint_number=sprint_data["sprint_number"],
                name=sprint_data["name"],
                description=sprint_data.get("description"),
                status="pending"
            )
            self.db.add(sprint)
            await self.db.flush()

            for task_data in sprint_data.get("tasks", []):
                task_count += 1
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
                    retry_count=0
                )
                self.db.add(task)

        project.status = "doc_review"
        await self.db.commit()

        yield {
            "status": "complete",
            "message": f"Generated {sprint_count} sprints with {task_count} tasks",
            "sprint_count": sprint_count,
            "task_count": task_count
        }

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
