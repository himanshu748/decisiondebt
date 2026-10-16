import { Check, ArrowUpRight, UserRound } from "lucide-react";
import { useState } from "react";
import type { Task } from "../types";
export default function ActionBoard({
  tasks,
  onApprove,
  onEvidence,
  admin,
  busy,
}: {
  tasks: Task[];
  onApprove: (id: string) => void;
  onEvidence: (id: string) => void;
  admin: boolean;
  busy: boolean;
}) {
  const [history, setHistory] = useState(false);
  const latestRevision = Math.max(0, ...tasks.map((t) => t.analysis_revision));
  const visibleTasks = history
    ? tasks
    : tasks.filter((t) => t.analysis_revision === latestRevision);
  if (!tasks.length)
    return (
      <div className="empty">
        <Check />
        <h3>No proposed actions yet.</h3>
        <p>
          Run an investigation from Preview. Only evidence-backed local drafts
          appear here.
        </p>
      </div>
    );
  return (
    <div>
      <div className="action-scope">
        <span>
          {visibleTasks.length} actions ·{" "}
          {history
            ? "All recorded analyses"
            : `Analysis revision ${latestRevision}`}
        </span>
        <label>
          <span className="sr-only">Action history</span>
          <select
            aria-label="Action history"
            value={history ? "all" : "latest"}
            onChange={(e) => setHistory(e.target.value === "all")}
          >
            <option value="latest">Latest analysis</option>
            <option value="all">All history ({tasks.length})</option>
          </select>
        </label>
      </div>
      <div className="action-grid">
        {visibleTasks.map((t) => (
          <article className="task-card" key={t.id}>
            <div className="between">
              <span className={"priority " + t.priority}>{t.priority}</span>
              <span className="mono">{t.service_id.replace("svc-", "")}</span>
              <span className="badge">{t.status}</span>
            </div>
            <h3>{t.title}</h3>
            <p>{t.reason}</p>
            <div className="task-owner">
              <UserRound size={14} />
              {t.owner_id ||
                (t.owner_status === "conflict"
                  ? "Needs owner resolution"
                  : "Unassigned")}
            </div>
            <p className="caption">
              Analysis revision {t.analysis_revision} · Score {t.score}
            </p>
            <div className="task-footer">
              <button
                className="text-button"
                onClick={() => onEvidence(t.evidence_ids[0])}
              >
                Inspect evidence <ArrowUpRight size={14} />
              </button>
              {t.status !== "approved" && (
                <button
                  className="button small"
                  disabled={!admin || busy}
                  onClick={() => onApprove(t.id)}
                >
                  Approve locally
                </button>
              )}
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
