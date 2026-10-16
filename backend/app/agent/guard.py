import hashlib
import re
from typing import Literal
from pydantic import Field
from backend.app.domain.models import Strict
from backend.app.graph.client import DomainError
from backend.app.domain.evidence import claim_evidence, get_source
from backend.app.domain.impact import ownership

ID = r"^[a-z][a-z0-9-]{2,79}$"


class DecisionArgs(Strict):
    decision_id: str = Field(pattern=ID)


class DependencyArgs(Strict):
    service_id: str = Field(pattern=ID)
    max_hops: int = Field(default=5, ge=1, le=5)


class SearchArgs(Strict):
    alias: str = Field(min_length=3, max_length=80)
    kind: Literal["doc", "ticket", "chat"] | None = None
    limit: int = Field(default=10, ge=1, le=20)


class ReadArgs(Strict):
    source_id: str = Field(pattern=ID)
    claim_ids: list[str] = Field(default_factory=list, max_length=20)
    max_chars: int = Field(default=2000, ge=100, le=3000)


class OwnerArgs(Strict):
    service_id: str = Field(pattern=ID)


class DriftArgs(DecisionArgs):
    tier: Literal[1, 2, 3] | None = None


class ProposeArgs(Strict):
    service_id: str = Field(
        pattern=ID,
        description="An affected svc-* service ID from the preview, never a doc-* or source ID. For document review use its related_service_ids.",
    )
    kind: Literal[
        "review_doc",
        "verify_owner",
        "migrate_client",
        "update_runbook",
        "test_integration",
    ] = Field(
        description="Use verify_owner for missing or conflicting primary ownership. Use review_doc for source-content review, including suspected obsolete mentions."
    )
    title: str = Field(min_length=8, max_length=160)
    reason: str = Field(min_length=10, max_length=1000)
    evidence_ids: list[str] = Field(
        min_length=1,
        max_length=20,
        description="Copy complete retrieved Claim IDs or mention IDs. Source IDs are not evidence IDs. Ownership review cites ownership/path Claim IDs; mention IDs support only document review.",
    )
    owner_id: str | None = Field(
        default=None,
        description="Leave null for unowned or conflicting services. Source authors and users are not verified primary owners.",
    )


class AbstainArgs(Strict):
    target_id: str = Field(pattern=ID)
    reason: str = Field(min_length=10, max_length=1000)
    evidence_ids: list[str] = Field(default_factory=list, max_length=20)


SCHEMAS = {
    "get_impact_summary": DecisionArgs,
    "trace_dependency": DependencyArgs,
    "search_sources": SearchArgs,
    "read_evidence": ReadArgs,
    "investigate_ownership": OwnerArgs,
    "list_drift": DriftArgs,
    "propose_remediation": ProposeArgs,
    "abstain": AbstainArgs,
}


def evidence(g, ident):
    if ident.startswith("mention:"):
        try:
            _, source_id, sha, start, end = ident.split(":")
            start = int(start)
            end = int(end)
        except (ValueError, TypeError):
            raise DomainError("INVALID_EVIDENCE", "Malformed source mention")
        s = get_source(g, source_id)
        if s["sha256"] != sha or start < 0 or end <= start or end > len(s["body"]):
            raise DomainError("INVALID_EVIDENCE", "Stale source mention")
        return {
            "source_id": source_id,
            "excerpt": s["body"][start:end],
            "suspected": True,
            "id": ident,
        }
    c = claim_evidence(g, ident)
    return {**c, "suspected": False}


def validate_task(g, args, analysis, observed):
    if g.revision() != analysis["graph_revision"]:
        raise DomainError(
            "STALE_ANALYSIS", "Graph changed. Run a fresh investigation.", 409
        )
    impact = next(
        (i for i in analysis["impacts"] if i["service_id"] == args.service_id), None
    )
    if not impact:
        raise DomainError("INVALID_TASK", "Service must exist in the live affected set")
    if not set(args.evidence_ids) <= observed:
        raise DomainError(
            "INVALID_EVIDENCE",
            "Task must cite evidence actually retrieved during this run",
        )
    proofs = [evidence(g, e) for e in args.evidence_ids]
    relevant = set(impact["evidence_ids"])
    # Mention-only evidence can support qualified document review, never a firm migration assertion.
    suspect = any(e["suspected"] for e in proofs)
    if suspect:
        if args.kind != "review_doc" or not re.search(
            r"\b(review|verify|possible|suspect|mention|check)\b",
            args.title + " " + args.reason,
            re.I,
        ):
            raise DomainError(
                "INVALID_TASK", "Unlinked mentions require a qualified review_doc task"
            )
    elif not any(e in relevant for e in args.evidence_ids):
        scoped = g.read(
            "MATCH (s:Source)-[:DESCRIBES]->(v:Service {id:$id}) RETURN s.id AS id",
            {"id": args.service_id},
        )
        if not any(p["source_id"] in {r["id"] for r in scoped} for p in proofs):
            raise DomainError(
                "INVALID_EVIDENCE", "Evidence does not support this service"
            )
    owners = ownership(g, args.service_id)
    owner = (
        args.owner_id
        if owners["owner_status"] == "single_primary"
        and args.owner_id in owners["owner_ids"]
        else None
    )
    if (
        owners["owner_status"] != "single_primary"
        and args.kind != "verify_owner"
        and args.owner_id
    ):
        owner = None
    key = (
        analysis["decision_id"]
        + args.service_id
        + args.kind
        + str(analysis["graph_revision"])
    )
    return dict(
        id="task-" + hashlib.sha256(key.encode()).hexdigest()[:24],
        decision_id=analysis["decision_id"],
        service_id=args.service_id,
        kind=args.kind,
        title=args.title,
        reason=args.reason,
        evidence_ids=args.evidence_ids,
        owner_id=owner or "",
        owner_status=owners["owner_status"],
        status="proposed",
        priority=impact["priority"],
        score=impact["score"],
        analysis_revision=analysis["graph_revision"],
        path_json=__import__("json").dumps(impact["paths"][0]),
        path_claim_ids=impact["path_claim_ids"][0],
        uncertainty="suspected_drift" if suspect else "",
    )
