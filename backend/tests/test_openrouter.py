from types import SimpleNamespace

from app.services.llm_service import LLMService


class FakeCompletions:
    def __init__(self, content: str):
        self.content = content
        self.request = None

    def create(self, **kwargs):
        self.request = kwargs
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=self.content))]
        )


def fake_client(content: str):
    completions = FakeCompletions(content)
    return SimpleNamespace(chat=SimpleNamespace(completions=completions)), completions


def test_openrouter_model_slug_is_used_for_structured_extraction(monkeypatch):
    service = LLMService()
    client, completions = fake_client(
        '{"should_store":true,"operation":"CREATE","memory_type":"project",'
        '"title":"Atlas launch","fact":"Project Atlas launches in October",'
        '"entity":"Project Atlas","property_key":"launch date","category":"work",'
        '"tags":["atlas"],"importance":0.8,"confidence":0.95,'
        '"effective_from":null,"possible_conflicts":[]}'
    )
    monkeypatch.setattr(service, "_client", lambda: client)
    monkeypatch.setattr(service, "_model", lambda: "openai/gpt-5.4-nano")

    result = service.extract_memory("Remember that Project Atlas launches in October.")

    assert result.entity == "Project Atlas"
    assert completions.request["model"] == "openai/gpt-5.4-nano"
    assert completions.request["response_format"]["type"] == "json_schema"
    assert completions.request["extra_body"] == {"provider": {"require_parameters": True}}


def test_openrouter_chat_completion_is_grounded(monkeypatch):
    service = LLMService()
    client, completions = fake_client("Atlas launches in October. [SOURCE 1]")
    monkeypatch.setattr(service, "_client", lambda: client)
    monkeypatch.setattr(service, "_model", lambda: "openai/gpt-5.4-nano")

    answer = service.grounded_answer(
        "When does Atlas launch?",
        [{"title": "Atlas launch", "excerpt": "Atlas launches in October."}],
    )

    assert answer.endswith("[SOURCE 1]")
    assert completions.request["model"] == "openai/gpt-5.4-nano"
    assert "Evidence:" in completions.request["messages"][1]["content"]
