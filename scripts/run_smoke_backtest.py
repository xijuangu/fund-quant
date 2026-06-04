from __future__ import annotations

import argparse
import uuid
from datetime import date, datetime

from app.api.backtests import get_backtest_report, run_backtest
from app.db.session import SessionLocal
from app.models.experiment import ExperimentGroup, PortfolioExperiment, PortfolioPosition
from app.models.fund import FundBasic


DEFAULT_POSITIONS = ["001595:0.45", "012349:0.30", "110037:0.15", "000217:0.10"]


def parse_positions(values: list[str]) -> dict[str, float]:
    positions: dict[str, float] = {}
    for value in values:
        try:
            fund_code, weight_text = value.split(":", 1)
            positions[fund_code] = float(weight_text)
        except ValueError as exc:
            raise SystemExit(
                f"仓位格式错误：{value}，应使用 fund_code:weight，例如 001595:0.45"
            ) from exc

    total_weight = sum(positions.values())
    if abs(total_weight - 1.0) > 0.001:
        raise SystemExit(f"权重合计必须为 1.0，当前为 {total_weight:.6f}")
    return positions


def format_pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def main() -> None:
    parser = argparse.ArgumentParser(description="创建并运行一组本地 75/15/10 smoke 回测。")
    parser.add_argument(
        "--name",
        default=f"75/15/10 smoke 回测 {datetime.now().strftime('%Y%m%d-%H%M%S')}",
        help="实验名称。",
    )
    parser.add_argument(
        "--start-date",
        default="2021-07-06",
        help="回测开始日期，格式 YYYY-MM-DD。",
    )
    parser.add_argument(
        "--end-date",
        default="2026-06-03",
        help="回测结束日期，格式 YYYY-MM-DD。",
    )
    parser.add_argument(
        "--rebalance-rule",
        default="monthly",
        choices=["no_rebalance", "monthly", "quarterly", "threshold_5pct", "threshold_10pct"],
        help="再平衡规则。",
    )
    parser.add_argument(
        "--position",
        action="append",
        dest="positions",
        help="基金仓位，格式 fund_code:weight。可重复传入；不传时使用默认 smoke 组合。",
    )
    args = parser.parse_args()

    positions = parse_positions(args.positions or DEFAULT_POSITIONS)
    start_date = date.fromisoformat(args.start_date)
    end_date = date.fromisoformat(args.end_date)

    db = SessionLocal()
    try:
        funds = {
            fund.fund_code: fund
            for fund in db.query(FundBasic)
            .filter(FundBasic.fund_code.in_(positions.keys()))
            .all()
        }
        missing_fund_codes = sorted(set(positions) - set(funds))
        if missing_fund_codes:
            raise SystemExit(f"基金池缺少这些基金：{', '.join(missing_fund_codes)}")

        group = ExperimentGroup(
            experiment_group_id=uuid.uuid4(),
            group_name=args.name,
            research_question="75% 权益/QDII + 15% 债券 + 10% 黄金是否能改善进取配置回撤。",
            note="由 scripts/run_smoke_backtest.py 创建的本地 smoke 回测。",
        )
        db.add(group)
        db.flush()

        experiment = PortfolioExperiment(
            experiment_id=uuid.uuid4(),
            experiment_name=f"{args.name} - 主组合",
            experiment_group_id=group.experiment_group_id,
            role="main",
            start_date=start_date,
            end_date=end_date,
            rebalance_rule=args.rebalance_rule,
            cost_model="{}",
            note="默认 smoke 组合：45% A 股权益、30% QDII、15% 债券、10% 黄金。",
        )
        db.add(experiment)
        db.flush()

        for fund_code, weight in positions.items():
            fund = funds[fund_code]
            db.add(
                PortfolioPosition(
                    experiment_id=experiment.experiment_id,
                    fund_code=fund_code,
                    target_weight=weight,
                    asset_bucket_snapshot=fund.asset_bucket,
                )
            )

        db.commit()

        result = run_backtest(str(experiment.experiment_id), db)
        report = get_backtest_report(result["result_id"], db)["report"]
        metrics = result["metrics"]

        print("回测已完成")
        print(f"实验组 ID: {group.experiment_group_id}")
        print(f"实验 ID: {experiment.experiment_id}")
        print(f"结果 ID: {result['result_id']}")
        print(f"区间: {start_date.isoformat()} 至 {end_date.isoformat()}")
        print(f"再平衡: {args.rebalance_rule}")
        print("仓位:")
        for fund_code, weight in positions.items():
            fund = funds[fund_code]
            print(f"  - {fund_code} {fund.fund_name} {format_pct(weight)} [{fund.asset_bucket}]")
        print("核心指标:")
        print(f"  - 累计收益: {format_pct(metrics['cumulative_return'])}")
        print(f"  - 年化收益: {format_pct(metrics['annualized_return'])}")
        print(f"  - 年化波动: {format_pct(metrics['annualized_volatility'])}")
        print(f"  - 最大回撤: {format_pct(metrics['max_drawdown'])}")
        print(f"  - 夏普比率: {metrics['sharpe_ratio']:.4f}")
        print(f"  - 卡玛比率: {metrics['calmar_ratio']:.4f}")
        print(f"  - 交易日数: {metrics['total_trading_days']}")
        print(f"数据质量: {result['data_quality_level']}")
        print(f"报告长度: {len(report)} 字符")
    finally:
        db.close()


if __name__ == "__main__":
    main()
