import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.stress_period import StressPeriod
from app.schemas import StressPeriodCreate, StressPeriodUpdate

router = APIRouter(prefix="/stress-periods", tags=["stress-periods"])


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/health")
def stress_periods_health() -> dict[str, str]:
    return {"status": "ok", "module": "stress_periods"}


@router.get("")
def list_stress_periods(is_active: bool | None = None, db: Session = Depends(get_db)):
    q = db.query(StressPeriod)
    if is_active is not None:
        q = q.filter(StressPeriod.is_active == is_active)
    periods = q.all()
    return [
        {
            "period_id": str(p.period_id),
            "period_name": p.period_name,
            "start_date": p.start_date.isoformat(),
            "end_date": p.end_date.isoformat(),
            "description": p.description,
            "is_active": p.is_active,
        }
        for p in periods
    ]


@router.post("", status_code=201)
def create_stress_period(body: StressPeriodCreate, db: Session = Depends(get_db)):
    from datetime import date as date_type

    p = StressPeriod(
        period_id=uuid.uuid4(),
        period_name=body.period_name,
        start_date=date_type.fromisoformat(body.start_date),
        end_date=date_type.fromisoformat(body.end_date),
        description=body.description,
    )
    db.add(p)
    db.commit()
    return {"period_id": str(p.period_id), "status": "created"}


@router.put("/{period_id}")
def update_stress_period(period_id: str, body: StressPeriodUpdate, db: Session = Depends(get_db)):
    from datetime import date as date_type

    p = db.query(StressPeriod).filter(StressPeriod.period_id == uuid.UUID(period_id)).first()
    if not p:
        raise HTTPException(status_code=404, detail="Stress period not found")

    updates = body.model_dump(exclude_unset=True)
    if "start_date" in updates:
        updates["start_date"] = date_type.fromisoformat(updates["start_date"]) if updates["start_date"] else None
    if "end_date" in updates:
        updates["end_date"] = date_type.fromisoformat(updates["end_date"]) if updates["end_date"] else None

    for key, val in updates.items():
        setattr(p, key, val)

    db.commit()
    return {"period_id": period_id, "status": "updated"}


@router.delete("/{period_id}")
def delete_stress_period(period_id: str, db: Session = Depends(get_db)):
    p = db.query(StressPeriod).filter(StressPeriod.period_id == uuid.UUID(period_id)).first()
    if not p:
        raise HTTPException(status_code=404, detail="Stress period not found")
    db.delete(p)
    db.commit()
    return {"period_id": period_id, "status": "deleted"}
