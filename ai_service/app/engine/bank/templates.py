from .constants import (
    STATE_ASK_AMOUNT,
    STATE_ASK_PURPOSE,
    STATE_CHECK_INCOME,
    STATE_SIGN_CONFIRM,
    STATE_GOODBYE,
)

OPENING_GREETING = "שלום, אני דנה מהבנק."
OPENING_QUESTION = "איך אפשר לעזור לך בתהליך בקשת הלוואה?"

ASK_AMOUNT_QUESTION = "מה סכום ההלוואה המשוער שתרצה לבקש?"
ASK_PURPOSE_QUESTION = "מה מטרת ההלוואה?"
CHECK_INCOME_QUESTION = "מה ההכנסה החודשית המשוערת שלך?"
SIGN_CONFIRM_QUESTION = "כדי להמשיך, האם אתה מאשר את הבקשה? נא ציין שם מלא ומספר תעודת זהות בלבד."
GOODBYE_TEXT = "תודה, הבקשה הושלמה. יום טוב."

REQUIRED_QUESTIONS = {
    STATE_ASK_AMOUNT: ASK_AMOUNT_QUESTION,
    STATE_ASK_PURPOSE: ASK_PURPOSE_QUESTION,
    STATE_CHECK_INCOME: CHECK_INCOME_QUESTION,
    STATE_SIGN_CONFIRM: SIGN_CONFIRM_QUESTION,
    STATE_GOODBYE: GOODBYE_TEXT,
}

RUDE_FIRST_WARNING = "אני כאן לעזור, אבל חשוב לשמור על שפה מכבדת."
RUDE_SECOND_TERMINATION = "אסיים כאן כי השפה אינה מכבדת. אפשר לחזור כשאפשר לשמור על שיח מכבד."

REFUSAL_FIRST_EXPLANATION = "כדי לטפל בבקשה אני חייבת לקבל את המידע שביקשתי."
REFUSAL_SECOND_TERMINATION = "בלי המידע המבוקש לא ניתן להמשיך בתהליך, לכן נסיים כאן. תודה."

REFUSAL_EXAMPLES = {
    STATE_ASK_AMOUNT: "דוגמה: \"אני צריך סכום של 20,000 ש\"ח\".",
    STATE_ASK_PURPOSE: "דוגמה: \"אני צריך הלוואה לרכב\".",
    STATE_CHECK_INCOME: "דוגמה: \"ההכנסה שלי 10,000 ש\"ח בחודש\".",
    STATE_SIGN_CONFIRM: "דוגמה: \"אני מאשר, שמי דנה לוי ות.ז 123456789\".",
}

REPAY_FIRST_EXPLANATION = "הלוואה מחייבת כוונה להחזיר את הכסף."
REPAY_FIRST_EXAMPLE = "דוגמה: \"כן, אני מתכוון להחזיר בזמן\"."
REPAY_QUESTION = "האם אתה מתכוון להחזיר את ההלוואה?"
REPAY_SECOND_TERMINATION = "בלי כוונה להחזיר לא ניתן להמשיך בתהליך. נסיים כאן, תודה."

COACH_TIPS = {
    "missing_greeting": "טיפ: פתח/י בברכה קצרה לפני הבקשה.",
    "commanding_tone": "טיפ: בקשה מנומסת עוזרת לשיחה מקצועית.",
    "low_relevance": "טיפ: התרכז/י במידע שהתבקש כדי להתקדם.",
}

CLARIFICATION_TIPS = {
    STATE_ASK_AMOUNT: "הסבר קצר: סכום משוער של ההלוואה, למשל 20,000.",
    STATE_ASK_PURPOSE: "הסבר קצר: מה המטרה, למשל רכב או שיפוץ.",
    STATE_CHECK_INCOME: "הסבר קצר: כמה אתה מכניס בחודש בערך, למשל 10,000.",
    STATE_SIGN_CONFIRM: "הסבר קצר: אני צריכה אישור + שם מלא ומספר תעודת זהות בלבד.",
}
