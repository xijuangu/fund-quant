from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.backtest import BacktestNavDaily, BacktestResult
from app.models.experiment import PortfolioExperiment, PortfolioPosition
from app.models.fund import FundBasic, FundNavDaily
from app.schemas import FundCreate, FundUpdate

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
def create_fund(body: FundCreate, db: Session = Depends(get_db)):
    from datetime import date as date_type

    existing = db.query(FundBasic).filter(FundBasic.fund_code == body.fund_code).first()
    if existing:
        raise HTTPException(status_code=409, detail="Fund already exists")

    inc_date = None
    if body.inception_date:
        inc_date = date_type.fromisoformat(body.inception_date)

    f = FundBasic(
        fund_code=body.fund_code,
        fund_name=body.fund_name,
        fund_type=body.fund_type,
        asset_bucket=body.asset_bucket,
        inception_date=inc_date,
        fund_company=body.fund_company,
        note=body.note,
    )
    db.add(f)
    db.commit()
    return {"fund_code": body.fund_code, "status": "created"}


@router.put("/{fund_code}")
def update_fund(fund_code: str, body: FundUpdate, db: Session = Depends(get_db)):
    from datetime import date as date_type

    f = db.query(FundBasic).filter(FundBasic.fund_code == fund_code).first()
    if not f:
        raise HTTPException(status_code=404, detail="Fund not found")

    updates = body.model_dump(exclude_unset=True)
    if "inception_date" in updates:
        updates["inception_date"] = date_type.fromisoformat(updates["inception_date"]) if updates["inception_date"] else None

    for key, val in updates.items():
        setattr(f, key, val)

    db.commit()
    return {"fund_code": fund_code, "status": "updated"}


@router.delete("/{fund_code}")
def delete_fund(fund_code: str, db: Session = Depends(get_db)):
    f = db.query(FundBasic).filter(FundBasic.fund_code == fund_code).first()
    if not f:
        raise HTTPException(status_code=404, detail="Fund not found")

    # Cascade: find experiments referencing this fund, delete backtests → positions → experiment
    positions = db.query(PortfolioPosition).filter(PortfolioPosition.fund_code == fund_code).all()
    for pos in positions:
        exp = db.query(PortfolioExperiment).filter(PortfolioExperiment.experiment_id == pos.experiment_id).first()
        if exp:
            backtests = db.query(BacktestResult).filter(BacktestResult.experiment_id == exp.experiment_id).all()
            for bt in backtests:
                db.query(BacktestNavDaily).filter(BacktestNavDaily.result_id == bt.result_id).delete()
                db.delete(bt)
            db.query(PortfolioPosition).filter(PortfolioPosition.experiment_id == exp.experiment_id).delete()
            db.delete(exp)

    db.query(FundNavDaily).filter(FundNavDaily.fund_code == fund_code).delete()
    db.delete(f)
    db.commit()
    return {"fund_code": fund_code, "status": "deleted"}
