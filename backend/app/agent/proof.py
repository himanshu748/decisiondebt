"""A saved run is genuine proof only with provider identity and all required investigations."""


def llm_proof(run):
    problems = []
    if run.get("mode") != "llm" or run.get("execution_kind") != "llm":
        problems.append("Run is not a genuine provider execution.")
    if not run.get("provider_verified"):
        problems.append("Provider response identity was not verified.")
    if run.get("status") != "completed":
        problems.append("Investigation did not complete successfully.")
    calls = run.get("provider_calls", [])
    if not calls or not all(
        c.get("provider_response_id") and c.get("provider_model") for c in calls
    ):
        problems.append("Provider response IDs or model identities are missing.")
    cases = run.get("coverage", {}).get("cases", {})
    if set(cases) != {"unowned", "conflicting_owners", "unlinked_mention"} or not all(
        c.get("passed") for c in cases.values()
    ):
        problems.append(
            "Not all three ambiguity cases have verified tool coverage and an outcome."
        )
    if (
        run.get("tool_calls", 99) > 12
        or run.get("turns", 99) > 8
        or run.get("elapsed_ms", 999999) > 90000
        or run.get("source_chars", 999999) > 12000
    ):
        problems.append("A run limit was exceeded.")
    return {
        "verified": not problems,
        "run_id": run.get("id"),
        "model": run.get("model"),
        "provider": run.get("provider"),
        "provider_call_count": len(calls),
        "cases": cases,
        "problems": problems,
    }
