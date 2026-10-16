# Genuine investigation findings

Run `run-07fef4a6b0464a57b15fb2e809e30e02` completed on 2026-10-16. It used OpenRouter's `nvidia/nemotron-3-super-120b-a12b:free` route, upstream Nvidia, with fallback disabled and prompt/completion maximum prices set to zero. The user explicitly approved reusing the existing EmbodiWeave key in DecisionDebt's ignored private `.env`. No key value is retained here.

[Recorded trace](agent-traces/llm-run.json) · [Machine proof](agent-traces/llm-proof.json) · [UI](screenshots/real-llm-trace.png)

Measured bounds: **8 model turns, 11 tool calls, 51,618.37 ms, 1,233 source characters**. Aggregate usage: 55,095 prompt tokens, 1,881 completion tokens, 56,976 total. All eight provider calls have actual response IDs and model identity; provider-reported cost totals **$0**. This records the completed run, not future quota or price guarantees. Analysis revision 12; persisted at revision 13.

| Ambiguity | Evidence actually retrieved | Model-selected outcome |
|---|---|---|
| Missing Token Cache owner | Ownership inspection returns no primary claims; verified `doc-005` dependency; native additional `ticket-047` context says Project Waypoint uses Token Cache, without identifying an owner. | `verify_owner`, task `task-ec6bc7d10728fc930aae4cb8`, owner blank. A dependency or project use does not identify an owner. |
| Conflicting Session Broker owners | `claim-a95d41576b896f0d8b140a35`, `doc-021`, Devon Shah; `claim-14c45e7d019b11ff49072d05`, `chat-077`, Taylor Roy. Both verified primary excerpts were returned. | `verify_owner`, task `task-98752902c2c69b3b7f1766b0`, owner blank; resolve the conflict before assignment. |
| Unlinked OrionAuth mention | Model requested native full-text search for `OrionAuth` in docs, then read full `doc-002` context. The paragraph explicitly says the checklist mention does not establish a provider dependency. | `review_doc`, task `task-ee6e0bfcdabd37376f08d931`, owner blank, `uncertainty=suspected_drift`; review whether the historical reference needs updating. No dependency claim was activated. |

Three rejected calls remain in the trace: a mention ID supplied as a Claim ID to `read_evidence`, then two ownership proposals citing a mention as task evidence. The model corrected the source read and ultimately cited only the verified dependency claim for Token Cache. The server accepted no invented owner. The document proposal's prose refers to an obsolete term, while the stored uncertainty remains suspected drift; its existence does not prove current provider use.

After recording, a separate human-style local confirmation approved the Token Cache task at graph revision 14. Its owner stayed blank. The import/retraction walkthrough then changed the affected set 12 → 13 → 12 at revisions 14 → 15 → 16. Neither the provider nor this walkthrough accepted the migration.

## Controller and retained failures

The controller gives factual coverage/budget feedback after each model turn. Tool schemas enumerate actual service IDs and retrieved evidence. Once all required retrieval is complete, only proposal and abstention tools remain available; task content and citations are still model-selected. Ownership investigation includes at most one additional native matching ticket, with a chat fallback. The recorded tool output identifies the source, exact span, paragraph and hash.

Six earlier persisted runs are retained as `agent-traces/llm-incomplete-run-*.json`. They include turn/call exhaustion, incomplete case coverage and one transport overrun. `llm-attempt-2-server-error.txt` records the hyphenated full-text parser failure; that attempt has no complete saved provider trace. `llm-attempt-5-client-timeout.txt` accompanies the 121-second overrun, which is explicitly excluded from proof. No failed attempt is relabeled as successful.

The measured fixes were safe native query tokenization, matching-paragraph context, actual-ID tool schemas, coverage feedback, outcome-stage tool restriction, and a hard request deadline around the HTTP client. The regression suite checks these paths without making paid model calls. Mocked runs cannot satisfy `llm_proof`.
