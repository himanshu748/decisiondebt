export interface Impact {
  service_id: string;
  name: string;
  criticality: number;
  depth: number;
  paths: string[][];
  path_claim_ids: string[][];
  alternative_path_count: number;
  owner_status: string;
  owner_ids: string[];
  ownership_claims: {
    owner_id: string;
    name: string;
    claim_id: string;
    role: string;
  }[];
  score: number;
  priority: string;
  evidence_ids: string[];
  drift_ids: string[];
}
export interface Drift {
  id: string;
  tier: number;
  certainty: string;
  source_id: string;
  excerpt: string;
  context?: string;
  reason: string;
  related_service_ids: string[];
  evidence_claim_ids: string[];
  mention_id?: string;
}
export interface Query {
  query_id: string;
  cypher: string;
  params: Record<string, unknown>;
  row_count: number;
  elapsed_ms: number;
  graph_revision?: number;
}
export interface AskAnswer {
  status: "answered" | "ambiguous" | "unsupported" | "not_found";
  question: string;
  intent: string | null;
  service: { id: string; name: string } | null;
  message: string;
  supported_shapes: string[];
  suggestions: { id: string; name: string }[];
  rows: {
    label: string;
    detail: string;
    depth?: number;
    evidence_ids: string[];
  }[];
  citations: {
    id: string;
    source_id: string;
    anchor_field: string;
    start: number;
    end: number;
    excerpt: string;
    context?: string;
    source_sha256: string;
    anchor_verified: boolean;
  }[];
  counts: Record<string, number>;
  row_count: number;
  graph_revision: number | null;
  max_hops: number;
  truncated: boolean;
  truncation_examples: { service_id: string; name: string; depth: number }[];
  cycle_detected: boolean;
  query_trace: Query[];
  query_ms: number;
  elapsed_ms: number;
}
export interface Preview {
  decision_id: string;
  decision_status: string;
  decision: { title: string; old_id: string };
  graph_revision: number;
  counts: Record<string, number>;
  max_hops: number;
  truncated: boolean;
  truncation_examples?: { service_id: string; name: string; depth: number }[];
  cycle_detected: boolean;
  review_date_issues: { source_id: string; kind: string; reason: string }[];
  impacts: Impact[];
  projects: {
    project_id: string;
    name: string;
    via_service: string;
    claim_id: string;
  }[];
  drifts: Drift[];
  roots: string[];
  edges: { source: string; target: string; claim_id: string }[];
  query_trace: Query[];
  elapsed_ms: number;
}
export interface Summary {
  counts: Record<string, number>;
  source_types: { kind: string; count: number }[];
  claim_statuses: { status: string; count: number }[];
  graph_revision: number;
}
export interface Claim {
  id: string;
  source_id: string;
  relation: string;
  excerpt: string;
  method: string;
  status: string;
  anchor_field: string;
  start: number;
  end: number;
  source_sha256?: string;
  anchor_verified?: boolean;
}
export interface Source {
  id: string;
  title: string;
  kind: string;
  body: string;
  sha256: string;
  claims: Claim[];
  revisions: { id: string; sha256: string; created_at: string }[];
}
export interface Task {
  id: string;
  service_id: string;
  title: string;
  reason: string;
  priority: string;
  score: number;
  status: string;
  owner_id: string;
  owner_status: string;
  analysis_revision: number;
  evidence_ids: string[];
  path_json: string;
  uncertainty: string;
}
export interface Trace {
  tool?: string;
  args?: Record<string, unknown>;
  result?: unknown;
  status?: string;
  elapsed_ms?: number;
  model_summary?: string;
  provider_error?: string;
  message?: string;
}
export interface Run {
  execution_kind?: string;
  provider_verified?: boolean;
  coverage?: {
    all_passed: boolean;
    cases: Record<string, { passed: boolean; target_id: string }>;
  };
  provider?: string;
  id: string;
  mode: string;
  model: string;
  status: string;
  trace: Trace[];
  tool_calls: number;
  graph_revision: number;
  elapsed_ms: number;
}
export interface Topology {
  nodes: { id: string; name: string; criticality: number }[];
  edges: { source: string; target: string; claim_id: string }[];
  graph_revision: number;
}
