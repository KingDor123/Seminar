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
            description="Opening the interview",
            actor_instruction="Introduce yourself as Sarah. Welcome the candidate. Ask them to sit down and if they are ready.",
            evaluation=EvaluationCriteria(
                criteria=["User responds to greeting"],
                pass_condition="User acknowledges the greeting politely.",
                failure_feedback_guidance="User should simply say hello or confirm they are ready."
            ),
            transitions=[
                Transition(target_state_id="ask_intro", condition="User replied to greeting")
            ]
        ),
        "ask_intro": ScenarioState(
            id="ask_intro",
            description="Asking for self-introduction",
            actor_instruction="Ask: 'Tell me a little about yourself.' (ספר לי קצת על עצמך)",
            evaluation=EvaluationCriteria(
                criteria=["User provides professional background", "User speaks clearly"],
                pass_condition="User gives a brief overview of their background.",
                failure_feedback_guidance="Encourage the user to focus on their professional experience."
            ),
            transitions=[
                Transition(target_state_id="ask_strength", condition="User provided introduction")
            ]
        ),
        "ask_strength": ScenarioState(
            id="ask_strength",
            description="Asking about strengths",
            actor_instruction="Ask about a key professional strength or skill.",
            evaluation=EvaluationCriteria(
                criteria=["User names a strength", "User gives an example"],
                pass_condition="User identifies a strength relevant to the job.",
                failure_feedback_guidance="Ask the user to name one thing they are good at professionally."
            ),
            transitions=[
                Transition(target_state_id="ask_challenge", condition="User answered strength question")
            ]
        ),
        "ask_challenge": ScenarioState(
            id="ask_challenge",
            description="Asking about a challenge",
            actor_instruction="Ask about a professional challenge they overcame.",
            evaluation=EvaluationCriteria(
                criteria=["User describes a situation", "User describes action taken", "User describes result"],
                pass_condition="User tells a story about overcoming a difficulty.",
                failure_feedback_guidance="Prompt for a specific time something went wrong and how they fixed it."
            ),
            transitions=[
                Transition(target_state_id="ask_motivation", condition="User answered challenge question")
            ]
        ),
        "ask_motivation": ScenarioState(
            id="ask_motivation",
            description="Asking why they want the job",
            actor_instruction="Ask why they are interested in this specific position/company.",
            evaluation=EvaluationCriteria(
                criteria=["User shows interest", "User connects skills to role"],
                pass_condition="User explains their motivation.",
                failure_feedback_guidance="Ask what specifically attracted them to this role."
            ),
            transitions=[
                Transition(target_state_id="ask_user_questions", condition="User answered motivation question")
            ]
        ),
        "ask_user_questions": ScenarioState(
            id="ask_user_questions",
            description="Inviting user questions",
            actor_instruction="Ask if the candidate has any questions for you.",
            evaluation=EvaluationCriteria(
                criteria=["User asks a question OR declines politely"],
                pass_condition="User engages in the Q&A part.",
                failure_feedback_guidance="It is okay if they have no questions, but they should say so."
            ),
            transitions=[
                Transition(target_state_id="closing", condition="User finished asking questions")
            ]
        ),
        "closing": ScenarioState(
            id="closing",
            description="End of interview",
            actor_instruction="Thank the candidate for coming. Say you will be in touch soon. Goodbye.",
            evaluation=EvaluationCriteria(
                criteria=["User says goodbye"],
                pass_condition="User ends conversation.",
                failure_feedback_guidance="Say goodbye."
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
                pass_condition="המשתמש מאשר שהוא מעוניין להגיש בקשה להלוואה.",
                failure_feedback_guidance="המשתמש צריך לציין שהוא כאן לצורך בקשת הלוואה."
            ),
            transitions=[
                Transition(target_state_id="ask_amount", condition="המשתמש אישר כוונה")
            ]
        ),
        "ask_amount": ScenarioState(
            id="ask_amount",
            description="בקשת סכום ההלוואה",
            actor_instruction="שאל/י מהו סכום ההלוואה המשוער שבו הוא/היא מעוניין/ת. סימולציה בלבד; ללא מידע אישי או מזהה.",
            evaluation=EvaluationCriteria(
                criteria=["המשתמש מספק סכום מספרי"],
                pass_condition="המשתמש מציין סכום הלוואה ברור.",
                failure_feedback_guidance="המשתמש חייב לציין כמה כסף הוא צריך."
            ),
            transitions=[
                Transition(target_state_id="ask_purpose", condition="המשתמש סיפק סכום"),
                Transition(target_state_id="ask_income", condition="המשתמש סיפק גם סכום הלוואה וגם מטרה")
            ]
        ),
        "ask_purpose": ScenarioState(
            id="ask_purpose",
            description="בקשת מטרת ההלוואה",
            actor_instruction="שאל/י בקצרה מהי מטרת ההלוואה.",
            evaluation=EvaluationCriteria(
                criteria=["המשתמש מציין מטרה תקפה (רכב, שיפוץ וכו')"],
                pass_condition="המשתמש מסביר לשם מה נדרש הכסף.",
                failure_feedback_guidance="המשתמש צריך לומר מדוע הוא זקוק לכסף."
            ),
            transitions=[
                Transition(target_state_id="ask_income", condition="המשתמש סיפק מטרה")
            ]
        ),
        "ask_income": ScenarioState(
            id="ask_income",
            description="בקשת פרטי הכנסה",
            actor_instruction="שאל/י לגבי טווח הכנסה חודשית משוער והאם קיימות התחייבויות נוספות. שמור/י על משפט קצר והימנע/י מכל מזהה אישי או מסמכים. סימולציה בלבד.",
            evaluation=EvaluationCriteria(
                criteria=["המשתמש מספק פרטי הכנסה"],
                pass_condition="המשתמש מציין הכנסה משוערת.",
                failure_feedback_guidance="המשתמש צריך לספק מידע על הכנסה לצורך הבקשה."
            ),
            transitions=[
                Transition(target_state_id="present_terms", condition="המשתמש סיפק הכנסה")
            ]
        ),
        "present_terms": ScenarioState(
            id="present_terms",
            description="הצגת תנאי הלוואה (סימולציה בלבד)",
            actor_instruction="ציין/י שעל סמך המידע שנמסר המשתמש זכאי להלוואה. הצג/י ריבית סטנדרטית (לדוגמה: פריים + 2%). שאל/י האם התנאים מתאימים או אם יש שאלות. סימולציה בלבד; אין לבקש מידע אישי או מזהה (תעודת זהות, מספר חשבון, כתובת, טלפון, הכנסה מדויקת).",
            evaluation=EvaluationCriteria(
                criteria=["המשתמש מאשר או שואל לגבי התנאים"],
                pass_condition="המשתמש מתייחס לתנאים.",
                failure_feedback_guidance="המשתמש צריך לאשר אם ברצונו להמשיך עם תנאים אלו."
            ),
            transitions=[
                Transition(target_state_id="closing", condition="המשתמש אישר את התנאים")
            ]
        ),
        "closing": ScenarioState(
            id="closing",
            description="סיום הבקשה",
            actor_instruction="אשר/י שהבקשה הוגשה (סימולציה). הודה/י למשתמש ואחל/י יום טוב.",
            evaluation=EvaluationCriteria(
                criteria=["המשתמש נפרד"],
                pass_condition="המשתמש מסיים את השיחה.",
                failure_feedback_guidance="להיפרד לשלום."
            ),
            is_terminal=True
        ),
        "end_not_eligible": ScenarioState(
            id="end_not_eligible",
            description="End - Not Eligible",
            actor_instruction="Politely and empathetically explain that based on the current financial details (income vs commitments), we cannot proceed with the loan application at this moment. Suggest checking again in the future. Close the conversation.",
            evaluation=EvaluationCriteria(
                criteria=["Conversation ends"],
                pass_condition="User acknowledges.",
                failure_feedback_guidance="Politely close."
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
            description="Greeting at checkout",
            actor_instruction="Say: 'Hi! Welcome to FreshMarket. Did you find everything you needed?'",
            evaluation=EvaluationCriteria(
                criteria=["User replies to greeting"],
                pass_condition="User confirms they found items or asks for something.",
                failure_feedback_guidance="User should answer yes or no."
            ),
            transitions=[
                Transition(target_state_id="ask_club_card", condition="User replied")
            ]
        ),
        "ask_club_card": ScenarioState(
            id="ask_club_card",
            description="Club card check",
            actor_instruction="Ask if they have a club member card.",
            evaluation=EvaluationCriteria(
                criteria=["User says yes/no to club card"],
                pass_condition="User answers about the card.",
                failure_feedback_guidance="User needs to say if they have a card or not."
            ),
            transitions=[
                Transition(target_state_id="scan_items", condition="User answered card question")
            ]
        ),
        "scan_items": ScenarioState(
            id="scan_items",
            description="Scanning items",
            actor_instruction="Pretend to scan items. Make a small talk comment like 'Wow, these apples look great.'",
            evaluation=EvaluationCriteria(
                criteria=["User engages in small talk or acknowledgment"],
                pass_condition="User responds politely.",
                failure_feedback_guidance="User should acknowledge the comment."
            ),
            transitions=[
                Transition(target_state_id="ask_bag", condition="User responded")
            ]
        ),
        "ask_bag": ScenarioState(
            id="ask_bag",
            description="Bag preference",
            actor_instruction="Ask: 'Regular bag or reusable?' (שקית רגילה או רב-פעמית?)",
            evaluation=EvaluationCriteria(
                criteria=["User chooses bag type"],
                pass_condition="User selects a bag option.",
                failure_feedback_guidance="User must choose a bag type."
            ),
            transitions=[
                Transition(target_state_id="payment", condition="User chose bag")
            ]
        ),
        "payment": ScenarioState(
            id="payment",
            description="Payment",
            actor_instruction="State the total (e.g., 45 shekels). Ask for payment.",
            evaluation=EvaluationCriteria(
                criteria=["User offers payment"],
                pass_condition="User pays (states they are paying).",
                failure_feedback_guidance="User needs to pay."
            ),
            transitions=[
                Transition(target_state_id="closing", condition="User paid")
            ]
        ),
        "closing": ScenarioState(
            id="closing",
            description="Goodbye",
            actor_instruction="Thank them and wish them a great day.",
            evaluation=EvaluationCriteria(
                criteria=["User says goodbye"],
                pass_condition="User ends conversation.",
                failure_feedback_guidance="Say goodbye."
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
            description="Meeting up",
            actor_instruction="Say: 'Hi! So fun to finally meet. How was your day?'",
            evaluation=EvaluationCriteria(
                criteria=["User returns greeting", "User answers how they are"],
                pass_condition="User greets back and answers.",
                failure_feedback_guidance="User should be polite and answer the question."
            ),
            transitions=[
                Transition(target_state_id="ask_hobby", condition="User replied")
            ]
        ),
        "ask_hobby": ScenarioState(
            id="ask_hobby",
            description="Icebreaker / Hobbies",
            actor_instruction="Ask about a hobby or shared interest.",
            evaluation=EvaluationCriteria(
                criteria=["User shares a hobby or interest"],
                pass_condition="User talks about themselves.",
                failure_feedback_guidance="Encourage user to share something they like doing."
            ),
            transitions=[
                Transition(target_state_id="share_self", condition="User shared hobby")
            ]
        ),
        "share_self": ScenarioState(
            id="share_self",
            description="Sharing back",
            actor_instruction="Share a brief interesting fact about yourself (Alex), then ask about food/drink preferences.",
            evaluation=EvaluationCriteria(
                criteria=["User listens and responds to preference question"],
                pass_condition="User answers the food/drink question.",
                failure_feedback_guidance="User should answer what they want to order."
            ),
            transitions=[
                Transition(target_state_id="ask_travel", condition="User answered preference")
            ]
        ),
        "ask_travel": ScenarioState(
            id="ask_travel",
            description="Deepening conversation",
            actor_instruction="Ask about favorite travel destinations or places they love.",
            evaluation=EvaluationCriteria(
                criteria=["User describes a place or trip"],
                pass_condition="User shares a travel story or preference.",
                failure_feedback_guidance="User should talk about a place they like."
            ),
            transitions=[
                Transition(target_state_id="closing", condition="User shared travel info")
            ]
        ),
        "closing": ScenarioState(
            id="closing",
            description="End of date segment",
            actor_instruction="Express you had a great time talking. Suggest doing this again.",
            evaluation=EvaluationCriteria(
                criteria=["User agrees or politely declines"],
                pass_condition="User responds to the suggestion.",
                failure_feedback_guidance="User should say if they enjoyed it too."
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
            description="The Complaint",
            actor_instruction="Angry start: 'Excuse me! We need to talk. The noise from your apartment last night was unbearable.'",
            evaluation=EvaluationCriteria(
                criteria=["User listens", "User does not attack back"],
                pass_condition="User acknowledges the neighbor is upset.",
                failure_feedback_guidance="User should ask what happened or apologize, not fight back."
            ),
            transitions=[
                Transition(target_state_id="express_frustration", condition="User acknowledged")
            ]
        ),
        "express_frustration": ScenarioState(
            id="express_frustration",
            description="Venting",
            actor_instruction="Say: 'I couldn't sleep at all! It was shaking my walls!' (Wait for apology/explanation).",
            evaluation=EvaluationCriteria(
                criteria=["User apologizes OR explains politely"],
                pass_condition="User offers an apology or valid explanation.",
                failure_feedback_guidance="User needs to apologize or explain calmly."
            ),
            transitions=[
                Transition(target_state_id="negotiate", condition="User apologized")
            ]
        ),
        "negotiate": ScenarioState(
            id="negotiate",
            description="Negotiating solution",
            actor_instruction="Calm down slightly. Ask: 'So what are you going to do about it next time?'",
            evaluation=EvaluationCriteria(
                criteria=["User proposes a solution (e.g. quiet hours)"],
                pass_condition="User offers a concrete fix.",
                failure_feedback_guidance="User must suggest a way to prevent the noise."
            ),
            transitions=[
                Transition(target_state_id="closing", condition="User offered solution")
            ]
        ),
        "closing": ScenarioState(
            id="closing",
            description="Resolution",
            actor_instruction="Accept the solution (if reasonable). 'Fine, let's hope it stays quiet.'",
            evaluation=EvaluationCriteria(
                criteria=["User confirms agreement"],
                pass_condition="User ends conversation politely.",
                failure_feedback_guidance="Say goodbye."
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
