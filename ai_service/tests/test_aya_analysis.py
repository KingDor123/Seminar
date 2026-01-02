import json
import logging
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai_service.pipeline import HybridPipeline


@pytest.mark.asyncio
async def test_aya_json_retry_and_fallback(caplog: pytest.LogCaptureFixture):
    pipeline = HybridPipeline()
    pipeline.llm_client = AsyncMock()

    first_response = MagicMock()
    first_response.choices = [MagicMock(message=MagicMock(content="not json at all"))]

    second_response = MagicMock()
    second_response.choices = [MagicMock(message=MagicMock(content="still not json"))]

    pipeline.llm_client.chat.completions.create = AsyncMock(
        side_effect=[first_response, second_response]
    )

    caplog.set_level(logging.INFO, logger="HybridPipeline")

    analysis = await pipeline._analyze_with_aya([], "Hello", "persona", "goal")

    assert analysis.sentiment == "neutral"
    assert analysis.confidence < 0.5
    assert "Fallback" in analysis.reasoning
    assert pipeline.llm_client.chat.completions.create.call_count == 2
    assert any("retrying" in record.message for record in caplog.records)
    assert any("fallback" in record.message.lower() for record in caplog.records)


@pytest.mark.asyncio
async def test_contextual_sentiment_differs_with_history():
    pipeline = HybridPipeline()
    pipeline.llm_client = AsyncMock()

    async def fake_create(*args, **kwargs):
        payload = json.loads(kwargs["messages"][1]["content"])
        if payload["conversation_history"]:
            content = json.dumps(
                {
                    "sentiment": "negative",
                    "confidence": 0.72,
                    "reasoning": "Prior conflict changes interpretation.",
                    "detected_intent": "complaint",
                    "social_impact": "hinders"
                }
            )
        else:
            content = json.dumps(
                {
                    "sentiment": "neutral",
                    "confidence": 0.66,
                    "reasoning": "Single-turn is ambiguous.",
                    "detected_intent": "information_request",
                    "social_impact": "neutral"
                }
            )
        response = MagicMock()
        response.choices = [MagicMock(message=MagicMock(content=content))]
        return response

    pipeline.llm_client.chat.completions.create = AsyncMock(side_effect=fake_create)

    analysis_no_history = await pipeline._analyze_with_aya(
        [], "אפשר עזרה?", "persona", "goal"
    )
    analysis_with_history = await pipeline._analyze_with_aya(
        [{"role": "user", "content": "אתה לא מקשיב לי בכלל."}],
        "אפשר עזרה?",
        "persona",
        "goal"
    )

    assert analysis_no_history.sentiment != analysis_with_history.sentiment
