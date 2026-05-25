# IdeaForge — Sprint 1 Prompts for Antigravity
## Foundation Sprint (7 Tasks)

---

## ⚡ PROMPT S1-01: Backend Project Scaffolding

```
Create a production-grade FastAPI backend project called "IdeaForge" — an AI-powered startup idea discovery and validation platform.

## Project Structure

ideaforge/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app entry point
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py              # Pydantic Settings configuration
│   │   │   └── database.py            # Async SQLAlchemy setup
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── router.py          # Aggregated API router
│   │   │       └── health.py          # Health check endpoint
│   │   ├── models/
│   │   │   └── __init__.py            # SQLAlchemy Base
│   │   ├── schemas/
│   │   │   └── __init__.py            # Base Pydantic schemas
│   │   ├── services/
│   │   │   └── __init__.py
│   │   └── ai/
│   │       ├── __init__.py
│   │       ├── provider.py            # AI provider base class + Gemini implementation
│   │       └── prompts/
│   │           └── __init__.py
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   ├── alembic.ini
│   ├── requirements.txt
│   └── .env.example

## Technical Requirements

1. **main.py**: FastAPI app with:
   - CORS middleware (origins from config)
   - API v1 router mounted at /api/v1
   - Health endpoint at GET /api/v1/health returning {"status": "healthy", "version": "1.0.0"}
   - Lifespan handler for startup/shutdown events

2. **core/config.py**: Using pydantic-settings:
   - DATABASE_URL (default: postgresql+asyncpg://postgres:postgres@localhost:5432/ideaforge)
   - REDIS_URL (default: redis://localhost:6379)
   - GEMINI_API_KEY (required)
   - JWT_SECRET (required)
   - JWT_ALGORITHM (default: HS256)
   - ACCESS_TOKEN_EXPIRE_MINUTES (default: 30)
   - REFRESH_TOKEN_EXPIRE_DAYS (default: 7)
   - CORS_ORIGINS (default: ["http://localhost:5173"])
   - APP_ENV (default: development)

3. **core/database.py**: Async SQLAlchemy setup:
   - create_async_engine with pool_size=5, max_overflow=10
   - async_sessionmaker
   - get_db async generator dependency
   - Base declarative base

4. **ai/provider.py**: AI provider abstraction:
   - Abstract base class AIProvider with method: async generate(prompt: str, system_prompt: str, response_schema: dict | None = None, temperature: float = 0.7, max_tokens: int = 4096) -> str
   - GeminiProvider implementation using google-generativeai SDK
   - Model: gemini-2.5-flash
   - Support structured JSON output via response_mime_type="application/json"
   - Retry logic: 1 retry on failure with exponential backoff
   - get_ai_provider() factory function reading from config

5. **requirements.txt**:
   fastapi>=0.110.0
   uvicorn[standard]>=0.27.0
   sqlalchemy[asyncio]>=2.0.25
   asyncpg>=0.29.0
   pydantic-settings>=2.1.0
   python-jose[cryptography]>=3.3.0
   passlib[bcrypt]>=1.7.4
   redis>=5.0.0
   google-generativeai>=0.8.0
   celery>=5.3.0
   alembic>=1.13.0
   httpx>=0.26.0

6. **Alembic**: Configure alembic.ini and env.py for async PostgreSQL. The env.py must import all models from app.models and use async engine.

7. **.env.example**: All config vars with placeholder values.

## Acceptance Criteria
- `pip install -r requirements.txt` succeeds
- `uvicorn backend.app.main:app --reload` starts without errors
- GET http://localhost:8000/api/v1/health returns {"status": "healthy", "version": "1.0.0"}
- CORS headers present in response
- GeminiProvider can be instantiated with API key from env
- No hardcoded secrets anywhere
```

---

## ⚡ PROMPT S1-02: Database Models & Migrations

```
In the existing IdeaForge FastAPI project (backend/app/), create the core database models and run the initial Alembic migration.

## Models to Create

### backend/app/models/user.py — User Model
- id: UUID, primary key, server_default=uuid4
- email: String(255), unique, not null, indexed
- hashed_password: String(255), not null
- full_name: String(255), not null
- is_active: Boolean, default=True
- created_at: DateTime, server_default=now(), not null
- updated_at: DateTime, server_default=now(), onupdate=now(), not null
- Relationship: sessions (one-to-many with Session)

### backend/app/models/session.py — Discovery Session Model
- id: UUID, primary key, server_default=uuid4
- user_id: UUID, ForeignKey("users.id"), not null, indexed
- industry: String(255), not null
- location: String(255), not null
- pain_points: JSON, nullable (stores AI-discovered pain points as JSON array)
- status: String(50), default="discovery" (enum values: discovery, problem_generation, solution_generation, evaluation, completed)
- created_at: DateTime, server_default=now(), not null
- updated_at: DateTime, server_default=now(), onupdate=now(), not null
- Relationship: user (many-to-one), problem_statements (one-to-many)

### backend/app/models/problem_statement.py — Problem Statement Model
- id: UUID, primary key, server_default=uuid4
- session_id: UUID, ForeignKey("sessions.id"), not null, indexed
- title: String(500), not null
- description: Text, not null
- target_user: String(500), nullable
- core_pain: Text, nullable
- market_context: Text, nullable
- severity: Float, default=0 (1-5 scale)
- feasibility: Float, default=0 (1-5 scale)
- market_size: Float, default=0 (1-5 scale)
- uniqueness: Float, default=0 (1-5 scale)
- overall_rating: Float, default=0 (weighted average)
- status: String(50), default="draft" (draft, selected, archived)
- created_at: DateTime, server_default=now(), not null
- updated_at: DateTime, server_default=now(), onupdate=now(), not null
- Relationships: session (many-to-one), solutions (one-to-many)

### backend/app/models/solution.py — Solution Model
- id: UUID, primary key, server_default=uuid4
- problem_id: UUID, ForeignKey("problem_statements.id"), not null, indexed
- title: String(500), not null
- description: Text, not null
- mechanism: Text, nullable (how it works technically)
- tech_stack: JSON, nullable (array of technologies)
- target_user: String(500), nullable
- revenue_model: String(500), nullable
- is_unconventional: Boolean, default=False
- status: String(50), default="candidate" (candidate, disqualified, evaluated, approved)
- created_at: DateTime, server_default=now(), not null
- updated_at: DateTime, server_default=now(), onupdate=now(), not null
- Relationships: problem_statement (many-to-one), evaluation (one-to-one)

### backend/app/models/evaluation.py — Evaluation Model
- id: UUID, primary key, server_default=uuid4
- solution_id: UUID, ForeignKey("solutions.id"), unique, not null
- rubric: JSON, not null (stores full rubric: criteria, weights, disqualifiers)
- scores: JSON, nullable (stores scoring matrix with justifications)
- weighted_avg: Float, nullable
- min_score: Float, nullable
- attack_summary: Text, nullable
- attack_survives: Boolean, nullable
- inconsistencies: JSON, nullable (array of inconsistency strings)
- inconsistency_count: Integer, default=0
- status: String(50), default="pending" (pending, in_progress, completed)
- created_at: DateTime, server_default=now(), not null
- Relationship: solution (one-to-one)

### backend/app/models/__init__.py
Import all models and export Base. This file must be importable by Alembic env.py.

## Migration
- Update alembic/env.py to import all models from backend.app.models
- Generate initial migration: `alembic revision --autogenerate -m "initial_models"`
- Verify the migration creates all 5 tables with correct columns, constraints, and indexes

## Acceptance Criteria
- `alembic upgrade head` creates all tables in PostgreSQL
- All foreign key relationships work correctly
- All models are importable: `from backend.app.models import User, Session, ProblemStatement, Solution, Evaluation`
- UUID primary keys generate automatically
- created_at and updated_at populate automatically
```

---

## ⚡ PROMPT S1-03: Authentication System

```
Implement JWT-based authentication for the IdeaForge FastAPI backend. The project already has User model, database setup, and config with JWT_SECRET, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS.

## Files to Create/Modify

### backend/app/core/security.py
- create_access_token(data: dict) -> str — JWT with exp claim, uses JWT_SECRET and JWT_ALGORITHM from config
- create_refresh_token(data: dict) -> str — JWT with longer expiry
- verify_token(token: str) -> dict — Decode and validate JWT, raise HTTPException 401 on invalid/expired
- hash_password(password: str) -> str — bcrypt hashing
- verify_password(plain: str, hashed: str) -> bool — bcrypt verification

### backend/app/schemas/auth.py — Pydantic Schemas
- UserCreate: email (EmailStr), password (str, min 8 chars), full_name (str)
- UserLogin: email (EmailStr), password (str)
- TokenResponse: access_token (str), refresh_token (str), token_type (str = "bearer")
- TokenRefresh: refresh_token (str)
- UserResponse: id (UUID), email (str), full_name (str), is_active (bool), created_at (datetime) — exclude password

### backend/app/api/deps.py — Dependencies
- get_current_user(token: str = Depends(oauth2_scheme)) -> User
  - Extract token from Authorization: Bearer header
  - Decode JWT, extract user_id from "sub" claim
  - Query User from database
  - Raise 401 if user not found or inactive
  - Return User object

### backend/app/services/auth_service.py — Business Logic
- async register_user(db, user_data: UserCreate) -> User
  - Check if email already exists (raise 409 Conflict if so)
  - Hash password
  - Create and return User
- async authenticate_user(db, email: str, password: str) -> User
  - Find user by email
  - Verify password
  - Raise 401 on failure
  - Return User

### backend/app/api/v1/auth.py — Auth Routes
- POST /api/v1/auth/register — Create new user, return UserResponse
- POST /api/v1/auth/login — Authenticate, return TokenResponse (access + refresh tokens)
- POST /api/v1/auth/refresh — Accept refresh token, return new TokenResponse
- GET /api/v1/auth/me — Protected endpoint, return current UserResponse

### Update backend/app/api/v1/router.py
- Include auth router

## Token Details
- Access token payload: {"sub": str(user.id), "type": "access"}
- Refresh token payload: {"sub": str(user.id), "type": "refresh"}
- Access token expiry: 30 minutes (from config)
- Refresh token expiry: 7 days (from config)
- Refresh endpoint must validate token type is "refresh"

## Error Responses (consistent JSON format)
- 401: {"detail": "Invalid credentials"} / {"detail": "Token expired"} / {"detail": "Invalid token"}
- 409: {"detail": "Email already registered"}
- 422: Pydantic validation errors (automatic)

## Acceptance Criteria
- POST /register with valid data creates user and returns UserResponse (no password in response)
- POST /register with duplicate email returns 409
- POST /login with correct credentials returns access + refresh tokens
- POST /login with wrong password returns 401
- GET /me with valid access token returns user data
- GET /me without token returns 401
- POST /refresh with valid refresh token returns new token pair
- POST /refresh with access token (wrong type) returns 401
```

---

## ⚡ PROMPT S1-04: Frontend Scaffolding

```
Create the React frontend project for IdeaForge — an AI-powered startup idea discovery and validation platform.

## Setup

Initialize in a `frontend/` directory at the project root (sibling to `backend/`).

### Stack
- React 18 + TypeScript + Vite
- Tailwind CSS 3 with @tailwindcss/forms plugin
- React Router DOM v6 for routing
- Zustand for state management
- Axios for HTTP requests
- Lucide React for icons
- Framer Motion for animations

## Project Structure

frontend/
├── src/
│   ├── App.tsx                      # Router setup + layout wrappers
│   ├── main.tsx                     # Entry point
│   ├── index.css                    # Tailwind imports + custom CSS vars + fonts
│   ├── pages/
│   │   ├── Dashboard.tsx            # Landing/home page (placeholder)
│   │   ├── Login.tsx                # Login page (placeholder)
│   │   ├── Register.tsx             # Registration page (placeholder)
│   │   ├── Discovery.tsx            # Industry/location input + pain points (placeholder)
│   │   ├── ProblemLibrary.tsx       # All problem statements library (placeholder)
│   │   ├── SolutionWorkspace.tsx    # Solutions + evaluation (placeholder)
│   │   └── Approvals.tsx            # Approved solutions queue (placeholder)
│   ├── components/
│   │   └── layout/
│   │       └── ProtectedRoute.tsx   # Auth guard component
│   ├── stores/
│   │   └── authStore.ts             # Zustand auth state
│   ├── services/
│   │   └── api.ts                   # Axios instance with interceptors
│   ├── types/
│   │   └── api.ts                   # TypeScript interfaces
│   └── lib/
│       └── utils.ts                 # Utility functions (cn classname merger, etc.)
├── tailwind.config.js
├── postcss.config.js
├── tsconfig.json
├── vite.config.ts
├── .env.example                     # VITE_API_URL=http://localhost:8000
└── package.json

## Design Direction

This is a luxury, professional tool for product managers and founders. NOT a toy.

- **Theme**: Dark mode default. Deep slate/charcoal backgrounds (slate-950, slate-900). NOT pure black.
- **Accent**: Electric blue primary (#2563EB / blue-600). Emerald for success states. Amber for warnings. Rose for errors.
- **Typography**: Import "Plus Jakarta Sans" from Google Fonts as the primary font. Clean, modern, geometric. Set as default in tailwind config.
- **Cards**: Subtle glass effect — bg-slate-800/50 with backdrop-blur-sm, border border-white/5. NOT heavy glassmorphism.
- **Spacing**: Generous. Let the UI breathe. Minimum p-6 on major cards, gap-6 between sections.
- **Transitions**: Smooth, 200ms default. Use framer-motion for page transitions (fade + slight upward movement).

### CSS Variables (in index.css)
Define these custom properties for consistent theming:
```css
:root {
  --color-bg-primary: #0f172a;      /* slate-900 */
  --color-bg-secondary: #1e293b;    /* slate-800 */
  --color-bg-card: rgba(30, 41, 59, 0.5);
  --color-border: rgba(255, 255, 255, 0.05);
  --color-accent: #2563eb;
  --color-text-primary: #f8fafc;
  --color-text-secondary: #94a3b8;
  --color-text-muted: #64748b;
}
```

## Key Files Detail

### stores/authStore.ts (Zustand)
```typescript
interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => void;
  refreshAccessToken: () => Promise<void>;
  fetchCurrentUser: () => Promise<void>;
}
```
- Persist tokens in localStorage
- login() calls POST /api/v1/auth/login, stores tokens, fetches user
- logout() clears everything and redirects to /login

### services/api.ts (Axios)
- Base URL from VITE_API_URL env var
- Request interceptor: attach Authorization: Bearer token from authStore
- Response interceptor: on 401, attempt token refresh. If refresh fails, logout.
- Export typed API functions: apiClient.get<T>(), apiClient.post<T>(), etc.

### types/api.ts
```typescript
interface User { id: string; email: string; fullName: string; isActive: boolean; createdAt: string; }
interface TokenResponse { access_token: string; refresh_token: string; token_type: string; }
interface ApiResponse<T> { data: T; message?: string; }
interface PaginatedResponse<T> { items: T[]; total: number; page: number; pages: number; }
```

### ProtectedRoute.tsx
- If not authenticated and not loading, redirect to /login with ?redirect= current path
- If loading, show centered spinner
- If authenticated, render children/Outlet

### App.tsx Routes
- /login → Login (public)
- /register → Register (public)
- / → Dashboard (protected)
- /discovery → Discovery (protected)
- /library → ProblemLibrary (protected)
- /workspace/:problemId → SolutionWorkspace (protected)
- /approvals → Approvals (protected)

### Placeholder Pages
Each placeholder should render:
- The page name as a heading
- "Coming in Sprint X" subtitle
- Consistent layout within the app shell area (even though AppShell is Sprint S1-05, just use a basic centered container for now — the shell will wrap these later)

## Acceptance Criteria
- `npm install && npm run dev` starts on localhost:5173
- All routes are accessible and render placeholder content
- Tailwind classes render correctly (dark theme visible)
- Plus Jakarta Sans font loads from Google Fonts
- Auth store is functional (actions callable, state updates)
- API service correctly configures Axios with interceptors
- TypeScript strict mode enabled, no type errors
- ProtectedRoute redirects unauthenticated users to /login
```

---

## ⚡ PROMPT S1-05: UI Shell & App Layout

```
Build the main application shell layout for IdeaForge. This wraps all authenticated pages with a sidebar, top bar, and content area.

The project uses React 18 + TypeScript + Tailwind CSS + Framer Motion + Lucide React. The design is dark-mode luxury professional (slate-950/slate-900 backgrounds, blue-600 accent, Plus Jakarta Sans font).

## Components to Create

### frontend/src/components/layout/AppShell.tsx
The main layout wrapper. All protected pages render inside this.

**Structure:**
- Fixed sidebar on the left (width: 260px expanded, 72px collapsed)
- Top bar across the top of the content area
- Scrollable content area filling the remaining space
- Sidebar collapse state stored in localStorage

**Sidebar:**
- Top: IdeaForge logo/brand (use a stylized text logo — "idea" in regular weight, "forge" in bold blue-600)
- Navigation items with icons (Lucide):
  - Dashboard (LayoutDashboard icon) → /
  - Discovery (Search icon) → /discovery
  - Problem Library (Library icon) → /library
  - Approvals (CheckCircle icon) → /approvals
- Each nav item: icon + label (label hidden when collapsed), hover state with bg-white/5, active state with blue-600/10 bg + blue-500 left border accent (3px)
- Bottom: collapse toggle button (ChevronLeft/ChevronRight icon)
- Subtle top-to-bottom gradient on sidebar background: from slate-950 to slate-900/95

**Top Bar:**
- Left: Breadcrumbs (auto-generated from current route path)
- Right: User avatar circle (initials from user's full_name, blue-600 bg), dropdown on click with:
  - User name and email (non-clickable header)
  - Divider
  - "Log out" button (calls authStore.logout())
- Height: 64px
- Bottom border: border-white/5
- Background: bg-slate-950/80 with backdrop-blur-md (sticky top)

**Content Area:**
- Padding: p-8
- Max width: max-w-7xl with mx-auto
- Scrollable independently from sidebar

### frontend/src/components/layout/Sidebar.tsx
Extract sidebar into its own component for cleanliness. Receives isCollapsed and onToggle props.

### frontend/src/components/layout/TopBar.tsx
Extract top bar. Receives user prop from authStore.

### frontend/src/components/layout/Breadcrumbs.tsx
Auto-generates breadcrumbs from useLocation():
- "/" → Dashboard
- "/discovery" → Dashboard > Discovery
- "/library" → Dashboard > Problem Library
- "/workspace/:id" → Dashboard > Problem Library > Solution Workspace
- "/approvals" → Dashboard > Approvals
Each segment is a clickable link except the last (current page, text-white).

## Responsive Behavior
- **Desktop (>1024px)**: Sidebar visible, collapsible
- **Tablet (768-1024px)**: Sidebar collapsed by default (icons only)
- **Mobile (<768px)**: Sidebar hidden, hamburger menu button in top bar, sidebar slides in as overlay with backdrop blur when opened

## Animations (Framer Motion)
- Sidebar collapse/expand: animate width transition (200ms, ease-out)
- Nav item labels: fade in/out on collapse toggle
- Page content: AnimatePresence wrapper, pages fade in with slight y-translate (y: 10 → 0, opacity: 0 → 1, duration: 300ms)
- User dropdown: scale from 0.95 + fade, origin top-right

## Update App.tsx
- Wrap all protected routes inside AppShell component
- Login and Register pages render WITHOUT AppShell (full-page layout)
- Fetch current user on app mount if tokens exist in localStorage

## Acceptance Criteria
- Shell renders with sidebar, top bar, and content area
- Sidebar navigation works — clicking items navigates between pages
- Active page is highlighted in sidebar
- Sidebar collapses to icon-only mode, persists preference in localStorage
- Breadcrumbs update automatically on navigation
- User dropdown shows name/email and logout works
- Mobile: hamburger menu opens sidebar overlay
- Page transitions are smooth (framer-motion fade)
- No layout shift or jank during sidebar collapse
- Entire shell feels premium — not generic Bootstrap/template vibes
```

---

## ⚡ PROMPT S1-06: Auth UI Pages (Login & Register)

```
Create polished, production-grade login and registration pages for IdeaForge.

The project uses React 18 + TypeScript + Tailwind CSS + Framer Motion + Lucide React. Design: dark luxury professional (slate-950 bg, blue-600 accent, Plus Jakarta Sans font). Auth store (Zustand) and API service already exist.

## Pages to Build

### frontend/src/pages/Login.tsx

**Layout:**
- Full viewport height, centered content
- Split layout on desktop: left 55% decorative panel, right 45% form
- Mobile: form only, full width

**Left Panel (desktop only):**
- Deep gradient background (slate-950 to blue-950/30)
- Large IdeaForge branding: "idea" light weight, "forge" bold blue-500
- Tagline below: "Transform industry pain points into validated solutions"
- Subtle decorative elements: abstract geometric grid pattern (CSS only, using repeating-linear-gradient), very low opacity (5-8%)
- Animated floating dots or particles (CSS keyframes, 4-5 subtle circles moving slowly)

**Right Panel (form):**
- Vertically centered in the panel
- Card: bg-slate-900/80 border border-white/5 rounded-2xl p-8 backdrop-blur
- Heading: "Welcome back" (text-2xl, font-bold, text-white)
- Subtitle: "Sign in to continue to IdeaForge" (text-slate-400, text-sm)
- Form fields (gap-5 between fields):
  - Email: label "Email address", input with Mail icon prefix, type="email"
  - Password: label "Password", input with Lock icon prefix, type="password", eye toggle to show/hide
- Input styling: bg-slate-800/50, border border-white/10, rounded-xl, h-12, px-4, focus:ring-2 ring-blue-500/40, focus:border-blue-500, text-white, placeholder-slate-500
- Button: "Sign in" — full width, h-12, bg-blue-600 hover:bg-blue-700, rounded-xl, font-semibold, transition-all, active:scale-[0.98]
- Loading state: button shows spinner + "Signing in..." when submitting, disabled
- Error state: red-400 text error message below form, animate in with framer-motion (fade + slide down)
- Footer: "Don't have an account?" + Link to /register (text-blue-400 hover:text-blue-300)

**Functionality:**
- Uses authStore.login(email, password)
- On success: redirect to / (or to ?redirect= URL if present)
- On error: display error message from API response
- Form validation: email required + valid format, password required + min 8 chars
- Validate on blur (not just submit) — show inline validation errors per field
- Enter key submits form

### frontend/src/pages/Register.tsx

**Same split layout as Login** but with:
- Heading: "Create your account"
- Subtitle: "Start discovering validated startup ideas"
- Fields:
  - Full name: Person icon prefix
  - Email: Mail icon prefix
  - Password: Lock icon prefix, strength indicator below (weak/medium/strong with colored bar — red/amber/green)
  - Confirm password: Lock icon prefix, must match password
- Button: "Create account"
- Footer: "Already have an account?" + Link to /login
- On success: auto-login and redirect to /

**Password Strength Indicator:**
- Bar below password field, 3 segments
- Weak (< 8 chars or no variety): 1 segment red
- Medium (8+ chars, 2 of: upper, lower, number, special): 2 segments amber
- Strong (8+ chars, 3+ of: upper, lower, number, special): 3 segments green
- Label text next to bar: "Weak" / "Medium" / "Strong"
- Animate segment fills with transition-all duration-300

## Shared Components to Extract

### frontend/src/components/ui/Input.tsx
Reusable input component with:
- Props: label, icon (Lucide component), type, error, ...inputProps
- Icon rendered inside input (left side, text-slate-500)
- Error message rendered below in text-red-400 text-sm
- Focus ring animation

### frontend/src/components/ui/Button.tsx
Reusable button with:
- Props: children, isLoading, variant (primary/secondary/ghost), size (sm/md/lg), ...buttonProps
- Loading: shows spinning Loader2 icon + loading text
- Variants: primary (blue-600), secondary (slate-700), ghost (transparent hover:bg-white/5)
- Disabled state: opacity-50 cursor-not-allowed

## Acceptance Criteria
- Login page renders with split layout on desktop, form-only on mobile
- Registration page matches login aesthetic
- Form validation works on blur and submit
- Error messages from API display correctly (e.g., "Email already registered")
- Successful login redirects to dashboard
- Successful registration auto-logs-in and redirects
- Password show/hide toggle works
- Password strength indicator updates in real-time
- Loading states on buttons during API calls
- Tab navigation works correctly through form fields
- Pages feel polished and premium — not a Bootstrap template
```

---

## ⚡ PROMPT S1-07: API Client Layer

```
Build the complete frontend API client layer for IdeaForge. The project has React 18 + TypeScript, Zustand authStore with tokens, and Axios already installed.

## Files to Create/Update

### frontend/src/types/api.ts — Complete TypeScript Interfaces

// ─── Base Types ───
interface ApiResponse<T> {
  data: T;
  message?: string;
}

interface ApiError {
  detail: string;
  status: number;
}

interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pages: number;
  per_page: number;
}

// ─── User ───
interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
}

// ─── Auth ───
interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

interface LoginRequest {
  email: string;
  password: string;
}

interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
}

// ─── Session ───
interface Session {
  id: string;
  user_id: string;
  industry: string;
  location: string;
  pain_points: PainPoint[] | null;
  status: 'discovery' | 'problem_generation' | 'solution_generation' | 'evaluation' | 'completed';
  created_at: string;
  updated_at: string;
}

interface CreateSessionRequest {
  industry: string;
  location: string;
}

// ─── Pain Points ───
interface PainPoint {
  name: string;
  description: string;
  severity: number;
  affected_stakeholders: string[];
  evidence: string;
}

// ─── Problem Statements ───
interface ProblemStatement {
  id: string;
  session_id: string;
  title: string;
  description: string;
  target_user: string | null;
  core_pain: string | null;
  market_context: string | null;
  severity: number;
  feasibility: number;
  market_size: number;
  uniqueness: number;
  overall_rating: number;
  status: 'draft' | 'selected' | 'archived';
  created_at: string;
  updated_at: string;
}

// ─── Solutions ───
interface Solution {
  id: string;
  problem_id: string;
  title: string;
  description: string;
  mechanism: string | null;
  tech_stack: string[] | null;
  target_user: string | null;
  revenue_model: string | null;
  is_unconventional: boolean;
  status: 'candidate' | 'disqualified' | 'evaluated' | 'approved';
  created_at: string;
  evaluation?: Evaluation | null;
}

// ─── Evaluation ───
interface RubricCriterion {
  name: string;
  description: string;
  weight: number;
  scale: { "1": string; "3": string; "5": string; };
}

interface Disqualifier {
  name: string;
  description: string;
}

interface Rubric {
  criteria: RubricCriterion[];
  disqualifiers: Disqualifier[];
}

interface CriterionScore {
  criterion_name: string;
  score: number;
  justification: string;
  weight: number;
}

interface Evaluation {
  id: string;
  solution_id: string;
  rubric: Rubric;
  scores: CriterionScore[] | null;
  weighted_avg: number | null;
  min_score: number | null;
  attack_summary: string | null;
  attack_survives: boolean | null;
  inconsistencies: string[] | null;
  inconsistency_count: number;
  status: 'pending' | 'in_progress' | 'completed';
  created_at: string;
}

Export all types.

### frontend/src/services/api.ts — Enhanced Axios Setup

Create a robust Axios instance:
1. baseURL from import.meta.env.VITE_API_URL (default http://localhost:8000)
2. Request interceptor:
   - If accessToken exists in authStore, add Authorization: Bearer {token}
   - Add Content-Type: application/json
3. Response interceptor:
   - On 401: check if it's a refresh token request (avoid infinite loop). If not, attempt token refresh via POST /api/v1/auth/refresh. If refresh succeeds, retry the original request with new token. If refresh fails, call authStore.logout().
   - On other errors: extract error message from response.data.detail or use generic message
4. Export the instance as `apiClient`

### frontend/src/services/authService.ts
- login(data: LoginRequest): Promise<TokenResponse>
- register(data: RegisterRequest): Promise<User>
- refreshToken(token: string): Promise<TokenResponse>
- getCurrentUser(): Promise<User>

### frontend/src/services/sessionService.ts
- createSession(data: CreateSessionRequest): Promise<Session>
- getSession(id: string): Promise<Session>
- getUserSessions(): Promise<Session[]>
- discoverPainPoints(sessionId: string): Promise<PainPoint[]>

### frontend/src/services/problemService.ts
- generateProblems(sessionId: string): Promise<ProblemStatement[]>
- getProblems(filters?: { industry?: string; status?: string; page?: number }): Promise<PaginatedResponse<ProblemStatement>>
- getProblem(id: string): Promise<ProblemStatement>
- updateProblem(id: string, data: Partial<ProblemStatement>): Promise<ProblemStatement>

### frontend/src/services/solutionService.ts
- generateSolutions(problemId: string): Promise<Solution[]>
- getSolutions(problemId: string): Promise<Solution[]>
- getSolution(id: string): Promise<Solution>
- approveSolution(id: string): Promise<Solution>

### frontend/src/services/evaluationService.ts
- runEvaluation(solutionIds: string[]): Promise<Evaluation[]>
- getEvaluation(id: string): Promise<Evaluation>
- updateRubric(evaluationId: string, rubric: Rubric): Promise<Evaluation>

## Toast Notification Setup

### frontend/src/components/ui/Toast.tsx
Simple toast notification component:
- Position: fixed bottom-right
- Types: success (green), error (red), info (blue)
- Auto-dismiss after 4 seconds
- Animate in from right (framer-motion)

### frontend/src/stores/toastStore.ts
Zustand store:
- toasts: Toast[]
- addToast(type, message): void — add toast with auto-generated ID
- removeToast(id): void

Wire the API error interceptor to automatically show error toasts on API failures.

## Acceptance Criteria
- All TypeScript types compile without errors
- API client attaches JWT to requests
- 401 responses trigger token refresh automatically
- Failed refresh triggers logout
- All service functions are properly typed with request and response types
- Toast notifications show on API errors
- No `any` types anywhere
- Services are thin wrappers — no business logic, just API calls
```

---

## 📋 Sprint 1 Execution Order

Run these prompts in order. Each builds on the previous:

1. **S1-01** → Backend scaffolding (run first — creates project structure)
2. **S1-02** → Database models (needs S1-01 project structure)
3. **S1-03** → Auth system (needs S1-02 User model)
4. **S1-04** → Frontend scaffolding (independent of backend, can run parallel)
5. **S1-05** → UI shell (needs S1-04 frontend project)
6. **S1-06** → Auth UI (needs S1-05 shell + S1-04 stores)
7. **S1-07** → API client layer (needs S1-06 UI + connects to S1-03 backend auth)

## ✅ Sprint 1 Done Criteria

After all 7 tasks:
- Backend runs on localhost:8000 with health check and auth endpoints
- Frontend runs on localhost:5173 with dark professional UI
- User can register, login, and see dashboard
- Sidebar navigation works between all placeholder pages
- JWT auth flow works end-to-end (login, token refresh, logout)
- All database models created and migrated
- Gemini AI provider configured and ready for Sprint 2
