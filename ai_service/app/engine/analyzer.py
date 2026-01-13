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
            "3. 'general_summary': A brief neutral summary of what the user did.\n"
            "4. 'guidance_directive': Instructions for the Persona Actor on how to react tone-wise.\n"
            "5. 'suggested_sentiment': The sentiment label the Persona should adopt.\n"
        )
        
        # 3. Define Output Schema for LLM guidance
        schema_desc = (
            "{\n"
            "  \"criteria_assessments\": [{ \"criterion_text\": \"...\", \"met\": true/false, \"reasoning\": \"...\" }],\n"
            "  \"signals\": [\"SIGNAL_NAME\"],\n"
            "  \"general_summary\": \"...\",\n"
            "  \"guidance_directive\": \"...\",\n"
            "  \"suggested_sentiment\": \"...\"\n"
            "}\n"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        # 4. LLM Call
        try:
            result = await llm_client.generate_json(messages, schema_desc)
        except Exception as e:
            logger.error(f"Analyzer failed: {e}. Fallback to diagnostic error.")
            result = {
                "criteria_assessments": [],
                "signals": [],
                "general_summary": "System Analysis Error",
                "guidance_directive": "Apologize and ask the user to repeat.",
                "suggested_sentiment": "neutral"
            }

        # 5. Construct SituationState
        assessments = []
        raw_assessments = result.get("criteria_assessments", [])
        
        for raw in raw_assessments:
            assessments.append(CriterionAssessment(
                criterion_text=raw.get("criterion_text", "Unknown"),
                met=raw.get("met", False),
                reasoning=raw.get("reasoning", "")
            ))
            
        # Validate Signals (Injection Hardening Step 1)
        raw_signals = result.get("signals", [])
        validated_signals = []
        for s in raw_signals:
            if s in allowed_signals:
                validated_signals.append(s)
            else:
                logger.warning(f"Analyzer Hallucinated Signal: {s}. Ignored.")

        return SituationState(
            session_id=session_id,
            scenario_id=scenario_id,
            current_node_id=current_node_id,
            criteria_assessments=assessments,
            signals=validated_signals,
            general_summary=result.get("general_summary", "No summary provided."),
            guidance_directive=result.get("guidance_directive", "Continue naturally."),
            suggested_sentiment=result.get("suggested_sentiment", "neutral"),
            turn_count=len(history) + 1
        )
