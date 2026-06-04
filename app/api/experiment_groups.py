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
    gid = uuid.UUID(group_id)
    g = db.query(ExperimentGroup).filter(ExperimentGroup.experiment_group_id == gid).first()
    if not g:
        raise HTTPException(status_code=404, detail="Experiment group not found")

    # Use bulk delete for all children, then delete the group.
    # Must use Query.delete() consistently (not db.delete()) so that all
    # SQL runs in a predictable order before the parent DELETE.
    exp_ids = (
        db.query(PortfolioExperiment.experiment_id)
        .filter(PortfolioExperiment.experiment_group_id == gid)
        .all()
    )
    exp_id_list = [eid for (eid,) in exp_ids]

    if exp_id_list:
        backtests = (
            db.query(BacktestResult.result_id)
            .filter(BacktestResult.experiment_id.in_(exp_id_list))
            .all()
        )
        bt_id_list = [rid for (rid,) in backtests]

        if bt_id_list:
            db.query(BacktestNavDaily).filter(
                BacktestNavDaily.result_id.in_(bt_id_list)
            ).delete(synchronize_session="fetch")
            db.query(BacktestResult).filter(
                BacktestResult.result_id.in_(bt_id_list)
            ).delete(synchronize_session="fetch")

        db.query(PortfolioPosition).filter(
            PortfolioPosition.experiment_id.in_(exp_id_list)
        ).delete(synchronize_session="fetch")

        db.query(PortfolioExperiment).filter(
            PortfolioExperiment.experiment_id.in_(exp_id_list)
        ).delete(synchronize_session="fetch")

    db.flush()
    db.delete(g)
    db.commit()
    return {"experiment_group_id": group_id, "status": "deleted"}
