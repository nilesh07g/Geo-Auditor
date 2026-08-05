export type Severity = 'critical' | 'high' | 'medium' | 'low';
export type Confidence = 'high' | 'medium' | 'low';
export type Impact = 'high' | 'medium' | 'low';
export type Effort = 'high' | 'medium' | 'low';
export type Grade = 'Strong' | 'Moderate gaps' | 'At Risk' | 'Critical';

export interface Finding {
  id: string;
  title: string;
  severity: Severity;
  confidence: Confidence;
  evidence: string;
  why_it_matters: string;
  recommended_fix: string;
  page_url?: string;
  check_id: string;
}

export interface ScoreBreakdownItem {
  check_id: string;
  check_name: string;
  score: number;
  max_score: number;
  weight: number;
  weighted_score: number;
}

export interface CheckResult {
  check_id: string;
  check_name: string;
  score: number;
  max_score: number;
  weight: number;
  weighted_score: number;
  findings: Finding[];
}

export interface ActionPlanItem {
  rank: number;
  action: string;
  impact: Impact;
  effort: Effort;
  source_finding_title?: string;
}

export interface Limitation {
  description: string;
}

export interface AuditResponse {
  url: string;
  business_name?: string;
  audited_at: string;
  geo_score: number;
  grade: Grade;
  executive_summary: string;
  aha_line: string;
  score_breakdown: ScoreBreakdownItem[];
  check_results: CheckResult[];
  action_plan: ActionPlanItem[];
  strengths: string[];
  limitations: Limitation[];
  pages_analyzed: string[];
}

export interface AIVisibilityPromptResult {
  prompt: string;
  mentioned: boolean;
  cited: boolean;
  response_excerpt: string;
  competitors_mentioned: string[];
}

export interface AIVisibilityResponse {
  url: string;
  business_name: string;
  results: AIVisibilityPromptResult[];
  experimental: boolean;
  note: string;
}
