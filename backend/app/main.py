from __future__ import annotations

import logging
import sys

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, data, documents, memory, projects, search, settings, voice
from app.core.config import get_settings
from app.core.database import db
from app.core.security import get_api_key

config = get_settings()
logging.basicConfig(
    level=logging.DEBUG if config.debug else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    handlers=[logging.FileHandler(config.data_dir / "second-brain.log", encoding="utf-8"), logging.StreamHandler()],
)

app = FastAPI(title="Second Brain Local API", version="0.1.0", docs_url="/docs" if config.debug else None)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in config.allowed_origins.split(",")],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
for router in (chat.router, memory.router, documents.router, search.router, projects.router, settings.router, voice.router, data.router):
    app.include_router(router, prefix="/api")


@app.on_event("startup")
def startup() -> None:
    db.migrate()


@app.get("/api/health")
def health():
    try:
        with db.connect() as connection:
            connection.execute("SELECT 1").fetchone()
        return {"status": "ok", "mode": "online" if get_api_key() else "local", "version": app.version}
    except Exception as exc:
        return {"status": "degraded", "mode": "local", "error": str(exc)}


def run() -> None:
    uvicorn.run(app, host=config.host, port=config.port, log_level="debug" if config.debug else "info")


if __name__ == "__main__":
    run()

