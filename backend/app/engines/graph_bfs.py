from collections import defaultdict, deque
from typing import NamedTuple


class Path(NamedTuple):
    """一条最短路径：途经站序列（含起终点）和站数。"""

    stations: list[str]
    hops: int


def edge_key(a: str, b: str) -> tuple[str, str]:
    """无向边的规范键：两端编码排序，正反方向同键。"""
    return tuple(sorted((a, b)))


def path_edges(path: Path) -> set[tuple[str, str]]:
    """路径对象途经的无向边（规范键）集合。"""
    seq = path.stations
    return {edge_key(a, b) for a, b in zip(seq, seq[1:])}


def shortest_path(
    edges: list[tuple[str, str]],
    start: str,
    end: str,
    blocked_edges=(),
) -> Path | None:
    """无向图 BFS 最短路径对象；不可达返回 None。blocked_edges 中的边不参与寻路。"""
    if start == end:
        return Path([start], 0)
    g: dict[str, set[str]] = defaultdict(set)
    for a, b in edges:
        g[a].add(b)
        g[b].add(a)
    if start not in g or end not in g:
        return None
    blocked = {edge_key(a, b) for a, b in blocked_edges}
    prev: dict[str, str | None] = {start: None}
    q = deque([start])
    while q:
        cur = q.popleft()
        for nxt in sorted(g[cur]):
            if nxt in prev or edge_key(cur, nxt) in blocked:
                continue
            prev[nxt] = cur
            if nxt == end:
                seq = [end]
                while prev[seq[-1]] is not None:
                    seq.append(prev[seq[-1]])
                seq.reverse()
                return Path(seq, len(seq) - 1)
            q.append(nxt)
    return None


def shortest_hops(edges: list[tuple[str, str]], start: str, end: str) -> int | None:
    """兼容旧接口：只取站数。寻路统一走 shortest_path 拿路径对象。"""
    p = shortest_path(edges, start, end)
    return None if p is None else p.hops
