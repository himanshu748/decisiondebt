import { Check, ArrowUpRight, UserRound, Copy, Download } from "lucide-react";
import { useState } from "react";
import type { Task } from "../types";
import { PUBLIC_WRITE_REASON } from "../deployment";
import { ticketMarkdown, downloadTicket } from "../ticket";
export default function ActionBoard({
  tasks,
  onApprove,
  onEvidence,
  admin,
  publicReadOnly = false,
  busy,
}: {
  tasks: Task[];
  onApprove: (id: string) => void;
  onEvidence: (id: string) => void;
  admin: boolean;
  publicReadOnly?: boolean;
  busy: boolean;
}) {
  const [history, setHistory] = useState(false);
  const [feedback, setFeedback] = useState<Record<string, string>>({});
  async function copyTicket(task: Task) {
    try {
      await navigator.clipboard.writeText(
        ticketMarkdown(task, window.location.origin),
      );
      setFeedback((f) => ({
        ...f,
        [task.id]: "Ticket copied. No external ticket was created.",
      }));
    } catch {
      setFeedback((f) => ({
        ...f,
        [task.id]: "Clipboard unavailable. Download the .md file instead.",
      }));
    }
  }
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
          <article className="task-card" data-task-id={t.id} key={t.id}>
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
                  title={publicReadOnly ? PUBLIC_WRITE_REASON : undefined}
                  aria-describedby={
                    publicReadOnly ? "public-write-reason" : undefined
                  }
                  onClick={() => onApprove(t.id)}
                >
                  Approve locally
                </button>
              )}
            </div>
            {t.status !== "approved" && (
              <div
                className="ticket-exports"
                aria-label={"Export draft: " + t.title}
              >
                <button
                  className="text-button"
                  onClick={() => void copyTicket(t)}
                >
                  <Copy size={13} /> Copy as ticket
                </button>
                <button
                  className="text-button"
                  onClick={() => downloadTicket(t)}
                >
                  <Download size={13} /> Download .md
                </button>
              </div>
            )}
            {feedback[t.id] && (
              <p className="ticket-feedback" role="status">
                {feedback[t.id]}
              </p>
            )}
          </article>
        ))}
      </div>
    </div>
  );
}
