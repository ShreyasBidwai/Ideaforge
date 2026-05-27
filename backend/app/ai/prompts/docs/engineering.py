def build_engineering_prompt(context: dict) -> tuple[str, str]:
    solution = context.get("solution") or {}
    problem = context.get("problem") or {}
    session = context.get("session") or {}
    maturity = context.get("maturity_config") or {}

    tech_stack_str = ", ".join(solution.get("tech_stack", []))

    system_prompt = f"""You are a Principal Developer Advocate and QA Director. Your job is to generate a comprehensive Engineering Standards and coding guidelines document for the proposed solution.
Your output must be in clean, well-structured Markdown.
Address coding standards, naming conventions, project directory structure, code review checklists, testing requirements, CI/CD pipeline, and error handling patterns using: {tech_stack_str}."""

    user_prompt = f"""Generate a detailed Engineering Standards document using this context:

### Solution Context:
- Title: {solution.get("title")}
- Description: {solution.get("description")}
- Mechanism: {solution.get("mechanism")}
- Tech Stack: {tech_stack_str}
- Target User: {solution.get("target_user")}
- Revenue Model: {solution.get("revenue_model")}

### Problem Context:
- Title: {problem.get("title")}
- Description: {problem.get("description")}
- Target User: {problem.get("target_user")}
- Core Pain: {problem.get("core_pain")}
- Market Context: {problem.get("market_context")}

### Session & Maturity:
- Industry: {session.get("industry")}
- Location: {session.get("location")}
- Maturity Level: {session.get("maturity_level")} (Maturity details: {maturity.get("label", "Standard")})

Generate a complete, specific, and professional Engineering Standards document in Markdown. Ensure the layout details folder conventions, testing paradigms, code documentation styles, and exception handling specific to: {tech_stack_str}."""

    return system_prompt, user_prompt
