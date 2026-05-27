import subprocess
import asyncio
import re
import logging
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.models.project import Project
from app.models.sprint import Sprint
from app.models.sprint_task import SprintTask
from app.models.build_log import BuildLog

logger = logging.getLogger(__name__)

class BuildOrchestrator:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._is_running = False
        self._should_stop = False
    
    async def start_build(self, project_id: UUID, user_id: UUID) -> None:
        """
        Main entry point. Starts the build process.
        1. Fetch project, verify ownership and status
        2. Set project status to "building"
        3. Get all sprints with tasks ordered by sprint_number, task_number
        4. Find first pending/failed task (resume support)
        5. Start executing from that task
        """
        stmt = (
            select(Project)
            .where(Project.id == project_id, Project.user_id == user_id)
            .options(
                selectinload(Project.sprints).selectinload(Sprint.tasks)
            )
        )
        res = await self.db.execute(stmt)
        project = res.scalars().first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if project.status == "complete":
            await self.log(project_id, "INFO", "orchestrator", "Build is already complete.")
            return

        from app.services.project_dir_service import ProjectDirService
        if not project.project_dir:
            project.project_dir = ProjectDirService.create_project_dir(str(project.id), project.name)

        project.status = "building"
        await self.db.commit()
        await self.log(project_id, "INFO", "orchestrator", "Starting/resuming build process.")

        # Get all tasks in order
        all_tasks = []
        # Sort sprints by sprint_number
        sorted_sprints = sorted(project.sprints, key=lambda s: s.sprint_number)
        for sprint in sorted_sprints:
            sorted_tasks = sorted(sprint.tasks, key=lambda t: t.task_number)
            all_tasks.extend(sorted_tasks)

        # Find first task that is not passed
        task_to_start = None
        for task in all_tasks:
            if task.status != "passed":
                task_to_start = task
                break

        if not task_to_start:
            project.status = "complete"
            await self.db.commit()
            await self.log(project_id, "INFO", "orchestrator", "All tasks are already completed. Build finished.")
            return

        start_idx = all_tasks.index(task_to_start)
        self._is_running = True

        for task in all_tasks[start_idx:]:
            # Check for pause / cancel from outside (refresh project status from DB)
            await self.db.refresh(project)
            if project.status == "paused" or self._should_stop:
                await self.log(project_id, "INFO", "orchestrator", "Build paused.")
                break
            if project.status == "failed":
                await self.log(project_id, "INFO", "orchestrator", "Build stopped/cancelled.")
                break

            # Execute the task
            success = await self.execute_task(task, project.project_dir or "/tmp")
            if not success:
                await self.db.refresh(project)
                if project.status == "rate_limited":
                    await self.log(project_id, "WARNING", "orchestrator", f"Build rate limited. Will resume at {task.rate_limit_reset_at}")
                    
                    from app.services.cron_service import CronService
                    
                    async def resume_callback(pid):
                        from app.core.database import async_session
                        async with async_session() as db_session:
                            orch = BuildOrchestrator(db_session)
                            await orch.start_build(pid, user_id)

                    await CronService.schedule_resume(project.id, task.rate_limit_reset_at, resume_callback)
                else:
                    project.status = "failed"
                    await self.db.commit()
                    await self.log(project_id, "ERROR", "orchestrator", f"Task {task.name} failed. Stopping build.")
                break
        else:
            # Completed all tasks successfully
            project.status = "complete"
            await self.db.commit()
            await self.log(project_id, "INFO", "orchestrator", "Build pipeline completed successfully!")

        self._is_running = False

    async def execute_task(self, task: SprintTask, project_dir: str) -> bool:
        """
        Execute a single task
        """
        task.status = "running"
        task.started_at = datetime.utcnow()
        await self.db.commit()
        
        # Load sprint and project details for logging
        stmt_sprint = select(Sprint).where(Sprint.id == task.sprint_id)
        res_sprint = await self.db.execute(stmt_sprint)
        sprint = res_sprint.scalars().first()
        project_id = sprint.project_id if sprint else task.sprint_id # fallback

        await self.log(project_id, "INFO", "orchestrator", f"Starting task {task.task_number}: {task.name}")

        # Run Claude
        success, output, rate_limit_reset = self.run_claude(task.prompt, project_dir)
        task.claude_output = output

        if rate_limit_reset is not None:
            task.status = "rate_limited"
            task.rate_limit_reset_at = rate_limit_reset
            
            # Fetch project
            stmt_proj = select(Project).where(Project.id == project_id)
            res_proj = await self.db.execute(stmt_proj)
            project = res_proj.scalars().first()
            if project:
                project.status = "rate_limited"

            await self.db.commit()
            await self.log(project_id, "WARNING", "orchestrator", f"Rate limit encountered. Resets at {rate_limit_reset}")
            return False

        if not success:
            task.status = "failed"
            task.completed_at = datetime.utcnow()
            await self.db.commit()
            await self.log(project_id, "ERROR", "orchestrator", f"Claude failed to run for task: {task.name}")
            return False

        # Run tests if test command is specified
        passed, failed, test_output = 0, 0, ""
        if task.test_command:
            passed, failed, test_output = self.run_tests(task.test_command, project_dir)
            task.test_count = passed + failed
            task.tests_passed = passed
            task.tests_failed = failed
            task.error_output = test_output if failed > 0 else None

        if failed == 0:
            task.status = "passed"
            task.completed_at = datetime.utcnow()
            await self.db.commit()
            await self.log(project_id, "INFO", "orchestrator", f"Task {task.name} passed successfully. Tests: {passed} passed.")
            return True

        # Retry logic if tests failed
        if task.retry_count < 1:
            task.status = "retrying"
            task.retry_count += 1
            await self.db.commit()
            await self.log(project_id, "WARNING", "orchestrator", f"Tests failed. Retrying task {task.name} (Attempt 2)...")

            retry_prompt = self.build_retry_prompt(task.prompt, test_output)
            success, output, rate_limit_reset = self.run_claude(retry_prompt, project_dir)
            task.claude_output = (task.claude_output or "") + "\n\n=== RETRY OUTPUT ===\n\n" + output

            if rate_limit_reset is not None:
                task.status = "rate_limited"
                task.rate_limit_reset_at = rate_limit_reset
                
                stmt_proj = select(Project).where(Project.id == project_id)
                res_proj = await self.db.execute(stmt_proj)
                project = res_proj.scalars().first()
                if project:
                    project.status = "rate_limited"

                await self.db.commit()
                await self.log(project_id, "WARNING", "orchestrator", f"Rate limit encountered on retry. Resets at {rate_limit_reset}")
                return False

            if not success:
                task.status = "failed"
                task.completed_at = datetime.utcnow()
                await self.db.commit()
                await self.log(project_id, "ERROR", "orchestrator", f"Claude failed to run on retry for task: {task.name}")
                return False

            # Re-run tests
            passed, failed, test_output = self.run_tests(task.test_command, project_dir)
            task.test_count = passed + failed
            task.tests_passed = passed
            task.tests_failed = failed
            task.error_output = test_output if failed > 0 else None

            if failed == 0:
                task.status = "passed"
                task.completed_at = datetime.utcnow()
                await self.db.commit()
                await self.log(project_id, "INFO", "orchestrator", f"Task {task.name} passed after retry. Tests: {passed} passed.")
                return True

        # If it still fails, it is marked as failed
        task.status = "failed"
        task.completed_at = datetime.utcnow()
        await self.db.commit()
        await self.log(project_id, "ERROR", "orchestrator", f"Task {task.name} failed after retry. Tests: {failed} failed.")
        return False

    def run_claude(self, prompt: str, project_dir: str) -> tuple[bool, str, datetime | None]:
        """
        Run claude -p via ClaudeService.run_prompt.
        """
        import os
        from app.services.claude_service import ClaudeService
        os.makedirs(project_dir, exist_ok=True)
        result = ClaudeService.run_prompt(prompt, cwd=project_dir)
        return result["success"], result["output"], result["rate_limit_reset"]

    def run_tests(self, test_command: str, project_dir: str) -> tuple[int, int, str]:
        """
        Run test command as subprocess.
        """
        if not test_command:
            return 0, 0, ""
        
        try:
            result = subprocess.run(
                test_command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=project_dir,
                timeout=120
            )
            output = result.stdout + "\n" + result.stderr
        except Exception as e:
            output = f"Test command execution failed: {str(e)}"

        from app.services.claude_service import ClaudeOutputParser
        res = ClaudeOutputParser.parse_test_results(output)
        
        passed = res["passed"]
        failed = res["failed"]
        errors = res["errors"]
        
        if errors > 0:
            failed += errors
        if res["total"] == 0:
            failed += 1
            
        return passed, failed, output

    def build_retry_prompt(self, original_prompt: str, error_output: str) -> str:
        """
        Build retry prompt that includes original task context plus errors.
        """
        return f"""The previous code changes caused test failures. Fix the issues.

ORIGINAL TASK:
{original_prompt}

TEST FAILURES:
{error_output}

Fix the code so all tests pass. Do not modify the test files — fix the source code only."""

    def parse_rate_limit_reset(self, output: str) -> datetime | None:
        """
        Parse rate limit reset time.
        """
        # Look for "Resets in: X hours Y minutes"
        m1 = re.search(r"[Rr]esets?\s+in:?\s*(\d+)\s*hours?\s*(\d+)\s*minutes?", output)
        if m1:
            hours = int(m1.group(1))
            minutes = int(m1.group(2))
            return datetime.utcnow() + timedelta(hours=hours, minutes=minutes)
        
        # Look for "reset at TIME"
        m2 = re.search(r"reset\s+at\s+(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)", output)
        if m2:
            time_str = m2.group(1).strip()
            try:
                t = datetime.strptime(time_str, "%I:%M %p").time()
            except ValueError:
                try:
                    t = datetime.strptime(time_str, "%I:%M%p").time()
                except ValueError:
                    try:
                        t = datetime.strptime(time_str, "%H:%M").time()
                    except ValueError:
                        return datetime.utcnow() + timedelta(hours=1)
            
            now = datetime.utcnow()
            reset_dt = datetime.combine(now.date(), t)
            if reset_dt <= now:
                reset_dt += timedelta(days=1)
            return reset_dt

        # Check for generic limit messages
        if "usage limit reached" in output.lower() or "rate limit" in output.lower():
            return datetime.utcnow() + timedelta(hours=1)
        
        return None

    async def log(self, project_id: UUID, level: str, source: str, message: str):
        """Write a BuildLog entry to the database"""
        log_entry = BuildLog(
            project_id=project_id,
            level=level,
            source=source,
            message=message
        )
        self.db.add(log_entry)
        await self.db.commit()

    async def pause_build(self, project_id: UUID, user_id: UUID):
        self._should_stop = True
        stmt = select(Project).where(Project.id == project_id, Project.user_id == user_id)
        res = await self.db.execute(stmt)
        project = res.scalars().first()
        if project:
            project.status = "paused"
            await self.db.commit()
            await self.log(project_id, "INFO", "orchestrator", "Pause request received. Pausing build process.")

    async def cancel_build(self, project_id: UUID, user_id: UUID):
        self._should_stop = True
        stmt = select(Project).where(Project.id == project_id, Project.user_id == user_id)
        res = await self.db.execute(stmt)
        project = res.scalars().first()
        if project:
            project.status = "failed"
            await self.db.commit()
            await self.log(project_id, "INFO", "orchestrator", "Cancel request received. Cancelling build process.")
