from __future__ import annotations

import re
from datetime import UTC, datetime
from uuid import uuid4

from app.core.database import Database, db
from app.models.schemas import ChatRequest, Citation, MemoryCreate
from app.services.llm_service import LLMService, LLMUnavailable, get_llm_service
from app.services.memory_service import MemoryService
from app.services.retrieval_service import RetrievalService


class ChatService:
    def __init__(self, database: Database = db) -> None:
        self.db = database
        from app.repositories.memory_repository import MemoryRepository

        self.memories = MemoryService(MemoryRepository(database))
        self.retrieval = RetrievalService(database)
        self.llm: LLMService = get_llm_service()

    def respond(self, request: ChatRequest) -> dict:
        conversation_id = request.conversation_id or self._create_conversation(request.project_id, request.message)
        self._save_message(conversation_id, "user", request.message)
        if self._is_memory_command(request.message):
            extracted = self.memories.local_extract(request.message)
            try:
                cloud = self.llm.extract_memory(request.message)
                if cloud.should_store:
                    extracted = cloud
            except LLMUnavailable:
                pass
            memory, action = self.memories.remember(
                MemoryCreate(content=request.message, project_id=request.project_id, source_type="conversation"),
                extracted,
            )
            if action == "SUPERSEDE" and memory.get("supersedes_memory_id"):
                old = self.memories.repository.get(memory["supersedes_memory_id"])
                answer = f"Updated {memory['title']} from “{old['normalized_fact']}” to “{memory['normalized_fact']}”."
            else:
                answer = f"Remembered: {memory['normalized_fact']}"
            citations = [Citation(id=memory["id"], source_type="memory", label=memory["title"], excerpt=memory["normalized_fact"], score=1)]
            self._save_message(conversation_id, "assistant", answer, citations)
            return self._response(answer, citations, conversation_id, [memory["id"]], action, False)

        evidence = self.retrieval.search(request.message, limit=8, project_id=request.project_id)
        citations = [
            Citation(
                id=item["id"], source_type=item["kind"], label=(
                    f"{item['title']} — Page {item['page']}" if item.get("page") else item["title"]
                ), page=item.get("page"), excerpt=item["excerpt"][:280], score=item["score"]
            ) for item in evidence
        ]
        offline = False
        try:
            answer = self.llm.grounded_answer(request.message, evidence)
        except LLMUnavailable:
            offline = True
            answer = self._local_answer(request.message, evidence)
        self._save_message(conversation_id, "assistant", answer, citations)
        memory_ids = [item["id"] for item in evidence if item["kind"] == "memory"]
        return self._response(answer, citations, conversation_id, memory_ids, None, offline)

    @staticmethod
    def _is_memory_command(message: str) -> bool:
        lowered = message.strip().lower()
        return bool(re.match(r"^(remember|save|note that|change|update|correct|i decided|i chose)\b", lowered)) or (
            not lowered.endswith("?") and bool(re.search(r"\b(will launch|pricing is|price is|i need to)\b", lowered))
        )

    @staticmethod
    def _local_answer(query: str, evidence: list[dict]) -> str:
        if not evidence:
            return "I couldn't find that information in your Second Brain."
        historical = any(word in query.lower() for word in ("previous", "before", "old", "history"))
        preferred = evidence
        if historical:
            history = [item for item in evidence if item.get("status") in {"superseded", "historical"}]
            preferred = history or evidence
        top = preferred[0]
        return f"{top['excerpt']}\n\nSource: [{top['title']}]"

    def _create_conversation(self, project_id: str | None, first_message: str) -> str:
        conversation_id = str(uuid4())
        now = datetime.now(UTC).isoformat()
        with self.db.transaction() as connection:
            connection.execute(
                "INSERT INTO conversations(id,title,project_id,created_at,updated_at) VALUES (?,?,?,?,?)",
                (conversation_id, first_message[:80], project_id, now, now),
            )
        return conversation_id

    def _save_message(self, conversation_id: str, role: str, content: str, citations: list[Citation] | None = None) -> None:
        import json

        now = datetime.now(UTC).isoformat()
        with self.db.transaction() as connection:
            connection.execute(
                "INSERT INTO messages(id,conversation_id,role,content,citations_json,created_at) VALUES (?,?,?,?,?,?)",
                (str(uuid4()), conversation_id, role, content,
                 json.dumps([citation.model_dump() for citation in citations or []]), now),
            )
            connection.execute("UPDATE conversations SET updated_at=? WHERE id=?", (now, conversation_id))

    @staticmethod
    def _response(answer: str, citations: list[Citation], conversation_id: str,
                  memory_ids: list[str], action: str | None, offline: bool) -> dict:
        return {
            "answer": answer, "citations": [citation.model_dump() for citation in citations],
            "confidence": min(0.98, 0.45 + len(citations) * 0.1) if citations else 0.1,
            "retrieved_memory_ids": memory_ids, "conversation_id": conversation_id,
            "memory_action": action, "offline": offline,
        }
