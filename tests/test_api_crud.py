"""Integration tests for CRUD API endpoints.

Uses in-memory SQLite — no PostgreSQL needed.
"""

import os
import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base

# ── 1. Build the app with SQLite ──────────────────────────────────
# StaticPool ensures all sessions share the SAME :memory: database.

os.environ["DATABASE_URL"] = "sqlite://"

from app.db import session as db_session  # noqa: E402
from app.main import create_app  # noqa: E402

TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=TEST_ENGINE)

db_session.engine = TEST_ENGINE
db_session.SessionLocal = TestingSessionLocal

app = create_app()

import app.api.funds as funds_mod  # noqa: E402
import app.api.experiment_groups as eg_mod  # noqa: E402
import app.api.experiments as exp_mod  # noqa: E402
import app.api.backtests as bt_mod  # noqa: E402
import app.api.stress_periods as sp_mod  # noqa: E402

for mod in [funds_mod, eg_mod, exp_mod, bt_mod, sp_mod]:
    mod.SessionLocal = TestingSessionLocal

client = TestClient(app)


# ── 2. Fixture: create tables before each test, drop after ────────

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)


# ═══════════════════════════════════════════════════════════════════
# Fund CRUD
# ═══════════════════════════════════════════════════════════════════

class TestFunds:
    def test_health(self):
        r = client.get("/funds/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_list_empty(self):
        r = client.get("/funds")
        assert r.status_code == 200
        assert r.json() == []

    def test_create_and_list(self):
        r = client.post("/funds", json={"fund_code": "000001", "fund_name": "测试基金"})
        assert r.status_code == 201

        r = client.get("/funds")
        assert len(r.json()) == 1
        assert r.json()[0]["fund_code"] == "000001"

    def test_create_duplicate_rejected(self):
        client.post("/funds", json={"fund_code": "000001", "fund_name": "测试基金"})
        r = client.post("/funds", json={"fund_code": "000001", "fund_name": "重复基金"})
        assert r.status_code == 409

    def test_get_single(self):
        client.post("/funds", json={"fund_code": "000002", "fund_name": "华夏成长"})
        r = client.get("/funds/000002")
        assert r.status_code == 200
        assert r.json()["fund_name"] == "华夏成长"

    def test_get_not_found(self):
        r = client.get("/funds/999999")
        assert r.status_code == 404

    def test_update(self):
        client.post("/funds", json={"fund_code": "000003", "fund_name": "原始名称", "asset_bucket": "bond"})
        r = client.put("/funds/000003", json={"fund_name": "更新名称", "asset_bucket": "gold_commodity"})
        assert r.status_code == 200

        r = client.get("/funds/000003")
        assert r.json()["fund_name"] == "更新名称"
        assert r.json()["asset_bucket"] == "gold_commodity"

    def test_update_partial(self):
        client.post("/funds", json={"fund_code": "000004", "fund_name": "部分更新", "asset_bucket": "bond"})
        r = client.put("/funds/000004", json={"fund_name": "新名字"})
        assert r.status_code == 200

        r = client.get("/funds/000004")
        assert r.json()["fund_name"] == "新名字"
        assert r.json()["asset_bucket"] == "bond"

    def test_update_not_found(self):
        r = client.put("/funds/999999", json={"fund_name": "x"})
        assert r.status_code == 404

    def test_delete(self):
        client.post("/funds", json={"fund_code": "000005", "fund_name": "待删除"})
        r = client.delete("/funds/000005")
        assert r.status_code == 200

        r = client.get("/funds/000005")
        assert r.status_code == 404

    def test_delete_referenced_fund_rejected(self):
        gid = client.post("/experiment-groups", json={"group_name": "引用测试"}).json()["experiment_group_id"]
        client.post("/funds", json={"fund_code": "REF001", "fund_name": "被引用基金"})
        client.post("/experiments", json={
            "experiment_name": "引用基金实验",
            "experiment_group_id": gid,
            "target_weights": {"REF001": 1.0},
        })

        r = client.delete("/funds/REF001")
        assert r.status_code == 409
        assert "referenced" in r.json()["detail"]

        r = client.get("/funds/REF001")
        assert r.status_code == 200

    def test_delete_not_found(self):
        r = client.delete("/funds/999999")
        assert r.status_code == 404

    def test_list_filter_by_bucket(self):
        client.post("/funds", json={"fund_code": "A001", "fund_name": "F1", "asset_bucket": "bond"})
        client.post("/funds", json={"fund_code": "A002", "fund_name": "F2", "asset_bucket": "gold_commodity"})
        r = client.get("/funds?asset_bucket=bond")
        assert len(r.json()) == 1
        assert r.json()[0]["fund_code"] == "A001"

    def test_list_filter_by_active(self):
        client.post("/funds", json={"fund_code": "B001", "fund_name": "F1"})
        client.post("/funds", json={"fund_code": "B002", "fund_name": "F2"})
        client.put("/funds/B002", json={"is_active": False})

        r = client.get("/funds?is_active=true")
        assert len(r.json()) == 1
        assert r.json()[0]["fund_code"] == "B001"


# ═══════════════════════════════════════════════════════════════════
# Experiment Group CRUD
# ═══════════════════════════════════════════════════════════════════

class TestExperimentGroups:
    def _create(self, name="测试实验组", question="研究问题", note=""):
        r = client.post("/experiment-groups", json={
            "group_name": name, "research_question": question, "note": note,
        })
        assert r.status_code == 201
        return r.json()["experiment_group_id"]

    def test_list_empty(self):
        r = client.get("/experiment-groups")
        assert r.status_code == 200
        assert r.json() == []

    def test_create_and_list(self):
        self._create("G1")
        r = client.get("/experiment-groups")
        assert len(r.json()) == 1

    def test_get_single(self):
        gid = self._create("G2", "Q2", "N2")
        r = client.get(f"/experiment-groups/{gid}")
        assert r.status_code == 200
        assert r.json()["group_name"] == "G2"

    def test_get_not_found(self):
        r = client.get(f"/experiment-groups/{uuid.uuid4()}")
        assert r.status_code == 404

    def test_update(self):
        gid = self._create("G3", "Q3")
        r = client.put(f"/experiment-groups/{gid}", json={"group_name": "G3-改", "note": "N3"})
        assert r.status_code == 200

        r = client.get(f"/experiment-groups/{gid}")
        assert r.json()["group_name"] == "G3-改"
        assert r.json()["note"] == "N3"
        assert r.json()["research_question"] == "Q3"

    def test_update_not_found(self):
        r = client.put(f"/experiment-groups/{uuid.uuid4()}", json={"group_name": "x"})
        assert r.status_code == 404

    def test_delete(self):
        gid = self._create("G4")
        r = client.delete(f"/experiment-groups/{gid}")
        assert r.status_code == 200

        r = client.get(f"/experiment-groups/{gid}")
        assert r.status_code == 404

    def test_delete_not_found(self):
        r = client.delete(f"/experiment-groups/{uuid.uuid4()}")
        assert r.status_code == 404


# ═══════════════════════════════════════════════════════════════════
# Experiment CRUD
# ═══════════════════════════════════════════════════════════════════

class TestExperiments:
    def _create_group(self, name="测试实验组"):
        r = client.post("/experiment-groups", json={"group_name": name})
        return r.json()["experiment_group_id"]

    def _create_fund(self, code="F001", name="测试基金", bucket="a_share_equity"):
        client.post("/funds", json={"fund_code": code, "fund_name": name, "asset_bucket": bucket})

    def _create_exp(self, group_id, name="测试实验", weights=None, role="main"):
        if weights is None:
            weights = {"F001": 1.0}
        r = client.post("/experiments", json={
            "experiment_name": name,
            "experiment_group_id": group_id,
            "target_weights": weights,
            "role": role,
            "rebalance_rule": "monthly",
        })
        assert r.status_code == 201
        return r.json()["experiment_id"]

    def test_list_empty(self):
        r = client.get("/experiments")
        assert r.status_code == 200
        assert r.json() == []

    def test_create_and_list(self):
        gid = self._create_group()
        self._create_fund("F001")
        self._create_exp(gid, "E1")

        r = client.get(f"/experiments?group_id={gid}")
        assert len(r.json()) == 1
        assert r.json()[0]["experiment_name"] == "E1"

    def test_create_rejects_invalid_weights(self):
        gid = self._create_group()
        self._create_fund("F001")
        r = client.post("/experiments", json={
            "experiment_name": "E1",
            "experiment_group_id": gid,
            "target_weights": {"F001": 0.5},
        })
        assert r.status_code == 400

    def test_create_rejects_missing_group(self):
        self._create_fund("F001")
        r = client.post("/experiments", json={
            "experiment_name": "E1",
            "experiment_group_id": str(uuid.uuid4()),
            "target_weights": {"F001": 1.0},
        })
        assert r.status_code == 404

    def test_create_rejects_missing_fund(self):
        gid = self._create_group()
        r = client.post("/experiments", json={
            "experiment_name": "E1",
            "experiment_group_id": gid,
            "target_weights": {"MISS01": 1.0},
        })
        assert r.status_code == 400

    def test_get_single_includes_positions(self):
        gid = self._create_group()
        self._create_fund("F001", bucket="bond")
        self._create_fund("F002", bucket="gold_commodity")
        eid = self._create_exp(gid, "E2", weights={"F001": 0.6, "F002": 0.4})

        r = client.get(f"/experiments/{eid}")
        assert r.status_code == 200
        assert r.json()["experiment_name"] == "E2"
        assert len(r.json()["positions"]) == 2
        assert {p["fund_code"] for p in r.json()["positions"]} == {"F001", "F002"}
        buckets = {p["fund_code"]: p["asset_bucket_snapshot"] for p in r.json()["positions"]}
        assert buckets["F001"] == "bond"
        assert buckets["F002"] == "gold_commodity"

    def test_get_not_found(self):
        r = client.get(f"/experiments/{uuid.uuid4()}")
        assert r.status_code == 404

    def test_update_scalar_fields(self):
        gid = self._create_group()
        self._create_fund("F001")
        eid = self._create_exp(gid, "E3", role="main", weights={"F001": 1.0})

        r = client.put(f"/experiments/{eid}", json={
            "experiment_name": "E3-改", "role": "benchmark",
            "rebalance_rule": "quarterly", "note": "备注",
        })
        assert r.status_code == 200

        r = client.get(f"/experiments/{eid}")
        assert r.json()["experiment_name"] == "E3-改"
        assert r.json()["role"] == "benchmark"
        assert r.json()["rebalance_rule"] == "quarterly"

    def test_update_positions(self):
        gid = self._create_group()
        self._create_fund("F001")
        self._create_fund("F002")
        self._create_fund("F003")
        eid = self._create_exp(gid, "E4", weights={"F001": 0.5, "F002": 0.5})

        r = client.put(f"/experiments/{eid}", json={
            "target_weights": {"F001": 0.3, "F002": 0.3, "F003": 0.4},
        })
        assert r.status_code == 200

        r = client.get(f"/experiments/{eid}")
        assert len(r.json()["positions"]) == 3

    def test_update_positions_rejects_invalid_weights(self):
        gid = self._create_group()
        self._create_fund("F001")
        eid = self._create_exp(gid, "E5", weights={"F001": 1.0})

        r = client.put(f"/experiments/{eid}", json={"target_weights": {"F001": 0.5}})
        assert r.status_code == 400

    def test_update_positions_rejects_missing_fund(self):
        gid = self._create_group()
        self._create_fund("F001")
        eid = self._create_exp(gid, "E5", weights={"F001": 1.0})

        r = client.put(f"/experiments/{eid}", json={"target_weights": {"MISS01": 1.0}})
        assert r.status_code == 400

    def test_update_not_found(self):
        r = client.put(f"/experiments/{uuid.uuid4()}", json={"experiment_name": "x"})
        assert r.status_code == 404

    def test_delete_cascades(self):
        gid = self._create_group()
        self._create_fund("F001")
        eid = self._create_exp(gid, "E6", weights={"F001": 1.0})

        r = client.delete(f"/experiments/{eid}")
        assert r.status_code == 200

        r = client.get(f"/experiments/{eid}")
        assert r.status_code == 404

    def test_delete_not_found(self):
        r = client.delete(f"/experiments/{uuid.uuid4()}")
        assert r.status_code == 404

    def test_list_filter_by_role(self):
        gid = self._create_group()
        self._create_fund("F001")
        self._create_exp(gid, "main-exp", role="main", weights={"F001": 1.0})
        self._create_exp(gid, "bench-exp", role="benchmark", weights={"F001": 1.0})

        r = client.get("/experiments?role=main")
        assert len(r.json()) == 1
        assert r.json()[0]["experiment_name"] == "main-exp"

        r = client.get("/experiments?role=benchmark")
        assert len(r.json()) == 1
        assert r.json()[0]["experiment_name"] == "bench-exp"


# ═══════════════════════════════════════════════════════════════════
# Stress Period CRUD
# ═══════════════════════════════════════════════════════════════════

class TestStressPeriods:
    def _create(self, name="2018熊市", start="2018-01-01", end="2018-12-31", desc=""):
        r = client.post("/stress-periods", json={
            "period_name": name, "start_date": start, "end_date": end, "description": desc,
        })
        assert r.status_code == 201
        return r.json()["period_id"]

    def test_list_empty(self):
        r = client.get("/stress-periods")
        assert r.status_code == 200
        assert r.json() == []

    def test_create_and_list(self):
        self._create()
        r = client.get("/stress-periods")
        assert len(r.json()) == 1
        assert r.json()[0]["period_name"] == "2018熊市"

    def test_update(self):
        pid = self._create("orig")
        r = client.put(f"/stress-periods/{pid}", json={
            "period_name": "updated", "description": "new desc", "is_active": False,
        })
        assert r.status_code == 200

        r = client.get("/stress-periods")
        assert r.json()[0]["period_name"] == "updated"
        assert r.json()[0]["is_active"] is False

    def test_update_not_found(self):
        r = client.put(f"/stress-periods/{uuid.uuid4()}", json={"period_name": "x"})
        assert r.status_code == 404

    def test_delete(self):
        pid = self._create("to-delete")
        r = client.delete(f"/stress-periods/{pid}")
        assert r.status_code == 200

        r = client.get("/stress-periods")
        assert r.json() == []

    def test_delete_not_found(self):
        r = client.delete(f"/stress-periods/{uuid.uuid4()}")
        assert r.status_code == 404

    def test_list_filter_active(self):
        self._create("active-one")
        pid2 = self._create("inactive-one")
        client.put(f"/stress-periods/{pid2}", json={"is_active": False})

        r = client.get("/stress-periods?is_active=true")
        assert len(r.json()) == 1
        assert r.json()[0]["period_name"] == "active-one"


# ═══════════════════════════════════════════════════════════════════
# Backtest Result CRUD
# ═══════════════════════════════════════════════════════════════════

class TestBacktestResults:
    def _create_group(self, name="测试实验组"):
        r = client.post("/experiment-groups", json={"group_name": name})
        return r.json()["experiment_group_id"]

    def _create_fund(self, code, name, bucket="a_share_equity"):
        client.post("/funds", json={"fund_code": code, "fund_name": name, "asset_bucket": bucket})

    def _create_exp(self, group_id, name="测试实验", weights=None, rebalance="no_rebalance"):
        if weights is None:
            weights = {"F001": 1.0}
        r = client.post("/experiments", json={
            "experiment_name": name,
            "experiment_group_id": group_id,
            "target_weights": weights,
            "rebalance_rule": rebalance,
        })
        return r.json()["experiment_id"]

    def _seed_nav(self, code, data):
        db = TestingSessionLocal()
        from app.models.fund import FundNavDaily
        for row in data:
            row["nav_date"] = date.fromisoformat(row["nav_date"]) if isinstance(row["nav_date"], str) else row["nav_date"]
            db.add(FundNavDaily(**row))
        db.commit()
        db.close()

    def test_get_result_not_found(self):
        r = client.get(f"/backtests/results/{uuid.uuid4()}")
        assert r.status_code == 404

    def test_get_by_experiment_not_found(self):
        r = client.get(f"/backtests/results/by-experiment/{uuid.uuid4()}")
        assert r.status_code == 404

    def test_run_and_query_backtest(self):
        gid = self._create_group()
        self._create_fund("F001", "基金A")
        eid = self._create_exp(gid, "E1", weights={"F001": 1.0}, rebalance="no_rebalance")

        self._seed_nav("F001", [
            {"fund_code": "F001", "nav_date": "2024-01-02", "unit_nav": 1.0, "accumulated_nav": 2.0, "adjusted_nav": 2.0, "source": "test"},
            {"fund_code": "F001", "nav_date": "2024-01-03", "unit_nav": 1.01, "accumulated_nav": 2.02, "adjusted_nav": 2.02, "source": "test"},
            {"fund_code": "F001", "nav_date": "2024-01-04", "unit_nav": 1.02, "accumulated_nav": 2.04, "adjusted_nav": 2.04, "source": "test"},
            {"fund_code": "F001", "nav_date": "2024-01-05", "unit_nav": 1.03, "accumulated_nav": 2.06, "adjusted_nav": 2.06, "source": "test"},
        ])

        r = client.post(f"/backtests/run/{eid}", json={})
        assert r.status_code == 200
        result = r.json()
        assert "result_id" in result
        assert result["experiment_id"] == eid
        assert result["data_quality_level"] == "A"
        result_id = result["result_id"]

        r = client.get(f"/backtests/results/{result_id}")
        assert r.status_code == 200
        assert len(r.json()["daily_nav"]) == 3

        r = client.get(f"/backtests/results/by-experiment/{eid}")
        assert r.status_code == 200
        assert r.json()["result_id"] == result_id

    def test_run_backtest_experiment_not_found(self):
        r = client.post(f"/backtests/run/{uuid.uuid4()}", json={})
        assert r.status_code == 404

    def test_run_backtest_no_nav(self):
        gid = self._create_group()
        self._create_fund("F001", "基金A")
        eid = self._create_exp(gid, "E2", weights={"F001": 1.0})

        # Seed 1 NAV row — engine needs >=2 overlapping dates → ValueError
        self._seed_nav("F001", [
            {"fund_code": "F001", "nav_date": "2024-01-02", "unit_nav": 1.0, "accumulated_nav": 2.0, "adjusted_nav": 2.0, "source": "test"},
        ])

        r = client.post(f"/backtests/run/{eid}", json={})
        assert r.status_code == 400
        assert "Not enough" in r.json()["detail"]

    def test_delete_backtest_result(self):
        gid = self._create_group()
        self._create_fund("F001", "基金A")
        eid = self._create_exp(gid, "E3", weights={"F001": 1.0})
        self._seed_nav("F001", [
            {"fund_code": "F001", "nav_date": "2024-01-02", "unit_nav": 1.0, "accumulated_nav": 2.0, "adjusted_nav": 2.0, "source": "test"},
            {"fund_code": "F001", "nav_date": "2024-01-03", "unit_nav": 1.01, "accumulated_nav": 2.02, "adjusted_nav": 2.02, "source": "test"},
        ])

        r = client.post(f"/backtests/run/{eid}", json={})
        result_id = r.json()["result_id"]

        r = client.delete(f"/backtests/results/{result_id}")
        assert r.status_code == 200

        r = client.get(f"/backtests/results/{result_id}")
        assert r.status_code == 404

    def test_delete_not_found(self):
        r = client.delete(f"/backtests/results/{uuid.uuid4()}")
        assert r.status_code == 404

    def test_report_endpoint(self):
        gid = self._create_group()
        self._create_fund("F001", "基金A")
        eid = self._create_exp(gid, "E4", weights={"F001": 1.0})
        self._seed_nav("F001", [
            {"fund_code": "F001", "nav_date": "2024-01-02", "unit_nav": 1.0, "accumulated_nav": 2.0, "adjusted_nav": 2.0, "source": "test"},
            {"fund_code": "F001", "nav_date": "2024-01-03", "unit_nav": 1.01, "accumulated_nav": 2.02, "adjusted_nav": 2.02, "source": "test"},
        ])

        r = client.post(f"/backtests/run/{eid}", json={})
        result_id = r.json()["result_id"]

        r = client.get(f"/backtests/results/{result_id}/report")
        assert r.status_code == 200
        assert "report" in r.json()
        report = r.json()["report"]
        for term in ["买入", "卖出", "推荐", "保证收益"]:
            assert term not in report

    def test_report_not_found(self):
        r = client.get(f"/backtests/results/{uuid.uuid4()}/report")
        assert r.status_code == 404
