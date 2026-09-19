from app.db import connect
from app.engines.route_quote import quote_route
from app.repositories import disruptions as disruptions_repo
from app.repositories import edges as edges_repo
from app.repositories import fare_rules as rules_repo
from app.repositories import runs as runs_repo
from app.repositories import settings as settings_repo
from app.repositories import stations as stations_repo


class MetroService:
    def __init__(self):
        self._conn = connect()

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()

    def stations(self):
        return stations_repo.list_all(self._conn)

    def station(self, code: str):
        return stations_repo.get_by_code(self._conn, code)

    def edges(self):
        return [{"a": a, "b": b} for a, b in edges_repo.list_pairs(self._conn)]

    def fare_rules(self):
        return rules_repo.list_ordered(self._conn)

    def settings(self):
        return settings_repo.get_map(self._conn)

    def disruptions(self):
        return disruptions_repo.list_active(self._conn)

    def create_disruption(self, a: str, b: str, reason: str):
        return disruptions_repo.create(self._conn, a, b, reason)

    def release_disruption(self, disruption_id: int):
        return disruptions_repo.release(self._conn, disruption_id)

    def quote(self, start: str, end: str, persist: bool):
        edges = edges_repo.list_pairs(self._conn)
        rules = rules_repo.as_calc_rules(self._conn)
        # 生效中断作为屏蔽边交给寻路；service 自己不扫邻接表、不临时数 hop。
        active = disruptions_repo.list_active(self._conn)
        blocked = [(d["a"], d["b"]) for d in active]
        result = quote_route(edges, start, end, rules, blocked_edges=blocked)
        reasons = {(d["a"], d["b"]): d.get("reason", "") for d in active}
        result["blocked_edges"] = [
            {**e, "reason": reasons.get((e["a"], e["b"]), "")}
            for e in result["blocked_edges"]
        ]
        run_id = None
        if persist and result.get("reachable"):
            run_id = runs_repo.insert(self._conn, "quote", {"start": start, "end": end}, result)
        return {"run_id": run_id, **result}

    def history(self, limit=50):
        return runs_repo.list_recent(self._conn, limit)

    def dashboard(self):
        st = stations_repo.list_all(self._conn)
        clean = [s for s in st if "种子" not in s["name"]]
        dirty = [s for s in st if "种子" in s["name"]]
        return {
            "station_count": len(st),
            "edge_count": len(edges_repo.list_pairs(self._conn)),
            "clean_stations": len(clean),
            "dirty_stations": len(dirty),
        }
