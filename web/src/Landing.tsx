import { useEffect, useState } from "react";
import { motion, useReducedMotion } from "motion/react";
import {
  ArrowRight,
  ArrowUpRight,
  Check,
  Database,
  FileText,
  GitBranch,
  Layers3,
  Network,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { api } from "./api";
import { companyQuestions } from "./companyQuestions";
import type { Preview, Summary, Run } from "./types";
import { motionIdentity as timing } from "./motion";
import "./landing.css";
export default function Landing() {
  const reduced = useReducedMotion();
  const [preview, setPreview] = useState<Preview | null>(null);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [recorded, setRecorded] = useState<Run | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    document.title = "DecisionDebt | See the consequence";
    let alive = true;
    Promise.all([
      api<Preview>("/decisions/dec-auth-002/preview"),
      api<Summary>("/company/summary"),
      api<{ runs: { id: string; mode: string }[] }>("/agent/runs"),
    ])
      .then(async ([p, s, r]) => {
        if (!alive) return;
        setPreview(p);
        setSummary(s);
        const candidate = r.runs.find((x) => x.mode === "llm");
        if (candidate) {
          const proof = await api<Run>("/agent/runs/" + candidate.id);
          if (
            alive &&
            proof.execution_kind === "llm" &&
            proof.status === "completed" &&
            proof.provider_verified &&
            proof.coverage?.all_passed
          )
            setRecorded(proof);
        }
      })
      .catch((e) => {
        if (alive) setError(e.message);
      });
    return () => {
      alive = false;
    };
  }, []);
  const path =
    preview?.impacts.find(
      (i) => i.alternative_path_count > 1 && i.owner_status === "conflict",
    ) || preview?.impacts[0];
  const rise = (delay = 0) => ({
    initial: reduced ? false : { opacity: 0, y: 18 },
    animate: { opacity: 1, y: 0 },
    transition: {
      duration: timing.slow,
      delay: reduced ? 0 : delay,
      ease: timing.ease,
    },
  });
  return (
    <div className="landing">
      <header className="landing-nav">
        <a className="landing-brand" href="/" aria-label="DecisionDebt home">
          <span>
            <GitBranch size={21} />
          </span>
          DecisionDebt<span className="brand-stop">.</span>
        </a>
        <nav aria-label="Product navigation">
          <a href="#how-it-works">How it works</a>
          <a href="#evidence">The evidence</a>
          <a href="/studio" className="landing-nav-cta">
            Open studio <ArrowUpRight size={14} />
          </a>
        </nav>
      </header>
      <main className="landing-main">
        <section className="landing-hero">
          <motion.a {...rise()} href="/studio" className="launch-pill">
            <span className="signal-dot" />
            Company knowledge, connected.
            <ArrowRight size={12} />
          </motion.a>
          <motion.h1 {...rise(0.07)}>
            One decision.
            <br />
            <span>A world of consequences.</span>
          </motion.h1>
          <motion.p {...rise(0.14)} className="hero-copy">
            Your company remembers what it decided.
            <br />
            DecisionDebt shows what that decision touches, and the evidence
            behind every connection.
          </motion.p>
          <motion.div {...rise(0.21)} className="hero-actions">
            <a className="landing-primary" href="/studio">
              Explore the live company brain <ArrowRight size={16} />
            </a>
            <a className="landing-secondary" href="#how-it-works">
              See how it works <span>↓</span>
            </a>
          </motion.div>
          <motion.div {...rise(0.28)} className="hero-facts">
            <span>
              <ShieldCheck size={13} />
              Source-backed relationships
            </span>
            <span>
              <GitBranch size={13} />
              FalkorDB native
            </span>
            <span>
              <Check size={13} />
              Human-controlled actions
            </span>
          </motion.div>
          <motion.div {...rise(0.24)} className="hero-product">
            <div className="product-bar">
              <div>
                <span className="window-dot" />
                <span className="window-dot" />
                <span className="window-dot" />
              </div>
              <span>Aster Works / Decision preview</span>
              <span className="product-live">
                <i />
                {preview
                  ? "Live graph"
                  : error
                    ? "Graph unavailable"
                    : "Connecting"}
              </span>
            </div>
            <div className="product-preview">
              <div className="product-decision">
                <span className="product-eyebrow">THE DECISION</span>
                <div className="product-badge">
                  {preview?.decision_status || "Awaiting graph"}
                </div>
                <h2>
                  {preview?.decision.title ||
                    "Know the consequence before the commitment."}
                </h2>
                <p>Preview the change. Keep the human decision separate.</p>
                {preview && (
                  <div className="hero-counts">
                    <div>
                      <strong>{preview.counts.services}</strong>
                      <span>affected services</span>
                    </div>
                    <div>
                      <strong>
                        {preview.counts.owner_gaps +
                          preview.counts.owner_conflicts}
                      </strong>
                      <span>owners to resolve</span>
                    </div>
                    <div>
                      <strong>
                        {preview.counts.drift_t1 +
                          preview.counts.drift_t2 +
                          preview.counts.drift_t3}
                      </strong>
                      <span>drift findings</span>
                    </div>
                  </div>
                )}
                <a href="/studio">
                  Inspect this decision <ArrowUpRight size={14} />
                </a>
              </div>
              <div className="product-path">
                <div className="product-path-header">
                  <span>
                    <Network size={14} />A consequence you can trace
                  </span>
                  <span className="mono">
                    {preview
                      ? "r" + preview.graph_revision
                      : "Live DB required"}
                  </span>
                </div>
                {error ? (
                  <p className="landing-error">{error}</p>
                ) : path ? (
                  <>
                    <div className="landing-path-nodes">
                      {path.paths[0]
                        .slice()
                        .reverse()
                        .map((id, i) => (
                          <motion.div
                            className={
                              "landing-path-node " +
                              (i === 0 ? "path-root" : "")
                            }
                            key={id}
                            initial={reduced ? false : { opacity: 0, x: -12 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{
                              delay: reduced ? 0 : 0.35 + i * 0.07,
                              duration: 0.3,
                            }}
                          >
                            <span className="path-node-symbol">
                              {i === 0 ? (
                                <GitBranch size={17} />
                              ) : (
                                <Layers3 size={17} />
                              )}
                            </span>
                            <div>
                              <small>
                                {i === 0
                                  ? "CHANGE ROOT"
                                  : "DOWNSTREAM CONSUMER"}
                              </small>
                              <strong>
                                {preview?.impacts.find(
                                  (v) => v.service_id === id,
                                )?.name || id}
                              </strong>
                            </div>
                            {i < path.paths[0].length - 1 && (
                              <span className="landing-path-connector" />
                            )}
                          </motion.div>
                        ))}
                    </div>
                    <div className="path-explanation">
                      <ShieldCheck size={14} />
                      <p>
                        Every connection has a verified source claim.
                        <br />
                        <span>
                          {path.alternative_path_count} path
                          {path.alternative_path_count === 1 ? "" : "s"} · query
                          limited to {preview?.max_hops} hops
                        </span>
                      </p>
                      <a
                        href="/studio?tab=Evidence"
                        aria-label="Inspect source evidence"
                      >
                        <ArrowUpRight size={17} />
                      </a>
                    </div>
                  </>
                ) : (
                  <div className="landing-loading">Reading the live graph…</div>
                )}
              </div>
            </div>
            <div className="product-bottom">
              <span>
                <Database size={12} />
                FalkorDB performs the traversal.
              </span>
              <span>Entirely synthetic Aster Works data</span>
            </div>
          </motion.div>
        </section>
        <section
          className="landing-measurements"
          aria-label="Live company dataset"
        >
          <span>
            A REAL GRAPH.
            <br />
            <strong>REPRODUCIBLE EVIDENCE.</strong>
          </span>
          {summary ? (
            [
              ["service", "Services"],
              ["source", "Source records"],
              ["semantic_edges", "Verified relationships"],
            ].map(([key, label]) => (
              <div key={key}>
                <strong>{summary.counts[key]}</strong>
                <span>{label}</span>
              </div>
            ))
          ) : (
            <p>Connect FalkorDB to see measured company counts.</p>
          )}
          <a href="/studio?tab=Evidence">
            Inspect the sources <ArrowUpRight size={15} />
          </a>
        </section>
        <section className="landing-ask" aria-labelledby="landing-ask-heading">
          <div>
            <span className="section-eyebrow">
              ANSWERS FROM CONNECTED KNOWLEDGE
            </span>
            <h2 id="landing-ask-heading">Ask the company graph.</h2>
            <p>
              Find an owner, trace a dependency, or find the right reviewers.
              Live FalkorDB answers with exact source citations. No model or
              key.
            </p>
          </div>
          <div>
            <form action="/studio" method="get">
              <label htmlFor="landing-question">Your company question</label>
              <div>
                <input
                  id="landing-question"
                  name="q"
                  required
                  maxLength={240}
                  defaultValue="Who owns Session Broker?"
                />
                <button className="button primary" type="submit">
                  Ask graph <ArrowRight size={15} />
                </button>
              </div>
            </form>
            <div className="landing-ask-examples">
              {companyQuestions.map((q) => (
                <a key={q} href={"/studio?q=" + encodeURIComponent(q)}>
                  {q}
                  <ArrowUpRight size={12} />
                </a>
              ))}
            </div>
          </div>
        </section>
        <section className="knowledge-story" id="how-it-works">
          <div className="story-art">
            <img
              src="/assets/knowledge-still-life.webp"
              width={1536}
              height={1024}
              loading="lazy"
              alt="Concept artwork: ivory source cards, an archive clip and a cobalt glass slab on graphite"
            />
            <span>Original concept artwork</span>
          </div>
          <motion.div
            initial={reduced ? false : { opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.2 }}
            transition={{ duration: 0.35, ease: timing.ease }}
            className="story-copy"
          >
            <div className="section-eyebrow">
              THE KNOWLEDGE IS ALREADY THERE
            </div>
            <h2>
              The context is scattered.
              <br />
              <span>The consequences don't have to be.</span>
            </h2>
            <p>
              A runbook remembers the old provider. A ticket names a dependency.
              A conversation disputes the owner. DecisionDebt connects those
              fragments before a proposed change becomes an expensive surprise.
            </p>
            <a href="/studio" className="landing-secondary">
              Follow a real dependency path <ArrowRight size={15} />
            </a>
          </motion.div>
        </section>
        <section className="landing-workflow" id="evidence">
          <div className="section-heading">
            <div>
              <span className="section-eyebrow">
                FROM KNOWING TO UNDERSTANDING
              </span>
              <h2>Evidence at every step.</h2>
            </div>
            <p>
              Understand the graph. Inspect the source.
              <br />
              Keep uncertainty visible.
            </p>
          </div>
          <div className="workflow-grid">
            {[
              {
                number: "01",
                icon: FileText,
                title: "Start with the messy truth.",
                copy: "Markdown, tickets and chat become exact-span claims. Hedged and negated statements remain inactive.",
              },
              {
                number: "02",
                icon: GitBranch,
                title: "Follow what follows.",
                copy: "Preview a proposed decision through five dependency hops. See real paths, shared dependencies and the boundary of the answer.",
              },
              {
                number: "03",
                icon: Sparkles,
                title: "Investigate the unknown.",
                copy: "A bounded agent chooses tools, compares ownership evidence, reviews unlinked mentions and proposes local drafts.",
              },
            ].map((c, i) => (
              <motion.article
                key={c.number}
                whileHover={reduced ? {} : { y: -4 }}
                initial={reduced ? false : { opacity: 0, y: 14 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.2 }}
                transition={{
                  duration: 0.3,
                  delay: reduced ? 0 : i * 0.06,
                  ease: timing.ease,
                }}
              >
                <div>
                  <span>{c.number}</span>
                  <c.icon size={24} />
                </div>
                <h3>{c.title}</h3>
                <p>{c.copy}</p>
              </motion.article>
            ))}
          </div>
          <div className="landing-proof-strip">
            <div>
              <span className="signal-dot" />
              <strong>
                {recorded
                  ? "Real LLM investigation recorded"
                  : "Live graph. Honest agent provenance."}
              </strong>
              <span>
                {recorded
                  ? recorded.model
                  : "A rule run is always labeled deterministic."}
              </span>
            </div>
            <a href="/studio?tab=Evidence">
              Inspect the trace <ArrowUpRight size={14} />
            </a>
          </div>
        </section>
        <section className="landing-final">
          <div className="section-eyebrow">DECIDE WITH YOUR EYES OPEN</div>
          <h2>
            See the ripple.
            <br />
            <span>Before you make the change.</span>
          </h2>
          <a className="landing-primary" href="/studio">
            Open the decision studio <ArrowRight size={16} />
          </a>
          <small>Synthetic data. Live FalkorDB. Local human approval.</small>
        </section>
      </main>
      <footer className="landing-footer">
        <a href="/" className="landing-brand">
          <span>
            <GitBranch size={18} />
          </span>
          DecisionDebt.
        </a>
        <span>Built for Company Brain · WeMakeDevs × FalkorDB</span>
        <a href="/studio">
          Open studio <ArrowUpRight size={13} />
        </a>
      </footer>
    </div>
  );
}
