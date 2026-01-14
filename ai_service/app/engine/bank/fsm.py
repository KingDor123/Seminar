from typing import List, Tuple

from .constants import (
    STATE_ASK_AMOUNT,
    STATE_ASK_PURPOSE,
    STATE_CHECK_INCOME,
    STATE_SIGN_CONFIRM,
    STATE_GOODBYE,
    STATE_TERMINATE,
    ACTION_ASK_REQUIRED,
    ACTION_COACH_AND_ASK_REQUIRED,
    ACTION_WARN_AND_ASK_REQUIRED,
    ACTION_TERMINATE,
)
from .templates import (
    OPENING_GREETING,
    GREETING_REPLY,
    REQUIRED_QUESTIONS,
    RUDE_FIRST_WARNING,
    RUDE_SECOND_TERMINATION,
    REFUSAL_FIRST_EXPLANATION,
    REFUSAL_SECOND_TERMINATION,
    REFUSAL_EXAMPLES,
    REPAY_FIRST_EXPLANATION,
    REPAY_FIRST_EXAMPLE,
    REPAY_QUESTION,
    REPAY_SECOND_TERMINATION,
    COACH_TIPS,
    CLARIFICATION_TIPS,
)
from .types import BankDecision, BankSlots, BankStrikes


def merge_slots(existing: BankSlots, extracted: BankSlots) -> BankSlots:
    merged = BankSlots(**existing.model_dump())
    if extracted.amount is not None:
        merged.amount = extracted.amount
    if extracted.purpose:
        merged.purpose = extracted.purpose
    if extracted.income is not None:
        merged.income = extracted.income
    if extracted.confirm_accepted is not None:
        merged.confirm_accepted = extracted.confirm_accepted
    if extracted.id_details:
        if merged.id_details is None:
            merged.id_details = extracted.id_details
        else:
            if extracted.id_details.full_name:
                merged.id_details.full_name = extracted.id_details.full_name
            if extracted.id_details.id_number:
                merged.id_details.id_number = extracted.id_details.id_number
    return merged


def farthest_state(slots: BankSlots) -> str:
    if slots.amount is None:
        return STATE_ASK_AMOUNT
    if not slots.purpose:
        return STATE_ASK_PURPOSE
    if slots.income is None:
        return STATE_CHECK_INCOME
    if slots.confirm_accepted is False:
        return STATE_GOODBYE
    if slots.confirm_accepted is not True or not (slots.id_details and slots.id_details.id_number):
        return STATE_SIGN_CONFIRM
    return STATE_GOODBYE


def _required_question(state_id: str) -> str:
    return REQUIRED_QUESTIONS.get(state_id, "")


def _needs_coach(signals: List[str]) -> Tuple[bool, str | None]:
    if "GREETING" in signals:
        return False, None
    if "MISSING_GREETING" in signals:
        return True, COACH_TIPS["missing_greeting"]
    if "COMMANDING_TONE" in signals:
        return True, COACH_TIPS["commanding_tone"]
    if "RELEVANCE:LOW" in signals or "APPROPRIATE_FOR_BANK:COACH" in signals:
        return True, COACH_TIPS["low_relevance"]
    return False, None


def decide_next_action(
    current_state: str,
    slots: BankSlots,
    signals: List[str],
    strikes: BankStrikes,
    is_first_turn: bool,
    already_greeted: bool,
    suppress_strike_increment: bool = False,
) -> Tuple[BankDecision, BankStrikes]:
    next_state = farthest_state(slots)
    required_question = _required_question(next_state)

    updated_strikes = BankStrikes(**strikes.model_dump())

    decision = BankDecision(
        next_state=next_state,
        next_action=ACTION_ASK_REQUIRED,
        required_question=required_question,
    )

    if is_first_turn and not already_greeted:
        decision.greeting_line = OPENING_GREETING
        if any([slots.amount is not None, slots.purpose, slots.income is not None]):
            parts = []
            if slots.amount is not None:
                parts.append(f"סכום {slots.amount:,}")
            if slots.purpose:
                parts.append(f"מטרה: {slots.purpose}")
            if slots.income is not None:
                parts.append(f"הכנסה חודשית {slots.income:,}")
            if parts:
                decision.acknowledgement_line = "קיבלתי: " + ", ".join(parts) + "."
    if "GREETING" in signals and not decision.greeting_line:
        decision.greeting_line = GREETING_REPLY

    if "RUDE_LANGUAGE" in signals:
        new_count = updated_strikes.rude_strikes + (0 if suppress_strike_increment else 1)
        updated_strikes.rude_strikes = new_count
        if new_count >= 2:
            decision.next_action = ACTION_TERMINATE
            decision.next_state = STATE_TERMINATE
            decision.termination_text = RUDE_SECOND_TERMINATION
            return decision, updated_strikes
        decision.next_action = ACTION_WARN_AND_ASK_REQUIRED
        decision.warning_text = RUDE_FIRST_WARNING
        decision.coach_tip = COACH_TIPS["commanding_tone"]
        return decision, updated_strikes

    if "REFUSES_TO_REPAY" in signals:
        new_count = updated_strikes.repay_strikes + (0 if suppress_strike_increment else 1)
        updated_strikes.repay_strikes = new_count
        if new_count >= 2:
            decision.next_action = ACTION_TERMINATE
            decision.next_state = STATE_TERMINATE
            decision.termination_text = REPAY_SECOND_TERMINATION
            return decision, updated_strikes
        decision.next_action = ACTION_WARN_AND_ASK_REQUIRED
        decision.warning_text = REPAY_FIRST_EXPLANATION
        decision.coach_tip = REPAY_FIRST_EXAMPLE
        decision.required_question = REPAY_QUESTION
        return decision, updated_strikes

    if "REFUSES_TO_PROVIDE_INFO" in signals:
        new_count = updated_strikes.refusal_strikes + (0 if suppress_strike_increment else 1)
        updated_strikes.refusal_strikes = new_count
        if new_count >= 2:
            decision.next_action = ACTION_TERMINATE
            decision.next_state = STATE_TERMINATE
            decision.termination_text = REFUSAL_SECOND_TERMINATION
            return decision, updated_strikes
        decision.next_action = ACTION_WARN_AND_ASK_REQUIRED
        decision.warning_text = REFUSAL_FIRST_EXPLANATION
        decision.coach_tip = REFUSAL_EXAMPLES.get(next_state)
        return decision, updated_strikes

    if "CLARIFICATION_NEEDED" in signals:
        decision.next_action = ACTION_COACH_AND_ASK_REQUIRED
        decision.clarification_text = CLARIFICATION_TIPS.get(next_state)
        return decision, updated_strikes

    needs_coach, coach_tip = _needs_coach(signals)
    if needs_coach:
        decision.next_action = ACTION_COACH_AND_ASK_REQUIRED
        decision.coach_tip = coach_tip
        return decision, updated_strikes

    return decision, updated_strikes
