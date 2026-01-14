import logging
from typing import Any, AsyncGenerator, Dict, List, Optional

from app.engine.state_manager import state_manager
from app.engine.features import FeatureExtractor
from .analyzer import analyze_turn_async
from .constants import STATE_START, STATE_TERMINATE, ACTION_TERMINATE
from .fsm import decide_next_action, merge_slots
from .templates import OPENING_GREETING, OPENING_QUESTION, TERMINATION_LOCK_TEXT
from .types import BankDecision
from .utils import mask_id_number
from .responder import bank_responder

logger = logging.getLogger("BankOrchestrator")


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
            async for token in bank_responder.generate(decision):
                yield token
            return

        if user_text.strip() == "[START]":
            bank_state.current_state_id = STATE_START
            bank_state.greeted = True
            state_manager.update_bank_state(session_id, scenario_id, bank_state)
            yield OPENING_GREETING + " " + OPENING_QUESTION
            return

        is_duplicate = (
            bank_state.last_user_text is not None
            and bank_state.last_state_id == current_state
            and bank_state.last_user_text == user_text
        )

        analysis = await analyze_turn_async(user_text, current_state)
        merged_slots = merge_slots(bank_state.slots, analysis.slots)

        decision, updated_strikes = decide_next_action(
            current_state=current_state,
            slots=merged_slots,
            signals=analysis.signals,
            strikes=bank_state.strikes,
            is_first_turn=bank_state.turn_count == 0,
            already_greeted=bank_state.greeted,
            suppress_strike_increment=is_duplicate,
        )

        bank_state.slots = merged_slots
        bank_state.strikes = updated_strikes
        bank_state.current_state_id = decision.next_state
        bank_state.turn_count += 1
        if decision.greeting_line:
            bank_state.greeted = True
        bank_state.last_user_text = user_text
        bank_state.last_state_id = current_state

        state_manager.update_bank_state(session_id, scenario_id, bank_state)

        logger.info(
            "[BANK] state=%s signals=%s slots=%s strikes=%s next_state=%s words=%s",
            current_state,
            analysis.signals,
            _masked_slots(merged_slots.model_dump()),
            updated_strikes.model_dump(),
            decision.next_state,
            features.word_count,
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
