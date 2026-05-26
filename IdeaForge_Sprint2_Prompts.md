# IdeaForge — Sprint 2 Prompts for Antigravity
## Discovery Engine Sprint (8 Tasks) — Each with Test Cases

**Pre-requisite:** Sprint 1 complete. All 65 tests passing. Backend running on :8000, Frontend on :5173, Auth working end-to-end.

---

## ⚡ PROMPT S2-01: Project Maturity Level & Session Enhancement

```
Enhance the IdeaForge backend to support Project Maturity Levels — a setting that controls the depth and rigor of AI-generated outputs throughout the entire pipeline.

The project uses FastAPI + SQLAlchemy async + PostgreSQL + Pydantic. Existing models are in backend/app/models/. Existing schemas in backend/app/schemas/.

## Maturity Level Definitions

Create an enum and configuration for these 4 levels:

| Level Code | Label | Description | AI Behavior |
|------------|-------|-------------|-------------|
| poc | Proof of Concept | Quick validation, speed over rigor | 3 pain points, 2 problem statements, 3 solution candidates, lightweight evaluation (rubric only, no devil's advocate/ACH), temperature 0.9 |
| mvp | Minimum Viable Product | Balanced depth, core features focus | 5 pain points, 2-3 problem statements, 4 solution candidates, standard evaluation (rubric + scoring + basic attack, no ACH), temperature 0.7 |
| pre_production | Pre-Production | Full rigor, production considerations | 6-8 pain points, 3 problem statements, 5 solution candidates, full evaluation protocol (all 8 steps), temperature 0.5 |
| production | Production-Grade | Enterprise-ready, compliance, security focus | 8-10 pain points, 3 problem statements, 5 solution candidates, full evaluation protocol + security/compliance criteria auto-added to rubric, temperature 0.3 |

## Files to Create/Modify

### backend/app/core/maturity.py
```python
from enum import Enum
from pydantic import BaseModel

class MaturityLevel(str, Enum):
    POC = "poc"
    MVP = "mvp"
    PRE_PRODUCTION = "pre_production"
    PRODUCTION = "production"

class MaturityConfig(BaseModel):
    level: MaturityLevel
    label: str
    pain_point_count: tuple[int, int]  # (min, max)
    problem_statement_count: int
    solution_candidate_count: int
    evaluation_steps: list[str]  # which evaluation steps to run
    temperature: float
    include_security_criteria: bool
    include_compliance_criteria: bool
    description: str

MATURITY_CONFIGS: dict[MaturityLevel, MaturityConfig] = {
    # ... define all 4 configs as per table above
}

def get_maturity_config(level: MaturityLevel) -> MaturityConfig:
    return MATURITY_CONFIGS[level]
```

### Modify backend/app/models/session.py
Add these fields to the Session model:
- maturity_level: String(50), default="mvp", not null
- tech_stack_preferences: JSON, nullable (user's preferred tech stack, stored as JSON array of strings)

### backend/app/schemas/session.py (create new file)
- SessionCreate: industry (str), location (str), maturity_level (MaturityLevel, default="mvp")
- SessionUpdate: maturity_level (optional), tech_stack_preferences (optional list[str])
- SessionResponse: all session fields + maturity_config (computed from level)
- MaturityLevelInfo: level, label, description, pain_point_count, problem_statement_count, solution_candidate_count, evaluation_steps

### backend/app/api/v1/maturity.py — Maturity Level endpoints
- GET /api/v1/maturity-levels — Return all 4 maturity levels with their configs (public info endpoint, useful for frontend dropdowns)

### Modify backend/app/api/v1/router.py
- Include maturity router

### Generate Alembic migration for the new Session fields
`alembic revision --autogenerate -m "add_maturity_level_to_sessions"`
`alembic upgrade head`

## Test Cases — Create backend/tests/test_s2_01_maturity.py

```python
import pytest

# TEST 1: All maturity levels are defined
def test_all_maturity_levels_exist():
    """All 4 maturity levels should be defined in the enum"""
    from backend.app.core.maturity import MaturityLevel
    assert MaturityLevel.POC == "poc"
    assert MaturityLevel.MVP == "mvp"
    assert MaturityLevel.PRE_PRODUCTION == "pre_production"
    assert MaturityLevel.PRODUCTION == "production"

# TEST 2: Maturity configs have correct defaults
def test_maturity_config_values():
    """Each maturity level should have a valid config"""
    from backend.app.core.maturity import get_maturity_config, MaturityLevel
    poc = get_maturity_config(MaturityLevel.POC)
    assert poc.temperature == 0.9
    assert poc.solution_candidate_count == 3
    assert poc.include_security_criteria is False
    
    prod = get_maturity_config(MaturityLevel.PRODUCTION)
    assert prod.temperature == 0.3
    assert prod.solution_candidate_count == 5
    assert prod.include_security_criteria is True
    assert prod.include_compliance_criteria is True

# TEST 3: POC has fewer evaluation steps than production
def test_poc_fewer_steps_than_production():
    """POC should skip devil's advocate and ACH"""
    from backend.app.core.maturity import get_maturity_config, MaturityLevel
    poc = get_maturity_config(MaturityLevel.POC)
    prod = get_maturity_config(MaturityLevel.PRODUCTION)
    assert len(poc.evaluation_steps) < len(prod.evaluation_steps)
    assert "devils_advocate" not in poc.evaluation_steps
    assert "ach_analysis" not in poc.evaluation_steps
    assert "devils_advocate" in prod.evaluation_steps
    assert "ach_analysis" in prod.evaluation_steps

# TEST 4: GET /maturity-levels returns all 4 levels
async def test_get_maturity_levels(client):
    """GET /api/v1/maturity-levels should return all 4 levels with descriptions"""
    response = await client.get("/api/v1/maturity-levels")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 4
    levels = {item["level"] for item in data}
    assert levels == {"poc", "mvp", "pre_production", "production"}
    for item in data:
        assert "label" in item
        assert "description" in item
        assert "evaluation_steps" in item

# TEST 5: Session model now has maturity_level field
def test_session_has_maturity_field():
    """Session model should have maturity_level column"""
    from sqlalchemy import inspect
    from backend.app.models.session import Session
    columns = {c.key for c in inspect(Session).columns}
    assert "maturity_level" in columns
    assert "tech_stack_preferences" in columns

# TEST 6: Session defaults to MVP maturity
def test_session_default_maturity():
    """New session should default to MVP maturity level"""
    from backend.app.models.session import Session
    from sqlalchemy import inspect
    mapper = inspect(Session)
    maturity_col = next(c for c in mapper.columns if c.key == "maturity_level")
    assert str(maturity_col.default.arg) == "mvp"

# TEST 7: SessionCreate schema validates maturity level
def test_session_create_schema_validation():
    """SessionCreate should reject invalid maturity levels"""
    from backend.app.schemas.session import SessionCreate
    from pydantic import ValidationError
    # Valid
    s = SessionCreate(industry="Fintech", location="India", maturity_level="poc")
    assert s.maturity_level == "poc"
    # Invalid
    with pytest.raises(ValidationError):
        SessionCreate(industry="Fintech", location="India", maturity_level="invalid_level")
```

Run: `cd backend && python -m pytest tests/test_s2_01_maturity.py -v`
All 7 tests must pass.
```

---

## ⚡ PROMPT S2-02: Tech Stack Selection Model & API

```
Add tech stack selection capability to IdeaForge. Users should be able to specify preferred technologies when creating a session, and later refine the tech stack for approved solutions.

The project uses FastAPI + SQLAlchemy async + PostgreSQL. Session model already has tech_stack_preferences (JSON) field from S2-01.

## Files to Create/Modify

### backend/app/core/tech_stacks.py — Predefined Tech Stack Registry

Define a registry of common tech stacks organized by category. This is used for autocomplete and suggestions in the frontend.

```python
TECH_STACK_REGISTRY = {
    "frontend": {
        "frameworks": ["React", "Next.js", "Vue.js", "Nuxt.js", "Angular", "Svelte", "SvelteKit", "Astro", "Remix"],
        "styling": ["Tailwind CSS", "CSS Modules", "Styled Components", "Material UI", "Chakra UI", "Ant Design", "shadcn/ui"],
        "state": ["Zustand", "Redux Toolkit", "Jotai", "Recoil", "MobX", "Pinia", "TanStack Query"],
        "mobile": ["React Native", "Flutter", "Swift/SwiftUI", "Kotlin/Jetpack Compose", "Expo"],
    },
    "backend": {
        "frameworks": ["FastAPI", "Django", "Flask", "Express.js", "NestJS", "Spring Boot", "Go Gin", "Ruby on Rails", "Laravel", "ASP.NET Core"],
        "languages": ["Python", "TypeScript/Node.js", "Go", "Java", "Rust", "Ruby", "PHP", "C#", "Kotlin"],
    },
    "database": {
        "relational": ["PostgreSQL", "MySQL", "SQLite", "SQL Server", "CockroachDB"],
        "nosql": ["MongoDB", "DynamoDB", "Firestore", "CouchDB", "Cassandra"],
        "cache": ["Redis", "Memcached", "Valkey"],
        "vector": ["Pinecone", "Weaviate", "Milvus", "pgvector", "ChromaDB"],
    },
    "infrastructure": {
        "cloud": ["AWS", "Google Cloud", "Azure", "Vercel", "Netlify", "Railway", "Fly.io", "DigitalOcean"],
        "containers": ["Docker", "Kubernetes", "Docker Compose"],
        "ci_cd": ["GitHub Actions", "GitLab CI", "Jenkins", "CircleCI"],
    },
    "ai_ml": {
        "providers": ["OpenAI API", "Anthropic Claude API", "Google Gemini API", "Groq", "Mistral", "Ollama", "Hugging Face"],
        "frameworks": ["LangChain", "LlamaIndex", "Haystack", "Semantic Kernel", "CrewAI"],
    },
}
```

### backend/app/api/v1/tech_stacks.py — Tech Stack endpoints
- GET /api/v1/tech-stacks — Return the full registry (for frontend autocomplete)
- GET /api/v1/tech-stacks/search?q={query} — Search/filter tech stacks by name (case-insensitive partial match across all categories)
- GET /api/v1/tech-stacks/categories — Return just the category names and subcategory names

### backend/app/schemas/tech_stack.py
- TechStackRegistry: the full nested dict structure
- TechStackSearchResult: name (str), category (str), subcategory (str)
- TechStackPreference: a flat list of selected tech names as strings

### Update backend/app/api/v1/router.py — Include tech_stacks router

## Test Cases — Create backend/tests/test_s2_02_tech_stacks.py

```python
import pytest

# TEST 1: Registry contains all major categories
def test_registry_categories():
    """Registry should have frontend, backend, database, infrastructure, ai_ml"""
    from backend.app.core.tech_stacks import TECH_STACK_REGISTRY
    assert "frontend" in TECH_STACK_REGISTRY
    assert "backend" in TECH_STACK_REGISTRY
    assert "database" in TECH_STACK_REGISTRY
    assert "infrastructure" in TECH_STACK_REGISTRY
    assert "ai_ml" in TECH_STACK_REGISTRY

# TEST 2: Each category has subcategories with items
def test_registry_has_items():
    """Each category should have at least one subcategory with at least one item"""
    from backend.app.core.tech_stacks import TECH_STACK_REGISTRY
    for category, subcats in TECH_STACK_REGISTRY.items():
        assert len(subcats) > 0, f"{category} has no subcategories"
        for subcat, items in subcats.items():
            assert len(items) > 0, f"{category}.{subcat} has no items"

# TEST 3: GET /tech-stacks returns full registry
async def test_get_full_registry(client, auth_headers):
    """GET /api/v1/tech-stacks should return the complete registry"""
    response = await client.get("/api/v1/tech-stacks", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "frontend" in data
    assert "backend" in data

# TEST 4: Search finds matching technologies
async def test_search_tech_stacks(client, auth_headers):
    """Search should return matching technologies across categories"""
    response = await client.get("/api/v1/tech-stacks/search?q=react", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    names = [item["name"].lower() for item in data]
    assert any("react" in name for name in names)

# TEST 5: Search is case-insensitive
async def test_search_case_insensitive(client, auth_headers):
    """Search should be case-insensitive"""
    r1 = await client.get("/api/v1/tech-stacks/search?q=PYTHON", headers=auth_headers)
    r2 = await client.get("/api/v1/tech-stacks/search?q=python", headers=auth_headers)
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert len(r1.json()) == len(r2.json())

# TEST 6: Search with no match returns empty
async def test_search_no_match(client, auth_headers):
    """Search with gibberish should return empty array"""
    response = await client.get("/api/v1/tech-stacks/search?q=xyznonexistent", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 0

# TEST 7: Categories endpoint returns structure
async def test_get_categories(client, auth_headers):
    """GET /api/v1/tech-stacks/categories should return category/subcategory names"""
    response = await client.get("/api/v1/tech-stacks/categories", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict) or isinstance(data, list)
```

Run: `cd backend && python -m pytest tests/test_s2_02_tech_stacks.py -v`
All 7 tests must pass.
```

---

## ⚡ PROMPT S2-03: Session CRUD API & Endpoints

```
Create the full Session CRUD API for IdeaForge. Sessions represent a discovery workflow — a user inputs an industry + location + maturity level and the system tracks the entire pipeline through that session.

The project uses FastAPI + SQLAlchemy async + PostgreSQL. Models exist: Session (with maturity_level, tech_stack_preferences fields). Auth system exists with get_current_user dependency.

## Files to Create

### backend/app/services/session_service.py — Business Logic
- async create_session(db, user_id: UUID, data: SessionCreate) -> Session
  - Create session with industry, location, maturity_level, status="discovery"
  - Save tech_stack_preferences if provided
- async get_session(db, session_id: UUID, user_id: UUID) -> Session
  - Return session, raise 404 if not found, 403 if not owned by user
- async get_user_sessions(db, user_id: UUID, page: int, per_page: int) -> PaginatedResponse
  - Return paginated sessions ordered by created_at desc
- async update_session(db, session_id: UUID, user_id: UUID, data: SessionUpdate) -> Session
  - Partial update (maturity_level, tech_stack_preferences, status)
- async delete_session(db, session_id: UUID, user_id: UUID) -> None
  - Soft delete or hard delete — your choice, just be consistent

### backend/app/api/v1/sessions.py — Session Routes
- POST /api/v1/sessions — Create session (requires auth)
- GET /api/v1/sessions — List user's sessions with pagination (requires auth)
- GET /api/v1/sessions/{id} — Get session by ID (requires auth, ownership check)
- PATCH /api/v1/sessions/{id} — Update session (requires auth, ownership check)
- DELETE /api/v1/sessions/{id} — Delete session (requires auth, ownership check)

### Update backend/app/schemas/session.py (if not already complete)
- SessionCreate: industry (str, required), location (str, required), maturity_level (MaturityLevel, default="mvp"), tech_stack_preferences (list[str] | None)
- SessionUpdate: maturity_level (optional), tech_stack_preferences (optional), status (optional)
- SessionResponse: all fields + maturity_config as nested object

### Update router.py to include sessions router

## Test Cases — Create backend/tests/test_s2_03_sessions.py

Write a conftest helper that registers + logs in a test user and returns auth headers.

```python
import pytest

# TEST 1: Create session successfully
async def test_create_session(client, auth_headers):
    """POST /sessions with valid data should create session"""
    response = await client.post("/api/v1/sessions", json={
        "industry": "Healthcare",
        "location": "Mumbai, India",
        "maturity_level": "mvp"
    }, headers=auth_headers)
    assert response.status_code in [200, 201]
    data = response.json()
    assert data["industry"] == "Healthcare"
    assert data["location"] == "Mumbai, India"
    assert data["maturity_level"] == "mvp"
    assert data["status"] == "discovery"

# TEST 2: Create session with tech stack preferences
async def test_create_session_with_tech_stack(client, auth_headers):
    """Session should store tech stack preferences"""
    response = await client.post("/api/v1/sessions", json={
        "industry": "Fintech",
        "location": "Bangalore, India",
        "maturity_level": "production",
        "tech_stack_preferences": ["React", "FastAPI", "PostgreSQL"]
    }, headers=auth_headers)
    assert response.status_code in [200, 201]
    data = response.json()
    assert data["tech_stack_preferences"] == ["React", "FastAPI", "PostgreSQL"]

# TEST 3: Create session defaults to MVP
async def test_create_session_default_mvp(client, auth_headers):
    """Session without maturity_level should default to mvp"""
    response = await client.post("/api/v1/sessions", json={
        "industry": "EdTech",
        "location": "Delhi, India"
    }, headers=auth_headers)
    assert response.status_code in [200, 201]
    assert response.json()["maturity_level"] == "mvp"

# TEST 4: List sessions with pagination
async def test_list_sessions(client, auth_headers):
    """GET /sessions should return user's sessions paginated"""
    # Create 3 sessions
    for industry in ["Healthcare", "Fintech", "EdTech"]:
        await client.post("/api/v1/sessions", json={
            "industry": industry, "location": "India"
        }, headers=auth_headers)
    response = await client.get("/api/v1/sessions?page=1&per_page=2", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) <= 2
    assert "total" in data

# TEST 5: Get session by ID
async def test_get_session_by_id(client, auth_headers):
    """GET /sessions/{id} should return the session"""
    create = await client.post("/api/v1/sessions", json={
        "industry": "Logistics", "location": "India"
    }, headers=auth_headers)
    session_id = create.json()["id"]
    response = await client.get(f"/api/v1/sessions/{session_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == session_id

# TEST 6: Get session returns 404 for non-existent
async def test_get_nonexistent_session(client, auth_headers):
    """GET /sessions/{id} with fake ID should return 404"""
    import uuid
    fake_id = str(uuid.uuid4())
    response = await client.get(f"/api/v1/sessions/{fake_id}", headers=auth_headers)
    assert response.status_code == 404

# TEST 7: Update session maturity level
async def test_update_session(client, auth_headers):
    """PATCH /sessions/{id} should update fields"""
    create = await client.post("/api/v1/sessions", json={
        "industry": "AgriTech", "location": "India"
    }, headers=auth_headers)
    session_id = create.json()["id"]
    response = await client.patch(f"/api/v1/sessions/{session_id}", json={
        "maturity_level": "production"
    }, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["maturity_level"] == "production"

# TEST 8: Delete session
async def test_delete_session(client, auth_headers):
    """DELETE /sessions/{id} should remove session"""
    create = await client.post("/api/v1/sessions", json={
        "industry": "Retail", "location": "India"
    }, headers=auth_headers)
    session_id = create.json()["id"]
    response = await client.delete(f"/api/v1/sessions/{session_id}", headers=auth_headers)
    assert response.status_code in [200, 204]
    # Verify it's gone
    get_response = await client.get(f"/api/v1/sessions/{session_id}", headers=auth_headers)
    assert get_response.status_code == 404

# TEST 9: Cannot access another user's session
async def test_session_ownership(client, auth_headers, other_auth_headers):
    """User A should not access User B's session"""
    create = await client.post("/api/v1/sessions", json={
        "industry": "Gaming", "location": "India"
    }, headers=auth_headers)
    session_id = create.json()["id"]
    response = await client.get(f"/api/v1/sessions/{session_id}", headers=other_auth_headers)
    assert response.status_code == 403

# TEST 10: Session requires authentication
async def test_session_requires_auth(client):
    """POST /sessions without auth should return 401"""
    response = await client.post("/api/v1/sessions", json={
        "industry": "Healthcare", "location": "India"
    })
    assert response.status_code in [401, 403]

# TEST 11: Sessions ordered by newest first
async def test_sessions_ordered_newest_first(client, auth_headers):
    """GET /sessions should return newest first"""
    await client.post("/api/v1/sessions", json={"industry": "First", "location": "India"}, headers=auth_headers)
    await client.post("/api/v1/sessions", json={"industry": "Second", "location": "India"}, headers=auth_headers)
    response = await client.get("/api/v1/sessions", headers=auth_headers)
    items = response.json()["items"]
    assert items[0]["industry"] == "Second"  # newest first
```

Run: `cd backend && python -m pytest tests/test_s2_03_sessions.py -v`
All 11 tests must pass.

Note: You'll need to update conftest.py to add `auth_headers` and `other_auth_headers` fixtures that register two different users, log them in, and return {"Authorization": "Bearer {token}"} dicts.
```

---

## ⚡ PROMPT S2-04: AI Pain Point Discovery Service

```
Build the AI-powered pain point discovery service for IdeaForge. Given an industry + location + maturity level, this service calls the Gemini API to discover real pain points in that industry.

The project uses FastAPI + SQLAlchemy async + Google Gemini AI (google-generativeai SDK). The GeminiProvider class exists in backend/app/ai/provider.py. MaturityConfig is in backend/app/core/maturity.py.

## Files to Create

### backend/app/ai/prompts/pain_points.py — Prompt Template

Create a function that builds the system prompt and user prompt for pain point discovery:

```python
def build_pain_point_prompt(industry: str, location: str, maturity_config: MaturityConfig) -> tuple[str, str]:
    """Returns (system_prompt, user_prompt) for pain point discovery"""
    
    min_count, max_count = maturity_config.pain_point_count
    
    system_prompt = f"""You are an expert industry analyst and startup researcher. Your job is to identify real, specific, actionable pain points in a given industry and location.

Rules:
- Return ONLY valid JSON. No markdown, no preamble, no explanation.
- Identify {min_count} to {max_count} pain points.
- Each pain point must be specific and grounded in reality — not generic platitudes.
- Pain points must be relevant to the specific location/geography (regulations, infrastructure, culture, market maturity).
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
    
    return system_prompt, user_prompt
```

### backend/app/services/pain_point_service.py — Pain Point Service

```python
class PainPointService:
    def __init__(self, ai_provider: AIProvider, db: AsyncSession):
        self.ai = ai_provider
        self.db = db
    
    async def discover_pain_points(self, session_id: UUID, industry: str, location: str, maturity_level: MaturityLevel) -> list[PainPoint]:
        """
        1. Get maturity config
        2. Build prompt from template
        3. Call Gemini AI with structured JSON output
        4. Parse and validate response against Pydantic schema
        5. If validation fails, retry once with error context
        6. Store pain points in session.pain_points (JSON field)
        7. Update session status to "problem_generation"
        8. Return parsed pain points
        """
```

### backend/app/schemas/pain_point.py — Pydantic Schemas
- PainPointSchema: name (str), description (str), severity (int, 1-10), affected_stakeholders (list[str]), evidence (str)
- PainPointResponse: pain_points (list[PainPointSchema])
- DiscoverRequest: (empty body — session already has industry/location)

### backend/app/api/v1/pain_points.py — Pain Point Routes
- POST /api/v1/sessions/{session_id}/discover — Trigger AI pain point discovery for this session
  - Requires auth + session ownership
  - Returns discovered pain points
  - Updates session.pain_points and session.status
- GET /api/v1/sessions/{session_id}/pain-points — Get stored pain points for session
  - Returns from database (cached), no AI call

### Update router.py to include pain_points router

## Test Cases — Create backend/tests/test_s2_04_pain_points.py

```python
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json

# ─── Prompt Template Tests ───

# TEST 1: Prompt template generates valid prompts
def test_prompt_template_generates():
    """build_pain_point_prompt should return (system_prompt, user_prompt) strings"""
    from backend.app.ai.prompts.pain_points import build_pain_point_prompt
    from backend.app.core.maturity import get_maturity_config, MaturityLevel
    config = get_maturity_config(MaturityLevel.MVP)
    system, user = build_pain_point_prompt("Healthcare", "Mumbai, India", config)
    assert isinstance(system, str)
    assert isinstance(user, str)
    assert "Healthcare" in user
    assert "Mumbai" in user
    assert "JSON" in system

# TEST 2: Prompt includes correct pain point count from maturity
def test_prompt_respects_maturity_count():
    """POC prompt should ask for fewer pain points than production"""
    from backend.app.ai.prompts.pain_points import build_pain_point_prompt
    from backend.app.core.maturity import get_maturity_config, MaturityLevel
    poc_sys, _ = build_pain_point_prompt("Fintech", "India", get_maturity_config(MaturityLevel.POC))
    prod_sys, _ = build_pain_point_prompt("Fintech", "India", get_maturity_config(MaturityLevel.PRODUCTION))
    # POC should reference smaller numbers than production
    assert "3" in poc_sys  # min count for POC
    assert "8" in prod_sys or "10" in prod_sys  # higher count for production

# TEST 3: Prompt enforces JSON-only output
def test_prompt_enforces_json():
    """System prompt must explicitly demand JSON-only output"""
    from backend.app.ai.prompts.pain_points import build_pain_point_prompt
    from backend.app.core.maturity import get_maturity_config, MaturityLevel
    system, _ = build_pain_point_prompt("EdTech", "India", get_maturity_config(MaturityLevel.MVP))
    assert "JSON" in system
    assert "no markdown" in system.lower() or "only valid json" in system.lower() or "only json" in system.lower()

# ─── Schema Validation Tests ───

# TEST 4: Valid pain point parses correctly
def test_valid_pain_point_schema():
    """PainPointSchema should accept valid data"""
    from backend.app.schemas.pain_point import PainPointSchema
    pp = PainPointSchema(
        name="High patient wait times",
        description="Patients wait 3+ hours in urban hospitals.",
        severity=8,
        affected_stakeholders=["Patients", "Hospital administrators"],
        evidence="NITI Aayog reports show average OPD wait of 3.2 hours."
    )
    assert pp.severity == 8

# TEST 5: Invalid severity rejected
def test_invalid_severity_rejected():
    """Severity outside 1-10 should be rejected"""
    from backend.app.schemas.pain_point import PainPointSchema
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        PainPointSchema(name="Test", description="Test", severity=15, affected_stakeholders=[], evidence="Test")

# ─── Service Tests (Mocked AI) ───

# TEST 6: Service calls AI and returns parsed pain points
async def test_discover_pain_points_success(client, auth_headers, mock_gemini):
    """POST /sessions/{id}/discover should call AI and return pain points"""
    # Create session first
    session = await client.post("/api/v1/sessions", json={
        "industry": "Healthcare", "location": "Mumbai, India"
    }, headers=auth_headers)
    session_id = session.json()["id"]
    
    # Mock AI response
    mock_gemini.return_value = json.dumps({
        "pain_points": [
            {
                "name": "Long patient wait times",
                "description": "Urban hospitals have 3+ hour wait times for OPD.",
                "severity": 8,
                "affected_stakeholders": ["Patients", "Doctors"],
                "evidence": "Government reports confirm this."
            },
            {
                "name": "Paper-based record keeping",
                "description": "90% of clinics still use paper records.",
                "severity": 7,
                "affected_stakeholders": ["Clinic staff", "Patients"],
                "evidence": "WHO India digital health survey."
            }
        ]
    })
    
    response = await client.post(f"/api/v1/sessions/{session_id}/discover", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "pain_points" in data
    assert len(data["pain_points"]) >= 2

# TEST 7: Discovery updates session status
async def test_discover_updates_session_status(client, auth_headers, mock_gemini):
    """After discovery, session status should update to problem_generation"""
    session = await client.post("/api/v1/sessions", json={
        "industry": "Fintech", "location": "India"
    }, headers=auth_headers)
    session_id = session.json()["id"]
    
    mock_gemini.return_value = json.dumps({"pain_points": [
        {"name": "Test", "description": "Test", "severity": 5, "affected_stakeholders": ["Users"], "evidence": "Data"}
    ]})
    
    await client.post(f"/api/v1/sessions/{session_id}/discover", headers=auth_headers)
    session_response = await client.get(f"/api/v1/sessions/{session_id}", headers=auth_headers)
    assert session_response.json()["status"] == "problem_generation"

# TEST 8: GET pain points returns cached data
async def test_get_cached_pain_points(client, auth_headers, mock_gemini):
    """GET /sessions/{id}/pain-points should return stored data without AI call"""
    session = await client.post("/api/v1/sessions", json={
        "industry": "EdTech", "location": "India"
    }, headers=auth_headers)
    session_id = session.json()["id"]
    
    mock_gemini.return_value = json.dumps({"pain_points": [
        {"name": "Test", "description": "Test", "severity": 5, "affected_stakeholders": ["Users"], "evidence": "Data"}
    ]})
    
    await client.post(f"/api/v1/sessions/{session_id}/discover", headers=auth_headers)
    mock_gemini.reset_mock()
    
    response = await client.get(f"/api/v1/sessions/{session_id}/pain-points", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()["pain_points"]) >= 1
    mock_gemini.assert_not_called()  # Should NOT call AI again

# TEST 9: Discovery requires session ownership
async def test_discover_requires_ownership(client, auth_headers, other_auth_headers, mock_gemini):
    """Cannot discover on another user's session"""
    session = await client.post("/api/v1/sessions", json={
        "industry": "Gaming", "location": "India"
    }, headers=auth_headers)
    session_id = session.json()["id"]
    response = await client.post(f"/api/v1/sessions/{session_id}/discover", headers=other_auth_headers)
    assert response.status_code == 403
```

Run: `cd backend && python -m pytest tests/test_s2_04_pain_points.py -v`
All 9 tests must pass.

Note: Add a `mock_gemini` fixture in conftest.py that patches the GeminiProvider.generate method with AsyncMock. This lets tests run without a real API key.
```

---

## ⚡ PROMPT S2-05: Frontend — Discovery Page UI

```
Build the Discovery page for IdeaForge — where users input an industry + location + maturity level and see AI-discovered pain points.

The project uses React 18 + TypeScript + Tailwind CSS + Framer Motion + Lucide React + Zustand + Vitest. Dark luxury design. API services exist in frontend/src/services/. Types defined in frontend/src/types/api.ts.

## Components to Build

### frontend/src/pages/Discovery.tsx — Main Discovery Page

**Layout — Two-phase view:**

**Phase 1: Input Form (shown when no active session)**
- Centered card on the page, max-w-2xl
- Heading: "Discover Industry Pain Points"
- Subtitle: "Enter an industry and location to uncover real problems worth solving"
- Fields:
  - Industry: text input with autocomplete/suggestions (common industries: Healthcare, Fintech, EdTech, Logistics, Agriculture, Real Estate, E-commerce, Manufacturing, Legal Tech, InsurTech, HR Tech, PropTech, FoodTech, CleanTech)
  - Location: text input with placeholder "e.g. Mumbai, India" or "United States"
  - Maturity Level: segmented button selector (4 options: POC, MVP, Pre-Production, Production)
    - Each option shows label + very short description on hover/selection
    - Default: MVP selected
  - Tech Stack Preferences (optional): multi-select tag input. User types, gets autocomplete from tech stack registry, selected techs appear as removable tags.
- "Start Discovery" button (full width, blue-600, large)

**Phase 2: Results (shown after discovery triggered)**
- Top: session info bar (industry pill, location pill, maturity badge)
- Main: pain point cards grid (2 columns on desktop, 1 on mobile)
- Bottom: "Generate Problem Statements" button (proceeds to next step)

### frontend/src/components/discovery/IndustryInput.tsx
- Text input with dropdown suggestion list
- Suggestions filter as user types
- User can type custom industry (not limited to suggestions)
- Keyboard navigation (arrow keys + enter to select)

### frontend/src/components/discovery/MaturitySelector.tsx
- 4 horizontal segments: POC | MVP | Pre-Prod | Production
- Selected segment: blue-600 bg, white text
- Unselected: bg-slate-800, slate-400 text
- Hover tooltip with description
- Framer-motion slide indicator on selection change

### frontend/src/components/discovery/TechStackInput.tsx
- Text input with autocomplete dropdown
- Fetches suggestions from GET /api/v1/tech-stacks/search?q=
- Selected items appear as removable tag pills below the input
- Tags: bg-blue-600/20, text-blue-400, X button to remove
- Debounced search (300ms)

### frontend/src/components/discovery/PainPointCard.tsx
- Card: bg-slate-800/50 border border-white/5 rounded-2xl p-6
- Top: severity badge (color-coded: 1-3 green, 4-6 amber, 7-10 red) + pain point name
- Body: description text (slate-300)
- Bottom row: stakeholder tags (small pills) + evidence text (italic, slate-400, smaller)
- Hover: subtle lift effect (translateY -2px, shadow increase)
- Framer-motion: stagger animation when cards appear (each card fades in 100ms after previous)

### frontend/src/components/discovery/PainPointSkeleton.tsx
- Skeleton loading card matching PainPointCard dimensions
- Animated shimmer effect (gradient moving left-to-right)
- Show 4-6 skeletons while AI is generating

### frontend/src/stores/discoveryStore.ts (Zustand)
```typescript
interface DiscoveryState {
  currentSession: Session | null;
  painPoints: PainPoint[];
  isDiscovering: boolean;
  error: string | null;
  createAndDiscover: (industry: string, location: string, maturityLevel: string, techStack: string[]) => Promise<void>;
  clearSession: () => void;
}
```

## Test Cases — Create frontend/src/__tests__/s2_05_discovery.test.tsx

```tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

// TEST 1: Discovery page renders input form
it('should render discovery form with all fields', async () => {
  const { default: Discovery } = await import('../pages/Discovery');
  render(<MemoryRouter><Discovery /></MemoryRouter>);
  expect(screen.getByText(/discover industry pain points/i)).toBeDefined();
  expect(screen.getByPlaceholderText(/industry/i) || screen.getByLabelText(/industry/i)).toBeDefined();
  expect(screen.getByPlaceholderText(/location/i) || screen.getByLabelText(/location/i)).toBeDefined();
  expect(screen.getByText(/start discovery/i)).toBeDefined();
});

// TEST 2: Maturity selector renders all 4 levels
it('should render all 4 maturity levels', async () => {
  const { default: MaturitySelector } = await import('../components/discovery/MaturitySelector');
  render(<MaturitySelector value="mvp" onChange={() => {}} />);
  expect(screen.getByText(/poc/i)).toBeDefined();
  expect(screen.getByText(/mvp/i)).toBeDefined();
  expect(screen.getByText(/pre-prod/i) || screen.getByText(/pre.production/i)).toBeDefined();
  expect(screen.getByText(/production/i)).toBeDefined();
});

// TEST 3: Maturity selector highlights selected level
it('should highlight the selected maturity level', async () => {
  const { default: MaturitySelector } = await import('../components/discovery/MaturitySelector');
  const onChange = vi.fn();
  render(<MaturitySelector value="mvp" onChange={onChange} />);
  const mvpButton = screen.getByText(/mvp/i);
  expect(mvpButton.closest('button')?.className || '').toContain('blue');
});

// TEST 4: Pain point card renders correctly
it('should render pain point card with all data', async () => {
  const { default: PainPointCard } = await import('../components/discovery/PainPointCard');
  render(<PainPointCard painPoint={{
    name: "Long wait times",
    description: "Patients wait 3+ hours",
    severity: 8,
    affected_stakeholders: ["Patients", "Doctors"],
    evidence: "Government data confirms this"
  }} />);
  expect(screen.getByText("Long wait times")).toBeDefined();
  expect(screen.getByText(/3\+ hours/)).toBeDefined();
  expect(screen.getByText("Patients")).toBeDefined();
});

// TEST 5: Severity badge shows correct color
it('should show red badge for high severity', async () => {
  const { default: PainPointCard } = await import('../components/discovery/PainPointCard');
  const { container } = render(<PainPointCard painPoint={{
    name: "Critical issue", description: "Very bad", severity: 9,
    affected_stakeholders: ["All"], evidence: "Real"
  }} />);
  // Severity badge should have red-ish styling for 9
  const badge = container.querySelector('[class*="red"]') || container.querySelector('[class*="rose"]');
  expect(badge).toBeDefined();
});

// TEST 6: Skeleton loading renders
it('should render skeleton loading cards', async () => {
  const { default: PainPointSkeleton } = await import('../components/discovery/PainPointSkeleton');
  const { container } = render(<PainPointSkeleton />);
  expect(container.querySelector('[class*="animate"]')).toBeDefined();
});

// TEST 7: Discovery store initializes correctly
it('should initialize discovery store with null session', async () => {
  const { useDiscoveryStore } = await import('../stores/discoveryStore');
  const state = useDiscoveryStore.getState();
  expect(state.currentSession).toBeNull();
  expect(state.painPoints).toEqual([]);
  expect(state.isDiscovering).toBe(false);
});

// TEST 8: Form validates required fields
it('should not submit without industry and location', async () => {
  const { default: Discovery } = await import('../pages/Discovery');
  render(<MemoryRouter><Discovery /></MemoryRouter>);
  const button = screen.getByText(/start discovery/i);
  fireEvent.click(button);
  await waitFor(() => {
    expect(screen.getByText(/required/i) || screen.getByText(/enter/i)).toBeDefined();
  });
});
```

Run: `cd frontend && npx vitest run src/__tests__/s2_05_discovery.test.tsx --reporter=verbose`
All 8 tests must pass.
```

---

## ⚡ PROMPT S2-06: SSE Streaming for AI Responses

```
Add Server-Sent Events (SSE) streaming support to IdeaForge so AI responses stream progressively to the frontend instead of blocking until completion.

## Backend Changes

### backend/app/core/streaming.py — SSE Utilities
- Create an SSE event formatter that yields properly formatted SSE strings
- Support event types: "progress" (status updates), "data" (partial results), "complete" (final result), "error" (failure)
- Format: `event: {type}\ndata: {json_data}\n\n`

### Modify backend/app/api/v1/pain_points.py
- Add a new endpoint: POST /api/v1/sessions/{session_id}/discover/stream
- Returns StreamingResponse with media_type="text/event-stream"
- Streams progress events:
  1. {"status": "starting", "message": "Analyzing {industry} industry in {location}..."}
  2. {"status": "calling_ai", "message": "Consulting AI for pain point analysis..."}
  3. {"status": "parsing", "message": "Processing discovered pain points..."}
  4. {"status": "complete", "data": {pain_points: [...]}} — final result with all pain points

### Modify backend/app/services/pain_point_service.py
- Add async generator version: async discover_pain_points_stream() that yields progress dicts

## Frontend Changes

### frontend/src/services/streamService.ts — SSE Client
```typescript
export async function streamDiscover(
  sessionId: string,
  onProgress: (status: string, message: string) => void,
  onComplete: (painPoints: PainPoint[]) => void,
  onError: (error: string) => void
): Promise<void> {
  // Use EventSource or fetch with ReadableStream to consume SSE
  // Parse each event and call appropriate callback
}
```

### frontend/src/components/discovery/StreamProgress.tsx
- Shows current AI status with animated progress indicator
- Steps: Analyzing → Consulting AI → Processing → Complete
- Each step has a check mark when done, spinner when active, gray when pending
- Framer-motion transitions between steps

### Update Discovery.tsx
- Use streaming endpoint instead of regular POST
- Show StreamProgress component while discovering
- Pain point cards appear one-by-one as they're processed (stagger animation)

## Test Cases — Create backend/tests/test_s2_06_streaming.py and frontend test

### Backend Tests:
```python
# TEST 1: SSE formatter produces correct format
def test_sse_format():
    """SSE events should be properly formatted"""
    from backend.app.core.streaming import format_sse_event
    event = format_sse_event("progress", {"status": "starting", "message": "Hello"})
    assert "event: progress" in event
    assert "data: " in event
    assert event.endswith("\n\n")

# TEST 2: SSE event data is valid JSON
def test_sse_data_is_json():
    """SSE data field should be parseable JSON"""
    from backend.app.core.streaming import format_sse_event
    import json
    event = format_sse_event("data", {"key": "value"})
    data_line = [l for l in event.split("\n") if l.startswith("data: ")][0]
    json_str = data_line.replace("data: ", "")
    parsed = json.loads(json_str)
    assert parsed["key"] == "value"

# TEST 3: Stream endpoint returns correct content type
async def test_stream_content_type(client, auth_headers, mock_gemini):
    """Stream endpoint should return text/event-stream"""
    import json
    session = await client.post("/api/v1/sessions", json={
        "industry": "Healthcare", "location": "India"
    }, headers=auth_headers)
    session_id = session.json()["id"]
    mock_gemini.return_value = json.dumps({"pain_points": [
        {"name": "Test", "description": "Test", "severity": 5, "affected_stakeholders": ["Users"], "evidence": "Data"}
    ]})
    response = await client.post(f"/api/v1/sessions/{session_id}/discover/stream", headers=auth_headers)
    assert response.headers.get("content-type", "").startswith("text/event-stream")

# TEST 4: Stream emits complete event with data
async def test_stream_emits_complete(client, auth_headers, mock_gemini):
    """Stream should end with a complete event containing pain points"""
    import json
    session = await client.post("/api/v1/sessions", json={
        "industry": "Fintech", "location": "India"
    }, headers=auth_headers)
    session_id = session.json()["id"]
    mock_gemini.return_value = json.dumps({"pain_points": [
        {"name": "KYC Friction", "description": "KYC takes too long", "severity": 7, "affected_stakeholders": ["Users"], "evidence": "RBI data"}
    ]})
    response = await client.post(f"/api/v1/sessions/{session_id}/discover/stream", headers=auth_headers)
    body = response.text if hasattr(response, 'text') else (await response.aread()).decode()
    assert "complete" in body
```

### Frontend Tests — frontend/src/__tests__/s2_06_streaming.test.tsx:
```tsx
// TEST 5: StreamProgress component renders steps
it('should render progress steps', async () => {
  const { default: StreamProgress } = await import('../components/discovery/StreamProgress');
  render(<StreamProgress currentStep="calling_ai" />);
  expect(screen.getByText(/analyzing/i) || screen.getByText(/consulting ai/i)).toBeDefined();
});

// TEST 6: StreamProgress shows active step with spinner
it('should show spinner on active step', async () => {
  const { default: StreamProgress } = await import('../components/discovery/StreamProgress');
  const { container } = render(<StreamProgress currentStep="calling_ai" />);
  expect(container.querySelector('[class*="animate-spin"]')).toBeDefined();
});
```

Run:
- Backend: `cd backend && python -m pytest tests/test_s2_06_streaming.py -v` (4 tests)
- Frontend: `cd frontend && npx vitest run src/__tests__/s2_06_streaming.test.tsx --reporter=verbose` (2 tests)
All 6 tests must pass.
```

---

## ⚡ PROMPT S2-07: Redis Caching Layer

```
Add Redis caching to IdeaForge for AI responses. Identical industry+location+maturity queries should return cached results instead of re-calling the AI.

The project uses FastAPI + Redis (redis-py async). Redis URL is in config.

## Files to Create

### backend/app/core/cache.py — Cache Service
```python
class CacheService:
    def __init__(self, redis_url: str):
        self.redis = None  # lazy connect
    
    async def connect(self):
        """Initialize async Redis connection"""
    
    async def get(self, key: str) -> str | None:
        """Get cached value by key"""
    
    async def set(self, key: str, value: str, ttl: int = 86400) -> None:
        """Set cached value with TTL (default 24 hours)"""
    
    async def delete(self, key: str) -> None:
        """Delete cached value"""
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
    
    @staticmethod
    def make_pain_point_key(industry: str, location: str, maturity: str) -> str:
        """Generate consistent cache key: 'pain_points:{industry}:{location}:{maturity}'"""
        # Normalize: lowercase, strip whitespace
    
    async def close(self):
        """Close Redis connection"""
```

### Modify backend/app/services/pain_point_service.py
- Before calling AI, check Redis cache
- After successful AI call, store in Redis with 24-hour TTL
- Cache key: `pain_points:{industry_normalized}:{location_normalized}:{maturity_level}`
- If cache hit, return cached data without AI call (skip SSE streaming, return instantly)

### Modify backend/app/main.py
- Initialize CacheService on startup, close on shutdown (lifespan handler)
- Make CacheService available as dependency

### Handle Redis being unavailable
- If Redis connection fails, log warning and skip caching (don't crash the app)
- AI calls should work fine without Redis — caching is an optimization, not a requirement

## Test Cases — Create backend/tests/test_s2_07_cache.py

```python
import pytest

# TEST 1: Cache key generation is consistent
def test_cache_key_consistent():
    """Same input should always produce same cache key"""
    from backend.app.core.cache import CacheService
    key1 = CacheService.make_pain_point_key("Healthcare", "Mumbai, India", "mvp")
    key2 = CacheService.make_pain_point_key("healthcare", "mumbai, india", "mvp")
    assert key1 == key2  # case-insensitive

# TEST 2: Cache key includes all parameters
def test_cache_key_includes_all_params():
    """Different maturity levels should produce different keys"""
    from backend.app.core.cache import CacheService
    key1 = CacheService.make_pain_point_key("Healthcare", "India", "mvp")
    key2 = CacheService.make_pain_point_key("Healthcare", "India", "production")
    assert key1 != key2

# TEST 3: Cache key normalizes whitespace
def test_cache_key_normalizes():
    """Extra whitespace should not affect cache key"""
    from backend.app.core.cache import CacheService
    key1 = CacheService.make_pain_point_key("Healthcare", "Mumbai, India", "mvp")
    key2 = CacheService.make_pain_point_key("  Healthcare  ", "  Mumbai,  India  ", "mvp")
    assert key1 == key2

# TEST 4: Cache set and get work (requires Redis running or mock)
async def test_cache_set_and_get(cache_service):
    """Set a value and get it back"""
    await cache_service.set("test_key", '{"data": "hello"}', ttl=60)
    result = await cache_service.get("test_key")
    assert result == '{"data": "hello"}'

# TEST 5: Cache returns None for missing key
async def test_cache_miss(cache_service):
    """Get on non-existent key returns None"""
    result = await cache_service.get("nonexistent_key_xyz")
    assert result is None

# TEST 6: Cache delete works
async def test_cache_delete(cache_service):
    """Delete should remove the key"""
    await cache_service.set("delete_me", "value", ttl=60)
    await cache_service.delete("delete_me")
    result = await cache_service.get("delete_me")
    assert result is None

# TEST 7: Second discovery call uses cache (no AI call)
async def test_second_discovery_uses_cache(client, auth_headers, mock_gemini):
    """Second identical discovery should not call AI again"""
    import json
    # Create two sessions with same industry/location/maturity
    s1 = await client.post("/api/v1/sessions", json={
        "industry": "Healthcare", "location": "India", "maturity_level": "mvp"
    }, headers=auth_headers)
    s2 = await client.post("/api/v1/sessions", json={
        "industry": "Healthcare", "location": "India", "maturity_level": "mvp"
    }, headers=auth_headers)
    
    mock_gemini.return_value = json.dumps({"pain_points": [
        {"name": "Test", "description": "Test", "severity": 5, "affected_stakeholders": ["Users"], "evidence": "Data"}
    ]})
    
    await client.post(f"/api/v1/sessions/{s1.json()['id']}/discover", headers=auth_headers)
    call_count_after_first = mock_gemini.call_count
    
    await client.post(f"/api/v1/sessions/{s2.json()['id']}/discover", headers=auth_headers)
    assert mock_gemini.call_count == call_count_after_first  # No additional AI call
```

Run: `cd backend && python -m pytest tests/test_s2_07_cache.py -v`
All 7 tests must pass.

Note: Add a `cache_service` fixture in conftest.py. If Redis isn't available in test env, mock it with a dict-based in-memory implementation.
```

---

## ⚡ PROMPT S2-08: Frontend — Maturity Level & Tech Stack Selection UI

```
Build the frontend components for maturity level selection and tech stack preferences on the IdeaForge Discovery page.

React 18 + TypeScript + Tailwind CSS + Framer Motion + Lucide React + Vitest. Integrate with the Discovery page from S2-05.

## Components to Enhance/Create

### frontend/src/components/discovery/MaturitySelector.tsx (enhance from S2-05)
Redesign as a premium card selector instead of simple segmented buttons:

- 4 cards in a horizontal row (2x2 grid on mobile)
- Each card shows:
  - Level icon (Lucide): POC = Zap, MVP = Rocket, Pre-Prod = Shield, Production = Building2
  - Level label (bold)
  - One-line description
  - Key stats: "3 solutions, light eval" / "5 solutions, full eval + security"
  - Selected state: blue-600 border, blue-600/10 bg, subtle glow (box-shadow: 0 0 20px rgba(37,99,235,0.15))
  - Unselected: border-white/5, bg-slate-800/30
- Framer-motion: scale(1.02) on selected, transition spring

### frontend/src/components/discovery/TechStackInput.tsx (enhance from S2-05)
Full-featured tech stack selector:

- Text input with search icon
- Debounced API call to /api/v1/tech-stacks/search?q= (300ms)
- Dropdown shows results grouped by category (category headers in slate-500, items below)
- Click item → adds to selected tags, clears input
- Selected tags bar below input: each tag is a pill with X button
  - Tag color by category: frontend = blue, backend = green, database = amber, infrastructure = purple, ai_ml = rose
- Keyboard: arrow keys navigate dropdown, enter selects, escape closes
- Max 10 selections (show warning at limit)
- Empty state in dropdown: "No technologies found matching '{query}'"

### frontend/src/stores/discoveryStore.ts (update)
Add fields:
- selectedMaturity: MaturityLevel (default "mvp")
- selectedTechStack: string[] (default [])
- maturityLevels: MaturityLevelInfo[] (fetched from API on mount)

### Fetch maturity levels on mount
- Call GET /api/v1/maturity-levels on Discovery page mount
- Store in discoveryStore

## Test Cases — Create frontend/src/__tests__/s2_08_selections.test.tsx

```tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';

// TEST 1: MaturitySelector renders all 4 level cards
it('should render 4 maturity level cards', async () => {
  const { default: MaturitySelector } = await import('../components/discovery/MaturitySelector');
  render(<MaturitySelector value="mvp" onChange={() => {}} levels={[
    { level: 'poc', label: 'POC', description: 'Quick validation' },
    { level: 'mvp', label: 'MVP', description: 'Balanced depth' },
    { level: 'pre_production', label: 'Pre-Production', description: 'Full rigor' },
    { level: 'production', label: 'Production', description: 'Enterprise-ready' },
  ]} />);
  expect(screen.getByText('POC')).toBeDefined();
  expect(screen.getByText('MVP')).toBeDefined();
  expect(screen.getByText('Pre-Production')).toBeDefined();
  expect(screen.getByText('Production')).toBeDefined();
});

// TEST 2: Clicking a maturity card calls onChange
it('should call onChange when a level is selected', async () => {
  const onChange = vi.fn();
  const { default: MaturitySelector } = await import('../components/discovery/MaturitySelector');
  render(<MaturitySelector value="mvp" onChange={onChange} levels={[
    { level: 'poc', label: 'POC', description: 'Quick' },
    { level: 'mvp', label: 'MVP', description: 'Balanced' },
    { level: 'pre_production', label: 'Pre-Prod', description: 'Full' },
    { level: 'production', label: 'Production', description: 'Enterprise' },
  ]} />);
  fireEvent.click(screen.getByText('POC'));
  expect(onChange).toHaveBeenCalledWith('poc');
});

// TEST 3: TechStackInput renders input field
it('should render tech stack search input', async () => {
  const { default: TechStackInput } = await import('../components/discovery/TechStackInput');
  render(<TechStackInput selected={[]} onChange={() => {}} />);
  expect(screen.getByPlaceholderText(/search|tech|stack/i)).toBeDefined();
});

// TEST 4: TechStackInput shows selected tags
it('should display selected technologies as tags', async () => {
  const { default: TechStackInput } = await import('../components/discovery/TechStackInput');
  render(<TechStackInput selected={["React", "FastAPI", "PostgreSQL"]} onChange={() => {}} />);
  expect(screen.getByText('React')).toBeDefined();
  expect(screen.getByText('FastAPI')).toBeDefined();
  expect(screen.getByText('PostgreSQL')).toBeDefined();
});

// TEST 5: TechStackInput allows removing tags
it('should remove tag when X is clicked', async () => {
  const onChange = vi.fn();
  const { default: TechStackInput } = await import('../components/discovery/TechStackInput');
  render(<TechStackInput selected={["React", "FastAPI"]} onChange={onChange} />);
  const removeButtons = screen.getAllByRole('button').filter(b => b.getAttribute('aria-label')?.includes('remove') || b.textContent === '×' || b.textContent === '✕');
  if (removeButtons.length > 0) {
    fireEvent.click(removeButtons[0]);
    expect(onChange).toHaveBeenCalled();
  }
});

// TEST 6: Discovery store has maturity and tech stack state
it('should have maturity and tech stack in discovery store', async () => {
  const { useDiscoveryStore } = await import('../stores/discoveryStore');
  const state = useDiscoveryStore.getState();
  expect(state.selectedMaturity).toBe('mvp');
  expect(Array.isArray(state.selectedTechStack)).toBe(true);
});
```

Run: `cd frontend && npx vitest run src/__tests__/s2_08_selections.test.tsx --reporter=verbose`
All 6 tests must pass.
```

---

## 📋 Sprint 2 Execution Order

1. **S2-01** → Maturity levels & session enhancement → 7 backend tests
2. **S2-02** → Tech stack registry & API → 7 backend tests
3. **S2-03** → Session CRUD API → 11 backend tests
4. **S2-04** → AI pain point discovery service → 9 backend tests
5. **S2-05** → Discovery page UI → 8 frontend tests
6. **S2-06** → SSE streaming → 4 backend + 2 frontend tests
7. **S2-07** → Redis caching → 7 backend tests
8. **S2-08** → Maturity & tech stack selection UI → 6 frontend tests

## ✅ Sprint 2 Total: 61 Test Cases
- Backend: 45 tests
- Frontend: 16 tests

Combined with Sprint 1 (65 tests): **126 total tests must pass**.

Run full suite:
- Backend: `cd backend && python -m pytest tests/ -v`
- Frontend: `cd frontend && npx vitest run --reporter=verbose`

ALL 126 TESTS MUST PASS before moving to Sprint 3.
