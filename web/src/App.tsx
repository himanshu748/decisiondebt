import { useCallback, useEffect, useRef, useState } from "react";
import { motion, useReducedMotion } from "motion/react";
import {
  Activity,
  ArrowRight,
  ArrowUpRight,
  BookOpen,
  Check,
  ChevronRight,
  Database,
  FileText,
  GitBranch,
  Layers3,
  LayoutDashboard,
  LockKeyhole,
  Network,
  Play,
  Plus,
  RefreshCw,
  Search,
  ShieldCheck,
  Sparkles,
  TriangleAlert,
  X,
} from "lucide-react";
import { api } from "./api";
import type {
  Claim,
  Drift,
  Impact,
  Preview,
  Run,
  Source,
  Summary,
  Task,
  Topology,
} from "./types";
import ImpactGraph from "./components/ImpactGraph";
import EvidenceDrawer from "./components/EvidenceDrawer";
import InvestigationTrace from "./components/InvestigationTrace";
import ActionBoard from "./components/ActionBoard";
import "./studio.css";
import StudioView from "./components/StudioView";
const decision = "dec-auth-002";
function badge(d: Drift) {
  return d.tier === 1
    ? "Stale reference"
    : d.tier === 2
      ? "Suspect mention"
      : "Review overdue";
}
export default function App() {
  const reduced = useReducedMotion();
  const [tab, setTab] = useState(
    ["Preview", "Evidence", "Action Board"].includes(
      new URLSearchParams(window.location.search).get("tab") || "",
    )
      ? new URLSearchParams(window.location.search).get("tab")!
      : "Preview",
  );
  const [preview, setPreview] = useState<Preview | null>(null);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [run, setRun] = useState<Run | null>(null);
  const [selected, setSelected] = useState("svc-session-broker");
  const [proofs, setProofs] = useState<Claim[]>([]);
  const [source, setSource] = useState<Source | null>(null);
  const [loading, setLoading] = useState(true);
  const [proofLoading, setProofLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [depth, setDepth] = useState(3);
  const [full, setFull] = useState<Topology | null>(null);
  const [token, setToken] = useState("");
  const [tokenDraft, setTokenDraft] = useState("");
  const [adminDialog, setAdminDialog] = useState(false);
  const [importDialog, setImportDialog] = useState(false);
  const [confirm, setConfirm] = useState<{ kind: string; id: string } | null>(
    null,
  );
  const [mode, setMode] = useState("local-admin");
  const [agentMode, setAgentMode] = useState("deterministic");
  const [query, setQuery] = useState("OrionAuth");
  const [results, setResults] = useState<
    | { source_id: string; title: string; context: string; ft_score: number }[]
    | null
  >(null);
  const [candidates, setCandidates] = useState<Claim[]>([]);
  const [importBody, setImportBody] = useState(
    "External Portal depends on Billing API for customer identity verification. This synthetic ticket adds the documented consumer connection.",
  );
  const sourceClose = useRef<HTMLButtonElement>(null);
  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [p, s, t, h] = await Promise.all([
        api<Preview>("/decisions/" + decision + "/preview"),
        api<Summary>("/company/summary"),
        api<{ tasks: Task[] }>("/tasks"),
        api<{ mode: string; provider_configured: boolean }>("/health"),
      ]);
      setPreview(p);
      setSummary(s);
      setTasks(t.tasks);
      setMode(h.mode);
      if (h.provider_configured) setAgentMode("llm");
      const [rs, cs] = await Promise.all([
        api<{ runs: { id: string }[] }>("/agent/runs"),
        api<{ claims: Claim[] }>("/claims?status=candidate"),
      ]);
      setCandidates(cs.claims);
      if (rs.runs[0]) setRun(await api<Run>("/agent/runs/" + rs.runs[0].id));
    } catch (e) {
      setError(String((e as Error).message));
      setPreview(null);
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => {
    document.title = "DecisionDebt | Decision studio";
    void load();
  }, [load]);
  const item: Impact | undefined = preview?.impacts.find(
    (i) => i.service_id === selected,
  );
  useEffect(() => {
    let active = true;
    setProofs([]);
    if (!item) return;
    setProofLoading(true);
    const ids = [
      ...new Set([
        ...item.ownership_claims.map((o) => o.claim_id),
        ...(item.path_claim_ids[0] || []),
        ...item.evidence_ids,
      ]),
    ].slice(0, 3);
    Promise.all(ids.map((id) => api<Claim>("/claims/" + id)))
      .then((cs) => {
        if (active) setProofs(cs);
      })
      .catch((e) => {
        if (active) setError(e.message);
      })
      .finally(() => {
        if (active) setProofLoading(false);
      });
    return () => {
      active = false;
    };
  }, [item]);
  useEffect(() => {
    if (source) sourceClose.current?.focus();
  }, [source]);
  const openSource = async (id: string) => {
    try {
      setSource(await api<Source>("/sources/" + id));
    } catch (e) {
      setError((e as Error).message);
    }
  };
  const inspect = async (id: string) => {
    try {
      if (id.startsWith("mention:")) await openSource(id.split(":")[1]);
      else {
        const c = await api<Claim>("/claims/" + id);
        await openSource(c.source_id);
      }
    } catch (e) {
      setError((e as Error).message);
    }
  };
  const investigate = async () => {
    setBusy(true);
    setError("");
    try {
      const r = await api<Run>(
        "/admin/agent/runs",
        { decision_id: decision, mode: agentMode },
        token,
      );
      setRun(r);
      await load();
      setTab("Evidence");
      setNotice("Investigation saved. All actions remain local drafts.");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  const doImport = async () => {
    setBusy(true);
    setError("");
    try {
      const content = JSON.stringify({
        id: "ticket-live-portal",
        title: "Synthetic partner portal dependency",
        created_at: "2026-10-16T10:30:00+05:30",
        author_id: "person-007",
        body: importBody,
        status: "open",
      });
      await api("/admin/import", { kind: "ticket", content }, token);
      setImportDialog(false);
      await load();
      setTab("Preview");
      setNotice(
        "Source imported. The next preview was recomputed by FalkorDB.",
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  const doConfirm = async () => {
    if (!confirm) return;
    setBusy(true);
    try {
      await api(
        "/admin/" +
          (confirm.kind === "task"
            ? "tasks/" + confirm.id + "/approve"
            : "decisions/" + confirm.id + "/accept"),
        { confirm: true },
        token,
      );
      setConfirm(null);
      await load();
      setNotice("Local approval recorded with an audit event.");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  const toggleFull = async () => {
    if (full) {
      setFull(null);
      return;
    }
    try {
      setFull(await api<Topology>("/company/graph"));
    } catch (e) {
      setError((e as Error).message);
    }
  };
  const dialogOpen = !!source || adminDialog || importDialog || !!confirm;
  useEffect(() => {
    if (!dialogOpen) return;
    const prior = document.activeElement as HTMLElement | null;
    const dialog = document.querySelector<HTMLElement>('[role="dialog"]');
    if (!dialog) return;
    const selector =
      'button:not(:disabled), input, textarea, select, a[href], [tabindex="0"]';
    const first =
      dialog.querySelector<HTMLElement>("input,textarea") ||
      dialog.querySelector<HTMLElement>(selector);
    first?.focus();
    const trap = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setSource(null);
        setAdminDialog(false);
        setImportDialog(false);
        setConfirm(null);
        return;
      }
      if (e.key !== "Tab") return;
      const items = Array.from(dialog.querySelectorAll<HTMLElement>(selector));
      const first = items[0],
        last = items[items.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last?.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first?.focus();
      }
    };
    document.addEventListener("keydown", trap);
    return () => {
      document.removeEventListener("keydown", trap);
      if (prior?.isConnected) prior.focus();
    };
  }, [dialogOpen]);
  const admin = !!token && mode !== "public-readonly";
  const latestTaskRevision = Math.max(
    0,
    ...tasks.map((t) => t.analysis_revision),
  );
  const latestTaskCount = tasks.filter(
    (t) => t.analysis_revision === latestTaskRevision,
  ).length;
  const driftCount = preview
    ? preview.counts.drift_t1 +
      preview.counts.drift_t2 +
      preview.counts.drift_t3
    : 0;
  return (
    <div className="app-shell studio">
      <aside className="sidebar">
        <a className="brand" href="/" aria-label="DecisionDebt home">
          <span className="brand-mark">
            <GitBranch size={21} />
          </span>
          DecisionDebt<span className="brand-period">.</span>
        </a>
        <div className="workspace">
          <span className="workspace-icon">A</span>
          <div>
            <strong>Aster Works</strong>
            <small>Synthetic company</small>
          </div>
          <ChevronRight size={14} />
        </div>
        <span className="nav-caption">WORKSPACE</span>
        <nav aria-label="Studio navigation">
          {[
            { name: "Preview", icon: LayoutDashboard },
            { name: "Evidence", icon: BookOpen },
            { name: "Action Board", icon: Layers3 },
          ].map((n) => (
            <button
              key={n.name}
              className={tab === n.name ? "active" : ""}
              onClick={() => setTab(n.name)}
            >
              <n.icon size={17} />
              {n.name}
              {n.name === "Action Board" && tasks.length > 0 && (
                <span className="nav-count">{latestTaskCount}</span>
              )}
            </button>
          ))}
        </nav>
        <div className="sidebar-note">
          <Network size={21} />
          <strong>No consequence without a source.</strong>
          <p>Every consequence has a path. Every path has a source.</p>
          <span>
            <ShieldCheck size={13} />
            FalkorDB native
          </span>
        </div>
        <div className="source-status">
          <div className="between">
            <span>
              <i className="live-dot" />
              {preview
                ? "Graph connected"
                : error
                  ? "Graph unavailable"
                  : "Connecting"}
            </span>
            <Database size={14} />
          </div>
          <div className="sidebar-stats">
            <span>
              <strong>{summary?.counts.service ?? "—"}</strong>services
            </span>
            <span>
              <strong>{summary?.counts.source ?? "—"}</strong>sources
            </span>
          </div>
          <small>Entirely fictional data · seed 42</small>
        </div>
        <button
          className="admin-link"
          disabled={mode === "public-readonly"}
          onClick={() => setAdminDialog(true)}
        >
          <LockKeyhole size={15} />
          {mode === "public-readonly"
            ? "Public read-only demo"
            : admin
              ? "Local admin unlocked"
              : "Local admin"}
          <ChevronRight size={13} />
        </button>
      </aside>
      <main className="studio-main">
        <header className="topbar">
          <div>
            Aster Works <ChevronRight size={13} />
            <strong>Decision studio</strong>
          </div>
          <div className="topbar-status">
            <button
              className="topbar-import button small"
              disabled={!admin || busy}
              onClick={() => setImportDialog(true)}
            >
              <Plus size={14} />
              Import source
            </button>
            <span
              className={"connection " + (error && !preview ? "offline" : "")}
            >
              <i />
              {preview
                ? "Live FalkorDB"
                : error
                  ? "Graph unavailable"
                  : "Connecting"}
            </span>
            <span className="avatar">AW</span>
          </div>
        </header>
        <div className="page-content">
          <motion.div
            initial={reduced ? false : { opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25, ease: [0.2, 0, 0, 1] }}
          >
            <div className="page-heading">
              <div>
                <div className="eyebrow">
                  <span className="eyebrow-line" />
                  DECISION INTELLIGENCE
                </div>
                <h1>
                  {tab === "Preview" ? (
                    <>Decision workspace</>
                  ) : tab === "Evidence" ? (
                    "Follow the evidence."
                  ) : (
                    "Turn uncertainty into action."
                  )}
                </h1>
                <p>
                  {tab === "Preview"
                    ? "Preview the change. Follow the evidence. Keep uncertainty in view."
                    : tab === "Evidence"
                      ? "Original sources, exact excerpts, and an investigation you can inspect."
                      : "Source-backed proposals. Human judgment. Local approval."}
                </p>
              </div>
              <span className="track-label">
                COMPANY BRAIN <span>03</span>
              </span>
            </div>
            <div className="tabs" role="tablist" aria-label="Decision views">
              {["Preview", "Evidence", "Action Board"].map((t, i) => (
                <button
                  key={t}
                  role="tab"
                  aria-selected={tab === t}
                  className={tab === t ? "selected" : ""}
                  onClick={() => setTab(t)}
                >
                  <span className="tab-num">0{i + 1}</span>
                  {t}
                  {t === "Action Board" && (
                    <span className="count-pill">{latestTaskCount}</span>
                  )}
                </button>
              ))}
              <span className="tabs-meta">
                {preview
                  ? "Revision " + preview.graph_revision
                  : "Connecting to graph"}
              </span>
            </div>
            {error && (
              <div className="alert" role="alert">
                <TriangleAlert size={18} />
                <span>
                  {error}{" "}
                  <button className="text-button" onClick={() => void load()}>
                    Retry live query
                  </button>
                </span>
                <button aria-label="Dismiss error" onClick={() => setError("")}>
                  <X size={16} />
                </button>
              </div>
            )}
            {notice && (
              <div className="notice" role="status">
                <Check size={16} />
                {notice}
                <button
                  aria-label="Dismiss notice"
                  onClick={() => setNotice("")}
                >
                  <X size={15} />
                </button>
              </div>
            )}
            {loading && !preview ? (
              <div className="loading" role="status">
                <RefreshCw className="spinner" />
                Querying the live company graph…
              </div>
            ) : !preview ? (
              <div className="empty">
                <Database />
                <h2>Live graph required</h2>
                <p>
                  Start FalkorDB and import the synthetic corpus, then retry. No
                  recorded results replace live data.
                </p>
                <button className="button primary" onClick={() => void load()}>
                  Retry connection
                </button>
              </div>
            ) : (
              <>
                <section className="decision-card">
                  <div className="decision-icon">
                    <GitBranch size={24} />
                  </div>
                  <div className="decision-text">
                    <div className="inline-tags">
                      <span className="mono">{decision}</span>
                      <span className="badge proposed">
                        {preview.decision_status}
                      </span>
                    </div>
                    <h2>{preview.decision.title}</h2>
                    <p>
                      Comparison:{" "}
                      <span className="mono">{preview.decision.old_id}</span>
                      <span className="separator">/</span>
                      {preview.decision_status === "proposed"
                        ? "Acceptance is a separate human action."
                        : "Human acceptance recorded."}
                    </p>
                  </div>
                  <div className="decision-actions">
                    <button
                      className="button"
                      disabled={busy || loading}
                      onClick={() => void load()}
                    >
                      <RefreshCw size={15} />
                      Refresh preview
                    </button>
                    {admin && preview.decision_status === "proposed" && (
                      <button
                        className="text-button"
                        onClick={() =>
                          setConfirm({ kind: "decision", id: decision })
                        }
                      >
                        Accept decision <ArrowUpRight size={14} />
                      </button>
                    )}
                  </div>
                </section>
                {tab === "Preview" && (
                  <StudioView>
                    <div className="metrics">
                      {[
                        {
                          label: "Affected services",
                          value: preview.counts.services,
                          sub:
                            "Within " + preview.max_hops + " dependency hops",
                          icon: Network,
                        },
                        {
                          label: "Projects in scope",
                          value: preview.counts.projects,
                          sub: "Linked through service usage",
                          icon: Layers3,
                        },
                        {
                          label: "Knowledge drift",
                          value: driftCount,
                          sub: `${preview.counts.drift_t1} citation · ${preview.counts.drift_t2} suspect · ${preview.counts.drift_t3} overdue`,
                          icon: FileText,
                        },
                        {
                          label: "Ownership to resolve",
                          value:
                            preview.counts.owner_gaps +
                            preview.counts.owner_conflicts,
                          sub: `${preview.counts.owner_gaps} unassigned · ${preview.counts.owner_conflicts} conflict`,
                          icon: TriangleAlert,
                        },
                      ].map((m) => (
                        <article className="metric" key={m.label}>
                          <div className="between">
                            <span>{m.label}</span>
                            <m.icon size={17} />
                          </div>
                          <strong
                            data-testid={
                              m.label === "Affected services"
                                ? "affected-count"
                                : undefined
                            }
                          >
                            {m.value}
                          </strong>
                          <small>{m.sub}</small>
                        </article>
                      ))}
                    </div>
                    <section className="graph-panel">
                      <div className="panel-heading">
                        <div>
                          <h2>
                            Follow the blast radius{" "}
                            <span className="live-label">
                              <i />
                              LIVE QUERY
                            </span>
                          </h2>
                          <p>
                            Consumer → provider. Select a service to inspect its
                            path and proof.
                          </p>
                        </div>
                        <div className="graph-tools">
                          <label>
                            Depth{" "}
                            <select
                              aria-label="Maximum displayed depth"
                              value={depth}
                              onChange={(e) => setDepth(Number(e.target.value))}
                            >
                              {[1, 2, 3, 4, 5].map((d) => (
                                <option key={d}>{d}</option>
                              ))}
                            </select>
                          </label>
                          <button
                            className={
                              "button small " + (full ? "selected" : "")
                            }
                            onClick={() => void toggleFull()}
                          >
                            <Network size={14} />
                            {full ? "Focused view" : "Company map"}
                          </button>
                        </div>
                      </div>
                      <label className="mobile-service-picker">
                        Inspect a service
                        <select
                          aria-label="Inspect an affected service"
                          value={selected}
                          onChange={(event) => {
                            setSelected(event.target.value);
                            const target = preview.impacts.find(
                              (i) => i.service_id === event.target.value,
                            );
                            if (target && target.depth > depth)
                              setDepth(target.depth);
                          }}
                        >
                          {preview.impacts.map((i) => (
                            <option key={i.service_id} value={i.service_id}>
                              {i.name}
                              {i.owner_status === "conflict"
                                ? " · Conflicting owners"
                                : i.owner_status === "unowned"
                                  ? " · Owner unassigned"
                                  : ""}
                            </option>
                          ))}
                        </select>
                      </label>
                      <div className="graph-layout">
                        <ImpactGraph
                          preview={preview}
                          selected={selected}
                          onSelect={(id) => {
                            setSelected(id);
                            if (
                              !preview.impacts.some((i) => i.service_id === id)
                            )
                              setNotice(
                                "This service is outside the bounded decision preview. Its company-map edges still come from live Cypher.",
                              );
                          }}
                          depth={depth}
                          full={full}
                        />
                        <EvidenceDrawer
                          item={item}
                          claims={proofs}
                          loading={proofLoading}
                          onSource={(id) => void openSource(id)}
                        />
                      </div>
                      <div className="graph-bottom">
                        <div className="graph-coverage">
                          <span className="graph-boundary-status">
                            <GitBranch size={14} />
                            Max depth {preview.max_hops}
                            {preview.cycle_detected
                              ? " · Cycle paths bounded"
                              : ""}{" "}
                            ·{" "}
                            {preview.truncated
                              ? "Truncated"
                              : "No additional consumers found at boundary"}
                          </span>
                          {preview.truncated && (
                            <p className="truncation-note">
                              We bound traversal to {preview.max_hops} hops to
                              keep query work predictable; these{" "}
                              {preview.counts.services} services and{" "}
                              {preview.counts.projects} projects are verified in
                              scope, with further affected services
                              {preview.truncation_examples?.[0]
                                ? ` including ${preview.truncation_examples[0].name} at hop ${preview.truncation_examples[0].depth}.`
                                : " beyond this boundary."}
                            </p>
                          )}
                        </div>
                        <span className="mono">
                          {preview.elapsed_ms.toFixed(1)} ms · revision{" "}
                          {preview.graph_revision}
                        </span>
                      </div>
                    </section>
                    <section className="investigation-callout">
                      <div className="investigation-symbol">
                        <Sparkles size={24} />
                      </div>
                      <div>
                        <span className="small-label">
                          THE NEXT QUESTION MATTERS
                        </span>
                        <h3>Some consequences need a closer look.</h3>
                        <p>
                          Investigate the owner gap, conflicting claims, and
                          unlinked OrionAuth mention.
                        </p>
                      </div>
                      <div className="investigation-controls">
                        <select
                          aria-label="Investigation mode"
                          value={agentMode}
                          onChange={(e) => setAgentMode(e.target.value)}
                        >
                          <option value="deterministic">
                            Deterministic rule run
                          </option>
                          <option value="llm">Configured LLM</option>
                        </select>
                        <button
                          className="button primary"
                          disabled={busy || !admin}
                          onClick={() => void investigate()}
                        >
                          <Play size={14} />
                          {busy ? "Investigating…" : "Run investigation"}
                        </button>
                        {!admin && <small>Unlock local admin to run.</small>}
                      </div>
                    </section>
                    <div className="lower-grid">
                      <section className="surface">
                        <div className="between">
                          <h3>Knowledge that needs attention</h3>
                          <button
                            className="text-button"
                            onClick={() => setTab("Evidence")}
                          >
                            View evidence <ArrowRight size={14} />
                          </button>
                        </div>
                        {preview.drifts.slice(0, 3).map((d) => (
                          <button
                            className="drift-row"
                            key={d.id}
                            onClick={() => void openSource(d.source_id)}
                          >
                            <span className={"tier tier-" + d.tier}>
                              T{d.tier}
                            </span>
                            <span>
                              <strong>{badge(d)}</strong>
                              <small>
                                {d.source_id} ·{" "}
                                {d.certainty.replaceAll("_", " ")}
                              </small>
                            </span>
                            <ArrowUpRight size={15} />
                          </button>
                        ))}
                      </section>
                      <section className="surface new-evidence">
                        <Plus size={22} />
                        <h3>A new source can change the story.</h3>
                        <p>
                          Import a synthetic ticket to connect External Portal.
                          Then remove its dependency and watch the live graph
                          retract the claim.
                        </p>
                        <button
                          className="button"
                          disabled={!admin || busy}
                          onClick={() => setImportDialog(true)}
                        >
                          Import new evidence <ArrowRight size={14} />
                        </button>
                      </section>
                    </div>
                  </StudioView>
                )}
                {tab === "Evidence" && (
                  <StudioView>
                    <div className="evidence-summary">
                      {summary?.source_types.map((t) => (
                        <span key={t.kind}>
                          <FileText size={16} />
                          <strong>{t.count}</strong>
                          {t.kind === "doc"
                            ? "Markdown documents"
                            : t.kind === "ticket"
                              ? "JSON tickets"
                              : "Chat messages"}
                        </span>
                      ))}
                      <span>
                        <ShieldCheck size={16} />
                        <strong>
                          {summary?.claim_statuses.find(
                            (s) => s.status === "verified",
                          )?.count ?? 0}
                        </strong>
                        verified claims
                      </span>
                      <span>
                        <TriangleAlert size={16} />
                        <strong>{candidates.length}</strong>candidates
                      </span>
                    </div>
                    <form
                      className="search-form"
                      onSubmit={(e) => {
                        e.preventDefault();
                        setBusy(true);
                        api<{ sources: typeof results }>(
                          "/sources/search?q=" + encodeURIComponent(query),
                        )
                          .then((r) => setResults(r.sources))
                          .catch((e) => setError(e.message))
                          .finally(() => setBusy(false));
                      }}
                    >
                      <Search size={18} />
                      <input
                        aria-label="Search source aliases"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Search an exact entity alias"
                      />
                      <button className="button primary" disabled={busy}>
                        Search sources
                      </button>
                    </form>
                    <p className="caption">
                      Native FalkorDB full-text search. Exact source text is
                      checked after retrieval.
                    </p>
                    {results && (
                      <section className="surface search-results">
                        <h3>{results.length} verified alias matches</h3>
                        {results.map((r) => (
                          <button
                            className="search-result"
                            key={r.source_id}
                            onClick={() => void openSource(r.source_id)}
                          >
                            <strong>
                              {r.title}
                              <ArrowUpRight size={14} />
                            </strong>
                            <p>{r.context}</p>
                            <small>
                              {r.source_id} · retrieval score{" "}
                              {r.ft_score.toFixed(3)}, not a truth probability
                            </small>
                          </button>
                        ))}
                      </section>
                    )}
                    {preview.review_date_issues?.length > 0 && (
                      <section className="surface">
                        <h3>Unknown review dates</h3>
                        {preview.review_date_issues.map((issue) => (
                          <button
                            className="candidate-row"
                            key={issue.source_id}
                            onClick={() => void openSource(issue.source_id)}
                          >
                            <TriangleAlert size={15} />
                            <span>
                              {issue.source_id}: {issue.reason}
                            </span>
                          </button>
                        ))}
                      </section>
                    )}
                    <div className="drift-grid">
                      {[1, 2, 3].map((tier) => (
                        <section className="surface" key={tier}>
                          <div className="between">
                            <span className={"tier tier-" + tier}>T{tier}</span>
                            <span className="count-pill">
                              {preview.counts["drift_t" + tier]}
                            </span>
                          </div>
                          <h3>
                            {tier === 1
                              ? "Explicit stale citations"
                              : tier === 2
                                ? "Unlinked obsolete mentions"
                                : "Overdue document reviews"}
                          </h3>
                          <p>
                            {tier === 1
                              ? "A reference to the decision being replaced."
                              : tier === 2
                                ? "A verified mention, requiring investigation."
                                : "A service document last reviewed 90+ days ago."}
                          </p>
                          {preview.drifts
                            .filter((d) => d.tier === tier)
                            .map((d) => (
                              <button
                                className="drift-evidence"
                                key={d.id}
                                onClick={() => void openSource(d.source_id)}
                              >
                                <span className="mono">
                                  {d.source_id}
                                  <ArrowUpRight size={13} />
                                </span>
                                <q>{d.excerpt}</q>
                                <small>
                                  {d.certainty.replaceAll("_", " ")}
                                </small>
                              </button>
                            ))}
                        </section>
                      ))}
                    </div>
                    <section className="surface">
                      <div className="between">
                        <div>
                          <h2>Investigation trace</h2>
                          <p className="caption">
                            Inspect the tools, retrieved evidence, and local
                            draft proposals.
                          </p>
                        </div>
                        <button
                          className="button"
                          disabled={!admin || busy}
                          onClick={() => void investigate()}
                        >
                          <Play size={14} />
                          Run investigation
                        </button>
                      </div>
                      <InvestigationTrace run={run} />
                    </section>
                    <section className="surface">
                      <h3>Candidate claims stay inactive</h3>
                      {candidates.map((c) => (
                        <button
                          className="candidate-row"
                          key={c.id}
                          onClick={() => void openSource(c.source_id)}
                        >
                          <TriangleAlert size={15} />
                          <span>{c.excerpt}</span>
                          <span className="badge">candidate</span>
                        </button>
                      ))}
                    </section>
                    <details className="surface query-details">
                      <summary>
                        <Database size={16} />
                        Query proof · {preview.query_trace.length} measured
                        queries{" "}
                        <span className="mono">
                          revision {preview.graph_revision}
                        </span>
                      </summary>
                      {preview.query_trace.map((q, i) => (
                        <div className="query" key={i}>
                          <strong>{q.query_id}</strong>
                          <small>
                            {q.row_count} rows · {q.elapsed_ms} ms
                          </small>
                          <pre>{q.cypher}</pre>
                          <code>{JSON.stringify(q.params)}</code>
                        </div>
                      ))}
                    </details>
                  </StudioView>
                )}
                {tab === "Action Board" && (
                  <StudioView>
                    <div className="action-intro">
                      <span>
                        <LockKeyhole size={16} />
                        Local drafts only. Approval creates an audit event.
                      </span>
                      <button
                        className="button primary"
                        disabled={!admin || busy}
                        onClick={() => void investigate()}
                      >
                        <Play size={14} />
                        Run investigation
                      </button>
                    </div>
                    <ActionBoard
                      tasks={tasks}
                      admin={admin}
                      busy={busy}
                      onApprove={(id) => setConfirm({ kind: "task", id })}
                      onEvidence={(id) => void inspect(id)}
                    />
                  </StudioView>
                )}
                <footer>
                  <span>
                    <Database size={13} />
                    Source text → verified claim → live graph → reviewable
                    action
                  </span>
                  <span>
                    Aster Works is synthetic. All counts come from FalkorDB.
                  </span>
                </footer>
              </>
            )}
          </motion.div>
        </div>
      </main>
      {source && (
        <div className="modal-backdrop" onClick={() => setSource(null)}>
          <section
            role="dialog"
            aria-modal="true"
            aria-label="Source evidence"
            className="source-modal"
            onClick={(e) => e.stopPropagation()}
            onKeyDown={(e) => {
              if (e.key === "Escape") setSource(null);
            }}
          >
            <div className="between">
              <span className="badge">{source.kind} · Synthetic</span>
              <button
                ref={sourceClose}
                className="icon-button"
                aria-label="Close source evidence"
                onClick={() => setSource(null)}
              >
                <X />
              </button>
            </div>
            <h2>{source.title}</h2>
            <p className="mono">
              {source.id} · {source.revisions.length} revision
              {source.revisions.length === 1 ? "" : "s"}
            </p>
            <p className="hash">SHA-256 {source.sha256}</p>
            <div className="source-body">{source.body}</div>
            <h3>Claims and exact source spans</h3>
            {source.claims.map((c) => (
              <article key={c.id} className="claim-detail">
                <span className="badge">{c.status}</span>
                <strong>{c.relation}</strong>
                <p>{c.excerpt}</p>
                <code>
                  {c.id} · {c.anchor_field}[{c.start}:{c.end}] · {c.method}
                </code>
              </article>
            ))}
          </section>
        </div>
      )}
      {(adminDialog || importDialog || confirm) && (
        <div className="modal-backdrop">
          <section
            className="small-modal"
            role="dialog"
            aria-modal="true"
            aria-label={
              adminDialog
                ? "Local admin"
                : importDialog
                  ? "Import synthetic evidence"
                  : "Confirm local approval"
            }
            onKeyDown={(e) => {
              if (e.key === "Escape") {
                setAdminDialog(false);
                setImportDialog(false);
                setConfirm(null);
              }
            }}
          >
            <button
              className="modal-close icon-button"
              aria-label="Close dialog"
              onClick={() => {
                setAdminDialog(false);
                setImportDialog(false);
                setConfirm(null);
              }}
            >
              <X size={20} />
            </button>
            {adminDialog ? (
              <>
                <LockKeyhole size={26} />
                <h2>Local admin</h2>
                <p>
                  Paste the ADMIN_TOKEN from your local .env file. It stays in
                  memory for this browser session.
                </p>
                <label className="field">
                  Admin token
                  <input
                    type="password"
                    autoComplete="off"
                    value={tokenDraft}
                    onChange={(e) => setTokenDraft(e.target.value)}
                  />
                </label>
                <button
                  className="button primary"
                  disabled={!tokenDraft || mode === "public-readonly"}
                  onClick={() => {
                    setToken(tokenDraft);
                    setTokenDraft("");
                    setAdminDialog(false);
                    setNotice(
                      "Token stored in memory. Write requests are validated by the server.",
                    );
                  }}
                >
                  Unlock local actions
                </button>
                {token && (
                  <button
                    className="text-button"
                    onClick={() => {
                      setToken("");
                      setAdminDialog(false);
                    }}
                  >
                    Lock local actions
                  </button>
                )}
              </>
            ) : importDialog ? (
              <>
                <Plus size={26} />
                <h2>Import synthetic evidence</h2>
                <p>
                  This imports or updates ticket-live-portal. Removing the
                  dependency sentence retracts only this ticket's claims.
                </p>
                <label className="field">
                  Ticket body
                  <textarea
                    rows={6}
                    value={importBody}
                    onChange={(e) => setImportBody(e.target.value)}
                  />
                </label>
                <button
                  className="text-button"
                  onClick={() =>
                    setImportBody(
                      "The partner portal review remains open. There is no asserted integration dependency in this revision.",
                    )
                  }
                >
                  Use retraction text
                </button>
                <button
                  className="button primary"
                  disabled={busy || !importBody}
                  onClick={() => void doImport()}
                >
                  Import and refresh live preview <ArrowRight size={14} />
                </button>
              </>
            ) : (
              <>
                <ShieldCheck size={26} />
                <h2>
                  {confirm?.kind === "task"
                    ? "Approve this local task?"
                    : "Accept the migration decision?"}
                </h2>
                <p>
                  {confirm?.kind === "task"
                    ? "This changes the local task status and records a human approval event."
                    : "This changes the decision status, creates SUPERSEDES lineage, and records an approval event."}
                </p>
                <p className="mono">{confirm?.id}</p>
                <button
                  className="button primary"
                  disabled={busy}
                  onClick={() => void doConfirm()}
                >
                  Confirm{" "}
                  {confirm?.kind === "task"
                    ? "local approval"
                    : "decision acceptance"}
                </button>
              </>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
