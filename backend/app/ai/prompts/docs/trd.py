from app.ai.prompts.docs.architecture import get_database_directive

def build_trd_prompt(context: dict) -> tuple[str, str]:
    solution = context.get("solution") or {}
    problem = context.get("problem") or {}
    session = context.get("session") or {}
    maturity = context.get("maturity_config") or {}

    tech_stack = solution.get("tech_stack") or []
    tech_stack_str = ", ".join(tech_stack)
    maturity_level = session.get("maturity_level", "mvp")
    db_directive = get_database_directive(maturity_level, tech_stack)

    system_prompt = f"""You are a Lead Software Engineer. Your job is to generate a comprehensive Technical Requirements Document (TRD) for the proposed solution.
Your output must be in clean, well-structured Markdown.
Address technical stack components, system dependencies, detailed API specifications, data structures/schemas, security standards, and testing strategies using: {tech_stack_str}.

{db_directive}"""

    user_prompt = f"""Generate a detailed Technical Requirements Document (TRD) using this context:

### Solution Context:
- Title: {solution.get("title")}
- Description: {solution.get("description")}
- Mechanism: {solution.get("mechanism")}
- Tech Stack: {tech_stack_str}
- Target User: {solution.get("target_user")}
- Revenue Model: {solution.get("revenue_model")}

### Database Requirements:
{db_directive}

### Problem Context:
- Title: {problem.get("title")}
- Description: {problem.get("description")}
- Target User: {problem.get("target_user")}
- Core Pain: {problem.get("core_pain")}
- Market Context: {problem.get("market_context")}

### Session & Maturity:
- Industry: {session.get("industry")}
- Location: {session.get("location")}
- Maturity Level: {maturity_level} (Maturity details: {maturity.get("label", "Standard")})

Generate a complete, specific, and professional Technical Requirements Document (TRD) in Markdown. Detail key API route endpoints, JSON payloads, third-party libraries, and database indexing strategies using: {tech_stack_str}."""

    return system_prompt, user_prompt
