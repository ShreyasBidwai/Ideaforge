import pytest
import json

MOCK_RUBRIC = {
    "criteria": [
        {"name": "Technical Feasibility", "description": "Can this be built with current technology?",
         "weight": 2, "scale": {"1": "Requires non-existent technology", "3": "Challenging but achievable with existing tools", "5": "Straightforward to build with proven tech stack"}},
        {"name": "User Adoption Potential", "description": "Will target users actually use this?",
         "weight": 2.5, "scale": {"1": "Requires major behavior change users won't make", "3": "Moderate adoption friction, needs marketing", "5": "Solves urgent pain, users will seek it out"}},
        {"name": "Revenue Viability", "description": "Can this generate sustainable revenue?",
         "weight": 1.5, "scale": {"1": "No clear path to revenue", "3": "Revenue possible but unproven model", "5": "Proven revenue model with clear unit economics"}},
        {"name": "Scalability", "description": "Can this grow without proportional cost increase?",
         "weight": 1, "scale": {"1": "Fundamentally unscalable, cost grows linearly with users", "3": "Scalable with significant re-architecture", "5": "Built to scale, marginal cost near zero"}}
    ],
    "disqualifiers": [
        {"name": "Regulatory Impossibility", "description": "Solution violates healthcare regulations that cannot be navigated"},
        {"name": "Requires Hardware at Scale", "description": "Solution requires deploying custom hardware to every hospital — too capital intensive for a startup"}
    ]
}

async def setup_problem_with_solutions(client, auth_headers, mock_gemini):
    """Helper: full pipeline to solutions"""
    session = await client.post("/api/v1/sessions", json={
        "industry": "Healthcare", "location": "India", "maturity_level": "pre_production"
    }, headers=auth_headers)
    sid = session.json()["id"]
    mock_gemini.return_value = json.dumps({"pain_points": [
        {"name": "P", "description": "D", "severity": 5, "affected_stakeholders": ["U"], "evidence": "E"}
    ]})
    await client.post(f"/api/v1/sessions/{sid}/discover", headers=auth_headers)
    mock_gemini.return_value = json.dumps({"problem_statements": [
        {"title": "Queue System", "description": "Digital queue for hospitals", "target_user": "Hospitals",
         "core_pain": "Long waits", "market_context": "India healthcare $100B+",
         "severity": 4, "feasibility": 5, "market_size": 4, "uniqueness": 3}
    ]})
    problems = await client.post(f"/api/v1/sessions/{sid}/generate-problems", headers=auth_headers)
    pid = problems.json()[0]["id"]
    await client.post(f"/api/v1/problem-statements/{pid}/select", headers=auth_headers)
    mock_gemini.return_value = json.dumps({"solutions": [
        {"title": f"Sol {i+1}", "description": f"D{i}", "mechanism": f"M{i} unique",
         "tech_stack": [f"T{i}"], "target_user": "Users", "revenue_model": "SaaS",
         "is_unconventional": i == 4} for i in range(5)
    ]})
    await client.post(f"/api/v1/problem-statements/{pid}/generate-solutions", headers=auth_headers)
    return sid, pid

# TEST 1: Rubric prompt does NOT contain solution info
def test_rubric_prompt_no_solutions():
    """Rubric prompt must not contain any solution candidate data"""
    from backend.app.ai.prompts.evaluation.rubric import build_rubric_prompt
    from backend.app.core.maturity import get_maturity_config, MaturityLevel
    problem = {"title": "Queue System", "description": "Digital queue for hospitals",
               "target_user": "Hospitals", "core_pain": "Waits", "market_context": "India"}
    system, user = build_rubric_prompt(problem, get_maturity_config(MaturityLevel.MVP))
    combined = system + user
    assert "Sol " not in combined
    assert "solution 1" not in combined.lower()
    assert "candidate" not in user.lower()  # user prompt should not reference candidates

# TEST 2: Rubric prompt includes problem details
def test_rubric_prompt_includes_problem():
    """Rubric prompt should contain the problem statement"""
    from backend.app.ai.prompts.evaluation.rubric import build_rubric_prompt
    from backend.app.core.maturity import get_maturity_config, MaturityLevel
    problem = {"title": "Queue System", "description": "Digital queue for hospitals"}
    system, user = build_rubric_prompt(problem, get_maturity_config(MaturityLevel.MVP))
    assert "Queue System" in user

# TEST 3: Production rubric prompt requests security criteria
def test_production_rubric_includes_security():
    """Production maturity should request security and compliance criteria"""
    from backend.app.ai.prompts.evaluation.rubric import build_rubric_prompt
    from backend.app.core.maturity import get_maturity_config, MaturityLevel
    problem = {"title": "Test", "description": "Test"}
    system, _ = build_rubric_prompt(problem, get_maturity_config(MaturityLevel.PRODUCTION))
    assert "security" in system.lower() or "Security" in system
    assert "compliance" in system.lower() or "Compliance" in system

# TEST 4: Rubric schema validates correctly
def test_rubric_schema_valid():
    """RubricSchema should accept valid rubric data"""
    from backend.app.schemas.evaluation import RubricSchema
    rubric = RubricSchema(**MOCK_RUBRIC)
    assert len(rubric.criteria) == 4
    assert len(rubric.disqualifiers) == 2

# TEST 5: Rubric rejects fewer than 3 criteria
def test_rubric_rejects_too_few_criteria():
    """Rubric must have at least 3 criteria"""
    from backend.app.schemas.evaluation import RubricSchema
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        RubricSchema(criteria=[MOCK_RUBRIC["criteria"][0]], disqualifiers=MOCK_RUBRIC["disqualifiers"])

# TEST 6: Rubric rejects more than 6 criteria
def test_rubric_rejects_too_many_criteria():
    """Rubric must have at most 6 criteria"""
    from backend.app.schemas.evaluation import RubricSchema
    from pydantic import ValidationError
    many_criteria = [MOCK_RUBRIC["criteria"][0]] * 7
    with pytest.raises(ValidationError):
        RubricSchema(criteria=many_criteria, disqualifiers=MOCK_RUBRIC["disqualifiers"])

# TEST 7: Criterion scale must have keys 1, 3, 5
def test_criterion_scale_keys():
    """Each criterion must define what 1, 3, and 5 mean"""
    from backend.app.schemas.evaluation import RubricCriterion
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        RubricCriterion(name="Test", description="Test", weight=1, scale={"1": "bad", "5": "good"})  # missing "3"

# TEST 8: Generate rubric via API
async def test_generate_rubric_api(client, auth_headers, mock_gemini):
    """POST /evaluation/rubric should return a valid rubric"""
    _, pid = await setup_problem_with_solutions(client, auth_headers, mock_gemini)
    mock_gemini.return_value = json.dumps(MOCK_RUBRIC)
    response = await client.post(f"/api/v1/problem-statements/{pid}/evaluation/rubric", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "criteria" in data["rubric"] or "criteria" in data
    assert len(data.get("rubric", data).get("criteria", [])) >= 3

# TEST 9: Get rubric returns stored rubric
async def test_get_rubric(client, auth_headers, mock_gemini):
    """GET /evaluation/rubric should return the stored rubric"""
    _, pid = await setup_problem_with_solutions(client, auth_headers, mock_gemini)
    mock_gemini.return_value = json.dumps(MOCK_RUBRIC)
    await client.post(f"/api/v1/problem-statements/{pid}/evaluation/rubric", headers=auth_headers)
    response = await client.get(f"/api/v1/problem-statements/{pid}/evaluation/rubric", headers=auth_headers)
    assert response.status_code == 200

# TEST 10: Lock rubric prevents edits
async def test_lock_rubric(client, auth_headers, mock_gemini):
    """After locking, rubric edits should be rejected"""
    _, pid = await setup_problem_with_solutions(client, auth_headers, mock_gemini)
    mock_gemini.return_value = json.dumps(MOCK_RUBRIC)
    await client.post(f"/api/v1/problem-statements/{pid}/evaluation/rubric", headers=auth_headers)
    await client.post(f"/api/v1/problem-statements/{pid}/evaluation/rubric/lock", headers=auth_headers)
    edit_response = await client.patch(f"/api/v1/problem-statements/{pid}/evaluation/rubric", json={
        "criteria": MOCK_RUBRIC["criteria"][:3], "disqualifiers": MOCK_RUBRIC["disqualifiers"]
    }, headers=auth_headers)
    assert edit_response.status_code in [400, 403, 409]
