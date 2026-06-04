import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.experiment import PortfolioExperiment, PortfolioPosition
from app.models.fund import FundBasic

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
def create_experiment(
    experiment_name: str,
    experiment_group_id: str,
    target_weights: dict[str, float],
    role: str = "main",
    start_date: str | None = None,
    end_date: str | None = None,
    rebalance_rule: str = "no_rebalance",
    cost_model: str = "{}",
    note: str = "",
    db: Session = Depends(get_db),
):
    from datetime import date as date_type

    if abs(sum(target_weights.values()) - 1.0) > 0.001:
        raise HTTPException(status_code=400, detail="Target weights must sum to 1.0")

    e = PortfolioExperiment(
        experiment_id=uuid.uuid4(),
        experiment_name=experiment_name,
        experiment_group_id=uuid.UUID(experiment_group_id),
        role=role,
        start_date=date_type.fromisoformat(start_date) if start_date else None,
        end_date=date_type.fromisoformat(end_date) if end_date else None,
        rebalance_rule=rebalance_rule,
        cost_model=cost_model,
        note=note,
    )
    db.add(e)

    for fund_code, weight in target_weights.items():
        fund = db.query(FundBasic).filter(FundBasic.fund_code == fund_code).first()
        bucket = fund.asset_bucket if fund else ""
        pos = PortfolioPosition(
            experiment_id=e.experiment_id,
            fund_code=fund_code,
            target_weight=weight,
            asset_bucket_snapshot=bucket,
        )
        db.add(pos)

    db.commit()
    return {"experiment_id": str(e.experiment_id), "status": "created"}
