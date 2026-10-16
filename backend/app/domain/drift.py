from datetime import datetime
import re
from backend.app.domain.evidence import claim_evidence, search
from backend.app.graph.queries import Q6, Q8


def classify(g, decision, affected_ids, as_of, trace):
    findings = []
    unknown_dates = {}
    links = g.read(
        "MATCH (s:Source)-[d:DESCRIBES]->(v:Service) RETURN s.id AS source_id,v.id AS service_id,d.claim_id AS claim_id",
        query_id="SOURCE_LINKS",
        trace=trace,
    )
    by_source = {}
    for r in links:
        by_source.setdefault(r["source_id"], set()).add(r["service_id"])

    def related(src):
        return sorted(by_source.get(src, set()).intersection(affected_ids))

    t1 = g.read(Q6, {"old_id": decision["old_id"]}, "Q6", trace)
    explicit = {r["source_id"] for r in t1}
    for r in t1:
        e = claim_evidence(g, r["claim_id"], trace)
        findings.append(
            dict(
                id="T1:" + r["source_id"],
                tier=1,
                kind="explicit_stale_reference",
                certainty="confirmed_reference_obsolete",
                source_id=r["source_id"],
                excerpt=e["excerpt"],
                evidence_claim_ids=[r["claim_id"]],
                related_service_ids=related(r["source_id"]),
                reason="Explicitly cites the decision this proposal would supersede. Technical content still requires review.",
            )
        )
    for term in decision["obsolete_terms"] or []:
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{2,39}", term):
            continue
        # Native query returns at most 80; stable fixture contains fewer than 20 exact mentions.
        for r in search(g, term, limit=80, trace=trace, internal=True):
            if r["source_id"] in explicit:
                continue
            findings.append(
                dict(
                    id="T2:" + r["source_id"] + ":" + term,
                    tier=2,
                    kind="unlinked_obsolete_mention",
                    certainty="suspected_drift",
                    source_id=r["source_id"],
                    excerpt=r["excerpt"],
                    context=r["context"],
                    evidence_claim_ids=[],
                    mention_id=r["mention_id"],
                    related_service_ids=related(r["source_id"]),
                    reason="Native full-text match verified against an exact alias. Mention alone does not prove usage.",
                )
            )
    rows = g.read(Q8, {"affected_ids": affected_ids}, "Q8", trace)
    grouped = {}
    for r in rows:
        try:
            reviewed = datetime.fromisoformat(r["last_reviewed_at"])
            proposal = datetime.fromisoformat(decision["created_at"])
        except (ValueError, TypeError):
            unknown_dates[r["source_id"]] = {
                "source_id": r["source_id"],
                "kind": "unknown_review_date",
                "last_reviewed_at": r["last_reviewed_at"],
                "reason": "Review date cannot be parsed; no overdue finding was inferred.",
            }
            continue
        if reviewed.tzinfo is None:
            unknown_dates[r["source_id"]] = {
                "source_id": r["source_id"],
                "kind": "unknown_review_date",
                "last_reviewed_at": r["last_reviewed_at"],
                "reason": "Review date has no timezone; no overdue finding was inferred.",
            }
            continue
        if reviewed < proposal and (as_of - reviewed).days >= 90:
            if r["source_id"] not in grouped:
                evidence = claim_evidence(g, r["claim_id"], trace)
                grouped[r["source_id"]] = dict(
                    id="T3:" + r["source_id"],
                    tier=3,
                    kind="overdue_review",
                    certainty="needs_review",
                    source_id=r["source_id"],
                    excerpt=evidence["excerpt"],
                    evidence_claim_ids=[],
                    related_service_ids=[],
                    reason=f"Last reviewed {r['last_reviewed_at']}; at least 90 days old and before the proposal.",
                )
            item = grouped[r["source_id"]]
            item["evidence_claim_ids"].append(r["claim_id"])
            item["related_service_ids"].append(r["service_id"])
    findings.extend(grouped.values())
    return findings, list(unknown_dates.values())
