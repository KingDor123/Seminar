import logging
import os
import re
from typing import AsyncGenerator, List

from app.engine.llm import llm_client
from .constants import STATE_SIGN_CONFIRM, STATE_ASK_PURPOSE, ACTION_REPEAT_AND_EXPLAIN
from .templates import SIGN_CONFIRM_QUESTION
from .types import BankDecision

logger = logging.getLogger("BankResponder")
DEBUG_LOGS = os.getenv("BANK_DEBUG_LOGS", "false").lower() in ("1", "true", "yes")


def _build_response_lines(decision: BankDecision) -> List[str]:
    if decision.termination_text:
        return [decision.termination_text]

    lines: List[str] = []
    if decision.next_action == ACTION_REPEAT_AND_EXPLAIN:
        order = [
            decision.greeting_line,
            decision.acknowledgement_line,
            decision.warning_text,
            decision.required_question,
            decision.supportive_line,
            decision.coach_tip,
        ]
    else:
        order = [
            decision.greeting_line,
            decision.acknowledgement_line,
            decision.warning_text,
            decision.clarification_text,
            decision.coach_tip,
            decision.supportive_line,
            decision.required_question,
        ]
    for line in order:
        if line:
            lines.append(line)
    if decision.options:
        lines.extend(decision.options)
    return lines


def _fallback_text(lines: List[str]) -> str:
    return "\n".join(lines)


def _needs_sign_confirm_guardrail(decision: BankDecision) -> bool:
    return decision.next_state == STATE_SIGN_CONFIRM or decision.required_question == SIGN_CONFIRM_QUESTION

def _violates_purpose_hallucination(text: str, decision: BankDecision) -> bool:
    if "מטרת ההלוואה היא" not in text:
        return False
    if decision.acknowledgement_line:
        return False
    if decision.next_state == STATE_ASK_PURPOSE:
        return True
    return True


def _violates_sign_confirm(text: str) -> bool:
    patterns = [
        r"תעודת הזהות שלי",
        r"\bת\.?ז שלי\b",
        r"השם שלי",
        r"\bשמי\b",
        r"\bאני מאשר\b",
        r"\bאני מאשרת\b",
        r"\bאני מסכים\b",
        r"\bאני מסכימה\b",
    ]
    if any(re.search(pattern, text) for pattern in patterns):
        return True
    if re.search(r"\d(?:[\s.-]?\d){6,8}", text):
        return True
    digits_only = re.sub(r"\D", "", text)
    return 7 <= len(digits_only) <= 9


async def _generate_llm_text(messages: List[dict]) -> str:
    chunks: List[str] = []
    async for token in llm_client.generate_stream(messages):
        if token.startswith("[Error:"):
            raise RuntimeError(token)
        chunks.append(token)
    return "".join(chunks)


class BankResponder:
    @staticmethod
    async def generate(decision: BankDecision) -> AsyncGenerator[str, None]:
        lines = _build_response_lines(decision)
        response_plan = "\n".join([f"- {line}" for line in lines])

        system_prompt = (
            "את דנה, נציגת בנק מקצועית בסימולציה. "
            "עליך להחזיר תשובה בעברית בלבד ובהתאם מלא לתכנית התגובה. "
            "אל תוסיף טקסט, שאלות, או פרטים מעבר למה שמופיע בתכנית. "
            "אסור לך לאשר בשם המשתמש או לתת פרטים אישיים שלך. "
            "אם יש שורות בתכנית — החזר אותן בדיוק, אחת בשורה."
        )

        user_prompt = (
            "תכנית תגובה (השתמשי רק בשורות האלו):\n"
            f"{response_plan}"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            if DEBUG_LOGS:
                logger.info("[BANK][RESPONDER] Response plan:\n%s", response_plan)
                logger.info("[BANK][RESPONDER] System prompt:\n%s", system_prompt)
                logger.info("[BANK][RESPONDER] User prompt:\n%s", user_prompt)
            needs_guardrail = _needs_sign_confirm_guardrail(decision) or decision.next_state == STATE_ASK_PURPOSE
            if needs_guardrail:
                text = await _generate_llm_text(messages)
                if DEBUG_LOGS:
                    logger.info("[BANK][RESPONDER] Raw response:\n%s", text)
                if _needs_sign_confirm_guardrail(decision) and _violates_sign_confirm(text):
                    logger.warning("[BANK][GUARDRAIL] blocked self-identification in sign_confirm")
                    yield _fallback_text(lines)
                    return
                if _violates_purpose_hallucination(text, decision):
                    logger.warning("[BANK][GUARDRAIL] blocked hallucinated purpose")
                    yield _fallback_text(lines)
                    return
                yield text
                return
            async for token in llm_client.generate_stream(messages):
                if token.startswith("[Error:"):
                    raise RuntimeError(token)
                yield token
        except Exception as exc:
            logger.error(f"[BankResponder] LLM failure, using fallback: {exc}")
            yield _fallback_text(lines)


bank_responder = BankResponder()
