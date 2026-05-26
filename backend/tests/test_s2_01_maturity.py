import pytest

# TEST 1: All maturity levels are defined
def test_all_maturity_levels_exist():
    """All 4 maturity levels should be defined in the enum"""
    from app.core.maturity import MaturityLevel
    assert MaturityLevel.POC == "poc"
    assert MaturityLevel.MVP == "mvp"
    assert MaturityLevel.PRE_PRODUCTION == "pre_production"
    assert MaturityLevel.PRODUCTION == "production"

# TEST 2: Maturity configs have correct defaults
def test_maturity_config_values():
    """Each maturity level should have a valid config"""
    from app.core.maturity import get_maturity_config, MaturityLevel
    poc = get_maturity_config(MaturityLevel.POC)
    assert poc.temperature == 0.9
    assert poc.solution_candidate_count == 3
    assert poc.include_security_criteria is False
    
    prod = get_maturity_config(MaturityLevel.PRODUCTION)
    assert prod.temperature == 0.3
    assert prod.solution_candidate_count == 5
    assert prod.include_security_criteria is True
    assert prod.include_compliance_criteria is True

# TEST 3: POC has fewer evaluation steps than production
def test_poc_fewer_steps_than_production():
    """POC should skip devil's advocate and ACH"""
    from app.core.maturity import get_maturity_config, MaturityLevel
    poc = get_maturity_config(MaturityLevel.POC)
    prod = get_maturity_config(MaturityLevel.PRODUCTION)
    assert len(poc.evaluation_steps) < len(prod.evaluation_steps)
    assert "devils_advocate" not in poc.evaluation_steps
    assert "ach_analysis" not in poc.evaluation_steps
    assert "devils_advocate" in prod.evaluation_steps
    assert "ach_analysis" in prod.evaluation_steps

# TEST 4: GET /maturity-levels returns all 4 levels
@pytest.mark.anyio
async def test_get_maturity_levels(client):
    """GET /api/v1/maturity-levels should return all 4 levels with descriptions"""
    response = await client.get("/api/v1/maturity-levels")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 4
    levels = {item["level"] for item in data}
    assert levels == {"poc", "mvp", "pre_production", "production"}
    for item in data:
        assert "label" in item
        assert "description" in item
        assert "evaluation_steps" in item

# TEST 5: Session model now has maturity_level field
def test_session_has_maturity_field():
    """Session model should have maturity_level column"""
    from sqlalchemy import inspect
    from app.models.session import Session
    columns = {c.key for c in inspect(Session).columns}
    assert "maturity_level" in columns
    assert "tech_stack_preferences" in columns

# TEST 6: Session defaults to MVP maturity
def test_session_default_maturity():
    """New session should default to MVP maturity level"""
    from app.models.session import Session
    from sqlalchemy import inspect
    mapper = inspect(Session)
    maturity_col = next(c for c in mapper.columns if c.key == "maturity_level")
    assert str(maturity_col.default.arg) == "mvp"

# TEST 7: SessionCreate schema validates maturity level
def test_session_create_schema_validation():
    """SessionCreate should reject invalid maturity levels"""
    from app.schemas.session import SessionCreate
    from pydantic import ValidationError
    # Valid
    s = SessionCreate(industry="Fintech", location="India", maturity_level="poc")
    assert s.maturity_level == "poc"
    # Invalid
    with pytest.raises(ValidationError):
        SessionCreate(industry="Fintech", location="India", maturity_level="invalid_level")
