from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from ai_service.main import app
from app.routers import conversation


class DummyPipeline:
    def __init__(self) -> None:
        self.calls = []

    async def process_user_message_stream(self, **kwargs):
        self.calls.append(kwargs)
        yield {
            "type": "analysis",
            "sentiment": "neutral",
            "confidence": 0.6,
            "reasoning": "Test analysis.",
            "detected_intent": "test",
            "social_impact": "neutral"
        }
        yield "ok"


def test_interact_missing_scenario_id():
    client = TestClient(app)
    response = client.post(
        "/ai/interact",
        data={"session_id": "1", "text": "hello"}
    )
    assert response.status_code == 400
    assert "scenario_id" in response.json()["detail"]


def test_interact_invalid_scenario_id(monkeypatch):
    client = TestClient(app)
    monkeypatch.setattr(conversation, "_fetch_scenario", AsyncMock(return_value=None))
    response = client.post(
        "/ai/interact",
        data={"session_id": "1", "text": "hello", "scenario_id": "unknown"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid scenario_id"


def test_interact_valid_scenario_loads_server_context(monkeypatch):
    client = TestClient(app)
    dummy_pipeline = DummyPipeline()

    monkeypatch.setattr(conversation, "_fetch_scenario", AsyncMock(return_value={
        "scenario_id": "interview",
        "persona_prompt": "SERVER PERSONA",
        "scenario_goal": "SERVER GOAL",
        "difficulty": 2
    }))
    monkeypatch.setattr(conversation, "_fetch_history", AsyncMock(return_value=[]))
    monkeypatch.setattr(conversation, "_save_message", AsyncMock())
    monkeypatch.setattr(conversation, "get_pipeline", lambda: dummy_pipeline)

    response = client.post(
        "/ai/interact",
        data={"session_id": "1", "text": "hello", "scenario_id": "interview"}
    )

    assert response.status_code == 200
    _ = response.text
    assert dummy_pipeline.calls
    assert dummy_pipeline.calls[0]["base_system_prompt"] == "SERVER PERSONA"
    assert dummy_pipeline.calls[0]["scenario_goal"] == "SERVER GOAL"
