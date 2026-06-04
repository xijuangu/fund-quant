import unittest
from datetime import date


from app.services.rebalance import (
    apply_rebalance,
    check_rebalance_trigger,
    compute_rebalance_trades,
)


class RebalanceTriggerTest(unittest.TestCase):
    def test_monthly_triggers_on_new_month(self):
        self.assertTrue(check_rebalance_trigger("monthly", date(2024, 2, 1), date(2024, 1, 31)))
        self.assertTrue(check_rebalance_trigger("monthly", date(2025, 1, 5), date(2024, 12, 20)))

    def test_monthly_no_trigger_same_month(self):
        self.assertFalse(check_rebalance_trigger("monthly", date(2024, 1, 15), date(2024, 1, 16)))

    def test_quarterly_triggers(self):
        self.assertTrue(check_rebalance_trigger("quarterly", date(2024, 4, 1), date(2024, 1, 15)))
        self.assertFalse(check_rebalance_trigger("quarterly", date(2024, 2, 15), date(2024, 1, 15)))

    def test_threshold_triggers(self):
        self.assertTrue(check_rebalance_trigger("threshold_5pct", date(2024, 1, 15), date(2024, 1, 14), {"A": 0.30, "B": 0.70}, {"A": 0.40, "B": 0.60}))
        self.assertFalse(check_rebalance_trigger("threshold_5pct", date(2024, 1, 15), date(2024, 1, 14), {"A": 0.30, "B": 0.70}, {"A": 0.34, "B": 0.66}))

    def test_no_rebalance_never_triggers(self):
        self.assertFalse(check_rebalance_trigger("no_rebalance", date(2024, 1, 15), date(2024, 1, 1)))


class RebalanceTradeTest(unittest.TestCase):
    def test_computes_trades(self):
        target = {"A": 0.3, "B": 0.7}
        current = {"A": 0.4, "B": 0.6}
        trades = compute_rebalance_trades(target, current)
        self.assertAlmostEqual(trades["A"], -0.1)
        self.assertAlmostEqual(trades["B"], 0.1)

    def test_trades_sum_to_zero(self):
        target = {"A": 0.25, "B": 0.35, "C": 0.4}
        current = {"A": 0.3, "B": 0.3, "C": 0.4}
        trades = compute_rebalance_trades(target, current)
        self.assertAlmostEqual(sum(trades.values()), 0.0)

    def test_turnover(self):
        target = {"A": 0.3, "B": 0.7}
        current = {"A": 0.5, "B": 0.5}
        trades = compute_rebalance_trades(target, current)
        total_trade = sum(abs(v) for v in trades.values())
        one_side = total_trade / 2
        self.assertAlmostEqual(one_side, 0.2)


class ApplyRebalanceTest(unittest.TestCase):
    def test_applies_rebalance(self):
        target = {"A": 0.3, "B": 0.7}
        current = {"A": 0.5, "B": 0.5}
        result = apply_rebalance(target, current)
        self.assertAlmostEqual(result["A"], 0.3)
        self.assertAlmostEqual(result["B"], 0.7)
