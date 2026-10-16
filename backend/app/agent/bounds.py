"""Structured, bounded results preserve complete IDs and usable JSON for tool models."""

import json


def references(value):
    if isinstance(value, str):
        return {value} if value.startswith(("claim-", "mention:")) else set()
    if isinstance(value, dict):
        return set().union(*(references(v) for v in value.values())) if value else set()
    if isinstance(value, list):
        return set().union(*(references(v) for v in value)) if value else set()
    return set()


def bounded_result(name, result):
    def claim(c):
        return {
            k: (v[:200] if k == "excerpt" else v)
            for k, v in c.items()
            if k
            in (
                "id",
                "source_id",
                "relation",
                "excerpt",
                "status",
                "anchor_field",
                "start",
                "end",
                "anchor_verified",
                "source_sha256",
                "method",
            )
        }

    if name == "get_impact_summary":
        result = {
            **result,
            "impacts": [
                {
                    k: v
                    for k, v in i.items()
                    if k in ("service_id", "name", "owner_status", "priority", "depth")
                }
                for i in result.get("impacts", [])
            ],
        }
    elif name == "investigate_ownership":
        result = {
            **result,
            "evidence": [claim(c) for c in result.get("evidence", [])],
            "supporting_path_evidence": [
                claim(c) for c in result.get("supporting_path_evidence", [])
            ],
        }
    elif name == "search_sources":
        result = {
            **result,
            "sources": [
                {
                    k: (v[:240] if k == "context" else v)
                    for k, v in s.items()
                    if k
                    in (
                        "source_id",
                        "title",
                        "kind",
                        "context",
                        "excerpt",
                        "mention_id",
                        "source_sha256",
                        "exact_match",
                        "ft_score",
                    )
                }
                for s in result.get("sources", [])
            ],
        }
    elif name == "read_evidence":
        result = {
            **result,
            "claims": [claim(c) for c in result.get("claims", [])],
            "untrusted_source_text": result.get("untrusted_source_text", "")[:1500],
        }
    elif name == "list_drift":
        result = {
            **result,
            "drifts": [
                {
                    k: (v[:160] if k in ("excerpt", "reason") else v)
                    for k, v in d.items()
                    if k
                    in (
                        "id",
                        "tier",
                        "source_id",
                        "certainty",
                        "excerpt",
                        "reason",
                        "mention_id",
                        "evidence_claim_ids",
                        "related_service_ids",
                    )
                }
                for d in result.get("drifts", [])
            ],
        }
    result = json.loads(json.dumps(result))
    while len(json.dumps(result, ensure_ascii=False)) > 3000:
        result["truncated"] = True
        text = result.get("untrusted_source_text", "")
        if len(text) > 200:
            result["untrusted_source_text"] = text[: max(200, len(text) // 2)]
            continue
        arrays = [
            v
            for k, v in result.items()
            if isinstance(v, list)
            and len(v) > 2
            and k not in ("owner_ids", "evidence_ids", "ownership_claims", "evidence")
        ]
        if arrays:
            largest = max(arrays, key=lambda v: len(json.dumps(v)))
            largest.pop()
            continue
        # Refuse oversized output instead of passing malformed, sliced JSON to a model.
        return {
            "error": "TOOL_RESULT_LIMIT",
            "message": "Use a narrower source limit or fewer claim IDs.",
            "available_evidence_ids": sorted(references(result))[:6],
        }
    return result
