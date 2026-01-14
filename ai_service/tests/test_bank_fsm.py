import pytest

from app.engine.bank.analyzer import analyze_turn
from app.engine.bank.constants import (
    STATE_START,
    STATE_ASK_AMOUNT,
    STATE_ASK_PURPOSE,
    STATE_CHECK_INCOME,
    STATE_SIGN_CONFIRM,
    STATE_TERMINATE,
    ACTION_COACH_AND_ASK_REQUIRED,
    ACTION_WARN_AND_REDIRECT,
    ACTION_BOUNDARY_AND_OFFER_RESTART,
    ACTION_END_CONVERSATION_SAFELY,
)
from app.engine.bank.fsm import merge_slots, farthest_state, decide_next_action
from app.engine.bank.templates import SIGN_CONFIRM_QUESTION
from app.engine.bank.types import BankSlots, BankStrikes


def test_early_slots_skip_to_sign_confirm():
    text = "היי דנה אני רוצה 20 אלף כדי לקנות רכב ומכניס 70 אלף בחודש"
    analysis = analyze_turn(text, STATE_START)
    merged = merge_slots(BankSlots(), analysis.slots)
    assert farthest_state(merged) == STATE_SIGN_CONFIRM

    decision, strikes, _ = decide_next_action(
        current_state=STATE_START,
        slots=merged,
        signals=analysis.signals,
        strikes=BankStrikes(),
        is_first_turn=True,
        already_greeted=False,
        retry_count=0,
    )
    assert decision.next_state == STATE_SIGN_CONFIRM
    assert decision.greeting_line is not None
    assert decision.acknowledgement_line is not None
    assert strikes.rude_strikes == 0


def test_rude_twice_terminates():
    strikes = BankStrikes()

    analysis1 = analyze_turn("אתם חרא", STATE_ASK_AMOUNT)
    decision1, strikes, _ = decide_next_action(
        current_state=STATE_ASK_AMOUNT,
        slots=merge_slots(BankSlots(), analysis1.slots),
        signals=analysis1.signals,
        strikes=strikes,
        is_first_turn=False,
        already_greeted=True,
        retry_count=0,
    )
    assert decision1.next_action == ACTION_WARN_AND_REDIRECT
    assert strikes.rude_strikes == 1

    analysis2 = analyze_turn("חרא", STATE_ASK_AMOUNT)
    decision2, strikes, _ = decide_next_action(
        current_state=STATE_ASK_AMOUNT,
        slots=merge_slots(BankSlots(), analysis2.slots),
        signals=analysis2.signals,
        strikes=strikes,
        is_first_turn=False,
        already_greeted=True,
        retry_count=0,
    )
    assert decision2.next_action == ACTION_BOUNDARY_AND_OFFER_RESTART
    assert strikes.rude_strikes == 2
    analysis3 = analyze_turn("חרא", STATE_ASK_AMOUNT)
    decision3, strikes, _ = decide_next_action(
        current_state=STATE_ASK_AMOUNT,
        slots=merge_slots(BankSlots(), analysis3.slots),
        signals=analysis3.signals,
        strikes=strikes,
        is_first_turn=False,
        already_greeted=True,
        retry_count=0,
    )
    assert decision3.next_action == ACTION_END_CONVERSATION_SAFELY
    assert decision3.next_state == STATE_TERMINATE
    assert strikes.rude_strikes == 3


def test_refusal_twice_terminates():
    strikes = BankStrikes()

    analysis1 = analyze_turn("לא רוצה לענות", STATE_ASK_AMOUNT)
    decision1, strikes, _ = decide_next_action(
        current_state=STATE_ASK_AMOUNT,
        slots=merge_slots(BankSlots(), analysis1.slots),
        signals=analysis1.signals,
        strikes=strikes,
        is_first_turn=False,
        already_greeted=True,
        retry_count=0,
    )
    assert decision1.next_action == ACTION_WARN_AND_REDIRECT
    assert strikes.refusal_strikes == 1

    analysis2 = analyze_turn("לא רוצה לענות", STATE_ASK_AMOUNT)
    decision2, strikes, _ = decide_next_action(
        current_state=STATE_ASK_AMOUNT,
        slots=merge_slots(BankSlots(), analysis2.slots),
        signals=analysis2.signals,
        strikes=strikes,
        is_first_turn=False,
        already_greeted=True,
        retry_count=0,
    )
    assert decision2.next_action == ACTION_BOUNDARY_AND_OFFER_RESTART
    assert strikes.refusal_strikes == 2


def test_commanding_tone_triggers_coaching():
    analysis = analyze_turn("תני לי 20 אלף", STATE_ASK_AMOUNT)
    merged = merge_slots(BankSlots(), analysis.slots)

    decision, strikes, _ = decide_next_action(
        current_state=STATE_ASK_AMOUNT,
        slots=merged,
        signals=analysis.signals,
        strikes=BankStrikes(),
        is_first_turn=False,
        already_greeted=True,
        retry_count=0,
    )
    assert decision.next_action == ACTION_COACH_AND_ASK_REQUIRED
    assert decision.next_state == STATE_ASK_PURPOSE
    assert strikes.rude_strikes == 0


def test_progresses_through_states():
    slots = BankSlots()

    analysis1 = analyze_turn("20 אלף", STATE_ASK_AMOUNT)
    slots = merge_slots(slots, analysis1.slots)
    assert farthest_state(slots) == STATE_ASK_PURPOSE

    analysis2 = analyze_turn("לרכב", STATE_ASK_PURPOSE)
    slots = merge_slots(slots, analysis2.slots)
    assert farthest_state(slots) == STATE_CHECK_INCOME

    analysis3 = analyze_turn("מכניס 10000", STATE_CHECK_INCOME)
    slots = merge_slots(slots, analysis3.slots)
    assert farthest_state(slots) == STATE_SIGN_CONFIRM


def test_clarification_is_not_refusal():
    analysis = analyze_turn("לא הבנתי", STATE_ASK_AMOUNT)
    decision, strikes, _ = decide_next_action(
        current_state=STATE_ASK_AMOUNT,
        slots=merge_slots(BankSlots(), analysis.slots),
        signals=analysis.signals,
        strikes=BankStrikes(),
        is_first_turn=False,
        already_greeted=True,
        retry_count=0,
    )
    assert decision.next_action == ACTION_COACH_AND_ASK_REQUIRED
    assert strikes.refusal_strikes == 0
    assert decision.clarification_text is not None


def test_id_details_extraction_and_template():
    analysis = analyze_turn("שמי דנה לוי ת.ז 123456789", STATE_SIGN_CONFIRM)
    assert analysis.slots.id_details is not None
    assert analysis.slots.id_details.full_name == "דנה לוי"
    assert analysis.slots.id_details.id_number == "123456789"

    assert "כתובת" not in SIGN_CONFIRM_QUESTION
    assert "טלפון" not in SIGN_CONFIRM_QUESTION
