import pytest

try:
    from app.ai.prompts.docs.architecture import get_database_directive
except ImportError:
    from backend.app.ai.prompts.docs.architecture import get_database_directive

try:
    from app.services.sprint_generation_service import SprintGenerationService
except ImportError:
    from backend.app.services.sprint_generation_service import SprintGenerationService


# TEST 1: POC uses SQLite directive
def test_poc_gets_sqlite():
    directive = get_database_directive("poc", ["FastAPI"])
    assert "sqlite" in directive.lower()
    assert "./app.db" in directive

# TEST 2: MVP uses SQLite directive
def test_mvp_gets_sqlite():
    directive = get_database_directive("mvp", ["FastAPI"])
    assert "sqlite" in directive.lower()
    assert "zero" in directive.lower() or "no external" in directive.lower() or "no system install" in directive.lower()

# TEST 3: Production uses PostgreSQL
def test_production_gets_postgres():
    directive = get_database_directive("production", ["FastAPI"])
    assert "postgresql" in directive.lower()

# TEST 4: Pre-production uses PostgreSQL
def test_preproduction_gets_postgres():
    directive = get_database_directive("pre_production", ["FastAPI"])
    assert "postgresql" in directive.lower()

# TEST 5: SQLite directive forbids docker/server
def test_sqlite_forbids_setup():
    directive = get_database_directive("mvp", ["FastAPI"])
    assert "docker" in directive.lower()  # mentioned as something NOT to require
    assert "do not require" in directive.lower() or "not require" in directive.lower()

# TEST 6: Sprint prompt embeds runnability requirement
def test_sprint_prompt_has_runnability():
    svc = SprintGenerationService(db=None)
    # Build a minimal fake project + docs
    class P: 
        name="X"; industry="HC"; location="IN"; maturity_level="mvp"; tech_stack=["FastAPI","React"]
        documents=[]
    prompt = svc._build_sprint_generation_prompt(P(), [])
    assert "runnab" in prompt.lower() or "run on a fresh machine" in prompt.lower()
    assert ".env.example" in prompt
