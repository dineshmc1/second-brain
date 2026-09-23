import json

from fastapi import APIRouter, HTTPException

from app.core.config import get_settings
from app.core.database import db
from app.core.security import get_api_key, set_api_key
from app.models.schemas import SettingUpdate

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("")
def read_settings():
    with db.connect() as connection:
        values = {row["key"]: json.loads(row["value_json"]) for row in connection.execute("SELECT * FROM settings")}
    defaults = {
        "model": get_settings().model, "top_k": 8, "vector_weight": 0.55,
        "keyword_weight": 0.45, "auto_memory": True, "ask_before_saving": False,
        "response_mode": "text", "animations": True, "close_to_tray": True,
    }
    return {**defaults, **values, "has_api_key": bool(get_api_key())}


@router.put("")
def update_settings(payload: SettingUpdate):
    if payload.api_key is not None:
        try:
            set_api_key(payload.api_key or None)
        except RuntimeError as exc:
            raise HTTPException(503, str(exc))
    with db.transaction() as connection:
        for key, value in payload.values.items():
            if key in {"api_key", "has_api_key"}:
                continue
            connection.execute(
                """INSERT INTO settings(key,value_json,updated_at) VALUES (?,?,CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET value_json=excluded.value_json,updated_at=CURRENT_TIMESTAMP""",
                (key, json.dumps(value)),
            )
    return read_settings()

