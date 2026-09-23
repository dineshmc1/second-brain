from app.models.schemas import ChatRequest, MemoryExtract
from app.services.chat_service import ChatService
from app.services.llm_service import LLMUnavailable


class OfflineLLM:
    def extract_memory(self, text):
        raise LLMUnavailable("offline")

    def grounded_answer(self, query, evidence):
        raise LLMUnavailable("offline")


def test_offline_memory_round_trip(database):
    service = ChatService(database)
    service.llm = OfflineLLM()
    remembered = service.respond(ChatRequest(message="Remember that Project Atlas will launch in October."))
    answer = service.respond(ChatRequest(message="When will Project Atlas launch?"))
    assert remembered["memory_action"] == "CREATE"
    assert "October" in answer["answer"]
    assert answer["offline"] is True
    assert answer["citations"]


def test_offline_unknown_question_does_not_fabricate(database):
    service = ChatService(database)
    service.llm = OfflineLLM()
    answer = service.respond(ChatRequest(message="What is my favorite telescope?"))
    assert "couldn't find" in answer["answer"]
    assert answer["citations"] == []


def test_malformed_llm_json_is_rejected():
    try:
        MemoryExtract.model_validate_json('{"should_store": true, "importance": "impossible"}')
    except Exception:
        pass
    else:
        raise AssertionError("Malformed model output must be rejected")

