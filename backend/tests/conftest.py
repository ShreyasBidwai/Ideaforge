import os
# Force tests to use isolated test database instead of wiping development database
os.environ["DATABASE_URL"] = "postgresql+asyncpg://tuition:tuition@localhost:5433/ideaforge_test"

import asyncio
import builtins
import sys
from importlib.abc import Loader, MetaPathFinder
from importlib.machinery import ModuleSpec
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

# Configure path resolutions
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Hook into builtins.__import__ to alias "backend.app" modules to "app" modules dynamically.
# This prevents double loading of files/classes in SQLAlchemy metadata.
original_import = builtins.__import__


def custom_import(name, globals=None, locals=None, fromlist=(), level=0):
    # Alias the main module being imported
    if name.startswith("backend.app"):
        sibling = name[8:]
        if sibling in sys.modules and name not in sys.modules:
            sys.modules[name] = sys.modules[sibling]
    elif name.startswith("app"):
        sibling = "backend." + name
        if sibling in sys.modules and name not in sys.modules:
            sys.modules[name] = sys.modules[sibling]

    # Alias any submodules in fromlist
    if fromlist:
        for item in fromlist:
            if isinstance(item, str):
                child_name = f"{name}.{item}"
                if child_name.startswith("backend.app"):
                    child_sibling = child_name[8:]
                    if (
                        child_sibling in sys.modules
                        and child_name not in sys.modules
                    ):
                        sys.modules[child_name] = sys.modules[child_sibling]
                elif child_name.startswith("app"):
                    child_sibling = "backend." + child_name
                    if (
                        child_sibling in sys.modules
                        and child_name not in sys.modules
                    ):
                        sys.modules[child_name] = sys.modules[child_sibling]

    return original_import(name, globals, locals, fromlist, level)


builtins.__import__ = custom_import

from backend.app.main import app


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as ac:
        yield ac


@pytest.fixture(autouse=True)
async def cleanup_db():
    from app.core.database import async_session, engine

    async with async_session() as session:
        await session.execute(text("TRUNCATE TABLE users CASCADE;"))
        await session.commit()

    await engine.dispose()

@pytest.fixture
async def auth_headers(client):
    # Register user A
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "usera@example.com",
            "password": "StrongPass123!",
            "full_name": "User A"
        }
    )
    # Login user A
    login = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "usera@example.com",
            "password": "StrongPass123!"
        }
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
async def other_auth_headers(client):
    # Register user B
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "userb@example.com",
            "password": "StrongPass123!",
            "full_name": "User B"
        }
    )
    # Login user B
    login = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "userb@example.com",
            "password": "StrongPass123!"
        }
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def mock_gemini():
    from unittest.mock import AsyncMock, patch
    with patch("app.ai.provider.GeminiProvider.generate", new_callable=AsyncMock) as mock:
        yield mock

@pytest.fixture(autouse=True)
def mock_claude():
    from unittest.mock import patch
    import json
    
    mock_sprints = {
        "sprints": [
            {
                "sprint_number": 1, "name": "Foundation",
                "description": "Project setup and scaffolding",
                "tasks": [
                    {"task_number": 1, "name": "Project scaffold",
                     "prompt": "Create a new project in an empty directory. Initialize with package.json for frontend (React 18 + TypeScript + Vite) and requirements.txt for backend (FastAPI + SQLAlchemy + PostgreSQL). Create directory structure: backend/app/, frontend/src/, backend/tests/, frontend/src/__tests__/. Create backend/app/main.py with FastAPI app and GET /health endpoint returning {status: healthy}. Create backend/tests/test_health.py with test for health endpoint. Run: cd backend && python -m pytest tests/test_health.py -v",
                     "test_command": "cd backend && python -m pytest tests/test_health.py -v",
                     "expected_test_count": 2},
                    {"task_number": 2, "name": "Database models",
                     "prompt": "The project has FastAPI in backend/app/main.py. Create SQLAlchemy models in backend/app/models/user.py with User model (id, email, name, created_at). Create backend/app/core/database.py with async engine setup. Create backend/tests/test_models.py with model tests. Run: cd backend && python -m pytest tests/test_models.py -v",
                     "test_command": "cd backend && python -m pytest tests/test_models.py -v",
                     "expected_test_count": 4}
                ]
            },
            {
                "sprint_number": 2, "name": "Core Features",
                "description": "Main application features",
                "tasks": [
                    {"task_number": 1, "name": "API endpoints",
                     "prompt": "The project has FastAPI in backend/app/main.py and User model in backend/app/models/user.py. Create REST endpoints in backend/app/api/v1/users.py: POST /users (create), GET /users (list), GET /users/{id} (detail). Create backend/tests/test_users.py with 6 tests. Run: cd backend && python -m pytest tests/test_users.py -v",
                     "test_command": "cd backend && python -m pytest tests/test_users.py -v",
                     "expected_test_count": 6}
                ]
            }
        ],
        "total_tasks": 3, "total_sprints": 2, "estimated_total_tests": 12
    }
    
    with patch("app.services.claude_service.ClaudeService.run_prompt") as mock:
        mock.return_value = {
            "success": True,
            "output": json.dumps(mock_sprints),
            "error": None,
            "is_rate_limited": False,
            "rate_limit_reset": None,
            "exit_code": 0,
            "duration_seconds": 1.0
        }
        yield mock

@pytest.fixture
async def cache_service():
    from app.core.cache import CacheService
    from app.core.config import settings
    
    cs = CacheService(settings.REDIS_URL)
    await cs.connect()
    
    if cs.redis is None:
        class MockRedis:
            def __init__(self):
                self.store = {}
            async def ping(self):
                return True
            async def get(self, key):
                return self.store.get(key)
            async def set(self, key, value, ex=None):
                self.store[key] = value
            async def delete(self, key):
                self.store.pop(key, None)
            async def exists(self, key):
                return key in self.store
            async def close(self):
                pass
        cs.redis = MockRedis()
    else:
        try:
            await cs.redis.flushdb()
        except Exception:
            pass

    app.state.cache = cs
    yield cs
    await cs.close()


from tests.test_s6_02_approvals import create_approved_solution


