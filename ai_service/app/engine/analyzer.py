import logging
import json
from typing import List, Dict, Optional
from app.engine.schema import (
    ScenarioState, 
    InteractionFeatures, 
    SituationState, 
    Transition,
    CriterionAssessment
)
from app.engine.llm import llm_client

logger = logging.getLogger("AnalyzerAgent")

class AnalyzerAgent:
    """
    Stage 1 of the LLM Pipeline.
    Responsibility: Analyze the user's input based on deterministic features and state criteria.
    Output: Strict structural state (SituationState) - DIAGNOSTIC ONLY.
    NO Routing decisions here.
    """

    @staticmethod
    async def analyze(
        session_id: str,
        scenario_id: str,
        current_node_id: str,
        state: ScenarioState,
        features: InteractionFeatures,
        history: List[Dict[str, str]]
    ) -> SituationState:
        
        # 1. Prepare Context
        last_turn = history[-1] if history else {"content": "None"}
        
        # 2. Build Prompt
        criteria_list = "\n".join([f"- {c}" for c in state.evaluation.criteria])
        
        # New: List allowed signals
        allowed_signals = state.evaluation.allowed_signals
        signals_text = ", ".join(allowed_signals) if allowed_signals else "NONE (No signals available)"

        system_prompt = (
            "You are the STATE ANALYZER for a social skills training simulation.\n"
            "Your job is to DIAGNOSE the interaction. You do NOT decide the next state.\n"
            "You DO NOT generate dialogue.\n\n"
            f"--- CURRENT CONTEXT: {state.id} ---\n"
            f"Description: {state.description}\n"
            f"Expected Criteria:\n{criteria_list}\n"
            f"Pass Condition (Reference): {state.evaluation.pass_condition}\n"
            f"ALLOWED SIGNALS: [{signals_text}]\n\n"
            "Analyze the User Input below against these criteria."
        )
        
        user_prompt = (
            f"--- USER INPUT ANALYSIS ---\n"
            f"Text: \"{features.text}\"\n"
            f"Linguistic Data: Sentiment={features.sentiment_label} ({features.sentiment_score:.2f}), "
            f"Root='{features.dependency_root}', Intent='{features.named_entities}'\n"
            f"Prosody Data: WPM={features.wpm}, Silence={features.silence_duration}s\n\n"
            "Provide the following strictly in JSON:\n"
            "1. 'criteria_assessments': List of objects { 'criterion_text': string, 'met': boolean, 'reasoning': string }.\n"
            f"2. 'signals': List of strings from the ALLOWED SIGNALS list above that apply. If none apply, return empty list [].\n"
            