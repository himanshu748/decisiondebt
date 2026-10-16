# Local workflow verification

The flow under test was: local proposed preview, graph-node selection, source evidence, native alias search, drift tiers, deterministic investigation, local task approval, new-ticket import and source-specific retraction.

Current UI environment: landing at `http://127.0.0.1:8000/`, studio at `/studio`, tested through the Codex in-app browser with `cua_repl`. Viewports were 1440x1100 and 375x900. Normal motion was visually inspected after settling; JavaScript and CSS reduced-motion guards were inspected without changing the OS preference. The original video used bundled Chromium via Playwright and the original UI.

| Check | Result | Evidence |
|---|---|---|
| Page identity and meaningful render | Pass | `test-results/ui-smoke.json`, desktop screenshot |
| Framework error overlay | Absent | Rendered screenshots and successful target interactions |
| Console health | Pass, no console/page errors | `test-results/ui-smoke.json` |
| Displayed service count matches API | Pass at desktop and 375 px | `test-results/ui-smoke.json` |
| Horizontal page overflow | Absent at both widths | `test-results/ui-smoke.json` |
| Node click reveals actual claim path | Pass | `screenshots/source-evidence.png` |
| Search and all three drift tiers | Pass | `screenshots/desktop-evidence.png` |
| Local action board | Pass | `screenshots/action-board.png`, native recording |
| Import/retraction changes live result | 12 to 13 to 12 | `query-results/dynamic-import.json` |
| Real DB outage and persistence | Both API operations return 503, restart retains state | `test-results/lifecycle.json` |
| Full pytest suite | 38 passed, one dependency deprecation warning | `test-results/pytest.txt` |
| Separate landing/studio routes | Both return 200; CTA reaches studio | `test-results/ui-api-check.json`, landing screenshots |
| Original generated artwork | Loaded at both widths, 1536 px source | `test-results/ui-smoke.json`, `../web/public/assets/ASSETS.md` |
| Conflicting primary claims | Both proof cards visible together; owner stays unresolved | `screenshots/desktop-preview.png` |
| Mobile service selection | Picker updates selected service and evidence | `screenshots/mobile-preview.png` |
| Static production build | Pass | `test-results/web-build.txt` |

The retained recording shows the original UI served from FastAPI; current screenshots show the redesign. A replacement recording is pending a genuine Groq run after the owner reviews the UI. It is 1280x960 H.264, native capture 25 fps, 97.8 seconds, with an embedded English caption track and no spoken narration. `test-results/video-metadata.json` is the ffprobe receipt. A mid-video thumbnail was visually inspected.

Remaining risks: no genuine configured-provider trace, no Safari/Firefox/hardware testing, no public deployment, and no portal submission. Extraction accuracy is measured on synthetic explicit statements. Optional reviewer confirmation and model-assisted extraction are not implemented. Missing-provider and graph-outage behavior remain explicit errors.

Screenshots are recorded evidence, not a replacement for live graph queries. After the demo, the graph retains the new source and its retracted revision history; the affected set returns to 12 services. Later graph revisions can change screenshots and live counts.

The provider proof gate now requires response IDs/model identity, successful status, all three ambiguity cases and the configured run limits. The new eight-turn regression uses mocked model choices and explicitly fails the genuine-provider proof gate. `agent-traces/provider-readiness.json` records the missing key without retaining credentials. No provider request has been made.
