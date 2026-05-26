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
  status: 'discovery' | 'problem_generation' | 'solution_generation' | 'evaluation' | 'completed';
  created_at: string;
  updated_at: string;
}

export interface CreateSessionRequest {
  industry: string;
  location: string;
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
