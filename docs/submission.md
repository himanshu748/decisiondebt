# DecisionDebt — Know what a decision breaks before you make it

**Track: Company Brain (Track 03)** — WeMakeDevs x FalkorDB Graph Hacks

DecisionDebt connects a company's people, teams, projects, services, documents and decisions in FalkorDB. Before a proposed change is accepted, it traces the affected services and projects, checks source-backed ownership, and finds knowledge that needs review. A bounded agent investigates uncertainty and produces local drafts for separate human approval.

## Required links

| Deliverable | Link |
|---|---|
| Public repository | https://github.com/himanshu748/decisiondebt |
| Live read-only demo | https://decisiondebt.52.202.25.181.sslip.io/ |
| YouTube demo, unlisted · 2:57 | https://youtu.be/_a0vrYwOlME |
| Complete local setup | [README: Run locally](https://github.com/himanshu748/decisiondebt/blob/main/README.md#run-locally) |
| Graph data model | [README: Graph model](https://github.com/himanshu748/decisiondebt/blob/main/README.md#graph-model) |
| Product Cypher queries | [Actual query templates](https://github.com/himanshu748/decisiondebt/blob/main/backend/app/graph/queries.py) |
| Why FalkorDB is central | [Load-bearing operations and queries](https://github.com/himanshu748/decisiondebt/blob/main/README.md#why-falkordb-is-load-bearing) |
| Decision lineage | [Live graph records](https://decisiondebt.52.202.25.181.sslip.io/api/decisions) |
| Agent results and work | [Action Board](https://decisiondebt.52.202.25.181.sslip.io/studio?tab=Action%20Board) |
| CI | [GitHub Actions](https://github.com/himanshu748/decisiondebt/actions/workflows/ci.yml) |

## What the working demonstration establishes

All records belong to fictional Aster Works. The [original corpus receipt](https://github.com/himanshu748/decisiondebt/blob/main/evidence/query-results/initial-preview.json) and [synthetic snapshot](https://github.com/himanshu748/decisiondebt/blob/main/evidence/deployment/graph-snapshot-20261016.json) make the dataset reproducible. Native graph queries establish multi-hop impact, ownership, connected projects and document provenance; the browser displays those returned results.

The [genuine provider trace](https://github.com/himanshu748/decisiondebt/blob/main/evidence/agent-traces/llm-run.json) and [three-case proof](https://github.com/himanshu748/decisiondebt/blob/main/evidence/agent-traces/llm-proof.json) record an investigation of missing Token Cache ownership, conflicting Session Broker owners, and an unlinked OrionAuth mention. Ambiguous owners stay unassigned. The mention supports a qualified document review with suspected-drift uncertainty. Rejected calls and model corrections remain in the trace.

The [recorded import/retraction receipt](https://github.com/himanshu748/decisiondebt/blob/main/evidence/query-results/dynamic-import.json) shows the affected set changing from 12 to 13 and back to 12 when one source's dependency support is added and removed. Separate local task approval is shown in the video; the migration itself remains proposed.

The public deployment is read-only and displays the recorded provider run; no visitor can import, invoke a provider, approve tasks or accept a decision. [HTTPS public smoke results](https://github.com/himanshu748/decisiondebt/blob/main/evidence/public-reliability-20261016/https-smoke.json) record write denials, native search, unchanged graph revision and rate limiting. It uses its own HTTPS hostname through an additive reverse-proxy site; port 8081 remains a fallback. The [external Chromium receipt](https://github.com/himanshu748/decisiondebt/blob/main/evidence/public-reliability-20261016/after-https/receipt.json) records fresh-profile checks at 1440 and 375 pixels. The [isolation receipt](https://github.com/himanshu748/decisiondebt/blob/main/evidence/public-reliability-20261016/isolation.json) confirms unchanged EmbodiWeave content, certificate and container identities. No credentials are needed for the public demo.

The [deployment receipt](https://github.com/himanshu748/decisiondebt/blob/main/evidence/deployment/receipt-20261016.json) records the URL, source commit, timestamp, credential exclusion, separate graph and real database outage/restart. Removing FalkorDB made preview, company summary and investigation-history reads return 503. Restart restored the same revision, while EmbodiWeave container identities and start times stayed unchanged during that outage test. The [isolation review](https://github.com/himanshu748/decisiondebt/blob/main/evidence/deployment/isolation-review-20261016.json) distinguishes that proof from the earlier preflight, which observed different EmbodiWeave containers.

[CI test output](https://github.com/himanshu748/decisiondebt/blob/main/evidence/ci/38896361671/pytest.txt) records 46 passing tests. The [successful run receipt](https://github.com/himanshu748/decisiondebt/blob/main/evidence/ci/run-38896361671.json) also verifies the frontend build and Chromium UI smoke. New runs are labeled separately; earlier measured evidence remains unchanged.

The **2:57.4** [narrated 4K demo](https://github.com/himanshu748/decisiondebt/blob/main/evidence/demo-v3/decisiondebt-demo-4k-under3.mp4) uses actual browser video captured at 3840×2160 and 30 fps, with close-ups and Deepgram AI narration. It shows live source inspection, the previously recorded genuine LLM trace, local task approval, and a new import/retraction demonstration in an isolated synthetic recording database. The public site permits reads only. Automated recording actions are not attributed to the participant as personal verification. [Capture receipt](https://github.com/himanshu748/decisiondebt/blob/main/evidence/demo-v3/capture-receipt.json) · [Edit receipt](https://github.com/himanshu748/decisiondebt/blob/main/evidence/demo-v3/under3-edit-receipt.json) · [Speech verification](https://github.com/himanshu748/decisiondebt/blob/main/evidence/demo-v3/speech-verification-under3.json) · [Video and preservation verification](https://github.com/himanshu748/decisiondebt/blob/main/evidence/demo-v3/verification.json).

[YouTube publication and 2160p playback receipt](https://github.com/himanshu748/decisiondebt/blob/main/evidence/demo-v3/youtube-upload-receipt.json) confirms the new unlisted upload, English captions and selected 2160p playback.

The [previous silent MP4](https://github.com/himanshu748/decisiondebt/blob/main/evidence/decisiondebt-demo.mp4), [historical capture manifest](https://github.com/himanshu748/decisiondebt/blob/main/evidence/demo-v2/manifest.json), and earlier application, provider and video measurements remain unchanged.

The [final automated submission review](https://github.com/himanshu748/decisiondebt/blob/main/evidence/submission-review-20261016/review.json) records fresh public workflow checks and preserved historical evidence. The [updated video disclosure receipt](https://github.com/himanshu748/decisiondebt/blob/main/evidence/demo-recheck-20261016/youtube-description.json) records the matching YouTube description; the video and captions are unchanged.

## AI disclosure and participant responsibility

I originated the core idea and directed the UI. AI expanded the detailed specification. I chose the separate landing and studio routes, requested the dashboard redesign, required an isolated read-only public deployment and genuine three-case LLM proof, and specified the replacement 4K demo with Deepgram narration below three minutes. The [full disclosure](https://github.com/himanshu748/decisiondebt/blob/main/README.md#ai-coding-disclosure) links those product decisions to their records.

Codex generated most of the implementation, tests and styling, plus the synthetic corpus, documentation, deployment/CI configuration, browser automation and video editing. Deepgram generated the narration. The [fresh Codex demo rerun](https://github.com/himanshu748/decisiondebt/blob/main/evidence/demo-recheck-20261016/verification.json) checked the 12-service impact result and Session Broker paths, original ownership-source evidence, and public write denials with an unchanged graph revision.

The participant remains responsible for understanding and explaining the code, graph model, queries and architecture under Rules 12–13. This file contains the submission text. This automation has not submitted the entry. Submit by **October 18, 2026, 11:59 PM IST**. [Official rules](https://www.wemakedevs.org/hackathons/falkordb/rules).
