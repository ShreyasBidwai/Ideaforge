import pytest
import json
from tests.test_s6_02_approvals import create_approved_solution
from tests.test_s7_03_sprint_generation import MOCK_SPRINTS

# TEST 1: Full flow — approve solution → create project → generate docs → generate sprints
async def test_phase2_full_flow(client, auth_headers, mock_gemini):
    """Complete Phase 2 preparation flow"""
    # Approve solution
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    
    # Create project
    project = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    assert project.status_code in [200, 201]
    proj_id = project.json()["id"]
    assert project.json()["status"] == "doc_generation"
    
    # Generate docs
    mock_gemini.return_value = "# Generated documentation content\n\n## Overview\n\nDetailed content here."
    await client.post(f"/api/v1/projects/{proj_id}/generate-docs", headers=auth_headers)
    docs = await client.get(f"/api/v1/projects/{proj_id}/documents", headers=auth_headers)
    assert len(docs.json()) == 5
    
    # Approve all docs
    await client.post(f"/api/v1/projects/{proj_id}/documents/approve-all", headers=auth_headers)
    
    # Generate sprints
    mock_gemini.return_value = json.dumps(MOCK_SPRINTS)
    await client.post(f"/api/v1/projects/{proj_id}/generate-sprints", headers=auth_headers)
    sprints = await client.get(f"/api/v1/projects/{proj_id}/sprints", headers=auth_headers)
    assert len(sprints.json()) >= 2
    
    # Project should be in doc_review status
    proj = await client.get(f"/api/v1/projects/{proj_id}", headers=auth_headers)
    assert proj.json()["status"] == "doc_review"

# TEST 2: Project has correct context from solution
async def test_project_inherits_context(client, auth_headers, mock_gemini):
    """Project should carry industry, location, tech_stack from solution/session"""
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    project = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    data = project.json()
    assert data["industry"] is not None
    assert data["tech_stack"] is not None
    assert len(data["tech_stack"]) > 0

# TEST 3: Cannot create duplicate project for same solution
async def test_no_duplicate_project(client, auth_headers, mock_gemini):
    """Should not allow two projects for the same solution"""
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    response = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    assert response.status_code in [400, 409]

# TEST 4: Claude status check works
async def test_claude_status_in_flow(client, auth_headers):
    """Setup status should be checkable"""
    response = await client.get("/api/v1/setup/claude-status", headers=auth_headers)
    assert response.status_code == 200
    assert "is_installed" in response.json()

# TEST 5: File browser works after project creation
async def test_file_access(client, auth_headers, mock_gemini):
    """Should be able to browse project files after creation"""
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    project = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    proj_id = project.json()["id"]
    response = await client.get(f"/api/v1/projects/{proj_id}/files", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["type"] == "directory"
