import asyncio
import builtins
import os
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
