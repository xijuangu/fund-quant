from fastapi import APIRouter

router = APIRouter(prefix="/stress-periods", tags=["stress-periods"])


@router.get("/health")
def stress_periods_health() -> dict[str, str]:
    return {"status": "ok", "module": "stress_periods"}

