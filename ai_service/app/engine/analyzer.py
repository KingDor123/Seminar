import logging
import json
import os
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

# 3. Add a single DEBUG_MODE flag
DEBUG_MODE = os.getenv("DEBUG_MODE", "true").lower() == "true"

class AnalyzerAgent:
    """
    Stage 1 of the LLM Pipeline.
    Responsibility: Analyze the user's input based on deterministic features and state criteria.
    Output: Strict structural state (SituationState) - DIAGNOSTIC ONLY.
    NO Routing decisions here.
    
    IMPORTANT: This agent distinguishes between 'Emotional Sentiment' and 'Social Appropriateness'.
    - Sentiment: Internal emotional state (anger, joy, sadness).
    - Appropriateness: Adherence to social norms (politeness, role awareness).
    This separation allows the system to correct impolite behavior without mislabeling it as 'angry'.
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
        
        allowed_signals = state.evaluation.allowed_signals
        signals_text = ", ".join(allowed_signals) if allowed_signals else "NONE (No signals available)"

        system_prompt = (
            "You are the STATE ANALYZER for a social skills training simulation.\n"
            "Your job is to DIAGNOSE the interaction. You do NOT decide the next state.\n"
            "You DO NOT generate dialogue.\n\n"
            
            "--- DEFINITIONS (CRITICAL) ---\n"
            "1. Emotional Sentiment: Refers ONLY to expressed emotion (anger, frustration, joy). \n"
            "   - Imperative language alone is NOT emotional negative sentiment.\n"
            "   - Financial need or factual statements are NOT emotional negativity.\n"
            "   - 'negative' sentiment implies EXPLICIT emotional words (e.g. 'I am angry', 'This is frustrating').\n\n"
            
            "2. Social Appropriateness: Refers to politeness, role awareness, and pragmatic norms.\n"
            "   - Values: 'high', 'medium', 'low'.\n"
            "   - Mark 'low' IF: Imperative verbs (ציווי like 'give me'), blunt commands without 'please', or rude tone.\n"
            "   - Example: 'Give me money' -> Sentiment: Neutral, Appropriateness: Low.\n\n"
            
            "3. Special Signal: FINANCIAL_INELIGIBLE (Bank Scenario ONLY)\n"
            "   - Emit this signal IF user states: No income, inability to repay, or explicit refusal to pay back.\n"
            "   - This is NOT an emotional sentiment. It is an objective financial status.\n"
            "   - Example: 'I don't have a job' -> Signal: FINANCIAL_INELIGIBLE (Sentiment: Neutral).\n\n"
            
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
            "3. 'social_appropriateness': One of 'high', 'medium', 'low'. (Assess politeness/norms separately from emotion).\n"
            "4. 'general_summary': A brief neutral summary of what the user did.\n"
            "5. 'guidance_directive': Instructions for the Persona Actor on how to react tone-wise.\n"
            "6. 'suggested_sentiment': The sentiment label the Persona should adopt.\n"
        )
        
        # Log Prompt (Phase 2)
        if DEBUG_MODE:
            logger.info(f"[ANALYSIS] System Prompt:\n{system_prompt}")
            logger.info(f"[ANALYSIS] User Prompt:\n{user_prompt}")
        
        # 3. Define Output Schema for LLM guidance
        schema_desc = (
            "{\n"
            "  \"criteria_assessments\": [{ \"criterion_text\": \"...\", \"met\": true/false, \"reasoning\": \"...\" }],\n"
            "  \"signals\": [\"SIGNAL_NAME\"],\n"
            "  \"social_appropriateness\": \"high|medium|low\",\n"
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
            
            # Log Raw (as Dict) and Parsed Fields (Phase 2)
            if DEBUG_MODE:
                logger.info(f"[ANALYSIS] Raw LLM Response (Parsed JSON): {json.dumps(result, ensure_ascii=False)}")
                
        except Exception as e:
            logger.error(f"[ANALYSIS] Analyzer failed: {e}. Fallback to diagnostic error.")
            result = {
                "criteria_assessments": [],
                "signals": [],
                "social_appropriateness": "medium", # Fallback safe default
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
                if DEBUG_MODE:
                    logger.warning(f"[ANALYSIS] Analyzer Hallucinated Signal: {s}. Ignored.")

        # Log Final Signals & Summary (Phase 2)
        if DEBUG_MODE:
            logger.info(f"[ANALYSIS] Final Valid Signals: {validated_signals}")
            logger.info(f"[ANALYSIS] Appropriateness: {result.get('social_appropriateness', 'medium')}")
            logger.info(f"[ANALYSIS] Summary: {result.get('general_summary', 'No summary')}")

        return SituationState(
            session_id=session_id,
            scenario_id=scenario_id,
            current_node_id=current_node_id,
            criteria_assessments=assessments,
            signals=validated_signals,
            social_appropriateness=result.get("social_appropriateness", "medium"), # New Field
            general_summary=result.get("general_summary", "No summary provided."),
            guidance_directive=result.get("guidance_directive", "Continue naturally."),
            suggested_sentiment=result.get("suggested_sentiment", "neutral"),
            turn_count=len(history) + 1
        )