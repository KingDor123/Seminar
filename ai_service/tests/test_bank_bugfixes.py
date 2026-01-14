import re
import pytest

from app.engine.bank.analyzer import analyze_turn
from app.engine.bank.constants import (
    ACTION_ASK_REQUIRED,
    ACTION_COACH_AND_ASK_REQUIRED,
    ACTION_WARN_AND_REDIRECT,
    ACTION_BOUNDARY_AND_OFFER_RESTART,
    ACTION_END_CONVERSATION_SAFELY,
    STATE_ASK_AMOUNT,
    STATE_START,
    STATE_SIGN_CONFIRM,
    STATE_TERMINATE,
)
from app.engine.bank.fsm import decide_next_action, merge_slots, farthest_state
from app.engine.bank.responder import bank_responder
from app.engine.bank.templates import GREETING_REPLY, SIGN_CONFIRM_QUESTION, REFUSAL_EXAMPLES, ASK_AMOUNT_QUESTION
from app.engine.bank.types import BankDecision, BankSlots, BankStrikes


@pytest.mark.asyncio
async def test_bug_sign_confirm_never_self_identifies_strict(monkeypatch):
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
    assert "תעודת זהות" not in SIGN_CONFIRM_QUESTION
    assert "בדוי" in SIGN_CONFIRM_QUESTION


@pytest.mark.asyncio
async def test_bug_greeting_polite_ack_then_question(monkeypatch):
    async def echo_plan(messages):
        plan = messages[1]["content"]
        for line in plan.split("\n")[1:]:
            yield line.replace("- ", "")

    monkeypatch.setattr("app.engine.bank.responder.llm_client.generate_stream", echo_plan)

    analysis = analyze_turn("היי דנה מה שלומך?", STATE_START)
    slots = merge_slots(BankSlots(), analysis.slots)

    decision, strikes, _ = decide_next_action(
        current_state=STATE_START,
        slots=slots,
        signals=analysis.signals,
        strikes=BankStrikes(),
        is_first_turn=True,
        already_greeted=True,
        retry_count=0,
    )

    assert decision.next_action == ACTION_ASK_REQUIRED
    assert decision.coach_tip is None
    assert decision.warning_text is None
    assert decision.greeting_line == GREETING_REPLY
    assert strikes.refusal_strikes == 0

    chunks = []
    async for chunk in bank_responder.generate(decision):
        chunks.append(chunk)
    output = "".join(chunks)
    assert "טיפ:" not in output
    assert GREETING_REPLY in output
    assert ASK_AMOUNT_QUESTION in output


def test_regression_commanding_tone_still_coaches():
    analysis = analyze_turn("תביאי לי 20000 עכשיו", STATE_ASK_AMOUNT)
    slots = merge_slots(BankSlots(), analysis.slots)
    decision, _, _ = decide_next_action(
        current_state=STATE_ASK_AMOUNT,
        slots=slots,
        signals=analysis.signals,
        strikes=BankStrikes(),
        is_first_turn=False,
        already_greeted=True,
        retry_count=0,
    )
    assert decision.next_action == ACTION_COACH_AND_ASK_REQUIRED


def test_regression_rude_twice_terminates():
    strikes = BankStrikes()
    analysis = analyze_turn("מה את רוצה יא מטומטמת", STATE_ASK_AMOUNT)
    decision, strikes, _ = decide_next_action(
        current_state=STATE_ASK_AMOUNT,
        slots=merge_slots(BankSlots(), analysis.slots),
        signals=analysis.signals,
        strikes=strikes,
        is_first_turn=False,
        already_greeted=True,
        retry_count=0,
    )
    assert decision.next_action == ACTION_WARN_AND_REDIRECT
    analysis = analyze_turn("סתמי כבר", STATE_ASK_AMOUNT)
    decision, strikes, _ = decide_next_action(
        current_state=STATE_ASK_AMOUNT,
        slots=merge_slots(BankSlots(), analysis.slots),
        signals=analysis.signals,
        strikes=strikes,
        is_first_turn=False,
        already_greeted=True,
        retry_count=0,
    )
    assert decision.next_action == ACTION_BOUNDARY_AND_OFFER_RESTART
    analysis = analyze_turn("סתמי כבר", STATE_ASK_AMOUNT)
    decision, strikes, _ = decide_next_action(
        current_state=STATE_ASK_AMOUNT,
        slots=merge_slots(BankSlots(), analysis.slots),
        signals=analysis.signals,
        strikes=strikes,
        is_first_turn=False,
        already_greeted=True,
        retry_count=0,
    )
    assert decision.next_action == ACTION_END_CONVERSATION_SAFELY
    assert decision.next_state == STATE_TERMINATE


def test_regression_slot_skip_all_in_one():
    analysis = analyze_turn(
        "היי דנה אני רוצה הלוואה 10000 לרכב וההכנסה שלי 15000 בחודש",
        STATE_START,
    )
    slots = merge_slots(BankSlots(), analysis.slots)
    assert farthest_state(slots) == STATE_SIGN_CONFIRM
