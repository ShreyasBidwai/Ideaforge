def build_sprint_prompts_prompt(context: dict, documents: dict[str, str]) -> str:
    """
    Build the sprint generation prompt for Claude Code.
    context: solution, problem, session data
    documents: dict of doc_type -> content
    Returns: single prompt string
    """
    tech_stack_str = ', '.join(context['solution']['tech_stack']) if isinstance(context['solution']['tech_stack'], list) else str(context['solution']['tech_stack'])
    
    prompt = f"""You are an expert software architect generating a sprint breakdown and coding task prompts for an AI coding agent (Claude Code).

OUTPUT FORMAT: Return ONLY valid JSON. No markdown fences, no preamble, no explanation. Just the raw JSON object.

CRITICAL RULES FOR TASK PROMPTS:
1. Each task prompt must be COMPLETELY SELF-CONTAINED. The AI agent executing it has ZERO memory of previous tasks. It can only read files that exist on disk from previous tasks.
2. Every prompt must specify EXACT file paths to create or modify.
3. Every prompt must include complete test cases with exact test file paths and test run commands.
4. Prompts must be ordered so each task builds on FILES created by previous tasks (not on memory).
5. Each prompt should create a SMALL, testable unit of work.
6. Sprint 1, Task 1 MUST ALWAYS be a full project scaffold — create the directory structure, init package managers (package.json, requirements.txt), create base config files, create a hello world health endpoint with a passing test. The project directory will be completely empty.
7. Test commands must be specific: "cd backend && python -m pytest tests/test_specific_file.py -v" not just "run tests".
8. Every prompt must include the full tech stack context and project folder structure as reference since the agent has no memory.
9. Each prompt must include a .env.example or reference to config if the task needs environment variables.

PROJECT CONTEXT:
- Name: {context['solution']['title']}
- Industry: {context['session']['industry']}
- Location: {context['session'].get('location', 'Not available')}
- Maturity Level: {context['session']['maturity_level']}
- Tech Stack: {tech_stack_str}

ARCHITECTURE DOCUMENT:
{documents.get('architecture', 'Not available')}

PRODUCT REQUIREMENTS (PRD):
{documents.get('prd', 'Not available')}

TECHNICAL REQUIREMENTS (TRD):
{documents.get('trd', 'Not available')}

SPRINT PLAN:
{documents.get('sprint_plan', 'Not available')}

ENGINEERING STANDARDS:
{documents.get('engineering_standards', 'Not available')}

JSON SCHEMA TO FOLLOW:
{{
  "sprints": [
    {{
      "sprint_number": 1,
      "name": "Sprint name",
      "description": "What this sprint delivers",
      "tasks": [
        {{
          "task_number": 1,
          "name": "Short descriptive task name",
          "prompt": "The self-contained prompt text. Must include: project context, file paths to create/modify, complete code patterns, complete test cases with file paths, and test run commands. Word count: 100-150 words.",
          "test_command": "cd backend && python -m pytest tests/test_xxx.py -v",
          "expected_test_count": 8
        }}
      ]
    }}
  ],
  "total_tasks": 10,
  "total_sprints": 3,
  "estimated_total_tests": 80
}}

Generate 2-4 sprints with 2-4 tasks each. Each task prompt must be self-contained and detailed enough that an AI agent with NO prior context can execute it by reading only the prompt and existing files on disk. Keep prompts focused and compact to avoid generation timeouts."""
    return prompt


def build_sprint_prompts_disk_prompt(context: dict) -> str:
    """
    Build the sprint generation prompt that instructs Claude Code to read docs from local disk CWD.
    """
    tech_stack_str = ', '.join(context['solution']['tech_stack']) if isinstance(context['solution']['tech_stack'], list) else str(context['solution']['tech_stack'])
    
    prompt = f"""You are an expert software architect generating a sprint breakdown and coding task prompts for an AI coding agent (Claude Code).

To generate this sprint breakdown, first read the project specification documents from the `docs/` folder in the current directory:
1. `docs/architecture.md` (Architecture Document)
2. `docs/prd.md` (Product Requirements Document)
3. `docs/trd.md` (Technical Requirements Document)
4. `docs/sprint_plan.md` (High Level Sprint Plan)
5. `docs/engineering_standards.md` (Engineering Standards)

OUTPUT FORMAT: Return ONLY valid JSON. No markdown fences, no preamble, no explanation. Just the raw JSON object.

CRITICAL RULES FOR TASK PROMPTS:
1. Each task prompt must be COMPLETELY SELF-CONTAINED. The AI agent executing it has ZERO memory of previous tasks. It can only read files that exist on disk from previous tasks.
2. Every prompt must specify EXACT file paths to create or modify.
3. Every prompt must include complete test cases with exact test file paths and test run commands.
4. Prompts must be ordered so each task builds on FILES created by previous tasks (not on memory).
5. Each prompt should create a SMALL, testable unit of work.
6. Sprint 1, Task 1 MUST ALWAYS be a full project scaffold — create the directory structure, init package managers (package.json, requirements.txt), create base config files, create a hello world health endpoint with a passing test. The project directory will be completely empty.
7. Test commands must be specific: "cd backend && python -m pytest tests/test_specific_file.py -v" not just "run tests".
8. Every prompt must include the full tech stack context and project folder structure as reference since the agent has no memory.
9. Each prompt must include a .env.example or reference to config if the task needs environment variables.

PROJECT CONTEXT:
- Name: {context['solution']['title']}
- Industry: {context['session']['industry']}
- Location: {context['session'].get('location', 'Not available')}
- Maturity Level: {context['session']['maturity_level']}
- Tech Stack: {tech_stack_str}

JSON SCHEMA TO FOLLOW:
{{
  "sprints": [
    {{
      "sprint_number": 1,
      "name": "Sprint name",
      "description": "What this sprint delivers",
      "tasks": [
        {{
          "task_number": 1,
          "name": "Short descriptive task name",
          "prompt": "The self-contained prompt text. Must include: project context, file paths to create/modify, complete code patterns, complete test cases with file paths, and test run commands. Word count: 100-150 words.",
          "test_command": "cd backend && python -m pytest tests/test_xxx.py -v",
          "expected_test_count": 8
        }}
      ]
    }}
  ],
  "total_tasks": 10,
  "total_sprints": 3,
  "estimated_total_tests": 80
}}

Generate 2-4 sprints with 2-4 tasks each based on the documents in the `docs/` folder. Each task prompt must be self-contained and detailed enough that an AI agent with NO prior context can execute it by reading only the prompt and existing files on disk. Keep prompts focused and compact to avoid generation timeouts."""
    return prompt

