from fastapi import APIRouter

router = APIRouter(prefix="/funds", tags=["funds"])


@router.get("/health")
def funds_health() -> dict[str, str]:
    return {"status": "ok", "module": "funds"}

