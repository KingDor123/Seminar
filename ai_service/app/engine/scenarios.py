from typing import List, Optional
from app.engine.schema import ScenarioGraph, ScenarioState, EvaluationCriteria, Transition

# --- Interview Scenario Definition ---

_INTERVIEW_PERSONA = """
את שרה, מנהלת גיוס מקצועית ומנומסת בחברת הייטק.
סגנון דיבור: מקצועית, נגישה, שאלות ברורות.
"""

interview_graph = ScenarioGraph(
    id="interview",
    name="ראיון עבודה - מנהלת גיוס",
    base_persona=_INTERVIEW_PERSONA,
    goal="להוביל ראיון עבודה מקצועי: לאסוף מידע על ניסיון וחוזקות.",
    initial_state_id="start",
    states={
        "start": ScenarioState(
            id="start",
            description="פתיחת הראיון",
            actor_instruction="הציגי את עצמך כשרה. ברכי את המועמד לשלום. הזמיני אותו לשבת ושאלי אם הוא מוכן.",
            evaluation=EvaluationCriteria(
                criteria=["המשתמש עונה לברכה"],
                allowed_signals=["GREETING_RETURNED", "USER_RESPONDED"],
                pass_condition="המשתמש מאשר את הברכה בנימוס.",
                failure_feedback_guidance="המשתמש צריך פשוט לומר שלום או לאשר שהוא מוכן."
            ),
            transitions=[
                Transition(
                    target_state_id="ask_intro", 
                    condition="המשתמש ענה לברכה",
                    condition_id="GREETING_RETURNED"
                ),
                Transition(
                    target_state_id="ask_intro",
                    condition="המשתמש הגיב",
                    condition_id="USER_RESPONDED",
                    priority=10
                )
            ]
        ),
        "ask_intro": ScenarioState(
            id="ask_intro",
            description="בקשה להצגה עצמית",
            actor_instruction="שאלי: 'ספר לי קצת על עצמך.'",
            evaluation=EvaluationCriteria(
                criteria=["המשתמש מספק רקע מקצועי", "המשתמש מדבר בבירור"],
                allowed_signals=["INTRO_GIVEN"],
                pass_condition="המשתמש נותן סקירה קצרה על הרקע שלו.",
                failure_feedback_guidance="עודדי את המשתמש להתמקד בניסיון המקצועי שלו."
            ),
            transitions=[
                Transition(
                    target_state_id="ask_strength", 
                    condition="המשתמש הציג את עצמו",
                    condition_id="INTRO_GIVEN"
                )
            ]
        ),
        "ask_strength": ScenarioState(
            id="ask_strength",
            description="שאלה על חוזקות",
            actor_instruction="שאלי על חוזקה או מיומנות מקצועית עיקרית.",
            evaluation=EvaluationCriteria(
                criteria=["המשתמש מציין חוזקה", "המשתמש נותן דוגמה"],
                allowed_signals=["STRENGTH_GIVEN"],
                pass_condition="המשתמש מזהה חוזקה רלוונטית לעבודה.",
                failure_feedback_guidance="בקשי מהמשתמש לציין דבר אחד שהוא טוב בו מבחינה מקצועית."
            ),
            transitions=[
                Transition(
                    target_state_id="ask_challenge", 
                    condition="המשתמש ענה על שאלת החוזקה",
                    condition_id="STRENGTH_GIVEN"
                )
            ]
        ),
        "ask_challenge": ScenarioState(
            id="ask_challenge",
            description="שאלה על אתגר",
            actor_instruction="שאלי על אתגר מקצועי שהוא התגבר עליו.",
            evaluation=EvaluationCriteria(
                criteria=["המשתמש מתאר סיטואציה", "המשתמש מתאר פעולה שננקטה", "המשתמש מתאר תוצאה"],
                allowed_signals=["CHALLENGE_DESCRIBED"],
                pass_condition="המשתמש מספר סיפור על התגברות על קושי.",
                failure_feedback_guidance="בקשי דוגמה לזמן ספציפי שבו משהו השתבש ואיך הוא תיקן את זה."
            ),
            transitions=[
                Transition(
                    target_state_id="ask_motivation", 
                    condition="המשתמש ענה על שאלת האתגר",
                    condition_id="CHALLENGE_DESCRIBED"
                )
            ]
        ),
        "ask_motivation": ScenarioState(
            id="ask_motivation",
            description="שאלה על מוטיבציה",
            actor_instruction="שאלי מדוע הוא מעוניין במשרה/בחברה הספציפית הזו.",
            evaluation=EvaluationCriteria(
                criteria=["המשתמש מראה עניין", "המשתמש מקשר מיומנויות לתפקיד"],
                allowed_signals=["MOTIVATION_GIVEN"],
                pass_condition="המשתמש מסביר את המוטיבציה שלו.",
                failure_feedback_guidance="שאלי מה משך אותו ספציפית לתפקיד זה."
            ),
            transitions=[
                Transition(
                    target_state_id="ask_user_questions", 
                    condition="המשתמש ענה על שאלת המוטיבציה",
                    condition_id="MOTIVATION_GIVEN"
                )
            ]
        ),
        "ask_user_questions": ScenarioState(
            id="ask_user_questions",
            description="הזמנת שאלות מצד המשתמש",
            actor_instruction="שאלי אם למועמד יש שאלות עבורך.",
            evaluation=EvaluationCriteria(
                criteria=["המשתמש שואל שאלה או מסרב בנימוס"],
                allowed_signals=["QUESTIONS_DONE"],
                pass_condition="המשתמש משתתף בחלק של השאלות ותשובות.",
                failure_feedback_guidance="זה בסדר אם אין לו שאלות, אבל הוא צריך לומר זאת."
            ),
            transitions=[
                Transition(
                    target_state_id="closing", 
                    condition="המשתמש סיים לשאול שאלות",
                    condition_id="QUESTIONS_DONE"
                )
            ]
        ),
        "closing": ScenarioState(
            id="closing",
            description="סיום הראיון",
            actor_instruction="הודי למועמד על הגעתו. אמרי שתהיו בקשר בקרוב. להתראות.",
            evaluation=EvaluationCriteria(
                criteria=["המשתמש נפרד לשלום"],
                allowed_signals=["GOODBYE"],
                pass_condition="המשתמש מסיים את השיחה.",
                failure_feedback_guidance="היפרדי לשלום."
            ),
            is_terminal=True
        )
    }
)

# --- Bank Scenario Definition ---

_BANK_PERSONA = """
את דנה, נציגת בנק רגועה ומקצועית בשיחת וידאו לבקשת הלוואה.
סגנון דיבור: חמימה, פשוטה, תומכת ומעודדת. משפט קצר אחד בכל תשובה.
"""
bank_graph = ScenarioGraph(
    id="bank",
    name="בקשת הלוואה - בנק",
    base_persona=_BANK_PERSONA,
    goal="לנהל בקשת הלוואה בצורה מקצועית: איסוף נתונים פיננסיים, הסבר תנאים ושמירה על תקשורת ברורה.",
    initial_state_id="start",
    states={
        "start": ScenarioState(
            id="start",
            description="פתיחת השיחה (סימולציה בלבד)",
            actor_instruction="הצג/י את עצמך כדנה מהבנק. שאל/י כיצד ניתן לסייע היום בתהליך בקשת ההלוואה. סימולציה בלבד; אין לבקש מידע אישי או מזהה.",
            evaluation=EvaluationCriteria(
                criteria=["המשתמש מציין כוונה להגיש בקשה להלוואה"],
                allowed_signals=["INTENT_CONFIRMED", "USER_RESPONDED"],
                pass_condition="המשתמש מאשר שהוא מעוניין להגיש בקשה להלוואה.",
                failure_feedback_guidance="המשתמש צריך לציין שהוא כאן לצורך בקשת הלוואה."
            ),
            transitions=[
                Transition(
                    target_state_id="ask_amount", 
                    condition="המשתמש אישר כוונה",
                    condition_id="INTENT_CONFIRMED"
                ),
                Transition(
                    target_state_id="ask_amount",
                    condition="המשתמש הגיב",
                    condition_id="USER_RESPONDED",
                    priority=10
                )
            ]
        ),
        "ask_amount": ScenarioState(
            id="ask_amount",
            description="בקשת סכום ההלוואה",
            actor_instruction="שאל/י מהו סכום ההלוואה המשוער שבו הוא/היא מעוניין/ת. סימולציה בלבד; ללא מידע אישי או מזהה.",
            evaluation=EvaluationCriteria(
                criteria=["המשתמש מספק סכום מספרי"],
                allowed_signals=["AMOUNT_GIVEN"],
                pass_condition="המשתמש מציין סכום הלוואה ברור.",
                failure_feedback_guidance="המשתמש חייב לציין כמה כסף הוא צריך."
            ),
            transitions=[
                Transition(
                    target_state_id="ask_purpose", 
                    condition="המשתמש סיפק סכום",
                    condition_id="AMOUNT_GIVEN"
                )
            ]
        ),
        "ask_purpose": ScenarioState(
            id="ask_purpose",
            description="בקשת מטרת ההלוואה",
            actor_instruction="שאל/י בקצרה מהי מטרת ההלוואה.",
            evaluation=EvaluationCriteria(
                criteria=["המשתמש מציין מטרה תקפה (רכב, שיפוץ וכו')"],
                allowed_signals=["PURPOSE_GIVEN"],
                pass_condition="המשתמש מסביר לשם מה נדרש הכסף.",
                failure_feedback_guidance="המשתמש צריך לומר מדוע הוא זקוק לכסף."
            ),
            transitions=[
                Transition(
                    target_state_id="ask_income", 
                    condition="המשתמש סיפק מטרה",
                    condition_id="PURPOSE_GIVEN"
                )
            ]
        ),
        "ask_income": ScenarioState(
            id="ask_income",
            description="בקשת פרטי הכנסה",
            actor_instruction="שאל/י לגבי טווח הכנסה חודשית משוער והאם קיימות התחייבויות נוספות. שמור/י על משפט קצר והימנע/י מכל מזהה אישי או מסמכים. סימולציה בלבד.",
            evaluation=EvaluationCriteria(
                criteria=["המשתמש מספק פרטי הכנסה תקינים", "המשתמש אינו חסר יכולת החזר"],
                allowed_signals=["INCOME_GIVEN", "FINANCIAL_INELIGIBLE"],
                pass_condition="המשתמש מציין הכנסה משוערת שמאפשרת החזר.",
                failure_feedback_guidance="המשתמש צריך לספק מידע על הכנסה לצורך הבקשה."
            ),
            transitions=[
                Transition(
                    target_state_id="present_terms", 
                    condition="המשתמש סיפק הכנסה תקינה",
                    condition_id="INCOME_GIVEN"
                ),
                # New transition for financial ineligibility (High Priority)
                Transition(
                    target_state_id="ineligible_financially", 
                    condition="המשתמש הצהיר על אי-יכולת החזר",
                    condition_id="FINANCIAL_INELIGIBLE",
                    priority=5
                )
            ]
        ),
        "present_terms": ScenarioState(
            id="present_terms",
            description="הצגת תנאי הלוואה (סימולציה בלבד)",
            actor_instruction="ציין/י שעל סמך המידע שנמסר המשתמש זכאי להלוואה. הצג/י ריבית סטנדרטית (לדוגמה: פריים + 2%). שאל/י האם התנאים מתאימים. סימולציה בלבד.",
            evaluation=EvaluationCriteria(
                criteria=["המשתמש מאשר את התנאים או מסרב"],
                allowed_signals=["TERMS_ACCEPTED", "TERMS_REJECTED"],
                pass_condition="המשתמש מגיב לתנאים.",
                failure_feedback_guidance="המשתמש צריך לאשר אם הוא מסכים לתנאים או לא."
            ),
            transitions=[
                Transition(
                    target_state_id="closing", 
                    condition="המשתמש אישר את התנאים",
                    condition_id="TERMS_ACCEPTED",
                    priority=1
                ),
                Transition(
                    target_state_id="negotiate", 
                    condition="המשתמש דחה את התנאים",
                    condition_id="TERMS_REJECTED",
                    priority=1
                )
            ]
        ),
        "negotiate": ScenarioState(
            id="negotiate",
            description="משא ומתן על ריביות (סימולציה)",
            actor_instruction="הסבירי בנימוס שאלו הריביות הקבועות כרגע, אך ניתן לבדוק זכאות להטבה בעתיד. שאלי אם ירצה להמשיך כך.",
            evaluation=EvaluationCriteria(
                criteria=["המשתמש מחליט אם להמשיך או לוותר"],
                allowed_signals=["TERMS_ACCEPTED", "TERMS_REJECTED"],
                pass_condition="המשתמש מקבל החלטה סופית.",
                failure_feedback_guidance="המשתמש צריך להחליט אם הוא לוקח את ההלוואה."
            ),
            transitions=[
                Transition(
                    target_state_id="closing", 
                    condition="המשתמש הסכים",
                    condition_id="TERMS_ACCEPTED"
                ),
                Transition(
                    target_state_id="closing", 
                    condition="המשתמש ויתר",
                    condition_id="TERMS_REJECTED"
                )
            ]
        ),
        # New State: Financial Ineligibility
        # This state handles cases where the loan cannot be processed due to objective financial reasons
        # (e.g., no income, refusal to repay). It is distinct from behavioral failure.
        "ineligible_financially": ScenarioState(
            id="ineligible_financially",
            description="דחיית בקשה על רקע כלכלי",
            actor_instruction="הסבירי בעדינות ובכבוד שללא הכנסה או יכולת החזר, הבנק לא יוכל לאשר את ההלוואה כרגע. הציעי לבדוק שוב בעתיד כשהמצב ישתנה. היי אמפתית אך מקצועית.",
            evaluation=EvaluationCriteria(
                criteria=["המשתמש מבין את הסירוב ונפרד"],
                allowed_signals=["GOODBYE"],
                pass_condition="המשתמש מסיים את השיחה.",
                failure_feedback_guidance="היפרדי לשלום."
            ),
            transitions=[
                Transition(
                    target_state_id="closing", 
                    condition="המשתמש הבין ונפרד",
                    condition_id="GOODBYE"
                )
            ]
        ),
        "closing": ScenarioState(
            id="closing",
            description="סיום הבקשה",
            actor_instruction="אשר/י שהבקשה הוגשה (או בוטלה). הודה/י למשתמש ואחל/י יום טוב.",
            evaluation=EvaluationCriteria(
                criteria=["המשתמש נפרד"],
                allowed_signals=["GOODBYE"],
                pass_condition="המשתמש מסיים את השיחה.",
                failure_feedback_guidance="להיפרד לשלום."
            ),
            is_terminal=True
        )
    }
)


# --- Grocery Scenario Definition ---

_GROCERY_PERSONA = """
אתה מייק, עובד חנות/מכולת ידידותי ועוזר.
סגנון דיבור: קליל, אופטימי, משפטים קצרים ("במעבר 4", "יש כרטיס מועדון?").
"""

grocery_graph = ScenarioGraph(
    id="grocery",
    name="קנייה במכולת",
    base_persona=_GROCERY_PERSONA,
    goal="להשלים רכישה במכולת בצורה מנומסת וברורה.",
    initial_state_id="start",
    states={
        "start": ScenarioState(
            id="start",
            description="ברכה בקופה",
            actor_instruction="אמרי: 'היי! ברוכים הבאים לפרש-מרקט. מצאתם את כל מה שהייתם צריכים?'",
            evaluation=EvaluationCriteria(
                criteria=["המשתמש עונה לברכה"],
                allowed_signals=["GREETING_RETURNED", "USER_RESPONDED"],
                pass_condition="המשתמש מאשר שמצא פריטים או מבקש משהו.",
                failure_feedback_guidance="המשתמש צריך לענות כן או לא."
            ),
            transitions=[
                Transition(
                    target_state_id="ask_club_card", 
                    condition="המשתמש ענה",
                    condition_id="GREETING_RETURNED"
                ),
                Transition(
                    target_state_id="ask_club_card",
                    condition="המשתמש הגיב",
                    condition_id="USER_RESPONDED",
                    priority=10
                )
            ]
        ),
        "ask_club_card": ScenarioState(
            id="ask_club_card",
            description="בדיקת כרטיס מועדון",
            actor_instruction="שאלי אם יש להם כרטיס חבר מועדון.",
            evaluation=EvaluationCriteria(
                criteria=["המשתמש אומר כן/לא לגבי כרטיס מועדון"],
                allowed_signals=["HAS_CARD", "NO_CARD"],
                pass_condition="המשתמש עונה לגבי הכרטיס.",
                failure_feedback_guidance="המשתמש צריך לומר אם יש לו כרטיס או לא."
            ),
            transitions=[
                Transition(
                    target_state_id="scan_items", 
                    condition="המשתמש ענה לשאלת הכרטיס",
                    condition_id="HAS_CARD"
                ),
                Transition(
                    target_state_id="scan_items", 
                    condition="המשתמש ענה לשאלת הכרטיס",
                    condition_id="NO_CARD"
                )
            ]
        ),
        "scan_items": ScenarioState(
            id="scan_items",
            description="סריקת פריטים",
            actor_instruction="העמידי פנים שאת סורקת פריטים. אמרי משפט סמול טוק כמו 'וואו, התפוחים האלה נראים נהדר'.",
            evaluation=EvaluationCriteria(
                criteria=["המשתמש משתתף בסמול טוק או מאשר"],
                allowed_signals=["SMALL_TALK_ENGAGED"],
                pass_condition="המשתמש מגיב בנימוס.",
                failure_feedback_guidance="המשתמש צריך להתייחס להערה."
            ),
            transitions=[
                Transition(
                    target_state_id="ask_bag", 
                    condition="המשתמש הגיב",
                    condition_id="SMALL_TALK_ENGAGED"
                )
            ]
        ),
        "ask_bag": ScenarioState(
            id="ask_bag",
            description="העדפת שקית",
            actor_instruction="שאלי: 'שקית רגילה או רב-פעמית?'",
            evaluation=EvaluationCriteria(
                criteria=["המשתמש בוחר סוג שקית"],
                allowed_signals=["BAG_SELECTED"],
                pass_condition="המשתמש בוחר אפשרות שקית.",
                failure_feedback_guidance="המשתמש חייב לבחור סוג שקית."
            ),
            transitions=[
                Transition(
                    target_state_id="payment", 
                    condition="המשתמש בחר שקית",
                    condition_id="BAG_SELECTED"
                )
            ]
        ),
        "payment": ScenarioState(
            id="payment",
            description="תשלום",
            actor_instruction="צייני את הסכום הכולל (למשל, 45 שקלים). בקשי תשלום.",
            evaluation=EvaluationCriteria(
                criteria=["המשתמש מציע תשלום"],
                allowed_signals=["PAYMENT_MADE"],
                pass_condition="המשתמש משלם (מציין שהוא משלם).",
                failure_feedback_guidance="המשתמש צריך לשלם."
            ),
            transitions=[
                Transition(
                    target_state_id="closing", 
                    condition="המשתמש שילם",
                    condition_id="PAYMENT_MADE"
                )
            ]
        ),
        "closing": ScenarioState(
            id="closing",
            description="פרידה",
            actor_instruction="הודי להם ואחלי להם יום נהדר.",
            evaluation=EvaluationCriteria(
                criteria=["המשתמש נפרד לשלום"],
                allowed_signals=["GOODBYE"],
                pass_condition="המשתמש מסיים את השיחה.",
                failure_feedback_guidance="היפרדי לשלום."
            ),
            is_terminal=True
        )
    }
)

# --- Date Scenario Definition ---

_DATE_PERSONA = """
את/ה אלכס, בחור/ה ידידותי/ת בדייט ראשון.
סגנון דיבור: חמים, סקרן, שאלות פתוחות, הראי עניין כנה.
"""

date_graph = ScenarioGraph(
    id="date",
    name="דייט ראשון",
    base_persona=_DATE_PERSONA,
    goal="לקיים שיחה טבעית בדייט ראשון וליצור חיבור.",
    initial_state_id="start",
    states={
        "start": ScenarioState(
            id="start",
            description="פגישה",
            actor_instruction="אמרי: 'היי! איזה כיף סוף סוף להיפגש. איך עבר היום שלך?'",
            evaluation=EvaluationCriteria(
                criteria=["המשתמש מחזיר ברכה", "המשתמש ענה איך הוא מרגיש"],
                allowed_signals=["GREETING_RETURNED", "USER_RESPONDED"],
                pass_condition="המשתמש מברך בחזרה ועונה.",
                failure_feedback_guidance="המשתמש צריך להיות מנומס ולענות על השאלה."
            ),
            transitions=[
                Transition(
                    target_state_id="ask_hobby", 
                    condition="המשתמש ענה",
                    condition_id="GREETING_RETURNED"
                ),
                Transition(
                    target_state_id="ask_hobby",
                    condition="המשתמש הגיב",
                    condition_id="USER_RESPONDED",
                    priority=10
                )
            ]
        ),
        "ask_hobby": ScenarioState(
            id="ask_hobby",
            description="שבירת קרח / תחביבים",
            actor_instruction="שאלי על תחביב או עניין משותף.",
            evaluation=EvaluationCriteria(
                criteria=["המשתמש משתף תחביב או עניין"],
                allowed_signals=["HOBBY_SHARED"],
                pass_condition="המשתמש מדבר על עצמו.",
                failure_feedback_guidance="עודדי את המשתמש לשתף משהו שהוא אוהב לעשות."
            ),
            transitions=[
                Transition(
                    target_state_id="share_self", 
                    condition="המשתמש שיתף תחביב",
                    condition_id="HOBBY_SHARED"
                )
            ]
        ),
        "share_self": ScenarioState(
            id="share_self",
            description="שיתוף הדדי",
            actor_instruction="שתפי עובדה מעניינת קצרה על עצמך (אלכס), ואז שאלי על העדפות אוכל/שתייה.",
            evaluation=EvaluationCriteria(
                criteria=["המשתמש מקשיב ומגיב לשאלת ההעדפה"],
                allowed_signals=["PREFERENCE_SHARED"],
                pass_condition="המשתמש ענה על שאלת האוכל/שתייה.",
                failure_feedback_guidance="המשתמש צריך לענות מה הוא רוצה להזמין."
            ),
            transitions=[
                Transition(
                    target_state_id="ask_travel", 
                    condition="המשתמש ענה על ההעדפה",
                    condition_id="PREFERENCE_SHARED"
                )
            ]
        ),
        "ask_travel": ScenarioState(
            id="ask_travel",
            description="העמקת השיחה",
            actor_instruction="שאלי על יעדי טיול אהובים או מקומות שהם אוהבים.",
            evaluation=EvaluationCriteria(
                criteria=["המשתמש מתאר מקום או טיול"],
                allowed_signals=["TRAVEL_SHARED"],
                pass_condition="המשתמש משתף סיפור טיול או העדפה.",
                failure_feedback_guidance="המשתמש צריך לדבר על מקום שהוא אוהב."
            ),
            transitions=[
                Transition(
                    target_state_id="closing", 
                    condition="המשתמש שיתף מידע על טיולים",
                    condition_id="TRAVEL_SHARED"
                )
            ]
        ),
        "closing": ScenarioState(
            id="closing",
            description="סיום חלק הדייט",
            actor_instruction="הביעי שנהנית מאוד לדבר. הציעי לעשות זאת שוב.",
            evaluation=EvaluationCriteria(
                criteria=["המשתמש מסכים או מסרב בנימוס"],
                allowed_signals=["RESPONSE_TO_DATE"],
                pass_condition="המשתמש מגיב להצעה.",
                failure_feedback_guidance="המשתמש צריך לומר אם הוא נהנה גם כן."
            ),
            is_terminal=True
        )
    }
)

# --- Conflict Scenario Definition ---

_CONFLICT_PERSONA = """
את גברת ג'נקינס, שכנה עצבנית שמתלוננת על רעש.
סגנון דיבור: בהתחלה נוקשה וכועסת, נרגעת אם מתנצלים. ישירה מאוד.
"""

conflict_graph = ScenarioGraph(
    id="conflict",
    name="קונפליקט שכנים",
    base_persona=_CONFLICT_PERSONA,
    goal="לפתור קונפליקט שכנים: דה-אסקלציה והגעה לפתרון.",
    initial_state_id="start",
    states={
        "start": ScenarioState(
            id="start",
            description="התלונה",
            actor_instruction="התחלה כועסת: 'סליחה! אנחנו צריכים לדבר. הרעש מהדירה שלך אתמול בלילה היה בלתי נסבל.'",
            evaluation=EvaluationCriteria(
                criteria=["המשתמש מקשיב", "המשתמש לא תוקף בחזרה"],
                allowed_signals=["LISTENING_CONFIRMED", "USER_RESPONDED"],
                pass_condition="המשתמש מבין שהשכנה כועסת.",
                failure_feedback_guidance="המשתמש צריך לשאול מה קרה או להתנצל, לא להילחם בחזרה."
            ),
            transitions=[
                Transition(
                    target_state_id="express_frustration", 
                    condition="המשתמש הודה",
                    condition_id="LISTENING_CONFIRMED"
                ),
                Transition(
                    target_state_id="express_frustration",
                    condition="המשתמש הגיב",
                    condition_id="USER_RESPONDED",
                    priority=10
                )
            ]
        ),
        "express_frustration": ScenarioState(
            id="express_frustration",
            description="שחרור קיטור",
            actor_instruction="אמרי: 'לא יכולתי לישון בכלל! הקירות רעדו!' (חכי להתנצלות/הסבר).",
            evaluation=EvaluationCriteria(
                criteria=["המשתמש מתנצל או מסביר בנימוס"],
                allowed_signals=["APOLOGY_GIVEN"],
                pass_condition="המשתמש מציע התנצלות או הסבר תקף.",
                failure_feedback_guidance="המשתמש צריך להתנצל או להסביר ברוגע."
            ),
            transitions=[
                Transition(
                    target_state_id="negotiate", 
                    condition="המשתמש התנצל",
                    condition_id="APOLOGY_GIVEN"
                )
            ]
        ),
        "negotiate": ScenarioState(
            id="negotiate",
            description="משא ומתן לפתרון",
            actor_instruction="הירגעי מעט. שאלי: 'אז מה אתה מתכוון לעשות בקשר לזה בפעם הבאה?'",
            evaluation=EvaluationCriteria(
                criteria=["המשתמש מציע פתרון (למשל שעות שקט)"],
                allowed_signals=["SOLUTION_PROPOSED"],
                pass_condition="המשתמש מציע תיקון קונקרטי.",
                failure_feedback_guidance="המשתמש חייב להציע דרך למנוע את הרעש."
            ),
            transitions=[
                Transition(
                    target_state_id="closing", 
                    condition="המשתמש הציע פתרון",
                    condition_id="SOLUTION_PROPOSED"
                )
            ]
        ),
        "closing": ScenarioState(
            id="closing",
            description="פתרון",
            actor_instruction="קבלי את הפתרון (אם הוא סביר). 'בסדר, נקווה שיישאר שקט.'",
            evaluation=EvaluationCriteria(
                criteria=["המשתמש מאשר הסכמה"],
                allowed_signals=["AGREEMENT_CONFIRMED"],
                pass_condition="המשתמש מסיים את השיחה בנימוס.",
                failure_feedback_guidance="היפרדי לשלום."
            ),
            is_terminal=True
        )
    }
)

# Registry
SCENARIO_REGISTRY = {
    "interview": interview_graph,
    "bank": bank_graph,
    "grocery": grocery_graph,
    "date": date_graph,
    "conflict": conflict_graph
}

def get_scenario_graph(scenario_id: str) -> Optional[ScenarioGraph]:
    return SCENARIO_REGISTRY.get(scenario_id)