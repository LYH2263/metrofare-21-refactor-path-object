from collections import defaultdict, deque
from dataclasses import dataclass


@dataclass(frozen=True)
class RoutePath:
    """寻路结果：途经站序列（含起终点）与站数。不可达时不产生该对象。"""

    stations: tuple[str, ...]

    @property
    def hops(self) -> int:
        """站数 = 途经边数 = 序列长度 - 1（同站为 0）。"""
        return len(self.stations) - 1


def _canonical(a: str, b: str) -> tuple[str, str]:
    return tuple(sorted((a, b)))


def shortest_path(
    edges: list[tuple[str, str]],
    start: str,
    end: str,
    blocked_edges: list[tuple[str, str]] | None = None,
) -> RoutePath | None:
    """无向图 BFS 最短路，返回含途经站序列的路径对象；不可达返回 None。

    blocked_edges 中的邻接边（无向，方向自动归一化）不参与寻路。
    """
    if start == end:
        return RoutePath((start,))

    blocked = {_canonical(a, b) for a, b in (blocked_edges or [])}
    g: dict[str, set[str]] = defaultdict(set)
    for a, b in edges:
        if _canonical(a, b) in blocked:
            continue
        g[a].add(b)
        g[b].add(a)
    if start not in g or end not in g:
        return None

    parent: dict[str, str | None] = {start: None}
    q: deque[str] = deque([start])
    while q:
        cur = q.popleft()
        if cur == end:
            break
        for nxt in g[cur]:
            if nxt not in parent:
                parent[nxt] = cur
                q.append(nxt)

    if end not in parent:
        return None
    trail: list[str] = []
    node: str | None = end
    while node is not None:
        trail.append(node)
        node = parent[node]
    return RoutePath(tuple(reversed(trail)))
