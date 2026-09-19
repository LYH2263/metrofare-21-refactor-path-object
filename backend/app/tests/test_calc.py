import pytest

import app.db as db_mod
from app import seed
from app.engines.fare_rules import fare_for_hops
from app.engines.graph_bfs import shortest_hops, shortest_path
from app.engines.route_quote import quote_route
from app.services.metro_service import MetroService

EDGES = [("A1", "A2"), ("A2", "A3"), ("A2", "B1"), ("B1", "B2")]
RULES = [{"max_hops": 2, "price": 3.0}, {"max_hops": 4, "price": 4.0}, {"max_hops": None, "price": 6.0}]


@pytest.fixture
def svc(tmp_path, monkeypatch):
    monkeypatch.setattr(db_mod, "DB_PATH", tmp_path / "test.db")
    seed.init_db()
    with MetroService() as s:
        yield s


def test_hops_a1_a3():
    assert shortest_hops(EDGES, "A1", "A3") == 2


def test_hops_a1_b2():
    assert shortest_hops(EDGES, "A1", "B2") == 3


def test_fare_by_hops():
    assert fare_for_hops(2, RULES) == 3.0
    assert fare_for_hops(3, RULES) == 4.0
    assert fare_for_hops(10, RULES) == 6.0


def test_quote():
    q = quote_route(EDGES, "A1", "B2", RULES)
    assert q["hops"] == 3 and q["fare"] == 4.0


# ---------- 路径对象 ----------

def test_path_same_station_single_code_zero_hops():
    # 同站：途经站序列只有起点一个编码，站数为 0
    p = shortest_path(EDGES, "A1", "A1")
    assert p is not None
    assert p.stations == ["A1"]
    assert p.hops == 0


def test_path_unreachable_has_no_path_object():
    # 不可达：没有路径对象
    assert shortest_path(EDGES, "A1", "ZZ") is None


def test_path_a1_b2_sequence_length_4():
    # A1 到 B2：途经站序列长度 4，站数 3
    p = shortest_path(EDGES, "A1", "B2")
    assert p is not None
    assert p.stations == ["A1", "A2", "B1", "B2"]
    assert len(p.stations) == 4
    assert p.hops == 3


# ---------- 种子数据询价不变量 ----------

def test_seed_city_to_airport_3_hops_fare_4(svc):
    # 城站 → 机场：3 站，票价 4.0
    q = svc.quote("A1", "B2", persist=False)
    assert q["reachable"] is True
    assert q["hops"] == 3 and q["fare"] == 4.0


def test_seed_city_to_east_bay_2_hops_fare_3(svc):
    # 城站 → 东湾：2 站，票价 3.0
    q = svc.quote("A1", "A3", persist=False)
    assert q["reachable"] is True
    assert q["hops"] == 2 and q["fare"] == 3.0
