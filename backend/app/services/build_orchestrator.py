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
    MAX_RETRIES = 2  # increased from 1

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
        return await self.execute_task_with_recovery(task, project_dir)

    async def execute_task_with_recovery(self, task: SprintTask, project_dir: str) -> bool:
        """
        Enhanced task execution with multi-level recovery:
        
        Level 1: Direct retry with error context (existing)
        Level 2: Dependency fix — if error contains "ModuleNotFoundError" or "Cannot find module",
                 run a dependency installation prompt first, then retry original
        Level 3: Clean retry — if Level 1 and 2 fail, ask Claude to read the existing code
                 and rewrite the failing parts from scratch
        
        Between retries, always re-run the FULL test suite for the task (not just failed tests).
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

        # Run Claude (Attempt 1)
        success, output, rate_limit_reset = self.run_claude(task.prompt, project_dir)
        task.claude_output = output

        if rate_limit_reset is not None:
            task.status = "rate_limited"
            task.rate_limit_reset_at = rate_limit_reset
            stmt_proj = select(Project).where(Project.id == project_id)
            res_proj = await self.db.execute(stmt_proj)
            project = res_proj.scalars().first()
            if project:
                project.status = "rate_limited"
            await self.db.commit()
            await self.log(project_id, "WARNING", "orchestrator", f"Rate limit encountered. Resets at {rate_limit_reset}")
            return False

        if not success:
            await self.handle_task_failure(task, project_id)
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

        # Recovery levels
        while task.retry_count < self.MAX_RETRIES:
            task.status = "retrying"
            task.retry_count += 1
            await self.db.commit()
            await self.log(project_id, "WARNING", "orchestrator", f"Tests failed. Retrying task {task.name} (Attempt {task.retry_count + 1})...")

            # Determine Level
            if task.retry_count == 1:
                # Level 1 or Level 2
                is_dep_error = any(key in (task.error_output or "") for key in ["ModuleNotFoundError", "Cannot find module", "ImportError", "Could not resolve dependency", "npm ERR!"])
                if is_dep_error:
                    # Level 2: Dependency fix first
                    dep_prompt = self.build_dependency_fix_prompt(task.error_output or "", project_dir)
                    await self.log(project_id, "INFO", "orchestrator", "Dependency/Import error detected. Running dependency fix prompt first...")
                    success_dep, output_dep, rate_limit_dep = self.run_claude(dep_prompt, project_dir)
                    task.claude_output = (task.claude_output or "") + "\n\n=== DEPENDENCY FIX OUTPUT ===\n\n" + output_dep
                    if rate_limit_dep is not None:
                        task.status = "rate_limited"
                        task.rate_limit_reset_at = rate_limit_dep
                        stmt_proj = select(Project).where(Project.id == project_id)
                        res_proj = await self.db.execute(stmt_proj)
                        project = res_proj.scalars().first()
                        if project:
                            project.status = "rate_limited"
                        await self.db.commit()
                        return False
                    
                    # Now retry the original task prompt (Standard retry format)
                    retry_prompt = self.build_retry_prompt(task.prompt, task.error_output or "")
                    success, output, rate_limit_reset = self.run_claude(retry_prompt, project_dir)
                else:
                    # Level 1: Direct retry with error context
                    retry_prompt = self.build_retry_prompt(task.prompt, task.error_output or "")
                    success, output, rate_limit_reset = self.run_claude(retry_prompt, project_dir)
            else:
                # Level 3: Clean retry with existing files context
                existing_files = []
                import os
                if os.path.exists(project_dir):
                    for root, dirs, files in os.walk(project_dir):
                        dirs[:] = [d for d in dirs if d not in [".git", "node_modules", "__pycache__", ".venv", "venv", ".pytest_cache"]]
                        for file in files:
                            rel_path = os.path.relpath(os.path.join(root, file), project_dir)
                            existing_files.append(rel_path)
                
                clean_prompt = self.build_clean_retry_prompt(task.prompt, task.error_output or "", existing_files)
                await self.log(project_id, "INFO", "orchestrator", "Level 3 Clean Retry: Instructing model to rewrite failing parts...")
                success, output, rate_limit_reset = self.run_claude(clean_prompt, project_dir)

            task.claude_output = (task.claude_output or "") + f"\n\n=== RETRY {task.retry_count} OUTPUT ===\n\n" + output

            if rate_limit_reset is not None:
                task.status = "rate_limited"
                task.rate_limit_reset_at = rate_limit_reset
                stmt_proj = select(Project).where(Project.id == project_id)
                res_proj = await self.db.execute(stmt_proj)
                project = res_proj.scalars().first()
                if project:
                    project.status = "rate_limited"
                await self.db.commit()
                return False

            if not success:
                await self.handle_task_failure(task, project_id)
                return False

            # Re-run full test suite
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

        # Fails all retry attempts
        await self.handle_task_failure(task, project_id)
        return False

    def build_dependency_fix_prompt(self, error_output: str, project_dir: str) -> str:
        """
        Build a prompt specifically for fixing dependency/import issues.
        """
        return f"The following import/dependency errors occurred. Install missing packages and fix import paths: {error_output}"

    def build_clean_retry_prompt(self, original_prompt: str, error_output: str, existing_files: list[str]) -> str:
        """
        Build a fresh attempt prompt that acknowledges existing code.
        """
        files_str = ", ".join(existing_files)
        return f"""Read the existing files in the project. The following task partially completed but has errors. Fix or rewrite as needed: {original_prompt}
         
Current errors: {error_output}
Existing files that may be relevant: {files_str}"""

    async def handle_task_failure(self, task: SprintTask, project_id: UUID):
        """
        Called when a task fails all retry attempts.
        """
        task.status = "failed"
        task.completed_at = datetime.utcnow()
        stmt = select(Project).where(Project.id == project_id)
        res = await self.db.execute(stmt)
        project = res.scalars().first()
        if project:
            project.status = "failed"
        await self.db.commit()
        await self.log(project_id, "ERROR", "orchestrator", f"Task {task.name} failed after all recovery attempts.")

    async def resume_from_failure(self, project_id: UUID, user_id: UUID):
        """
        Resume a failed build from the failed task.
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

        failed_task = None
        for sprint in project.sprints:
            for task in sprint.tasks:
                if task.status == "failed":
                    failed_task = task
                    break
            if failed_task:
                break

        if not failed_task:
            raise HTTPException(status_code=400, detail="No failed task to retry")

        failed_task.status = "pending"
        failed_task.retry_count = 0
        failed_task.error_output = None
        project.status = "building"
        await self.db.commit()

        from app.core.database import async_session
        async def run_in_background():
            async with async_session() as background_db:
                orch = BuildOrchestrator(background_db)
                await orch.start_build(project_id, user_id)

        asyncio.create_task(run_in_background())

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
