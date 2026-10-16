from backend.app.agent.guard import SCHEMAS, validate_task, evidence
from backend.app.domain.evidence import get_source, claim_evidence, search
from backend.app.domain.impact import ownership
from backend.app.graph.client import LOCK, DomainError

DESCRIPTIONS = {
    "get_impact_summary": "Read live affected services, unresolved ownership and graph revision.",
    "trace_dependency": "Inspect verified paths from an affected consumer to the changed provider.",
    "search_sources": "Search native FalkorDB full-text, then verify exact aliases in source text.",
    "read_evidence": "Read untrusted source context and verified active claim excerpts.",
    "investigate_ownership": "Read every primary owner and evidence, preserving gaps and conflicts.",
    "list_drift": "Inspect distinct stale citations, suspected mentions and overdue reviews.",
    "propose_remediation": "Propose a source-backed local draft, subject to evidence/revision validation.",
    "abstain": "Record uncertainty and decline an unsupported assignment or conclusion.",
}


def registry():
    return [
        {
            "type": "function",
            "function": {
                "name": name,
                "description": DESCRIPTIONS[name],
                "parameters": schema.model_json_schema(),
            },
        }
        for name, schema in SCHEMAS.items()
    ]


class ToolSession:
    def __init__(self, g, analysis):
        self.g = g
        self.analysis = analysis
        self.observed = set()
        self.tasks = {}
        self.abstentions = []
        self.source_chars = 0

    def call(self, name, arguments):
        if name not in SCHEMAS:
            raise DomainError("INVALID_TOOL", "Tool is not allowlisted")
        args = SCHEMAS[name].model_validate(arguments)
        with LOCK:
            if self.g.revision() != self.analysis["graph_revision"]:
                raise DomainError(
                    "STALE_ANALYSIS", "Graph changed during investigation", 409
                )
            if (
                name in ("get_impact_summary", "list_drift")
                and args.decision_id != self.analysis["decision_id"]
            ):
                raise DomainError(
                    "INVALID_TOOL", "Only the selected decision may be investigated"
                )
            if name == "get_impact_summary":
                result = {
                    "counts": self.analysis["counts"],
                    "impacts": self.analysis["impacts"][:20],
                    "graph_revision": self.analysis["graph_revision"],
                }
            elif name == "trace_dependency":
                item = next(
                    (
                        i
                        for i in self.analysis["impacts"]
                        if i["service_id"] == args.service_id
                    ),
                    None,
                )
                if not item:
                    raise DomainError("NOT_FOUND", "Affected service not found", 404)
                result = {
                    k: v
                    for k, v in item.items()
                    if k
                    in (
                        "service_id",
                        "paths",
                        "path_claim_ids",
                        "evidence_ids",
                        "depth",
                    )
                }
                allowed = [
                    (path, claims)
                    for path, claims in zip(item["paths"], item["path_claim_ids"])
                    if len(path) - 1 <= args.max_hops
                ]
                result["paths"] = [path for path, _ in allowed]
                result["path_claim_ids"] = [claims for _, claims in allowed]
                result["max_hops"] = args.max_hops
                result["outside_requested_depth"] = item["depth"] > args.max_hops
            elif name == "investigate_ownership":
                if not any(
                    i["service_id"] == args.service_id for i in self.analysis["impacts"]
                ):
                    raise DomainError("NOT_FOUND", "Affected service not found", 404)
                result = ownership(self.g, args.service_id)
                result["evidence"] = [
                    claim_evidence(self.g, r["claim_id"])
                    for r in result["ownership_claims"]
                ][:20]
                result["service_id"] = args.service_id
                impact = next(
                    i
                    for i in self.analysis["impacts"]
                    if i["service_id"] == args.service_id
                )
                path_ids = (
                    impact["path_claim_ids"][0][:1]
                    if impact["owner_status"] == "unowned"
                    else []
                )
                result["supporting_path_evidence"] = [
                    claim_evidence(self.g, ident) for ident in path_ids
                ]
                result["evidence_ids"] = [
                    e["id"]
                    for e in result["evidence"] + result["supporting_path_evidence"]
                ]
            elif name == "list_drift":
                result = {
                    "drifts": [
                        d
                        for d in self.analysis["drifts"]
                        if not args.tier or d["tier"] == args.tier
                    ][:20]
                }
            elif name == "search_sources":
                result = {"sources": search(self.g, args.alias, args.kind, args.limit)}
            elif name == "read_evidence":
                src = get_source(self.g, args.source_id)
                cs = (
                    args.claim_ids
                    or [c["id"] for c in src["claims"] if c["status"] == "verified"][:6]
                )
                claims = [claim_evidence(self.g, c) for c in cs]
                if any(c["source_id"] != src["id"] for c in claims):
                    raise DomainError(
                        "INVALID_EVIDENCE", "Claim must belong to the selected source"
                    )
                remaining = max(0, 12000 - self.source_chars)
                max_chars = min(args.max_chars, remaining)
                context = src["body"][:max_chars]
                result = {
                    "source_id": src["id"],
                    "source_sha256": src["sha256"],
                    "untrusted_source_text": context,
                    "claims": claims,
                    "source_text_budget_remaining": 12000 - self.source_chars,
                }
            elif name == "propose_remediation":
                task = validate_task(self.g, args, self.analysis, self.observed)
                self.tasks[task["id"]] = task
                result = {"draft_task": task}
            else:
                for ident in args.evidence_ids:
                    if ident not in self.observed:
                        raise DomainError(
                            "INVALID_EVIDENCE", "Abstention cites unseen evidence"
                        )
                    evidence(self.g, ident)
                if not self.g.read(
                    "MATCH (n {id:$id}) RETURN n.id AS id LIMIT 1",
                    {"id": args.target_id},
                ):
                    raise DomainError("NOT_FOUND", "Unknown abstention target", 404)
                result = {"abstention": args.model_dump()}
                self.abstentions.append(args.model_dump())

            # Reference inventory is derived from actual tool output, never model-supplied IDs.
            def collect(value):
                if isinstance(value, dict):
                    for k, v in value.items():
                        if k in ("claim_id", "mention_id") and isinstance(v, str):
                            self.observed.add(v)
                        if k in ("evidence_ids", "evidence_claim_ids") and isinstance(
                            v, list
                        ):
                            self.observed.update(x for x in v if isinstance(x, str))
                        if k == "id" and isinstance(v, str) and v.startswith("claim-"):
                            self.observed.add(v)
                        collect(v)
                elif isinstance(value, list):
                    for v in value:
                        collect(v)

            def cap_text(value):
                if isinstance(value, dict):
                    for k, v in value.items():
                        if k in (
                            "excerpt",
                            "context",
                            "untrusted_source_text",
                        ) and isinstance(v, str):
                            remaining = max(0, 12000 - self.source_chars)
                            value[k] = v[:remaining]
                            self.source_chars += len(value[k])
                        else:
                            cap_text(v)
                elif isinstance(value, list):
                    for v in value:
                        cap_text(v)

            cap_text(result)
            collect(result)
            return result
