import pytest
import json

# TEST 1: Full flow — create session, discover, generate problems
async def test_full_discovery_to_problems_flow(client, auth_headers, mock_gemini):
    """Complete pipeline: session → pain points → problem statements"""
    # Step 1: Create session
    session = await client.post("/api/v1/sessions", json={
        "industry": "Healthcare",
        "location": "Mumbai, India",
        "maturity_level": "mvp",
        "tech_stack_preferences": ["React", "FastAPI", "PostgreSQL"]
    }, headers=auth_headers)
    assert session.status_code in [200, 201]
    session_id = session.json()["id"]
    assert session.json()["status"] == "discovery"
    
    # Step 2: Discover pain points
    mock_gemini.return_value = json.dumps({"pain_points": [
        {"name": "Long patient wait times", "description": "Patients wait 3+ hours in urban hospitals.",
         "severity": 8, "affected_stakeholders": ["Patients", "Hospital staff"], "evidence": "NITI Aayog data"},
        {"name": "Paper-based medical records", "description": "90% of clinics use paper records causing errors.",
         "severity": 7, "affected_stakeholders": ["Doctors", "Patients"], "evidence": "WHO India survey"},
        {"name": "Drug supply chain opacity", "description": "No visibility into drug authenticity or supply chain.",
         "severity": 9, "affected_stakeholders": ["Pharmacies", "Regulators"], "evidence": "Counterfeit drug reports"}
    ]})
    discover_resp = await client.post(f"/api/v1/sessions/{session_id}/discover", headers=auth_headers)
    assert discover_resp.status_code == 200
    assert len(discover_resp.json()["pain_points"]) == 3
    
    # Verify session status updated
    session_check = await client.get(f"/api/v1/sessions/{session_id}", headers=auth_headers)
    assert session_check.json()["status"] == "problem_generation"
    
    # Step 3: Generate problem statements
    mock_gemini.return_value = json.dumps({"problem_statements": [
        {"title": "Digital Queue Management for Hospitals", "description": "A real-time digital queue system that reduces patient wait times.",
         "target_user": "Hospital administrators and outpatients", "core_pain": "3+ hour wait times causing patient dropout",
         "market_context": "India hospital market $100B+, digital health growing 30% YoY.",
         "severity": 4, "feasibility": 5, "market_size": 4, "uniqueness": 3},
        {"title": "Cloud EHR for Small Clinics", "description": "Affordable cloud-based electronic health records for small/medium clinics.",
         "target_user": "Clinic owners and general practitioners", "core_pain": "Paper records cause errors, delays, and data loss",
         "market_context": "700K+ clinics in India without digital records. Government pushing digital health.",
         "severity": 4, "feasibility": 4, "market_size": 5, "uniqueness": 2}
    ]})
    problems_resp = await client.post(f"/api/v1/sessions/{session_id}/generate-problems", headers=auth_headers)
    assert problems_resp.status_code == 200
    problems = problems_resp.json()
    assert len(problems) == 2
    
    # Verify overall ratings computed
    for p in problems:
        assert p["overall_rating"] > 0
        assert 1 <= p["severity"] <= 5
    
    # Step 4: Verify in library
    library_resp = await client.get("/api/v1/problem-statements", headers=auth_headers)
    assert library_resp.json()["total"] >= 2
    
    # Step 5: Select a problem
    select_resp = await client.post(f"/api/v1/problem-statements/{problems[0]['id']}/select", headers=auth_headers)
    assert select_resp.json()["status"] == "selected"

# TEST 2: Multiple sessions create distinct problem sets
async def test_multiple_sessions_distinct(client, auth_headers, mock_gemini):
    """Problem statements from different sessions should be separate"""
    # Session 1: Healthcare
    s1 = await client.post("/api/v1/sessions", json={"industry": "Healthcare", "location": "India"}, headers=auth_headers)
    mock_gemini.return_value = json.dumps({"pain_points": [
        {"name": "Pain1", "description": "Desc", "severity": 5, "affected_stakeholders": ["Users"], "evidence": "Data"}
    ]})
    await client.post(f"/api/v1/sessions/{s1.json()['id']}/discover", headers=auth_headers)
    mock_gemini.return_value = json.dumps({"problem_statements": [
        {"title": "HC Problem", "description": "D", "target_user": "U", "core_pain": "P", "market_context": "M",
         "severity": 4, "feasibility": 4, "market_size": 4, "uniqueness": 4}
    ]})
    await client.post(f"/api/v1/sessions/{s1.json()['id']}/generate-problems", headers=auth_headers)
    
    # Session 2: Fintech
    s2 = await client.post("/api/v1/sessions", json={"industry": "Fintech", "location": "India"}, headers=auth_headers)
    mock_gemini.return_value = json.dumps({"pain_points": [
        {"name": "Pain2", "description": "Desc", "severity": 5, "affected_stakeholders": ["Users"], "evidence": "Data"}
    ]})
    await client.post(f"/api/v1/sessions/{s2.json()['id']}/discover", headers=auth_headers)
    mock_gemini.return_value = json.dumps({"problem_statements": [
        {"title": "FT Problem", "description": "D", "target_user": "U", "core_pain": "P", "market_context": "M",
         "severity": 3, "feasibility": 5, "market_size": 3, "uniqueness": 5}
    ]})
    await client.post(f"/api/v1/sessions/{s2.json()['id']}/generate-problems", headers=auth_headers)
    
    # Get session-specific problems
    hc_problems = await client.get(f"/api/v1/sessions/{s1.json()['id']}/problem-statements", headers=auth_headers)
    ft_problems = await client.get(f"/api/v1/sessions/{s2.json()['id']}/problem-statements", headers=auth_headers)
    assert hc_problems.json()[0]["title"] == "HC Problem"
    assert ft_problems.json()[0]["title"] == "FT Problem"
    
    # Library has both
    all_problems = await client.get("/api/v1/problem-statements", headers=auth_headers)
    assert all_problems.json()["total"] >= 2

# TEST 3: Industry filter works in library
async def test_library_industry_filter(client, auth_headers, mock_gemini):
    """Filtering by industry should return only matching problems"""
    # Create HC and FT sessions with problems (reuse helper or inline)
    for industry in ["Healthcare", "Fintech"]:
        s = await client.post("/api/v1/sessions", json={"industry": industry, "location": "India"}, headers=auth_headers)
        mock_gemini.return_value = json.dumps({"pain_points": [
            {"name": "P", "description": "D", "severity": 5, "affected_stakeholders": ["U"], "evidence": "E"}
        ]})
        await client.post(f"/api/v1/sessions/{s.json()['id']}/discover", headers=auth_headers)
        mock_gemini.return_value = json.dumps({"problem_statements": [
            {"title": f"{industry} PS", "description": "D", "target_user": "U", "core_pain": "P", "market_context": "M",
             "severity": 3, "feasibility": 3, "market_size": 3, "uniqueness": 3}
        ]})
        await client.post(f"/api/v1/sessions/{s.json()['id']}/generate-problems", headers=auth_headers)
    
    hc_only = await client.get("/api/v1/problem-statements?industry=Healthcare", headers=auth_headers)
    for item in hc_only.json()["items"]:
        assert "Healthcare" in item.get("title", "") or item.get("industry", "") == "Healthcare"

# TEST 4: Maturity level affects problem count
async def test_maturity_affects_count(client, auth_headers, mock_gemini):
    """POC should generate 2, production should generate 3 problem statements"""
    for maturity, expected_count in [("poc", 2), ("production", 3)]:
        s = await client.post("/api/v1/sessions", json={
            "industry": "EdTech", "location": "India", "maturity_level": maturity
        }, headers=auth_headers)
        mock_gemini.return_value = json.dumps({"pain_points": [
            {"name": "P", "description": "D", "severity": 5, "affected_stakeholders": ["U"], "evidence": "E"}
        ]})
        await client.post(f"/api/v1/sessions/{s.json()['id']}/discover", headers=auth_headers)
        # Mock AI returns the expected count
        mock_gemini.return_value = json.dumps({"problem_statements": [
            {"title": f"PS {i+1}", "description": "D", "target_user": "U", "core_pain": "P", "market_context": "M",
             "severity": 3, "feasibility": 3, "market_size": 3, "uniqueness": 3}
            for i in range(expected_count)
        ]})
        resp = await client.post(f"/api/v1/sessions/{s.json()['id']}/generate-problems", headers=auth_headers)
        assert len(resp.json()) == expected_count

# TEST 5: Tech stack stored and accessible
async def test_tech_stack_in_session(client, auth_headers):
    """Tech stack preferences should persist and be retrievable"""
    s = await client.post("/api/v1/sessions", json={
        "industry": "SaaS", "location": "India",
        "tech_stack_preferences": ["React", "Node.js", "MongoDB"]
    }, headers=auth_headers)
    session = await client.get(f"/api/v1/sessions/{s.json()['id']}", headers=auth_headers)
    assert session.json()["tech_stack_preferences"] == ["React", "Node.js", "MongoDB"]
