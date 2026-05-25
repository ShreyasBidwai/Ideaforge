import pytest
from uuid import uuid4
from sqlalchemy import inspect


# TEST 1: All models are importable
def test_models_importable():
    """All 5 models should be importable from backend.app.models"""
    from backend.app.models import Base
    from backend.app.models.user import User
    from backend.app.models.session import Session
    from backend.app.models.problem_statement import ProblemStatement
    from backend.app.models.solution import Solution
    from backend.app.models.evaluation import Evaluation

    assert all([User, Session, ProblemStatement, Solution, Evaluation])


# TEST 2: User model has correct table name and columns
def test_user_model_schema():
    """User model should have correct columns"""
    from backend.app.models.user import User

    mapper = inspect(User)
    columns = {c.key for c in mapper.columns}
    required = {
        "id",
        "email",
        "hashed_password",
        "full_name",
        "is_active",
        "created_at",
        "updated_at",
    }
    assert required.issubset(columns), f"Missing columns: {required - columns}"


# TEST 3: Session model has correct columns
def test_session_model_schema():
    """Session model should have correct columns"""
    from backend.app.models.session import Session

    mapper = inspect(Session)
    columns = {c.key for c in mapper.columns}
    required = {
        "id",
        "user_id",
        "industry",
        "location",
        "pain_points",
        "status",
        "created_at",
    }
    assert required.issubset(columns)


# TEST 4: ProblemStatement has all rating columns
def test_problem_statement_rating_columns():
    """ProblemStatement should have severity, feasibility, market_size, uniqueness, overall_rating"""
    from backend.app.models.problem_statement import ProblemStatement

    mapper = inspect(ProblemStatement)
    columns = {c.key for c in mapper.columns}
    rating_cols = {
        "severity",
        "feasibility",
        "market_size",
        "uniqueness",
        "overall_rating",
    }
    assert rating_cols.issubset(columns), f"Missing rating columns: {rating_cols - columns}"


# TEST 5: Solution model has is_unconventional flag
def test_solution_unconventional_flag():
    """Solution model must have is_unconventional boolean field"""
    from backend.app.models.solution import Solution

    mapper = inspect(Solution)
    columns = {c.key for c in mapper.columns}
    assert "is_unconventional" in columns


# TEST 6: Evaluation model has all evaluation protocol fields
def test_evaluation_protocol_fields():
    """Evaluation must have rubric, scores, weighted_avg, min_score, attack_summary, attack_survives, inconsistencies, inconsistency_count"""
    from backend.app.models.evaluation import Evaluation

    mapper = inspect(Evaluation)
    columns = {c.key for c in mapper.columns}
    required = {
        "rubric",
        "scores",
        "weighted_avg",
        "min_score",
        "attack_summary",
        "attack_survives",
        "inconsistencies",
        "inconsistency_count",
    }
    assert required.issubset(columns), f"Missing: {required - columns}"


# TEST 7: Foreign key relationships exist
def test_foreign_keys():
    """Session -> User, ProblemStatement -> Session, Solution -> ProblemStatement, Evaluation -> Solution"""
    from backend.app.models.session import Session
    from backend.app.models.problem_statement import ProblemStatement
    from backend.app.models.solution import Solution
    from backend.app.models.evaluation import Evaluation

    assert any(
        "users.id" in str(fk.target_fullname)
        for fk in inspect(Session).columns["user_id"].foreign_keys
    )
    assert any(
        "sessions.id" in str(fk.target_fullname)
        for fk in inspect(ProblemStatement).columns["session_id"].foreign_keys
    )
    assert any(
        "problem_statements.id" in str(fk.target_fullname)
        for fk in inspect(Solution).columns["problem_id"].foreign_keys
    )
    assert any(
        "solutions.id" in str(fk.target_fullname)
        for fk in inspect(Evaluation).columns["solution_id"].foreign_keys
    )


# TEST 8: Base.metadata contains all tables
def test_all_tables_registered():
    """All 5 tables should be registered in Base.metadata"""
    from backend.app.models import Base

    table_names = set(Base.metadata.tables.keys())
    required = {
        "users",
        "sessions",
        "problem_statements",
        "solutions",
        "evaluations",
    }
    assert required.issubset(table_names), f"Missing tables: {required - table_names}"


# TEST 9: Alembic migration file exists
def test_migration_file_exists():
    """At least one migration file should exist in alembic/versions/"""
    import os

    # We need to look up relative to the project root or backend folder
    # Since pytest runs with rootdir = backend, alembic is at backend/alembic/
    versions_dir = os.path.join("alembic", "versions")
    if not os.path.exists(versions_dir):
        # Fallback to double check
        versions_dir = os.path.join("backend", "alembic", "versions")

    py_files = [
        f
        for f in os.listdir(versions_dir)
        if f.endswith(".py") and f != "__init__.py"
    ]
    assert len(py_files) >= 1, "No migration files found"
