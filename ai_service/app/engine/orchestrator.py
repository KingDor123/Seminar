import logging
import json
import os
from typing import AsyncGenerator, Dict, Any, List, Optional, Callable

from app.engine.schema import (
    ScenarioGraph, 
    InteractionFeatures, 
    SituationState
)
from app.engine.scenarios import get_scenario_graph
from app.engine.state_manager import state_manager

# New Components
from app.engine.features import FeatureExtractor
from app.engine.analyzer import AnalyzerAgent
from app.engine.persona import PersonaAgent

logger = logging.getLogger("Orchestrator")

# 3. Add a single DEBUG_MODE flag
DEBUG_MODE = os.getenv("DEBUG_MODE", "true").lower() == "true"

# --- 3. Generalized Signal Guards ---
# Predicates: (features) -> bool
# If predicate returns False, the signal is rejected even if LLM emitted it.
SIGNAL_GUARDS: Dict[str, Callable[[InteractionFeatures], bool]] = {
    "AMOUNT_GIVEN": lambda f: any(char.isdigit() for char in f.text), # Heuristic: needs digits
    # Add more as needed, e.g. "GREETING" -> lambda f: f.text.len < 10 ...
}

class ScenarioOrchestrator:
    """
    The Central Controller of the AI Pipeline.
    Enforces the strict flow:
    Input -> Features -> Analyzer (LLM 1) -> Routing Logic (Code) -> State Update -> Persona (LLM 2) -> Output
    """
    
    async def process_turn(
        self,
        session_id: str,
        scenario_id: str,
        user_text: str,
        history: List[Dict[str, str]],
        audio_meta: Dict[str, Any] = {}
    ) -> AsyncGenerator[Any, None]:
        
        # 0. Load Context
        graph = get_scenario_graph(scenario_id)
        if not graph:
            yield f"Error: Scenario '{scenario_id}' not found."
            return

        # Load current pointer (or init)
        session_data = state_manager.get_state(session_id)
        current_node_id = session_data.current_node_id if session_data else graph.initial_state_id
        
        # Validate node existence
        if current_node_id not in graph.states:
            logger.warning(f"State {current_node_id} invalid. Resetting.")
            current_node_id = graph.initial_state_id
            
        current_state_obj = graph.states[current_node_id]
        
        # --- PHASE 0: COLD START HANDLING ---
        if user_text.strip() == "[START]":
            if DEBUG_MODE:
                logger.info("🎬 [ROUTING] Cold Start detected.")
            state_manager.update_state(session_id, scenario_id, graph.initial_state_id)
            
            # Synthetic situation for start
            initial_situation = SituationState(
                session_id=session_id,
                scenario_id=scenario_id,
                current_node_id=graph.initial_state_id,
                criteria_assessments=[],
                signals=[],
                general_summary="Session started.",
                guidance_directive="Start the conversation. Introduce yourself.",
                suggested_sentiment="welcoming"
            )
            
            async for token in PersonaAgent.generate(
                graph.base_persona,
                current_state_obj, 
                initial_situation,
                [] 
            ):
                yield token
            return

        # --- PHASE 1: FEATURE EXTRACTION (Deterministic) ---
        if DEBUG_MODE:
            logger.info("Phase 1: Feature Extraction")
        features = FeatureExtractor.extract(user_text, audio_meta)
        
        yield {
            "type": "debug_features",
            "sentiment": features.sentiment_score,
            "wpm": features.wpm,
            "entities": features.named_entities
        }

        # --- PHASE 2: ANALYSIS (Analyzer LLM - Diagnostic Only) ---
        if DEBUG_MODE:
            logger.info(f"Phase 2: Analysis (Current: {current_node_id})")
        situation = await AnalyzerAgent.analyze(
            session_id,
            scenario_id,
            current_node_id,
            current_state_obj,
            features,
            history
        )
        
        # --- PHASE 3: ROUTING LOGIC (Orchestrator Exclusive) ---
        
        raw_signals = set(situation.signals)
        allowed_signals = set(current_state_obj.evaluation.allowed_signals)
        
        if DEBUG_MODE:
            logger.info(f"[ROUTING] Allowed Signals for {current_node_id}: {allowed_signals}")
            logger.info(f"[ROUTING] Raw Signals from Analyzer: {raw_signals}")
        
        # FIX: Deterministic Signal Injection for "start" state
        # If we are in "start" and user said something (not [START]), force USER_RESPONDED
        if current_node_id == graph.initial_state_id and user_text.strip() != "[START]":
            if DEBUG_MODE:
                logger.info("⚡ [ROUTING] Injecting USER_RESPONDED signal for start state exit.")
            raw_signals.add("USER_RESPONDED")
            # Ensure it is allowed (we updated scenarios to allow it, but safety check)
            if "USER_RESPONDED" not in allowed_signals:
                # This should not happen if scenarios.py was updated correctly, but good for debug
                logger.warning("[ROUTING] USER_RESPONDED injected but not in allowed_signals! Check scenarios.py")

        # 2. Unknown Signals Reporting
        unknown_signals = raw_signals - allowed_signals
        if unknown_signals:
            if DEBUG_MODE:
                logger.warning(f"⚠️ [ROUTING] Unknown signals detected in state {current_node_id}: {unknown_signals}. Ignoring.")
        
        # Filter to allowed only
        valid_signals = raw_signals.intersection(allowed_signals)

        # 3. Guard Application (Generalized)
        filtered_signals = set()
        for sig in valid_signals:
            guard = SIGNAL_GUARDS.get(sig)
            if guard:
                if guard(features):
                    filtered_signals.add(sig)
                else:
                    if DEBUG_MODE:
                        logger.warning(f"🛡️ [ROUTING] Security: Guard blocked signal '{sig}' based on features.")
            else:
                filtered_signals.add(sig)
        
        if DEBUG_MODE:
            logger.info(f"[ROUTING] Final Filtered Signals: {filtered_signals}")
        
        # 4. Select Transition with Ambiguity Check
        sorted_transitions = sorted(current_state_obj.transitions, key=lambda t: t.priority, reverse=True)
        
        next_node_id = current_node_id
        transition_reason = "No matching signal"
        
        # Find potential matches at the highest priority level
        matches = []
        if sorted_transitions:
            highest_pri_match = -9999
            for transition in sorted_transitions:
                if transition.condition_id in filtered_signals:
                    if not matches:
                        matches.append(transition)
                        highest_pri_match = transition.priority
                    elif transition.priority == highest_pri_match:
                        matches.append(transition)
        
        # 1. Ambiguity Detection
        if len(matches) > 1:
            if DEBUG_MODE:
                logger.warning(
                    f"⚠️ [ROUTING] Ambiguous Transitions in {current_node_id}: "
                    f"Multiple transitions matched signals {filtered_signals} at priority {matches[0].priority}. "
                    f"Targets: {[m.target_state_id for m in matches]}. "
                    f"Defaulting to first match: {matches[0].target_state_id}"
                )

        if matches:
            chosen = matches[0]
            next_node_id = chosen.target_state_id
            transition_reason = f"Signal '{chosen.condition_id}' matched priority {chosen.priority}"
            if DEBUG_MODE:
                logger.info(f"🚀 [ROUTING] Decision: Transition to '{next_node_id}'. Reason: {transition_reason}")
        else:
            if DEBUG_MODE:
                logger.info(f"🛑 [ROUTING] Decision: Stay in '{current_node_id}'. Reason: {transition_reason}")

        # Yield analysis result for dashboard
        # FIX: Add skip_persist flag if no transition occurred
        skip_persist = (next_node_id == current_node_id)
        
        yield {
            "type": "analysis",
            "passed": next_node_id != current_node_id,
            "reasoning": f"{situation.general_summary} ({transition_reason})", 
            "sentiment": features.sentiment_label,
            "next_state": next_node_id,
            "signals": list(filtered_signals),
            "skip_persist": skip_persist # Backend hint
        }

        # Update State
        if next_node_id != current_node_id:
            state_manager.update_state(session_id, scenario_id, next_node_id)
            yield {
                "type": "transition",
                "from": current_node_id,
                "to": next_node_id
            }

        # --- PHASE 4: RESPONSE GENERATION (Persona LLM) ---
        target_state_obj = graph.states.get(next_node_id, current_state_obj)
        
        generation_history = history.copy()
        generation_history.append({"role": "user", "content": user_text})

        if DEBUG_MODE:
            logger.info(f"Phase 4: Generating Response for {next_node_id}")
        
        async for token in PersonaAgent.generate(
            graph.base_persona,
            target_state_obj,
            situation,
            generation_history
        ):
            yield token

# Singleton
orchestrator = ScenarioOrchestrator()
