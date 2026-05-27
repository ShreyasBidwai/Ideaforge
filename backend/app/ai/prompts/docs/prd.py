def build_prd_prompt(context: dict) -> tuple[str, str]:
    solution = context.get("solution") or {}
    problem = context.get("problem") or {}
    session = context.get("session") or {}
    maturity = context.get("maturity_config") or {}

    tech_stack_str = ", ".join(solution.get("tech_stack", []))

    system_prompt = """You are a Senior Product Manager. Your job is to generate a detailed Product Requirements Document (PRD) for the proposed solution.
Your output must be in clean, well-structured Markdown.
Address the product vision, user personas, user stories, feature scope (MVP vs Future), metrics, and release criteria."""

    user_prompt = f"""Generate a detailed Product Requirements Document (PRD) using this context:

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

Generate a complete, specific, and professional Product Requirements Document (PRD) in Markdown. Make sure it targets the primary user persona and aligns with the defined revenue model and tech stack constraints."""

    return system_prompt, user_prompt
