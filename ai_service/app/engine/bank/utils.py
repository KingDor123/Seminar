import re
from typing import Iterable, Optional

HEBREW_NUMBER_WORDS = {
    "אפס": 0,
    "אחד": 1,
    "אחת": 1,
    "שניים": 2,
    "שתיים": 2,
    "שתי": 2,
    "שני": 2,
    "שלוש": 3,
    "שלושה": 3,
    "ארבע": 4,
    "ארבעה": 4,
    "חמש": 5,
    "חמישה": 5,
    "שש": 6,
    "שישה": 6,
    "שבע": 7,
    "שבעה": 7,
    "שמונה": 8,
    "תשע": 9,
    "תשעה": 9,
    "עשר": 10,
    "עשרה": 10,
}

HEBREW_TENS = {
    "עשרים": 20,
    "שלושים": 30,
    "ארבעים": 40,
    "חמישים": 50,
    "שישים": 60,
    "שבעים": 70,
    "שמונים": 80,
    "תשעים": 90,
}

HEBREW_HUNDREDS = {
    "מאה": 100,
    "מאתיים": 200,
}

STOPWORDS_FOR_NAMES = {
    "רוצה",
    "מבקש",
    "מבקשת",
    "צריך",
    "צריכה",
    "הלוואה",
    "סכום",
    "מכניס",
    "מרוויח",
    "הכנסה",
    "בבקשה",
}


def normalize_text(text: str) -> str:
    cleaned = text.strip()
    cleaned = re.sub(r"[\t\n\r]+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned


def extract_number_from_digits(text: str) -> Optional[int]:
    match = re.search(r"(\d{1,3}(?:[\s,\.]\d{3})+|\d+)", text)
    if not match:
        return None
    raw = match.group(1)
    normalized = raw.replace(" ", "").replace(",", "").replace(".", "")
    try:
        return int(normalized)
    except ValueError:
        return None


def parse_number_words(text: str) -> Optional[int]:
    tokens = re.findall(r"[א-ת]+", text)
    if not tokens:
        return None
    total = 0
    current = 0
    for token in tokens:
        if token.startswith("ו") and token != "ו":
            token = token[1:]
        if token in HEBREW_NUMBER_WORDS:
            current += HEBREW_NUMBER_WORDS[token]
        elif token in HEBREW_TENS:
            current += HEBREW_TENS[token]
        elif token in HEBREW_HUNDREDS:
            current += HEBREW_HUNDREDS[token]
        elif token == "אלף":
            if current == 0:
                current = 1
            total += current * 1000
            current = 0
        elif token == "מיליון":
            if current == 0:
                current = 1
            total += current * 1_000_000
            current = 0
    total += current
    return total or None


def apply_unit_multiplier(value: int, text: str) -> int:
    if re.search(r"\bמיליון\b", text):
        return value * 1_000_000
    if re.search(r"\bאלף\b|\bאלפים\b|\bk\b", text, flags=re.IGNORECASE):
        return value * 1000
    return value


def extract_number(text: str) -> Optional[int]:
    digit_value = extract_number_from_digits(text)
    if digit_value is not None:
        return apply_unit_multiplier(digit_value, text)
    word_value = parse_number_words(text)
    if word_value is not None:
        return apply_unit_multiplier(word_value, text)
    return None


def contains_any(text: str, patterns: Iterable[str]) -> bool:
    return any(p in text for p in patterns)


def extract_number_near_keywords(text: str, keywords: Iterable[str]) -> Optional[int]:
    for keyword in keywords:
        pattern = rf"{re.escape(keyword)}[^\dא-ת]*(\d{{1,3}}(?:[\s,\.]\d{{3}})+|\d+)"
        match = re.search(pattern, text)
        if match:
            value = extract_number(match.group(1))
            if value is not None:
                return value
    return None


def mask_id_number(id_number: Optional[str]) -> Optional[str]:
    if not id_number:
        return None
    digits = re.sub(r"\D", "", id_number)
    if not digits:
        return None
    if len(digits) <= 3:
        return "*" * len(digits)
    return "*" * (len(digits) - 3) + digits[-3:]


def clean_name(candidate: str) -> Optional[str]:
    candidate = candidate.strip()
    if not candidate:
        return None
    tokens = candidate.split()
    filtered = [
        t
        for t in tokens
        if t not in STOPWORDS_FOR_NAMES
        and len(t) > 1
        and t not in {"ת", "תז", "ת.ז"}
    ]
    if not filtered:
        return None
    return " ".join(filtered)
