import unittest

from app.services.report_generator import (
    FORBIDDEN_TERMS,
    generate_experiment_report,
    generate_quality_footer,
    sanitize_report,
)


class ReportLanguageGuardTest(unittest.TestCase):
    def test_forbidden_terms_not_in_output(self):
        """Report must never contain forbidden terms."""
        metrics = {
            "cumulative_return": 0.35,
            "annualized_return": 0.12,
            "annualized_volatility": 0.15,
            "max_drawdown": -0.25,
            "sharpe_ratio": 0.8,
            "calmar_ratio": 0.48,
            "best_month_return": 0.08,
            "worst_month_return": -0.07,
            "positive_month_pct": 0.62,
            "total_trading_days": 500,
            "years": 2.0,
        }
        report = generate_experiment_report(
            experiment_name="测试实验",
            target_weights={"000001": 0.75, "000002": 0.25},
            rebalance_rule="monthly",
            start_date="2022-01-01",
            end_date="2024-12-31",
            metrics=metrics,
            nav_policy={"preferred": "adjusted_nav", "actual_used": {"000001": "adjusted_nav", "000002": "adjusted_nav"}, "mixed_policy": False},
            data_quality_level="A",
            data_quality_reasons=["数据完整"],
            missing_data_diag={"000001": {"forward_fill_count": 0}, "000002": {"forward_fill_count": 0}},
            contributions_summary={"000001_equity": 0.25, "000002_bond": 0.10},
            turnover_total=0.15,
            cost_total=0.001,
        )
        for term in FORBIDDEN_TERMS:
            with self.subTest(term=term):
                self.assertNotIn(term, report)

    def test_report_includes_required_sections(self):
        metrics = {
            "cumulative_return": 0.35,
            "annualized_return": 0.12,
            "annualized_volatility": 0.15,
            "max_drawdown": -0.25,
            "sharpe_ratio": 0.8,
            "calmar_ratio": 0.48,
            "best_month_return": 0.08,
            "worst_month_return": -0.07,
            "positive_month_pct": 0.62,
            "total_trading_days": 500,
            "years": 2.0,
        }
        report = generate_experiment_report(
            experiment_name="测试实验",
            target_weights={"000001": 0.75, "000002": 0.25},
            rebalance_rule="monthly",
            start_date="2022-01-01",
            end_date="2024-12-31",
            metrics=metrics,
            nav_policy={"preferred": "adjusted_nav", "actual_used": {}, "mixed_policy": False},
            data_quality_level="A",
            data_quality_reasons=["数据完整"],
            missing_data_diag={},
            contributions_summary={},
            turnover_total=0.0,
            cost_total=0.0,
        )
        self.assertIn("测试实验", report)
        self.assertIn("回测区间", report)
        self.assertIn("再平衡规则", report)
        self.assertIn("收益指标", report)
        self.assertIn("风险指标", report)
        self.assertIn("数据质量", report)
        self.assertIn("**A**", report)

    def test_sanitize_removes_forbidden_terms(self):
        dirty = "建议买入该基金，卖出其他。推荐持有。保证收益稳定。"
        clean = sanitize_report(dirty)
        self.assertNotIn("买入", clean)
        self.assertNotIn("卖出", clean)
        self.assertNotIn("推荐", clean)
        self.assertNotIn("保证收益", clean)

    def test_quality_footer_includes_reasons(self):
        footer = generate_quality_footer("B", ["2 只 QDII 基金存在净值滞后", "共 18 次前向填充"])
        self.assertIn("B", footer)
        self.assertIn("QDII", footer)
        self.assertIn("前向填充", footer)

    def test_report_refuses_quality_d(self):
        metrics = {"cumulative_return": 0.35, "annualized_return": 0.12,
                   "annualized_volatility": 0.15, "max_drawdown": -0.25,
                   "sharpe_ratio": 0.8, "calmar_ratio": 0.48,
                   "best_month_return": 0.08, "worst_month_return": -0.07,
                   "positive_month_pct": 0.62, "total_trading_days": 500, "years": 2.0}
        report = generate_experiment_report(
            experiment_name="测试实验",
            target_weights={"000001": 0.75, "000002": 0.25},
            rebalance_rule="monthly",
            start_date="2022-01-01",
            end_date="2024-12-31",
            metrics=metrics,
            nav_policy={"preferred": "adjusted_nav", "actual_used": {}, "mixed_policy": True},
            data_quality_level="D",
            data_quality_reasons=["数据质量过低"],
            missing_data_diag={},
            contributions_summary={},
            turnover_total=0.0,
            cost_total=0.0,
        )
        self.assertIn("本次回测数据质量等级为 D", report)
        self.assertNotIn("收益指标", report)
