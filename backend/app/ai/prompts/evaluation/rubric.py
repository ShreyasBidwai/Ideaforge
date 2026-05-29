from app.core.maturity import MaturityConfig

def build_rubric_prompt(
    problem_statement: dict,
    maturity_config: MaturityConfig
) -> tuple[str, str]:
    """
    Returns (system_prompt, user_prompt) for rubric generation.
    MUST NOT include any solution candidate information.
    """
    
    extra_criteria = ""
    if maturity_config.include_security_criteria:
        extra_criteria += "\n- Include a 'Security & Data Privacy' criterion."
    if maturity_config.include_compliance_criteria:
        extra_criteria += "\n- Include a 'Regulatory Compliance' criterion relevant to the industry/location."
    
    system_prompt = f"""You are an expert evaluator designing a scoring rubric for technology solution proposals.

TASK: Create a rubric to evaluate solutions for the given problem statement. You are creating the rubric BEFORE seeing any solutions — this ensures unbiased evaluation.

Rules:
- Return ONLY valid JSON. No markdown, no preamble.
- Create 3-6 scored criteria. Each must be relevant to THIS specific problem.
- For each criterion, define concrete anchors for scores 1, 3, and 5 on a 1-5 scale.
  - 1 = fails badly at this criterion
  - 3 = adequate, meets basic expectations
  - 5 = exceptional, best-in-class
- Assign explicit weights to each criterion reflecting what matters most for THIS problem (weights are positive numbers, typically 1-3).
- Define 1-3 disqualifiers — hard pass/fail gates that eliminate a candidate regardless of score.
- Disqualifiers should be concrete and testable, not vague.
- CRITICAL: Disqualifiers must target actual violations, fundamental design flaws, or direct incompatibilities. They must NOT require a solution to "explicitly state" or "explicitly mention" compliance, certification, or specific legal/regulatory boilerplate (e.g. "fails to explicitly state adherence to DPDP Act 2023"), since high-level solution proposals will not include such boilerplate.
{extra_criteria}

JSON Schema:
{{
  "criteria": [
    {{
      "name": "Criterion name",
      "description": "What this criterion measures (1 sentence)",
      "weight": <number 1-3>,
      "scale": {{
        "1": "Concrete description of what score 1 looks like",
        "3": "Concrete description of what score 3 looks like",
        "5": "Concrete description of what score 5 looks like"
      }}
    }}
  ],
  "disqualifiers": [
    {{
      "name": "Disqualifier name",
      "description": "Concrete pass/fail gate description"
    }}
  ]
}}"""

    user_prompt = f"""Create an evaluation rubric for solutions to this problem:

Title: {problem_statement['title']}
Description: {problem_statement['description']}
Target User: {problem_statement.get('target_user', 'Not specified')}
Core Pain: {problem_statement.get('core_pain', 'Not specified')}
Market Context: {problem_statement.get('market_context', 'Not specified')}

Design criteria that will meaningfully differentiate between good and bad solutions to this specific problem."""
    
    return system_prompt, user_prompt
