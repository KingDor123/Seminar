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
            "Determine if the user satisfied the criteria to move forward."
        )

        schema = (
            '{"passed": boolean, "reasoning": "string", "feedback": "string (optional internal note)", ' 
            '"suggested_transition": "string (name of next state or null)"}'
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
            next_state_id=next_state
        )


class RolePlayAgent:
    """
    Generates the in-character response.
    """

    @staticmethod
    async def generate_response(
        user_text: str,
        base_persona: str,
        state: ScenarioState,
        history: List[Dict[str, str]],
        eval_result: Optional[AgentOutput] = None
    ):
        # 1. Construct System Prompt
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
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add limited history (last 5 turns)
        messages.extend(history[-5:])
        messages.append({"role": "user", "content": user_text})

        # 3. Stream Response
        async for token in llm_client.generate_stream(messages):
            yield token
