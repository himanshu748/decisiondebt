def rank(depth, criticality, owner_status, tiers):
    score = max(
        0,
        min(
            100,
            60
            - 10 * depth
            + 5 * criticality
            + 12 * (owner_status == "unowned")
            + 8 * (owner_status == "conflict")
            + 6 * (1 in tiers)
            + 4 * (2 in tiers)
            + 2 * (3 in tiers),
        ),
    )
    return score, "P0" if score >= 70 else "P1" if score >= 45 else "P2"
