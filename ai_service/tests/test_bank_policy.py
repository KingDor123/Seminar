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
    ASK_PURPOSE_QUESTION,
)
from app.engine.bank.types import BankSlots, BankStrikes, BankDecision
from app.engine.bank.responder import bank_responder
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
async def test_repeat_last_question_repeats_exact(monkeypatch):
    async def echo_plan(messages):
        plan = messages[1]["content"]
        for line in plan.split("\n")[1:]:
            yield line.replace("- ", "")

    monkeypatch.setattr("app.engine.bank.responder.llm_client.generate_stream", echo_plan)

    session_id = "policy-repeat"
    state_manager.clear_session(session_id)

    gen = bank_orchestrator.process_turn(session_id, "bank", "[START]", [])
    async for _ in gen:
        break
    await gen.aclose()

    await _next_analysis(session_id, "שלום")

    chunks = []
    gen = bank_orchestrator.process_turn(session_id, "bank", "טוב מה שאלת אותי?", [])
    async for item in gen:
        if isinstance(item, str):
            chunks.append(item)
    await gen.aclose()
    output = "".join(chunks)
    assert ASK_AMOUNT_QUESTION in output
    assert "דוגמה: 20,000" in output
    assert "כדי להתקדם" not in output


@pytest.mark.asyncio
async def test_responder_blocks_invented_purpose(monkeypatch):
    async def fake_stream(_messages):
        yield "מטרת ההלוואה היא רכב."

    monkeypatch.setattr("app.engine.bank.responder.llm_client.generate_stream", fake_stream)

    decision = BankDecision(
        next_state=STATE_ASK_PURPOSE,
        next_action="ASK_REQUIRED",
        required_question=ASK_PURPOSE_QUESTION,
    )

    chunks = []
    async for chunk in bank_responder.generate(decision):
        chunks.append(chunk)
    output = "".join(chunks)

    assert "מטרת ההלוואה היא" not in output
    assert ASK_PURPOSE_QUESTION in output


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
