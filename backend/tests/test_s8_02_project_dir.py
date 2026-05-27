import pytest
import os
import tempfile
import json
from datetime import datetime, timedelta

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

# TEST 1: Sanitize name
def test_sanitize_name():
    from app.services.project_dir_service import ProjectDirService
    assert ProjectDirService.sanitize_name("Digital Queue System!") == "digital-queue-system"
    assert ProjectDirService.sanitize_name("  My App  ") == "my-app"
    assert ProjectDirService.sanitize_name("App@#$%123") == "app123"

# TEST 2: Create project directory
def test_create_project_dir():
    from app.services.project_dir_service import ProjectDirService
    with tempfile.TemporaryDirectory() as tmp:
        ProjectDirService.BASE_DIR = tmp
        path = ProjectDirService.create_project_dir("abc123", "Test Project")
        assert os.path.isdir(path)
        assert os.path.isfile(os.path.join(path, "README.md"))
        assert os.path.isdir(os.path.join(path, ".git"))

# TEST 3: Create is idempotent
def test_create_idempotent():
    from app.services.project_dir_service import ProjectDirService
    with tempfile.TemporaryDirectory() as tmp:
        ProjectDirService.BASE_DIR = tmp
        path1 = ProjectDirService.create_project_dir("abc", "Test")
        path2 = ProjectDirService.create_project_dir("abc", "Test")
        assert path1 == path2

# TEST 4: Get directory structure
def test_get_structure():
    from app.services.project_dir_service import ProjectDirService
    with tempfile.TemporaryDirectory() as tmp:
        ProjectDirService.BASE_DIR = tmp
        path = ProjectDirService.create_project_dir("xyz", "Test")
        os.makedirs(os.path.join(path, "backend", "app"), exist_ok=True)
        with open(os.path.join(path, "backend", "app", "main.py"), "w") as f:
            f.write("# main")
        structure = ProjectDirService.get_project_structure(path)
        assert structure["type"] == "directory"
        assert any(c["name"] == "backend" for c in structure["children"])

# TEST 5: Get file content
def test_get_file_content():
    from app.services.project_dir_service import ProjectDirService
    with tempfile.TemporaryDirectory() as tmp:
        ProjectDirService.BASE_DIR = tmp
        path = ProjectDirService.create_project_dir("filetest", "Test")
        with open(os.path.join(path, "test.txt"), "w") as f:
            f.write("hello world")
        content = ProjectDirService.get_file_content(path, "test.txt")
        assert content == "hello world"

# TEST 6: Path traversal blocked
def test_path_traversal_blocked():
    from app.services.project_dir_service import ProjectDirService
    with tempfile.TemporaryDirectory() as tmp:
        ProjectDirService.BASE_DIR = tmp
        path = ProjectDirService.create_project_dir("secure", "Test")
        content = ProjectDirService.get_file_content(path, "../../etc/passwd")
        assert content is None

# TEST 7: Delete project directory
def test_delete_project_dir():
    from app.services.project_dir_service import ProjectDirService
    with tempfile.TemporaryDirectory() as tmp:
        ProjectDirService.BASE_DIR = tmp
        path = ProjectDirService.create_project_dir("del", "Test")
        assert os.path.isdir(path)
        ProjectDirService.delete_project_dir(path)
        assert not os.path.isdir(path)

# TEST 8: Create zip
def test_create_zip():
    from app.services.project_dir_service import ProjectDirService
    with tempfile.TemporaryDirectory() as tmp:
        ProjectDirService.BASE_DIR = tmp
        path = ProjectDirService.create_project_dir("ziptest", "Test")
        with open(os.path.join(path, "app.py"), "w") as f:
            f.write("print('hello')")
        zip_path = ProjectDirService.create_zip(path)
        assert os.path.isfile(zip_path)
        assert zip_path.endswith(".zip")

# TEST 9: Files API endpoint
@pytest.mark.anyio
async def test_files_endpoint(client, auth_headers, mock_gemini):
    """GET /projects/{id}/files should return directory tree"""
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    project = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    proj_id = project.json()["id"]
    response = await client.get(f"/api/v1/projects/{proj_id}/files", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "directory"

# TEST 10: Download endpoint
@pytest.mark.anyio
async def test_download_endpoint(client, auth_headers, mock_gemini):
    """GET /projects/{id}/download should return zip file"""
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    project = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    proj_id = project.json()["id"]
    response = await client.get(f"/api/v1/projects/{proj_id}/download", headers=auth_headers)
    assert response.status_code == 200
    assert "zip" in response.headers.get("content-type", "") or "octet-stream" in response.headers.get("content-type", "")
