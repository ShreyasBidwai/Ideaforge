import pytest
import json

MOCK_SOLUTIONS = {
    "solutions": [
        {
            "title": "AI-Powered Smart Queue Kiosk",
            "description": "Physical kiosk + mobile app that uses ML to predict wait times and optimize queue flow.",
            "mechanism": "Computer vision tracks patient flow, ML model predicts wait times based on historical data, patients get real-time SMS updates.",
            "tech_stack": ["React Native", "Python", "TensorFlow Lite", "PostgreSQL", "Twilio"],
            "target_user": "Hospital administrators",
            "revenue_model": "Hardware lease $200/mo + SaaS $99/mo per hospital",
            "is_unconventional": False
        },
        {
            "title": "WhatsApp-Based Queue Bot",
            "description": "No-app-download queue system that runs entirely through WhatsApp Business API.",
            "mechanism": "Patients send WhatsApp message to hospital number, bot assigns queue position, sends updates via WhatsApp. Hospital dashboard shows real-time queue.",
            "tech_stack": ["Node.js", "WhatsApp Business API", "Redis", "React", "MongoDB"],
            "target_user": "Patients and hospital reception staff",
            "revenue_model": "Per-message pricing $0.005/msg + monthly dashboard fee $49/hospital",
            "is_unconventional": False
        },
        {
            "title": "Appointment Marketplace with Dynamic Pricing",
            "description": "Platform where patients book specific time slots with surge pricing for popular times.",
            "mechanism": "Dynamic pricing algorithm adjusts slot costs based on demand. Off-peak slots cheaper, peak slots premium. Hospitals earn more, patients self-sort by urgency/price.",
            "tech_stack": ["Next.js", "FastAPI", "PostgreSQL", "Stripe", "Redis"],
            "target_user": "Urban patients willing to pay for convenience",
            "revenue_model": "15% commission on each booking + premium listing for hospitals",
            "is_unconventional": False
        },
        {
            "title": "Decentralized Health Queue Protocol",
            "description": "Blockchain-based patient queue that works across multiple hospitals, letting patients transfer queue positions.",
            "mechanism": "Smart contracts manage queue positions as transferable tokens. Patients can sell/transfer their position. Cross-hospital interoperability via shared protocol.",
            "tech_stack": ["Solidity", "Ethereum L2", "React", "The Graph", "IPFS"],
            "target_user": "Hospital networks and health-conscious tech users",
            "revenue_model": "Protocol fee 0.1% on queue transfers + enterprise licensing for hospital chains",
            "is_unconventional": True
        },
        {
            "title": "Predictive Triage Routing Engine",
            "description": "AI system that pre-triages patients before they arrive and routes them to the optimal department/doctor.",
            "mechanism": "Patient fills symptom form pre-visit, NLP engine matches to department + urgency level, auto-schedules with least-busy matching doctor. Reduces misdirected visits by 60%.",
            "tech_stack": ["FastAPI", "spaCy", "React", "PostgreSQL", "Docker"],
            "target_user": "Multi-department hospitals with 500+ daily patients",
            "revenue_model": "SaaS tier: $299/mo small hospital, $999/mo large hospital, $2499/mo hospital chain",
            "is_unconventional": False
        }
    ]
}

# ─── Prompt Tests ───

# TEST 1: Prompt includes problem statement details
def test_prompt_includes_problem():
    """Solution prompt should contain problem title and description"""
    from app.ai.prompts.solutions import build_solution_prompt
    from app.core.maturity import get_maturity_config, MaturityLevel
    problem = {"title": "Digital Queue System", "description": "Reduce hospital wait times",
               "target_user": "Hospitals", "core_pain": "Long waits", "market_context": "India healthcare"}
    system, user = build_solution_prompt(problem, get_maturity_config(MaturityLevel.MVP))
    assert "Digital Queue System" in user
    assert "hospital wait times" in user.lower() or "Reduce hospital wait times" in user

# TEST 2: Prompt enforces diversity constraints
def test_prompt_enforces_diversity():
    """Prompt must mention genuinely different, unconventional, falsifiable"""
    from app.ai.prompts.solutions import build_solution_prompt
    from app.core.maturity import get_maturity_config, MaturityLevel
    problem = {"title": "Test", "description": "Test"}
    system, user = build_solution_prompt(problem, get_maturity_config(MaturityLevel.MVP))
    system_lower = system.lower()
    assert "genuinely different" in system_lower or "different in mechanism" in system_lower
    assert "unconventional" in system_lower
    assert "falsifiable" in system_lower or "specific" in system_lower

# TEST 3: Prompt respects maturity candidate count
def test_prompt_maturity_count():
    """POC should ask for 3 solutions, production for 5"""
    from app.ai.prompts.solutions import build_solution_prompt
    from app.core.maturity import get_maturity_config, MaturityLevel
    problem = {"title": "Test", "description": "Test"}
    poc_sys, _ = build_solution_prompt(problem, get_maturity_config(MaturityLevel.POC))
    prod_sys, _ = build_solution_prompt(problem, get_maturity_config(MaturityLevel.PRODUCTION))
    assert "3" in poc_sys
    assert "5" in prod_sys

# TEST 4: Prompt includes tech stack preferences when provided
def test_prompt_includes_tech_prefs():
    """Tech stack preferences should appear in prompt"""
    from app.ai.prompts.solutions import build_solution_prompt
    from app.core.maturity import get_maturity_config, MaturityLevel
    problem = {"title": "Test", "description": "Test"}
    system, _ = build_solution_prompt(problem, get_maturity_config(MaturityLevel.MVP), ["React", "FastAPI"])
    assert "React" in system
    assert "FastAPI" in system

# ─── Schema Tests ───

# TEST 5: Valid solution schema
def test_valid_solution_schema():
    """SolutionCreate should accept valid data"""
    from app.schemas.solution import SolutionCreate
    s = SolutionCreate(
        title="AI Queue Kiosk", description="Smart queue system",
        mechanism="ML predicts wait times", tech_stack=["React", "Python"],
        target_user="Hospitals", revenue_model="SaaS $99/mo", is_unconventional=False
    )
    assert s.is_unconventional is False

# TEST 6: Solution requires title and description
def test_solution_requires_fields():
    """Solution without title should fail"""
    from app.schemas.solution import SolutionCreate
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        SolutionCreate(description="Test", mechanism="Test", tech_stack=[], target_user="Test",
                      revenue_model="Test", is_unconventional=False)

# ─── API Tests ───

# TEST 7: Generate solutions for selected problem
async def test_generate_solutions(client, auth_headers, mock_gemini):
    """POST /problem-statements/{id}/generate-solutions should return solutions"""
    # Create full pipeline: session → pain points → problem → select
    session = await client.post("/api/v1/sessions", json={
        "industry": "Healthcare", "location": "India", "maturity_level": "mvp"
    }, headers=auth_headers)
    sid = session.json()["id"]
    mock_gemini.return_value = json.dumps({"pain_points": [
        {"name": "Wait", "description": "Long waits", "severity": 8, "affected_stakeholders": ["Patients"], "evidence": "Data"}
    ]})
    await client.post(f"/api/v1/sessions/{sid}/discover", headers=auth_headers)
    mock_gemini.return_value = json.dumps({"problem_statements": [
        {"title": "Queue System", "description": "Digital queue", "target_user": "Hospitals",
         "core_pain": "Waits", "market_context": "India", "severity": 4, "feasibility": 5, "market_size": 4, "uniqueness": 3}
    ]})
    problems = await client.post(f"/api/v1/sessions/{sid}/generate-problems", headers=auth_headers)
    pid = problems.json()[0]["id"]
    await client.post(f"/api/v1/problem-statements/{pid}/select", headers=auth_headers)
    
    # Generate solutions
    mock_gemini.return_value = json.dumps(MOCK_SOLUTIONS)
    response = await client.post(f"/api/v1/problem-statements/{pid}/generate-solutions", headers=auth_headers)
    assert response.status_code == 200
    solutions = response.json()
    assert len(solutions) >= 4  # MVP = 4 candidates
    assert any(s["is_unconventional"] for s in solutions)

# TEST 8: Solutions are persisted
async def test_solutions_persisted(client, auth_headers, mock_gemini):
    """GET /problem-statements/{id}/solutions should return stored solutions"""
    session = await client.post("/api/v1/sessions", json={"industry": "Fintech", "location": "India"}, headers=auth_headers)
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
    mock_gemini.return_value = json.dumps(MOCK_SOLUTIONS)
    await client.post(f"/api/v1/problem-statements/{pid}/generate-solutions", headers=auth_headers)
    
    response = await client.get(f"/api/v1/problem-statements/{pid}/solutions", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) >= 4

# TEST 9: Cannot generate solutions for non-selected problem
async def test_generate_requires_selected(client, auth_headers, mock_gemini):
    """Should fail if problem is not in 'selected' status"""
    session = await client.post("/api/v1/sessions", json={"industry": "EdTech", "location": "India"}, headers=auth_headers)
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
    # NOT selecting the problem
    response = await client.post(f"/api/v1/problem-statements/{pid}/generate-solutions", headers=auth_headers)
    assert response.status_code in [400, 422]

# TEST 10: Approve solution
async def test_approve_solution(client, auth_headers, mock_gemini):
    """POST /solutions/{id}/approve should set status to approved"""
    session = await client.post("/api/v1/sessions", json={"industry": "Logistics", "location": "India"}, headers=auth_headers)
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
    mock_gemini.return_value = json.dumps(MOCK_SOLUTIONS)
    solutions = await client.post(f"/api/v1/problem-statements/{pid}/generate-solutions", headers=auth_headers)
    sol_id = solutions.json()[0]["id"]
    
    response = await client.post(f"/api/v1/solutions/{sol_id}/approve", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "approved"

# TEST 11: At least one unconventional solution flagged
async def test_unconventional_solution_exists(client, auth_headers, mock_gemini):
    """Generated solutions must include at least one unconventional"""
    session = await client.post("/api/v1/sessions", json={"industry": "AgriTech", "location": "India"}, headers=auth_headers)
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
    mock_gemini.return_value = json.dumps(MOCK_SOLUTIONS)
    solutions = await client.post(f"/api/v1/problem-statements/{pid}/generate-solutions", headers=auth_headers)
    assert any(s["is_unconventional"] for s in solutions.json())

# TEST 12: Session status updates to evaluation
async def test_session_status_evaluation(client, auth_headers, mock_gemini):
    """Session status should change to evaluation after solution generation"""
    session = await client.post("/api/v1/sessions", json={"industry": "Retail", "location": "India"}, headers=auth_headers)
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
    mock_gemini.return_value = json.dumps(MOCK_SOLUTIONS)
    await client.post(f"/api/v1/problem-statements/{pid}/generate-solutions", headers=auth_headers)
    
    session_check = await client.get(f"/api/v1/sessions/{sid}", headers=auth_headers)
    assert session_check.json()["status"] == "evaluation"
