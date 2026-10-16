import json
import uuid
from threading import Lock
from fastapi import FastAPI, Depends, Query, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from backend.app.settings import ROOT, settings
from backend.app.security import require_admin
from backend.app.graph.client import Graph, GraphUnavailable, DomainError, LOCK
from backend.app.domain.models import (
    ImportRequest,
    RunRequest,
    AcceptRequest,
    PreviewResponse,
    HealthResponse,
    SummaryResponse,
    TopologyResponse,
    DecisionsResponse,
    SearchResponse,
    SourceResponse,
    ClaimsResponse,
    TasksResponse,
    RunsResponse,
    RunResponse,
    ApprovalResponse,
    ImportResponse,
    ClaimResponse,
)
from backend.app.domain.company import summary, topology
from backend.app.domain.impact import preview, DEFAULT_AS_OF
from backend.app.domain.evidence import get_source, claim_evidence, search
from backend.app.ingest.entities import Catalog
from backend.app.ingest.parsers import parse
from backend.app.ingest.refresh import refresh
from backend.app.routes.admin import accept, approve_task
from backend.app.agent.loop import run

app = FastAPI(
    title="DecisionDebt",
    version="1.0.0",
    description="Synthetic Aster Works company intelligence. Live FalkorDB, source-backed evidence.",
)
IMPORT_LOCK = Lock()


def graph():
    return Graph()


@app.exception_handler(GraphUnavailable)
async def graph_error(request, exc):
    return JSONResponse(
        status_code=503,
        content={
            "error": {
                "code": "GRAPH_UNAVAILABLE",
                "message": "FalkorDB is unavailable; no live impact was computed.",
                "request_id": uuid.uuid4().hex,
            }
        },
    )


@app.exception_handler(DomainError)
async def domain_error(request, exc):
    return JSONResponse(
        status_code=exc.status,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "request_id": uuid.uuid4().hex,
            }
        },
    )


@app.middleware("http")
async def boundaries(request: Request, call_next):
    if (
        request.url.path.startswith("/api/admin/")
        and settings.mode == "public-readonly"
    ):
        return JSONResponse(
            status_code=403,
            content={
                "error": {
                    "code": "FORBIDDEN",
                    "message": "Public demo is read-only.",
                    "request_id": uuid.uuid4().hex,
                }
            },
        )
    if request.method in ("POST", "PUT", "PATCH"):
        if len(await request.body()) > 262144:
            return JSONResponse(
                status_code=413,
                content={
                    "error": {
                        "code": "INVALID_SOURCE",
                        "message": "Request exceeds 256 KiB",
                        "request_id": uuid.uuid4().hex,
                    }
                },
            )
    with_request = await call_next(request)
    with_request.headers["X-Content-Type-Options"] = "nosniff"
    with_request.headers["Referrer-Policy"] = "same-origin"
    return with_request


@app.get("/api/health", response_model=HealthResponse)
def health(g=Depends(graph)):
    return dict(
        status="ok",
        graph_revision=g.health(),
        synthetic=True,
        source_mode="live_falkordb",
        provider_configured=bool(settings.api_key and settings.agent_mode == "llm"),
        mode=settings.mode,
    )


@app.get("/api/company/summary", response_model=SummaryResponse)
def company(g=Depends(graph)):
    return summary(g)


@app.get("/api/company/graph", response_model=TopologyResponse)
def company_graph(g=Depends(graph)):
    return topology(g)


@app.get("/api/decisions", response_model=DecisionsResponse)
def decisions(g=Depends(graph)):
    with LOCK:
        ds = g.read("MATCH (d:Decision) RETURN properties(d) AS decision ORDER BY d.id")
        approvals = g.read(
            "MATCH (a:ApprovalEvent) RETURN properties(a) AS approval ORDER BY a.at"
        )
        return dict(
            decisions=[d["decision"] for d in ds],
            approvals=[a["approval"] for a in approvals],
            graph_revision=g.revision(),
        )


@app.get("/api/decisions/{ident}/preview", response_model=PreviewResponse)
def decision_preview(ident: str, as_of: str = DEFAULT_AS_OF, g=Depends(graph)):
    return preview(g, ident, as_of)


@app.get("/api/impact/{service_id}/paths")
def paths(service_id: str, decision_id: str = "dec-auth-002", g=Depends(graph)):
    p = preview(g, decision_id)
    item = next((i for i in p["impacts"] if i["service_id"] == service_id), None)
    if not item:
        raise DomainError("NOT_FOUND", "Service is outside the bounded preview", 404)
    return dict(
        **item, query_trace=p["query_trace"], graph_revision=p["graph_revision"]
    )


@app.get("/api/sources/search", response_model=SearchResponse)
def source_search(
    q: str,
    kind: str | None = None,
    limit: int = Query(default=20, ge=1, le=20),
    g=Depends(graph),
):
    with LOCK:
        trace = []
        results = search(g, q, kind, limit, trace)
        return dict(sources=results, query_trace=trace, graph_revision=g.revision())


@app.get("/api/sources/{ident}", response_model=SourceResponse)
def source(ident: str, g=Depends(graph)):
    with LOCK:
        return get_source(g, ident)


@app.get("/api/claims/{ident}", response_model=ClaimResponse)
def claim(ident: str, g=Depends(graph)):
    with LOCK:
        return claim_evidence(g, ident)


@app.get("/api/claims", response_model=ClaimsResponse)
def claims(status: str = "candidate", g=Depends(graph)):
    with LOCK:
        return {
            "claims": [
                r["claim"]
                for r in g.read(
                    "MATCH (c:Claim {status:$status}) RETURN properties(c) AS claim LIMIT 100",
                    {"status": status},
                )
            ],
            "graph_revision": g.revision(),
        }


@app.get("/api/tasks", response_model=TasksResponse)
def tasks(decision_id: str = "dec-auth-002", g=Depends(graph)):
    with LOCK:
        return dict(
            tasks=[
                r["task"]
                for r in g.read(
                    "MATCH (t:Task {decision_id:$id}) RETURN properties(t) AS task ORDER BY t.score DESC",
                    {"id": decision_id},
                )
            ],
            graph_revision=g.revision(),
        )


@app.get("/api/agent/runs", response_model=RunsResponse)
def runs(g=Depends(graph)):
    with LOCK:
        return {
            "runs": g.read(
                "MATCH (r:AgentRun) RETURN r.id AS id,r.mode AS mode,r.model AS model,r.status AS status,r.started_at AS started_at ORDER BY started_at DESC LIMIT 20"
            )
        }


@app.get("/api/agent/runs/{ident}", response_model=RunResponse)
def agent_run(ident: str, g=Depends(graph)):
    with LOCK:
        rows = g.read(
            "MATCH (r:AgentRun {id:$id}) RETURN properties(r) AS run", {"id": ident}
        )
        if not rows:
            raise DomainError("NOT_FOUND", "Unknown run", 404)
        r = rows[0]["run"]
        r["trace"] = json.loads(r.pop("trace_json"))
        for key in (
            "coverage",
            "provider_calls",
            "token_usage",
            "progress_feedback",
            "tool_offers",
        ):
            if key + "_json" in r:
                r[key] = json.loads(r.pop(key + "_json"))
        return r


@app.post(
    "/api/admin/import",
    response_model=ImportResponse,
    dependencies=[Depends(require_admin)],
)
def import_source(body: ImportRequest, g=Depends(graph)):
    if not IMPORT_LOCK.acquire(blocking=False):
        raise DomainError("RATE_LIMITED", "An import is already running", 429)
    try:
        try:
            src = parse(body.kind, body.content)
            return refresh(g, [src], Catalog())
        except (ValueError, KeyError, TypeError) as e:
            raise DomainError("INVALID_SOURCE", str(e)[:300]) from e
    finally:
        IMPORT_LOCK.release()


@app.post(
    "/api/admin/decisions/{ident}/accept",
    response_model=ApprovalResponse,
    dependencies=[Depends(require_admin)],
)
def accept_decision(ident: str, body: AcceptRequest, g=Depends(graph)):
    return accept(g, ident, body.confirm)


@app.post(
    "/api/admin/tasks/{ident}/approve",
    response_model=ApprovalResponse,
    dependencies=[Depends(require_admin)],
)
def approve(ident: str, body: AcceptRequest, g=Depends(graph)):
    return approve_task(g, ident, body.confirm)


@app.post(
    "/api/admin/agent/runs",
    response_model=RunResponse,
    dependencies=[Depends(require_admin)],
)
def agent(body: RunRequest, g=Depends(graph)):
    return run(g, body.decision_id, body.mode)


DIST = ROOT / "web/dist"
if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/")
    @app.get("/studio")
    def spa():
        return FileResponse(DIST / "index.html")
