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
    goal="לנהל בקשת הלוואה מקצועית: איסוף נתונים פיננסיים, הסבר תנאים, ושמירה על תקשורת ברורה.",
    initial_state_id="start",
    states={
        "start": ScenarioState(
            id="start",
            description="Opening the call (simulation only)",
            actor_instruction="Introduce yourself as Dana from the bank. Ask how you can help with the loan application today. Simulation only; do not request any personal or identifying information.",
            evaluation=EvaluationCriteria(
                criteria=["User states intent to apply for a loan"],
                pass_condition="User confirms they want to apply for a loan.",
                failure_feedback_guidance="User needs to state they are here for the loan application."
            ),
            transitions=[
                Transition(target_state_id="ask_amount", condition="User confirmed intent")
            ]
        ),
        "ask_amount": ScenarioState(
            id="ask_amount",
            description="Asking for loan amount",
            actor_instruction="Ask for the approximate loan amount they want. (באיזה סכום הלוואה את/ה מעוניין/ת?) Simulation only; no personal or identifying info.",
            evaluation=EvaluationCriteria(
                criteria=["User provides a numeric amount"],
                pass_condition="User states a clear loan amount.",
                failure_feedback_guidance="User must specify how much money they need."
            ),
            transitions=[
                Transition(target_state_id="ask_purpose", condition="User provided amount")
            ]
        ),
        "ask_purpose": ScenarioState(
            id="ask_purpose",
            description="Asking for loan purpose",
            actor_instruction="Ask for the purpose of the loan in one short question. (מהי מטרת ההלוואה?) Simulation only; no personal or identifying info.",
            evaluation=EvaluationCriteria(
                criteria=["User states a valid purpose (car, renovation, etc.)"],
                pass_condition="User explains what the money is for.",
                failure_feedback_guidance="User needs to say why they need the money."
            ),
            transitions=[
                Transition(target_state_id="ask_income", condition="User provided purpose")
            ]
        ),
        "ask_income": ScenarioState(
            id="ask_income",
            description="Asking for income details",
            actor_instruction="Ask for an approximate monthly income range and whether they have other commitments. Keep it to one short sentence and avoid any personal identifiers or documents. Simulation only.",
            evaluation=EvaluationCriteria(
                criteria=["User provides income details"],
                pass_condition="User states their approximate income.",
                failure_feedback_guidance="User needs to provide income information for the application."
            ),
            transitions=[
                Transition(target_state_id="present_terms", condition="User provided income")
            ]
        ),
        "present_terms": ScenarioState(
            id="present_terms",
            description="Presenting loan options (simulation only)",
            actor_instruction="State that based on the provided info, they are eligible. Mention a standard interest rate (e.g., Prime + 2%). Ask if these terms work or if they have questions. Simulation only; do NOT request personal or identifying info (ID, account number, address, phone, exact income).",
            evaluation=EvaluationCriteria(
                criteria=["User accepts or asks about terms"],
                pass_condition="User acknowledges the terms.",
                failure_feedback_guidance="User should confirm if they want to proceed with these terms."
            ),
            transitions=[
                Transition(target_state_id="closing", condition="User accepted terms")
            ]
        ),
        "closing": ScenarioState(
            id="closing",
            description="Closing the application",
            actor_instruction="Confirm the application is submitted (simulation). Thank them and say goodbye.",
            evaluation=EvaluationCriteria(
                criteria=["User says goodbye"],
                pass_condition="User ends conversation.",
                failure_feedback_guidance="Say goodbye."
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
