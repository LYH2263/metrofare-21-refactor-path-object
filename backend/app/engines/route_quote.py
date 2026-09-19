from app.engines.fare_rules import fare_for_hops
from app.engines.graph_bfs import edge_key, path_edges, shortest_path


def quote_route(
    edges: list[tuple[str, str]],
    start: str,
    end: str,
    rules: list[dict],
    blocked_edges=(),
) -> dict:
    """先寻路拿到路径对象（途经站序列+站数），再拿站数去票价表取价。

    blocked_edges 为生效中的区间中断（无向边），寻路时剔除；
    回包点名真正落在原最短路上的中断边。
    """
    blocked = {edge_key(a, b) for a, b in blocked_edges}
    original = shortest_path(edges, start, end)
    if not blocked or original is None:
        path = original
    else:
        path = shortest_path(edges, start, end, blocked_edges=blocked)
    culprits = sorted(path_edges(original) & blocked) if original else []
    named = [{"a": a, "b": b} for a, b in culprits]
    if path is None:
        return {
            "start": start, "end": end, "reachable": False,
            "path": None, "hops": None, "fare": None,
            "detoured": False, "avoided_edges": [], "blocked_edges": named,
        }
    return {
        "start": start, "end": end, "reachable": True,
        "path": path.stations, "hops": path.hops,
        "fare": fare_for_hops(path.hops, rules),
        "detoured": bool(named),
        "avoided_edges": named,
        "blocked_edges": named,
    }
