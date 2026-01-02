import sys
from transformers import pipeline

print("--- 1. LOADING HeBERT MODEL ---")
model_name = "avichr/heBERT_sentiment_analysis"
sentiment_pipeline = pipeline("sentiment-analysis", model=model_name, tokenizer=model_name, return_all_scores=True)

print("--- 2. RUNNING 100-SENTENCE STRESS TEST ---")
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
print(f"\n{'SENTENCE':<40} | {'EXPECTED':<10} | {'ACTUAL':<10} | {'SCORE':<5} | {'STATUS'}")
print("-" * 105)

correct = 0
failed_categories = {"neutral": 0, "positive": 0, "negative": 0}

for case in test_cases:
    results = sentiment_pipeline(case["text"])[0]
    top = max(results, key=lambda x: x['score'])

    # נרמול תוויות
    raw_label = top['label']
    label = raw_label.lower()

    if 'pos' in label: label = 'positive'
    elif 'neg' in label: label = 'negative'
    else: label = 'neutral'

    is_correct = label == case['expected']
    if is_correct:
        correct += 1
    else:
        failed_categories[case['expected']] += 1

    status = "✅" if is_correct else "❌"

    # הדפסה רק של שגיאות כדי לא להציף את המסך? לא, המשתמש ביקש לבדוק כל משפט. נדפיס הכל.
    # אם נכשל - נוסיף את מה שהמודל חשב בסוגריים
    debug_info = "" if is_correct else f" (Got: {label})"
    print(f"{case['text']:<40} | {case['expected']:<10} | {label:<10} | {top['score']:.2f}  | {status}{debug_info}")

print("-" * 105)
accuracy = (correct/len(test_cases))*100
print(f"FINAL ACCURACY: {accuracy:.1f}%")
print("FAILURES BY TYPE:")
print(f"  Neutral Missed: {failed_categories['neutral']}")
print(f"  Positive Missed: {failed_categories['positive']}")
print(f"  Negative Missed: {failed_categories['negative']}")
