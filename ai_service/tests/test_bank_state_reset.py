import json

import pytest

from app.engine.bank.constants import STATE_ASK_AMOUNT, STATE_GOODBYE, STATE_START
from app.engine.bank.types import BankSessionState, BankSlots, BankStrikes, IdDetails
from app.engine.bank.orchestrator import bank_orchestrator
from app.engine.state_manager import SessionStateManager


def _write_stale_session(store_path):
    bank_state = BankSessionState(
        current_state_id=STATE_GOODBYE,
        slots=BankSlots(
            amount=10000,
            purpose="רכב",
            income=15000,
            confirm_accepted=True,
            id_details=IdDetails(full_name="בדיקה", id_number="123456789"),
        ),
        strikes=BankStrikes(rude_strikes=1, refusal_strikes=1, repay_strikes=0),
        turn_count=6,
        greeted=True,
        last_user_text="ישן",
        last_state_id=STATE_GOODBYE,
    )
    payload = {
        "1": {
            "scenario_id": "bank",
            "current_node_id": bank_state.current_state_id,
            "variables": {},
            "bank_state": bank_state.model_dump(),
        }
    }
    store_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


@pytest.mark.asyncio
async def test_start_resets_persisted_state(tmp_path, monkeypatch):
    store_path = tmp_path / "session_store.json"
    _write_stale_session(store_path)
    manager = SessionStateManager(persistence_file=str(store_path))
    monkeypatch.setattr("app.engine.bank.orchestrator.state_manager", manager)

    gen = bank_orchestrator.process_turn("1", "bank", "[START]", [])
    async for _ in gen:
        break
    await gen.aclose()

    bank_state = manager.get_state("1").bank_state
    assert bank_state.current_state_id == STATE_START
    assert bank_state.slots.amount is None
    assert bank_state.slots.purpose is None
    assert bank_state.slots.income is None
    assert bank_state.slots.confirm_accepted is None
    assert bank_state.slots.id_details is None
    assert bank_state.strikes.rude_strikes == 0
    assert bank_state.strikes.refusal_strikes == 0
    assert bank_state.strikes.repay_strikes == 0

    gen2 = bank_orchestrator.process_turn("1", "bank", "היי מה קורה?", [])
    next_state = None
    async for item in gen2:
        if isinstance(item, dict) and item.get("type") == "analysis":
            next_state = item.get("next_state")
            break
    await gen2.aclose()

    assert next_state == STATE_ASK_AMOUNT
