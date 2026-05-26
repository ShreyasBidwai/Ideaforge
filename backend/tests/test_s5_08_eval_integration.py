import pytest
import json

# Import mock data from previous tests
MOCK_RUBRIC = {
    "criteria": [
        {"name": "Feasibility", "description": "Can it be built?", "weight": 2.0, "scale": {"1": "No", "3": "Maybe", "5": "Yes"}},
        {"name": "Adoption", "description": "Will users adopt?", "weight": 2.5, "scale": {"1": "No", "3": "Some", "5": "Yes"}},
        {"name": "Revenue", "description": "Makes money?", "weight": 1.5, "scale": {"1": "No", "3": "Maybe", "5": "Yes"}}
    ],
    "disqualifiers": [{"name": "Illegal", "description": "Breaks laws"}, {"name": "Too expensive", "description": "Needs >$10M"}]
}

async def full_pipeline(client, auth_headers, mock_gemini, maturity="pre_production"):
    """Run entire pipeline from session to evaluation completion"""
    session = await client.post("/api/v1/sessions", json={
        "industry": "Healthcare", "location": "India", "maturity_level": maturity
    }, headers=auth_headers)
    sid = session.json()["id"]
    
    # Discover
    mock_gemini.return_value = json.dumps({"pain_points": [
        {"name": "Waits", "description": "Long waits", "severity": 8, "affected_stakeholders": ["Patients"], "evidence": "Data"}
    ]})
    await client.post(f"/api/v1/sessions/{sid}/discover", headers=auth_headers)
    
    # Problems
    mock_gemini.return_value = json.dumps({"problem_statements": [
        {"title": "Queue System", "description": "Digital queue", "target_user": "Hospitals",
         "core_pain": "Waits", "market_context": "India", "severity": 4, "feasibility": 5, "market_size": 4, "uniqueness": 3}
    ]})
    problems = await client.post(f"/api/v1/sessions/{sid}/generate-problems", headers=auth_headers)
    pid = problems.json()[0]["id"]
    await client.post(f"/api/v1/problem-statements/{pid}/select", headers=auth_headers)
    
    # Solutions
    mock_gemini.return_value = json.dumps({"solutions": [
        {"title": f"Sol {i+1}", "description": f"D{i}", "mechanism": f"Unique mech {i}",
         "tech_stack": [f"T{i}"], "target_user": "Users", "revenue_model": "SaaS",
         "is_unconventional": i == 4} for i in range(5)
    ]})
    await client.post(f"/api/v1/problem-statements/{pid}/generate-solutions", headers=auth_headers)
    
    return sid, pid

# TEST 1: Complete pre-production evaluation pipeline
async def test_full_pre_production_pipeline(client, auth_headers, mock_gemini):
    """Full 8-step evaluation should complete for pre_production maturity"""
    sid, pid = await full_pipeline(client, auth_headers, mock_gemini, "pre_production")
    
    # Rubric
    mock_gemini.return_value = json.dumps(MOCK_RUBRIC)
    r = await client.post(f"/api/v1/problem-statements/{pid}/evaluation/rubric", headers=auth_headers)
    assert r.status_code == 200
    await client.post(f"/api/v1/problem-statements/{pid}/evaluation/rubric/lock", headers=auth_headers)
    
    # Disqualify
    mock_gemini.return_value = json.dumps({"results": [
        {"solution_title": f"Sol {i+1}", "passed": i != 2, "failed_disqualifiers": ["Too expensive"] if i == 2 else [], "reasons": ["Needs hardware"] if i == 2 else []}
        for i in range(5)
    ]})
    r = await client.post(f"/api/v1/problem-statements/{pid}/evaluation/disqualify", headers=auth_headers)
    assert r.status_code == 200
    
    # Score
    mock_gemini.return_value = json.dumps({"scores": [
        {"solution_title": f"Sol {i+1}", "criterion_scores": [
            {"criterion": "Feasibility", "score": 4-i%2, "justification": "J"},
            {"criterion": "Adoption", "score": 3+i%2, "justification": "J"},
            {"criterion": "Revenue", "score": 3, "justification": "J"}
        ], "weighted_avg": 3.5, "min_score": 3}
        for i in range(5) if i != 2
    ]})
    r = await client.post(f"/api/v1/problem-statements/{pid}/evaluation/score", headers=auth_headers)
    assert r.status_code == 200
    
    # Attack
    mock_gemini.return_value = json.dumps({"attacks": [
        {"solution_title": f"Sol {i+1}", "attack": f"Attack on sol {i+1}", "severity": "medium",
         "survives": i % 2 == 0, "survival_reasoning": "Reasoning"}
        for i in range(5) if i != 2
    ]})
    r = await client.post(f"/api/v1/problem-statements/{pid}/evaluation/attack", headers=auth_headers)
    assert r.status_code == 200
    
    # ACH
    mock_gemini.return_value = json.dumps({"analysis": [
        {"solution_title": f"Sol {i+1}", "inconsistencies": [f"Issue {j}" for j in range(i)], "count": i}
        for i in range(5) if i != 2
    ]})
    r = await client.post(f"/api/v1/problem-statements/{pid}/evaluation/ach", headers=auth_headers)
    assert r.status_code == 200
    
    # Compare
    r = await client.post(f"/api/v1/problem-statements/{pid}/evaluation/compare", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "entries" in data
    assert "leaders" in data
    assert "is_clear_winner" in data
    
    # Session should be completed
    session = await client.get(f"/api/v1/sessions/{sid}", headers=auth_headers)
    assert session.json()["status"] == "completed"

# TEST 2: POC pipeline skips attack and ACH
async def test_poc_pipeline_skips_steps(client, auth_headers, mock_gemini):
    """POC should complete without requiring attack and ACH steps"""
    sid, pid = await full_pipeline(client, auth_headers, mock_gemini, "poc")
    
    mock_gemini.return_value = json.dumps(MOCK_RUBRIC)
    await client.post(f"/api/v1/problem-statements/{pid}/evaluation/rubric", headers=auth_headers)
    await client.post(f"/api/v1/problem-statements/{pid}/evaluation/rubric/lock", headers=auth_headers)
    
    mock_gemini.return_value = json.dumps({"results": [
        {"solution_title": f"Sol {i+1}", "passed": True, "failed_disqualifiers": [], "reasons": []}
        for i in range(3)  # POC has 3 solutions
    ]})
    await client.post(f"/api/v1/problem-statements/{pid}/evaluation/disqualify", headers=auth_headers)
    
    mock_gemini.return_value = json.dumps({"scores": [
        {"solution_title": f"Sol {i+1}", "criterion_scores": [
            {"criterion": "Feasibility", "score": 4, "justification": "J"},
            {"criterion": "Adoption", "score": 3, "justification": "J"},
            {"criterion": "Revenue", "score": 3, "justification": "J"}
        ], "weighted_avg": 3.5, "min_score": 3}
        for i in range(3)
    ]})
    await client.post(f"/api/v1/problem-statements/{pid}/evaluation/score", headers=auth_headers)
    
    # Skip attack and ACH, go straight to compare
    r = await client.post(f"/api/v1/problem-statements/{pid}/evaluation/compare", headers=auth_headers)
    assert r.status_code == 200

# TEST 3: Approve solution after evaluation
async def test_approve_after_evaluation(client, auth_headers, mock_gemini):
    """Should be able to approve a solution after full evaluation"""
    _, pid = await full_pipeline(client, auth_headers, mock_gemini)
    # Run abbreviated eval
    mock_gemini.return_value = json.dumps(MOCK_RUBRIC)
    await client.post(f"/api/v1/problem-statements/{pid}/evaluation/rubric", headers=auth_headers)
    await client.post(f"/api/v1/problem-statements/{pid}/evaluation/rubric/lock", headers=auth_headers)
    mock_gemini.return_value = json.dumps({"results": [
        {"solution_title": f"Sol {i+1}", "passed": True, "failed_disqualifiers": [], "reasons": []} for i in range(5)
    ]})
    await client.post(f"/api/v1/problem-statements/{pid}/evaluation/disqualify", headers=auth_headers)
    
    # Get solutions and approve one
    solutions = await client.get(f"/api/v1/problem-statements/{pid}/solutions", headers=auth_headers)
    sol_id = solutions.json()[0]["id"]
    r = await client.post(f"/api/v1/solutions/{sol_id}/approve", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "approved"

# TEST 4: Full evaluation endpoint returns all data
async def test_full_evaluation_data(client, auth_headers, mock_gemini):
    """GET /evaluation should return complete data after full run"""
    _, pid = await full_pipeline(client, auth_headers, mock_gemini)
    mock_gemini.return_value = json.dumps(MOCK_RUBRIC)
    await client.post(f"/api/v1/problem-statements/{pid}/evaluation/rubric", headers=auth_headers)
    await client.post(f"/api/v1/problem-statements/{pid}/evaluation/rubric/lock", headers=auth_headers)
    
    response = await client.get(f"/api/v1/problem-statements/{pid}/evaluation", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "rubric" in data
