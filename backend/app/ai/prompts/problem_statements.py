from app.core.maturity import MaturityConfig

def build_problem_statement_prompt(
    pain_points: list[dict],
    industry: str,
    location: str,
    maturity_config: MaturityConfig
) -> tuple[str, str]:
    """Returns (system_prompt, user_prompt) for problem statement generation"""
    
    count = maturity_config.problem_statement_count  # 2 for POC, 2-3 for MVP, 3 for pre_prod/production
    
    system_prompt = f"""You are a product strategist who converts industry pain points into actionable problem statements for technology startups.

Rules:
- Return ONLY valid JSON. No markdown, no preamble.
- Generate exactly {count} problem statements.
- Each problem statement must be DISTINCT — addressing a different pain point or a fundamentally different angle on the same pain point.
- Problem statements must be specific enough that a team could build a product around them.
- Rate each problem statement on 4 dimensions (1-5 scale, where 5 is best):
  - severity: How painful is this problem? (1=mild annoyance, 3=significant friction, 5=business-critical/life-threatening)
  - feasibility: How realistic is it to build a tech solution? (1=requires breakthrough tech, 3=challenging but doable, 5=straightforward with existing tech)
  - market_size: How large is the addressable market? (1=tiny niche, 3=decent mid-market, 5=massive global market)
  - uniqueness: How differentiated would a solution be from existing alternatives? (1=many competitors do this already, 3=some competitors but room for differentiation, 5=no viable solution exists)

JSON Schema:
{{
  "problem_statements": [
    {{
      "title": "Concise problem title (5-15 words)",
      "description": "Detailed problem description (3-5 sentences). Explain what's broken, who suffers, and why existing solutions fail.",
      "target_user": "Specific user persona who experiences this problem (1 sentence)",
      "core_pain": "The fundamental pain this addresses (1 sentence)",
      "market_context": "Market context — size indicators, trends, regulatory factors (2-3 sentences)",
      "severity": <1-5>,
      "feasibility": <1-5>,
      "market_size": <1-5>,
      "uniqueness": <1-5>
    }}
  ]
}}"""

    pain_points_text = "\n".join([
        f"- {pp['name']} (severity: {pp['severity']}/10): {pp['description']}"
        for pp in pain_points
    ])
    
    user_prompt = f"""Based on these discovered pain points in the {industry} industry in {location}:

{pain_points_text}

Generate {count} distinct, actionable problem statements that a tech startup could solve."""
    
    return system_prompt, user_prompt
