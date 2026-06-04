"""Markdown research report generation."""

FORBIDDEN_TERMS = ["买入", "卖出", "推荐", "保证收益", "跟投组合", "必涨", "稳赚"]


def sanitize_report(text: str) -> str:
    """Replace forbidden terms with safe alternatives."""
    replacements = {
        "买入": "配置",
        "卖出": "调整",
        "推荐": "观察",
        "保证收益": "历史收益",
        "跟投组合": "参考组合",
    }
    result = text
    for forbidden, safe in replacements.items():
        result = result.replace(forbidden, safe)
    return result


def generate_quality_footer(level: str, reasons: list[str]) -> str:
    """Generate a data quality footer for the report."""
    lines = ["\n## 数据质量", f"\n本次回测数据质量等级：**{level}**\n"]
    if reasons:
        lines.append("原因：")
        for r in reasons:
            lines.append(f"- {r}")
    return "\n".join(lines)


def generate_experiment_report(
    experiment_name: str,
    target_weights: dict[str, float],
    rebalance_rule: str,
    start_date: str,
    end_date: str,
    metrics: dict,
    nav_policy: dict,
    data_quality_level: str,
    data_quality_reasons: list[str],
    missing_data_diag: dict,
    contributions_summary: dict[str, float],
    turnover_total: float,
    cost_total: float,
    benchmark_comparison: dict | None = None,
    stress_period_results: list[dict] | None = None,
) -> str:
    """Generate a Markdown research report for a portfolio experiment.

    Returns a Markdown string suitable for saving or display.
    """
    if data_quality_level == "D":
        return sanitize_report(
            f"# 研究备忘录（未生成正式报告）\n\n"
            f"**实验名称：** {experiment_name}\n\n"
            f"本次回测数据质量等级为 D，数据质量过低，拒绝生成正式研究报告。\n\n"
            f"诊断信息：\n"
            + "".join(f"- {r}\n" for r in data_quality_reasons)
            + f"\n回测区间：{start_date} 至 {end_date}\n\n"
            f"请检查净值数据完整性后重新运行回测。\n"
        )

    rebalance_labels = {
        "no_rebalance": "不再平衡",
        "monthly": "月度再平衡",
        "quarterly": "季度再平衡",
        "threshold_5pct": "阈值再平衡（5%）",
        "threshold_10pct": "阈值再平衡（10%）",
    }
    rebalance_label = rebalance_labels.get(rebalance_rule, rebalance_rule)

    lines = [
        f"# 研究备忘录：{experiment_name}",
        "",
        "## 实验概要",
        "",
        f"- **实验名称：** {experiment_name}",
        f"- **回测区间：** {start_date} 至 {end_date}",
        f"- **再平衡规则：** {rebalance_label}",
        "",
        "## 基金配置",
        "",
        "| 基金代码 | 目标权重 |",
        "|---------|---------|",
    ]
    for code, weight in target_weights.items():
        lines.append(f"| {code} | {weight:.1%} |")

    lines.extend(
        [
            "",
            "## 收益指标",
            "",
            "| 指标 | 数值 |",
            "|------|------|",
            f"| 累计收益 | {metrics.get('cumulative_return', 0):.2%} |",
            f"| 年化收益 | {metrics.get('annualized_return', 0):.2%} |",
            f"| 回测年数 | {metrics.get('years', 0):.1f} 年 |",
            f"| 总交易日数 | {metrics.get('total_trading_days', 0)} 天 |",
            "",
            "## 风险指标",
            "",
            "| 指标 | 数值 |",
            "|------|------|",
            f"| 年化波动率 | {metrics.get('annualized_volatility', 0):.2%} |",
            f"| 最大回撤 | {metrics.get('max_drawdown', 0):.2%} |",
            f"| 夏普比率 | {metrics.get('sharpe_ratio', 0):.2f} |",
            f"| 卡玛比率 | {metrics.get('calmar_ratio', 0):.2f} |",
            f"| 最佳月份收益 | {metrics.get('best_month_return', 0):.2%} |",
            f"| 最差月份收益 | {metrics.get('worst_month_return', 0):.2%} |",
            f"| 正收益月份占比 | {metrics.get('positive_month_pct', 0):.1%} |",
            "",
            "## 调仓与成本",
            "",
            "| 项目 | 数值 |",
            "|------|------|",
            f"| 总调仓幅度 | {turnover_total * 2:.2%} |",
            f"| 单边换手率 | {turnover_total:.2%} |",
            f"| 估算交易成本 | {cost_total:.4%} |",
        ]
    )

    # NAV policy
    lines.extend(
        [
            "",
            "## 净值口径",
            "",
            f"- 优先口径：{nav_policy.get('preferred', 'N/A')}",
            "- 实际使用：",
        ]
    )
    for code, col in nav_policy.get("actual_used", {}).items():
        lines.append(f"  - {code}: {col}")
    if nav_policy.get("mixed_policy"):
        lines.append("- 注意：本次回测存在净值口径混用，结果置信度较低。")

    # Missing data
    if missing_data_diag:
        lines.extend(["", "## 缺失数据诊断", ""])
        for code, diag in missing_data_diag.items():
            lines.append(f"- **{code}**：前向填充 {diag.get('forward_fill_count', 0)} 次，仍缺失 {diag.get('still_missing', 0)} 天")

    # Contributions
    if contributions_summary:
        lines.extend(["", "## 收益贡献（近似）", ""])
        for code, contrib in contributions_summary.items():
            lines.append(f"- {code}: {contrib:.2%}")
        lines.append("")
        lines.append("收益贡献为基于日度持仓权重和日收益率的近似归因。")

    # Benchmark comparison
    if benchmark_comparison:
        lines.extend(
            [
                "",
                "## 基准对比",
                "",
                "| 指标 | 本实验 | 基准 |",
                "|------|--------|------|",
            ]
        )
        for key, label in [
            ("annualized_return", "年化收益"),
            ("annualized_volatility", "年化波动率"),
            ("max_drawdown", "最大回撤"),
            ("sharpe_ratio", "夏普比率"),
            ("calmar_ratio", "卡玛比率"),
        ]:
            exp_val = metrics.get(key, 0)
            bench_val = benchmark_comparison.get(key, 0)
            lines.append(f"| {label} | {exp_val:.2%} | {bench_val:.2%} |")

    # Stress period diagnostics
    if stress_period_results:
        lines.extend(
            [
                "",
                "## 压力区间诊断",
                "",
                "| 压力区间 | 覆盖区间 | 交易日数 | 区间收益 | 区间最大回撤 |",
                "|----------|----------|----------|----------|--------------|",
            ]
        )
        for item in stress_period_results:
            lines.append(
                "| {name} | {start} 至 {end} | {days} | {period_return:.2%} | {max_drawdown:.2%} |".format(
                    name=item.get("period_name", "N/A"),
                    start=item.get("overlap_start", "N/A"),
                    end=item.get("overlap_end", "N/A"),
                    days=item.get("trading_days", 0),
                    period_return=item.get("period_return", 0.0),
                    max_drawdown=item.get("max_drawdown", 0.0),
                )
            )
        lines.append("")
        lines.append("压力区间结果基于组合日度净值在指定日期范围内的表现计算。")

    # Quality footer
    lines.append(generate_quality_footer(data_quality_level, data_quality_reasons))

    # Observation notes
    lines.extend(
        [
            "",
            "## 后续观察",
            "",
            "- 后续实验可继续观察不同再平衡频率对回撤控制的影响。",
            "- 可进一步增加压力区间诊断以验证防守资产在不同市场环境下的表现。",
        ]
    )

    return sanitize_report("\n".join(lines))
