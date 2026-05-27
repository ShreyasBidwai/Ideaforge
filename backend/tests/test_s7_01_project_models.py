import pytest
from sqlalchemy import inspect

# TEST 1: All new models importable
def test_new_models_importable():
    from app.models.project import Project
    from app.models.document import Document
    from app.models.sprint import Sprint
    from app.models.sprint_task import SprintTask
    from app.models.build_log import BuildLog
    assert all([Project, Document, Sprint, SprintTask, BuildLog])

# TEST 2: Project model has all columns
def test_project_columns():
    from app.models.project import Project
    cols = {c.key for c in inspect(Project).columns}
    required = {"id", "user_id", "solution_id", "name", "status", "tech_stack", "project_dir", "maturity_level"}
    assert required.issubset(cols)

# TEST 3: SprintTask has prompt and test fields
def test_sprint_task_columns():
    from app.models.sprint_task import SprintTask
    cols = {c.key for c in inspect(SprintTask).columns}
    required = {"prompt", "test_command", "test_count", "tests_passed", "tests_failed", "claude_output", "error_output", "retry_count", "rate_limit_reset_at", "status"}
    assert required.issubset(cols)

# TEST 4: BuildLog has required fields
def test_build_log_columns():
    from app.models.build_log import BuildLog
    cols = {c.key for c in inspect(BuildLog).columns}
    required = {"project_id", "timestamp", "level", "source", "message"}
    assert required.issubset(cols)

# TEST 5: Project status default
def test_project_default_status():
    from app.models.project import Project
    col = next(c for c in inspect(Project).columns if c.key == "status")
    assert str(col.default.arg) == "doc_generation"

# TEST 6: Foreign keys exist
def test_foreign_keys():
    from app.models.project import Project
    from app.models.sprint import Sprint
    from app.models.sprint_task import SprintTask
    assert any("users.id" in str(fk.target_fullname) for fk in inspect(Project).columns["user_id"].foreign_keys)
    assert any("projects.id" in str(fk.target_fullname) for fk in inspect(Sprint).columns["project_id"].foreign_keys)
    assert any("sprints.id" in str(fk.target_fullname) for fk in inspect(SprintTask).columns["sprint_id"].foreign_keys)

# TEST 7: All tables registered
def test_all_tables():
    from app.models import Base
    tables = set(Base.metadata.tables.keys())
    required = {"projects", "documents", "sprints", "sprint_tasks", "build_logs"}
    assert required.issubset(tables)
