import { useEffect, useRef, useState } from "react";
import { ArrowUpRight, CornerDownLeft, Database, Search } from "lucide-react";
import { api } from "../api";
import { companyQuestions, questionFor } from "../companyQuestions";
import { RECORDED_DEMO } from "../deployment";
import type { AskAnswer } from "../types";
import "../ask.css";

export default function AskGraph({
  onSource,
}: {
  onSource: (id: string) => void;
}) {
  const initial = useRef(
    new URLSearchParams(window.location.search).get("q") || "",
  );
  const autoAsked = useRef(false);
  const [question, setQuestion] = useState(initial.current);
  const [answer, setAnswer] = useState<AskAnswer | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(value: string) {
    if (!value.trim()) return;
    setQuestion(value);
    setBusy(true);
    setError("");
    setAnswer(null);
    try {
      setAnswer(
        await api<AskAnswer>("/company/ask?q=" + encodeURIComponent(value)),
      );
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "The live graph didn't respond.",
      );
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    if (initial.current && !autoAsked.current) {
      autoAsked.current = true;
      void submit(initial.current);
    }
  }, []);

  return (
    <section
      className="ask-graph"
      aria-labelledby="ask-heading"
      id="ask-company-graph"
    >
      <div className="ask-heading">
        <div>
          <span className="eyebrow">
            <Database size={13} /> LIVE COMPANY KNOWLEDGE
          </span>
          <h2 id="ask-heading">Ask the company graph</h2>
          <p>
            People, projects and proof. Fixed graph queries, no model or API
            key.
          </p>
        </div>
        <span className="badge">READ ONLY</span>
      </div>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          void submit(question);
        }}
      >
        <label className="sr-only" htmlFor="company-question">
          Company question
        </label>
        <Search size={18} aria-hidden="true" />
        <input
          id="company-question"
          value={question}
          maxLength={240}
          required
          placeholder="Who owns Session Broker?"
          onChange={(e) => setQuestion(e.target.value)}
        />
        <button
          type="submit"
          className="button primary"
          disabled={busy || !question.trim()}
        >
          {busy ? "Querying…" : "Ask graph"}
          <CornerDownLeft size={15} />
        </button>
      </form>
      <div className="ask-examples" aria-label="Example company questions">
        {companyQuestions.map((q) => (
          <button key={q} disabled={busy} onClick={() => void submit(q)}>
            {q}
            <ArrowUpRight size={12} />
          </button>
        ))}
      </div>
      <details className="ask-shapes">
        <summary>What can I ask?</summary>
        <p>
          Use a service name with one of these shapes. Partial names and typos
          offer suggestions for you to confirm.
        </p>
        <ul>
          {[
            "Who owns <service>?",
            "What depends on <service>?",
            "What would replacing <service> affect?",
            "Which projects use <service>?",
            "Who should review a change to <service>?",
            "What documents mention <service>?",
          ].map((s) => (
            <li key={s}>{s}</li>
          ))}
        </ul>
      </details>
      {busy && (
        <p role="status" className="ask-progress">
          Reading verified relationships from FalkorDB…
        </p>
      )}
      {error && (
        <div role="alert" className="ask-error">
          <p>
            {error} Retry, or{" "}
            <a href={RECORDED_DEMO}>watch the recorded demo</a>.
          </p>
          <button
            className="button small"
            onClick={() => void submit(question)}
          >
            Retry question
          </button>
        </div>
      )}
      {answer && (
        <div
          className="ask-answer"
          data-answer-status={answer.status}
          aria-live="polite"
        >
          <div className="ask-result-heading">
            <h3>{answer.message}</h3>
            {answer.status === "answered" && (
              <span className="mono">
                {answer.row_count} answer rows · {answer.query_ms} ms query time
                · revision {answer.graph_revision}
              </span>
            )}
          </div>
          {answer.status === "ambiguous" && (
            <div className="ask-suggestions">
              {answer.suggestions.map((s) => (
                <button
                  className="button small"
                  key={s.id}
                  onClick={() =>
                    void submit(questionFor(answer.intent!, s.name))
                  }
                >
                  {s.name}
                  <ArrowUpRight size={13} />
                </button>
              ))}
              <p>
                No service was selected. Choose a recorded name to run the
                answer query.
              </p>
            </div>
          )}
          {(answer.status === "unsupported" ||
            answer.status === "not_found") && (
            <ul>
              {answer.supported_shapes.map((s) => (
                <li key={s}>{s}</li>
              ))}
            </ul>
          )}
          {answer.truncated && (
            <p className="ask-boundary">
              We bound traversal to {answer.max_hops} hops to keep query work
              predictable; these {answer.counts.services} services and{" "}
              {answer.counts.projects} projects are verified in scope, with
              further affected services including{" "}
              {answer.truncation_examples
                .map((s) => `${s.name} at hop ${s.depth}`)
                .join(", ")}
              .
            </p>
          )}
          {answer.cycle_detected && (
            <p className="ask-boundary">
              A dependency cycle is present. Services are counted once, at their
              shortest verified depth.
            </p>
          )}
          {!!answer.rows.length && (
            <ol className="ask-rows">
              {answer.rows.map((row, i) => (
                <li key={i}>
                  <div>
                    <strong>{row.label}</strong>
                    {row.depth !== undefined && (
                      <span className="badge">hop {row.depth}</span>
                    )}
                    <p>{row.detail}</p>
                  </div>
                  <div className="ask-row-sources">
                    {row.evidence_ids.slice(0, 3).map((id) => {
                      const citation = answer.citations.find(
                        (c) => c.id === id,
                      );
                      return (
                        citation && (
                          <button
                            key={id}
                            className="text-button"
                            onClick={() => onSource(citation.source_id)}
                            title={citation.excerpt}
                          >
                            {citation.source_id} [{citation.start}–
                            {citation.end}]<ArrowUpRight size={12} />
                          </button>
                        )
                      );
                    })}
                  </div>
                </li>
              ))}
            </ol>
          )}
          {!!answer.citations.length && (
            <details className="ask-citations">
              <summary>
                Exact source citations · {answer.citations.length}
              </summary>
              <p>
                Spans are zero-based, end-exclusive in the named source field.
                Source hashes and quoted spans were checked for this answer.
              </p>
              {answer.citations.map((c) => (
                <div key={c.id} className="ask-citation">
                  <button
                    className="text-button"
                    onClick={() => onSource(c.source_id)}
                  >
                    {c.source_id}
                    <ArrowUpRight size={13} />
                  </button>
                  <span className="mono">
                    {c.anchor_field}[{c.start}:{c.end}]
                  </span>
                  <blockquote>{c.excerpt}</blockquote>
                  {c.context && <p>{c.context}</p>}
                  <code>SHA-256 {c.source_sha256}</code>
                </div>
              ))}
            </details>
          )}
          {!!answer.query_trace.length && (
            <details className="ask-query-proof">
              <summary>
                Cypher &amp; parameters · {answer.query_trace.length} read-only
                queries · {answer.query_ms} ms
              </summary>
              <p>
                Executed with GRAPH.RO_QUERY. Answer rows are shown above; each
                query below has its own raw row count and client-measured
                duration, including database round trips.
              </p>
              {answer.query_trace.map((q, i) => (
                <div className="ask-query" key={i}>
                  <strong>{q.query_id}</strong>
                  <span className="mono">
                    {q.row_count} rows · {q.elapsed_ms} ms
                  </span>
                  <pre>{q.cypher}</pre>
                  <pre aria-label={q.query_id + " parameters"}>
                    {JSON.stringify(q.params, null, 2)}
                  </pre>
                </div>
              ))}
            </details>
          )}
          {answer.status === "unsupported" && (
            <p className="caption">No query was run. No answer was guessed.</p>
          )}
        </div>
      )}
    </section>
  );
}
