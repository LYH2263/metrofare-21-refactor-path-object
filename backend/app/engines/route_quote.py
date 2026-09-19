"""询价编排：先寻路得到路径对象，再拿路径对象的站数去票价表取价。

本文件只做编排：BFS 在 graph_bfs，按档取价在 fare_rules，
不在此处重扫邻接表临时数 hop。
"""
from app.engines.fare_rules import fare_for_hops
from app.engines.graph_bfs import shortest_path


def _canonical(a: str, b: str) -> tuple[str, str]:
    return tuple(sorted((a, b)))


def quote_route(
    edges: list[tuple[str, str]],
    start: str,
    end: str,
    rules: list[dict],
    blocked_edges: list[tuple[str, str]] | None = None,
) -> dict:
    blocked = blocked_edges or []
    blocked_set = {_canonical(a, b) for a, b in blocked}

    path = shortest_path(edges, start, end, blocked_edges=blocked)
    if path is None:
        return {
            "start": start,
            "end": end,
            "hops": None,
            "fare": None,
            "reachable": False,
            "path": None,
            "detoured": False,
            "avoided_edges": [],
            "blocked_edges": [{"a": a, "b": b} for a, b in sorted(blocked_set)],
        }

    # 站数只取自路径对象，绝不另扫邻接表。
    hops = path.hops
    fare = fare_for_hops(hops, rules)

    # 点名真正绕开的边：无中断最短路本来会经过、却被屏蔽的边。
    clear_path = shortest_path(edges, start, end)
    clear_edges = (
        {_canonical(x, y) for x, y in zip(clear_path.stations, clear_path.stations[1:])}
        if clear_path is not None
        else set()
    )
    avoided = sorted({"a": a, "b": b} for a, b in blocked_set if (a, b) in clear_edges)
    return {
        "start": start,
        "end": end,
        "hops": hops,
        "fare": fare,
        "reachable": True,
        "path": list(path.stations),
        "detoured": bool(avoided),
        "avoided_edges": avoided,
        "blocked_edges": [{"a": a, "b": b} for a, b in sorted(blocked_set)],
    }
