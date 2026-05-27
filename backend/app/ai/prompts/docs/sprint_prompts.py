def build_sprint_prompts_prompt(context: dict, architecture_doc: str, prd_doc: str, trd_doc: str) -> tuple[str, str]:
    """
    Generate the sprint breakdown and individual task prompts.
    
    This is the MOST IMPORTANT prompt in the system.
    The AI must produce self-contained, explicit prompts that Claude Code
    can execute without any prior context — because each claude -p call
    is a fresh session.
    
    Each prompt must include:
    - Explicit file paths to create/modify
    - Explicit code patterns and schemas
    - Explicit test cases with test file paths and test commands
    - Acceptance criteria
    - NO references to "previous prompt" or "as we did before"
    """
    
    system_prompt = """You are an expert software architect who creates sprint breakdowns and coding prompts for AI coding agents.

CRITICAL RULES:
1. Return ONLY valid JSON. No markdown, no preamble.
2. Each task prompt must be COMPLETELY SELF-CONTAINED. The AI agent that executes it has NO memory of previous tasks. It can only read existing files in the project directory.
3. Every prompt must specify EXACT file paths to create or modify.
4. Every prompt must include test cases with exact test file paths and test run commands.
5. Prompts must be ordered so each task builds on files created by previous tasks.
6. Each prompt should create a SMALL, testable unit of work — not an entire feature.
7. Include the full tech stack and folder structure context in EVERY prompt that needs it.
8. Test commands must be specific: "cd backend && python -m pytest tests/test_specific_file.py -v" not just "run tests".

JSON Schema:
{
  "sprints": [
    {
      "sprint_number": 1,
      "name": "Sprint name",
      "description": "What this sprint delivers",
      "tasks": [
        {
          "task_number": 1,
          "name": "Short task name",
          "prompt": "The FULL prompt text to send to claude -p. Must be self-contained. Include all file paths, schemas, patterns, and test cases.",
          "test_command": "cd backend && python -m pytest tests/test_xxx.py -v",
          "expected_test_count": 8,
          "estimated_tokens": 5000
        }
      ]
    }
  ],
  "total_tasks": 45,
  "total_sprints": 6,
  "estimated_total_tests": 300
}"""

    user_prompt = f"""Based on the following project documentation, generate a complete sprint breakdown with self-contained task prompts.

PROJECT CONTEXT:
- Solution: {context['solution']['title']}
- Tech Stack: {', '.join(context['solution']['tech_stack'])}
- Industry: {context['session']['industry']}
- Maturity: {context['session']['maturity_level']}

ARCHITECTURE DOCUMENT:
{architecture_doc[:3000]}

PRD (KEY REQUIREMENTS):
{prd_doc[:2000]}

TRD (TECHNICAL DETAILS):
{trd_doc[:2000]}

Generate 4-8 sprints with 5-10 tasks each. Each task prompt must be self-contained and include test cases."""

    return system_prompt, user_prompt
