# DecisionDebt implementation decisions

Aster Works and all source records are synthetic. The initial measurements below describe the local build; the separately labeled public deployment and CI receipts are linked in the final entry.

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
| Recorded provider | Owner-approved OpenRouter reuse; `nvidia/nemotron-3-super-120b-a12b:free`; zero-price routing, fallback disabled |
| Documentation | README, DECISIONS, LEARNING, DEMO, measured evidence logs |

## Measurement-backed log

| Date (IST) | Choice | Evidence/test | Reason | Consequence |
|---|---|---|---|---|
| 2026-10-16 | Keep pinned 6.0.2 ARM64 image | `evidence/test-results/db-smoke.json`, `lifecycle.json` | Image actually started on arm64; `g.query`, `g.ro_query`, native full-text and persisted marker passed | No database/version fallback |
| 2026-10-16 | Use full-text DDL | `evidence/test-results/fulltext-compatibility.json`: the specified `CALL db.idx.fulltext.createNodeIndex('Source','title','body')` returned `Received 3 arguments ... expected at most 1`; `CREATE FULLTEXT INDEX FOR (s:Source) ON (s.title,s.body)` succeeded, and `queryNodes` returned the smoke marker | Reproduced incompatibility on this exact tag | Only index creation syntax changes; native full-text search remains mandatory |
| 2026-10-16 | Handle exact `already indexed` initialization error | Second full-suite setup returned `Attribute 'id' is already indexed`; repeated setup passes after ignoring only that response | This image does not silently ignore duplicate index DDL | Setup is repeatable; unrelated schema errors still fail |
| 2026-10-16 | DB-only Docker CLI fallback on this host | Docker 29.9.0 client, server 29.5.2; `docker compose` reports unknown command | Compose plugin absent | `tools/db.sh` runs the same pinned image, loopback port and volume; `compose.yaml` ships for hosts with Compose |
| 2026-10-16 | Keep official Python client 1.8.0 | Locked `requirements.txt`; real DB integration suite | Resolved client works with the image | No alternative graph client or Python topology fallback |
| 2026-10-16 | Deterministic demonstration | `evidence/agent-traces/deterministic.json`: 12 tools, 3 local drafts, abstention | No provider key was supplied for this project | Historical deterministic trace retained; later real proof is recorded separately |
| 2026-10-16 | Bundled Chromium capture | `evidence/test-results/ui-smoke.json`; desktop and 375 px screenshots | Dedicated Browser plugin absent; installed Playwright/Chromium works | Capture is an actual local browser session; no public deployment is claimed |
| 2026-10-16 | Split graph and motion browser bundles | `evidence/test-results/web-build.txt` | Initial single JS bundle exceeded Vite's 500 kB warning | Separate graph, motion and app chunks; identical API behavior |
| 2026-10-16 | Landing at `/`, studio at `/studio` | Owner's explicit route choice; current UI screenshots | The owner requested a separate landing and a Manu Arora inspired dashboard redesign | Original graphite/cobalt composition, larger graph, separate evidence rail, generated concept art and restrained Motion for React transitions |
| 2026-10-16 | Bound structured tool results before recording observed evidence | `backend/tests/unit/test_agent_bounds.py` | Slicing serialized JSON could hide IDs or source context while still counting it as retrieved | Valid JSON under 3000 characters; only delivered references become observed evidence |
| 2026-10-16 | Require three-case coverage and provider identity for real proof | `backend/tests/integrations/test_agent_api.py`, `tools/run_llm.py` | A saved record with mode `llm` alone is insufficient proof | Eight-turn mocked regression covers all cases but is explicitly excluded from genuine provider proof; real OpenRouter run now passes all three cases |

## Runtime receipt

- Host: `arm64`; Docker server: `aarch64`.
- Image digest: `sha256:107455e862a824e45e8e9f5a7fbfdf5e00a08b14e13eae2577c72fd9e3f59ba6`.
- Python: 3.12.13; Node: 22.14.0; npm: 10.9.2.
- Initial import: 94 sources, 315 verified claims/semantic edges, 4 candidates, revision 1.
- Canonical preview: 12 unique services, 12 projects, T1=1, T2=1, T3=3, 1 owner gap, 1 conflict. `truncated=true`: a consumer exists beyond depth 5.
- The independent fixture oracle comparison measured precision=1.0 and recall=1.0 on 315 unique explicit relationships. This measures the synthetic fixture, not general-language extraction accuracy.

## Deliberate limits

The application uses one API worker and an in-process RLock for graph-dependent operations. CLI ingestion runs with the API stopped. This is neither a distributed lock nor snapshot isolation. Source validation precedes writes, but a process crash during a multi-query source batch can require rerunning the importer; no transactional recovery guarantee is claimed. Single-instance local operation is the supported mode.

Public mode is supported in code and tested locally. The user explicitly approved reusing the existing EmbodiWeave OpenRouter key for this private local project and the bounded free-model run. The successful run used eight turns, eleven tools and 51.6 seconds, with $0 reported cost. Groq remains an optional configuration, not the recorded provider. The owner subsequently approved creating the public `himanshu748/decisiondebt` repository and uploading the code, synthetic data, demo, screenshots and verification evidence. The ignored `.env` and credentials remain excluded. At that local-build checkpoint, public deployment and hackathon portal submission had not been performed. The later deployment is recorded below; the event form remains unsubmitted.

## Real-run corrections and outcome

- Hyphenated service IDs caused a native full-text parser error. Resolve service IDs to catalog names and quote safe alphanumeric query tokens; native search errors remain explicit.
- A clipped context could show an unrelated person's name before the matching service. Return the whole matching paragraph while preserving exact match offsets and hashes. The task guard rejected unsupported owner assignments.
- Live service/evidence enums prevent invented references. Progress feedback states the remaining retrieval and outcome work; after evidence retrieval, only propose/abstain tools are offered. Outcome content remains the provider's choice.
- An earlier attempt overran 90 seconds when HTTP keep-alives defeated the read timeout. Wrap the request in a hard total deadline, test cancellation, and retain that attempt as failed evidence.
- Run `run-07fef4a6b0464a57b15fb2e809e30e02`: all three cases passed; 8 turns, 11 tools, 51,618.37 ms, 1,233 source characters, 56,976 aggregate tokens, $0 provider-reported cost. No ambiguous owner was assigned. Three rejected calls and corrections remain in the trace.
- The action board now opens on the latest analysis (three drafts). All history retains 16 tasks across earlier analysis revisions. A separate local approval changed only the new Token Cache task's status. The import/retraction demo then verified 12 → 13 → 12 at graph revisions 14 → 15 → 16; no decision acceptance occurred.
- The new 90-second demo uses actual CUA browser captures assembled in narrative order, with an embedded English caption track. It is labeled as an edited walkthrough, not continuous native recording. Original native video remains archived.

See [investigation findings](evidence/LLM-INVESTIGATION.md), [provider proof](evidence/agent-traces/llm-proof.json) and [capture manifest](evidence/demo-v2/manifest.json).

The outcome-stage tool restriction is applied per provider response: completing coverage during a batch does not revoke tools already offered in that response. The next turn receives the narrowed tool set. Both single-call and batched retrieval variants pass the eight-turn regression.

## Public deployment and CI — 2026-10-16

The owner requested a separate read-only service on the existing Lightsail host. DecisionDebt uses its own API container, FalkorDB 6.0.2 container, `decisiondebt_public` graph, network and volume, with public HTTP on port 8081. This preserves EmbodiWeave's existing HTTPS proxy and ports 80/443. The [deployment receipt](evidence/deployment/receipt-20261016.json) records the source commit, runtime identities, absence of credentials and actual database outage/restart; the before/after EmbodiWeave identities and start times match during that outage test. The [isolation review](evidence/deployment/isolation-review-20261016.json) records that EmbodiWeave changed between the original preflight and the later test; its cause was not established by DecisionDebt checks.

Public mode discards provider/admin credentials and rejects all admin routes and non-read methods before graph or provider work. Per-peer and global token buckets bound public API work. Uvicorn does not trust forwarded headers. The [public smoke receipt](evidence/deployment/public-smoke-20261016.json) records 403 write denials, 429 with `Retry-After`, live native search and unchanged revision. The deployed graph copies the [recorded synthetic snapshot](evidence/deployment/snapshot-export-20261016.json); seeding makes no provider request and refuses to overwrite a populated graph.

CI starts the pinned graph service, builds the frontend, runs the full pytest suite including outage/restart, then runs Chromium smoke against credential-free public mode. The first workflow placed a service-container expression at job scope; moving it to the test step fixed validation. The [successful CI run](evidence/ci/run-38896361671.json) and [test output](evidence/ci/38896361671/pytest.txt) record the actual result. New local, CI and deployed runs have separate evidence paths; historical measurements are preserved.

The owner requested upload of the existing demo. It was uploaded unchanged as an unlisted YouTube video, matching the latest entries on the channel, with its existing English SRT captions and a description containing the repository, live URL and chapters. No narration was added. The [upload receipt](evidence/youtube/upload-20261016.json) records persisted visibility and captioned playback. Participant contribution statements remain TODO fields in README; automated implementation or verification is not attributed to the participant.

## Native 4K narrated demo — 2026-10-16

The owner requested an actual screen recording with close-ups and Deepgram narration, then asked for a cut below three minutes. The new [2:57.4 film](evidence/demo-v3/decisiondebt-demo-4k-under3.mp4) edits continuous native 3840×2160, 30 fps Chromium compositor video; no screenshot is used as video input. A separate disposable synthetic FalkorDB instance supports the filmed approval and import/retraction actions, leaving the original local and deployed graphs unchanged. The UI displays the existing genuine provider trace; recording makes no new LLM call. Automated actions are not participant verification.

The [edit receipt](evidence/demo-v3/under3-edit-receipt.json), [Deepgram speech checks](evidence/demo-v3/speech-verification-under3.json), [verification report](evidence/demo-v3/verification.json), and [YouTube receipt](evidence/demo-v3/youtube-upload-receipt.json) record the actual output. Trailing chapter holds were removed with speech at its original speed. The linked official rules require a working demonstration but do not state a duration limit; the delivered cut nevertheless stays below 180 seconds. YouTube publication is unlisted, matching the earlier entry, with English captions and AI voice disclosure. All historical evidence and the earlier video remain unchanged.

## Participant disclosure — 2026-10-16

The participant confirmed originating the core idea, with AI expanding the specification, and supplying UI direction. The [completed disclosure](README.md#ai-coding-disclosure) credits the recorded route, redesign, deployment and demo requirements as participant product decisions. Codex-generated implementation and automated verification remain attributed to Codex. Personal verification details are not published, and the submission does not treat automated receipts as evidence of participant understanding. The [submission text](docs/submission.md) uses absolute repository links so its references work when pasted into the event form.

## Demo verification rerun — 2026-10-16

The personal-verification section was removed from the submission copy. A separate [Verification section](README.md#verification) records concrete checks run by Codex: live decision impact, original ownership evidence, and public write denials. The [fresh receipt](evidence/demo-recheck-20261016/verification.json) identifies the actor and preserves the measured responses. The event-panel JSON and screenshot were removed at the owner's request; earlier application, provider and video evidence is retained.
