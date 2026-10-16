"""Independent graph traversal, available only to tests."""

from collections import deque


def bfs(relations, root, max_hops=5):
    incoming = {}
    for predicate, a, b in relations:
        if predicate == "DEPENDS_ON":
            incoming.setdefault(b, set()).add(a)
    depth = {root: 0}
    queue = deque([root])
    while queue:
        p = queue.popleft()
        if depth[p] >= max_hops:
            continue
        for c in incoming.get(p, []):
            if c not in depth:
                depth[c] = depth[p] + 1
                queue.append(c)
    return depth
