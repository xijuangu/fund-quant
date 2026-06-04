import unittest

from app.models.fund import FundBasic, FundNavDaily
from app.models.experiment import ExperimentGroup, PortfolioExperiment, PortfolioPosition
from app.models.backtest import BacktestResult, BacktestNavDaily
from app.models.stress_period import StressPeriod


class FundModelTest(unittest.TestCase):
    def test_fund_basic_has_required_columns(self):
        cols = {c.name for c in FundBasic.__table__.columns}
        required = {
            "fund_code", "fund_name", "fund_type", "asset_bucket",
            "inception_date", "fund_company", "is_active", "note",
            "created_at", "updated_at",
        }
        self.assertTrue(required.issubset(cols))

    def test_fund_nav_daily_has_required_columns(self):
        cols = {c.name for c in FundNavDaily.__table__.columns}
        required = {
            "fund_code", "nav_date", "unit_nav", "accumulated_nav",
            "adjusted_nav", "source", "created_at", "updated_at",
        }
        self.assertTrue(required.issubset(cols))


class ExperimentModelTest(unittest.TestCase):
    def test_experiment_group_has_required_columns(self):
        cols = {c.name for c in ExperimentGroup.__table__.columns}
        required = {
            "experiment_group_id", "group_name", "research_question",
            "note", "created_at", "updated_at",
        }
        self.assertTrue(required.issubset(cols))

    def test_portfolio_experiment_has_required_columns(self):
        cols = {c.name for c in PortfolioExperiment.__table__.columns}
        required = {
            "experiment_id", "experiment_name", "experiment_group_id",
            "role", "start_date", "end_date", "rebalance_rule",
            "cost_model", "note", "created_at", "updated_at",
        }
        self.assertTrue(required.issubset(cols))

    def test_portfolio_position_has_required_columns(self):
        cols = {c.name for c in PortfolioPosition.__table__.columns}
        required = {
            "experiment_id", "fund_code", "target_weight",
            "asset_bucket_snapshot",
        }
        self.assertTrue(required.issubset(cols))


class BacktestModelTest(unittest.TestCase):
    def test_backtest_result_has_required_columns(self):
        cols = {c.name for c in BacktestResult.__table__.columns}
        required = {
            "result_id", "experiment_id", "run_time", "metrics_json",
            "contribution_json", "rebalance_records_json", "nav_policy_json",
            "missing_data_json", "data_quality_level", "data_quality_json",
            "report_markdown",
        }
        self.assertTrue(required.issubset(cols))

    def test_backtest_nav_daily_has_required_columns(self):
        cols = {c.name for c in BacktestNavDaily.__table__.columns}
        required = {
            "result_id", "nav_date", "portfolio_nav",
            "portfolio_return", "drawdown",
        }
        self.assertTrue(required.issubset(cols))


class StressPeriodModelTest(unittest.TestCase):
    def test_stress_period_has_required_columns(self):
        cols = {c.name for c in StressPeriod.__table__.columns}
        required = {
            "period_id", "period_name", "start_date", "end_date",
            "description", "is_active", "created_at", "updated_at",
        }
        self.assertTrue(required.issubset(cols))
