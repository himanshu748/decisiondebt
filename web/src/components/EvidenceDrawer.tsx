import { ArrowUpRight, FileText, ShieldCheck } from "lucide-react";
import type { Impact, Claim } from "../types";
export default function EvidenceDrawer({
  item,
  claims,
  onSource,
  loading,
}: {
  item: Impact | undefined;
  claims: Claim[];
  onSource: (id: string) => void;
  loading: boolean;
}) {
  if (!item)
    return (
      <aside className="evidence-rail">
        <h3>Select an affected service</h3>
        <p>
          Choose a node to inspect its live dependency path and source evidence.
        </p>
      </aside>
    );
  return (
    <aside className="evidence-rail">
      <div className="rail-label">
        SELECTED SERVICE <ArrowUpRight size={15} />
      </div>
      <h3>{item.name}</h3>
      <div className="inline-tags">
        <span className={"priority " + item.priority}>{item.priority}</span>
        <span className="muted">Score {item.score} / 100</span>
      </div>
      <div className="rail-section">
        <span className="small-label">WHY IT IS AFFECTED</span>
        <div className="path">
          {item.paths[0].map((id, i) => (
            <div key={i}>
              <span className="path-dot" />
              {id.replace("svc-", "").replaceAll("-", " ")}
              {i < item.paths[0].length - 1 && <small>depends on</small>}
            </div>
          ))}
        </div>
        <p className="caption">
          Depth {item.depth} · {item.alternative_path_count} verified path
          {item.alternative_path_count === 1 ? "" : "s"}
        </p>
      </div>
      <div className="rail-section">
        <span className="small-label">PRIMARY OWNERSHIP</span>
        <p
          className={
            item.owner_status === "single_primary" ? "" : "warning-text"
          }
        >
          {item.owner_status === "unowned"
            ? "Unassigned. No verified primary owner."
            : item.owner_status === "conflict"
              ? "Needs owner resolution"
              : item.ownership_claims[0]?.name}
        </p>
        {item.owner_status === "conflict" && (
          <p className="caption">
            {item.ownership_claims.map((o) => o.name).join(" / ")}
          </p>
        )}
      </div>
      <div className="rail-section">
        <span className="small-label">SOURCE PROOF</span>
        {loading ? (
          <p role="status">Reading claim anchors…</p>
        ) : (
          claims.map((c) => (
            <button
              key={c.id}
              className="proof"
              onClick={() => onSource(c.source_id)}
            >
              <span>
                <FileText size={14} />
                {c.source_id}
                <ArrowUpRight size={13} />
              </span>
              <q>{c.excerpt}</q>
              <small>
                <ShieldCheck size={12} />
                Exact span verified · {c.method}
              </small>
            </button>
          ))
        )}
      </div>
    </aside>
  );
}
