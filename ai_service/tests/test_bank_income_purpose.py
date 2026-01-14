import pytest

from app.engine.bank.constants import (
    STATE_ASK_AMOUNT,
    STATE_ASK_PURPOSE,
    STATE_CHECK_INCOME,
    STATE_INELIGIBLE_FINANCIAL,
)
from app.engine.bank.orchestrator import bank_orchestrator
from app.engine.state_manager import state_manager


async def _next_analysis(session_id: str, text: str):
    gen = bank_orchestrator.process_turn(session_id, "bank", text, [])
    next_state = None
    signals = []
    async for item in gen:
        if isinstance(item, dict) and item.get("type") == "analysis":
            next_state = item.get("next_state")
            signals = item.get("signals", [])
            break
    await gen.aclose()
    return next_state, signals


@pytest.mark.asyncio
async def test_income_zero_and_purpose_flow():
    session_id = "income-purpose-flow"
    state_manager.clear_session(session_id)

    gen = bank_orchestrator.process_turn(session_id, "bank", "[START]", [])
    async for _ in gen:
        break
    await gen.aclose()

    next_state, _ = await _next_analysis(session_id, "היי מה קורה?")
    assert next_state == STATE_ASK_AMOUNT

    next_state, _ = await _next_analysis(session_id, "10000")
    assert next_state == STATE_ASK_PURPOSE

    next_state, signals = await _next_analysis(session_id, "לשפץ את הבית שלי")
    assert next_state == STATE_CHECK_INCOME
    assert "HAS_PURPOSE" in signals

    next_state, signals = await _next_analysis(session_id, "אין לי")
    assert next_state == STATE_INELIGIBLE_FINANCIAL
    assert "HAS_INCOME" in signals
    assert "FINANCIAL_INELIGIBLE" in signals

    next_state, _ = await _next_analysis(session_id, "0")
    assert next_state == STATE_INELIGIBLE_FINANCIAL
