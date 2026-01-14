import json

import pytest

from app.engine.bank.analyzer import analyze_turn
from app.engine.bank.constants import (
    STATE_START,
    STATE_ASK_AMOUNT,
    STATE_ASK_PURPOSE,
    STATE_CHECK_INCOME,
    STATE_SIGN_CONFIRM,
    STATE_GOODBYE,
    STATE_TERMINATE,
)
from app.engine.bank.fsm import merge_slots, decide_next_action
from app.engine.bank.types import BankSessionState, BankStrikes

SPEC_JSON = r'''
{
  "meta": {
    "scenario": "bank",
    "currency": "ILS",
      "notes": [
      "States: start -> ask_amount -> ask_purpose -> check_income -> ineligible_financially -> sign_confirm -> goodbye -> terminate",
      "Slots: amount, purpose, income, confirm_accepted, id_details",
      "Strikes: rude_strikes, refusal_strikes, repay_strikes"
    ]
  },
  "global_assertions": [
    {
      "id": "GA1",
      "description": "confirm_accepted must be null/None until sign_confirm with explicit accept/decline",
      "rule": "if state_after != 'sign_confirm' then slots.confirm_accepted must be null"
    },
    {
      "id": "GA2",
      "description": "After terminate, strikes must not increase and state must remain terminate",
      "rule": "if state_before == 'terminate' then state_after == 'terminate' and strikes unchanged"
    }
  ],
  "tests": [
    {
      "id": "T01_gold_full_flow_digits",
      "description": "שיחה רגילה שעוברת את כל השלבים (ספרות) + ת\"ז",
      "steps": [
        { "user": "[START]", "expect": { "state_after": "start" } },
        { "user": "שלום דנה, אני צריך הלוואה", "expect": { "state_after": "ask_amount" } },
        { "user": "20000", "expect": { "state_after": "ask_purpose", "slots": { "amount": 20000 }, "strikes": { "refusal_strikes": 0 } } },
        { "user": "לקנות רכב", "expect": { "state_after": "check_income", "slots": { "purpose": "רכב" }, "strikes": { "refusal_strikes": 0 } } },
        { "user": "15000", "expect": { "state_after": "sign_confirm", "slots": { "income": 15000 }, "strikes": { "refusal_strikes": 0 } } },
        { "user": "כן מאשר, ת\"ז 123456789", "expect": { "state_after": "goodbye", "slots": { "confirm_accepted": true, "id_details": "123456789" } } }
      ]
    },

    {
      "id": "T02_slot_skip_all_in_one",
      "description": "SLOT-SKIP: המשתמש נותן סכום+מטרה+הכנסה בהודעה אחת",
      "steps": [
        { "user": "[START]", "expect": { "state_after": "start" } },
        {
          "user": "היי דנה אני רוצה הלוואה 10000 לרכב וההכנסה שלי 15000 בחודש",
          "expect": {
            "state_after": "sign_confirm",
            "slots": { "amount": 10000, "purpose": "רכב", "income": 15000 },
            "strikes": { "refusal_strikes": 0 }
          }
        }
      ]
    },

    {
      "id": "T03_slot_skip_amount_purpose",
      "description": "נותן סכום+מטרה, צריך לקפוץ ל-check_income",
      "steps": [
        { "user": "[START]", "expect": { "state_after": "start" } },
        {
          "user": "אני צריך 10000 שקל לסלון חדש",
          "expect": { "state_after": "check_income", "slots": { "amount": 10000, "purpose": "סלון" }, "strikes": { "refusal_strikes": 0 } }
        }
      ]
    },

    {
      "id": "T04_hebrew_amount_words",
      "description": "סכום במילים: 'עשרים אלף'",
      "steps": [
        { "user": "[START]", "expect": { "state_after": "start" } },
        { "user": "שלום, אני צריך הלוואה", "expect": { "state_after": "ask_amount" } },
        { "user": "עשרים אלף", "expect": { "state_after": "ask_purpose", "slots": { "amount": 20000 }, "strikes": { "refusal_strikes": 0 } } }
      ]
    },

    {
      "id": "T05_currency_symbols",
      "description": "סכום עם ₪ ו'שח'",
      "steps": [
        { "user": "[START]", "expect": { "state_after": "start" } },
        { "user": "הלוואה בבקשה", "expect": { "state_after": "ask_amount" } },
        { "user": "10,000₪", "expect": { "state_after": "ask_purpose", "slots": { "amount": 10000 }, "strikes": { "refusal_strikes": 0 } } },
        { "user": "8000 שח לסלון", "expect": { "state_after": "check_income", "slots": { "amount": 8000, "purpose": "סלון" }, "strikes": { "refusal_strikes": 0 } } }
      ]
    },

    {
      "id": "T06_commanding_tone_coach_not_refusal",
      "description": "טון פקוד: 'תביאי לי' => COACH אבל לא refusal",
      "steps": [
        { "user": "[START]", "expect": { "state_after": "start" } },
        { "user": "תביאי לי הלוואה", "expect": { "state_after": "ask_amount" } },
        { "user": "תביאי לי 20000 עכשיו", "expect": { "state_after": "ask_purpose", "slots": { "amount": 20000 }, "strikes": { "refusal_strikes": 0 } } }
      ]
    },

    {
      "id": "T07_refusal_twice_terminates",
      "description": "מסרב פעמיים לתת סכום => terminate",
      "steps": [
        { "user": "[START]", "expect": { "state_after": "start" } },
        { "user": "אני צריך הלוואה", "expect": { "state_after": "ask_amount" } },
        { "user": "לא אומר לך כמה", "expect": { "state_after": "ask_amount", "strikes": { "refusal_strikes": 1 } } },
        { "user": "עזבי אותי", "expect": { "state_after": "terminate", "strikes": { "refusal_strikes": 2 } } }
      ]
    },

    {
      "id": "T08_clarification_is_not_refusal_ask_amount",
      "description": "שאלה 'למה צריך?' בזמן ask_amount אינה refusal",
      "steps": [
        { "user": "[START]", "expect": { "state_after": "start" } },
        { "user": "אני צריך הלוואה", "expect": { "state_after": "ask_amount" } },
        { "user": "למה צריך סכום?", "expect": { "state_after": "ask_amount", "strikes": { "refusal_strikes": 0 } } },
        { "user": "10000", "expect": { "state_after": "ask_purpose", "slots": { "amount": 10000 }, "strikes": { "refusal_strikes": 0 } } }
      ]
    },

    {
      "id": "T09_purpose_typo_should_not_be_refusal",
      "description": "טעות כתיב במטרה (רעב במקום רכב) => still purpose set or ask clarify, not terminate",
      "steps": [
        { "user": "[START]", "expect": { "state_after": "start" } },
        { "user": "הלוואה", "expect": { "state_after": "ask_amount" } },
        { "user": "10000", "expect": { "state_after": "ask_purpose", "slots": { "amount": 10000 } } },
        { "user": "לקנות רעב", "expect": { "state_after": "ask_purpose", "strikes": { "refusal_strikes": 0 } } },
        { "user": "לקנות רכב", "expect": { "state_after": "check_income", "slots": { "purpose": "רכב" }, "strikes": { "refusal_strikes": 0 } } }
      ]
    },

    {
      "id": "T10_purpose_given_should_not_increment_refusal",
      "description": "מטרה ניתנה בצורה תקינה => refusal_strikes נשאר 0",
      "steps": [
        { "user": "[START]", "expect": { "state_after": "start" } },
        { "user": "הלוואה", "expect": { "state_after": "ask_amount" } },
        { "user": "10000", "expect": { "state_after": "ask_purpose" } },
        { "user": "מטרת ההלוואה היא סלון חדש לבית", "expect": { "state_after": "check_income", "slots": { "purpose": "סלון" }, "strikes": { "refusal_strikes": 0 } } }
      ]
    },

    {
      "id": "T11_income_zero_financial_ineligible",
      "description": "הכנסה 0 => FINANCIAL_INELIGIBLE או terminate flow ייעודי (אם קיים)",
      "steps": [
        { "user": "[START]", "expect": { "state_after": "start" } },
        { "user": "הלוואה 10000 לסלון הכנסה 0", "expect": { "state_after": "ineligible_financially", "slots": { "income": 0 } } }
      ]
    },

    {
      "id": "T12_refuse_to_repay_twice_terminates",
      "description": "מסרב להחזיר פעמיים => terminate",
      "steps": [
        { "user": "[START]", "expect": { "state_after": "start" } },
        { "user": "הלוואה 10000 לרכב הכנסה 15000", "expect": { "state_after": "sign_confirm" } },
        { "user": "אני לא מתכוון להחזיר את הכסף", "expect": { "state_after": "sign_confirm", "strikes": { "repay_strikes": 1 } } },
        { "user": "לא מחזיר. נקודה.", "expect": { "state_after": "terminate", "strikes": { "repay_strikes": 2 } } }
      ]
    },

    {
      "id": "T13_rude_twice_terminates",
      "description": "קללה פעמיים => terminate",
      "steps": [
        { "user": "[START]", "expect": { "state_after": "start" } },
        { "user": "הלוואה", "expect": { "state_after": "ask_amount" } },
        { "user": "מה את רוצה יא מטומטמת", "expect": { "state_after": "ask_amount", "strikes": { "rude_strikes": 1 } } },
        { "user": "סתמי כבר", "expect": { "state_after": "terminate", "strikes": { "rude_strikes": 2 } } }
      ]
    },

    {
      "id": "T14_greeting_missing_coach_only",
      "description": "חסר שלום בתחילת שיחה אבל תוכן תקין => coaching, לא חסימה",
      "steps": [
        { "user": "[START]", "expect": { "state_after": "start" } },
        { "user": "10000 לרכב הכנסה 15000", "expect": { "state_after": "sign_confirm", "strikes": { "refusal_strikes": 0 } } }
      ]
    },

    {
      "id": "T15_amount_with_commas",
      "description": "סכום עם פסיקים",
      "steps": [
        { "user": "[START]", "expect": { "state_after": "start" } },
        { "user": "אני צריך הלוואה", "expect": { "state_after": "ask_amount" } },
        { "user": "25,000", "expect": { "state_after": "ask_purpose", "slots": { "amount": 25000 } } }
      ]
    },

    {
      "id": "T16_income_with_text",
      "description": "הכנסה עם טקסט",
      "steps": [
        { "user": "[START]", "expect": { "state_after": "start" } },
        { "user": "10000 לרכב", "expect": { "state_after": "check_income" } },
        { "user": "בערך 15000 בחודש", "expect": { "state_after": "sign_confirm", "slots": { "income": 15000 } } }
      ]
    },

    {
      "id": "T17_decline_in_sign_confirm",
      "description": "דחייה מפורשת בשלב האישור",
      "steps": [
        { "user": "[START]", "expect": { "state_after": "start" } },
        { "user": "10000 לרכב הכנסה 15000", "expect": { "state_after": "sign_confirm" } },
        { "user": "לא מאשר", "expect": { "state_after": "goodbye", "slots": { "confirm_accepted": false } } }
      ]
    },

    {
      "id": "T18_sign_confirm_clarification_not_refusal",
      "description": "בשביל הבאג שלך: 'מזה?' ב-sign_confirm לא מעלה refusal ולא terminate",
      "steps": [
        { "user": "[START]", "expect": { "state_after": "start" } },
        { "user": "10000 לרכב הכנסה 15000", "expect": { "state_after": "sign_confirm" } },
        { "user": "מזה? למה צריך ת\"ז?", "expect": { "state_after": "sign_confirm", "strikes": { "refusal_strikes": 0 } } }
      ]
    },

    {
      "id": "T19_refusal_in_sign_confirm_twice_terminates",
      "description": "מסרב לתת אישור/פרטים פעמיים בשלב האישור => terminate",
      "steps": [
        { "user": "[START]", "expect": { "state_after": "start" } },
        { "user": "10000 לרכב הכנסה 15000", "expect": { "state_after": "sign_confirm" } },
        { "user": "לא עכשיו", "expect": { "state_after": "sign_confirm", "strikes": { "refusal_strikes": 1 } } },
        { "user": "עזבי", "expect": { "state_after": "terminate", "strikes": { "refusal_strikes": 2 } } }
      ]
    },

    {
      "id": "T20_post_terminate_lock",
      "description": "אחרי terminate: כל הודעה נשארת terminate בלי להעלות strikes",
      "steps": [
        { "user": "[START]", "expect": { "state_after": "start" } },
        { "user": "הלוואה", "expect": { "state_after": "ask_amount" } },
        { "user": "לא אומר", "expect": { "state_after": "ask_amount", "strikes": { "refusal_strikes": 1 } } },
        { "user": "עזבי", "expect": { "state_after": "terminate", "strikes": { "refusal_strikes": 2 } } },
        { "user": "טוב אז 10000", "expect": { "state_after": "terminate", "strikes": { "refusal_strikes": 2 } } }
      ]
    },

    {
      "id": "T21_duplicate_message_should_not_double_strike",
      "description": "אותה הודעה פעמיים (עקב UI retry) לא אמורה להעלות strike פעמיים אם כבר נסגרה",
      "steps": [
        { "user": "[START]", "expect": { "state_after": "start" } },
        { "user": "הלוואה", "expect": { "state_after": "ask_amount" } },
        { "user": "לא אומר", "expect": { "state_after": "ask_amount", "strikes": { "refusal_strikes": 1 } } },
        { "user": "לא אומר", "expect": { "state_after": "ask_amount", "strikes": { "refusal_strikes": 1 } } }
      ]
    },

    {
      "id": "T22_amount_then_unrelated_smalltalk_not_refusal_once",
      "description": "דיבור לא רלוונטי אחרי ask_purpose: צריך coaching ולהישאר ask_purpose (לא terminate מיד)",
      "steps": [
        { "user": "[START]", "expect": { "state_after": "start" } },
        { "user": "הלוואה", "expect": { "state_after": "ask_amount" } },
        { "user": "10000", "expect": { "state_after": "ask_purpose" } },
        { "user": "מה נשמע?", "expect": { "state_after": "ask_purpose", "strikes": { "refusal_strikes": 0 } } },
        { "user": "לרכב", "expect": { "state_after": "check_income", "strikes": { "refusal_strikes": 0 } } }
      ]
    },

    {
      "id": "T23_income_non_numeric_should_ask_again_not_strike",
      "description": "הכנסה לא מובנת => לא refusal, בקשה להבהרה",
      "steps": [
        { "user": "[START]", "expect": { "state_after": "start" } },
        { "user": "10000 לרכב", "expect": { "state_after": "check_income" } },
        { "user": "אני מרוויח בסדר", "expect": { "state_after": "check_income", "strikes": { "refusal_strikes": 0 } } },
        { "user": "15000", "expect": { "state_after": "sign_confirm", "slots": { "income": 15000 } } }
      ]
    },

    {
      "id": "T24_amount_zero_should_be_invalid_not_refusal",
      "description": "סכום 0 => בקשה לתיקון, לא refusal",
      "steps": [
        { "user": "[START]", "expect": { "state_after": "start" } },
        { "user": "הלוואה", "expect": { "state_after": "ask_amount" } },
        { "user": "0", "expect": { "state_after": "ask_amount", "strikes": { "refusal_strikes": 0 } } },
        { "user": "10000", "expect": { "state_after": "ask_purpose", "slots": { "amount": 10000 } } }
      ]
    },

    {
      "id": "T25_negative_amount_invalid",
      "description": "סכום שלילי => invalid, לא refusal",
      "steps": [
        { "user": "[START]", "expect": { "state_after": "start" } },
        { "user": "הלוואה", "expect": { "state_after": "ask_amount" } },
        { "user": "-10000", "expect": { "state_after": "ask_amount", "strikes": { "refusal_strikes": 0 } } }
      ]
    },

    {
      "id": "T26_provide_id_but_no_accept",
      "description": "נותן ת\"ז בלי לומר מאשר => לא לקבוע confirm_accepted",
      "steps": [
        { "user": "[START]", "expect": { "state_after": "start" } },
        { "user": "10000 לרכב הכנסה 15000", "expect": { "state_after": "sign_confirm" } },
        { "user": "ת\"ז 123456789", "expect": { "state_after": "sign_confirm", "slots": { "confirm_accepted": null, "id_details": "123456789" } } }
      ]
    },

    {
      "id": "T27_accept_without_id_discovery",
      "description": "DISCOVERY: אישור בלי ת\"ז. מערכת או מסיימת או מבקשת ת\"ז, אבל לא terminate",
      "steps": [
        { "user": "[START]", "expect": { "state_after": "start" } },
        { "user": "10000 לרכב הכנסה 15000", "expect": { "state_after": "sign_confirm" } },
        { "user": "כן מאשר", "expect": { "state_after_any_of": ["goodbye", "sign_confirm"], "must_not": { "state_after": "terminate" } } }
      ]
    },

    {
      "id": "T28_accept_with_id_always_ok",
      "description": "אישור עם ת\"ז אמור לעבוד תמיד",
      "steps": [
        { "user": "[START]", "expect": { "state_after": "start" } },
        { "user": "10000 לרכב הכנסה 15000", "expect": { "state_after": "sign_confirm" } },
        { "user": "כן מאשר, ת\"ז 123456789", "expect": { "state_after": "goodbye", "slots": { "confirm_accepted": true } } }
      ]
    },

    {
      "id": "T29_amount_and_income_given_in_start_should_go_ask_purpose",
      "description": "הבאג שראית בלוגים: נותן מטרה+סכום+הכנסה בהתחלה -> חייב להגיע ל-sign_confirm, לא ask_purpose",
      "steps": [
        { "user": "[START]", "expect": { "state_after": "start" } },
        {
          "user": "היי דנה אני רוצה לקנות סלון חדש לבית ב 10000 ואני עובד בביטוח לאומי ויש לי הכנסה 15000 בחודש",
          "expect": {
            "state_after": "sign_confirm",
            "slots": { "amount": 10000, "purpose": "סלון", "income": 15000 }
          }
        }
      ]
    },

    {
      "id": "T30_regression_no_false_confirm_default",
      "description": "Regression: confirm_accepted לא הופך False אוטומטית בתחילת שיחה",
      "steps": [
        { "user": "[START]", "expect": { "state_after": "start" } },
        { "user": "אני צריך הלוואה", "expect": { "state_after": "ask_amount", "slots": { "confirm_accepted": null } } }
      ]
    }
  ]
}
'''

SPEC = json.loads(SPEC_JSON)


def _slot_snapshot(state: BankSessionState):
    return {
        "amount": state.slots.amount,
        "purpose": state.slots.purpose,
        "income": state.slots.income,
        "confirm_accepted": state.slots.confirm_accepted,
        "id_details": state.slots.id_details.id_number if state.slots.id_details else None,
    }


def _simulate_turn(state: BankSessionState, user_text: str) -> BankSessionState:
    if state.current_state_id == STATE_TERMINATE:
        return state

    if user_text.strip() == "[START]":
        state.current_state_id = STATE_START
        state.greeted = True
        return state

    current_state = state.current_state_id or STATE_START
    is_duplicate = state.last_user_text == user_text and state.last_state_id == current_state

    analysis = analyze_turn(user_text, current_state)
    merged_slots = merge_slots(state.slots, analysis.slots)

    decision, updated_strikes = decide_next_action(
        current_state=current_state,
        slots=merged_slots,
        signals=analysis.signals,
        strikes=state.strikes,
        is_first_turn=state.turn_count == 0,
        already_greeted=state.greeted,
        suppress_strike_increment=is_duplicate,
    )

    state.slots = merged_slots
    state.strikes = updated_strikes
    state.current_state_id = decision.next_state
    state.turn_count += 1
    if decision.greeting_line:
        state.greeted = True
    state.last_user_text = user_text
    state.last_state_id = current_state
    return state


@pytest.mark.parametrize("case", SPEC["tests"], ids=[case["id"] for case in SPEC["tests"]])
def test_bank_spec_cases(case):
    state = BankSessionState()

    for step in case["steps"]:
        state_before = state.current_state_id
        strikes_before = BankStrikes(**state.strikes.model_dump())

        state = _simulate_turn(state, step["user"])
        expect = step.get("expect", {})

        state_after = state.current_state_id
        slots = _slot_snapshot(state)

        if "state_after" in expect:
            assert state_after == expect["state_after"]
        if "state_after_any_of" in expect:
            assert state_after in expect["state_after_any_of"]
        if "must_not" in expect:
            if "state_after" in expect["must_not"]:
                assert state_after != expect["must_not"]["state_after"]

        expected_slots = expect.get("slots", {})
        for key, value in expected_slots.items():
            assert slots.get(key) == value

        expected_strikes = expect.get("strikes", {})
        for key, value in expected_strikes.items():
            assert getattr(state.strikes, key) == value

        # GA1: Before sign_confirm, confirm_accepted must remain null.
        if state_after in {STATE_START, STATE_ASK_AMOUNT, STATE_ASK_PURPOSE, STATE_CHECK_INCOME}:
            assert state.slots.confirm_accepted is None

        # GA2: After terminate, strikes must not change.
        if state_before == STATE_TERMINATE:
            assert state_after == STATE_TERMINATE
            assert state.strikes == strikes_before
