import pytest
import json

MOCK_ATTACKS = {"attacks": [
    {"solution_title": "Sol 1", "attack": "Hospitals have no IT staff to manage kiosks. Hardware maintenance becomes a nightmare at scale. One broken kiosk = no queue system.", "severity": "high", "survives": True, "survival_reasoning": "Can mitigate with cloud-managed kiosks and remote support contracts"},
    {"solution_title": "Sol 2", "attack": "WhatsApp can change their API pricing or terms overnight. Your entire business depends on a platform you don't control. Meta has killed APIs before.", "severity": "high", "survives": False, "survival_reasoning": "Platform dependency is existential risk with no mitigation"},
    {"solution_title": "Sol 4", "attack": "No hospital administrator will adopt a blockchain-based system. The target user has zero crypto literacy. This solves a problem nobody asked for.", "severity": "high", "survives": False, "survival_reasoning": "Target user mismatch is fatal — the unconventional approach doesn't fit the user"},
    {"solution_title": "Sol 5", "attack": "NLP-based triage carries liability risk — misrouting a patient could have health consequences. No hospital will accept AI-driven triage without regulatory approval.", "severity": "medium", "survives": True, "survival_reasoning": "Can position as decision-support (not decision-maker) to avoid liability"}
]}

MOCK_ACH = {"analysis": [
    {"solution_title": "Sol 1", "inconsistencies": ["Hospitals in India have unreliable internet, kiosks need connectivity", "Budget constraints — most Indian hospitals won't pay $200/mo for hardware"], "count": 2},
    {"solution_title": "Sol 2", "inconsistencies": ["WhatsApp Business API costs are increasing", "Platform lock-in risk confirmed by Meta's history", "Older patients may not use WhatsApp"], "count": 3},
    {"solution_title": "Sol 4", "inconsistencies": ["Zero blockchain adoption in Indian healthcare", "Regulatory uncertainty around health data on blockchain", "Target users are tech-illiterate"], "count": 3},
    {"solution_title": "Sol 5", "inconsistencies": ["Medical AI requires FDA/CDSCO approval", "Liability concerns for AI-driven triage"], "count": 2}
]}

# TEST 1: Devil's advocate prompt steelmans attacks
def test_da_prompt_steelmans():
    """Prompt should explicitly request steelmanned attacks, not strawmen"""
    from backend.app.ai.prompts.evaluation.devils_advocate import build_devils_advocate_prompt
    solutions = [{"title": "Sol 1", "description": "D", "mechanism": "M"}]
    scores = [{"solution_title": "Sol 1", "weighted_avg": 4.0}]
    system, _ = build_devils_advocate_prompt(solutions, scores)
    assert "steelman" in system.lower() or "strongest" in system.lower()
    assert "strawman" in system.lower()  # should mention not to strawman

# TEST 2: ACH prompt requests only disconfirming evidence
def test_ach_prompt_disconfirming_only():
    """ACH prompt must explicitly request ONLY disconfirming evidence"""
    from backend.app.ai.prompts.evaluation.ach import build_ach_prompt
    solutions = [{"title": "Sol 1"}]
    problem = {"title": "Queue", "description": "Digital queue"}
    scores = [{"solution_title": "Sol 1", "weighted_avg": 4.0}]
    system, _ = build_ach_prompt(solutions, problem, scores)
    system_lower = system.lower()
    assert "disconfirming" in system_lower or "inconsistent" in system_lower
    assert "do not count consistent" in system_lower or "only disconfirming" in system_lower

# TEST 3: Run devil's advocate via API
async def test_devils_advocate_api(client, auth_headers, mock_gemini):
    """POST /evaluation/attack should return attacks for each survivor"""
    from tests.test_s5_01_rubric import setup_problem_with_solutions, MOCK_RUBRIC
    from tests.test_s5_02_scoring import MOCK_DISQUALIFIER_RESULTS, MOCK_SCORES
    _, pid = await setup_problem_with_solutions(client, auth_headers, mock_gemini)
    # Run rubric → lock → disqualify → score → attack
    mock_gemini.return_value = json.dumps(MOCK_RUBRIC)
    await client.post(f"/api/v1/problem-statements/{pid}/evaluation/rubric", headers=auth_headers)
    await client.post(f"/api/v1/problem-statements/{pid}/evaluation/rubric/lock", headers=auth_headers)
    mock_gemini.return_value = json.dumps(MOCK_DISQUALIFIER_RESULTS)
    await client.post(f"/api/v1/problem-statements/{pid}/evaluation/disqualify", headers=auth_headers)
    mock_gemini.return_value = json.dumps(MOCK_SCORES)
    await client.post(f"/api/v1/problem-statements/{pid}/evaluation/score", headers=auth_headers)
    mock_gemini.return_value = json.dumps(MOCK_ATTACKS)
    response = await client.post(f"/api/v1/problem-statements/{pid}/evaluation/attack", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "attacks" in data
    assert len(data["attacks"]) >= 2
    assert all("attack" in a for a in data["attacks"])
    assert all("survives" in a for a in data["attacks"])

# TEST 4: Run ACH analysis via API
async def test_ach_analysis_api(client, auth_headers, mock_gemini):
    """POST /evaluation/ach should return inconsistency counts"""
    from tests.test_s5_01_rubric import setup_problem_with_solutions, MOCK_RUBRIC
    from tests.test_s5_02_scoring import MOCK_DISQUALIFIER_RESULTS, MOCK_SCORES
    _, pid = await setup_problem_with_solutions(client, auth_headers, mock_gemini)
    mock_gemini.return_value = json.dumps(MOCK_RUBRIC)
    await client.post(f"/api/v1/problem-statements/{pid}/evaluation/rubric", headers=auth_headers)
    await client.post(f"/api/v1/problem-statements/{pid}/evaluation/rubric/lock", headers=auth_headers)
    mock_gemini.return_value = json.dumps(MOCK_DISQUALIFIER_RESULTS)
    await client.post(f"/api/v1/problem-statements/{pid}/evaluation/disqualify", headers=auth_headers)
    mock_gemini.return_value = json.dumps(MOCK_SCORES)
    await client.post(f"/api/v1/problem-statements/{pid}/evaluation/score", headers=auth_headers)
    mock_gemini.return_value = json.dumps(MOCK_ATTACKS)
    await client.post(f"/api/v1/problem-statements/{pid}/evaluation/attack", headers=auth_headers)
    mock_gemini.return_value = json.dumps(MOCK_ACH)
    response = await client.post(f"/api/v1/problem-statements/{pid}/evaluation/ach", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "analysis" in data
    for a in data["analysis"]:
        assert "inconsistencies" in a
        assert "count" in a
        assert a["count"] == len(a["inconsistencies"])

# TEST 5: Attack survival is stored in evaluation
async def test_attack_stored(client, auth_headers, mock_gemini):
    """Attack results should persist in evaluation records"""
    from tests.test_s5_01_rubric import setup_problem_with_solutions, MOCK_RUBRIC
    from tests.test_s5_02_scoring import MOCK_DISQUALIFIER_RESULTS, MOCK_SCORES
    _, pid = await setup_problem_with_solutions(client, auth_headers, mock_gemini)
    mock_gemini.return_value = json.dumps(MOCK_RUBRIC)
    await client.post(f"/api/v1/problem-statements/{pid}/evaluation/rubric", headers=auth_headers)
    await client.post(f"/api/v1/problem-statements/{pid}/evaluation/rubric/lock", headers=auth_headers)
    mock_gemini.return_value = json.dumps(MOCK_DISQUALIFIER_RESULTS)
    await client.post(f"/api/v1/problem-statements/{pid}/evaluation/disqualify", headers=auth_headers)
    mock_gemini.return_value = json.dumps(MOCK_SCORES)
    await client.post(f"/api/v1/problem-statements/{pid}/evaluation/score", headers=auth_headers)
    mock_gemini.return_value = json.dumps(MOCK_ATTACKS)
    await client.post(f"/api/v1/problem-statements/{pid}/evaluation/attack", headers=auth_headers)
    
    attacks_resp = await client.get(f"/api/v1/problem-statements/{pid}/evaluation/attacks", headers=auth_headers)
    assert attacks_resp.status_code == 200

# TEST 6: POC maturity skips devil's advocate and ACH
async def test_poc_skips_attack_ach(client, auth_headers, mock_gemini):
    """POC maturity should not require attack and ACH steps"""
    from backend.app.core.maturity import get_maturity_config, MaturityLevel
    config = get_maturity_config(MaturityLevel.POC)
    assert "devils_advocate" not in config.evaluation_steps
    assert "ach_analysis" not in config.evaluation_steps
