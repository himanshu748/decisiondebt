"""Audit what the model actually retrieved and resolved, without prescribing tool order."""

from backend.app.ingest.entities import Catalog


class Coverage:
    def __init__(self, analysis):
        self.analysis = analysis
        self.catalog = Catalog()
        self.gaps = {
            i["service_id"]
            for i in analysis["impacts"]
            if i["owner_status"] == "unowned"
        }
        self.conflicts = {
            i["service_id"]: {o["claim_id"] for o in i["ownership_claims"]}
            for i in analysis["impacts"]
            if i["owner_status"] == "conflict"
        }
        self.suspects = {
            d["source_id"]: d for d in analysis["drifts"] if d["tier"] == 2
        }
        self.owners_seen = set()
        self.additional_sources = set()
        self.conflict_claims = set()
        self.mention_sources = set()
        self.context_sources = set()
        self.outcomes = []

    def observe(self, name, args, result):
        if name == "investigate_ownership":
            self.owners_seen.add(args.get("service_id"))
            self.conflict_claims.update(
                e["id"] for e in result.get("evidence", []) if e.get("id")
            )
        elif name == "search_sources":
            for src in result.get("sources", []):
                if src.get("kind") in ("chat", "ticket"):
                    self.additional_sources.add(
                        (args.get("alias", "").casefold(), src["source_id"])
                    )
                if src["source_id"] in self.suspects and args.get(
                    "alias", ""
                ).casefold() in {
                    t.casefold() for t in self.analysis["decision"]["obsolete_terms"]
                }:
                    self.mention_sources.add(src["source_id"])
        elif name == "read_evidence":
            if result.get("untrusted_source_text"):
                self.context_sources.add(args.get("source_id"))
        elif name == "propose_remediation" and "draft_task" in result:
            self.outcomes.append({"tool": name, **result["draft_task"]})
        elif name == "abstain" and "abstention" in result:
            self.outcomes.append({"tool": name, **result["abstention"]})

    def report(self):
        cases = {}
        for service in sorted(self.gaps):
            entity = self.catalog.by_id[service]
            aliases = {
                a.casefold()
                for a in [service, entity["name"], *entity.get("aliases", [])]
            }
            extra = sorted(
                src for alias, src in self.additional_sources if alias in aliases
            )
            outcomes = [
                o
                for o in self.outcomes
                if (
                    o.get("service_id") == service
                    and o.get("kind") == "verify_owner"
                    and not o.get("owner_id")
                )
                or (o.get("target_id") == service and o["tool"] == "abstain")
            ]
            cases["unowned"] = {
                "target_id": service,
                "ownership_inspected": service in self.owners_seen,
                "additional_source_ids": extra,
                "outcome_ids": [o.get("id", "abstention") for o in outcomes],
                "passed": service in self.owners_seen
                and bool(extra)
                and bool(outcomes),
            }
        for service, claims in self.conflicts.items():
            outcomes = [
                o
                for o in self.outcomes
                if (
                    o.get("service_id") == service
                    and o.get("kind") == "verify_owner"
                    and not o.get("owner_id")
                )
                or (o.get("target_id") == service and o["tool"] == "abstain")
            ]
            seen = sorted(claims & self.conflict_claims)
            cases["conflicting_owners"] = {
                "target_id": service,
                "ownership_inspected": service in self.owners_seen,
                "primary_claim_ids": sorted(claims),
                "read_claim_ids": seen,
                "outcome_ids": [o.get("id", "abstention") for o in outcomes],
                "passed": service in self.owners_seen
                and claims <= self.conflict_claims
                and bool(outcomes),
            }
        for src, drift in self.suspects.items():
            outcomes = [
                o
                for o in self.outcomes
                if (
                    o.get("kind") == "review_doc"
                    and drift.get("mention_id") in o.get("evidence_ids", [])
                    and o.get("uncertainty") == "suspected_drift"
                )
                or (o.get("target_id") == src and o["tool"] == "abstain")
            ]
            cases["unlinked_mention"] = {
                "target_id": src,
                "native_search_used": src in self.mention_sources,
                "source_context_read": src in self.context_sources,
                "outcome_ids": [o.get("id", "abstention") for o in outcomes],
                "passed": src in self.mention_sources
                and src in self.context_sources
                and bool(outcomes),
            }
        return {
            "cases": cases,
            "all_passed": len(cases) == 3 and all(c["passed"] for c in cases.values()),
        }
