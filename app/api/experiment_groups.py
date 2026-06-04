import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.experiment import ExperimentGroup

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
def create_experiment_group(
    group_name: str,
    research_question: str = "",
    note: str = "",
    db: Session = Depends(get_db),
):
    g = ExperimentGroup(
        experiment_group_id=uuid.uuid4(),
        group_name=group_name,
        research_question=research_question,
        note=note,
    )
    db.add(g)
    db.commit()
    return {"experiment_group_id": str(g.experiment_group_id), "status": "created"}
