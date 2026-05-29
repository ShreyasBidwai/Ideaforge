from typing import Optional
from app.core.maturity import MaturityConfig, get_maturity_config, MaturityLevel

def build_pain_point_prompt(
    industry: str,
    location: str,
    maturity_config: Optional[MaturityConfig] = None,
    guidance: Optional[str] = None
) -> tuple[str, str]:
    """Returns (system_prompt, user_prompt) for pain point discovery"""
    if maturity_config is None:
        maturity_config = get_maturity_config(MaturityLevel.MVP)

    min_count, max_count = maturity_config.pain_point_count
    
    system_prompt = f"""You are an expert industry analyst and startup researcher. Your job is to identify real, specific, actionable pain points in a given industry and location.

Rules:
- Return ONLY valid JSON. No markdown, no preamble, no explanation.
- Identify {min_count} to {max_count} pain points.
- Each pain point must be specific and grounded in reality — not generic platitudes.
- Pain points must be relevant to the specific location/geography (regulations, infrastructure, culture, market market maturity).
- Severity scores must reflect genuine business impact, not hype.
- Affected stakeholders must be specific roles/entities, not "everyone".
- Evidence should reference real-world patterns, not hypotheticals.

JSON Schema:
{{
  "pain_points": [
    {{
      "name": "Short title (5-10 words)",
      "description": "Detailed description of the pain point (2-4 sentences). Be specific about what's broken, why it matters, and who suffers.",
      "severity": <1-10 integer, 10 = critical business-stopping issue>,
      "affected_stakeholders": ["Specific role 1", "Specific role 2"],
      "evidence": "Real-world evidence or pattern that confirms this pain point exists (1-2 sentences)"
    }}
  ]
}}"""

    user_prompt = f"Discover the top pain points in the {industry} industry in {location}. Focus on problems that a technology startup could potentially solve."
    
    if guidance and guidance.strip():
        user_prompt += (
            f"\n\nUSER GUIDANCE (treat as a strong steer, not a hard constraint):\n"
            f"{guidance.strip()}\n"
            f"Bias the pain points and resulting ideas toward this guidance where reasonable, "
            f"but do not invent pain points that don't fit the industry/location."
        )

    return system_prompt, user_prompt
