import uuid
import unittest
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

from app.api.backtests import run_backtest
from app.models.backtest import BacktestNavDaily, BacktestResult
from app.models.experiment import PortfolioExperiment, PortfolioPosition


class FakeQuery:
    def __init__(self, rows):
        self.rows = rows

    def filter(self, *_args, **_kwargs):
        return self

    def first(self):
        return self.rows[0] if self.rows else None

    def all(self):
        return self.rows


class FakeDb:
    def __init__(self, experiment, positions):
        self.experiment = experiment
        self.positions = positions
        self.operations = []

    def query(self, model):
        if model is PortfolioExperiment:
            return FakeQuery([self.experiment])
        if model is PortfolioPosition:
            return FakeQuery(self.positions)
        return FakeQuery([])

    def add(self, obj):
        self.operations.append(("add", type(obj)))

    def flush(self):
        self.operations.append(("flush", None))

    def commit(self):
        self.operations.append(("commit", None))


class BacktestPersistenceTest(unittest.TestCase):
    def test_flushes_backtest_result_before_daily_rows(self):
        experiment_id = uuid.uuid4()
        experiment = SimpleNamespace(
            experiment_id=experiment_id,
            start_date=date(2021, 7, 6),
            end_date=date(2026, 6, 3),
            rebalance_rule="monthly",
        )
        positions = [
            SimpleNamespace(fund_code="001595", target_weight=0.45),
            SimpleNamespace(fund_code="012349", target_weight=0.30),
            SimpleNamespace(fund_code="110037", target_weight=0.15),
            SimpleNamespace(fund_code="000217", target_weight=0.10),
        ]
        db = FakeDb(experiment, positions)
        backtest_payload = {
            "daily": [
                {
                    "nav_date": date(2021, 7, 7),
                    "portfolio_nav": 1.0,
                    "portfolio_return": 0.0,
                    "drawdown": 0.0,
                }
            ],
            "metrics": {"cumulative_return": 0.0},
            "nav_policy": {"preferred": "accumulated_nav", "actual_used": {}, "mixed_policy": False},
            "missing_data_diagnostics": {},
            "data_quality_level": "A",
            "data_quality": [],
            "rebalance_records": [],
            "contributions": [],
        }

        with patch("app.api.backtests.load_nav_dataframe", return_value={"001595": object()}), patch(
            "app.api.backtests.backtest_portfolio", return_value=backtest_payload
        ):
            run_backtest(str(experiment_id), db)

        self.assertEqual(db.operations[0], ("add", BacktestResult))
        self.assertEqual(db.operations[1], ("flush", None))
        self.assertEqual(db.operations[2], ("add", BacktestNavDaily))
        self.assertEqual(db.operations[-1], ("commit", None))


if __name__ == "__main__":
    unittest.main()
