# DecisionDebt implementation decisions

Aster Works and all source records are synthetic. Measurements below describe this machine and this repository, not a hosted deployment.

## Frozen choices

| Choice | Implemented contract |
|---|---|
| Runtime | Python 3.12, Node 22 LTS, npm, Docker Compose configuration |
| Database | `falkordb/falkordb:6.0.2`, graph `decisiondebt`, loopback port 16380, `/data`, AOF |
| Frontend | Vite, React, TypeScript, Tailwind, `@xyflow/react`; Vite `/api` proxy to 8000 |
| Serving | FastAPI serves `web/dist`; public mode blocks writes |
| Fixture | Seed 42; 60 services, 8 teams, 24 people, 12 projects, 40 docs, 30 tickets, 24 chats |
| Ingestion | Raw source, parsed entities and phrases, exact-span verified Claim, semantic edge |
| Graph | Service, Person, Team, Project, Decision, Source, SourceRevision, Claim, Task, AgentRun, Meta, ApprovalEvent |
| Dependency | Consumer `DEPENDS_ON` provider; reverse impact, max 5 hops |
| Preview | Proposed `dec-auth-002` compares with accepted `dec-auth-001`; no automatic SUPERSEDES |
| Drift | T1 explicit old citation; T2 native full-text with exact check; T3 linked doc reviewed at least 90 days ago and before proposal |
| Priority | `clamp(60-10*depth+5*criticality+12*unowned+8*conflict+6*T1+4*T2+2*T3,0,100)`; P0 >=70, P1 >=45 |
| Agent | Eight allowlisted tools; 8 model turns, 12 calls, 90 seconds; no external business writes |
| Provider example | Groq-compatible endpoint, `openai/gpt-oss-120b`; requires supplied key and explicit LLM mode |
| Documentation | README, DECISIONS, LEARNING, DEMO, measured evidence logs |

## Measurement-backed log

| Date (IST) | Choice | Evidence/test | Reason | Consequence |
|---|---|---|---|---|
| 2026-10-16 | Keep pinned 6.0.2 ARM64 image | `evidence/test-results/db-smoke.json`, `lifecycle.json` | Image actually started on arm64; `g.query`, `g.ro_query`, native full-text and persisted marker passed | No database/version fallback |
| 2026-10-16 | Use full-text DDL | `evidence/test-results/fulltext-compatibility.json`: the specified `CALL db.idx.fulltext.createNodeIndex('Source','title','body')` returned `Received 3 arguments ... expected at most 1`; `CREATE FULLTEXT INDEX FOR (s:Source) ON (s.title,s.body)` succeeded, and `queryNodes` returned the smoke marker | Reproduced incompatibility on this exact tag | Only index creation syntax changes; native full-text search remains mandatory |
| 2026-10-16 | Handle exact `already indexed` initialization error | Second full-suite setup returned `Attribute 'id' is already indexed`; repeated setup passes after ignoring only that response | This image does not silently ignore duplicate index DDL | Setup is repeatable; unrelated schema errors still fail |
| 2026-10-16 | DB-only Docker CLI fallback on this host | Docker 29.9.0 client, server 29.5.2; `docker compose` reports unknown command | Compose plugin absent | `tools/db.sh` runs the same pinned image, loopback port and volume; `compose.yaml` ships for hosts with Compose |
| 2026-10-16 | Keep official Python client 1.8.0 | Locked `requirements.txt`; real DB integration suite | Resolved client works with the image | No alternative graph client or Python topology fallback |
| 2026-10-16 | Deterministic demonstration | `evidence/agent-traces/deterministic.json`: 12 tools, 3 local drafts, abstention | No provider key was supplied for this project | Genuine LLM proof remains unverified; mocked tests are not provider evidence |
| 2026-10-16 | Bundled Chromium capture | `evidence/test-results/ui-smoke.json`; desktop and 375 px screenshots | Dedicated Browser plugin absent; installed Playwright/Chromium works | Capture is an actual local browser session; no public deployment is claimed |
| 2026-10-16 | Split graph and motion browser bundles | `evidence/test-results/web-build.txt` | Initial single JS bundle exceeded Vite's 500 kB warning | Separate graph, motion and app chunks; identical API behavior |
| 2026-10-16 | Landing at `/`, studio at `/studio` | Owner's explicit route choice; current UI screenshots | The owner requested a separate landing and a Manu Arora inspired dashboard redesign | Original graphite/cobalt composition, larger graph, separate evidence rail, generated concept art and restrained Motion for React transitions |
| 2026-10-16 | Bound structured tool results before recording observed evidence | `backend/tests/unit/test_agent_bounds.py` | Slicing serialized JSON could hide IDs or source context while still counting it as retrieved | Valid JSON under 3000 characters; only delivered references become observed evidence |
| 2026-10-16 | Require three-case coverage and provider identity for real proof | `backend/tests/integrations/test_agent_api.py`, `tools/run_llm.py` | A saved record with mode `llm` alone is insufficient proof | Eight-turn mocked regression covers all cases but is explicitly excluded from genuine provider proof; actual Groq key remains pending UI review |

## Runtime receipt

- Host: `arm64`; Docker server: `aarch64`.
- Image digest: `sha256:107455e862a824e45e8e9f5a7fbfdf5e00a08b14e13eae2577c72fd9e3f59ba6`.
- Python: 3.12.13; Node: 22.14.0; npm: 10.9.2.
- Initial import: 94 sources, 315 verified claims/semantic edges, 4 candidates, revision 1.
- Canonical preview: 12 unique services, 12 projects, T1=1, T2=1, T3=3, 1 owner gap, 1 conflict. `truncated=true`: a consumer exists beyond depth 5.
- The independent fixture oracle comparison measured precision=1.0 and recall=1.0 on 315 unique explicit relationships. This measures the synthetic fixture, not general-language extraction accuracy.

## Deliberate limits

The application uses one API worker and an in-process RLock for graph-dependent operations. CLI ingestion runs with the API stopped. This is neither a distributed lock nor snapshot isolation. Source validation precedes writes, but a process crash during a multi-query source batch can require rerunning the importer; no transactional recovery guarantee is claimed. Single-instance local operation is the supported mode.

Public mode is supported in code and tested locally. The user authorized a bounded real Groq investigation and will supply the key after reviewing the redesigned UI. No provider call has been performed. Publishing, remote Git push, and hackathon portal submission have not been authorized or performed.
