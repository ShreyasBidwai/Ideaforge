import json

def build_scoring_prompt(solutions: list[dict], rubric: dict) -> tuple[str, str]:
    """
    Prompt to score each surviving solution on each criterion.
    Only survivors (passed disqualifiers) are scored.
    """
    system_prompt = """You are an expert technology evaluator.
Your task is to score a list of solution candidates against a locked rubric consisting of multiple evaluation criteria.

Rules:
- For each solution, evaluate and score it on a 1-5 scale for EVERY criterion in the rubric.
- Provide a clear, one-sentence justification for each score based on the rubric's score anchors (1, 3, 5).
- Return ONLY valid JSON matching the schema.

JSON Schema:
{
  "scores": [
    {
      "solution_title": "Title of the solution",
      "criterion_scores": [
        {
          "criterion": "Criterion Name",
          "score": 4,
          "justification": "One-sentence justification based on anchors."
        }
      ]
    }
  ]
}"""

    user_prompt = f"""Here is the locked evaluation rubric:
{json.dumps(rubric, indent=2)}

Here are the solution candidates to score:
{json.dumps(solutions, indent=2)}

For each solution candidate, generate scores and justifications."""

    return system_prompt, user_prompt
