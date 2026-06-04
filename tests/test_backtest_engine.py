import unittest

import pandas as pd

from app.services.backtest_engine import backtest_portfolio
from app.services.data_quality import compute_data_quality
from app.services.metrics import (
    calculate_annualized_return,
    calculate_annualized_volatility,
    calculate_calmar_ratio,
    calculate_cumulative_return,
    calculate_sharpe_ratio,
)


class BacktestEngineTest(unittest.TestCase):
    def setUp(self):
        dates = pd.to_datetime(
            ["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05", "2024-01-08"]
        )
        self.fund_navs = {
            "equity": pd.DataFrame(
                {"adjusted_nav": [1.00, 1.02, 1.04, 1.03, 1.06]},
                index=dates,
            ),
            "bond": pd.DataFrame(
                {"adjusted_nav": [1.00, 1.001, 1.002, 1.003, 1.004]},
                index=dates,
            ),
        }
        self.target_weights = {"equity": 0.75, "bond": 0.25}

    def test_backtest_no_rebalance(self):
        result = backtest_portfolio(
            self.fund_navs,
            self.target_weights,
            rebalance_rule="no_rebalance",
            nav_column="adjusted_nav",
        )
        self.assertIn("daily", result)
        self.assertIn("metrics", result)
        self.assertIn("nav_policy", result)
        self.assertIn("missing_data_diagnostics", result)
        self.assertIn("data_quality", result)
        self.assertEqual(len(result["daily"]), 4)  # 4 trading days of returns

    def test_backtest_monthly_rebalance(self):
        result = backtest_portfolio(
            self.fund_navs,
            self.target_weights,
            rebalance_rule="monthly",
            nav_column="adjusted_nav",
        )
        self.assertIn("rebalance_records", result)

    def test_backtest_handles_missing_fund(self):
        with self.assertRaises(ValueError):
            backtest_portfolio(
                {"equity": self.fund_navs["equity"]},
                {"equity": 0.5, "gold": 0.5},
                rebalance_rule="no_rebalance",
                nav_column="adjusted_nav",
            )

    def test_backtest_rejects_weights_not_summing_to_one(self):
        with self.assertRaises(ValueError):
            backtest_portfolio(
                self.fund_navs,
                {"equity": 0.5, "bond": 0.3},
                rebalance_rule="no_rebalance",
                nav_column="adjusted_nav",
            )


class DataQualityTest(unittest.TestCase):
    def test_grade_a_perfect_data(self):
        diag = {"equity": {"forward_fill_count": 0}, "bond": {"forward_fill_count": 0}}
        level, reasons = compute_data_quality(False, diag, 0)
        self.assertEqual(level, "A")

    def test_grade_b_minor_fills(self):
        diag = {"equity": {"forward_fill_count": 5}, "bond": {"forward_fill_count": 8}}
        level, reasons = compute_data_quality(False, diag, 2)
        self.assertEqual(level, "B")

    def test_grade_c_mixed_nav(self):
        diag = {"equity": {"forward_fill_count": 0}}
        level, reasons = compute_data_quality(True, diag, 0)
        self.assertEqual(level, "C")

    def test_grade_d_excessive_missing(self):
        diag = {"equity": {"forward_fill_count": 50}, "bond": {"forward_fill_count": 30}}
        level, reasons = compute_data_quality(True, diag, 5)
        self.assertEqual(level, "D")


class AdditionalMetricsTest(unittest.TestCase):
    def test_cumulative_return(self):
        navs = [1.0, 1.1, 1.21]
        self.assertAlmostEqual(calculate_cumulative_return(navs), 0.21)

    def test_annualized_return(self):
        self.assertAlmostEqual(calculate_annualized_return(1.0, 1.21, 2.0), 0.1, places=3)

    def test_annualized_volatility(self):
        returns = [0.01, -0.02, 0.03, 0.01, -0.01]
        vol = calculate_annualized_volatility(returns)
        self.assertGreater(vol, 0)

    def test_sharpe_ratio(self):
        returns = [0.01, 0.02, 0.01, 0.03, -0.01]
        sr = calculate_sharpe_ratio(returns)
        self.assertGreater(sr, 0)

    def test_calmar_ratio(self):
        self.assertAlmostEqual(calculate_calmar_ratio(0.12, -0.25), 0.48)
        self.assertAlmostEqual(calculate_calmar_ratio(0.12, 0.0), 0.0)
