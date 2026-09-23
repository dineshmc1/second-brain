from app.core.database import db
from app.models.schemas import MemoryCreate
from app.repositories.memory_repository import MemoryRepository
from app.services.memory_service import MemoryService


def main():
    db.migrate()
    service = MemoryService(MemoryRepository(db))
    examples = [
        "Remember that Project Second Brain uses local-first storage.",
        "Remember that retrieval should prioritize evidence before confidence.",
        "I decided to use SQLite because the application must remain portable and local.",
    ]
    for example in examples:
        memory, operation = service.remember(MemoryCreate(content=example, source_type="demo"))
        print(operation, memory["normalized_fact"])


if __name__ == "__main__":
    main()

