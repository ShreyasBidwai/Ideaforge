import json

def build_ach_prompt(solutions: list[dict], problem: dict, scores: list[dict]) -> tuple[str, str]:
    """
    ACH Analysis: for each survivor, list ONLY disconfirming evidence.
    Do not list consistent evidence. Count inconsistencies.
    """
    system_prompt = """You are conducting an Analysis of Competing Hypotheses (ACH).
Your task is to identify and list ONLY disconfirming evidence for each solution candidate.
Do not count consistent or confirming evidence — focus strictly on inconsistencies, contradictions, and negative mismatches.

Rules:
- For each solution, list disconfirming evidence items.
- Count the number of inconsistencies.
- Return ONLY valid JSON matching the schema.

JSON Schema:
{
  "analysis": [
    {
      "solution_title": "Title of solution",
      "inconsistencies": [
        "Inconsistent/disconfirming evidence item 1",
        "Inconsistent/disconfirming evidence item 2"
      ],
      "count": 2
    }
  ]
}"""

    user_prompt = f"""Here is the target problem statement:
{json.dumps(problem, indent=2)}

Here are the solution candidates:
{json.dumps(solutions, indent=2)}

Here are their scores:
{json.dumps(scores, indent=2)}

Generate the ACH inconsistency analysis for each solution candidate."""

    return system_prompt, user_prompt
