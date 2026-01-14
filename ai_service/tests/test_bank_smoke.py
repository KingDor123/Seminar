import pytest

from app.engine.bank.orchestrator import bank_orchestrator


@pytest.mark.asyncio
async def test_bank_orchestrator_smoke_slot_skip():
    gen = bank_orchestrator.process_turn("smoke", "bank", "[START]", [])
    async for _ in gen:
        break

    gen2 = bank_orchestrator.process_turn(
        "smoke",
        "bank",
        "היי דנה אני רוצה הלוואה 10000 לרכב וההכנסה שלי 15000 בחודש",
        [],
    )

    next_state = None
    async for item in gen2:
        if isinstance(item, dict) and item.get("type") == "analysis":
            next_state = item.get("next_state")
            break

    assert next_state == "sign_confirm"
