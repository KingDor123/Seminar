import os
import re
from typing import List

from .constants import (
    STATE_START,
    STATE_ASK_AMOUNT,
    STATE_ASK_PURPOSE,
    STATE_CHECK_INCOME,
    STATE_SIGN_CONFIRM,
)
from .types import BankAnalyzerResult, BankSlots, IdDetails
from .utils import (
    normalize_text,
    extract_number,
    extract_number_near_keywords,
    contains_any,
    clean_name,
)
from app.engine.llm import llm_client

RUDE_WORDS = [
    "מטומטם",
    "מטומטמת",
    "אידיוט",
    "דביל",
    "מפגר",
    "חרא",
    "זונה",
    "בן זונה",
    "סתום",
    "סתמי",
    "נוכל",
    "גנבים",
    "על הפנים",
]

REFUSAL_PATTERNS = [
    "לא רוצה לענות",
    "לא מעוניין לענות",
    "לא מוסר",
    "לא אגיד",
    "לא מתכוון להגיד",
    "לא אומר",
    "לא עניינך",
    "זה לא עניינך",
    "לא רוצה",
    "לא בא לי",
    "אחר כך",
    "לא עכשיו",
    "לא בזמן הזה",
    "סודי",
    "עזוב",
    "עזבי",
    "עזבו",
    "עזוב אותי",
    "עזבי אותי",
]

REFUSAL_REPAY_PATTERNS = [
    "לא אחזיר",
    "לא מתכוון להחזיר",
    "לא מתכוונת להחזיר",
    "לא אשלם",
    "לא אשלם חזרה",
    "אין סיכוי שאחזיר",
    "לא מחזיר",
    "לא מחזירה",
]

CLARIFICATION_PATTERNS = [
    "לא הבנתי",
    "לא הבנתי אותך",
    "תסבירי",
    "תסביר",
    "מה זאת אומרת",
    "מה זה אומר",
    "מה זה",
    "מזה",
    "לא ברור",
    "אפשר להסביר",
    "למה צריך",
]

REPEAT_PATTERNS = [
    "מה שאלת",
    "מה שאלת אותי",
    "איזו שאלה",
    "אני לא מבין מה השאלה",
    "אני לא מבינה מה השאלה",
    "תחזור על השאלה",
    "תחזרי על השאלה",
    "תזכיר לי מה שאלת",
]

SHORT_REPEAT_UTTERANCES = {
    "מה",
    "מה?",
    "הא",
    "הא?",
    "אה",
    "אה?",
}

GREETING_WORDS = [
    "שלום",
    "היי",
    "הי",
    "בוקר טוב",
    "ערב טוב",
    "צהריים טובים",
    "מה שלומך",
    "מה נשמע",
    "מה המצב",
    "מה קורה",
]

POLITE_MARKERS = ["בבקשה", "אפשר", "אם אפשר", "אשמח", "הייתי שמח", "תודה"]

COMMANDING_PATTERNS = [
    r"\bתן לי\b",
    r"\bתני לי\b",
    r"\bתביאי לי\b",
    r"\bתביא לי\b",
    r"\bתעשה\b",
    r"\bתעשי\b",
    r"\bתן עכשיו\b",
    r"\bתני עכשיו\b",
    r"\bיאללה\b",
]

INCOME_KEYWORDS = ["מכניס", "הכנסה", "מרוויח", "שכר", "בחודש", "נטו", "ברוטו"]
AMOUNT_KEYWORDS = ["הלוואה", "סכום", "צריך", "צריכה", "מבקש", "מבקשת", "רוצה", "מעוניין", "מעוניינת"]
PURPOSE_KEYWORDS = ["רכב", "שיפוץ", "לימודים", "חתונה", "דירה", "עסק", "חופשה", "משכנתא", "סלון"]
BANK_KEYWORDS = ["הלוואה", "בנק", "ריבית", "תנאים", "בקשה"]

UNREALISTIC_PURPOSE_PATTERNS = [
    "חד קרן",
    "חד-קרן",
    "unicorn",
    "דרקון",
    "מכונת זמן",
    "מכונת הזמן",
    "time machine",
]

ILLEGAL_PURPOSE_PATTERNS = [
    "סמים",
    "סחר בסמים",
    "סחר בסם",
    "נשק",
    "אקדח",
    "רובה",
    "הלבנת הון",
    "הימורים לא חוקיים",
    "הימורים לא חוקי",
    "שוחד",
]

CONFIRM_POSITIVE = ["כן", "מאשר", "מאשרת", "מסכים", "מסכימה", "מאושר", "בסדר", "מתאים"]
CONFIRM_NEGATIVE = ["לא מסכים", "לא מסכימה", "לא מאשר", "לא מאשרת"]

ID_LABELS = [
    "ת.ז",
    "תז",
    "תעודת זהות",
    "מספר זהות",
    "מספר תעודת זהות",
]

CURRENCY_MARKERS = ["₪", "שח", "ש\"ח", "ש״ח"]

NO_INCOME_PATTERNS = [
    "אין לי הכנסה",
    "אין לי",
    "בלי הכנסה",
    "לא עובד",
    "לא עובדת",
    "מובטל",
    "מובטלת",
]

THREAT_PATTERNS = [
    "אני אבוא אליכם",
    "אני אגיע אליכם",
    "אני אגיע אליך",
    "אני אבוא אליך",
    "אני אמצא אותך",
    "אני אפגע",
    "אני אפגע בך",
    "אני ארביץ",
    "אני אראה לך",
    "אני אשבור",
    "אני אדקור",
    "אני אירה",
    "אני ארצח",
    "אני אפרק",
    "אני אדפוק אותך",
]

ALLOW_LLM_FALLBACK = os.getenv("BANK_LLM_FALLBACK", "false").lower() in ("1", "true", "yes")


def _detect_rude(text: str) -> bool:
    return contains_any(text, RUDE_WORDS)


def _detect_commanding(text: str) -> bool:
    if contains_any(text, POLITE_MARKERS):
        return False
    for pattern in COMMANDING_PATTERNS:
        if re.search(pattern, text):
            return True
    return False


def _detect_refusal_to_provide(text: str) -> bool:
    return contains_any(text, REFUSAL_PATTERNS)


def _detect_refusal_to_repay(text: str) -> bool:
    return contains_any(text, REFUSAL_REPAY_PATTERNS)


def _detect_clarification(text: str) -> bool:
    return contains_any(text, CLARIFICATION_PATTERNS)


def _detect_greeting(text: str) -> bool:
    return contains_any(text, GREETING_WORDS)

def _detect_repeat_request(text: str) -> bool:
    if text.strip() in SHORT_REPEAT_UTTERANCES:
        return True
    return contains_any(text, REPEAT_PATTERNS)

def _detect_threat(text: str) -> bool:
    if contains_any(text, THREAT_PATTERNS):
        return True
    return re.search(r"\bאני א(הרוג|רצח|דקור|כה|רביץ|שבור|שרוף|פגע|ירה)\b", text) is not None

def _detect_purpose_unrealistic(text: str) -> bool:
    return contains_any(text, UNREALISTIC_PURPOSE_PATTERNS)

def _detect_purpose_illegal(text: str) -> bool:
    return contains_any(text, ILLEGAL_PURPOSE_PATTERNS)


def _extract_purpose(text: str) -> str | None:
    if re.search(r"\bשיפוצ", text) or re.search(r"\bלשפץ", text):
        return "שיפוץ"
    if re.search(r"\bמחשב\b", text):
        return "מחשב"
    if re.search(r"\bבר[\s-]?מצווה\b", text):
        return "בר מצווה"
    if re.search(r"\bבת[\s-]?מצווה\b", text):
        return "בת מצווה"
    if re.search(r"\bמינוס\b", text):
        return "סגירת מינוס"
    if re.search(r"\bחובות?\b", text):
        return "חובות"
    for keyword in PURPOSE_KEYWORDS:
        if keyword in text:
            return keyword
    match = re.search(r"(?:כדי|בשביל|עבור)\s+(.+)$", text)
    if match:
        phrase = match.group(1).strip()
        phrase = re.sub(r"[\.!?]", "", phrase)
        tokens = re.findall(r"[א-ת]+", phrase)
        if len(tokens) >= 2:
            return phrase[:40]
        return None
    match = re.search(r"(?:לקנות|לרכוש|לממן|לשלם|לסגור|לכסות)\s+(.+)$", text)
    if match:
        phrase = match.group(1).strip()
        phrase = re.sub(r"[\.!?]", "", phrase)
        tokens = re.findall(r"[א-ת]+", phrase)
        if len(tokens) >= 2:
            return phrase[:40]
        return None
    return None


def _has_negative_number(text: str) -> bool:
    return re.search(r"-\s*\d", text) is not None


def _extract_amount(text: str, current_state: str) -> int | None:
    if _has_negative_number(text):
        return None
    keyword_amount = extract_number_near_keywords(text, AMOUNT_KEYWORDS)
    if keyword_amount is not None and keyword_amount > 0:
        return keyword_amount
    if contains_any(text, AMOUNT_KEYWORDS) or contains_any(text, CURRENCY_MARKERS):
        value = extract_number(text)
        if value is not None and value > 0:
            return value
    if current_state in {STATE_ASK_AMOUNT, STATE_START, STATE_ASK_PURPOSE}:
        value = extract_number(text)
        if value is not None and value > 0:
            return value
    return None


def _extract_income(text: str, current_state: str) -> int | None:
    if _has_negative_number(text):
        return None
    if contains_any(text, NO_INCOME_PATTERNS):
        return 0
    keyword_income = extract_number_near_keywords(text, INCOME_KEYWORDS)
    if keyword_income is not None:
        return keyword_income
    if contains_any(text, INCOME_KEYWORDS):
        value = extract_number(text)
        if value is not None:
            return value
    if current_state == STATE_CHECK_INCOME:
        return extract_number(text)
    return None


def _extract_confirm(text: str, current_state: str) -> bool | None:
    if current_state != STATE_SIGN_CONFIRM:
        return None
    for phrase in CONFIRM_NEGATIVE:
        if phrase in text:
            return False
    for phrase in CONFIRM_POSITIVE:
        if phrase in text:
            return True
    return None


def _extract_id_details(text: str) -> IdDetails | None:
    id_number = None
    label_pattern = r"(?:" + "|".join(re.escape(label) for label in ID_LABELS) + r")\s*[:\-]?\s*(\d{6,9})"
    match = re.search(label_pattern, text)
    if match:
        id_number = match.group(1)
    else:
        plain_match = re.search(r"\b(\d{7,9})\b", text)
        if plain_match:
            id_number = plain_match.group(1)

    full_name = None
    name_match = re.search(r"(?:שמי|שם מלא|שם)\s+([א-ת]+(?:\s+[א-ת]+){0,2})", text)
    if name_match:
        full_name = clean_name(name_match.group(1))
    else:
        name_digits_match = re.search(r"([א-ת]+(?:\s+[א-ת]+){1,2})\s*\d{7,9}", text)
        if name_digits_match:
            full_name = clean_name(name_digits_match.group(1))

    if not full_name and not id_number:
        return None
    return IdDetails(full_name=full_name, id_number=id_number)


def _required_slots_present(current_state: str, slots: BankSlots) -> bool:
    if current_state == STATE_ASK_AMOUNT:
        return slots.amount is not None
    if current_state == STATE_ASK_PURPOSE:
        return bool(slots.purpose)
    if current_state == STATE_CHECK_INCOME:
        return slots.income is not None
    if current_state == STATE_SIGN_CONFIRM:
        return slots.confirm_accepted is not None
    return False


def analyze_turn(text: str, current_state: str) -> BankAnalyzerResult:
    normalized = normalize_text(text)
    normalized_lower = normalized.lower()

    slots = BankSlots(
        amount=_extract_amount(normalized, current_state),
        purpose=_extract_purpose(normalized),
        income=_extract_income(normalized, current_state),
        confirm_accepted=_extract_confirm(normalized, current_state),
        id_details=_extract_id_details(normalized),
    )

    signals: List[str] = []

    rude = _detect_rude(normalized)
    threat = _detect_threat(normalized)
    commanding = _detect_commanding(normalized)
    clarification_needed = _detect_clarification(normalized)
    repeat_requested = _detect_repeat_request(normalized)
    refuses_repay = _detect_refusal_to_repay(normalized)
    no_income_detected = contains_any(normalized, NO_INCOME_PATTERNS)
    purpose_unrealistic = _detect_purpose_unrealistic(normalized_lower)
    purpose_illegal = _detect_purpose_illegal(normalized_lower)

    if purpose_unrealistic or purpose_illegal:
        slots.purpose = None

    required_present = _required_slots_present(current_state, slots)
    any_slot_present = any(
        [
            slots.amount is not None,
            bool(slots.purpose),
            slots.income is not None,
            slots.confirm_accepted is not None,
            bool(slots.id_details and slots.id_details.id_number),
        ]
    )

    greeting_present = _detect_greeting(normalized)
    missing_greeting = current_state == STATE_START and not greeting_present and not repeat_requested

    refusal_to_provide = False
    if not clarification_needed and _detect_refusal_to_provide(normalized):
        refusal_to_provide = True

    relevance = "LOW"
    clarity = "AMBIGUOUS"
    if repeat_requested:
        relevance = "MED"
        clarity = "CLEAR"
    elif greeting_present and not any_slot_present and not clarification_needed:
        relevance = "MED"
        clarity = "CLEAR"
    elif clarification_needed:
        relevance = "MED"
        clarity = "AMBIGUOUS"
    elif required_present:
        relevance = "HIGH"
        clarity = "CLEAR"
    elif any_slot_present or contains_any(normalized, BANK_KEYWORDS):
        relevance = "MED"
        clarity = "AMBIGUOUS"
    if purpose_unrealistic or purpose_illegal:
        relevance = "MED"
        clarity = "CLEAR"

    appropriateness = "OK"
    if repeat_requested:
        appropriateness = "OK"
    elif rude or threat:
        appropriateness = "BAD"
    elif purpose_unrealistic or purpose_illegal:
        appropriateness = "COACH"
    elif commanding or missing_greeting or relevance == "LOW":
        appropriateness = "COACH"

    if rude:
        signals.append("RUDE")
        signals.append("RUDE_LANGUAGE")
    if threat:
        signals.append("THREAT")
    if commanding:
        signals.append("COMMANDING_TONE")
    if refusal_to_provide:
        signals.append("REFUSAL")
        signals.append("REFUSES_TO_PROVIDE_INFO")
    if refuses_repay:
        signals.append("REFUSES_TO_REPAY")
    if clarification_needed:
        signals.append("CLARIFICATION_NEEDED")
    if repeat_requested:
        signals.append("REPEAT_LAST_QUESTION")
    if missing_greeting:
        signals.append("MISSING_GREETING")
    if greeting_present:
        signals.append("GREETING")
    if purpose_unrealistic:
        signals.append("PURPOSE_UNREALISTIC")
    if purpose_illegal:
        signals.append("PURPOSE_ILLEGAL")

    if slots.amount is not None:
        signals.append("HAS_AMOUNT")
    if slots.purpose:
        signals.append("HAS_PURPOSE")
    if slots.income is not None:
        signals.append("HAS_INCOME")
        if slots.income <= 0 or no_income_detected:
            signals.append("FINANCIAL_INELIGIBLE")
    if slots.confirm_accepted is True:
        signals.append("HAS_CONFIRM")
    if slots.id_details and slots.id_details.id_number:
        signals.append("HAS_ID_DETAILS")

    if relevance == "LOW" and not repeat_requested:
        signals.append("IRRELEVANT")
    signals.append(f"RELEVANCE:{relevance}")
    signals.append(f"CLARITY:{clarity}")
    signals.append(f"APPROPRIATE_FOR_BANK:{appropriateness}")

    explanations = {
        "why_relevance": "ענה במדויק" if relevance == "HIGH" else "נדרש חידוד" if relevance == "MED" else "לא קשור לשאלה",
        "why_appropriateness": "נימוסי ומקצועי" if appropriateness == "OK" else "נדרש תיקון טון",
    }

    return BankAnalyzerResult(
        user_text=text,
        slots=slots,
        signals=signals,
        explanations=explanations,
    )


async def analyze_turn_async(text: str, current_state: str) -> BankAnalyzerResult:
    result = analyze_turn(text, current_state)
    if not ALLOW_LLM_FALLBACK:
        return result
    if "CLARITY:AMBIGUOUS" not in result.signals and "RELEVANCE:LOW" not in result.signals:
        return result

    system_prompt = (
        "את/ה מעריך רלוונטיות, בהירות והתאמה לשיחה בבנק. "
        "החזר JSON בלבד. אל תקבע מצב או פעולה."
    )
    user_prompt = (
        f"משפט משתמש: \"{text}\"\n"
        f"מצב נוכחי: {current_state}\n"
        "החזר JSON עם השדות:\n"
        "{\"relevance\":\"HIGH|MED|LOW\",\"appropriateness\":\"OK|COACH|BAD\","
        "\"clarity\":\"CLEAR|AMBIGUOUS\",\"why_relevance\":\"<=12 מילים\","
        "\"why_appropriateness\":\"<=12 מילים\"}\n"
    )

    try:
        response = await llm_client.generate_json(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            schema="{relevance,appropriateness,clarity,why_relevance,why_appropriateness}",
        )
    except Exception:
        return result

    relevance = response.get("relevance")
    appropriateness = response.get("appropriateness")
    clarity = response.get("clarity")
    if relevance not in {"HIGH", "MED", "LOW"} or clarity not in {"CLEAR", "AMBIGUOUS"}:
        return result

    filtered = [
        s
        for s in result.signals
        if not (s.startswith("RELEVANCE:") or s.startswith("CLARITY:") or s.startswith("APPROPRIATE_FOR_BANK:"))
    ]
    filtered.append(f"RELEVANCE:{relevance}")
    filtered.append(f"CLARITY:{clarity}")
    if appropriateness in {"OK", "COACH", "BAD"}:
        filtered.append(f"APPROPRIATE_FOR_BANK:{appropriateness}")
    result.signals = filtered
    if isinstance(result.explanations, dict):
        if response.get("why_relevance"):
            result.explanations["why_relevance"] = response.get("why_relevance")
        if response.get("why_appropriateness"):
            result.explanations["why_appropriateness"] = response.get("why_appropriateness")
    return result
