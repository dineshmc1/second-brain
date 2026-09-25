from __future__ import annotations

import logging
import os
import sys

# PyInstaller's windowed bootloader intentionally provides no standard streams.
# Uvicorn and a few dependencies still inspect them during startup, so route
# those writes to the null device without creating a console window.
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, data, documents, inbox, intelligence, learning, memory, projects, search, settings, tasks, voice
from app.core.config import get_settings
from app.core.database import db
from app.core.security import get_api_key

config = get_settings()
handlers: list[logging.Handler] = [logging.FileHandler(config.data_dir / "second-brain.log", encoding="utf-8")]
if sys.stderr is not None:
    handlers.append(logging.StreamHandler())
logging.basicConfig(
    level=logging.DEBUG if config.debug else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    handlers=handlers,
)

app = FastAPI(title="Second Brain Local API", version="0.2.0", docs_url="/docs" if config.debug else None)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in config.allowed_origins.split(",")],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
for router in (chat.router, memory.router, documents.router, search.router, projects.router, inbox.router,
               tasks.router, intelligence.router, learning.router, settings.router, voice.router, data.router):
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
