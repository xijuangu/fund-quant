import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.backtest import BacktestNavDaily, BacktestResult
from app.models.experiment import ExperimentGroup, PortfolioExperiment, PortfolioPosition
from app.models.fund import FundBasic
from app.schemas import ExperimentCreate, ExperimentUpdate

router = APIRouter(prefix="/experiments", tags=["experiments"])


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/health")
def experiments_health() -> dict[str, str]:
    return {"status": "ok", "module": "experiments"}


def validate_fund_codes(db: Session, fund_codes: list[str]) -> dict[str, FundBasic]:
    funds = db.query(FundBasic).filter(FundBasic.fund_code.in_(fund_codes)).all()
    fund_map = {fund.fund_code: fund for fund in funds}
    missing = sorted(set(fund_codes) - set(fund_map))
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Fund not found: {', '.join(missing)}",
        )
    return fund_map


@router.get("")
def list_experiments(
    group_id: str | None = Query(None),
    role: str | None = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(PortfolioExperiment)
    if group_id:
        q = q.filter(PortfolioExperiment.experiment_group_id == uuid.UUID(group_id))
    if role:
        q = q.filter(PortfolioExperiment.role == role)
    exps = q.all()
    return [
        {
            "experiment_id": str(e.experiment_id),
            "experiment_name": e.experiment_name,
            "experiment_group_id": str(e.experiment_group_id),
            "role": e.role,
            "start_date": e.start_date.isoformat() if e.start_date else None,
            "end_date": e.end_date.isoformat() if e.end_date else None,
            "rebalance_rule": e.rebalance_rule,
            "note": e.note,
        }
        for e in exps
    ]


@router.get("/{experiment_id}")
def get_experiment(experiment_id: str, db: Session = Depends(get_db)):
    e = db.query(PortfolioExperiment).filter(
        PortfolioExperiment.experiment_id == uuid.UUID(experiment_id)
    ).first()
    if not e:
        raise HTTPException(status_code=404, detail="Experiment not found")

    positions = (
        db.query(PortfolioPosition)
        .filter(PortfolioPosition.experiment_id == e.experiment_id)
        .all()
    )
    return {
        "experiment_id": str(e.experiment_id),
        "experiment_name": e.experiment_name,
        "experiment_group_id": str(e.experiment_group_id),
        "role": e.role,
        "start_date": e.start_date.isoformat() if e.start_date else None,
        "end_date": e.end_date.isoformat() if e.end_date else None,
        "rebalance_rule": e.rebalance_rule,
        "note": e.note,
        "positions": [
            {
                "fund_code": p.fund_code,
                "target_weight": p.target_weight,
                "asset_bucket_snapshot": p.asset_bucket_snapshot,
            }
            for p in positions
        ],
    }


@router.post("", status_code=201)
def create_experiment(body: ExperimentCreate, db: Session = Depends(get_db)):
    from datetime import date as date_type

    if abs(sum(body.target_weights.values()) - 1.0) > 0.001:
        raise HTTPException(status_code=400, detail="Target weights must sum to 1.0")

    group_id = uuid.UUID(body.experiment_group_id)
    group = db.query(ExperimentGroup).filter(ExperimentGroup.experiment_group_id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Experiment group not found")

    fund_map = validate_fund_codes(db, list(body.target_weights.keys()))

    e = PortfolioExperiment(
        experiment_id=uuid.uuid4(),
        experiment_name=body.experiment_name,
        experiment_group_id=group_id,
        role=body.role,
        start_date=date_type.fromisoformat(body.start_date) if body.start_date else None,
        end_date=date_type.fromisoformat(body.end_date) if body.end_date else None,
        rebalance_rule=body.rebalance_rule,
        cost_model=body.cost_model,
        note=body.note,
    )
    db.add(e)

    for fund_code, weight in body.target_weights.items():
        fund = fund_map[fund_code]
        pos = PortfolioPosition(
            experiment_id=e.experiment_id,
            fund_code=fund_code,
            target_weight=weight,
            asset_bucket_snapshot=fund.asset_bucket,
        )
        db.add(pos)

    db.commit()
    return {"experiment_id": str(e.experiment_id), "status": "created"}


@router.put("/{experiment_id}")
def update_experiment(experiment_id: str, body: ExperimentUpdate, db: Session = Depends(get_db)):
    from datetime import date as date_type

    e = db.query(PortfolioExperiment).filter(
        PortfolioExperiment.experiment_id == uuid.UUID(experiment_id)
    ).first()
    if not e:
        raise HTTPException(status_code=404, detail="Experiment not found")

    # Update scalar fields
    scalar_updates = body.model_dump(exclude_unset=True, exclude={"target_weights"})
    if "start_date" in scalar_updates:
        scalar_updates["start_date"] = date_type.fromisoformat(scalar_updates["start_date"]) if scalar_updates["start_date"] else None
    if "end_date" in scalar_updates:
        scalar_updates["end_date"] = date_type.fromisoformat(scalar_updates["end_date"]) if scalar_updates["end_date"] else None

    for key, val in scalar_updates.items():
        setattr(e, key, val)

    # Update positions if provided
    if body.target_weights is not None:
        if abs(sum(body.target_weights.values()) - 1.0) > 0.001:
            raise HTTPException(status_code=400, detail="Target weights must sum to 1.0")

        fund_map = validate_fund_codes(db, list(body.target_weights.keys()))

        # Delete old positions
        db.query(PortfolioPosition).filter(PortfolioPosition.experiment_id == e.experiment_id).delete()

        # Insert new positions
        for fund_code, weight in body.target_weights.items():
            fund = fund_map[fund_code]
            pos = PortfolioPosition(
                experiment_id=e.experiment_id,
                fund_code=fund_code,
                target_weight=weight,
                asset_bucket_snapshot=fund.asset_bucket,
            )
            db.add(pos)

    db.commit()
    return {"experiment_id": experiment_id, "status": "updated"}


@router.delete("/{experiment_id}")
def delete_experiment(experiment_id: str, db: Session = Depends(get_db)):
    e = db.query(PortfolioExperiment).filter(
        PortfolioExperiment.experiment_id == uuid.UUID(experiment_id)
    ).first()
    if not e:
        raise HTTPException(status_code=404, detail="Experiment not found")

    # Delete backtest results and daily NAVs first
    backtests = db.query(BacktestResult).filter(BacktestResult.experiment_id == e.experiment_id).all()
    for bt in backtests:
        db.query(BacktestNavDaily).filter(BacktestNavDaily.result_id == bt.result_id).delete()
        db.delete(bt)

    # Delete positions
    db.query(PortfolioPosition).filter(PortfolioPosition.experiment_id == e.experiment_id).delete()

    db.delete(e)
    db.commit()
    return {"experiment_id": experiment_id, "status": "deleted"}
