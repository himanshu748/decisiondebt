# Local workflow verification

The verified flow is the redesigned landing (`/`) and studio (`/studio`), proposed preview, graph selection, exact-source proof, native alias search and three drift tiers, a genuine bounded provider run covering all three ambiguities, separate local task approval, and source import/retraction.

The real run used OpenRouter with `nvidia/nemotron-3-super-120b-a12b:free`: **8 turns, 11 tools, 51.6 seconds, $0 reported cost**. All three cases pass the provider proof gate. Missing and conflicting owners remain blank; the unlinked mention creates a qualified review with suspected-drift uncertainty. Rejected calls and corrections are retained. See [findings](LLM-INVESTIGATION.md), [trace](agent-traces/llm-run.json) and [machine proof](agent-traces/llm-proof.json).

| Check | Result | Evidence |
|---|---|---|
| Landing and studio routes | 200; CTA reaches studio | `test-results/ui-api-check.json`, landing screenshots |
| Meaningful render and console | Pass, no console errors | `test-results/ui-smoke.json` |
| Displayed service count matches API | 12 at desktop and mobile | `test-results/ui-smoke.json` |
| Horizontal page overflow | Absent at 1440, 375 and 360 px | `test-results/ui-smoke.json` |
| Conflicting claims visible together | Both primary proofs; unresolved owner | `screenshots/desktop-preview.png` |
| Mobile service selection | Picker updates evidence | `screenshots/mobile-preview.png` |
| Source proof | Actual source, SHA-256, exact spans | `demo-v2/frames/04-source-proof.png` |
| Three distinct drift tiers | All render; native search verifies exact matches | `demo-v2/frames/06-evidence.png` |
| Genuine provider coverage | All three cases pass, eight real response identities | `agent-traces/llm-proof.json` |
| Latest action board | 3 current actions; all history retains 16 tasks | `screenshots/action-board.png` |
| Mobile action board | 3 cards, no horizontal overflow at 375 px | `screenshots/mobile-actions.png`, UI receipt |
| Separate local task approval | Token Cache approved, owner blank; migration proposed | `demo-v2/frames/10-approval-dialog.png`, `11-approved.png` |
| Live import and retraction | 12 → 13 → 12; revisions 14 → 15 → 16 | `query-results/dynamic-import.json` |
| Database outage and persistence | Both protected agent call and preview return 503; restart retains state | `test-results/lifecycle.json` |
| Full pytest suite | **42 passed**, one dependency deprecation warning | `test-results/pytest.txt` |
| Production build | Pass | `test-results/web-build.txt` |
| Original generated concept artwork | Loaded at desktop and mobile, 1536 px source | `test-results/ui-smoke.json`, `../web/public/assets/ASSETS.md` |
| Video encoding and full decode | H.264 1280×960, 30 fps, 90s, English subtitle track; decode has no errors | `test-results/video-metadata.json`, `video-decode.txt` |

Browser interactions used Codex in-app browser through `cua_repl`. Normal motion was visually inspected after settling. Motion for React and CSS reduced-motion guards were inspected; the OS preference was not changed. Temporary viewport overrides were reset. Tests cover Chromium, not Safari/Firefox or physical devices.

The new demo is an edited walkthrough of 15 actual browser captures, with cursor/camera motion and captions, not a continuous native recording. Its manifest retains frame hashes, capture times and the genuine provider run ID. Revision values preserve each captured state; the narrative order is edited. The original 97.8-second continuous recording is archived and explicitly labeled original UI/deterministic. A thumbnail from the new exported video was visually inspected.

All model evidence is synthetic. The private provider key is server-only in the ignored `.env`. Earlier incomplete attempts, including the transport deadline overrun and full-text parser failure, remain labeled as failures. The source import is retracted in the final live preview, with history retained. No decision acceptance, remote push, public deployment or portal submission occurred. Single-worker local operation and explicit extraction rules remain the supported scope.
