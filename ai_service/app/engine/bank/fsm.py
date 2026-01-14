from typing import List, Tuple

from .constants import (
    STATE_ASK_AMOUNT,
    STATE_ASK_PURPOSE,
    STATE_CHECK_INCOME,
    STATE_INELIGIBLE_FINANCIAL,
    STATE_SIGN_CONFIRM,
    STATE_GOODBYE,
    STATE_TERMINATE,
    ACTION_ASK_REQUIRED,
    ACTION_COACH_AND_ASK_REQUIRED,
    ACTION_WARN_AND_REDIRECT,
    ACTION_BOUNDARY_AND_OFFER_RESTART,
    ACTION_END_CONVERSATION_SAFELY,
    ACTION_OFFER_RESTART,
    ACTION_TERMINATE,
)
from .templates import (
    OPENING_GREETING,
    GREETING_REPLY,
    REQUIRED_QUESTIONS,
    RETRY_QUESTIONS,
    WARN_RUDE_TEXT,
    WARN_REDIRECT_PREFIX,
    BOUNDARY_RESTART_TEXT,
    END_CONVERSATION_SAFE,
    WARN_REFUSAL_TEXT,
    RESTART_OFFER_TEXT,
    RESTART_OPTIONS,
    REFUSAL_EXAMPLES,
    REPAY_FIRST_EXPLANATION,
    REPAY_FIRST_EXAMPLE,
    REPAY_QUESTION,
    REPAY_SECOND_TERMINATION,
    COACH_TIPS,
    CLARIFICATION_TIPS,
    INELIGIBLE_OPTIONS,
    SUPPORTIVE_LINES,
    ESCAPE_OPTIONS,
    ESCAPE_HINTS,
    PURPOSE_UNREALISTIC_TEXT,
    PURPOSE_ILLEGAL_TEXT,
)
from .types import BankDecision, BankSlots, BankStrikes

ESCAPE_AFTER_RETRIES = 2  # After 2 failed turns, offer quick options to prevent loops.


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
    if slots.income <= 0:
        return STATE_INELIGIBLE_FINANCIAL
    if slots.confirm_accepted is None:
        return STATE_SIGN_CONFIRM
    return STATE_GOODBYE


def _required_question(state_id: str) -> str:
    return REQUIRED_QUESTIONS.get(state_id, "")

def _question_for_state(state_id: str, retry_index: int) -> str:
    if state_id in RETRY_QUESTIONS:
        return RETRY_QUESTIONS[state_id].get(retry_index, RETRY_QUESTIONS[state_id][2])
    return _required_question(state_id)


def _needs_coach(signals: List[str]) -> Tuple[bool, str | None]:
    if "GREETING" in signals:
        return False, None
    if "MISSING_GREETING" in signals:
        return True, COACH_TIPS["missing_greeting"]
    if "COMMANDING_TONE" in signals:
        return True, COACH_TIPS["commanding_tone"]
    if "IRRELEVANT" in signals or "RELEVANCE:LOW" in signals or "APPROPRIATE_FOR_BANK:COACH" in signals:
        return True, COACH_TIPS["low_relevance"]
    return False, None


def _apply_retry_controls(
    decision: BankDecision,
    state_id: str,
    is_retry: bool,
    retry_next: int,
) -> bool:
    if is_retry and retry_next >= 3:
        decision.next_action = ACTION_OFFER_RESTART
        decision.required_question = RESTART_OFFER_TEXT
        decision.options = RESTART_OPTIONS
        return True
    if is_retry and retry_next >= ESCAPE_AFTER_RETRIES:
        options = ESCAPE_OPTIONS.get(state_id)
        if options:
            decision.options = options
            if not decision.supportive_line:
                decision.supportive_line = ESCAPE_HINTS.get(state_id)
    return False


def decide_next_action(
    current_state: str,
    slots: BankSlots,
    signals: List[str],
    strikes: BankStrikes,
    is_first_turn: bool,
    already_greeted: bool,
    retry_count: int,
    suppress_strike_increment: bool = False,
) -> Tuple[BankDecision, BankStrikes, int]:
    next_state = farthest_state(slots)
    is_retry = next_state == current_state
    retry_next = retry_count + 1 if is_retry else 0
    retry_index = min(retry_next, 2) if is_retry else 0
    required_question = _question_for_state(current_state if is_retry else next_state, retry_index)

    updated_strikes = BankStrikes(**strikes.model_dump())

    decision = BankDecision(
        next_state=next_state,
        next_action=ACTION_ASK_REQUIRED,
        required_question=required_question,
    )
    if next_state == STATE_INELIGIBLE_FINANCIAL:
        decision.next_action = ACTION_OFFER_RESTART
        decision.options = INELIGIBLE_OPTIONS

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

    if "THREAT" in signals:
        new_count = updated_strikes.threat_strikes + (0 if suppress_strike_increment else 1)
        updated_strikes.threat_strikes = new_count
        decision.next_action = ACTION_END_CONVERSATION_SAFELY
        decision.next_state = STATE_TERMINATE
        decision.termination_text = END_CONVERSATION_SAFE
        return decision, updated_strikes, retry_count

    if "RUDE" in signals or "RUDE_LANGUAGE" in signals:
        new_count = updated_strikes.rude_strikes + (0 if suppress_strike_increment else 1)
        updated_strikes.rude_strikes = new_count
        if new_count >= 3:
            decision.next_action = ACTION_END_CONVERSATION_SAFELY
            decision.next_state = STATE_TERMINATE
            decision.termination_text = END_CONVERSATION_SAFE
            return decision, updated_strikes, retry_count
        if new_count == 2:
            decision.next_action = ACTION_BOUNDARY_AND_OFFER_RESTART
            decision.warning_text = BOUNDARY_RESTART_TEXT
            decision.required_question = RESTART_OFFER_TEXT
            decision.options = RESTART_OPTIONS
            return decision, updated_strikes, retry_count
        decision.next_action = ACTION_WARN_AND_REDIRECT
        decision.warning_text = WARN_RUDE_TEXT
        decision.required_question = f"{WARN_REDIRECT_PREFIX} {required_question}"
        return decision, updated_strikes, retry_count

    if "REFUSES_TO_REPAY" in signals:
        new_count = updated_strikes.repay_strikes + (0 if suppress_strike_increment else 1)
        updated_strikes.repay_strikes = new_count
        if new_count >= 2:
            decision.next_action = ACTION_TERMINATE
            decision.next_state = STATE_TERMINATE
            decision.termination_text = REPAY_SECOND_TERMINATION
            return decision, updated_strikes, retry_count
        decision.next_action = ACTION_WARN_AND_REDIRECT
        decision.warning_text = REPAY_FIRST_EXPLANATION
        decision.coach_tip = REPAY_FIRST_EXAMPLE
        decision.required_question = REPAY_QUESTION
        return decision, updated_strikes, retry_count

    if "REFUSAL" in signals or "REFUSES_TO_PROVIDE_INFO" in signals:
        new_count = updated_strikes.refusal_strikes + (0 if suppress_strike_increment else 1)
        updated_strikes.refusal_strikes = new_count
        if new_count >= 3:
            decision.next_action = ACTION_END_CONVERSATION_SAFELY
            decision.next_state = STATE_TERMINATE
            decision.termination_text = END_CONVERSATION_SAFE
            return decision, updated_strikes, retry_count
        if new_count == 2:
            decision.next_action = ACTION_BOUNDARY_AND_OFFER_RESTART
            decision.warning_text = WARN_REFUSAL_TEXT
            decision.required_question = RESTART_OFFER_TEXT
            decision.options = RESTART_OPTIONS
            return decision, updated_strikes, retry_count
        decision.next_action = ACTION_WARN_AND_REDIRECT
        decision.warning_text = WARN_REFUSAL_TEXT
        decision.coach_tip = REFUSAL_EXAMPLES.get(next_state)
        decision.required_question = f"{WARN_REDIRECT_PREFIX} {required_question}"
        return decision, updated_strikes, retry_count

    if "CLARIFICATION_NEEDED" in signals:
        decision.next_action = ACTION_COACH_AND_ASK_REQUIRED
        decision.clarification_text = CLARIFICATION_TIPS.get(next_state)
        decision.supportive_line = SUPPORTIVE_LINES.get("coach")
        if _apply_retry_controls(decision, current_state, is_retry, retry_next):
            return decision, updated_strikes, retry_next
        return decision, updated_strikes, retry_next

    if "PURPOSE_ILLEGAL" in signals:
        decision.next_action = ACTION_COACH_AND_ASK_REQUIRED
        decision.clarification_text = PURPOSE_ILLEGAL_TEXT
        decision.supportive_line = SUPPORTIVE_LINES.get("coach")
        if _apply_retry_controls(decision, current_state, is_retry, retry_next):
            return decision, updated_strikes, retry_next
        return decision, updated_strikes, retry_next

    if "PURPOSE_UNREALISTIC" in signals:
        decision.next_action = ACTION_COACH_AND_ASK_REQUIRED
        decision.clarification_text = PURPOSE_UNREALISTIC_TEXT
        decision.supportive_line = SUPPORTIVE_LINES.get("coach")
        if _apply_retry_controls(decision, current_state, is_retry, retry_next):
            return decision, updated_strikes, retry_next
        return decision, updated_strikes, retry_next

    needs_coach, coach_tip = _needs_coach(signals)
    if needs_coach:
        decision.next_action = ACTION_COACH_AND_ASK_REQUIRED
        decision.coach_tip = coach_tip
        decision.supportive_line = SUPPORTIVE_LINES.get("coach")
        if _apply_retry_controls(decision, current_state, is_retry, retry_next):
            return decision, updated_strikes, retry_next
        return decision, updated_strikes, retry_next

    if _apply_retry_controls(decision, current_state, is_retry, retry_next):
        return decision, updated_strikes, retry_next

    return decision, updated_strikes, retry_next
