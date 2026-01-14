import logging
import os
import re
from typing import Any, AsyncGenerator, Dict, List, Optional

from app.engine.state_manager import state_manager
from app.engine.features import FeatureExtractor
from .analyzer import analyze_turn_async
from .constants import (
    STATE_START,
    STATE_TERMINATE,
    STATE_GOODBYE,
    STATE_INELIGIBLE_FINANCIAL,
    ACTION_TERMINATE,
    ACTION_ASK_REQUIRED,
    ACTION_OFFER_RESTART,
    ACTION_BOUNDARY_AND_OFFER_RESTART,
    ACTION_END_CONVERSATION_SAFELY,
    ACTION_REPEAT_AND_EXPLAIN,
)
from .fsm import decide_next_action, merge_slots
from .templates import (
    OPENING_GREETING,
    OPENING_QUESTION,
    TERMINATION_LOCK_TEXT,
    GOODBYE_RESTART_PROMPT,
    GOODBYE_TEXT,
    END_CONVERSATION_SAFE,
    REPEAT_EXAMPLES,
    RETRY_QUESTIONS,
)
from .types import BankDecision
from .utils import mask_id_number
from .responder import bank_responder

logger = logging.getLogger("BankOrchestrator")
DEBUG_LOGS = os.getenv("BANK_DEBUG_LOGS", "false").lower() in ("1", "true", "yes")


def _is_reset_command(text: str) -> bool:
    normalized = text.strip().lower()
    if normalized == "[start]":
        return True
    reset_phrases = (
        "התחל מחדש",
        "התחלה מחדש",
        "להתחיל מחדש",
        "שיחה חדשה",
        "reset",
        "new session",
    )
    return any(phrase in normalized for phrase in reset_phrases)

def _parse_choice_index(text: str) -> int | None:
    match = re.search(r"\b([12])\b", text)
    if match:
        return int(match.group(1))
    return None


def _is_yes(text: str) -> bool:
    normalized = text.strip().lower()
    return normalized in {"כן", "כן תודה", "בטח", "ברור", "כן בבקשה"}


def _is_no(text: str) -> bool:
    normalized = text.strip().lower()
    return normalized in {"לא", "לא תודה", "עזוב", "עזבי", "לא רוצה"}


def _is_exit_command(text: str) -> bool:
    normalized = text.strip().lower()
    exit_phrases = ("לצאת", "יציאה", "לסיים", "סיים", "סיימי", "סיום")
    return _is_no(text) or any(phrase in normalized for phrase in exit_phrases)


def _is_continue_command(text: str) -> bool:
    normalized = text.strip().lower()
    return any(phrase in normalized for phrase in ("נמשיך", "בוא נמשיך", "להמשיך", "נמשיך בבקשת הלוואה"))


def _should_store_last_question(state_id: str) -> bool:
    return state_id in {"ask_amount", "ask_purpose", "check_income", "sign_confirm"}


def _fallback_question_for_state(state_id: str) -> str | None:
    if state_id in RETRY_QUESTIONS:
        return RETRY_QUESTIONS[state_id][0]
    if state_id == STATE_START:
        return OPENING_QUESTION
    return None

def _masked_slots(slots_dict: Dict[str, Any]) -> Dict[str, Any]:
    masked = dict(slots_dict)
    id_details = masked.get("id_details")
    if id_details:
        masked_details = dict(id_details)
        masked_details["id_number"] = mask_id_number(id_details.get("id_number"))
        masked["id_details"] = masked_details
    return masked


class BankOrchestrator:
    async def process_turn(
        self,
        session_id: str,
        scenario_id: str,
        user_text: str,
        history: List[Dict[str, str]],
        audio_meta: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[Any, None]:
        del history
        features = FeatureExtractor.extract(user_text, audio_meta or {})

        reset_requested = _is_reset_command(user_text)
        loaded_from_disk = state_manager.was_loaded_from_disk(session_id)

        if reset_requested:
            bank_state = state_manager.reset_bank_state(session_id, scenario_id, reason="start")
            bank_state.greeted = True
            bank_state.last_question = OPENING_QUESTION
            state_manager.update_bank_state(session_id, scenario_id, bank_state)
            if DEBUG_LOGS:
                logger.info(
                    "[BANK][DEBUG] session=%s loaded_from_disk=%s reset=%s state=%s next_state=%s slots=amount:%s purpose:%s income:%s confirm_present:%s id_present:%s",
                    session_id,
                    loaded_from_disk,
                    True,
                    bank_state.current_state_id,
                    bank_state.current_state_id,
                    bank_state.slots.amount,
                    bank_state.slots.purpose,
                    bank_state.slots.income,
                    bank_state.slots.confirm_accepted is not None,
                    bool(bank_state.slots.id_details and bank_state.slots.id_details.id_number),
                )
            yield OPENING_GREETING + " " + OPENING_QUESTION
            return

        bank_state = state_manager.get_or_create_bank_state(session_id, scenario_id)
        current_state = bank_state.current_state_id or STATE_START

        if current_state == STATE_TERMINATE:
            decision = BankDecision(
                next_state=STATE_TERMINATE,
                next_action=ACTION_TERMINATE,
                termination_text=TERMINATION_LOCK_TEXT,
            )
            yield {
                "type": "analysis",
                "passed": False,
                "reasoning": "Session already terminated",
                "sentiment": "neutral",
                "next_state": STATE_TERMINATE,
                "signals": [],
                "skip_persist": True,
            }
            if DEBUG_LOGS:
                logger.info(
                    "[BANK][DEBUG] session=%s loaded_from_disk=%s reset=%s state=%s next_state=%s slots=amount:%s purpose:%s income:%s confirm_present:%s id_present:%s",
                    session_id,
                    loaded_from_disk,
                    False,
                    current_state,
                    STATE_TERMINATE,
                    bank_state.slots.amount,
                    bank_state.slots.purpose,
                    bank_state.slots.income,
                    bank_state.slots.confirm_accepted is not None,
                    bool(bank_state.slots.id_details and bank_state.slots.id_details.id_number),
                )
            async for token in bank_responder.generate(decision):
                yield token
            return

        if current_state == STATE_GOODBYE:
            if bank_state.goodbye_prompted:
                if _is_yes(user_text) or _is_reset_command(user_text):
                    bank_state = state_manager.reset_bank_state(session_id, scenario_id, reason="goodbye_restart")
                    bank_state.greeted = True
                    state_manager.update_bank_state(session_id, scenario_id, bank_state)
                    yield OPENING_GREETING + " " + OPENING_QUESTION
                    return
                bank_state.current_state_id = STATE_TERMINATE
                state_manager.update_bank_state(session_id, scenario_id, bank_state)
                decision = BankDecision(
                    next_state=STATE_TERMINATE,
                    next_action=ACTION_END_CONVERSATION_SAFELY,
                    termination_text=END_CONVERSATION_SAFE,
                )
                yield {
                    "type": "analysis",
                    "passed": False,
                    "reasoning": "Goodbye already prompted",
                    "sentiment": "neutral",
                    "next_state": STATE_TERMINATE,
                    "signals": [],
                    "skip_persist": True,
                }
                async for token in bank_responder.generate(decision):
                    yield token
                return

            bank_state.goodbye_prompted = True
            bank_state.last_user_text = user_text
            bank_state.last_state_id = current_state
            bank_state.turn_count += 1
            state_manager.update_bank_state(session_id, scenario_id, bank_state)
            decision = BankDecision(
                next_state=STATE_GOODBYE,
                next_action=ACTION_OFFER_RESTART,
                required_question=GOODBYE_RESTART_PROMPT,
            )
            yield {
                "type": "analysis",
                "passed": False,
                "reasoning": "Post-goodbye prompt",
                "sentiment": "neutral",
                "next_state": STATE_GOODBYE,
                "signals": [],
                "skip_persist": True,
            }
            async for token in bank_responder.generate(decision):
                yield token
            return

        if bank_state.restart_offered:
            choice = _parse_choice_index(user_text)
            if current_state == STATE_INELIGIBLE_FINANCIAL:
                if choice == 1 or _is_yes(user_text) or _is_reset_command(user_text):
                    bank_state = state_manager.reset_bank_state(session_id, scenario_id, reason="ineligible_restart")
                    bank_state.greeted = True
                    state_manager.update_bank_state(session_id, scenario_id, bank_state)
                    yield OPENING_GREETING + " " + OPENING_QUESTION
                    return
                if choice == 2 or _is_exit_command(user_text):
                    bank_state.current_state_id = STATE_GOODBYE
                    bank_state.restart_offered = False
                    state_manager.update_bank_state(session_id, scenario_id, bank_state)
                    decision = BankDecision(
                        next_state=STATE_GOODBYE,
                        next_action=ACTION_ASK_REQUIRED,
                        required_question=GOODBYE_TEXT,
                    )
                    yield {
                        "type": "analysis",
                        "passed": True,
                        "reasoning": "Exit after ineligible",
                        "sentiment": "neutral",
                        "next_state": STATE_GOODBYE,
                        "signals": [],
                        "skip_persist": False,
                    }
                    async for token in bank_responder.generate(decision):
                        yield token
                    return
            else:
                if choice == 2 or _is_reset_command(user_text):
                    bank_state = state_manager.reset_bank_state(session_id, scenario_id, reason="restart_offer")
                    bank_state.greeted = True
                    state_manager.update_bank_state(session_id, scenario_id, bank_state)
                    yield OPENING_GREETING + " " + OPENING_QUESTION
                    return
                if choice == 1 or _is_continue_command(user_text) or _is_yes(user_text):
                    bank_state.restart_offered = False
                    state_manager.update_bank_state(session_id, scenario_id, bank_state)
                elif _is_exit_command(user_text):
                    bank_state.current_state_id = STATE_TERMINATE
                    state_manager.update_bank_state(session_id, scenario_id, bank_state)
                    decision = BankDecision(
                        next_state=STATE_TERMINATE,
                        next_action=ACTION_END_CONVERSATION_SAFELY,
                        termination_text=END_CONVERSATION_SAFE,
                    )
                    yield {
                        "type": "analysis",
                        "passed": False,
                        "reasoning": "Exit after restart offer",
                        "sentiment": "neutral",
                        "next_state": STATE_TERMINATE,
                        "signals": [],
                        "skip_persist": True,
                    }
                    async for token in bank_responder.generate(decision):
                        yield token
                    return
                else:
                    bank_state.restart_offered = False
                    state_manager.update_bank_state(session_id, scenario_id, bank_state)

        is_duplicate = (
            bank_state.last_user_text is not None
            and bank_state.last_state_id == current_state
            and bank_state.last_user_text == user_text
        )

        analysis = await analyze_turn_async(user_text, current_state)
        merged_slots = merge_slots(bank_state.slots, analysis.slots)

        if "REPEAT_LAST_QUESTION" in analysis.signals:
            last_question = bank_state.last_question or _fallback_question_for_state(current_state)
            example = REPEAT_EXAMPLES.get(current_state)
            decision = BankDecision(
                next_state=current_state,
                next_action=ACTION_REPEAT_AND_EXPLAIN,
                required_question=last_question,
                coach_tip=example,
            )
            bank_state.turn_count += 1
            bank_state.last_user_text = user_text
            bank_state.last_state_id = current_state
            state_manager.update_bank_state(session_id, scenario_id, bank_state)
            yield {
                "type": "analysis",
                "passed": False,
                "reasoning": "Repeat last question",
                "sentiment": "neutral",
                "next_state": current_state,
                "signals": analysis.signals,
                "skip_persist": True,
            }
            async for token in bank_responder.generate(decision):
                yield token
            return

        retry_count = bank_state.retry_counts.get(current_state, 0)
        decision, updated_strikes, next_retry = decide_next_action(
            current_state=current_state,
            slots=merged_slots,
            signals=analysis.signals,
            strikes=bank_state.strikes,
            is_first_turn=bank_state.turn_count == 0,
            already_greeted=bank_state.greeted,
            retry_count=retry_count,
            suppress_strike_increment=is_duplicate,
        )

        if current_state == STATE_INELIGIBLE_FINANCIAL and bank_state.ineligible_prompted:
            if decision.next_state == STATE_INELIGIBLE_FINANCIAL:
                decision.next_state = STATE_GOODBYE
                decision.required_question = GOODBYE_TEXT
                decision.options = None

        bank_state.slots = merged_slots
        bank_state.strikes = updated_strikes
        bank_state.current_state_id = decision.next_state
        bank_state.turn_count += 1
        if decision.greeting_line:
            bank_state.greeted = True
        bank_state.last_user_text = user_text
        bank_state.last_state_id = current_state
        bank_state.restart_offered = decision.next_action in {
            ACTION_BOUNDARY_AND_OFFER_RESTART,
            ACTION_OFFER_RESTART,
        } or decision.next_state == STATE_INELIGIBLE_FINANCIAL
        bank_state.ineligible_prompted = decision.next_state == STATE_INELIGIBLE_FINANCIAL
        if decision.next_state != current_state:
            bank_state.retry_counts[current_state] = 0
        else:
            bank_state.retry_counts[current_state] = next_retry

        if decision.required_question and _should_store_last_question(
            current_state if decision.next_state == current_state else decision.next_state
        ):
            bank_state.last_question = decision.required_question

        state_manager.update_bank_state(session_id, scenario_id, bank_state)

        logger.info(
            "[BANK] state=%s signals=%s slots=%s strikes=%s next_state=%s action=%s question=%s words=%s",
            current_state,
            analysis.signals,
            _masked_slots(merged_slots.model_dump()),
            updated_strikes.model_dump(),
            decision.next_state,
            decision.next_action,
            decision.required_question,
            features.word_count,
        )
        if DEBUG_LOGS:
            logger.info(
                "[BANK][DEBUG] session=%s loaded_from_disk=%s reset=%s state=%s next_state=%s slots=amount:%s purpose:%s income:%s confirm_present:%s id_present:%s",
                session_id,
                loaded_from_disk,
                False,
                current_state,
                decision.next_state,
                bank_state.slots.amount,
                bank_state.slots.purpose,
                bank_state.slots.income,
                bank_state.slots.confirm_accepted is not None,
                bool(bank_state.slots.id_details and bank_state.slots.id_details.id_number),
            )

        skip_persist = decision.next_state == current_state
        yield {
            "type": "analysis",
            "passed": decision.next_state != current_state,
            "reasoning": analysis.explanations.get("why_relevance", ""),
            "sentiment": "neutral",
            "next_state": decision.next_state,
            "signals": analysis.signals,
            "skip_persist": skip_persist,
        }

        if decision.next_state != current_state:
            yield {
                "type": "transition",
                "from": current_state,
                "to": decision.next_state,
            }

        async for token in bank_responder.generate(decision):
            yield token


bank_orchestrator = BankOrchestrator()
