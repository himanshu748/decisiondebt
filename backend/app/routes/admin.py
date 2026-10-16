import uuid
from datetime import datetime, timezone
from backend.app.graph.client import LOCK, DomainError


def approval(g, target, action):
    ident = "approval-" + uuid.uuid4().hex
    props = dict(
        id=ident,
        actor="local-admin",
        at=datetime.now(timezone.utc).isoformat(),
        target_id=target,
        action=action,
    )
    g.write("CREATE (e:ApprovalEvent) SET e += $props", {"props": props})
    return ident


def accept(g, ident, confirmed):
    if not confirmed:
        raise DomainError(
            "CONFIRM_REQUIRED", "Confirm decision acceptance explicitly", 409
        )
    with LOCK:
        rows = g.read(
            "MATCH (d:Decision {id:$id}) RETURN d.status AS status,d.proposed_supersedes_id AS old_id",
            {"id": ident},
        )
        if not rows:
            raise DomainError("NOT_FOUND", "Unknown decision", 404)
        d = rows[0]
        if d["status"] != "proposed":
            raise DomainError(
                "INVALID_DECISION_STATE", "Only a proposal may be accepted", 409
            )
        if not g.read(
            "MATCH (d:Decision {id:$id,status:'accepted'}) RETURN d.id AS id",
            {"id": d["old_id"]},
        ):
            raise DomainError(
                "INVALID_DECISION_STATE", "Previous accepted decision missing", 409
            )
        aid = approval(g, ident, "accept_decision")
        g.write(
            "MATCH (d:Decision {id:$id}),(old:Decision {id:$old}) SET d.status='accepted' MERGE (d)-[:SUPERSEDES {approval_id:$approval}]->(old)",
            {"id": ident, "old": d["old_id"], "approval": aid},
        )
        g.bump()
        return dict(
            id=ident, status="accepted", approval_id=aid, graph_revision=g.revision()
        )


def approve_task(g, ident, confirmed):
    if not confirmed:
        raise DomainError("CONFIRM_REQUIRED", "Confirm local task approval", 409)
    with LOCK:
        rows = g.read(
            "MATCH (t:Task {id:$id}) RETURN t.status AS status", {"id": ident}
        )
        if not rows:
            raise DomainError("NOT_FOUND", "Unknown task", 404)
        if rows[0]["status"] == "approved":
            return dict(id=ident, status="approved", graph_revision=g.revision())
        aid = approval(g, ident, "approve_task")
        g.write("MATCH (t:Task {id:$id}) SET t.status='approved'", {"id": ident})
        g.bump()
        return dict(
            id=ident, status="approved", approval_id=aid, graph_revision=g.revision()
        )
