# DecisionDebt: 90-second working demo

[Watch the demo](evidence/decisiondebt-demo.mp4). It shows the redesigned landing at `/`, studio at `/studio`, recorded genuine OpenRouter investigation, explicit local approval, and actual source import/retraction.

This is an **edited walkthrough of actual Codex in-app browser captures**, assembled in narrative order with cursor motion and an embedded default English caption track. It is 1280×960, 30 fps, exactly 90 seconds, silent. It is not a continuous native video or a claim of 4K/60 fps. No UI result was fabricated. Captured revision labels retain their actual values; replay does not execute another model request. The provider ran before the trace was displayed.

Aster Works is fictional. The database and counts come from real local FalkorDB. The model is `nvidia/nemotron-3-super-120b-a12b:free` through OpenRouter. Groq was not used. The user approved private key reuse and the free run. No credentials appear in the recording.

## Evidence

- [Capture manifest](evidence/demo-v2/manifest.json): all 15 actual browser frames, SHA-256, capture times, provider run ID and edit format.
- [Render configuration](evidence/demo-v2/render-config.json): scene, cursor and camera keyframes; paths relative to `evidence/demo-v2`.
- [Captions](evidence/demo.srt) and [ffprobe receipt](evidence/test-results/video-metadata.json).
- [Real provider trace](evidence/agent-traces/llm-run.json), [coverage proof](evidence/agent-traces/llm-proof.json), and [findings](evidence/LLM-INVESTIGATION.md).
- [Live import/retraction receipts](evidence/query-results/dynamic-import.json): 12 → 13 → 12, graph revisions 14 → 15 → 16.
- [Original continuous recording](evidence/archive/original-ui/decisiondebt-demo.mp4) and [native WebM](evidence/archive/original-ui/decisiondebt-demo.webm): original UI, deterministic investigation, 97.8 seconds. Retained as historical evidence, not the new provider demo.

The `browser-video-recording` skill's screenshot-sequence renderer was used because no native recording capability was exposed by the available CUA browser. Frames were captured through CUA. The cursor asset comes from the local macOS system pointer resource; no alternate UI automation or desktop capture was used.

## Timed walkthrough

| Time | Actual browser state | Caption story |
|---|---|---|
| 0–6s | Landing page, live preview card | Fictional company, real FalkorDB results; edited browser walkthrough. |
| 6–13s | Proposed migration, 12 affected services | Preview before human acceptance; the five-hop limit is disclosed. |
| 13–19s | Session Broker selected | Two verified paths and competing primary ownership claims. |
| 19–25s | Exact source dialog | Original context, SHA-256, claim IDs and character spans. |
| 25–31s | Token Cache selected | No verified primary owner; dependency evidence does not identify an owner. |
| 31–36s | Evidence view | Three distinct drift tiers; native full-text search. |
| 36–42s | Full `doc-002` context | The unlinked OrionAuth mention supports review, not a provider dependency. |
| 42–55s | Completed real provider trace | Eight turns, eleven tools, 51.6 seconds, $0 reported cost. All three cases pass; rejected calls and corrections remain visible. |
| 55–63s | Latest analysis action board | Three source-backed drafts, unresolved owners, qualified suspected drift. |
| 63–70s | Separate approval dialog and result | Approves the Token Cache task locally; no owner assignment or decision acceptance. |
| 70–74s | Import dialog | Add the explicit External Portal → Billing API sentence. |
| 74–81s | Live preview | A fresh query returns 13 affected services. |
| 81–85s | Same source, retraction text | Remove only this source's dependency support. |
| 85–90s | Recomputed preview | Returns to 12; retained source history and proposed decision. |

## Reproduce by hand

1. Follow README setup. Open `http://127.0.0.1:8000/`, select Open studio, or visit `/studio`.
2. Verify Proposed status and the initial 12-service result. Refresh does not change graph revision.
3. Select Session Broker and inspect both primary claims; select Token Cache and inspect the owner gap. Open a proof card to verify source context and anchors.
4. Open Evidence, search `OrionAuth`, inspect all three tiers and expand Query proof. Inspect the recorded provider trace and its three coverage cards.
5. To execute a new real run, configure a private provider key as described in README, unlock Local admin and choose Configured LLM. `python tools/run_llm.py` is the equivalent protected local API call. Do not describe a deterministic selection as a provider run.
6. Open Action Board. Latest analysis shows the new drafts; All history shows earlier attempts. Approve one local task through its separate confirmation dialog. Keep the migration proposed.
7. Open Import source. The default `ticket-live-portal` body is:

   `External Portal depends on Billing API for customer identity verification. This synthetic ticket adds the documented consumer connection.`

   Import and observe 13 affected services. Select External Portal to inspect its newly anchored path.
8. Open Import source again, choose Use retraction text and import. The same source gets a new immutable revision, its previous support retracts, and the affected count returns to 12.
9. Run `DD_TEST_LIFECYCLE=1 pytest -q` with the local API running and no browser mutations in progress. It stops only `decisiondebt-db`, verifies 503, restarts it in a `finally` block and verifies persisted state.

The canonical preview is truncated beyond five hops. The used demo graph retains 95 sources and source revision history. Public deployment, remote push and portal submission were not performed.
