import json
import uuid as uuid_mod

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.backtest import BacktestNavDaily, BacktestResult
from app.models.experiment import PortfolioExperiment, PortfolioPosition
from app.services.backtest_engine import backtest_portfolio
from app.services.nav_loader import load_nav_dataframe
from app.services.report_generator import generate_experiment_report

router = APIRouter(prefix="/backtests", tags=["backtests"])


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/health")
def backtests_health() -> dict[str, str]:
    return {"status": "ok", "module": "backtests"}


@router.post("/run/{experiment_id}")
def run_backtest(experiment_id: str, db: Session = Depends(get_db)):
    """Run a backtest for the given experiment and persist results."""
    exp = (
        db.query(PortfolioExperiment)
        .filter(PortfolioExperiment.experiment_id == uuid_mod.UUID(experiment_id))
        .first()
    )
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")

    positions = (
        db.query(PortfolioPosition)
        .filter(PortfolioPosition.experiment_id == exp.experiment_id)
        .all()
    )
    if not positions:
        raise HTTPException(status_code=400, detail="Experiment has no positions")

    fund_codes = [p.fund_code for p in positions]
    target_weights = {p.fund_code: p.target_weight for p in positions}

    nav_data = load_nav_dataframe(db, fund_codes, exp.start_date, exp.end_date)
    if not nav_data:
        raise HTTPException(status_code=400, detail="No NAV data available for experiment funds")

    result = backtest_portfolio(
        nav_data,
        target_weights,
        rebalance_rule=exp.rebalance_rule,
        start_date=exp.start_date,
        end_date=exp.end_date,
    )

    # Persist backtest result
    bt = BacktestResult(
        result_id=uuid_mod.uuid4(),
        experiment_id=exp.experiment_id,
        metrics_json=json.dumps(result["metrics"]),
        contribution_json=json.dumps(result.get("contributions", [])),
        rebalance_records_json=json.dumps(result.get("rebalance_records", [])),
        nav_policy_json=json.dumps(result["nav_policy"]),
        missing_data_json=json.dumps(result.get("missing_data_diagnostics", {})),
        data_quality_level=result["data_quality_level"],
        data_quality_json=json.dumps(result.get("data_quality", [])),
    )
    db.add(bt)
    db.flush()

    # Persist daily NAV
    for day in result["daily"]:
        bn = BacktestNavDaily(
            result_id=bt.result_id,
            nav_date=day["nav_date"],
            portfolio_nav=day["portfolio_nav"],
            portfolio_return=day["portfolio_return"],
            drawdown=day["drawdown"],
        )
        db.add(bn)

    db.commit()

    return {
        "result_id": str(bt.result_id),
        "experiment_id": str(exp.experiment_id),
        "metrics": result["metrics"],
        "data_quality_level": result["data_quality_level"],
        "data_quality": result["data_quality"],
        "nav_policy": result["nav_policy"],
    }


@router.get("/results/{result_id}")
def get_backtest_result(result_id: str, db: Session = Depends(get_db)):
    bt = (
        db.query(BacktestResult)
        .filter(BacktestResult.result_id == uuid_mod.UUID(result_id))
        .first()
    )
    if not bt:
        raise HTTPException(status_code=404, detail="Backtest result not found")

    daily = (
        db.query(BacktestNavDaily)
        .filter(BacktestNavDaily.result_id == bt.result_id)
        .order_by(BacktestNavDaily.nav_date)
        .all()
    )

    return {
        "result_id": str(bt.result_id),
        "experiment_id": str(bt.experiment_id),
        "metrics": json.loads(bt.metrics_json),
        "nav_policy": json.loads(bt.nav_policy_json),
        "data_quality_level": bt.data_quality_level,
        "data_quality": json.loads(bt.data_quality_json),
        "daily_nav": [
            {"nav_date": d.nav_date.isoformat(), "portfolio_nav": d.portfolio_nav, "portfolio_return": d.portfolio_return, "drawdown": d.drawdown}
            for d in daily
        ],
        "report_markdown": bt.report_markdown,
    }


@router.get("/results/{result_id}/report")
def get_backtest_report(result_id: str, db: Session = Depends(get_db)):
    bt = (
        db.query(BacktestResult)
        .filter(BacktestResult.result_id == uuid_mod.UUID(result_id))
        .first()
    )
    if not bt:
        raise HTTPException(status_code=404, detail="Backtest result not found")

    if bt.report_markdown:
        return {"report": bt.report_markdown}

    # Generate report if not yet saved
    exp = (
        db.query(PortfolioExperiment)
        .filter(PortfolioExperiment.experiment_id == bt.experiment_id)
        .first()
    )
    positions = (
        db.query(PortfolioPosition)
        .filter(PortfolioPosition.experiment_id == bt.experiment_id)
        .all()
    ) if exp else []

    metrics = json.loads(bt.metrics_json)
    nav_policy = json.loads(bt.nav_policy_json)
    missing_diag = json.loads(bt.missing_data_json)
    quality_reasons = json.loads(bt.data_quality_json)
    contributions = json.loads(bt.contribution_json)

    # Aggregate contributions
    contrib_summary: dict[str, float] = {}
    if isinstance(contributions, list):
        for day in contributions:
            for code, val in day.get("contributions", {}).items():
                contrib_summary[code] = contrib_summary.get(code, 0.0) + val

    # Compute turnover from rebalance records
    rebalance_records = json.loads(bt.rebalance_records_json)
    turnover_total = sum(r.get("turnover", 0.0) for r in rebalance_records) if isinstance(rebalance_records, list) else 0.0
    cost_total = sum(r.get("estimated_cost", 0.0) for r in rebalance_records) if isinstance(rebalance_records, list) else 0.0

    report = generate_experiment_report(
        experiment_name=exp.experiment_name if exp else "Unknown",
        target_weights={p.fund_code: p.target_weight for p in positions},
        rebalance_rule=exp.rebalance_rule if exp else "no_rebalance",
        start_date=exp.start_date.isoformat() if exp and exp.start_date else "N/A",
        end_date=exp.end_date.isoformat() if exp and exp.end_date else "N/A",
        metrics=metrics,
        nav_policy=nav_policy,
        data_quality_level=bt.data_quality_level,
        data_quality_reasons=quality_reasons,
        missing_data_diag=missing_diag,
        contributions_summary=contrib_summary,
        turnover_total=turnover_total,
        cost_total=cost_total,
    )

    bt.report_markdown = report
    db.commit()

    return {"report": report}
