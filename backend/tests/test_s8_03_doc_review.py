import pytest
import json

# Helper to create an approved solution for API endpoint tests
async def create_approved_solution(client, auth_headers, mock_gemini):
    """Helper: create full pipeline and approve a solution"""
    session = await client.post("/api/v1/sessions", json={
        "industry": "Healthcare", "location": "India"
    }, headers=auth_headers)
    sid = session.json()["id"]
    mock_gemini.return_value = json.dumps({"pain_points": [
        {"name": "P", "description": "D", "severity": 5, "affected_stakeholders": ["U"], "evidence": "E"}
    ]})
    await client.post(f"/api/v1/sessions/{sid}/discover", headers=auth_headers)
    mock_gemini.return_value = json.dumps({"problem_statements": [
        {"title": "Problem", "description": "D", "target_user": "U", "core_pain": "P", "market_context": "M",
         "severity": 4, "feasibility": 4, "market_size": 4, "uniqueness": 3}
    ]})
    problems = await client.post(f"/api/v1/sessions/{sid}/generate-problems", headers=auth_headers)
    pid = problems.json()[0]["id"]
    await client.post(f"/api/v1/problem-statements/{pid}/select", headers=auth_headers)
    mock_gemini.return_value = json.dumps({"solutions": [
        {"title": "Approved Sol", "description": "D", "mechanism": "M", "tech_stack": ["React"],
         "target_user": "Users", "revenue_model": "SaaS $99/mo", "is_unconventional": False}
    ]})
    solutions = await client.post(f"/api/v1/problem-statements/{pid}/generate-solutions", headers=auth_headers)
    sol_id = solutions.json()[0]["id"]
    await client.post(f"/api/v1/solutions/{sol_id}/approve", headers=auth_headers)
    return sol_id

# TEST 1: Update document content
@pytest.mark.anyio
async def test_update_document(client, auth_headers, mock_gemini):
    """PATCH /documents/{doc_id} should update content"""
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    project = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    proj_id = project.json()["id"]
    mock_gemini.return_value = "# Original doc content"
    await client.post(f"/api/v1/projects/{proj_id}/generate-docs", headers=auth_headers)
    
    docs = await client.get(f"/api/v1/projects/{proj_id}/documents", headers=auth_headers)
    doc_id = docs.json()[0]["id"]
    
    response = await client.patch(f"/api/v1/projects/{proj_id}/documents/{doc_id}", json={
        "content": "# Updated architecture\n\nNew content here."
    }, headers=auth_headers)
    assert response.status_code == 200
    assert "Updated architecture" in response.json()["content"]

# TEST 2: Approve single document
@pytest.mark.anyio
async def test_approve_document(client, auth_headers, mock_gemini):
    """POST /documents/{doc_id}/approve should set status to approved"""
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    project = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    proj_id = project.json()["id"]
    mock_gemini.return_value = "# Doc"
    await client.post(f"/api/v1/projects/{proj_id}/generate-docs", headers=auth_headers)
    
    docs = await client.get(f"/api/v1/projects/{proj_id}/documents", headers=auth_headers)
    doc_id = docs.json()[0]["id"]
    
    response = await client.post(f"/api/v1/projects/{proj_id}/documents/{doc_id}/approve", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "approved"

# TEST 3: Approve all documents
@pytest.mark.anyio
async def test_approve_all_documents(client, auth_headers, mock_gemini):
    """POST /documents/approve-all should approve all 5 docs"""
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    project = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    proj_id = project.json()["id"]
    mock_gemini.return_value = "# Doc"
    await client.post(f"/api/v1/projects/{proj_id}/generate-docs", headers=auth_headers)
    
    response = await client.post(f"/api/v1/projects/{proj_id}/documents/approve-all", headers=auth_headers)
    assert response.status_code == 200
    
    docs = await client.get(f"/api/v1/projects/{proj_id}/documents", headers=auth_headers)
    assert all(d["status"] == "approved" for d in docs.json())

# TEST 4: Edit task prompt
@pytest.mark.anyio
async def test_edit_task_prompt(client, auth_headers, mock_gemini):
    """PATCH /tasks/{task_id}/prompt should update the prompt"""
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    project = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    proj_id = project.json()["id"]
    mock_gemini.return_value = "# Doc"
    await client.post(f"/api/v1/projects/{proj_id}/generate-docs", headers=auth_headers)
    
    from tests.test_s7_03_sprint_generation import MOCK_SPRINTS
    mock_gemini.return_value = json.dumps(MOCK_SPRINTS)
    await client.post(f"/api/v1/projects/{proj_id}/generate-sprints", headers=auth_headers)
    
    sprints = await client.get(f"/api/v1/projects/{proj_id}/sprints", headers=auth_headers)
    tasks = await client.get(f"/api/v1/projects/{proj_id}/sprints/{sprints.json()[0]['id']}/tasks", headers=auth_headers)
    task_id = tasks.json()[0]["id"]
    
    response = await client.patch(f"/api/v1/tasks/{task_id}/prompt", json={
        "prompt": "Updated prompt content with more detail..."
    }, headers=auth_headers)
    assert response.status_code == 200
    assert "Updated prompt" in response.json()["prompt"]

# TEST 5: Cannot start build without approved docs
@pytest.mark.anyio
async def test_build_requires_approved_docs(client, auth_headers, mock_gemini):
    """POST /approve-and-build should fail if docs not all approved"""
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    project = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    proj_id = project.json()["id"]
    mock_gemini.return_value = "# Doc"
    await client.post(f"/api/v1/projects/{proj_id}/generate-docs", headers=auth_headers)
    # Don't approve docs
    from tests.test_s7_03_sprint_generation import MOCK_SPRINTS
    mock_gemini.return_value = json.dumps(MOCK_SPRINTS)
    await client.post(f"/api/v1/projects/{proj_id}/generate-sprints", headers=auth_headers)
    
    response = await client.post(f"/api/v1/projects/{proj_id}/approve-and-build", headers=auth_headers)
    assert response.status_code in [400, 422]
