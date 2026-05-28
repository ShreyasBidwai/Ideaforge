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
import os

logger = logging.getLogger(__name__)


class SprintGenerationService:
    def __init__(self, db: AsyncSession):
        self.db = db

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

        # 3. Dump docs to project directory and build the prompt pointing to files
        project_dir = self._dump_project_docs_to_disk(project)
        prompt = build_sprint_prompts_disk_prompt(context)

        # 4. Call ClaudeService.run_prompt() with this prompt and read permission in project directory
        result = await asyncio.to_thread(
            ClaudeService.run_prompt,
            prompt=prompt,
            cwd=project_dir,
            timeout=600,
            tools="Read",
            check_success=False
        )

        if not result["success"]:
            if result["is_rate_limited"]:
                reset_time = result["rate_limit_reset"]
                reset_str = reset_time.isoformat() if hasattr(reset_time, "isoformat") else str(reset_time)
                raise HTTPException(429, detail=f"Claude Code rate limited. Resets at: {reset_str}")
            raise HTTPException(500, detail=f"Sprint generation failed: {result['error']}")

        # 5. Parse JSON response into Sprint + SprintTask records
        sprint_data = self._parse_sprint_json(result["output"])

        # 6. Save to database
        await self._save_sprints(project_id, sprint_data)

        # 7. Update project status to "doc_review"
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

        # 2. Generating
        yield {"status": "generating", "message": "Claude Code is generating sprint breakdown... (this may take 2-5 minutes)"}
        project_dir = self._dump_project_docs_to_disk(project)
        prompt = build_sprint_prompts_disk_prompt(context)
        
        result = await asyncio.to_thread(
            ClaudeService.run_prompt,
            prompt=prompt,
            cwd=project_dir,
            timeout=600,
            tools="Read",
            check_success=False
        )

        if not result["success"]:
            if result["is_rate_limited"]:
                reset_time = result["rate_limit_reset"]
                reset_str = reset_time.isoformat() if hasattr(reset_time, "isoformat") else str(reset_time)
                raise HTTPException(429, detail=f"Claude Code rate limited. Resets at: {reset_str}")
            raise HTTPException(500, detail=f"Sprint generation failed: {result['error']}")

        # 3. Parsing
        yield {"status": "parsing", "message": "Parsing sprint structure..."}
        sprint_data = self._parse_sprint_json(result["output"])

        # 4. Validating
        yield {"status": "validating", "message": "Validating prompt quality..."}
        
        # 5. Saving (includes validation internally)
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

    def _parse_sprint_json(self, output: str) -> dict:
        """
        Parse JSON from Claude's output.
        Handle cases where Claude wraps JSON in markdown fences.
        """
        import json
        import re
        
        # Strip markdown code fences if present
        cleaned = output.strip()
        cleaned = re.sub(r'^```(?:json)?\s*\n?', '', cleaned)
        cleaned = re.sub(r'\n?```\s*$', '', cleaned)
        cleaned = cleaned.strip()
        
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            # Try to find JSON object in the output
            match = re.search(r'\{[\s\S]*\}', cleaned)
            if match:
                return json.loads(match.group())
            raise ValueError(f"Failed to parse sprint JSON from Claude output: {e}")

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
