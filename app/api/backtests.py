from fastapi import APIRouter

router = APIRouter(prefix="/backtests", tags=["backtests"])


@router.get("/health")
def backtests_health() -> dict[str, str]:
    return {"status": "ok", "module": "backtests"}

