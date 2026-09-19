import pytest

import app.db as db_mod
from app import seed
from app.engines.fare_rules import fare_for_hops
from app.engines.graph_bfs import shortest_path
from app.engines.route_quote import quote_route
from app.services.metro_service import MetroService

EDGES = [("A1", "A2"), ("A2", "A3"), ("A2", "B1"), ("B1", "B2")]
RULES = [{"max_hops": 2, "price": 3.0}, {"max_hops": 4, "price": 4.0}, {"max_hops": None, "price": 6.0}]


# ---------- 路径对象 ----------

def test_hops_a1_a3():
    assert shortest_path(EDGES, "A1", "A3").hops == 2


def test_path_a1_b2_sequence_len_4():
    p = shortest_path(EDGES, "A1", "B2")
    assert p.stations == ("A1", "A2", "B1", "B2")
    assert len(p.stations) == 4
    assert p.hops == 3


def test_same_station_path_single_code_zero_hops():
    p = shortest_path(EDGES, "A1", "A1")
    assert p is not None
    assert p.stations == ("A1",)
    assert len(p.stations) == 1
    assert p.hops == 0


def test_unreachable_has_no_path_object():
    # 端点不在图中：没有路径对象
    assert shortest_path(EDGES, "A1", "ZZ") is None
    # 桥边被屏蔽后 A1 到 B2 不连通：同样没有路径对象
    assert shortest_path(EDGES, "A1", "B2", blocked_edges=[("B1", "B2")]) is None


# ---------- 按档取价 ----------

def test_fare_by_hops():
    assert fare_for_hops(0, RULES) == 3.0
    assert fare_for_hops(2, RULES) == 3.0
    assert fare_for_hops(3, RULES) == 4.0
    assert fare_for_hops(10, RULES) == 6.0


# ---------- 编排：先路径对象，再按站数取价 ----------

def test_quote():
    q = quote_route(EDGES, "A1", "B2", RULES)
    assert q["reachable"] is True
    assert q["path"] == ["A1", "A2", "B1", "B2"]
    assert q["hops"] == 3 and q["fare"] == 4.0


def test_quote_same_station_uses_zero_hops():
    q = quote_route(EDGES, "A1", "A1", RULES)
    assert q["reachable"] is True
    assert q["path"] == ["A1"] and q["hops"] == 0


def test_quote_unreachable_invents_no_path():
    q = quote_route(EDGES, "A1", "B2", RULES, blocked_edges=[("B1", "B2")])
    assert q["reachable"] is False
    assert q["path"] is None and q["hops"] is None and q["fare"] is None


# ---------- 种子数据回归（不得改种子数字） ----------

@pytest.fixture
def svc(tmp_path, monkeypatch):
    monkeypatch.setattr(db_mod, "DB_PATH", tmp_path / "test.db")
    seed.init_db()
    with MetroService() as s:
        yield s


def test_seed_fares_unchanged(svc):
    # 城站(A1) → 机场(B2)：3 站，票价 4.0
    q1 = svc.quote("A1", "B2", persist=False)
    assert q1["path"] == ["A1", "A2", "B1", "B2"]
    assert q1["hops"] == 3 and q1["fare"] == 4.0
    # 城站(A1) → 东湾(A3)：2 站，票价 3.0
    q2 = svc.quote("A1", "A3", persist=False)
    assert q2["path"] == ["A1", "A2", "A3"]
    assert q2["hops"] == 2 and q2["fare"] == 3.0
