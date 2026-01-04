from typing import List, Dict, Optional
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
    async def generate_response(
        user_text: str,
        base_persona: str,
        state: ScenarioState,
        history: List[Dict[str, str]],
        eval_result: Optional[AgentOutput] = None
    ):
        # 1. Construct System Prompt (The "Head" - Always Pinned)
        system_prompt = (
            "SYSTEM INSTRUCTIONS:\n"
            "1. Output Language: Hebrew.\n"
            "2. Keep responses natural and concise.\n"
            f"3. STAY IN CHARACTER.\n\n"
            f"--- PERSONA ---\n{base_persona}\n\n"
            f"--- CURRENT SITUATION ---\n{state.description}\n"
            f"--- YOUR GOAL ---\n{state.actor_instruction}\n"
        )

        # 2. Add Dynamic Guidance
        if eval_result and not eval_result.passed:
            system_prompt += (
                f"\n--- GUIDANCE ---\n"
                f"The user did NOT meet the goal. {state.evaluation.failure_feedback_guidance}\n"
                f"Internal Reasoning: {eval_result.reasoning}"
            )
        
        # 3. Smart Context Trimming (The "Middle")
        # We need to fit: System Prompt + History + User Message <= MAX_TOTAL_TOKENS
        
        sys_tokens = RolePlayAgent._estimate_tokens(system_prompt)
        user_tokens = RolePlayAgent._estimate_tokens(user_text)
        reserved_tokens = sys_tokens + user_tokens + 200 # +200 buffer for safety/output
        
        available_history_tokens = RolePlayAgent.MAX_TOTAL_TOKENS - reserved_tokens
        
        trimmed_history = []
        current_history_tokens = 0
        
        # Iterate backwards (newest first) to keep the most relevant context
        for msg in reversed(history):
            msg_content = msg.get("content", "")
            msg_tokens = RolePlayAgent._estimate_tokens(msg_content)
            
            if current_history_tokens + msg_tokens < available_history_tokens:
                trimmed_history.append(msg)
                current_history_tokens += msg_tokens
            else:
                break # Stop if we run out of space
        
        # Reverse back to chronological order
        trimmed_history.reverse()
        
        # 4. Final Assembly
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(trimmed_history)
        
        if user_text.strip() == "[START]":
            # For cold start, we don't append user text. 
            # We append a system trigger to start the conversation.
            messages.append({"role": "system", "content": "ACTION: Start the conversation according to your goal. Say the opening line."})
        else:
            messages.append({"role": "user", "content": user_text})

        # 5. Stream Response
        async for token in llm_client.generate_stream(messages):
            yield token
