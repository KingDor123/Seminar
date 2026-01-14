import logging
from typing import AsyncGenerator, List

from app.engine.llm import llm_client
from .types import BankDecision

logger = logging.getLogger("BankResponder")


def _build_response_lines(decision: BankDecision) -> List[str]:
    if decision.termination_text:
        return [decision.termination_text]

    lines: List[str] = []
    for line in [
        decision.greeting_line,
        decision.acknowledgement_line,
        decision.warning_text,
        decision.clarification_text,
        decision.coach_tip,
        decision.required_question,
    ]:
        if line:
            lines.append(line)
    return lines


def _fallback_text(lines: List[str]) -> str:
    return "\n".join(lines)


class BankResponder:
    @staticmethod
    async def generate(decision: BankDecision) -> AsyncGenerator[str, None]:
        lines = _build_response_lines(decision)
        response_plan = "\n".join([f"- {line}" for line in lines])

        system_prompt = (
            "את דנה, נציגת בנק מקצועית בסימולציה. "
            "עליך להחזיר תשובה בעברית בלבד ובהתאם מלא לתכנית התגובה. "
            "אל תוסיף טקסט, שאלות, או פרטים מעבר למה שמופיע בתכנית. "
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
            async for token in llm_client.generate_stream(messages):
                if token.startswith("[Error:"):
                    raise RuntimeError(token)
                yield token
        except Exception as exc:
            logger.error(f"[BankResponder] LLM failure, using fallback: {exc}")
            yield _fallback_text(lines)


bank_responder = BankResponder()
