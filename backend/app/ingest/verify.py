RELATIONS = {
    "DEPENDS_ON": ("Service", "Service"),
    "OWNS": ("Person", "Service"),
    "USES": ("Project", "Service"),
    "MEMBER_OF": ("Person", "Team"),
    "AUTHORED": ("Person", "Source"),
    "DESCRIBES": ("Source", "Service"),
    "REFERENCES": ("Source", "Decision"),
    "CHANGES": ("Decision", "Service"),
}


def verify(claim, source, catalog):
    text = (
        getattr(source, claim.anchor_field, None)
        if claim.anchor_field in ("body", "raw_text")
        else None
    )
    if (
        text is None
        or claim.start < 0
        or claim.end <= claim.start
        or text[claim.start : claim.end] != claim.excerpt
    ):
        return False
    labels = RELATIONS.get(claim.relation)
    if not labels:
        return False
    for ident, label in zip([claim.subject_id, claim.object_id], labels):
        if label == "Source":
            if ident != source.id:
                return False
        elif catalog.by_id.get(ident, {}).get("label") != label:
            return False
    return claim.status == "verified" and not claim.uncertainty
