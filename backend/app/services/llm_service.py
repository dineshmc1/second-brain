from __future__ import annotations

import json
import hashlib
import logging
from datetime import UTC, datetime
from functools import lru_cache
from typing import Any
from uuid import uuid4

from app.core.config import get_settings
from app.core.security import get_api_key
from app.models.schemas import MemoryExtract

logger = logging.getLogger(__name__)


class LLMUnavailable(RuntimeError):
    pass


class LLMService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _client(self):
        key = get_api_key()
        if not key:
            raise LLMUnavailable("No OpenRouter API key is configured")
        from openai import OpenAI

        return OpenAI(
            api_key=key,
            base_url=self.settings.openrouter_base_url,
            timeout=30,
            max_retries=1,
            default_headers={
                "HTTP-Referer": self.settings.openrouter_site_url,
                "X-OpenRouter-Title": self.settings.openrouter_app_name,
            },
        )

    def _model(self) -> str:
        try:
            from app.core.database import db

            with db.connect() as connection:
                row = connection.execute("SELECT value_json FROM settings WHERE key='model'").fetchone()
            model = str(json.loads(row[0])) if row else self.settings.model
        except Exception:
            model = self.settings.model
        # OpenRouter model IDs include their provider. This also upgrades the
        # value stored by pre-OpenRouter builds without mutating user data.
        return model if "/" in model else f"openai/{model}"

    @staticmethod
    def _message_text(message: Any) -> str:
        content = message.content
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            return "".join(
                item.get("text", "") if isinstance(item, dict) else getattr(item, "text", "")
                for item in content
            ).strip()
        return str(content or "").strip()

    def extract_memory(self, text: str) -> MemoryExtract:
        try:
            schema = MemoryExtract.model_json_schema()
            schema["required"] = list(schema["properties"])
            schema["additionalProperties"] = False
            response = self._client().chat.completions.create(
                model=self._model(),
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Extract durable personal knowledge. Preserve exact facts and dates. "
                            "Classify updates as UPDATE. Return should_store=false for greetings, "
                            "questions, or transient chatter. Never invent missing fields. Return "
                            "every schema field, using null or an empty list when appropriate."
                        ),
                    },
                    {"role": "user", "content": text},
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "memory_extract",
                        "strict": True,
                        "schema": schema,
                    },
                },
                extra_body={"provider": {"require_parameters": True}},
            )
            content = self._message_text(response.choices[0].message)
            if not content:
                raise ValueError("Model returned no structured output")
            return MemoryExtract.model_validate_json(content)
        except LLMUnavailable:
            raise
        except Exception as exc:
            logger.exception("Memory extraction failed")
            raise LLMUnavailable(str(exc)) from exc

    def grounded_answer(self, query: str, evidence: list[dict[str, Any]]) -> str:
        if not evidence:
            return "I couldn't find that information in your Second Brain."
        context = "\n\n".join(
            f"[SOURCE {index}] {item['title']}\n{item['excerpt'][:600]}"
            for index, item in enumerate(evidence[:6], 1)
        )
        system = (
            "Answer only from the supplied Second Brain evidence. Do not add general "
            "knowledge unless explicitly labeled as such. If evidence is insufficient, "
            "say so. Prefer current facts unless history is requested. Cite claims inline "
            "as [SOURCE n]."
        )
        answer = self.compact_response(
            "grounded_answer", system, f"Question: {query}\n\nEvidence:\n{context}", max_tokens=500
        )["text"]
        if not answer:
            raise LLMUnavailable("OpenRouter returned an empty response")
        return answer

    def compact_response(self, mode: str, system: str, user: str, max_tokens: int = 500) -> dict[str, Any]:
        """Cost-controlled AI call with deterministic caching and a daily call ceiling."""
        model = self._model()
        cache_key = hashlib.sha256(f"{model}\n{mode}\n{system}\n{user}".encode("utf-8")).hexdigest()
        cache_enabled = bool(self._setting("ai_cache", True))
        if cache_enabled:
            try:
                with self._database().connect() as connection:
                    cached = connection.execute("SELECT response_text FROM ai_cache WHERE cache_key=?", (cache_key,)).fetchone()
            except Exception:
                cached = None
            if cached:
                self._record_usage(mode, model, 0, 0, True)
                return {"text": cached[0], "cache_hit": True, "input_tokens": 0, "output_tokens": 0}

        budget = max(int(self._setting("daily_ai_budget", 12)), 0)
        today = datetime.now(UTC).date().isoformat()
        try:
            with self._database().connect() as connection:
                used = connection.execute(
                    "SELECT COUNT(*) FROM ai_usage WHERE cache_hit=0 AND substr(created_at,1,10)=?", (today,)
                ).fetchone()[0]
        except Exception:
            used = 0
        if budget and used >= budget:
            raise LLMUnavailable(f"Daily AI call budget reached ({budget}). Cached and local tools remain available.")

        response = self._client().chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user[:18_000]}],
            max_tokens=max_tokens,
        )
        text = self._message_text(response.choices[0].message)
        if not text:
            raise LLMUnavailable("OpenRouter returned an empty response")
        usage = getattr(response, "usage", None)
        input_tokens = int(getattr(usage, "prompt_tokens", 0) or max((len(system) + len(user)) // 4, 1))
        output_tokens = int(getattr(usage, "completion_tokens", 0) or max(len(text) // 4, 1))
        now = datetime.now(UTC).isoformat()
        if cache_enabled:
            try:
                with self._database().transaction() as connection:
                    connection.execute(
                        "INSERT OR REPLACE INTO ai_cache(cache_key,mode,response_text,input_chars,output_chars,created_at) VALUES (?,?,?,?,?,?)",
                        (cache_key, mode, text, len(user), len(text), now),
                    )
            except Exception:
                logger.debug("Could not cache AI response", exc_info=True)
        self._record_usage(mode, model, input_tokens, output_tokens, False)
        return {"text": text, "cache_hit": False, "input_tokens": input_tokens, "output_tokens": output_tokens}

    @staticmethod
    def _database():
        from app.core.database import db

        return db

    def _setting(self, key: str, default: Any) -> Any:
        try:
            with self._database().connect() as connection:
                row = connection.execute("SELECT value_json FROM settings WHERE key=?", (key,)).fetchone()
            return json.loads(row[0]) if row else default
        except Exception:
            return default

    def _record_usage(self, mode: str, model: str, input_tokens: int, output_tokens: int, cache_hit: bool) -> None:
        try:
            with self._database().transaction() as connection:
                connection.execute(
                    "INSERT INTO ai_usage(id,mode,model,input_tokens,output_tokens,cache_hit,created_at) VALUES (?,?,?,?,?,?,?)",
                    (str(uuid4()), mode, model, input_tokens, output_tokens, int(cache_hit), datetime.now(UTC).isoformat()),
                )
        except Exception:
            logger.debug("Could not record AI usage", exc_info=True)


@lru_cache
def get_llm_service() -> LLMService:
    return LLMService()
