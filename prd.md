# DecisionDebt
## Final Product Requirements Document (PRD)

**Version:** 2.0, final build brief  
**Date:** 15 October 2026 (IST)  
**Hackathon:** WeMakeDevs x FalkorDB Graph Hacks, Track 03: Company Brain  
**Build window:** 15-18 October 2026; submission closes 18 October at 23:59 IST  
**Internal freeze:** 18 October at 20:00 IST  
**Companion:** [`spec.md`](./spec.md), [`CODEX_INITIAL_PROMPT.md`](./CODEX_INITIAL_PROMPT.md)  
**Tagline:** *Your company remembers what it decided. DecisionDebt remembers what those decisions broke.*

> **Build directive:** A new decision should produce an evidence-backed preview of which services, projects, documents and people are affected, even when the relevant dependencies are scattered across raw documentation, tickets and conversations. FalkorDB must be required to reach the answer, not just render it.

## 1. The problem and product

An engineering lead proposes replacing an authentication provider. The knowledge is fragmented: a runbook names a gateway, a ticket describes a downstream dependency, chat reveals competing owners, and an aging document mentions the old provider without citing the original decision. Ordinary document search finds mentions. DecisionDebt finds **connected consequences**, shows **why they are connected**, and turns unresolved impact into **reviewable action**.

The product runs on a **fictional 60-service company, Aster Works**, whose raw Markdown files, ticket JSON and chat JSONL are imported by a real extraction pipeline. Its source documents, claims, ownership and decision lineage live in FalkorDB. A user can preview the impact of a *proposed* decision before accepting it. A bounded agent chooses which uncertain evidence to investigate, then proposes remediations with explicit evidence and abstentions.

**Not** a chatbot that happens to draw a graph. **Not** a hand-maintained `relationships.json` masquerading as ingestion. **Not** an LLM allowed to invent services, dependencies, owners or paths.

## 2. Users and jobs

| User | Core question | Required experience |
|---|---|---|
| Engineering lead | "If we retire OrionAuth, what breaks?" | A pre-approval impact preview with depth, severity, owners and paths. |
| Service owner | "Why am I assigned this?" | Source excerpt, originating document/ticket/chat, claim and dependency path. |
| Technical program manager | "Who still needs to act?" | An approval-gated action board with unresolved and disputed ownership. |
| Reviewer/judge | "Did FalkorDB actually discover that?" | Live Cypher, query parameters, graph revision, extracted source anchors and outage behavior. |

## 3. Core differentiator and scope

**The one excellent story:**

1. Import messy company documents, tickets and chat messages. Show entity and relationship extraction with evidence-backed claims and a count of accepted vs uncertain claims.
2. Open the full company map (60 services) and the focused OrionAuth dependency subgraph. The same graph is used for reasoning and presentation.
3. Preview decision `dec-auth-002`, "Replace OrionAuth with NovaID", while it is still proposed. The accepted decision `dec-auth-001`, "Retain OrionAuth through Q4", remains unchanged.
4. Follow dependencies backwards from `svc-auth-gateway`, deduplicate the diamond, handle a cycle, identify linked projects and detect three kinds of stale knowledge.
5. The agent investigates three deliberately ambiguous cases: an **unowned service**, a **dual-primary-owner conflict**, and a **document mentioning OrionAuth without formally referencing the decision**. It retrieves additional sources before proposing or abstaining.
6. Open a remediation task: see the affected service, priority, proposed owner or unresolved status, supporting source excerpts, exact graph path and the analysis revision. Human approval changes only the local task state.
7. Import a new ticket saying an initially unconnected service depends on an affected service. Re-run the preview. A new affected service appears because the extracted edge entered FalkorDB, not because the UI changed a fixture counter.

A successful 90-second demo spends most of its time on steps 3-7. The 60-service network exists to supply real traversal and search work, not to fill the screen with nodes.

## 4. P0 requirements (must ship)

| ID | Capability | Definition of success |
|---|---|---|
| P0-01 | Source-first ingestion | Parse raw `*.md`, ticket `*.json` and chat `*.jsonl`, resolve entities and create **only source-anchored** graph claims. No operational relationship imported directly from a truth file. |
| P0-02 | Non-toy company | Reproducible fixture: exactly **60 services**, **8 teams**, **24 people**, **12 projects**, and **at least 90 raw source records** across all 3 types. At least **100 source-supported semantic relationships**, plus cycle and diamond cases. |
| P0-03 | Real graph reasoning | FalkorDB stores source-backed dependencies, decision lineage and ownership; Cypher returns affected services through depth 5, service paths and claim IDs. No parallel Python impact graph. |
| P0-04 | Preview before approval | `dec-auth-002` can be previewed in `proposed` state, without changing the accepted decision or graph revision. Approving it is a separate admin-only action. |
| P0-05 | Three-tier drift | Tier 1: explicit outdated decision reference. Tier 2: unlinked full-text mention of obsolete terminology, requiring text verification. Tier 3: overdue review of documentation associated with an affected service. Each tier is visibly labeled, not collapsed into "confirmed stale". |
| P0-06 | Honest extraction | Every accepted claim has a source ID, source hash, exact substring span into the original/parsed source field, relation, method and claim status. Hedge/negation language cannot activate facts. Ambiguous or contradicting extractions remain candidates, not active facts. |
| P0-07 | Agent that investigates | A real configured LLM selects between bounded read tools and task/abstention tools, makes at least one different tool choice for each of the three ambiguous scenarios, and produces a visible trace. A non-LLM run is clearly labeled deterministic mode. |
| P0-08 | Human-controlled actions | Task proposals are source-backed, deduplicated and stored; no external ticket creation, emails or changes to services. Only an authenticated local operator can approve them. |
| P0-09 | Interactive studio | One responsive React app with Decision Preview, Evidence Drawer/Graph, and Action Board. Nodes and metrics come from backend graph queries. |
| P0-10 | Reproducibility | One-command DB startup, documented local app commands, idempotent import, integration tests with real FalkorDB, `README`, `DECISIONS.md`, `LEARNING.md`, `DEMO.md`, and a recorded demo. |
| P0-11 | Failure truthfulness | If the DB is unavailable, impact, drift and agent requests fail explicitly with `503 GRAPH_UNAVAILABLE`. If no LLM is configured, do not claim an LLM run. |

**P0 measurement targets, not completed results:** After import, at least 95% of unambiguous, explicitly stated dependency relations in the held-out fixture oracle are recovered; all 3 ambiguity cases are presented; at least 1 decision, 2+ projects and 3 drift tiers appear in the canonical preview. Record actual import precision/recall and timings instead of assuming targets passed. Unsupported edges count as false positives even when the UI looks convincing.

## 5. The canonical Aster Works company

- Fictional products: **OrionAuth** (legacy identity provider), **NovaID** (replacement), and **Aster Works** (company). There is no claim that a real vendor has issued an advisory.
- Fixed main decision IDs: `dec-auth-001` (accepted historical), `dec-auth-002` (proposed replacement), and `dec-auth-003` (unrelated accepted control case).
- Fixed root service: `svc-auth-gateway`. `consumer -[:DEPENDS_ON]-> provider`, so reverse traversal finds consumers of the changed root.
- Company geography: 6 product domains x 10 services, 8 teams, 24 people, 12 projects. Naming, source text, owners and edges are deterministically generated from seed `42`, but the **importer sees only the generated raw documents and a permitted entity-alias catalog**, never the oracle edges.
- At least 90 source records: 40 Markdown pages, 30 ticket JSON records, 24 chat JSONL messages as initial targets (94 total). Counts are enforced by a fixture test. Every document includes stable source ID, authored timestamp and, if applicable, last-reviewed timestamp.
- Required graph shape: one dependency diamond, one two-node dependency cycle, a two-hop downstream impact, one service with no verified owner, one with two conflicting primary owner claims, at least one project on an affected path, and at least one disconnected service that joins the affected subgraph only after a new source is imported.
- Deliberate discovery cases: a page explicitly referencing `dec-auth-001`; a different page casually mentioning `OrionAuth` without decision ID; an old document describing an affected service but lacking a fresh review; a chat message contradicting the formal ownership ticket.

**Critical honesty rule:** The generator may know the ground truth, but the runtime must not read a truth/expected-edges file. Evaluation files are for tests only. Do not hand-seed `DEPENDS_ON`, `OWNS`, `USES`, `REFERENCES` or `CHANGES` semantic edges from generated truth.

## 6. Information architecture and experience

### Main screen: Decision Preview

- Landing headline: "Know what a decision breaks before you make it."
- One concrete action: **Preview OrionAuth migration**. Status must show **Proposed**, not Approved.
- At-a-glance metrics derived from live responses: affected services, depth, projects, source-backed drifts by tier, missing/conflicting owners, and number of proposed actions.
- Main canvas: a clean, interactive dependency subgraph with root highlight, path emphasis on selection, depth filters and an optional full-company view. Never render a fake path.
- Evidence rail: for each affected item, show exact query name/Cypher, source snippet, original document title/type, extraction method, claim ID and confidence/verification state.

### Evidence / Investigation

- Source ingestion summary by type and extraction method; accepted and candidate claims are separate.
- Search field uses **native FalkorDB full-text query** with an alias-based mention review.
- Three drift tiers are separate and explained in plain language. A possible mention is not asserted to be a confirmed implementation dependency.
- Agent trace panel lists model, tool calls, arguments, returned evidence IDs, decisions and abstentions. A scripted demonstration must visibly say **Recorded** or **Deterministic**, never **Live LLM**.

### Action Board

- Tasks grouped by P0, P1 and P2, with `proposed` / `approved` / `rejected` states.
- Unknown owner remains **Unassigned**, conflicting primary owners remain **Needs owner resolution**.
- Approval changes the task record in the local graph; it must not silently rewrite decisions, edit documents or call external systems.

### Visual bar

Desktop-first premium interface that also works at 375 px, keyboard accessible, high contrast, loading/empty/error states. Prefer a focused subgraph over a 60-node hairball. Use brand language consistently; no fake telemetry, simulated labels hidden in tooltips, or spurious AI certainty.

## 7. Decision/drift and remediation semantics

- **Preview:** Use `proposed_supersedes_id` to compare the proposed decision with the accepted one. Do not write a `SUPERSEDES` edge until approval. Preview is read-only and may be repeated without changing the graph revision.
- **Blast radius:** Start with every verified `CHANGES` root. Include the root at depth 0 and all consumers reachable by reversed `DEPENDS_ON` paths of length 1-5. Deduplicate nodes even through diamonds and cycles; retain up to 3 supporting paths per affected service.
- **Drift T1:** A source explicitly `REFERENCES` the superseded decision ID. This proves the citation is stale, not necessarily that the entire technical content is false.
- **Drift T2:** A Source node matches the legacy term through the FalkorDB full-text index, and the original text contains an exact verified alias boundary, but the source does not explicitly reference the old decision. Label **Suspect mention / investigate**.
- **Drift T3:** A document about an affected service has `last_reviewed_at` at least 90 days before the analysis `as_of` time and before the proposed change. Label **Review overdue**, not **definitely wrong**.
- **Severity:** Transparent deterministic scores based on graph depth, service criticality (1-3), ownership gaps/conflicts and drift tier. Exact formula and sort order live in `spec.md` and must be implemented identically in code/tests.
- **Agent autonomy:** The trusted tool layer establishes possible impacts; the LLM chooses what to inspect next, which ambiguity is worth deeper investigation, which source-backed remediation to propose, and when to abstain. The agent cannot invent new graph facts or self-approve actions.

## 8. Evaluation and demo acceptance

A judge can reproduce the following, locally, without private data or paid services:

1. Start DB, import the corpus, and inspect at least 60 services / 90 sources / 100 supported relationships. Display measured counts.
2. Disable FalkorDB and observe `503` for impact and agent endpoints; turn it back on and recover.
3. Query the fixed canonical case; verify a depth-2 service, a diamond with one deduplicated affected record and multiple paths, and finite traversal through a cycle.
4. Preview a proposed decision, then verify accepted statuses and graph revision are unchanged.
5. Observe T1, T2 and T3 drift with distinct evidence and certainty badges; full-text results are rechecked against exact source text.
6. Run an actual LLM agent with an explicitly named configured model and view its bounded trace, or disclose a deterministic-only limitation if credentials are unavailable.
7. See the agent investigate unowned, dual-owned and unlinked-document cases without fabricated owner assignment.
8. Import the new synthetic ticket; prove an additional service becomes reachable and a re-run changes impact findings.
9. Open and approve one **local** task through an admin-only route; confirm the task changes, not the underlying source facts.
10. Read `LEARNING.md` and see a correct explanation of the graph model, queries, source evidence, and tradeoffs.

**Out-of-scope:** Connecting real Slack, Jira or Gmail; production SSO/RBAC; embeddings/vector DB; continuous background sync; PR/code auto-remediation; unbounded agent tool calls; multi-tenant SaaS; automatic approval; graph claims assembled from a fixture truth JSON; claims of actual enterprise deployment.

## 9. Scope locks and time budget

| Time (IST) | Ship target | Failing this? |
|---|---|---|
| Thu 15 Oct, 19:00-23:30 | Repository scaffold, Docker smoke on Apple Silicon, source generator, parser, FalkorDB schema, first Cypher assertions. | Cut visual flourish, not extraction or graph. |
| Fri 16 Oct, 09:00-19:00 | Complete source-backed extraction, 60-service corpus, graph update/retraction, dependency paths, oracle tests. | Reduce decorative source variety; retain all 3 types and 60 services. |
| Sat 17 Oct, 09:00-18:00 | Proposed-decision preview, 3-tier drift, scoring, ambiguous-owner paths, agent + trace. | Keep only one provider, one bounded agent flow. |
| Sat 17 Oct, 18:00 to Sun 18 Oct, 15:00 | Vite studio, evidence drawer, action board, responsive fixes and recorded real run. | Skip vector search, auth providers, animations, public admin deployment. |
| Sun 18 Oct, 15:00-20:00 | Integration tests, graph outage test, README, demo film, screenshots, explanation, submission packaging. | Prioritize working demo + clear local runbook. |
| Sun 18 Oct, 20:00-23:59 | Submission buffer. | Freeze features. |

The time boxes are planning allocations, not evidence of elapsed work or a guarantee. Work on **DecisionDebt** separately from **EmbodiWeave**; the latter is already substantially built and should receive only final submission checks.

**Cut order:** (1) external integrations, (2) vector search/embeddings, (3) graph animation/marketing effects, (4) public admin, (5) cross-platform Docker builds, (6) extra agent providers, (7) elaborate owner inference. Never cut evidence provenance, source ingestion, native graph traversal, proposed preview, mandatory drift tiers or the final demo.

## 10. Deliverables and submission

- A public **DecisionDebt** repository with `prd.md`, `spec.md`, README, source generator, versioned synthetic sample corpus, setup instructions, schema diagram and key Cypher.
- A working app plus proof screenshots from **real backend responses**, not mocked counts.
- A 60-120 second project video showing actual import, proposed preview, evidence query, investigation and a changed result after new evidence arrives.
- `DECISIONS.md` with implementation defaults and only measurement-driven revisions; `LEARNING.md` explaining technology; `DEMO.md` with exact walkthrough.
- AI assistant disclosure listing Codex (and any other helpers), specific roles, and real participant verification.
- Track declared **Company Brain**. The user confirmed multiple independent project submissions are permitted; submit DecisionDebt separately from EmbodiWeave and follow the event's one-team-per-participant rule.

**Official event rules:** https://www.wemakedevs.org/hackathons/falkordb/rules  
**Company Brain brief:** https://www.wemakedevs.org/hackathons/falkordb  
**Technical API references:** https://github.com/FalkorDB/falkordb-py and https://docs.falkordb.com/cypher/indexing/fulltext-index

Implementation details and acceptance tests are normative in [`spec.md`](./spec.md). If the documents disagree, the spec controls program behavior, and this PRD controls user-visible goals.
