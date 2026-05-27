import pytest
import json

MOCK_RUBRIC = {
    "criteria": [
        {"name": "Technical Feasibility", "description": "Buildable?", "weight": 2,
         "scale": {"1": "Impossible", "3": "Doable", "5": "Easy"}},
        {"name": "User Adoption", "description": "Will users use it?", "weight": 2.5,
         "scale": {"1": "No way", "3": "Maybe", "5": "Definitely"}},
        {"name": "Revenue Viability", "description": "Makes money?", "weight": 1.5,
         "scale": {"1": "No revenue path", "3": "Possible", "5": "Proven model"}}
    ],
    "disqualifiers": [
        {"name": "Illegal", "description": "Solution violates laws"},
        {"name": "Requires >$10M upfront", "description": "Needs more than $10M capital to launch"}
    ]
}

MOCK_DISQUALIFIER_RESULTS = {"results": [
    {"solution_title": "Sol 1", "passed": True, "failed_disqualifiers": [], "reasons": []},
    {"solution_title": "Sol 2", "passed": True, "failed_disqualifiers": [], "reasons": []},
    {"solution_title": "Sol 3", "passed": False, "failed_disqualifiers": ["Requires >$10M upfront"], "reasons": ["Needs custom hardware deployment at scale"]},
    {"solution_title": "Sol 4", "passed": True, "failed_disqualifiers": [], "reasons": []},
    {"solution_title": "Sol 5", "passed": True, "failed_disqualifiers": [], "reasons": []}
]}

MOCK_SCORES = {"scores": [
    {"solution_title": "Sol 1", "criterion_scores": [
        {"criterion": "Technical Feasibility", "score": 4, "justification": "Uses proven tech stack"},
        {"criterion": "User Adoption", "score": 3, "justification": "Moderate friction"},
        {"criterion": "Revenue Viability", "score": 4, "justification": "Clear SaaS model"}
    ], "weighted_avg": 3.58, "min_score": 3},
    {"solution_title": "Sol 2", "criterion_scores": [
        {"criterion": "Technical Feasibility", "score": 5, "justification": "WhatsApp API is simple"},
        {"criterion": "User Adoption", "score": 5, "justification": "Everyone uses WhatsApp"},
        {"criterion": "Revenue Viability", "score": 2, "justification": "Per-message pricing is thin"}
    ], "weighted_avg": 4.17, "min_score": 2},
    {"solution_title": "Sol 4", "criterion_scores": [
        {"criterion": "Technical Feasibility", "score": 2, "justification": "Blockchain is overkill"},
        {"criterion": "User Adoption", "score": 1, "justification": "Users won't learn crypto"},
        {"criterion": "Revenue Viability", "score": 1, "justification": "Protocol fees are negligible"}
    ], "weighted_avg": 1.33, "min_score": 1},
    {"solution_title": "Sol 5", "criterion_scores": [
        {"criterion": "Technical Feasibility", "score": 4, "justification": "NLP is mature"},
        {"criterion": "User Adoption", "score": 4, "justification": "Pre-visit form is low friction"},
        {"criterion": "Revenue Viability", "score": 5, "justification": "Tiered SaaS pricing proven"}
    ], "weighted_avg": 4.25, "min_score": 4}
]}

# TEST 1: Weighted average computation
def test_weighted_avg_computation():
    """Weighted average should correctly weight scores"""
    from backend.app.services.evaluation_service import EvaluationService
    scores = [
        {"criterion": "A", "score": 5},
        {"criterion": "B", "score": 3},
        {"criterion": "C", "score": 1}
    ]
    criteria = [
        {"name": "A", "weight": 2},
        {"name": "B", "weight": 1},
        {"name": "C", "weight": 1}
    ]
    avg = EvaluationService.compute_weighted_avg(scores, criteria)
    expected = round((5*2 + 3*1 + 1*1) / (2+1+1), 2)
    assert avg == expected

# TEST 2: Min score computation
def test_min_score_computation():
    """Min score should return the lowest score"""
    from backend.app.services.evaluation_service import EvaluationService
    scores = [{"criterion": "A", "score": 4}, {"criterion": "B", "score": 2}, {"criterion": "C", "score": 5}]
    assert EvaluationService.compute_min_score(scores) == 2

# TEST 3: Min score with empty list
def test_min_score_empty():
    """Min score of empty list should return 0"""
    from backend.app.services.evaluation_service import EvaluationService
    assert EvaluationService.compute_min_score([]) == 0

# TEST 4: Disqualifier gate runs
async def test_disqualifier_gate(client, auth_headers, mock_gemini):
    """POST /evaluation/disqualify should eliminate failing solutions"""
    from tests.test_s5_01_rubric import setup_problem_with_solutions, MOCK_RUBRIC as RUBRIC
    _, pid = await setup_problem_with_solutions(client, auth_headers, mock_gemini)
    mock_gemini.return_value = json.dumps(RUBRIC)
    await client.post(f"/api/v1/problem-statements/{pid}/evaluation/rubric", headers=auth_headers)
    await client.post(f"/api/v1/problem-statements/{pid}/evaluation/rubric/lock", headers=auth_headers)
    
    mock_gemini.return_value = json.dumps(MOCK_DISQUALIFIER_RESULTS)
    response = await client.post(f"/api/v1/problem-statements/{pid}/evaluation/disqualify", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    passed = [r for r in data["results"] if r["passed"]]
    failed = [r for r in data["results"] if not r["passed"]]
    assert len(passed) >= 2  # at least 2 must survive
    assert len(failed) >= 1

# TEST 5: Disqualifier requires locked rubric
async def test_disqualifier_requires_locked_rubric(client, auth_headers, mock_gemini):
    """Cannot run disqualifier gate without locked rubric"""
    from tests.test_s5_01_rubric import setup_problem_with_solutions
    _, pid = await setup_problem_with_solutions(client, auth_headers, mock_gemini)
    # Don't generate or lock rubric
    response = await client.post(f"/api/v1/problem-statements/{pid}/evaluation/disqualify", headers=auth_headers)
    assert response.status_code in [400, 422]

# TEST 6: Scoring runs on survivors only
async def test_scoring_survivors_only(client, auth_headers, mock_gemini):
    """POST /evaluation/score should only score non-disqualified solutions"""
    from tests.test_s5_01_rubric import setup_problem_with_solutions, MOCK_RUBRIC as RUBRIC
    _, pid = await setup_problem_with_solutions(client, auth_headers, mock_gemini)
    mock_gemini.return_value = json.dumps(RUBRIC)
    await client.post(f"/api/v1/problem-statements/{pid}/evaluation/rubric", headers=auth_headers)
    await client.post(f"/api/v1/problem-statements/{pid}/evaluation/rubric/lock", headers=auth_headers)
    mock_gemini.return_value = json.dumps(MOCK_DISQUALIFIER_RESULTS)
    await client.post(f"/api/v1/problem-statements/{pid}/evaluation/disqualify", headers=auth_headers)
    
    mock_gemini.return_value = json.dumps(MOCK_SCORES)
    response = await client.post(f"/api/v1/problem-statements/{pid}/evaluation/score", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "scores" in data
    # All scored solutions should have weighted_avg and min_score
    for s in data["scores"]:
        assert "weighted_avg" in s
        assert "min_score" in s

# TEST 7: Scores persist in database
async def test_scores_persist(client, auth_headers, mock_gemini):
    """GET /evaluation/scores should return stored scores"""
    from tests.test_s5_01_rubric import setup_problem_with_solutions, MOCK_RUBRIC as RUBRIC
    _, pid = await setup_problem_with_solutions(client, auth_headers, mock_gemini)
    mock_gemini.return_value = json.dumps(RUBRIC)
    await client.post(f"/api/v1/problem-statements/{pid}/evaluation/rubric", headers=auth_headers)
    await client.post(f"/api/v1/problem-statements/{pid}/evaluation/rubric/lock", headers=auth_headers)
    mock_gemini.return_value = json.dumps(MOCK_DISQUALIFIER_RESULTS)
    await client.post(f"/api/v1/problem-statements/{pid}/evaluation/disqualify", headers=auth_headers)
    mock_gemini.return_value = json.dumps(MOCK_SCORES)
    await client.post(f"/api/v1/problem-statements/{pid}/evaluation/score", headers=auth_headers)
    
    response = await client.get(f"/api/v1/problem-statements/{pid}/evaluation/scores", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()["scores"]) >= 2

# TEST 8: Disqualifier prompt includes solutions and disqualifiers
def test_disqualifier_prompt_content():
    """Disqualifier prompt should include solution data and disqualifier gates"""
    from backend.app.ai.prompts.evaluation.disqualify import build_disqualifier_prompt
    solutions = [{"title": "Sol 1", "description": "D1", "mechanism": "M1"}]
    disqualifiers = [{"name": "Illegal", "description": "Violates laws"}]
    system, user = build_disqualifier_prompt(solutions, disqualifiers)
    assert "Sol 1" in user
    assert "Illegal" in user or "Illegal" in system
