from __future__ import annotations

import os

SERVICE_NAME = "Second Brain"
ACCOUNT_NAME = "openrouter-api-key"


def get_api_key() -> str | None:
    try:
        import keyring

        stored = keyring.get_password(SERVICE_NAME, ACCOUNT_NAME)
        if stored:
            return stored
    except Exception:
        pass
    return os.getenv("OPENROUTER_API_KEY") or None


def set_api_key(value: str | None) -> None:
    try:
        import keyring

        if value:
            keyring.set_password(SERVICE_NAME, ACCOUNT_NAME, value.strip())
        else:
            try:
                keyring.delete_password(SERVICE_NAME, ACCOUNT_NAME)
            except keyring.errors.PasswordDeleteError:
                pass
    except Exception as exc:
        raise RuntimeError("Windows Credential Manager is unavailable") from exc
