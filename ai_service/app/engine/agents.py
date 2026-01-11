import json
from typing import List, Dict, Optional, Any
from app.engine.schema import ScenarioState, AgentOutput
from app.engine.llm import llm_client

class EvaluatorAgent:
    """
    Analyzes the user's input against the current state's passing criteria.
    Decides if we move to the next state.
    """
    
    @staticmethod
    async def evaluate(
        user_text: str, 
        state: ScenarioState, 
        history: List[Dict[str, str]]
    ) -> AgentOutput:
        
        criteria_text = "\n".join([f"- {c}" for c in state.evaluation.criteria])
        
        system_prompt = (
            "You are a strict conversation evaluator.\n"
            "Analyze the user's latest message against the required criteria.\n"
            f"Current Context: {state.description}\n"
            f"Passing Criteria:\n{criteria_text}\n"
            f"Pass Condition: {state.evaluation.pass_condition}\n"
            "Determine if the user satisfied the criteria to move forward.\n"
            "Also classify the user's sentiment as 'positive', 'negative', or 'neutral'."
        )

        schema = (
            '{"passed": boolean, "reasoning": "string", "feedback": "string (optional internal note)", '
            '"suggested_transition": "string (name of next state or null)", '
            '"sentiment": "positive|negative|neutral"}'
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"User Input: {user_text}"}
        ]

        # In a real app, we might include recent history context here too

        result = await llm_client.generate_json(messages, schema)
        
        # Determine next state
        next_state = None
        if result.get("passed", False):
            # Simple logic: take the first transition if passed, or what LLM suggests
            # For this scripted engine, we usually just take the first transition if passed.
            if state.transitions:
                next_state = state.transitions[0].target_state_id
        
        return AgentOutput(
            passed=result.get("passed", False),
            reasoning=result.get("reasoning", ""),
            feedback=result.get("feedback", ""),
            next_state_id=next_state,
            sentiment=result.get("sentiment", "neutral")
        )

class RolePlayAgent:
    """
    Generates the in-character response.
    """
    
    # Heuristic constants
    MAX_TOTAL_TOKENS = 2048
    EST_CHARS_PER_TOKEN = 3.5 # Conservative estimate for Hebrew/English
    
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
        Constructs the enhanced system prompt with context and repair instructions.
        """
        # Extract context safely
        decision = llm_context.get("decision", {})
        decision_label = decision.get("label", "GATE_PASSED")
        signals = llm_context.get("signals", {})
        slots = llm_context.get("slots", {})
        filled_slots = slots.get("filled", {})
        missing_slots = slots.get("missing", [])
        
        # Base System Instructions
        prompt = (
            "SYSTEM INSTRUCTIONS:\n"
            "1. Output Language: Hebrew.\n"
            "2. Keep responses natural and concise.\n"
            "3. Use 1-2 short sentences max and ask at most one question.\n"
            "4. Avoid lists or long explanations unless the user asks.\n"
            f"5. STAY IN CHARACTER.\n\n"
            f"--- PERSONA ---\n{base_persona}\n\n"
            f"--- CURRENT SITUATION ---\n{state.description}\n"
            f"--- YOUR GOAL ---\n{state.actor_instruction}\n"
        )

        # Context Injection
        context_block = {
            "state": state.id,
            "decision": decision_label,
            "known_info": filled_slots,
            "missing_info": missing_slots,
            "user_signals": {k: v for k, v in signals.items() if v}
        }
        prompt += f"\n--- CONTEXT ---\n{json.dumps(context_block, ensure_ascii=False, indent=2)}\n"

        # Dynamic Repair Policy
        if decision_label == "UNCLEAR" or signals.get("user_confused"):
            prompt += (
                "\n--- REPAIR POLICY (User is Unclear/Confused) ---\n"
                "1. Acknowledge the user's input briefly.\n"
                "2. Ask a clarifying question specifically about the missing info.\n"
                "3. Provide 1-2 short Hebrew examples of valid answers.\n"
                "4. Do NOT advance the topic until this is resolved.\n"
                "Example: 'I understood you want a loan, but I need a number. For example: 20,000 or 50,000.'\n"
            )
        elif decision_label == "INAPPROPRIATE_FOR_CONTEXT":
             prompt += (
                "\n--- REPAIR POLICY (Inappropriate Behavior) ---\n"
                "1. Politely but firmly address the tone/content.\n"
                "2. Remind the user of the professional context.\n"
                "3. Ask them to rephrase or provide the needed info politely.\n"
            )
        elif signals.get("user_frustrated"):
            prompt += (
                "\n--- REPAIR POLICY (Frustration Detected) ---\n"
                "1. Acknowledge the user's frustration or repetition.\n"
                "2. Confirm what you ALREADY know (from 'known_info').\n"
                "3. Move the conversation forward gently.\n"
                "4. Do NOT re-ask for information you already have.\n"
            )
        
        # Memory & Focus Policy (Always Active)
        if filled_slots:
            prompt += f"\n--- MEMORY POLICY ---\nDo NOT re-ask for: {', '.join(filled_slots.keys())}.\n"
        
        if missing_slots and not (decision_label == "UNCLEAR" or signals.get("user_confused")):
            # Only focus on missing slots if not currently confused/repairing (repair has its own focus)
            prompt += f"Focus on obtaining: {', '.join(missing_slots)}.\n"

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
        # Ensure llm_context exists
        if llm_context is None:
            llm_context = {}

        # 1. Build Prompt
        system_prompt = RolePlayAgent._build_llm_prompt(base_persona, state, llm_context)

        # 2. Add Legacy Dynamic Guidance (if eval_result exists and failed, override/append)
        # Note: The new _build_llm_prompt handles repair policies, but we keep this for specific scenario guidance
        if eval_result and not eval_result.passed:
            system_prompt += (
                f"\n--- SPECIFIC SCENARIO GUIDANCE ---\n"
                f"The user did NOT meet the goal. {state.evaluation.failure_feedback_guidance}\n"
                f"Internal Reasoning: {eval_result.reasoning}"
            )
        
        # 3. Smart Context Trimming
        sys_tokens = RolePlayAgent._estimate_tokens(system_prompt)
        user_tokens = RolePlayAgent._estimate_tokens(user_text)
        reserved_tokens = sys_tokens + user_tokens + 200 
        
        available_history_tokens = RolePlayAgent.MAX_TOTAL_TOKENS - reserved_tokens
        
        trimmed_history = []
        current_history_tokens = 0
        
        for msg in reversed(history):
            msg_content = msg.get("content", "")
            msg_tokens = RolePlayAgent._estimate_tokens(msg_content)
            
            if current_history_tokens + msg_tokens < available_history_tokens:
                trimmed_history.append(msg)
                current_history_tokens += msg_tokens
            else:
                break 
        
        trimmed_history.reverse()
        
        # 4. Final Assembly
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(trimmed_history)
        
        if user_text.strip() == "[START]":
            messages.append({"role": "system", "content": "ACTION: Start the conversation according to your goal. Say the opening line."})
        else:
            messages.append({"role": "user", "content": user_text})

        # 5. Stream Response
        async for token in llm_client.generate_stream(messages):
            yield token
