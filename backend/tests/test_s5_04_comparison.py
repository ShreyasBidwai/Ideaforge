import pytest
import json

# TEST 1: Comparison identifies leaders correctly
def test_comparison_leaders():
    """Should identify the leader per metric"""
    from backend.app.services.evaluation_service import EvaluationService
    entries = [
        {"solution_title": "Sol A", "weighted_avg": 4.5, "min_score": 3, "attack_survives": True, "inconsistency_count": 2},
        {"solution_title": "Sol B", "weighted_avg": 3.8, "min_score": 4, "attack_survives": False, "inconsistency_count": 1},
        {"solution_title": "Sol C", "weighted_avg": 4.0, "min_score": 2, "attack_survives": True, "inconsistency_count": 3},
    ]
    # Sol A leads weighted_avg, Sol B leads min_score + inconsistencies, Sol A and C lead attack survival
    res = EvaluationService._compute_comparison_results(entries)
    assert res["leaders"]["weighted_avg"] == "Sol A"
    assert res["leaders"]["min_score"] == "Sol B"
    assert res["leaders"]["attack_survives"] in ("Sol A", "Sol C")
    assert res["leaders"]["inconsistency_count"] == "Sol B"
    assert res["is_clear_winner"] is False
    assert len(res["disagreements"]) > 0

# TEST 2: Clear winner when one solution leads all metrics
def test_clear_winner():
    """When one solution wins all 4 metrics, flag as clear survivor"""
    from backend.app.services.evaluation_service import EvaluationService
    entries = [
        {"solution_title": "Sol A", "weighted_avg": 5.0, "min_score": 5, "attack_survives": True, "inconsistency_count": 0},
        {"solution_title": "Sol B", "weighted_avg": 2.0, "min_score": 1, "attack_survives": False, "inconsistency_count": 5},
    ]
    res = EvaluationService._compute_comparison_results(entries)
    assert res["is_clear_winner"] is True
    assert len(res["disagreements"]) == 0

# TEST 3: Disagreement flagged when metrics conflict
def test_disagreement_flagged():
    """When different solutions lead different metrics, flag disagreement"""
    from backend.app.services.evaluation_service import EvaluationService
    # Sol A: best score but fails attack
    # Sol B: lower score but survives attack and fewer inconsistencies
    entries = [
        {"solution_title": "Sol A", "weighted_avg": 4.5, "min_score": 3, "attack_survives": False, "inconsistency_count": 3},
        {"solution_title": "Sol B", "weighted_avg": 3.5, "min_score": 4, "attack_survives": True, "inconsistency_count": 1},
    ]
    res = EvaluationService._compute_comparison_results(entries)
    assert res["is_clear_winner"] is False
    assert len(res["disagreements"]) > 0

# TEST 4: Comparison API works
async def test_comparison_api(client, auth_headers, mock_gemini):
    """POST /evaluation/compare should return comparison with leaders"""
    from tests.test_s5_01_rubric import setup_problem_with_solutions, MOCK_RUBRIC
    from tests.test_s5_02_scoring import MOCK_DISQUALIFIER_RESULTS, MOCK_SCORES
    from tests.test_s5_03_attacks import MOCK_ATTACKS, MOCK_ACH
    _, pid = await setup_problem_with_solutions(client, auth_headers, mock_gemini)
    # Run full protocol
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
    await client.post(f"/api/v1/problem-statements/{pid}/evaluation/ach", headers=auth_headers)
    
    response = await client.post(f"/api/v1/problem-statements/{pid}/evaluation/compare", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "entries" in data
    assert "leaders" in data
    assert "is_clear_winner" in data

# TEST 5: Full evaluation endpoint returns everything
async def test_full_evaluation_endpoint(client, auth_headers, mock_gemini):
    """GET /evaluation should return complete evaluation state"""
    from tests.test_s5_01_rubric import setup_problem_with_solutions, MOCK_RUBRIC
    from tests.test_s5_02_scoring import MOCK_DISQUALIFIER_RESULTS, MOCK_SCORES
    from tests.test_s5_03_attacks import MOCK_ATTACKS, MOCK_ACH
    _, pid = await setup_problem_with_solutions(client, auth_headers, mock_gemini)
    # Run full protocol
    for mock_data, endpoint in [
        (MOCK_RUBRIC, f"/api/v1/problem-statements/{pid}/evaluation/rubric"),
        (None, f"/api/v1/problem-statements/{pid}/evaluation/rubric/lock"),
        (MOCK_DISQUALIFIER_RESULTS, f"/api/v1/problem-statements/{pid}/evaluation/disqualify"),
        (MOCK_SCORES, f"/api/v1/problem-statements/{pid}/evaluation/score"),
        (MOCK_ATTACKS, f"/api/v1/problem-statements/{pid}/evaluation/attack"),
        (MOCK_ACH, f"/api/v1/problem-statements/{pid}/evaluation/ach"),
        (None, f"/api/v1/problem-statements/{pid}/evaluation/compare"),
    ]:
        if mock_data:
            mock_gemini.return_value = json.dumps(mock_data)
        await client.post(endpoint, headers=auth_headers)
    
    response = await client.get(f"/api/v1/problem-statements/{pid}/evaluation", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "rubric" in data
    assert "scores" in data or "comparison" in data

# TEST 6: Session status changes to completed after comparison
async def test_session_completed_after_comparison(client, auth_headers, mock_gemini):
    """Session status should be 'completed' after comparison"""
    from tests.test_s5_01_rubric import setup_problem_with_solutions, MOCK_RUBRIC
    from tests.test_s5_02_scoring import MOCK_DISQUALIFIER_RESULTS, MOCK_SCORES
    from tests.test_s5_03_attacks import MOCK_ATTACKS, MOCK_ACH
    sid, pid = await setup_problem_with_solutions(client, auth_headers, mock_gemini)
    for mock_data, endpoint in [
        (MOCK_RUBRIC, f"/api/v1/problem-statements/{pid}/evaluation/rubric"),
        (None, f"/api/v1/problem-statements/{pid}/evaluation/rubric/lock"),
        (MOCK_DISQUALIFIER_RESULTS, f"/api/v1/problem-statements/{pid}/evaluation/disqualify"),
        (MOCK_SCORES, f"/api/v1/problem-statements/{pid}/evaluation/score"),
        (MOCK_ATTACKS, f"/api/v1/problem-statements/{pid}/evaluation/attack"),
        (MOCK_ACH, f"/api/v1/problem-statements/{pid}/evaluation/ach"),
        (None, f"/api/v1/problem-statements/{pid}/evaluation/compare"),
    ]:
        if mock_data:
            mock_gemini.return_value = json.dumps(mock_data)
        await client.post(endpoint, headers=auth_headers)
    
    session = await client.get(f"/api/v1/sessions/{sid}", headers=auth_headers)
    assert session.json()["status"] == "completed"
