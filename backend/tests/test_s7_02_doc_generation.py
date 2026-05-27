import pytest
import json
from tests.test_s6_02_approvals import create_approved_solution

# TEST 1: Create project from approved solution
async def test_create_project(client, auth_headers, mock_gemini):
    """POST /solutions/{id}/create-project should create a project"""
    # Setup: create full pipeline and approve a solution
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    response = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    assert response.status_code in [200, 201]
    data = response.json()
    assert data["status"] == "doc_generation"
    assert data["solution_id"] == sol_id
    assert data["tech_stack"] is not None

# TEST 2: Cannot create project for non-approved solution
async def test_create_project_requires_approved(client, auth_headers, mock_gemini):
    """Should fail if solution is not approved"""
    session = await client.post("/api/v1/sessions", json={
        "industry": "Healthcare", "location": "India"
    }, headers=auth_headers)
    sid = session.json()["id"]
    mock_gemini.return_value = json.dumps({"pain_points": [
        {"name": "P", "description": "D", "severity": 5, "affected_stakeholders": ["U"], "evidence": "E"}
    ]})
    await client.post(f"/api/v1/sessions/{sid}/discover", headers=auth_headers)
    mock_gemini.return_value = json.dumps({"problem_statements": [
        {"title": "T", "description": "D", "target_user": "U", "core_pain": "P", "market_context": "M",
         "severity": 3, "feasibility": 3, "market_size": 3, "uniqueness": 3}
    ]})
    problems = await client.post(f"/api/v1/sessions/{sid}/generate-problems", headers=auth_headers)
    pid = problems.json()[0]["id"]
    await client.post(f"/api/v1/problem-statements/{pid}/select", headers=auth_headers)
    mock_gemini.return_value = json.dumps({"solutions": [
        {"title": "Sol", "description": "D", "mechanism": "M", "tech_stack": ["React"],
         "target_user": "Users", "revenue_model": "SaaS", "is_unconventional": False}
    ]})
    solutions = await client.post(f"/api/v1/problem-statements/{pid}/generate-solutions", headers=auth_headers)
    sol_id = solutions.json()[0]["id"]
    # NOT approving
    response = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    assert response.status_code in [400, 422]

# TEST 3: Generate docs creates 5 documents
async def test_generate_docs(client, auth_headers, mock_gemini):
    """POST /projects/{id}/generate-docs should create 5 documents"""
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    project = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    proj_id = project.json()["id"]
    
    # Mock Gemini to return markdown content for each doc
    mock_gemini.return_value = "# Architecture Document\n\nThis is the architecture for the solution.\n\n## System Overview\n\nThe system uses React + FastAPI..."
    
    response = await client.post(f"/api/v1/projects/{proj_id}/generate-docs", headers=auth_headers)
    assert response.status_code == 200
    
    docs = await client.get(f"/api/v1/projects/{proj_id}/documents", headers=auth_headers)
    assert len(docs.json()) == 5
    doc_types = {d["doc_type"] for d in docs.json()}
    assert doc_types == {"architecture", "prd", "trd", "sprint_plan", "engineering_standards"}

# TEST 4: Document content is not empty
async def test_doc_content_not_empty(client, auth_headers, mock_gemini):
    """Generated documents should have actual content"""
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    project = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    proj_id = project.json()["id"]
    mock_gemini.return_value = "# PRD\n\n## Product Vision\n\nDetailed product vision content here."
    await client.post(f"/api/v1/projects/{proj_id}/generate-docs", headers=auth_headers)
    
    docs = await client.get(f"/api/v1/projects/{proj_id}/documents", headers=auth_headers)
    for doc in docs.json():
        assert len(doc["content"]) > 50

# TEST 5: List projects
async def test_list_projects(client, auth_headers, mock_gemini):
    """GET /projects should list user's projects"""
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    response = await client.get("/api/v1/projects", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) >= 1

# TEST 6: Architecture prompt includes tech stack
def test_architecture_prompt_includes_tech():
    """Architecture prompt should reference the solution's tech stack"""
    from app.ai.prompts.docs.architecture import build_architecture_prompt
    context = {
        "solution": {"title": "Queue System", "description": "Digital queue", "mechanism": "ML-based",
                     "tech_stack": ["React", "FastAPI", "PostgreSQL"], "target_user": "Hospitals", "revenue_model": "SaaS"},
        "problem": {"title": "Wait times", "description": "Long waits"},
        "session": {"industry": "Healthcare", "location": "India", "maturity_level": "mvp"},
    }
    system, user = build_architecture_prompt(context)
    combined = system + user
    assert "React" in combined
    assert "FastAPI" in combined
    assert "PostgreSQL" in combined

# TEST 7: Project requires auth
async def test_project_requires_auth(client):
    response = await client.get("/api/v1/projects")
    assert response.status_code in [401, 403]

# TEST 8: Prompt templates exist for all doc types
def test_all_prompt_templates_exist():
    """All 5 doc type prompt builders should be importable"""
    from app.ai.prompts.docs.architecture import build_architecture_prompt
    from app.ai.prompts.docs.prd import build_prd_prompt
    from app.ai.prompts.docs.trd import build_trd_prompt
    from app.ai.prompts.docs.sprint_plan import build_sprint_plan_prompt
    from app.ai.prompts.docs.engineering import build_engineering_prompt
    assert all([build_architecture_prompt, build_prd_prompt, build_trd_prompt, build_sprint_plan_prompt, build_engineering_prompt])
