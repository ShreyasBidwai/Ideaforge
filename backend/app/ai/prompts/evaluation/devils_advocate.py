import json

def build_devils_advocate_prompt(solutions: list[dict], scores: list[dict]) -> tuple[str, str]:
    """
    For each surviving scored solution, generate the STRONGEST possible attack.
    Steelman the attack. Do NOT strawman.
    Minimax framing: find whose worst case is least bad.
    """
    system_prompt = """You are acting as the Devil's Advocate.
Your task is to identify and articulate the STRONGEST possible attack against each solution candidate.
You must steelman the attack (critique the strongest form of their argument/mechanism).
Do NOT strawman the solution.
Your goal is to use minimax framing to find whose worst-case risk is least bad.

Rules:
- For each solution, generate a 2-3 sentence strongest critique.
- Rate the attack severity (high/medium/low).
- Determine if the solution survives the attack (true/false) and provide 1 sentence of survival reasoning.
- Return ONLY valid JSON matching the schema.

JSON Schema:
{
  "attacks": [
    {
      "solution_title": "Title of solution",
      "attack": "Strongest critique (2-3 sentences)",
      "severity": "high/medium/low",
      "survives": true,
      "survival_reasoning": "Why it does or doesn't survive (1 sentence)"
    }
  ]
}"""

    user_prompt = f"""Here are the solution candidates:
{json.dumps(solutions, indent=2)}

Here are their evaluation scores:
{json.dumps(scores, indent=2)}

Generate the steelmanned critiques and determine survival for each solution."""

    return system_prompt, user_prompt
