from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.fund import FundBasic

router = APIRouter(prefix="/funds", tags=["funds"])


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/health")
def funds_health() -> dict[str, str]:
    return {"status": "ok", "module": "funds"}


@router.get("")
def list_funds(
    asset_bucket: str | None = Query(None),
    is_active: bool | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(FundBasic)
    if asset_bucket:
        q = q.filter(FundBasic.asset_bucket == asset_bucket)
    if is_active is not None:
        q = q.filter(FundBasic.is_active == is_active)
    funds = q.all()
    return [
        {
            "fund_code": f.fund_code,
            "fund_name": f.fund_name,
            "fund_type": f.fund_type,
            "asset_bucket": f.asset_bucket,
            "inception_date": f.inception_date.isoformat() if f.inception_date else None,
            "fund_company": f.fund_company,
            "is_active": f.is_active,
            "note": f.note,
        }
        for f in funds
    ]


@router.get("/{fund_code}")
def get_fund(fund_code: str, db: Session = Depends(get_db)):
    f = db.query(FundBasic).filter(FundBasic.fund_code == fund_code).first()
    if not f:
        raise HTTPException(status_code=404, detail="Fund not found")
    return {
        "fund_code": f.fund_code,
        "fund_name": f.fund_name,
        "fund_type": f.fund_type,
        "asset_bucket": f.asset_bucket,
        "inception_date": f.inception_date.isoformat() if f.inception_date else None,
        "fund_company": f.fund_company,
        "is_active": f.is_active,
        "note": f.note,
    }


@router.post("", status_code=201)
def create_fund(
    fund_code: str,
    fund_name: str,
    fund_type: str = "",
    asset_bucket: str = "",
    inception_date: str | None = None,
    fund_company: str = "",
    note: str = "",
    db: Session = Depends(get_db),
):
    from datetime import date as date_type

    existing = db.query(FundBasic).filter(FundBasic.fund_code == fund_code).first()
    if existing:
        raise HTTPException(status_code=409, detail="Fund already exists")

    inc_date = None
    if inception_date:
        inc_date = date_type.fromisoformat(inception_date)

    f = FundBasic(
        fund_code=fund_code,
        fund_name=fund_name,
        fund_type=fund_type,
        asset_bucket=asset_bucket,
        inception_date=inc_date,
        fund_company=fund_company,
        note=note,
    )
    db.add(f)
    db.commit()
    return {"fund_code": fund_code, "status": "created"}
