// ─── Base Types ───
export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface ApiError {
  detail: string;
  status: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pages: number;
  per_page: number;
}

// ─── User ───
export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
}

// ─── Auth ───
export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
}

// ─── Session ───
export interface Session {
  id: string;
  user_id: string;
  industry: string;
  location: string;
  pain_points: PainPoint[] | null;
  maturity_level: 'poc' | 'mvp' | 'pre_production' | 'production';
  tech_stack_preferences: string[] | null;
  status: 'discovery' | 'problem_generation' | 'solution_generation' | 'evaluation' | 'completed';
  created_at: string;
  updated_at: string;
}

export interface CreateSessionRequest {
  industry: string;
  location: string;
  maturity_level?: 'poc' | 'mvp' | 'pre_production' | 'production';
  tech_stack_preferences?: string[];
}

// ─── Pain Points ───
export interface PainPoint {
  name: string;
  description: string;
  severity: number;
  affected_stakeholders: string[];
  evidence: string;
}

// ─── Problem Statements ───
export interface ProblemStatement {
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
  session?: Session;
  industry?: string;
  location?: string;
}

// ─── Solutions ───
export interface Solution {
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
export interface RubricCriterion {
  name: string;
  description: string;
  weight: number;
  scale: { "1": string; "3": string; "5": string; };
}

export interface Disqualifier {
  name: string;
  description: string;
}

export interface Rubric {
  criteria: RubricCriterion[];
  disqualifiers: Disqualifier[];
}

export interface CriterionScore {
  criterion_name: string;
  score: number;
  justification: string;
  weight: number;
}

export interface Evaluation {
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

export interface DisqualifierResult {
  solution_title: string;
  passed: boolean;
  failed_disqualifiers: string[];
  reasons: string[];
}

export interface ScoringResult {
  solution_title: string;
  criterion_scores: {
    criterion: string;
    score: number;
    justification: string;
  }[];
  weighted_avg: number;
  min_score: number;
}

export interface AttackResult {
  solution_title: string;
  attack: string;
  severity: string;
  survives: boolean;
  survival_reasoning?: string;
}

export interface ACHResult {
  solution_title: string;
  inconsistencies: string[];
  count: number;
}

export interface ComparisonEntry {
  solution_id: string;
  solution_title: string;
  weighted_avg: number;
  min_score: number;
  attack_summary: string;
  attack_survives: boolean;
  inconsistency_count: number;
}

export interface ComparisonResult {
  entries: ComparisonEntry[];
  leaders: Record<string, string>;
  is_clear_winner: boolean;
  disagreements: string[];
}

// ─── Project & Build ───
export interface Project {
  id: string;
  user_id: string;
  solution_id: string;
  name: string;
  description: string | null;
  industry: string;
  location: string;
  maturity_level: string;
  tech_stack: string[] | Record<string, any> | null;
  status: string;
  project_dir: string | null;
  created_at: string;
  updated_at: string;
  documents?: Document[];
}

export interface Document {
  id: string;
  project_id: string;
  doc_type: string;
  title: string;
  content: string;
  version: number;
  status: string;
  created_at: string;
}

export interface Sprint {
  id: string;
  project_id: string;
  sprint_number: number;
  name: string;
  description: string | null;
  status: string;
  created_at: string;
  tasks: SprintTask[];
}

export interface SprintTask {
  id: string;
  sprint_id: string;
  task_number: number;
  name: string;
  prompt: string;
  status: string;
  test_command: string | null;
  test_count: number;
  tests_passed: number;
  tests_failed: number;
  retry_count: number;
  created_at: string;
  error_output?: string | null;
  rate_limit_reset_at?: string | null;
}

export interface BuildLogEntry {
  id: string;
  project_id: string;
  timestamp: string;
  level: string;
  source: string;
  message: string;
}


