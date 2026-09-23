from __future__ import annotations

import re
from typing import Any

from app.models.schemas import MemoryCreate, MemoryExtract, MemoryOperation, MemoryType
from app.repositories.memory_repository import MemoryRepository
from app.utils.text import clean_text


MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"


class MemoryService:
    def __init__(self, repository: MemoryRepository | None = None) -> None:
        self.repository = repository or MemoryRepository()

    def local_extract(self, text: str) -> MemoryExtract:
        raw = clean_text(text)
        lowered = raw.lower()
        is_update = bool(re.match(r"^(change|update|replace|correct|actually)\b", lowered))
        memory_type = MemoryType.DECISION if "decid" in lowered or is_update else MemoryType.SEMANTIC
        if re.search(r"\b(todo|need to|must|task)\b", lowered):
            memory_type = MemoryType.TASK

        entity = None
        project_match = re.search(r"\bProject\s+([A-Z][\w-]*(?:\s+[A-Z][\w-]*){0,2})", raw)
        possessive_match = re.search(r"\b([A-Z][\w-]+(?:\s+[A-Z][\w-]+){0,2})['’]s\s+", raw)
        if project_match:
            entity = f"Project {project_match.group(1)}"
        elif possessive_match:
            entity = possessive_match.group(1)
        else:
            named = re.search(r"\b(?:that|for)\s+([A-Z][\w-]+)", raw)
            entity = named.group(1) if named else None

        property_key = self._property_key(lowered)
        fact = re.sub(r"^(remember(?: that)?|please remember(?: that)?|change|update|correct)\s+", "", raw, flags=re.I)
        month = re.search(rf"\b({MONTHS})\b", fact, flags=re.I)
        if is_update and entity and property_key == "launch_date" and month:
            fact = f"{entity} will launch in {month.group(1).title()}."

        title_bits = [entity, property_key.replace("_", " ").title() if property_key else None]
        title = " — ".join(bit for bit in title_bits if bit) or fact[:80]
        tags = [part for part in [property_key, memory_type.value] if part]
        return MemoryExtract(
            should_store=True,
            operation=MemoryOperation.UPDATE if is_update else MemoryOperation.CREATE,
            memory_type=memory_type,
            title=title,
            fact=fact,
            entity=entity,
            property_key=property_key,
            category="Project" if entity and entity.startswith("Project ") else None,
            tags=tags,
            importance=0.8 if memory_type in {MemoryType.DECISION, MemoryType.TASK} else 0.65,
            confidence=0.82,
        )

    @staticmethod
    def _property_key(lowered: str) -> str | None:
        mappings = {
            "launch_date": ("launch", "release date", "go live"),
            "price": ("price", "pricing", "cost", "rm", "$"),
            "database": ("postgresql", "mongodb", "database"),
            "deadline": ("deadline", "due date", "due "),
            "status": ("status", "state"),
        }
        for key, needles in mappings.items():
            if any(needle in lowered for needle in needles):
                return key
        words = re.findall(r"\w+", lowered)
        return words[0] if words else None

    def remember(self, payload: MemoryCreate, extracted: MemoryExtract | None = None) -> tuple[dict[str, Any], str]:
        memory = extracted or self.local_extract(payload.content)
        existing = self.repository.find_current(payload.entity or memory.entity, payload.property_key or memory.property_key)
        if existing and existing["normalized_fact"].strip().lower() == memory.fact.strip().lower() and memory.operation == MemoryOperation.CREATE:
            return existing, "CONFIRM"
        should_supersede = existing is not None and (
            memory.operation in {MemoryOperation.UPDATE, MemoryOperation.SUPERSEDE}
            or existing["normalized_fact"].lower() != memory.fact.lower()
        )
        data = {
            "memory_type": (payload.memory_type or memory.memory_type).value,
            "title": payload.title or memory.title,
            "content": payload.content,
            "normalized_fact": memory.fact,
            "entity": payload.entity or memory.entity,
            "property_key": payload.property_key or memory.property_key,
            "category": payload.category or memory.category,
            "tags": list(dict.fromkeys([*payload.tags, *memory.tags])),
            "source_type": payload.source_type,
            "project_id": payload.project_id,
            "importance_score": payload.importance_score or memory.importance,
            "confidence_score": payload.confidence_score or memory.confidence,
            "metadata": {"original_input": payload.content, "extractor": "local"},
        }
        created = self.repository.create(data, supersedes=existing["id"] if should_supersede else None)
        return created, "SUPERSEDE" if should_supersede else "CREATE"
