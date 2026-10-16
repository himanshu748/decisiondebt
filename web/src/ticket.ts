import type { Task } from "./types";

export function ticketMarkdown(task: Task, origin: string) {
  const owner =
    task.owner_status === "single_primary" && task.owner_id
      ? task.owner_id
      : "unassigned: needs decision";
  const evidence = task.evidence_ids
    .map((id) => {
      const path = id.startsWith("mention:")
        ? "/api/sources/" + encodeURIComponent(id.split(":")[1])
        : "/api/claims/" + encodeURIComponent(id);
      return `- [${id}](${origin}${path})`;
    })
    .join("\n");
  return (
    `# ${task.title.replace(/[\r\n]+/g, " ")}\n\n` +
    `Draft task: ${task.id}\nAnalysis revision: ${task.analysis_revision}\nPriority: ${task.priority}\n\n` +
    `## Why\n\n${task.reason}\n\n## Suggested owner\n\n${owner}\n\n` +
    `## Evidence\n\n${evidence || "No evidence links recorded."}\n\n` +
    `## Uncertainty\n\n${task.uncertainty || "Review the source assertions before assigning work."}\n\n` +
    `Exported from [DecisionDebt Action Board](${origin}/studio?tab=Action%20Board). ` +
    `This is a local draft export; no ticket was created and no graph state changed.\n`
  );
}

export function downloadTicket(task: Task) {
  const url = URL.createObjectURL(
    new Blob([ticketMarkdown(task, window.location.origin)], {
      type: "text/markdown;charset=utf-8",
    }),
  );
  const link = document.createElement("a");
  link.href = url;
  link.download = `decisiondebt-${task.id.replace(/[^a-zA-Z0-9_-]/g, "-")}.md`;
  link.click();
  // Allow the browser to finish starting the download before releasing the Blob.
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}
