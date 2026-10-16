# DecisionDebt — Know what a decision breaks before you make it

**Track: Company Brain (Track 03)** — WeMakeDevs x FalkorDB Graph Hacks

DecisionDebt connects a company's people, teams, projects, services, documents and decisions in FalkorDB. Before a proposed change is accepted, it traces the affected services and projects, checks source-backed ownership, and finds knowledge that needs review. A bounded agent investigates uncertainty and produces local drafts for separate human approval.

## Required links

| Deliverable | Link |
|---|---|
| Public repository | https://github.com/himanshu748/decisiondebt |
| Live read-only demo | http://decisiondebt.52.202.25.181.sslip.io:8081/ |
| YouTube demo, unlisted | https://youtu.be/_9faaH35xPI |
| Complete local setup | [README: Run locally](../README.md#run-locally) |
| Graph data model | [README: Graph model](../README.md#graph-model) |
| Product Cypher queries | [Actual query templates](../backend/app/graph/queries.py) |
| Why FalkorDB is central | [Load-bearing operations and queries](../README.md#why-falkordb-is-load-bearing) |
| Decision lineage | [Live graph records](http://decisiondebt.52.202.25.181.sslip.io:8081/api/decisions) |
| Agent results and work | [Action Board](http://decisiondebt.52.202.25.181.sslip.io:8081/studio?tab=Action%20Board) |
| CI | [GitHub Actions](https://github.com/himanshu748/decisiondebt/actions/workflows/ci.yml) |

## What the working demonstration establishes

All records belong to fictional Aster Works. The [original corpus receipt](../evidence/query-results/initial-preview.json) and [synthetic snapshot](../evidence/deployment/graph-snapshot-20261016.json) make the dataset reproducible. Native graph queries establish multi-hop impact, ownership, connected projects and document provenance; the browser displays those returned results.

The [genuine provider trace](../evidence/agent-traces/llm-run.json) and [three-case proof](../evidence/agent-traces/llm-proof.json) record an investigation of missing Token Cache ownership, conflicting Session Broker owners, and an unlinked OrionAuth mention. Ambiguous owners stay unassigned. The mention supports a qualified document review with suspected-drift uncertainty. Rejected calls and model corrections remain in the trace.

The [recorded import/retraction receipt](../evidence/query-results/dynamic-import.json) shows the affected set changing from 12 to 13 and back to 12 when one source's dependency support is added and removed. Separate local task approval is shown in the video; the migration itself remains proposed.

The public deployment is read-only and displays the recorded provider run; no visitor can import, invoke a provider, approve tasks or accept a decision. [Public smoke results](../evidence/deployment/public-smoke-20261016.json) record write denials, native search, unchanged graph revision and rate limiting. It uses HTTP on its own port so the existing EmbodiWeave HTTPS service remains untouched; no credentials should be entered there.

The [deployment receipt](../evidence/deployment/receipt-20261016.json) records the URL, source commit, timestamp, credential exclusion, separate graph and real database outage/restart. Removing FalkorDB made preview, company summary and investigation-history reads return 503. Restart restored the same revision, while EmbodiWeave container identities and start times stayed unchanged during that outage test. The [isolation review](../evidence/deployment/isolation-review-20261016.json) distinguishes that proof from the earlier preflight, which observed different EmbodiWeave containers.

[CI test output](../evidence/ci/38896361671/pytest.txt) records 46 passing tests. The [successful run receipt](../evidence/ci/run-38896361671.json) also verifies the frontend build and Chromium UI smoke. New runs are labeled separately; earlier measured evidence remains unchanged.

The video is the original silent, captioned MP4, uploaded unchanged. It is an edited walkthrough of actual browser captures; local write demonstrations are recorded, while the live site permits reads only. [Capture manifest](../evidence/demo-v2/manifest.json) · [Original MP4](../evidence/decisiondebt-demo.mp4). The [quality review](../evidence/youtube/quality-review-20261016.json) records the 1280×960 source and currently available 720p playback; dense dashboard text can be difficult to read.

## AI disclosure and participant completion

Codex generated most of the implementation, tests and styling, as well as fixture data, documentation and automation. Automated checks are not claimed as personal participant verification or technical understanding.

**Participant action required before submitting:** complete the four TODO sections in [README: AI coding disclosure](../README.md#ai-coding-disclosure): “What I designed,” “Decisions I made,” “What I verified myself,” and “What Codex generated.” Those statements must reflect actual contributions and personal verification; no contribution has been invented here.

After completing those fields, submit this entry through the official form by **October 18, 2026, 11:59 PM IST**. This file is the submission text; the form has not been submitted. [Official rules](https://www.wemakedevs.org/hackathons/falkordb/rules).
