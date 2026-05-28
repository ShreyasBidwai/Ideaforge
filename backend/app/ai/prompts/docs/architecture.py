def get_database_directive(maturity_level: str, tech_stack: list[str]) -> str:
    """Return the database instruction block to embed in generation prompts."""
    if maturity_level in ("poc", "mvp"):
        return (
            "DATABASE REQUIREMENT (MANDATORY):\n"
            "- Use SQLite as the database. It must require ZERO external setup.\n"
            "- The database file MUST live inside the project folder at ./app.db\n"
            "- If using SQLAlchemy async, the connection string is: "
            "sqlite+aiosqlite:///./app.db and the dependency is aiosqlite.\n"
            "- If using a sync stack, use the built-in sqlite3 / standard SQLite driver.\n"
            "- Put the connection string in a .env file as DATABASE_URL so a user can "
            "later switch to PostgreSQL by changing one line.\n"
            "- Do NOT require Docker, a running database server, or any system install "
            "for the database.\n"
            "- Generate database tables automatically on app startup if they do not "
            "exist (e.g. Base.metadata.create_all or Alembic auto-run), so the app works "
            "on first run with an empty ./app.db.\n"
        )
    else:
        return (
            "DATABASE REQUIREMENT:\n"
            "- Use PostgreSQL. Put the connection string in .env as DATABASE_URL.\n"
            "- Provide an Alembic migration setup.\n"
            "- Include a .env.example with a sample PostgreSQL DATABASE_URL.\n"
            "- ALSO include a commented SQLite fallback line in .env.example so the "
            "project can run locally without PostgreSQL if needed.\n"
        )


def build_architecture_prompt(context: dict) -> tuple[str, str]:
    solution = context.get("solution") or {}
    problem = context.get("problem") or {}
    evaluation = context.get("evaluation") or {}
    session = context.get("session") or {}
    maturity = context.get("maturity_config") or {}

    tech_stack = solution.get("tech_stack") or []
    tech_stack_str = ", ".join(tech_stack)
    maturity_level = session.get("maturity_level", "mvp")
    db_directive = get_database_directive(maturity_level, tech_stack)

    system_prompt = f"""You are a Principal Software Architect. Your job is to generate a comprehensive, production-grade Architecture Document for the proposed solution.
Your output must be in clean, well-structured Markdown.
Ensure you address the system architecture, component design, data flow, database schemas, deployment, and security.
You must use the specified technologies from the tech stack: {tech_stack_str}.

{db_directive}"""

    user_prompt = f"""Generate a detailed Architecture Document using this context:

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

Generate a complete, specific, and professional Architecture Document in Markdown. Incorporate structural design, databases, API designs, and system components explicitly referencing: {tech_stack_str}."""

    return system_prompt, user_prompt
