import pytest

from app.engine.bank.analyzer import analyze_turn
from app.engine.bank.constants import (
    STATE_START,
    STATE_ASK_AMOUNT,
    STATE_ASK_PURPOSE,
    STATE_CHECK_INCOME,
    STATE_INELIGIBLE_FINANCIAL,
    STATE_GOODBYE,
    STATE_TERMINATE,
    ACTION_COACH_AND_ASK_REQUIRED,
    ACTION_BOUNDARY_AND_OFFER_RESTART,
    ACTION_END_CONVERSATION_SAFELY,
)
from app.engine.bank.fsm import decide_next_action, merge_slots
from app.engine.bank.templates import (
    ASK_AMOUNT_QUESTION,
    MISSING_GREETING_COACH,
    RESTART_OPTIONS,
)
from app.engine.bank.types import BankSlots, BankStrikes
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


def test_missing_greeting_coaching_then_question():
    analysis = analyze_turn("אני צריך הלוואה", STATE_START)
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
    assert decision.coach_tip == MISSING_GREETING_COACH
    assert ASK_AMOUNT_QUESTION in decision.required_question


def test_refusal_restart_offer_after_two():
    strikes = BankStrikes()
    analysis1 = analyze_turn("לא רוצה", STATE_ASK_AMOUNT)
    decision1, strikes, _ = decide_next_action(
        current_state=STATE_ASK_AMOUNT,
        slots=merge_slots(BankSlots(), analysis1.slots),
        signals=analysis1.signals,
        strikes=strikes,
        is_first_turn=False,
        already_greeted=True,
        retry_count=0,
    )
    assert strikes.refusal_strikes == 1

    analysis2 = analyze_turn("עזבי אותי", STATE_ASK_AMOUNT)
    decision2, strikes, _ = decide_next_action(
        current_state=STATE_ASK_AMOUNT,
        slots=merge_slots(BankSlots(), analysis2.slots),
        signals=analysis2.signals,
        strikes=strikes,
        is_first_turn=False,
        already_greeted=True,
        retry_count=0,
    )
    assert strikes.refusal_strikes == 2
    assert decision2.next_action == ACTION_BOUNDARY_AND_OFFER_RESTART
    assert decision2.options == RESTART_OPTIONS


def test_threat_ends_immediately():
    analysis = analyze_turn("אני אפגע בך", STATE_ASK_AMOUNT)
    decision, strikes, _ = decide_next_action(
        current_state=STATE_ASK_AMOUNT,
        slots=merge_slots(BankSlots(), analysis.slots),
        signals=analysis.signals,
        strikes=BankStrikes(),
        is_first_turn=False,
        already_greeted=True,
        retry_count=0,
    )
    assert decision.next_action == ACTION_END_CONVERSATION_SAFELY
    assert decision.next_state == STATE_TERMINATE
    assert strikes.threat_strikes == 1


def test_purpose_not_invented_when_missing():
    analysis = analyze_turn("לא יודע עדיין", STATE_ASK_PURPOSE)
    assert analysis.slots.purpose is None
    assert "HAS_PURPOSE" not in analysis.signals


@pytest.mark.asyncio
async def test_ineligible_then_goodbye_no_loop():
    session_id = "policy-ineligible"
    state_manager.clear_session(session_id)

    gen = bank_orchestrator.process_turn(session_id, "bank", "[START]", [])
    async for _ in gen:
        break
    await gen.aclose()

    next_state, _ = await _next_analysis(session_id, "שלום")
    assert next_state == STATE_ASK_AMOUNT

    next_state, _ = await _next_analysis(session_id, "10000")
    assert next_state == STATE_ASK_PURPOSE

    next_state, _ = await _next_analysis(session_id, "שיפוץ הבית")
    assert next_state == STATE_CHECK_INCOME

    next_state, _ = await _next_analysis(session_id, "אין לי הכנסה")
    assert next_state == STATE_INELIGIBLE_FINANCIAL

    next_state, _ = await _next_analysis(session_id, "אוקיי")
    assert next_state == STATE_GOODBYE


@pytest.mark.asyncio
async def test_post_goodbye_offer_restart_once():
    session_id = "policy-goodbye"
    state_manager.clear_session(session_id)

    gen = bank_orchestrator.process_turn(session_id, "bank", "[START]", [])
    async for _ in gen:
        break
    await gen.aclose()

    await _next_analysis(session_id, "10000 לרכב הכנסה 15000")
    next_state, _ = await _next_analysis(session_id, "מאשר")
    assert next_state == STATE_GOODBYE

    next_state, _ = await _next_analysis(session_id, "עוד משהו")
    assert next_state == STATE_GOODBYE

    next_state, _ = await _next_analysis(session_id, "לא")
    assert next_state == STATE_TERMINATE
