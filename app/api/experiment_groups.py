import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.backtest import BacktestNavDaily, BacktestResult
from app.models.experiment import ExperimentGroup, PortfolioExperiment, PortfolioPosition
from app.schemas import ExperimentGroupCreate, ExperimentGroupUpdate

router = APIRouter(prefix="/experiment-groups", tags=["experiment-groups"])


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/health")
def experiment_groups_health() -> dict[str, str]:
    return {"status": "ok", "module": "experiment_groups"}


@router.get("")
def list_experiment_groups(db: Session = Depends(get_db)):
    groups = db.query(ExperimentGroup).all()
    return [
        {
            "experiment_group_id": str(g.experiment_group_id),
            "group_name": g.group_name,
            "research_question": g.research_question,
            "note": g.note,
        }
        for g in groups
    ]


@router.get("/{group_id}")
def get_experiment_group(group_id: str, db: Session = Depends(get_db)):
    g = db.query(ExperimentGroup).filter(ExperimentGroup.experiment_group_id == uuid.UUID(group_id)).first()
    if not g:
        raise HTTPException(status_code=404, detail="Experiment group not found")
    return {
        "experiment_group_id": str(g.experiment_group_id),
        "group_name": g.group_name,
        "research_question": g.research_question,
        "note": g.note,
    }


@router.post("", status_code=201)
def create_experiment_group(body: ExperimentGroupCreate, db: Session = Depends(get_db)):
    g = ExperimentGroup(
        experiment_group_id=uuid.uuid4(),
        group_name=body.group_name,
        research_question=body.research_question,
        note=body.note,
    )
    db.add(g)
    db.commit()
    return {"experiment_group_id": str(g.experiment_group_id), "status": "created"}


@router.put("/{group_id}")
def update_experiment_group(group_id: str, body: ExperimentGroupUpdate, db: Session = Depends(get_db)):
    g = db.query(ExperimentGroup).filter(ExperimentGroup.experiment_group_id == uuid.UUID(group_id)).first()
    if not g:
        raise HTTPException(status_code=404, detail="Experiment group not found")

    updates = body.model_dump(exclude_unset=True)
    for key, val in updates.items():
        setattr(g, key, val)

    db.commit()
    return {"experiment_group_id": group_id, "status": "updated"}


@router.delete("/{group_id}")
def delete_experiment_group(group_id: str, db: Session = Depends(get_db)):
    g = db.query(ExperimentGroup).filter(ExperimentGroup.experiment_group_id == uuid.UUID(group_id)).first()
    if not g:
        raise HTTPException(status_code=404, detail="Experiment group not found")

    # Cascade-delete all experiments in this group (and their backtests/positions)
    exps = db.query(PortfolioExperiment).filter(
        PortfolioExperiment.experiment_group_id == g.experiment_group_id
    ).all()
    for e in exps:
        backtests = db.query(BacktestResult).filter(BacktestResult.experiment_id == e.experiment_id).all()
        for bt in backtests:
            db.query(BacktestNavDaily).filter(BacktestNavDaily.result_id == bt.result_id).delete()
            db.delete(bt)
        db.query(PortfolioPosition).filter(PortfolioPosition.experiment_id == e.experiment_id).delete()
        db.delete(e)

    db.delete(g)
    db.commit()
    return {"experiment_group_id": group_id, "status": "deleted"}
