# DecisionDebt: working demo and 90-second script

The measured capture is 97.8 seconds, including its final hold. The scripted action sequence is 90 seconds.

The supplied video records the original UI. The redesigned landing is at `/` and the studio is at `/studio`; current screenshots show the redesign. The owner requested UI review before adding the Groq key. A new recording and genuine-provider trace are pending that key and have not been substituted with a mocked run.

Aster Works is fictional. All source data is synthetic. The database and all counts shown in this recording are live local FalkorDB results. The investigation is a **Deterministic rule run**, not an LLM provider call. The delivered MP4 is a recorded local browser session, not a deployment.

## Assets

- `evidence/decisiondebt-demo.mp4`: actual browser capture, 1280x960, with an embedded explanatory caption track, no spoken narration.
- `evidence/decisiondebt-demo.webm`: original native Chromium capture.
- `evidence/demo.srt`: caption/narration script.
- `evidence/test-results/video-metadata.json`: ffprobe verification.
- `evidence/query-results/dynamic-import.json`: actual before, after, and retraction query receipts with event times.
- `evidence/screenshots/`: recorded desktop, 375 px, exact-source and changed-impact states.

The dedicated Browser plugin was unavailable, so capture used installed Playwright and bundled Chromium. This is a real session capture rather than a screenshot animation. It uses the native capture frame rate and 4:3 viewport; it is not claimed as 4K/60 fps.

## Timed narration and actions

| Time | On screen | Suggested spoken script |
|---|---|---|
| 0-10s | Preview proposed migration; service count and live graph | “This is DecisionDebt. Aster Works is a synthetic 60-service company. We are previewing an OrionAuth migration before accepting it. Every number comes from FalkorDB.” |
| 10-15s | Select Session Broker, inspect diamond and ownership | “The graph follows consumer dependencies backward. Session Broker appears once, even though two claim-backed paths connect it to the change. Its primary owners disagree.” |
| 15-22s | Open exact source evidence | “Each relationship has a source quote, immutable revision, exact character span and hash. These are extracted claims, not hand-seeded graph answers.” |
| 22-28s | Native full-text search and drift tiers | “There are three different findings: an old decision citation, a suspected unlinked OrionAuth mention, and overdue document reviews. A mention is not proof of usage.” |
| 28-40s | Run deterministic investigation; expand tool trace | “No model key was supplied, so this is explicitly a deterministic rule run. It investigates both owner claims and missing ownership, reads extra context, and proposes local drafts without inventing an owner.” |
| 40-50s | Action board and explicit approval | “Drafts stay unassigned where evidence is missing or disputed. Human approval is a separate protected operation that changes only the local task.” |
| 50-65s | Import the new dependency ticket; live preview gains External Portal | “Now add one source: External Portal depends on Billing API. The importer verifies that sentence and activates its claim. A fresh Cypher query finds one more affected service.” |
| 65-82s | Inspect new path; update same ticket to remove assertion | “This is a changed graph result. Removing the assertion retracts only this source's support. The service leaves the blast radius, while the migration remains proposed.” |
| 82-90s | Return to owner gap and live paths | “DecisionDebt keeps evidence, uncertainty and human authority visible. The five-hop boundary is disclosed, and a database outage fails explicitly instead of serving invented results.” |

## Reproduce by hand

1. Follow README setup. Import the original corpus, open `http://127.0.0.1:8000/` for the landing page, then select Open studio or visit `/studio`.
2. Verify Proposed status and the live initial service count. Repeated Refresh preview must not change graph revision.
3. Select Session Broker; read its two dependency paths and competing owners. Select Token Cache for the owner gap. Open a proof card to see source text and Claim anchors.
4. Open Evidence, search `OrionAuth`, and inspect all three drift tiers. Expand Query proof to see actual Cypher and parameters.
5. Unlock Local admin using the server's `.env` token. Select deterministic mode and click Run investigation. Inspect the saved trace. A genuine provider run requires the explicit server configuration described in README.
6. Open Action Board. Approve one local task with the confirmation dialog. Do not accept the decision during the main walkthrough.
7. Open Preview and Import new evidence. Use this ticket body:

   `External Portal depends on Billing API for customer identity verification. This synthetic ticket adds the documented consumer connection.`

   The dialog uses ID `ticket-live-portal`. Observe the next live preview gain `svc-external-portal` and inspect its Claim-backed path.
8. Open the import dialog again and choose Use retraction text, then import. The same source ID creates a new revision, retracts the former dependency claim, and restores the original affected-service count.
9. To prove graph necessity, run `python tools/check_lifecycle.py` while the local API is running and no browser interaction is in progress. It stops only `decisiondebt-db`, asserts real 503 responses, starts it again in a `finally` block, and checks persisted state.

The five-hop result intentionally reports `truncated=true`. Do not narrate it as the complete unlimited blast radius. The demo may leave an extra retained Source and source history; that is expected audit data, not an additional initial fixture record.

## Submission gates

The local build, source evidence, tests, screenshots and recorded browser demo are provided. A real configured LLM run, public Git remote, deployment and hackathon portal submission remain distinct external gates. No remote push or portal action was performed.

## Replacement recording after UI review

After saving the Groq key and restarting the local server, run `python tools/run_llm.py`. Verify `evidence/agent-traces/llm-proof.json` has `verified: true` and all three cases pass. Record the new `/studio` investigation trace with its actual provider identity, tool choices, evidence and outcomes. Retain any incomplete attempts honestly. Replace the video and captions only after this real run exists, then rerun `python tools/verify_submission.py` and inspect the exported video. Do not narrate the deterministic recording as a provider run.
