import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.stress_period import StressPeriod

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
def create_stress_period(
    period_name: str,
    start_date: str,
    end_date: str,
    description: str = "",
    db: Session = Depends(get_db),
):
    from datetime import date as date_type

    p = StressPeriod(
        period_id=uuid.uuid4(),
        period_name=period_name,
        start_date=date_type.fromisoformat(start_date),
        end_date=date_type.fromisoformat(end_date),
        description=description,
    )
    db.add(p)
    db.commit()
    return {"period_id": str(p.period_id), "status": "created"}
