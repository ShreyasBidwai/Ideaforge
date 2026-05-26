from app.core.maturity import MaturityConfig

def build_solution_prompt(
    problem_statement: dict,
    maturity_config: MaturityConfig,
    tech_stack_preferences: list[str] | None = None
) -> tuple[str, str]:
    """Returns (system_prompt, user_prompt) for solution generation"""
    
    count = maturity_config.solution_candidate_count
    
    tech_context = ""
    if tech_stack_preferences:
        tech_context = f"\nThe user has expressed preference for these technologies: {', '.join(tech_stack_preferences)}. Consider these in your proposals but don't limit yourself to them — suggest better alternatives if appropriate."
    
    system_prompt = f"""You are a senior technical architect and startup strategist. Your job is to generate {count} diverse technology solution candidates for a given problem statement.

CRITICAL CONSTRAINTS (from the Idea Evaluation Protocol):
1. The {count} candidates must be GENUINELY DIFFERENT in mechanism or approach — not {count} flavors of the same idea.
2. Each must be SPECIFIC and FALSIFIABLE — concrete enough to be scored against a rubric. No vague handwaving.
3. At least one candidate MUST be deliberately unconventional — an approach most teams wouldn't think of.
4. Each solution must include a concrete tech stack, not just "use AI" or "build an app".

Rules:
- Return ONLY valid JSON. No markdown, no preamble.
- Mark exactly one solution as is_unconventional: true
- Mechanism should explain HOW the solution works technically, not just WHAT it does
- Revenue model should be specific (e.g., "SaaS subscription $49/mo per clinic" not just "subscription")
{tech_context}

JSON Schema:
{{
  "solutions": [
    {{
      "title": "Solution name (5-10 words)",
      "description": "What this solution does and why it's different (2-4 sentences)",
      "mechanism": "How it works technically — the core technical approach (2-3 sentences)",
      "tech_stack": ["Technology 1", "Technology 2", "Technology 3"],
      "target_user": "Primary user persona (1 sentence)",
      "revenue_model": "Specific monetization approach (1-2 sentences)",
      "is_unconventional": false
    }}
  ]
}}"""

    user_prompt = f"""Generate {count} diverse tech solution candidates for this problem:

Title: {problem_statement['title']}
Description: {problem_statement['description']}
Target User: {problem_statement.get('target_user', 'Not specified')}
Core Pain: {problem_statement.get('core_pain', 'Not specified')}
Market Context: {problem_statement.get('market_context', 'Not specified')}

Remember: genuinely different mechanisms, at least one unconventional, all specific and falsifiable."""
    
    return system_prompt, user_prompt
