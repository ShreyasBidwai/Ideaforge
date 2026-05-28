import asyncio
import os
import json
import re
import logging
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.project import Project
from app.models.e2e_suite import E2ETest
from app.services.claude_service import ClaudeService, ClaudeOutputParser
from app.services.project_dir_service import ProjectDirService

logger = logging.getLogger(__name__)


class E2EService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_e2e_tests(self, project_id: UUID, user_id: UUID) -> list[E2ETest]:
        """
        1. Read project structure + key route files (via ProjectDirService).
        2. Build a claude -p prompt: 'Generate end-to-end tests for this running app.
           Backend API base URL will be provided as BASE_URL env var. For a web frontend,
           use Playwright; for API-only, use httpx integration tests. Output JSON:
           {tests:[{name, framework, file_path, test_code}]}'
        3. await asyncio.to_thread(ClaudeService.run_prompt, ...) with timeout=600.
        4. Parse JSON (reuse the fenced-JSON parser pattern), write test files into
           the project dir (e.g. e2e/), save E2ETest rows.
        5. Handle rate limit → 429 with reset time, same pattern as sprint generation.
        """
        # Fetch project
        stmt = select(Project).where(Project.id == project_id)
        res = await self.db.execute(stmt)
        project = res.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        project_dir = project.project_dir
        if not project_dir:
            project_dir = ProjectDirService.get_project_dir(str(project.id), project.name)

        # Read structure and key route files
        structure = ProjectDirService.get_project_structure(project_dir)
        context_files = []
        try:
            for root, dirs, files in os.walk(project_dir):
                dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "__pycache__", ".venv", "venv", ".pytest_cache", "e2e"}]
                for file in files:
                    if file.endswith((".py", ".ts", ".js")) and any(k in file.lower() for k in ("main", "app", "router", "route", "server", "controller", "api")):
                        rel_path = os.path.relpath(os.path.join(root, file), project_dir)
                        content = ProjectDirService.get_file_content(project_dir, rel_path)
                        if content:
                            context_files.append({"path": rel_path, "content": content[:4000]})
        except Exception as e:
            logger.error(f"Error walking project dir: {e}")

        # Build prompt
        prompt = (
            f"Generate end-to-end / integration tests for this running app.\n"
            f"Project Directory Structure:\n{json.dumps(structure, indent=2)}\n\n"
            f"Key files content:\n"
        )
        for cf in context_files[:5]:
            prompt += f"\nFile: {cf['path']}\n```\n{cf['content']}\n```\n"

        prompt += (
            "\nGenerate end-to-end / integration tests for this running app. "
            "Backend API base URL will be provided as BASE_URL env var. For a web frontend, "
            "use Playwright; for API-only, use httpx integration tests. Output JSON: "
            "{tests:[{name, framework, file_path, test_code}]}.\n"
            "Output ONLY the JSON object, starting with { and ending with }."
        )

        # Execute claude prompt
        result = await asyncio.to_thread(
            ClaudeService.run_prompt,
            prompt=prompt,
            cwd=project_dir,
            timeout=600
        )

        if result.get("is_rate_limited"):
            reset_time = result.get("rate_limit_reset")
            reset_str = reset_time.isoformat() if reset_time else None
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "reset_at": reset_str
                }
            )

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error") or "Failed to generate E2E tests"
            )

        # Parse JSON
        try:
            parsed = self._parse_json(result.get("output", ""))
            tests = parsed.get("tests", [])
        except Exception as e:
            logger.error(f"Error parsing E2E test JSON: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to parse Claude JSON output: {str(e)}"
            )

        # Write files and create DB records
        created_tests = []
        for t in tests:
            name = t.get("name", "E2E Test")
            framework = t.get("framework", "pytest-httpx")
            file_path = t.get("file_path", "e2e/test_default.py")
            test_code = t.get("test_code", "")

            # Ensure e2e directory exists inside project_dir
            abs_file_path = os.path.join(project_dir, file_path)
            os.makedirs(os.path.dirname(abs_file_path), exist_ok=True)
            with open(abs_file_path, "w", encoding="utf-8") as f:
                f.write(test_code)

            # Create DB row
            db_test = E2ETest(
                project_id=project_id,
                name=name,
                framework=framework,
                test_code=test_code,
                file_path=file_path,
                status="pending"
            )
            self.db.add(db_test)
            created_tests.append(db_test)

        await self.db.commit()
        return created_tests

    async def run_e2e_tests(self, project_id: UUID, base_url: str) -> dict:
        """
        Run the generated E2E suite against a running instance.
        - playwright: `npx playwright test` in project dir with BASE_URL env
        - pytest-httpx: `python -m pytest e2e/ -v` with BASE_URL env
        Run via asyncio.to_thread. Parse pass/fail with the existing
        ClaudeOutputParser.parse_test_results. Update E2ETest rows + return summary.
        Requires the project to be running (caller passes the run URL).
        """
        stmt = select(E2ETest).where(E2ETest.project_id == project_id)
        res = await self.db.execute(stmt)
        tests = res.scalars().all()

        stmt_p = select(Project).where(Project.id == project_id)
        res_p = await self.db.execute(stmt_p)
        project = res_p.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        project_dir = project.project_dir
        if not project_dir:
            raise HTTPException(status_code=400, detail="Project directory not set")

        env = os.environ.copy()
        env["BASE_URL"] = base_url

        passed_count = 0
        failed_count = 0

        for test in tests:
            if test.framework == "playwright":
                cmd = ["npx", "playwright", "test", test.file_path]
            else:
                # pytest-httpx
                venv_pytest = os.path.join(project_dir, ".venv", "bin", "pytest")
                if os.path.exists(venv_pytest):
                    cmd = [venv_pytest, test.file_path, "-v"]
                else:
                    cmd = ["pytest", test.file_path, "-v"]

            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    cwd=project_dir,
                    env=env,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await proc.communicate()
                output = (stdout or b"").decode("utf-8", errors="ignore") + "\n" + (stderr or b"").decode("utf-8", errors="ignore")

                results = ClaudeOutputParser.parse_test_results(output)
                test.last_output = output

                if results["all_passed"] or (results["passed"] > 0 and results["failed"] == 0 and results["errors"] == 0):
                    test.status = "passed"
                    passed_count += 1
                else:
                    test.status = "failed"
                    failed_count += 1
            except Exception as e:
                test.status = "failed"
                test.last_output = f"Failed to execute command: {e}"
                failed_count += 1

            self.db.add(test)

        await self.db.commit()

        return {
            "passed": passed_count,
            "failed": failed_count,
            "total": len(tests)
        }

    def _parse_json(self, output: str) -> dict:
        cleaned = output.strip()
        cleaned = re.sub(r'^```(?:json)?\s*\n?', '', cleaned)
        cleaned = re.sub(r'\n?```\s*$', '', cleaned)
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r'\{[\s\S]*\}', cleaned)
            if match:
                return json.loads(match.group())
            raise
