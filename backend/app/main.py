import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, billing, notes
from app.core.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Tests provide their own schema via a fixture and skip global init.
    if os.getenv("LAUNCHKIT_SKIP_INIT") != "1":
        init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="LaunchKit API", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(auth.router)
    app.include_router(notes.router)
    app.include_router(billing.router)
    return app


app = create_app()
