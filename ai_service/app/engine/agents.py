import json
from typing import List, Dict, Optional, Any
from app.engine.schema import ScenarioState, AgentOutput
from app.engine.llm import llm_client

class ContextAnalyzerAgent:
    """
    Aya: The Situational Analyzer (Sensor).
    Observes user input and conversational context to produce a structured state description.
    Does NOT decide progression, response, or corrective action.
    """
    
    @staticmethod
    async def analyze_context(
        user_text: str, 
        state: ScenarioState, 
        history: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        
        system_prompt = (
            "You are a clinical conversational observer analyzing a user's input in a social skills training scenario.\n"
            "Your role is PURE ANALYSIS. Do not interpret for the user. Do not suggest responses.\n"
            f"Current Context: {state.description}\n\n"
            "Analyze the following dimensions strictly:\n"
            "1. Intent: What is the user functionally trying to do? (e.g., attempt_answer, avoidance, silence, clarification_request)\n"
            "2. Clarity: 0.0-1.0 score of how intelligible the input is.\n"
            "3. Confidence: 0.0-1.0 score of user's apparent confidence.\n"
            "4. Engagement: low/medium/high.\n"
            "5. Emotional Tone: neutral/positive/negative/uncertain.\n"
            "- readiness: Is the user ready to proceed? (ready/not_ready)\n"
            "  * 'not_ready': Greetings (Hi, Hello), pure acknowledgements (Okay, Yes), confusion (What?), vague social chatter, or SHORT COMMANDS without details (e.g., 'Give me money', 'Start').\n"
            "  * 'ready': User provides ANY relevant info (amount, purpose, income), states a clear intent WITH details (e.g. 'I want a car loan'), or asks a specific relevant question.\n"
        )

        schema = (
            '{"intent": "string", '
            '"clarity": float, '
            '"confidence": float, '
            '"engagement": "low|medium|high", '
            '"emotional_tone": "neutral|positive|negative|uncertain", '
            '"readiness": "ready|not_ready", '
            '"signals": ["string"], '
            '"extracted_slots": {"amount": "string|null", "purpose": "string|null", "income": "string|null"}}'
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"User Input: {user_text}"}
        ]

        result = await llm_client.generate_json(messages, schema)
        return result

class RolePlayAgent:
    """
    Step 2: The "Actor". Generates the in-character response using the 
    analysis from Step 1.
    """
    
    # Heuristic constants
    MAX_TOTAL_TOKENS = 2048
    EST_CHARS_PER_TOKEN = 3.5 
    
    @staticmethod
    def _estimate_tokens(text: str) -> int:
        return int(len(text) / RolePlayAgent.EST_CHARS_PER_TOKEN) + 5

    @staticmethod
    def _build_llm_prompt(
        base_persona: str,
        state: ScenarioState,
        llm_context: Dict[str, Any]
    ) -> str:
        """
        Constructs the natural language system prompt.
        We use natural summaries instead of rigid JSON to keep the model 'human'.
        """
        decision = llm_context.get("decision", {})
        decision_label = decision.get("label", "GATE_PASSED")
        signals = llm_context.get("signals", {})
        slots = llm_context.get("slots", {})
        filled_slots = slots.get("filled", {})
        missing_slots = slots.get("missing", [])
        
        prompt = (
            "SYSTEM INSTRUCTIONS:\n"
            "1. Output Language: Hebrew.\n"
            "2. Keep responses natural and concise.\n"
            "3. Use 1-2 short sentences max and ask at most one question.\n"
            f"4. STAY IN CHARACTER.\n\n"
            f"--- PERSONA ---\n{base_persona}\n\n"
            f"--- CURRENT SITUATION ---\n{state.description}\n"
            f"--- YOUR GOAL ---\n{state.actor_instruction}\n"
        )

        # Natural Language Context Summary (Better for Aya-8b than raw JSON)
        prompt += "\n--- CONTEXT SUMMARY ---\n"
        prompt += f"- Current Step: {state.id}\n"
        
        if filled_slots:
            prompt += f"- Known Information: {', '.join([f'{k}: {v}' for k, v in filled_slots.items()])}\n"
        
        if missing_slots:
            prompt += f"- Still Missing: {', '.join(missing_slots)}\n"

        # Behavior Handling
        if decision_label == "UNCLEAR" or signals.get("user_confused"):
            prompt += (
                "\n--- CONVERSATION REPAIR ---\n"
                "The user's response was unclear. Gently acknowledge what they said, "
                "but ask specifically for the missing info with a short example.\n"
            )
        elif signals.get("user_frustrated"):
            prompt += (
                "\n--- EMPATHY NOTE ---\n"
                "The user seems frustrated. Acknowledge their feelings or what they already said, "
                "and try to move to the next point politely.\n"
            )
        elif signals.get("readiness") == "not_ready":
            prompt += (
                "\n--- SOCIAL BRIDGE (MODE: CHAT) ---\n"
                "The user is greeting you or chatting socially.\n"
                "1. Ignore any technical 'reasoning' provided below.\n"
                "2. Respond naturally, warmly, and politely as your Persona.\n"
                "3. Do NOT ask for the missing information (loan amount, etc.) yet.\n"
                "4. Simply build rapport.\n"
            )

        if filled_slots:
            prompt += f"\n--- MEMORY ---\nDo NOT ask for information already provided above.\n"

        return prompt

    @staticmethod
    async def generate_response(
        user_text: str,
        base_persona: str,
        state: ScenarioState,
        history: List[Dict[str, str]],
        eval_result: Optional[AgentOutput] = None,
        llm_context: Dict[str, Any] = None
    ):
        if llm_context is None:
            llm_context = {}

        # 1. Build Prompt
        system_prompt = RolePlayAgent._build_llm_prompt(base_persona, state, llm_context)

        # 2. Specific Guidance (Backward Compatibility)
        if eval_result and not eval_result.passed:
            system_prompt += f"\nNote: {state.evaluation.failure_feedback_guidance}\n"
        
        # 3. Trim context...
        sys_tokens = RolePlayAgent._estimate_tokens(system_prompt)
        user_tokens = RolePlayAgent._estimate_tokens(user_text)
        reserved_tokens = sys_tokens + user_tokens + 200 
        available_history_tokens = RolePlayAgent.MAX_TOTAL_TOKENS - reserved_tokens
        
        trimmed_history = []
        current_history_tokens = 0
        for msg in reversed(history):
            msg_tokens = RolePlayAgent._estimate_tokens(msg.get("content", ""))
            if current_history_tokens + msg_tokens < available_history_tokens:
                trimmed_history.append(msg)
                current_history_tokens += msg_tokens
            else:
                break 
        trimmed_history.reverse()
        
        # 4. Assembly
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(trimmed_history)
        
        if user_text.strip() == "[START]":
            messages.append({"role": "system", "content": "ACTION: Start the conversation according to your goal."})
        else:
            messages.append({"role": "user", "content": user_text})

        # 5. Stream
        async for token in llm_client.generate_stream(messages):
            yield token
