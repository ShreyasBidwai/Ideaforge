import os
import re
import logging
from uuid import UUID
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.orm import selectinload
from app.models.project import Project
from app.models.setup_step import SetupStep
from app.services.project_dir_service import ProjectDirService

logger = logging.getLogger(__name__)

KNOWN_SERVICES = {
    "stripe": ("external_account", "https://dashboard.stripe.com/apikeys"),
    "twilio": ("external_account", "https://console.twilio.com"),
    "sendgrid": ("api_key", "https://app.sendgrid.com/settings/api_keys"),
    "openai": ("api_key", "https://platform.openai.com/api-keys"),
    "google": ("oauth_config", "https://console.cloud.google.com/apis/credentials"),
    "firebase": ("external_account", "https://console.firebase.google.com"),
}


class SetupManifestService:
    def __init__(self, db: AsyncSession | None = None):
        self.db = db

    def _parse_env_example(self, env_example_content: str) -> list[dict]:
        """
        Parse .env.example content.
        Ignore comments and blank lines.
        """
        steps = []
        lines = env_example_content.splitlines()
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip()
            else:
                key = line
                val = ""

            key_upper = key.upper()
            is_apikey = any(
                term in key_upper
                for term in ["API_KEY", "SECRET", "TOKEN", "CLIENT_ID", "CLIENT_SECRET"]
            )

            if is_apikey:
                step_type = "api_key"
                is_required = True
            else:
                step_type = "env_var"
                is_required = not bool(val)  # If it has a default value, it is not required

            steps.append({
                "env_key": key,
                "step_type": step_type,
                "title": f"Configure {key}",
                "description": f"Set the value for the environment variable {key}.",
                "target_file": ".env",
                "is_required": is_required,
                "is_completed": False
            })
        return steps

    def _scan_docs_for_services(self, text: str) -> list[dict]:
        """Scan documentation text for references to known external services."""
        steps = []
        if not text:
            return steps

        text_lower = text.lower()
        for service, (step_type, doc_url) in KNOWN_SERVICES.items():
            # Use regex with word boundary to avoid partial matches
            if re.search(rf"\b{service}\b", text_lower):
                steps.append({
                    "step_type": step_type,
                    "title": f"Set up {service.capitalize()} account",
                    "description": f"Create an account or obtain credentials for {service.capitalize()}.",
                    "doc_url": doc_url,
                    "is_required": True,
                    "is_completed": False
                })
        return steps

    def _write_env_line(self, project_dir: str, env_key: str, value: str, allowed_keys: set[str]) -> bool:
        """
        Write/update a single KEY=value line in the project's .env file.
        Only allow keys that exist in allowed_keys. Validate no newlines in value.
        """
        if env_key not in allowed_keys:
            logger.warning(f"Rejected attempt to write unapproved env key: {env_key}")
            return False

        if "\n" in value or "\r" in value:
            logger.warning("Rejected attempt to write value containing newline/carriage return")
            return False

        env_file_path = os.path.join(project_dir, ".env")
        
        # Read existing file content if it exists
        lines = []
        if os.path.exists(env_file_path):
            try:
                with open(env_file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
            except Exception as e:
                logger.error(f"Failed to read existing .env file: {e}")
                return False

        updated = False
        new_line = f"{env_key}={value}\n"
        for i, line in enumerate(lines):
            stripped = line.strip()
            # Skip comments or empty lines
            if stripped.startswith("#") or not stripped:
                continue
            if "=" in line:
                k, _ = line.split("=", 1)
                if k.strip() == env_key:
                    lines[i] = new_line
                    updated = True
                    break

        if not updated:
            # Ensure file ends with newline or append
            if lines and not lines[-1].endswith("\n"):
                lines[-1] += "\n"
            lines.append(new_line)

        try:
            with open(env_file_path, "w", encoding="utf-8") as f:
                f.writelines(lines)
            return True
        except Exception as e:
            logger.error(f"Failed to write to .env file: {e}")
            return False

    async def generate_manifest(self, project_id: UUID) -> list[SetupStep]:
        """Build and persist the manifest for a project."""
        stmt = select(Project).where(Project.id == project_id).options(selectinload(Project.documents))
        res = await self.db.execute(stmt)
        project = res.scalars().first()
        if not project:
            raise ValueError("Project not found")

        # 1. Parse .env.example if it exists in project folder
        project_dir = ProjectDirService.get_project_dir(str(project.id), project.name)
        env_example_path = os.path.join(project_dir, ".env.example")
        
        env_steps = []
        allowed_keys = set()
        if os.path.exists(env_example_path):
            try:
                with open(env_example_path, "r", encoding="utf-8") as f:
                    content = f.read()
                env_steps = self._parse_env_example(content)
                allowed_keys = {s["env_key"] for s in env_steps}
            except Exception as e:
                logger.error(f"Failed to read .env.example: {e}")

        # 2. Scan docs for known services
        doc_text = ""
        for doc in project.documents:
            if doc.content:
                doc_text += "\n" + doc.content
        doc_steps = self._scan_docs_for_services(doc_text)

        # 3. Clean up existing steps for this project (re-generation)
        delete_stmt = select(SetupStep).where(SetupStep.project_id == project_id)
        existing_res = await self.db.execute(delete_stmt)
        for step in existing_res.scalars().all():
            await self.db.delete(step)
        await self.db.flush()

        # 4. Save new steps
        saved_steps = []
        
        # Combine env steps
        for es in env_steps:
            step = SetupStep(
                project_id=project_id,
                step_type=es["step_type"],
                title=es["title"],
                description=es["description"],
                target_file=es["target_file"],
                env_key=es["env_key"],
                is_required=es["is_required"],
                is_completed=es["is_completed"]
            )
            self.db.add(step)
            saved_steps.append(step)

        # Combine service steps
        for ds in doc_steps:
            # Avoid duplicating titles
            if any(s.title == ds["title"] for s in saved_steps):
                continue
            step = SetupStep(
                project_id=project_id,
                step_type=ds["step_type"],
                title=ds["title"],
                description=ds["description"],
                doc_url=ds["doc_url"],
                is_required=ds["is_required"],
                is_completed=ds["is_completed"]
            )
            self.db.add(step)
            saved_steps.append(step)

        await self.db.commit()
        return saved_steps

    async def get_manifest(self, project_id: UUID) -> list[SetupStep]:
        stmt = select(SetupStep).where(SetupStep.project_id == project_id).order_by(SetupStep.created_at.asc())
        res = await self.db.execute(stmt)
        return res.scalars().all()

    async def mark_step(self, step_id: UUID, completed: bool) -> SetupStep:
        stmt = select(SetupStep).where(SetupStep.id == step_id)
        res = await self.db.execute(stmt)
        step = res.scalars().first()
        if not step:
            raise ValueError("Step not found")
        step.is_completed = completed
        await self.db.commit()
        return step

    async def write_env_value(self, project_id: UUID, env_key: str, value: str) -> bool:
        stmt = select(Project).where(Project.id == project_id)
        res = await self.db.execute(stmt)
        project = res.scalars().first()
        if not project:
            return False

        project_dir = ProjectDirService.get_project_dir(str(project.id), project.name)
        env_example_path = os.path.join(project_dir, ".env.example")
        
        allowed_keys = set()
        if os.path.exists(env_example_path):
            try:
                with open(env_example_path, "r", encoding="utf-8") as f:
                    content = f.read()
                parsed = self._parse_env_example(content)
                allowed_keys = {s["env_key"] for s in parsed}
            except Exception as e:
                logger.error(f"Failed to read .env.example: {e}")
                return False

        # Write to .env
        ok = self._write_env_line(project_dir, env_key, value, allowed_keys)
        if ok:
            # Mark the matching SetupStep in db as completed
            step_stmt = select(SetupStep).where(SetupStep.project_id == project_id, SetupStep.env_key == env_key)
            step_res = await self.db.execute(step_stmt)
            step = step_res.scalars().first()
            if step:
                step.is_completed = True
                await self.db.commit()
        return ok

    async def all_required_complete(self, project_id: UUID) -> bool:
        stmt = select(SetupStep).where(SetupStep.project_id == project_id, SetupStep.is_required == True, SetupStep.is_completed == False)
        res = await self.db.execute(stmt)
        incompleted = res.scalars().all()
        return len(incompleted) == 0
