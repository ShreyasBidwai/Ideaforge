def build_sprint_plan_prompt(context: dict) -> tuple[str, str]:
    solution = context.get("solution") or {}
    problem = context.get("problem") or {}
    session = context.get("session") or {}
    maturity = context.get("maturity_config") or {}

    tech_stack_str = ", ".join(solution.get("tech_stack", []))

    system_prompt = """You are an Agile Project Manager and Scrum Master. Your job is to generate a comprehensive Sprint Plan for building the proposed solution.
Your output must be in clean, well-structured Markdown.
Address the project roadmap, sprint milestones, sprint durations, and detail individual tasks, test descriptions, and acceptance criteria."""

    user_prompt = f"""Generate a detailed Sprint Plan using this context:

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

Generate a complete, specific, and professional Sprint Plan in Markdown. Detail Sprint 1, Sprint 2, Sprint 3, etc. with concrete objectives, backlog items, task definitions, and target testing strategies using: {tech_stack_str}."""

    return system_prompt, user_prompt
