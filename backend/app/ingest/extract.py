import hashlib
import re
from backend.app.domain.models import Claim
from backend.app.ingest.verify import verify

UNCERTAIN = re.compile(
    r"\b(i think|probably|maybe|may|might|could|no longer|not|never|doesn.t)\b", re.I
)


def extract(source, catalog):
    claims = []
    revision = (
        "rev-" + hashlib.sha256((source.id + source.sha256).encode()).hexdigest()[:24]
    )

    def add(rel, a, b, start, end, field="body", uncertainty=""):
        text = getattr(source, field)
        key = f"{revision}:{rel}:{a}:{b}:{field}:{start}:{end}"
        c = Claim(
            id="claim-" + hashlib.sha256(key.encode()).hexdigest()[:24],
            relation=rel,
            subject_id=a,
            object_id=b,
            source_id=source.id,
            source_revision_id=revision,
            anchor_field=field,
            start=start,
            end=end,
            excerpt=text[start:end],
            method="metadata" if field == "raw_text" else "explicit_rule",
            status="candidate" if uncertainty else "verified",
            uncertainty=uncertainty,
            confidence=0.4 if uncertainty else 1,
        )
        if c.status == "verified" and not verify(c, source, catalog):
            c.status = "candidate"
            c.uncertainty = "invalid_anchor_or_entity"
        claims.append(c)

    # Capture entire sentences, including any hedge preceding the subject.
    for sent in re.finditer(r"[^.!?\n]+[.!?]?", source.body):
        text = sent[0]
        mentions = catalog.mentions(text)
        uncertain = UNCERTAIN.search(text)
        uncertainty = uncertain[0].casefold() if uncertain else ""
        for (ma, aa), (mb, bb) in zip(mentions, mentions[1:]):
            between = text[ma.end() : mb.start()].strip().casefold()
            a = next(iter(aa)) if len(aa) == 1 else sorted(aa)[0]
            b = next(iter(bb)) if len(bb) == 1 else sorted(bb)[0]
            la = catalog.by_id[a]["label"]
            lb = catalog.by_id[b]["label"]
            rel = None
            if (
                la == "Service"
                and lb == "Service"
                and re.fullmatch(
                    r"(?:no longer |does not |maybe |may |might )?(depends? on|calls?|uses?|depend on)",
                    between,
                )
            ):
                rel = "DEPENDS_ON"
            elif (
                la == "Person"
                and lb == "Service"
                and re.fullmatch(r"(?:probably |maybe )?owns", between)
            ):
                rel = "OWNS"
            elif (
                la == "Service"
                and lb == "Person"
                and between in ("is owned by", "is probably owned by")
            ):
                rel = "OWNS"
                a, b = b, a
            elif la == "Project" and lb == "Service" and between == "uses":
                rel = "USES"
            elif la == "Person" and lb == "Team" and between == "is a member of":
                rel = "MEMBER_OF"
            elif la == "Decision" and lb == "Service" and between == "changes service":
                rel = "CHANGES"
            if rel:
                add(
                    rel,
                    a,
                    b,
                    sent.start(),
                    sent.end(),
                    uncertainty=uncertainty
                    or ("ambiguous_alias" if len(aa) != 1 or len(bb) != 1 else ""),
                )
        for m, ids in mentions:
            if len(ids) != 1:
                continue
            ident = next(iter(ids))
            label = catalog.by_id[ident]["label"]
            prefix = text[: m.start()].strip().casefold()
            if label == "Service" and prefix == "this document describes":
                add(
                    "DESCRIBES",
                    source.id,
                    ident,
                    sent.start(),
                    sent.end(),
                    uncertainty=uncertainty,
                )
            if label == "Decision" and re.search(r"follows decision\s*$", prefix):
                add(
                    "REFERENCES",
                    source.id,
                    ident,
                    sent.start(),
                    sent.end(),
                    uncertainty=uncertainty,
                )
    # Anchor the metadata field itself, rather than a coincidental author name in body text.
    pattern = (
        r"(?m)^author_id:\s*" + re.escape(source.author_id) + r"\s*$"
        if source.kind == "doc"
        else r'"author_id"\s*:\s*"' + re.escape(source.author_id) + r'"'
    )
    anchor = re.search(pattern, source.raw_text)
    if anchor:
        add(
            "AUTHORED",
            source.author_id,
            source.id,
            anchor.start(),
            anchor.end(),
            "raw_text",
        )
    return claims
