from app.api import inbox as inbox_api
from app.api import tasks as tasks_api
from app.models.schemas import InboxCreate, InboxProcess, LearningGoalCreate, LearningNodePatch, LearningRun, TaskBreakdown
from app.services.learning_service import LearningService
from app.services.llm_service import LLMUnavailable


class OfflineCompactLLM:
    def compact_response(self, *args, **kwargs):
        raise LLMUnavailable("offline")


def test_smart_inbox_routes_capture_to_task(database, monkeypatch):
    monkeypatch.setattr(inbox_api, "db", database)
    item = inbox_api.capture(InboxCreate(content="Need to prepare the launch checklist"))
    assert item["suggested_type"] == "task"
    result = inbox_api.process(item["id"], InboxProcess(action="task"))
    assert result["processed"] is True
    with database.connect() as connection:
        assert connection.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] == 1
        assert connection.execute("SELECT status FROM inbox_items").fetchone()[0] == "processed"


def test_task_breakdown_has_offline_low_cost_fallback(database, monkeypatch):
    monkeypatch.setattr(tasks_api, "db", database)
    monkeypatch.setattr(tasks_api, "get_llm_service", lambda: OfflineCompactLLM())
    result = tasks_api.breakdown(TaskBreakdown(title="Launch a research newsletter"))
    assert result["ai_used"] is False
    assert len(result["cards"]) == 5
    assert len(tasks_api.list_tasks()) == 6


def test_goal_compiler_and_learning_modes_work_offline(database, monkeypatch):
    from app.services import learning_service

    monkeypatch.setattr(learning_service, "get_llm_service", lambda: OfflineCompactLLM())
    service = LearningService(database)
    goal = service.create_goal(LearningGoalCreate(title="Systems thinking", objective="Diagnose feedback loops in real projects"))
    assert len(goal["nodes"]) == 7
    assert goal["nodes"][0]["status"] == "ready"

    updated = service.patch_node(goal["nodes"][0]["id"], LearningNodePatch(status="mastered", mastery=100).model_dump())
    assert updated["mastery"] == 100
    refreshed = service.goals()[0]
    assert refreshed["nodes"][1]["status"] == "ready"

    session = service.run(LearningRun(mode="transfer", input="Feedback loops", depth="quick"))
    assert session["local"] is True
    assert "physical system" in session["result"]

