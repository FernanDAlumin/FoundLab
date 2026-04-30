from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from foundlab.api.routes import assets, runs
from foundlab.storage.database import create_db_and_tables


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    create_db_and_tables()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="FoundLab API", version="0.1.0", lifespan=lifespan)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "foundlab-api"}

    app.include_router(assets.router)
    app.include_router(runs.router)
    return app


app = create_app()
