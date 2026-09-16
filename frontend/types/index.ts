export interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  created_at: string | null;
}

export interface Customer {
  id: string;
  user_id: string | null;
  first_name: string;
  last_name: string;
  national_id: string | null;
  passport_number: string | null;
  birth_date: string | null;
  gender: string | null;
  nationality: string;
  province: string | null;
  city: string | null;
  address: string | null;
  phone: string | null;
  email: string | null;
  overall_risk_score: number;
  overall_risk_level: string;
  created_at: string | null;
  application_count: number;
}

export interface Application {
  id: string;
  application_number: string;
  customer_id: string;
  status: string;
  source: string;
  current_step: string;
  declared_income: string | null;
  source_of_funds: string | null;
  occupation: string | null;
  expected_volume: string | null;
  jurisdiction: string;
  submitted_at: string | null;
  decided_at: string | null;
  created_at: string | null;
  updated_at: string | null;
  customer_name: string;
  risk_level: string | null;
  risk_score: number | null;
  screenings?: ScreeningResult[];
}

export interface ApplicationDetail extends Application {
  customer: Customer | null;
  documents: Document[];
  events: ApplicationEvent[];
  risk: RiskAssessment | null;
  screenings: ScreeningResult[];
  decisions: Decision[];
  verifications: Verification[];
  cases: CaseSummary[];
  face_verification: FaceVerification | null;
}

export interface Document {
  id: string;
  application_id: string;
  customer_id: string;
  doc_type: string;
  status: string;
  original_filename: string;
  content_type: string;
  size_bytes: number;
  is_simulated: boolean;
  created_at: string | null;
  fields?: ExtractedField[];
}

export interface ExtractedField {
  id: string;
  document_id: string;
  field_name: string;
  field_label: string;
  value: string | null;
  confidence: number;
  confirmed: boolean;
}

export interface ApplicationEvent {
  id: string;
  kind: string;
  message: string;
  created_at: string | null;
}

export interface RiskAssessment {
  id: string;
  application_id: string;
  score: number;
  level: string;
  recommended_decision: string;
  explanation: string;
  created_at: string | null;
  factors: RiskFactor[];
}

export interface RiskFactor {
  code: string;
  label: string;
  weight: number;
  triggered: boolean;
  detail: string;
}

export interface ScreeningResult {
  id: string;
  kind: string;
  matched: boolean;
  score: number;
  list_name: string | null;
  matched_name: string | null;
  is_simulated: boolean;
  payload: Record<string, unknown> | null;
}

export interface Case {
  id: string;
  case_number: string;
  application_id: string;
  customer_id: string;
  status: string;
  priority: string;
  risk_level: string;
  assigned_to: string | null;
  sla_hours: number;
  sla_due_at: string | null;
  decision: string | null;
  decision_reason: string | null;
  created_at: string | null;
  customer_name: string;
  application_number: string;
}

export interface CaseSummary {
  id: string;
  case_number: string;
  status: string;
  priority: string;
  risk_level: string;
}

export interface CaseDetail extends Case {
  reviews: Review[];
  assignments: CaseAssignment[];
}

export interface Review {
  id: string;
  reviewer_id: string;
  action: string;
  reason: string;
  created_at: string | null;
}

export interface CaseAssignment {
  id: string;
  user_id: string;
  created_at: string | null;
}

export interface Decision {
  id: string;
  code: string;
  source: string;
  reason: string;
  policy_clauses: unknown[] | null;
  created_at: string | null;
}

export interface Verification {
  id: string;
  kind: string;
  status: string;
  score: number | null;
  details: Record<string, unknown> | null;
}

export interface FaceVerification {
  id: string;
  similarity: number;
  quality_score: number;
  confidence: number;
  decision: string;
  reasons: string[] | null;
  is_simulated: boolean;
}

export interface AuditEvent {
  id: string;
  actor_id: string | null;
  actor_role: string | null;
  action: string;
  entity: string;
  entity_id: string;
  previous_state: Record<string, unknown> | null;
  new_state: Record<string, unknown> | null;
  reason: string | null;
  ip: string | null;
  policy_version: string | null;
  model_version: string | null;
  created_at: string | null;
}

export interface Notification {
  id: string;
  title: string;
  body: string;
  kind: string;
  read: boolean;
  payload: Record<string, unknown> | null;
  created_at: string | null;
}

export interface Policy {
  id: string;
  code: string;
  title: string;
  created_at: string | null;
  versions: PolicyVersion[];
}

export interface PolicyVersion {
  id: string;
  version: string;
  is_active: boolean;
  body?: string;
  created_at: string | null;
  chunk_count?: number;
  chunks?: PolicyChunk[];
}

export interface PolicyChunk {
  id: string;
  clause: string;
  section: string;
  text: string;
}

export interface Job {
  id: string;
  kind: string;
  status: string;
  progress: number;
  stage: string;
  entity_id: string | null;
  error: string | null;
}

export interface KPIs {
  total_applications: number;
  new_applications: number;
  approved_count: number;
  rejected_count: number;
  in_review_count: number;
  approval_rate: number;
  rejection_rate: number;
  human_review_rate: number;
  avg_processing_hours: number;
  avg_review_hours: number;
  high_risk_count: number;
  critical_count: number;
  total_customers: number;
  total_cases: number;
  open_cases: number;
}

export interface AnalyticsData {
  kpis: KPIs;
  applications_over_time: { date: string; value: number }[];
  risk_distribution: { label: string; value: number }[];
  verification_funnel: { step: string; count: number; percentage: number }[];
  document_type_distribution: { label: string; value: number }[];
  status_distribution: { label: string; value: number }[];
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface SearchResult {
  id: string;
  type: string;
  title: string;
  subtitle: string;
  url: string;
}
