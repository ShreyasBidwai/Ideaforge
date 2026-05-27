import pytest
import json
from tests.test_s7_03_sprint_generation import MOCK_SPRINTS
from tests.test_s6_02_approvals import create_approved_solution

# TEST 1: Complete Phase 2 preparation pipeline
@pytest.mark.anyio
async def test_complete_phase2_prep(client, auth_headers, mock_gemini):
    """Full pipeline: approve → project → docs → review → sprints → validate → ready to build"""
    # Approve solution
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    
    # Create project
    project = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    proj_id = project.json()["id"]
    
    # Generate docs
    mock_gemini.return_value = "# Architecture\n\n## Overview\n\nDetailed arch doc."
    await client.post(f"/api/v1/projects/{proj_id}/generate-docs", headers=auth_headers)
    
    # Verify 5 docs created
    docs = await client.get(f"/api/v1/projects/{proj_id}/documents", headers=auth_headers)
    assert len(docs.json()) == 5
    
    # Edit a document
    doc_id = docs.json()[0]["id"]
    await client.patch(f"/api/v1/projects/{proj_id}/documents/{doc_id}", json={
        "content": "# Updated Architecture\n\nBetter content."
    }, headers=auth_headers)
    
    # Approve all docs
    await client.post(f"/api/v1/projects/{proj_id}/documents/approve-all", headers=auth_headers)
    
    # Generate sprints
    mock_gemini.return_value = json.dumps(MOCK_SPRINTS)
    await client.post(f"/api/v1/projects/{proj_id}/generate-sprints", headers=auth_headers)
    
    # Validate prompts
    validation = await client.post(f"/api/v1/projects/{proj_id}/validate-prompts", headers=auth_headers)
    assert validation.status_code == 200
    assert "total_tasks" in validation.json()
    
    # Project should be ready for build
    proj = await client.get(f"/api/v1/projects/{proj_id}", headers=auth_headers)
    assert proj.json()["status"] == "doc_review"
    
    # Files endpoint should work
    files = await client.get(f"/api/v1/projects/{proj_id}/files", headers=auth_headers)
    assert files.status_code == 200
    
    # Build status should be available
    status = await client.get(f"/api/v1/projects/{proj_id}/build/status", headers=auth_headers)
    assert status.status_code == 200

# TEST 2: Multiple projects are independent
@pytest.mark.anyio
async def test_independent_projects(client, auth_headers, mock_gemini):
    """Two projects should not interfere with each other"""
    sol1 = await create_approved_solution(client, auth_headers, mock_gemini)
    sol2 = await create_approved_solution(client, auth_headers, mock_gemini)
    
    p1 = await client.post(f"/api/v1/solutions/{sol1}/create-project", headers=auth_headers)
    p2 = await client.post(f"/api/v1/solutions/{sol2}/create-project", headers=auth_headers)
    
    assert p1.json()["id"] != p2.json()["id"]
    
    projects = await client.get("/api/v1/projects", headers=auth_headers)
    assert len(projects.json()) >= 2

# TEST 3: Queue handles multiple builds
@pytest.mark.anyio
async def test_queue_multiple_builds(client, auth_headers, mock_gemini):
    """Multiple build requests should be queued"""
    queue = await client.get("/api/v1/build-queue", headers=auth_headers)
    assert queue.status_code == 200
    assert "total_in_queue" in queue.json()

# TEST 4: Claude status is accessible
@pytest.mark.anyio
async def test_claude_accessible(client, auth_headers):
    """Claude status check should work"""
    response = await client.get("/api/v1/setup/claude-status", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "is_installed" in data

# TEST 5: Output parser handles real-world patterns
def test_parser_real_world():
    """Parser should handle realistic Claude output"""
    from backend.app.services.claude_service import ClaudeOutputParser
    # Simulated real claude output with ANSI codes and mixed content
    output = "\x1b[32m✓\x1b[0m Created backend/app/main.py\n\x1b[32m✓\x1b[0m Modified backend/app/core/config.py\n\n\x1b[33m⚠\x1b[0m Warning: file already exists, overwriting\n\nDone! Created 2 files."
    cleaned = ClaudeOutputParser.clean_output(output)
    assert "\x1b" not in cleaned
    files = ClaudeOutputParser.extract_files_created(cleaned)
    assert len(files) >= 2
