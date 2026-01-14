import re
import pytest

from app.engine.bank.analyzer import analyze_turn
from app.engine.bank.constants import (
    ACTION_ASK_REQUIRED,
    STATE_START,
    STATE_SIGN_CONFIRM,
)
from app.engine.bank.fsm import decide_next_action, merge_slots
from app.engine.bank.responder import bank_responder
from app.engine.bank.templates import GREETING_REPLY, SIGN_CONFIRM_QUESTION, REFUSAL_EXAMPLES
from app.engine.bank.types import BankDecision, BankSlots, BankStrikes


@pytest.mark.asyncio
async def test_bugA_sign_confirm_never_self_identifies(monkeypatch):
    async def fake_stream(_messages):
        yield "כן, אני מאשר את הבקשה. השם שלי הוא דנה כהן ותעודת הזהות שלי היא 123456789."

    monkeypatch.setattr("app.engine.bank.responder.llm_client.generate_stream", fake_stream)

    decision = BankDecision(
        next_state=STATE_SIGN_CONFIRM,
        next_action="ASK_REQUIRED",
        required_question=SIGN_CONFIRM_QUESTION,
    )

    chunks = []
    async for chunk in bank_responder.generate(decision):
        chunks.append(chunk)
    output = "".join(chunks)

    assert SIGN_CONFIRM_QUESTION in output
    assert "תעודת הזהות שלי" not in output
    assert "השם שלי" not in output
    assert re.search(r"\b\d{7,9}\b", output) is None


def test_bugA_no_hardcoded_dana_id():
    assert "דנה כהן" not in SIGN_CONFIRM_QUESTION
    assert "123456789" not in SIGN_CONFIRM_QUESTION
    assert "123456789" not in REFUSAL_EXAMPLES.get("sign_confirm", "")


def test_bugB_greeting_is_polite_not_scolding():
    analysis = analyze_turn("היי דנה מה שלומך?", STATE_START)
    slots = merge_slots(BankSlots(), analysis.slots)

    decision, strikes = decide_next_action(
        current_state=STATE_START,
        slots=slots,
        signals=analysis.signals,
        strikes=BankStrikes(),
        is_first_turn=True,
        already_greeted=True,
    )

    assert decision.next_action == ACTION_ASK_REQUIRED
    assert decision.coach_tip is None
    assert decision.warning_text is None
    assert decision.greeting_line == GREETING_REPLY
    assert strikes.refusal_strikes == 0
