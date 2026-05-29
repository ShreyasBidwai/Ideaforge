import json

def build_disqualifier_prompt(solutions: list[dict], disqualifiers: list[dict]) -> tuple[str, str]:
    """
    Prompt to check each solution against disqualifier gates.
    Returns pass/fail per solution with reasons.
    """
    system_prompt = """You are an expert technology evaluator.
Your task is to evaluate a list of solution candidates against a set of negative filters (disqualifiers).
If a solution meets ANY of the disqualifiers, it FAILS (passed = false) and must list which disqualifier(s) it triggered.
If a solution meets none of the disqualifiers, it PASSES (passed = true).

Rules:
- Return ONLY valid JSON matching the schema. No explanations outside JSON.
- Be objective and specific.
- Be realistic and fair: since these are high-level solution proposals, do not disqualify a solution for 'failing to explicitly state' compliance or safety measures unless the description directly indicates a clear violation, risk, or incompatibility with the disqualifier. Assume standard best-practice compliance unless there is a clear red flag.

JSON Schema:
{
  "results": [
    {
      "solution_title": "Title of the solution",
      "passed": true,
      "failed_disqualifiers": [],
      "reasons": []
    }
  ]
}"""

    user_prompt = f"""Here are the disqualifier gates:
{json.dumps(disqualifiers, indent=2)}

Here are the solution candidates to evaluate:
{json.dumps(solutions, indent=2)}

For each solution candidate, determine whether it passes or fails each disqualifier gate."""

    return system_prompt, user_prompt
