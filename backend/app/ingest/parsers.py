import hashlib
import json
import re
from pathlib import Path
from backend.app.domain.models import Source

ID = re.compile(r"^[a-z][a-z0-9-]{2,79}$")


def parse(kind, raw):
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    if len(raw.encode()) > 65536:
        raise ValueError("Source exceeds 64 KiB")
    if kind == "doc":
        match = re.match(r"\A---\n(.*?)\n---\n(.*)\Z", raw, re.S)
        if not match:
            raise ValueError("Markdown requires front matter")
        meta = {}
        for line in match[1].splitlines():
            k, sep, v = line.partition(":")
            if not sep or k in meta:
                raise ValueError("Malformed/duplicate metadata")
            meta[k] = v.strip()
        body = match[2]
    elif kind in ("ticket", "chat"):
        meta = json.loads(raw)
        if not isinstance(meta, dict):
            raise ValueError("Source must be an object")
        body = meta.get("body", "")
    else:
        raise ValueError("kind must be doc, ticket or chat")
    for field in ("id", "title", "author_id", "created_at"):
        if not isinstance(meta.get(field), str) or not meta[field]:
            raise ValueError(f"Missing {field}")
    if not ID.fullmatch(meta["id"]) or not ID.fullmatch(meta["author_id"]):
        raise ValueError("Invalid stable ID")
    if not isinstance(body, str) or not body.strip():
        raise ValueError("Missing body")
    from datetime import datetime

    dt = datetime.fromisoformat(meta["created_at"])
    if dt.tzinfo is None:
        raise ValueError("Timezone required")
    return Source(
        id=meta["id"],
        kind=kind,
        title=meta["title"],
        body=body,
        raw_text=raw,
        sha256=hashlib.sha256(raw.encode()).hexdigest(),
        created_at=meta["created_at"],
        author_id=meta["author_id"],
        last_reviewed_at=meta.get("last_reviewed_at", ""),
        metadata=meta,
    )


def load_directory(directory, allowed):
    directory = Path(directory).resolve()
    allowed = Path(allowed).resolve()
    if not directory.is_relative_to(allowed):
        raise ValueError("CLI path must be inside synthetic raw directory")
    result = []
    seen = set()
    for path in sorted(directory.rglob("*")):
        if not path.is_file():
            continue
        if not path.resolve().is_relative_to(allowed):
            raise ValueError("Source symlink leaves corpus directory")
        kind = {".md": "doc", ".json": "ticket", ".jsonl": "chat"}.get(path.suffix)
        if not kind:
            continue
        contents = path.read_text(encoding="utf-8")
        chunks = contents.splitlines() if kind == "chat" else [contents]
        for raw in chunks:
            if not raw.strip():
                continue
            src = parse(kind, raw)
            if src.id in seen:
                raise ValueError("Duplicate source ID " + src.id)
            seen.add(src.id)
            result.append(src)
    return result
