import { Check, ChevronDown, CornerDownRight } from "lucide-react";
import type { Run } from "../types";
export default function InvestigationTrace({ run }: { run: Run | null }) {
  if (!run)
    return (
      <div className="empty">
        <CornerDownRight />
        <h3>Let the evidence guide the next step.</h3>
        <p>
          Run an investigation to review missing owners, conflicting claims, and
          suspected document drift.
        </p>
      </div>
    );
  const providerRun = run.execution_kind === "llm" && run.provider_verified;
  const caseLabels: Record<string, string> = {
    unowned: "Missing owner",
    conflicting_owners: "Conflicting owners",
    unlinked_mention: "Unlinked mention",
  };
  return (
    <div className="trace">
      <div className="trace-intro">
        <span className="badge">
          {providerRun
            ? "Recorded provider run"
            : run.execution_kind === "mocked_test"
              ? "Mocked test run"
              : "Deterministic rule run"}
        </span>
        <span className="mono">{run.model}</span>
        <span>
          {run.tool_calls} tools · revision {run.graph_revision} · {run.status}
        </span>
      </div>
      {run.coverage && (
        <div
          className="trace-coverage"
          aria-label="Ambiguity investigation coverage"
        >
          {Object.entries(run.coverage.cases).map(([key, value]) => (
            <div key={key}>
              <span
                className={value.passed ? "coverage-pass" : "coverage-pending"}
              >
                {value.passed ? (
                  <Check size={13} />
                ) : (
                  <CornerDownRight size={13} />
                )}
                {value.passed ? "Evidence checked" : "Investigation incomplete"}
              </span>
              <strong>{caseLabels[key] || key}</strong>
              <small className="mono">{value.target_id}</small>
            </div>
          ))}
        </div>
      )}
      {run.trace.map((t, i) => (
        <details key={i} className="trace-step">
          <summary>
            <span className="step-index">{String(i + 1).padStart(2, "0")}</span>
            <div>
              <strong>
                {t.tool?.replaceAll("_", " ") || "Investigation summary"}
              </strong>
              <small>
                {t.args
                  ? Object.values(t.args)
                      .filter((v) => typeof v === "string")
                      .slice(0, 2)
                      .join(" · ")
                  : t.model_summary || t.message}
              </small>
            </div>
            {t.status === "ok" ? <Check size={15} /> : <span>{t.status}</span>}
            <ChevronDown size={15} />
          </summary>
          <pre>{JSON.stringify(t, null, 2)}</pre>
        </details>
      ))}
    </div>
  );
}
