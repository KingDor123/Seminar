import json
import time
import urllib.request
import urllib.error

try:
    import requests
except ImportError:
    requests = None

# --- הגדרות ---
# כתובת ה-LLM (הנחה שזה Ollama שרץ על המחשב המארח או בקונטיינר)
# אם זה רץ בתוך דוקר, לרוב משתמשים ב-host.docker.internal
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL_NAME = "aya:8b"

print(f"--- 1. CONNECTING TO AYA ({OLLAMA_URL}) ---")

# פונקציה ששולחת את הטקסט ל-Aya
def post_json(url, payload, timeout=60):
    if requests:
        response = requests.post(url, json=payload, timeout=timeout)
        return response.status_code, response.text

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        return e.code, body


def analyze_with_aya(text):
    prompt = f"""
    You are a strict sentiment analysis engine for Hebrew banking customer service.
    Analyze the sentiment of the text below.

    Rules:
    1. Reply with EXACTLY ONE word from this list: "positive", "negative", "neutral".
    2. "Hi", "Hello", "Bye", questions like "Where is the branch?", and factual statements are "neutral".
    3. Slang like "Chaval al hazman" or "Sof haderech" is "positive".
    4. Short answers like "Yes", "No", "Okay" are "neutral".

    Text: "{text}"

    Sentiment:
    """

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.0 
        }
    }

    try:
        start = time.time()
        status_code, body = post_json(OLLAMA_URL, payload, timeout=60)
        duration = time.time() - start

        if status_code == 200:
            result = json.loads(body).get("response", "").strip().lower()
            # ניקוי סימני פיסוק אם Aya הוסיפה בטעות
            result = result.replace(".", "").replace("\n", "")

            # בדיקת תקינות
            if "pos" in result: return "positive", duration
            if "neg" in result: return "negative", duration
            return "neutral", duration # ברירת מחדל אם היא התבלבלה
        else:
            return "error", 0
    except Exception as e:
        print(f"Connection Error: {e}")
        return "error", 0

# --- אותם 100 משפטים בדיוק ---
test_cases = [
    # === קבוצה 1: "חבל על הזמן" (בזבוז vs סלנג חיובי) ===
    {"text": "סתם חיכיתי שעות חבל על הזמן שלי איתכם", "expected": "negative"},
    {"text": "השירות שלכם איטי וחבל על הזמן שאני משקיע", "expected": "negative"},
    {"text": "אל תתקשרו אליי סתם חבל על הזמן", "expected": "negative"},
    {"text": "הנציגה מרחה אותי וזה היה חבל על הזמן", "expected": "negative"},
    {"text": "בזבוז משווע חבל על הזמן והכסף", "expected": "negative"},
    {"text": "וואו איזה שירות מהיר חבל על הזמן תודה", "expected": "positive"},
    {"text": "האפליקציה החדשה שלכם חבל על הזמן", "expected": "positive"},
    {"text": "הפקידה הייתה מקצועית חבל על הזמן", "expected": "positive"},
    {"text": "הכל עבד חלק חבל על הזמן", "expected": "positive"},
    {"text": "ממש נהניתי מהיחס חבל על הזמן", "expected": "positive"},

    # === קבוצה 2: "חולה/מת/שרוף" (בריאות/מוות vs אהבה) ===
    {"text": "אני חולה כבר שבוע ולא מצליח להגיע לסניף", "expected": "negative"}, # או ניטרלי (דיווח עובדתי על קושי)
    {"text": "הנציג אמר שהוא חולה ולא יכול לעזור לי", "expected": "negative"},
    {"text": "אני חולה מעצבים עליכם", "expected": "negative"},
    {"text": "אני חולה על השירות שלכם אין עליכם", "expected": "positive"},
    {"text": "חולה על האפליקציה הזאת", "expected": "positive"},
    {"text": "האתר שלכם מת כל הזמן ואי אפשר לגלוש", "expected": "negative"},
    {"text": "הטלפון שלי מת באמצע השיחה עם הנציג", "expected": "negative"}, # תסכול
    {"text": "אני מת על הנציגים שלכם תמיד עוזרים", "expected": "positive"},
    {"text": "מת עליכם תודה רבה", "expected": "positive"},
    {"text": "האוכל הגיע שרוף וזה מגעיל", "expected": "negative"}, # (למרות שזה לא בנק, זה הקשר)
    {"text": "אני שרוף על הבנק הזה", "expected": "positive"},

    # === קבוצה 3: "סוף/סוף הדרך" (סיום רע vs מצוין) ===
    {"text": "זה הסוף של הקשר שלי עם הבנק הזה", "expected": "negative"},
    {"text": "אני רוצה לשים סוף לסאגה הזאת", "expected": "negative"},
    {"text": "נמאס לי לחכות זה הסוף של הסבלנות שלי", "expected": "negative"},
    {"text": "הטיפול בבעיה היה סוף הדרך", "expected": "positive"},
    {"text": "איזה כיף קיבלתי מענה סוף", "expected": "positive"},
    {"text": "העיצוב החדש פשוט סוף", "expected": "positive"},
    {"text": "החבילה הגיעה מהר פשוט סוף הדרך", "expected": "positive"},

    # === קבוצה 4: "לא נורמלי/משוגע" (כעס vs התפעלות) ===
    {"text": "היחס של הפקידה היה פשוט לא נורמלי בקטע רע", "expected": "negative"},
    {"text": "העמלות שאתם לוקחים זה משהו לא נורמלי", "expected": "negative"},
    {"text": "זה לא נורמלי לחכות כל כך הרבה זמן", "expected": "negative"},
    {"text": "יש לכם נציגים משוגעים שצועקים על לקוחות", "expected": "negative"},
    {"text": "המהירות שבה טיפלתם בי היא משהו לא נורמלי", "expected": "positive"},
    {"text": "הטבות לא נורמליות תודה רבה", "expected": "positive"},
    {"text": "יש לכם שירות משוגע בקטע טוב", "expected": "positive"},

    # === קבוצה 5: "אש/פצצה" (אלימות/כעס vs סלנג) ===
    {"text": "אני רותח אש מכעס עליכם", "expected": "negative"},
    {"text": "הבית שלי עלה באש וצריך ביטוח", "expected": "negative"}, # הקשר שלילי (אסון)
    {"text": "השירות שלכם פשוט אש אהבתי", "expected": "positive"},
    {"text": "אתם עובדים אש כל הכבוד", "expected": "positive"},
    {"text": "המצב בחשבון שלי נראה אחרי הפצצה", "expected": "negative"},
    {"text": "הריבית הזאת היא פצצה מתקתקת", "expected": "negative"},
    {"text": "ההלוואה שנתתם לי היא פצצה", "expected": "positive"}, # הקשר חיובי (תנאים טובים)
    {"text": "היה פצצה של שירות", "expected": "positive"},

    # === קבוצה 6: ציניות וטונים (המבחן הקשה ביותר) ===
    {"text": "ממש תודה שעניתם לי אחרי שנה", "expected": "negative"}, # ציניות
    {"text": "יופי באמת גאונים", "expected": "negative"}, # ציניות
    {"text": "כל הכבוד שאיבדתם לי את הטופס", "expected": "negative"}, # ציניות
    {"text": "תודה רבה שעניתם לי מהר", "expected": "positive"}, # רציני
    {"text": "איזה יופי של שירות", "expected": "positive"}, # רציני
    {"text": "כל הכבוד על העזרה", "expected": "positive"}, # רציני

    # === קבוצה 7: מילות שלילה מבלבלות ("אין") ===
    {"text": "אין עם מי לדבר אצלכם", "expected": "negative"},
    {"text": "אין מענה ואין יחס", "expected": "negative"},
    {"text": "אין לי כוח אליכם יותר", "expected": "negative"},
    {"text": "אין עליכם בעולם", "expected": "positive"},
    {"text": "אין דברים כאלה איזה שירות", "expected": "positive"},
    {"text": "אין לי מילים להודות לכם", "expected": "positive"},

    # === קבוצה 8: "גדול" (בעיה גדולה vs מחמאה) ===
    {"text": "יש לי מינוס גדול מאוד", "expected": "negative"},
    {"text": "קרתה טעות גדולה בחשבון", "expected": "negative"},
    {"text": "הנזק הוא גדול ובלתי הפיך", "expected": "negative"},
    {"text": "אתה גדול תודה רבה", "expected": "positive"},
    {"text": "יצאתם גדולים עם הזיכוי", "expected": "positive"},
    {"text": "שיחקתם אותה בגדול", "expected": "positive"},

    # === קבוצה 9: "טוב" (סתמי/כעס vs חיובי) ===
    {"text": "טוב תעשה מה שאתה רוצה", "expected": "negative"}, # כניעה/עצבים
    {"text": "נו טוב מתי זה יגיע כבר", "expected": "negative"}, # חוסר סבלנות
    {"text": "זה לא טוב בכלל", "expected": "negative"},
    {"text": "בוקר טוב ומבורך", "expected": "positive"}, # ברכה (לפעמים מזוהה כניטרלי, נצפה ל-Pos/Neu)
    {"text": "הכל טוב תודה", "expected": "positive"},
    {"text": "קיבלתי שירות טוב מאוד", "expected": "positive"},

    # === קבוצה 10: הקשר בנקאי ספציפי (פעולות vs תקלות) ===
    {"text": "למה הכרטיס לא עובר לי", "expected": "negative"},
    {"text": "הכספומט בלע לי את הכרטיס", "expected": "negative"},
    {"text": "חזרו לי שלושה צ'קים היום", "expected": "negative"},
    {"text": "סגרו לי את המסגרת אשראי", "expected": "negative"},
    {"text": "ההעברה עברה בהצלחה", "expected": "positive"}, # או ניטרלי חיובי
    {"text": "הכסף נכנס לחשבון תודה", "expected": "positive"},
    {"text": "הצלחתם לסדר את הבעיה", "expected": "positive"},
    {"text": "קיבלתי את האישור המבוקש", "expected": "positive"}, # שביעות רצון

    # === השלמות ל-100 (עוד מוקשים) ===
    {"text": "למה אתם לא עונים", "expected": "negative"},
    {"text": "כמה זמן צריך לחכות", "expected": "negative"},
    {"text": "זה פשוט לא יאומן החוצפה", "expected": "negative"},
    {"text": "אני בהלם מהשירות הגרוע", "expected": "negative"},
    {"text": "אני בהלם כמה מהר זה טופל", "expected": "positive"},
    {"text": "לא יאומן איזה כיף", "expected": "positive"},
    {"text": "תשמעו אתם פשוט בדיחה", "expected": "negative"},
    {"text": "סיפרתי לחברים איזו בדיחה מצחיקה", "expected": "neutral"}, # מוקש הקשר (לא קשור לשירות)
    {"text": "חבל שלא עניתם קודם", "expected": "negative"},
    {"text": "חבל על כל דקה שעוברת", "expected": "negative"},
    {"text": "מזל שיש אתכם", "expected": "positive"},
    {"text": "איזה מזל שפניתי אליכם", "expected": "positive"},
    {"text": "ביזיון של התנהלות", "expected": "negative"},
    {"text": "שכונה מה שקורה פה", "expected": "negative"},
    {"text": "אתם עושים צחוק מעבודה", "expected": "negative"},
    {"text": "פשוט תענוג לעבוד איתכם", "expected": "positive"},
    {"text": "חוויה מתקנת", "expected": "positive"},
    {"text": "הצלתם אותי", "expected": "positive"},
    {"text": "אתם המלאכים שלי", "expected": "positive"},
    {"text": "לך לעזאזל", "expected": "negative"},
    {"text": "תבורכו משמיים", "expected": "positive"},
    {"text": "אלוהים ישמור אתכם", "expected": "positive"},
    {"text": "אלוהים ישמור איזה בלגן", "expected": "negative"}
]
# (קיצרתי את הרשימה ל-20 משפטים כדי שלא תחכה שעה, אם זה יעבוד טוב נריץ על הכל)

print(f"\n{'SENTENCE':<30} | {'EXPECTED':<10} | {'AYA SAYS':<10} | {'TIME':<6} | {'STATUS'}")
print("-" * 80)

correct = 0
total_time = 0

for case in test_cases:
    prediction, duration = analyze_with_aya(case["text"])
    total_time += duration

    is_correct = prediction == case["expected"]
    if is_correct: correct += 1

    status = "✅" if is_correct else "❌"
    print(f"{case['text']:<30} | {case['expected']:<10} | {prediction:<10} | {duration:.2f}s  | {status}")

print("-" * 80)
accuracy = (correct / len(test_cases)) * 100
avg_time = total_time / len(test_cases)

print(f"FINAL ACCURACY: {accuracy:.1f}%")
print(f"AVG TIME PER SENTENCE: {avg_time:.2f}s")
