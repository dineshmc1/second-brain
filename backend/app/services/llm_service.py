from __future__ import annotations

import json
import logging
from functools import lru_cache
from typing import Any

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
            f"[SOURCE {index}] {item['title']}\n{item['excerpt']}"
            for index, item in enumerate(evidence, 1)
        )
        response = self._client().chat.completions.create(
            model=self._model(),
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Answer only from the supplied Second Brain evidence. Do not add general "
                        "knowledge unless explicitly labeled as such. If evidence is insufficient, "
                        "say so. Prefer current facts unless history is requested. Cite claims inline "
                        "as [SOURCE n]."
                    ),
                },
                {"role": "user", "content": f"Question: {query}\n\nEvidence:\n{context}"},
            ],
            max_tokens=800,
        )
        answer = self._message_text(response.choices[0].message)
        if not answer:
            raise LLMUnavailable("OpenRouter returned an empty response")
        return answer


@lru_cache
def get_llm_service() -> LLMService:
    return LLMService()
