import { Check, ArrowUpRight, UserRound } from "lucide-react";
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
    <div className="action-columns">
      {["P0", "P1", "P2"].map((p) => (
        <section key={p}>
          <div className="column-head">
            <span className={"priority " + p}>{p}</span>
            <span>{tasks.filter((t) => t.priority === p).length} actions</span>
          </div>
          {tasks
            .filter((t) => t.priority === p)
            .map((t) => (
              <article className="task-card" key={t.id}>
                <div className="between">
                  <span className="mono">
                    {t.service_id.replace("svc-", "")}
                  </span>
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
        </section>
      ))}
    </div>
  );
}
