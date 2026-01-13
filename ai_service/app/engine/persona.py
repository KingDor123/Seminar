import logging
import os
from typing import List, Dict, AsyncGenerator
from app.engine.schema import ScenarioState, SituationState
from app.engine.llm import llm_client

logger = logging.getLogger("PersonaAgent")

# 3. Add a single DEBUG_MODE flag
DEBUG_MODE = os.getenv("DEBUG_MODE", "true").lower() == "true"

class PersonaAgent:
    """
    Stage 2 of the LLM Pipeline.
    Responsibility: Generate the user-facing response (Actor).
    Input: Strict SituationState + Persona + History.
    Output: Streamed text.
    """

    @staticmethod
    async def generate(
        base_persona: str,
        target_state: ScenarioState,
        situation: SituationState,
        history: List[Dict[str, str]]
    ) -> AsyncGenerator[str, None]:

        # 1. Build System Instructions
        system_prompt = (
            "You are a professional role-play actor. \n"
            "Your goal is to simulate a realistic social interaction for training purposes.\n"
            "--- CHARACTER ---"
            f"{base_persona}\n\n"
            "--- CURRENT SCENE CONTEXT ---"
            f"{target_state.description}\n"
            f"Goal for this step: {target_state.actor_instruction}\n\n"
            "--- DIRECTION FROM DIRECTOR ---"
        )

        # Add dynamic direction from Analyzer (Diagnostic)
        system_prompt += (
            f"Context from last turn: {situation.general_summary}\n"
            f"Acting Guidance: {situation.guidance_directive}\n"
            f"Sentiment to project: {situation.suggested_sentiment}\n"
        )

        # STRICT LANGUAGE ENFORCEMENT
        # We explicitly forbid any other language to prevent model drifting.
        system_prompt += (
            "\nRULES:\n"
            "1. Output Language: Hebrew ONLY. (עברית בלבד)\n"
            "2. Keep it concise (1-2 sentences). Do not monologue.\n"
            "3. Stay 100% in character. Never mention you are an AI or actor.\n"
            "4. Respond naturally to the user's last message."
        )

        # Log System Prompt (Phase 4)
        if DEBUG_MODE:
            logger.info(f"[PERSONA] Target State: {target_state.id}")
            logger.info(f"[PERSONA] System Prompt:\n{system_prompt}")

        # 2. History Management (Simple Trimming)
        MAX_CHARS = 4000
        trimmed_history = []
        current_chars = len(system_prompt)

        for msg in reversed(history):
            content_len = len(msg.get("content", ""))
            if current_chars + content_len < MAX_CHARS:
                trimmed_history.append(msg)
                current_chars += content_len
            else:
                break

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(reversed(trimmed_history))

        if DEBUG_MODE:
            logger.info(f"[PERSONA] Generation Starting...")

        # 3. Stream
        async for token in llm_client.generate_stream(messages):
            yield token
            
        if DEBUG_MODE:
            logger.info(f"[PERSONA] Generation Complete.")