import pytest

from app.engine.bank.analyzer import analyze_turn
from app.engine.bank.constants import (
    STATE_START,
    STATE_ASK_AMOUNT,
    STATE_ASK_PURPOSE,
    STATE_CHECK_INCOME,
    ACTION_COACH_AND_ASK_REQUIRED,
)
from app.engine.bank.fsm import decide_next_action, merge_slots
from app.engine.bank.templates import (
    ASK_AMOUNT_QUESTION,
    ASK_PURPOSE_QUESTION,
    ASK_PURPOSE_RETRY_1,
    PURPOSE_UNREALISTIC_TEXT,
    ESCAPE_OPTIONS,
)
from app.engine.bank.types import BankSlots, BankStrikes
from app.engine.bank.orchestrator import bank_orchestrator
from app.engine.state_manager import state_manager


def test_commanding_tone_coach_ask_amount():
    analysis = analyze_turn("תביאי לי כסף", STATE_START)
    slots = merge_slots(BankSlots(), analysis.slots)
    decision, _, _ = decide_next_action(
        current_state=STATE_START,
        slots=slots,
        signals=analysis.signals,
        strikes=BankStrikes(),
        is_first_turn=True,
        already_greeted=False,
        retry_count=0,
    )
    assert decision.next_action == ACTION_COACH_AND_ASK_REQUIRED
    assert ASK_AMOUNT_QUESTION in decision.required_question


@pytest.mark.asyncio
async def test_repeat_short_confusion_repeats_question(monkeypatch):
    async def echo_plan(messages):
        plan = messages[1]["content"]
        for line in plan.split("\n")[1:]:
            yield line.replace("- ", "")

    monkeypatch.setattr("app.engine.bank.responder.llm_client.generate_stream", echo_plan)

    session_id = "repeat-short"
    state_manager.clear_session(session_id)

    gen = bank_orchestrator.process_turn(session_id, "bank", "[START]", [])
    async for _ in gen:
        break
    await gen.aclose()

    gen = bank_orchestrator.process_turn(session_id, "bank", "שלום", [])
    async for _ in gen:
        pass
    await gen.aclose()

    chunks = []
    gen = bank_orchestrator.process_turn(session_id, "bank", "מה?", [])
    async for item in gen:
        if isinstance(item, str):
            chunks.append(item)
    await gen.aclose()
    output = "".join(chunks)
    assert ASK_AMOUNT_QUESTION in output
    assert "דוגמה: 20,000" in output


def test_purpose_free_text_computer_moves_to_income():
    analysis = analyze_turn("לקנות מחשב חדש", STATE_ASK_PURPOSE)
    assert analysis.slots.purpose == "מחשב"
    assert "HAS_PURPOSE" in analysis.signals

    slots = merge_slots(BankSlots(amount=10000), analysis.slots)
    decision, _, _ = decide_next_action(
        current_state=STATE_ASK_PURPOSE,
        slots=slots,
        signals=analysis.signals,
        strikes=BankStrikes(),
        is_first_turn=False,
        already_greeted=True,
        retry_count=0,
    )
    assert decision.next_state == STATE_CHECK_INCOME


def test_purpose_unrealistic_reasks_with_explanation():
    analysis = analyze_turn("לקנות חד קרן", STATE_ASK_PURPOSE)
    assert "PURPOSE_UNREALISTIC" in analysis.signals
    assert analysis.slots.purpose is None

    slots = merge_slots(BankSlots(amount=10000), analysis.slots)
    decision, _, _ = decide_next_action(
        current_state=STATE_ASK_PURPOSE,
        slots=slots,
        signals=analysis.signals,
        strikes=BankStrikes(),
        is_first_turn=False,
        already_greeted=True,
        retry_count=0,
    )
    assert decision.next_state == STATE_ASK_PURPOSE
    assert decision.clarification_text == PURPOSE_UNREALISTIC_TEXT
    assert decision.required_question in {ASK_PURPOSE_QUESTION, ASK_PURPOSE_RETRY_1}


def test_escape_hatch_options_after_two_irrelevant():
    analysis1 = analyze_turn("לא יודע", STATE_ASK_AMOUNT)
    decision1, _, retry1 = decide_next_action(
        current_state=STATE_ASK_AMOUNT,
        slots=merge_slots(BankSlots(), analysis1.slots),
        signals=analysis1.signals,
        strikes=BankStrikes(),
        is_first_turn=False,
        already_greeted=True,
        retry_count=0,
    )
    assert retry1 == 1

    analysis2 = analyze_turn("לא יודע", STATE_ASK_AMOUNT)
    decision2, _, retry2 = decide_next_action(
        current_state=STATE_ASK_AMOUNT,
        slots=merge_slots(BankSlots(), analysis2.slots),
        signals=analysis2.signals,
        strikes=BankStrikes(),
        is_first_turn=False,
        already_greeted=True,
        retry_count=retry1,
    )
    assert retry2 == 2
    assert decision2.options == ESCAPE_OPTIONS[STATE_ASK_AMOUNT]
