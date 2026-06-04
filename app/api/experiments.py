from fastapi import APIRouter

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.get("/health")
def experiments_health() -> dict[str, str]:
    return {"status": "ok", "module": "experiments"}

