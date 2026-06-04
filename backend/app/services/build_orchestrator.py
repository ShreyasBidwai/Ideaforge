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

# Map BuildLog level strings (incl. custom ones like PROMPT/CLAUDE/TESTS) to
# Python logging levels so build activity can be mirrored into complete.log.
_PY_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

# Task states that mean a task is still queued or actively being worked on.
# If ANY task in a project is in one of these states, the build is not finished.
ACTIVE_TASK_STATES = {"pending", "running", "retrying", "rate_limited"}

# Project states we are allowed to self-heal. "building" can get stuck if the
# orchestrator process dies before writing the final status; the *complete*
# states are reconcilable too so stale sprint badges get fixed even on a build
# that already finished. We deliberately never touch paused/failed/queued/doc_*
# so we don't override a status the user or orchestrator set intentionally.
RECONCILABLE_PROJECT_STATES = {"building", "complete", "complete_with_gaps"}


async def reconcile_build_status(db: AsyncSession, project: Project) -> bool:
    """
    Self-heal a build whose stored status drifted from the real task states.

    The orchestrator writes ``project.status = "complete"`` (and never writes
    ``sprint.status`` at all) only at the very end of its loop. If that process
    is interrupted (server restart, crash) after the last task is committed but
    before the final write, the project is left stuck in ``building`` forever
    even though every task is in a terminal state — which is exactly why a
    project can show 100% progress while still reporting "building".

    This derives the correct status purely from the task rows. When the build is
    genuinely finished (nothing pending/running), it persists the terminal
    project status and marks every fully-resolved sprint ``completed``. It only
    acts on reconcilable states and never completes a build that still has
    pending/running work, so a live or paused build is left untouched.

    ``project`` must already have ``sprints`` and each sprint's ``tasks`` loaded.
    Returns ``True`` if anything was changed and committed.
    """
    if project.status not in RECONCILABLE_PROJECT_STATES:
        return False

    all_tasks = [task for sprint in project.sprints for task in sprint.tasks]
    if not all_tasks:
        return False

    # If any task is still queued or running, the build is genuinely in flight
    # (or paused mid-way). Don't declare it finished.
    if any(task.status in ACTIVE_TASK_STATES for task in all_tasks):
        return False

    changed = False

    # Mark every sprint whose tasks are all in a terminal state as completed so
    # the UI stops showing finished sprints as "Pending".
    for sprint in project.sprints:
        if sprint.tasks and sprint.status != "completed":
            sprint.status = "completed"
            changed = True

    # Reconcile a stale in-flight project status to the correct terminal one.
    if project.status == "building":
        has_gaps = any(
            task.status in ("failed", "failed_skipped") for task in all_tasks
        )
        project.status = "complete_with_gaps" if has_gaps else "complete"
        changed = True

    if changed:
        await db.commit()

    return changed


class BuildOrchestrator:
    MAX_RETRIES = 2  # increased from 1

    def __init__(self, db: AsyncSession):
        self.db = db
        self._is_running = False
        self._should_stop = False
        self.project_id = None
    
    async def start_build(self, project_id: UUID, user_id: UUID) -> None:
        """
        Main entry point. Starts the build process.
        1. Fetch project, verify ownership and status
        2. Set project status to "building"
        3. Get all sprints with tasks ordered by sprint_number, task_number
        4. Find first pending/failed task (resume support)
        5. Start executing from that task
        """
        self.project_id = project_id
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
                    break
                
                # Check project settings to see if we should pause or continue
                if getattr(project, "pause_on_failure", False):
                    project.status = "paused"
                    task.status = "failed"
                    await self.db.commit()
                    await self.log(project_id, "WARNING", "orchestrator", f"Task {task.name} failed and pause_on_failure is enabled. Pausing build.")
                    break
                else:
                    task.status = "failed_skipped"
                    await self.db.commit()
                    await self.log(project_id, "WARNING", "orchestrator", f"Task {task.name} failed. Skipping and continuing automatically...")
                    continue
        else:
            # Completed all tasks loop (may contain skipped tasks)
            # Fetch all tasks again to check for skipped tasks
            skipped_tasks = [t for t in all_tasks if t.status == "failed_skipped"]
            if skipped_tasks:
                await self.log(project_id, "INFO", "orchestrator", f"Starting automatic post-build self-healing phase for {len(skipped_tasks)} skipped tasks.")
                for task in skipped_tasks:
                    await self.log(project_id, "INFO", "orchestrator", f"Attempting self-healing for task: {task.name}")
                    success = await self.execute_task(task, project.project_dir or "/tmp")
                    if success:
                        task.status = "passed"
                        await self.db.commit()
                        await self.log(project_id, "INFO", "orchestrator", f"Self-healing successful! Task {task.name} passed.")
                    else:
                        await self.log(project_id, "WARNING", "orchestrator", f"Self-healing failed for task: {task.name}")
                        task.status = "failed"
                        await self.db.commit()

                # Re-check task statuses after self-healing attempts
                final_failed = [t for t in all_tasks if t.status in ["failed", "failed_skipped"]]
                if final_failed:
                    project.status = "complete_with_gaps"
                    await self.db.commit()
                    await self.log(project_id, "WARNING", "orchestrator", f"Build finished with gaps. {len(final_failed)} tasks failed to resolve.")
                else:
                    project.status = "complete"
                    await self.db.commit()
                    await self.log(project_id, "INFO", "orchestrator", "Build pipeline completed successfully after self-healing!")
            else:
                project.status = "complete"
                await self.db.commit()
                await self.log(project_id, "INFO", "orchestrator", "Build pipeline completed successfully!")

        self._is_running = False

    async def execute_task(self, task: SprintTask, project_dir: str) -> bool:
        """
        Execute a single task
        """
        await self.db.refresh(task)
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

        # Log the prompt being sent
        prompt_preview = task.prompt[:500] + "..." if len(task.prompt) > 500 else task.prompt
        await self.log(project_id, "PROMPT", f"task:{task.task_number}", prompt_preview)

        # Run Claude (Attempt 1)
        success, output, rate_limit_reset = await self.run_claude(task.prompt, project_dir)
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

        # Log Claude's output
        output_preview = output[:800] + "..." if len(output) > 800 else output
        await self.log(project_id, "CLAUDE", f"task:{task.task_number}", output_preview)

        # Run tests if test command is specified
        passed, failed, test_output = 0, 0, ""
        if task.test_command:
            await self.log(project_id, "INFO", "orchestrator", f"Running tests: {task.test_command}")
            passed, failed, test_output = self.run_tests(task.test_command, project_dir)
            task.test_count = passed + failed
            task.tests_passed = passed
            task.tests_failed = failed
            task.error_output = test_output if failed > 0 else None
            # Log test result summary
            test_summary = "\n".join([l for l in test_output.split("\n") if any(x in l for x in ["passed", "failed", "error", "PASSED", "FAILED", "ERROR"])])[-600:]
            await self.log(project_id, "TESTS", f"task:{task.task_number}", test_summary or test_output[-400:])

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
                    success_dep, output_dep, rate_limit_dep = await self.run_claude(dep_prompt, project_dir)
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
                    success, output, rate_limit_reset = await self.run_claude(retry_prompt, project_dir)
                else:
                    # Level 1: Direct retry with error context
                    retry_prompt = self.build_retry_prompt(task.prompt, task.error_output or "")
                    success, output, rate_limit_reset = await self.run_claude(retry_prompt, project_dir)
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
                success, output, rate_limit_reset = await self.run_claude(clean_prompt, project_dir)

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
        Marks the task as failed but keeps the project in 'building' state
        so the orchestrator loop can continue to the next task automatically.
        """
        task.status = "failed"
        task.completed_at = datetime.utcnow()
        await self.db.commit()
        await self.log(project_id, "ERROR", "orchestrator", f"Task {task.name} failed after all recovery attempts. Continuing to next task...")

    async def resume_from_failure(self, project_id: UUID, user_id: UUID):
        """
        Resume a failed build. Finds the first failed/retrying task and resets it,
        then starts the build. If no failed task exists (e.g. all tasks are pending),
        just starts the build from where it left off.
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

        # Find and reset the first blocked task (failed or retrying)
        failed_task = None
        for sprint in sorted(project.sprints, key=lambda s: s.sprint_number):
            for task in sorted(sprint.tasks, key=lambda t: t.task_number):
                if task.status in ("failed", "retrying"):
                    failed_task = task
                    break
            if failed_task:
                break

        if failed_task:
            # Reset the blocked task so it can run again
            failed_task.status = "pending"
            failed_task.retry_count = 0
            failed_task.error_output = None

        # Always transition project back to building and kick off the pipeline
        project.status = "building"
        await self.db.commit()

        from app.core.database import async_session
        async def run_in_background():
            async with async_session() as background_db:
                orch = BuildOrchestrator(background_db)
                await orch.start_build(project_id, user_id)

        asyncio.create_task(run_in_background())

    async def run_claude(self, prompt: str, project_dir: str) -> tuple[bool, str, datetime | None]:
        """
        Run claude -p via ClaudeService.run_prompt.
        """
        import os
        import asyncio
        from app.services.claude_service import ClaudeService
        os.makedirs(project_dir, exist_ok=True)
        project_id_str = str(self.project_id) if getattr(self, "project_id", None) else None
        result = await asyncio.to_thread(
            ClaudeService.run_prompt, 
            prompt, 
            cwd=project_dir, 
            project_id=project_id_str
        )
        return result["success"], result["output"], result["rate_limit_reset"]

    def run_tests(self, test_command: str, project_dir: str) -> tuple[int, int, str]:
        """
        Run test command as subprocess.
        Auto-installs requirements.txt first if present to ensure all test
        dependencies (e.g. pytest-mock) are available.
        """
        if not test_command:
            return 0, 0, ""

        import os
        import sys
        
        # Prepend virtual environment bin path to PATH
        env = os.environ.copy()
        venv_bin = os.path.dirname(sys.executable)
        env["PATH"] = venv_bin + os.pathsep + env.get("PATH", "")

        req_file = os.path.join(project_dir, "requirements.txt")
        req_cwd = project_dir
        if not os.path.exists(req_file):
            alt_req = os.path.join(project_dir, "backend", "requirements.txt")
            if os.path.exists(alt_req):
                req_file = alt_req
                req_cwd = os.path.join(project_dir, "backend")

        if os.path.exists(req_file):
            subprocess.run(
                f"pip install -q -r {req_file}",
                shell=True,
                capture_output=True,
                cwd=req_cwd,
                env=env,
                timeout=120
            )
        
        try:
            result = subprocess.run(
                test_command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=project_dir,
                env=env,
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
        # Mirror into the unified complete.log so build activity is visible
        # there alongside app/uvicorn/Claude logs (in addition to the DB).
        logger.log(
            _PY_LEVELS.get(level, logging.INFO),
            "[build:%s] %s | %s: %s", project_id, level, source, message,
        )

    async def pause_build(self, project_id: UUID, user_id: UUID):
        self._should_stop = True
        from app.services.claude_service import ClaudeService
        ClaudeService.terminate_process(str(project_id))
        stmt = select(Project).where(Project.id == project_id, Project.user_id == user_id)
        res = await self.db.execute(stmt)
        project = res.scalars().first()
        if project:
            project.status = "paused"
            await self.db.commit()
            await self.log(project_id, "INFO", "orchestrator", "Pause request received. Pausing build process and terminating running Claude process.")

    async def cancel_build(self, project_id: UUID, user_id: UUID):
        self._should_stop = True
        from app.services.claude_service import ClaudeService
        ClaudeService.terminate_process(str(project_id))
        stmt = select(Project).where(Project.id == project_id, Project.user_id == user_id)
        res = await self.db.execute(stmt)
        project = res.scalars().first()
        if project:
            project.status = "failed"
            await self.db.commit()
            await self.log(project_id, "INFO", "orchestrator", "Cancel request received. Cancelling build process and terminating running Claude process.")
