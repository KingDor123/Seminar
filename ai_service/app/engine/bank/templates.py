from .constants import (
    STATE_ASK_AMOUNT,
    STATE_ASK_PURPOSE,
    STATE_CHECK_INCOME,
    STATE_INELIGIBLE_FINANCIAL,
    STATE_SIGN_CONFIRM,
    STATE_GOODBYE,
)

OPENING_GREETING = "שלום, אני דנה מהבנק."
GREETING_VARIANTS = [
    "שלום, אני דנה מהבנק.",
    "שלום, כאן דנה מהבנק.",
]
GREETING_REPLY = "היי, תודה ששאלת."
OPENING_QUESTION = "איך אפשר לעזור לך בתהליך בקשת הלוואה?"
MISSING_GREETING_COACH = "בדרך כלל מתחילים ב\"שלום, אני רוצה לבדוק אפשרות להלוואה\"."

ASK_AMOUNT_QUESTION = "מה סכום ההלוואה המשוער שתרצה לבקש?"
ASK_PURPOSE_QUESTION = "מה מטרת ההלוואה?"
CHECK_INCOME_QUESTION = "מה ההכנסה החודשית המשוערת שלך?"
ASK_AMOUNT_RETRY_1 = "כדי להתקדם צריך סכום משוער. למשל: \"20,000\". מה הסכום?"
ASK_AMOUNT_RETRY_2 = "אפשר לבחור: 1) 5,000 2) 10,000 3) 20,000 (אפשר גם מספר אחר). מה הסכום?"
ASK_PURPOSE_RETRY_1 = "כדי להתקדם צריך מטרה קצרה. לדוגמה: \"רכב\" או \"שיפוץ\". מה המטרה?"
ASK_PURPOSE_RETRY_2 = "אפשר לבחור: 1) רכב 2) שיפוץ 3) לימודים (אפשר גם אחר). מה המטרה?"
CHECK_INCOME_RETRY_1 = "כדי להתקדם צריך סכום חודשי. למשל: \"10,000\". מה ההכנסה?"
CHECK_INCOME_RETRY_2 = "אפשר לבחור: 1) 0 2) 5,000 3) 10,000 (אפשר גם אחר). מה ההכנסה?"
SIGN_CONFIRM_QUESTION = "כדי לתרגל, כתוב/י \"מאשר/ת\" וזהו. אם תרצה/י לתרגל, אפשר גם שם בדוי ומספר בדוי בלבד."
SIGN_CONFIRM_RETRY_1 = "דוגמה קצרה: \"מאשר/ת\". אפשר גם שם בדוי ומספר בדוי בלבד."
SIGN_CONFIRM_RETRY_2 = "אפשר לבחור: 1) מאשר/ת 2) לא מאשר/ת."
INELIGIBLE_FINANCIAL_TEXT = "לצערי בלי הכנסה חודשית אי אפשר להמשיך בבקשת הלוואה כרגע."
INELIGIBLE_OPTIONS = ["1) להתחיל מחדש", "2) לצאת"]
GOODBYE_TEXT = "תודה, הבקשה הושלמה. יום טוב."
GOODBYE_RESTART_PROMPT = "הבקשה נסגרה. רוצה להתחיל תרגול חדש? (כן/לא)"
TERMINATION_LOCK_TEXT = "השיחה הסתיימה. תודה."
PURPOSE_UNREALISTIC_TEXT = "המטרה צריכה להיות מציאותית ומותרת."
PURPOSE_ILLEGAL_TEXT = "הבנק לא יכול לסייע במטרה לא חוקית. אפשר לציין מטרה חוקית בלבד."

REQUIRED_QUESTIONS = {
    STATE_ASK_AMOUNT: ASK_AMOUNT_QUESTION,
    STATE_ASK_PURPOSE: ASK_PURPOSE_QUESTION,
    STATE_CHECK_INCOME: CHECK_INCOME_QUESTION,
    STATE_INELIGIBLE_FINANCIAL: INELIGIBLE_FINANCIAL_TEXT,
    STATE_SIGN_CONFIRM: SIGN_CONFIRM_QUESTION,
    STATE_GOODBYE: GOODBYE_TEXT,
}

RETRY_QUESTIONS = {
    STATE_ASK_AMOUNT: {
        0: ASK_AMOUNT_QUESTION,
        1: ASK_AMOUNT_RETRY_1,
        2: ASK_AMOUNT_RETRY_2,
    },
    STATE_ASK_PURPOSE: {
        0: ASK_PURPOSE_QUESTION,
        1: ASK_PURPOSE_RETRY_1,
        2: ASK_PURPOSE_RETRY_2,
    },
    STATE_CHECK_INCOME: {
        0: CHECK_INCOME_QUESTION,
        1: CHECK_INCOME_RETRY_1,
        2: CHECK_INCOME_RETRY_2,
    },
    STATE_SIGN_CONFIRM: {
        0: SIGN_CONFIRM_QUESTION,
        1: SIGN_CONFIRM_RETRY_1,
        2: SIGN_CONFIRM_RETRY_2,
    },
}

REPEAT_EXAMPLES = {
    STATE_ASK_AMOUNT: "דוגמה: 20,000",
    STATE_ASK_PURPOSE: "דוגמה: רכב",
    STATE_CHECK_INCOME: "דוגמה: 10,000",
    STATE_SIGN_CONFIRM: "דוגמה: מאשר/ת",
}

SUPPORTIVE_LINES = {
    "coach": "אני מבינה שזה חשוב לך. כדי להתקדם אני צריכה תשובה קצרה לשאלה הבאה.",
}

ESCAPE_OPTIONS = {
    STATE_ASK_AMOUNT: ["1) 10,000", "2) 20,000", "3) 50,000", "4) אחר"],
    STATE_ASK_PURPOSE: ["1) רכב", "2) שיפוץ", "3) לימודים", "4) מחשב", "5) אחר (כתיבה חופשית)"],
    STATE_CHECK_INCOME: ["1) 0", "2) 5,000", "3) 10,000", "4) 15,000", "5) אחר"],
}

ESCAPE_HINTS = {
    STATE_ASK_AMOUNT: "אפשר לבחור מהרשימה או לכתוב סכום אחר.",
    STATE_ASK_PURPOSE: "אפשר לבחור מהרשימה או לכתוב מטרה אחרת בקצרה.",
    STATE_CHECK_INCOME: "אפשר לבחור מהרשימה או לכתוב סכום אחר.",
}

WARN_RUDE_TEXT = "אני כאן כדי לעזור, אבל לא אוכל להמשיך אם יש קללות או עלבונות."
WARN_REDIRECT_PREFIX = "אם תרצה/י, נמשיך. השאלה:"
BOUNDARY_RESTART_TEXT = "כדי שנוכל להתקדם, בוא ננסה ניסוח מכבד."
END_CONVERSATION_SAFE = "אני מסיימת כאן את השיחה. אם תרצה/י לנסות שוב, אפשר לחזור כשזה זמן נוח יותר."

WARN_REFUSAL_TEXT = "כדי להתקדם אני צריכה את המידע שביקשתי."
RESTART_OFFER_TEXT = "רוצה להתחיל מחדש או לסיים את השיחה?"
RESTART_OPTIONS = ["1) נמשיך בבקשת הלוואה", "2) להתחיל מחדש"]

REFUSAL_EXAMPLES = {
    STATE_ASK_AMOUNT: "דוגמה: \"אני צריך סכום של 20,000 ש\"ח\".",
    STATE_ASK_PURPOSE: "דוגמה: \"אני צריך הלוואה לרכב\".",
    STATE_CHECK_INCOME: "דוגמה: \"ההכנסה שלי 10,000 ש\"ח בחודש\".",
    STATE_SIGN_CONFIRM: "דוגמה: \"מאשר/ת\".",
}

REPAY_FIRST_EXPLANATION = "הלוואה מחייבת כוונה להחזיר את הכסף."
REPAY_FIRST_EXAMPLE = "דוגמה: \"כן, אני מתכוון להחזיר בזמן\"."
REPAY_QUESTION = "האם אתה מתכוון להחזיר את ההלוואה?"
REPAY_SECOND_TERMINATION = "בלי כוונה להחזיר לא ניתן להמשיך בתהליך. נסיים כאן, תודה."

COACH_TIPS = {
    "missing_greeting": MISSING_GREETING_COACH,
    "commanding_tone": "אפשר לנסח בנימוס, למשל: \"אני רוצה לבדוק אפשרות להלוואה\".",
    "low_relevance": "כדי להתקדם צריך תשובה קצרה לשאלה.",
}

CLARIFICATION_TIPS = {
    STATE_ASK_AMOUNT: "הסבר קצר: סכום משוער של ההלוואה, למשל 20,000.",
    STATE_ASK_PURPOSE: "הסבר קצר: מה המטרה, למשל רכב או שיפוץ.",
    STATE_CHECK_INCOME: "הסבר קצר: כמה אתה מכניס בחודש בערך, למשל 10,000.",
    STATE_SIGN_CONFIRM: "הסבר קצר: זה תרגול, מספיק לכתוב \"מאשר/ת\".",
}
