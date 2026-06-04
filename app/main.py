from fastapi import FastAPI

from app.api import backtests, experiment_groups, experiments, funds, reports, stress_periods


def create_app() -> FastAPI:
    app = FastAPI(title="Fund Portfolio Lab", version="0.1.0")
    app.include_router(funds.router)
    app.include_router(experiment_groups.router)
    app.include_router(experiments.router)
    app.include_router(backtests.router)
    app.include_router(stress_periods.router)
    app.include_router(reports.router)
    return app


app = create_app()

