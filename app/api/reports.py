from fastapi import APIRouter

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/health")
def reports_health() -> dict[str, str]:
    return {"status": "ok", "module": "reports"}

