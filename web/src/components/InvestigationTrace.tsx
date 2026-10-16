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
  return (
    <div className="trace">
      <div className="trace-intro">
        <span className="badge">
          {run.mode === "llm" ? "Recorded LLM" : "Deterministic rule run"}
        </span>
        <span className="mono">{run.model}</span>
        <span>
          {run.tool_calls} tools · revision {run.graph_revision} · {run.status}
        </span>
      </div>
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
