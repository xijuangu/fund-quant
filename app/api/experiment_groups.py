from fastapi import APIRouter

router = APIRouter(prefix="/experiment-groups", tags=["experiment-groups"])


@router.get("/health")
def experiment_groups_health() -> dict[str, str]:
    return {"status": "ok", "module": "experiment_groups"}

