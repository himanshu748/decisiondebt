from pydantic import BaseModel, ConfigDict, Field


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Source(Strict):
    id: str
    kind: str
    title: str
    body: str
    raw_text: str
    sha256: str
    created_at: str
    author_id: str
    last_reviewed_at: str = ""
    metadata: dict = Field(default_factory=dict)


class Claim(Strict):
    id: str
    relation: str
    subject_id: str
    object_id: str
    source_id: str
    source_revision_id: str
    anchor_field: str = "body"
    start: int
    end: int
    excerpt: str
    method: str = "explicit_rule"
    confidence: float = 1.0
    status: str = "verified"
    uncertainty: str = ""


class ImportRequest(Strict):
    kind: str
    content: str = Field(max_length=65536)


class RunRequest(Strict):
    decision_id: str = "dec-auth-002"
    mode: str = "deterministic"


class AcceptRequest(Strict):
    confirm: bool = False


class TruncationExample(Strict):
    service_id: str
    name: str
    depth: int


class PreviewResponse(BaseModel):
    decision_id: str
    decision_status: str
    analysis_mode: str = "preview"
    graph_revision: int
    as_of: str
    max_hops: int = 5
    truncated: bool
    truncation_examples: list[TruncationExample] = Field(default_factory=list)
    cycle_detected: bool = False
    review_date_issues: list[dict] = Field(default_factory=list)
    counts: dict
    impacts: list[dict]
    projects: list[dict]
    drifts: list[dict]
    query_trace: list[dict]
    source_mode: str = "live_falkordb"
    roots: list[str]
    edges: list[dict]
    decision: dict
    elapsed_ms: float


class HealthResponse(Strict):
    status: str
    graph_revision: int
    synthetic: bool
    source_mode: str
    provider_configured: bool
    mode: str


class SummaryResponse(Strict):
    counts: dict[str, int]
    source_types: list[dict]
    claim_statuses: list[dict]
    graph_revision: int
    synthetic: bool
    source_mode: str
    elapsed_ms: float


class TopologyResponse(Strict):
    nodes: list[dict]
    edges: list[dict]
    graph_revision: int
    source_mode: str


class DecisionsResponse(Strict):
    decisions: list[dict]
    approvals: list[dict]
    graph_revision: int


class SearchResponse(Strict):
    sources: list[dict]
    query_trace: list[dict]
    graph_revision: int


class AskResponse(Strict):
    status: str
    question: str
    intent: str | None
    service: dict | None
    message: str
    supported_shapes: list[str]
    suggestions: list[dict]
    rows: list[dict]
    citations: list[dict]
    counts: dict[str, int]
    row_count: int
    graph_revision: int | None
    max_hops: int
    truncated: bool
    truncation_examples: list[TruncationExample]
    cycle_detected: bool
    query_trace: list[dict]
    query_ms: float
    elapsed_ms: float
    source_mode: str


class SourceResponse(Strict):
    id: str
    kind: str
    title: str
    body: str
    sha256: str
    created_at: str
    author_id: str
    last_reviewed_at: str
    active_revision: str
    claims: list[dict]
    revisions: list[dict]


class ClaimsResponse(Strict):
    claims: list[dict]
    graph_revision: int


class TasksResponse(Strict):
    tasks: list[dict]
    graph_revision: int


class RunsResponse(Strict):
    runs: list[dict]


class RunResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    mode: str
    model: str
    decision_id: str
    status: str
    graph_revision: int
    trace: list[dict]
    tool_calls: int


class ApprovalResponse(Strict):
    id: str
    status: str
    graph_revision: int
    approval_id: str | None = None


class ImportResponse(Strict):
    sources: list[dict]
    graph_revision: int
    changed: int


class ClaimResponse(Claim):
    source_sha256: str
    anchor_verified: bool
