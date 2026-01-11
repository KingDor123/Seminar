import logging
from typing import AsyncGenerator, Dict, Any, List, Optional

from app.engine.schema import ScenarioGraph, AgentOutput
from app.engine.scenarios import get_scenario_graph
from app.engine.state_manager import state_manager
from app.engine.agents import RolePlayAgent, ContextAnalyzerAgent
from app.engine.metrics import MetricsEngine
from app.engine.decision import DecisionEngine
from app.engine.memory import slot_manager
from app.engine.norms import norm_manager
from app.engine.signals import signal_manager

# Map states to the slots they require/collect
STATE_SLOT_MAP = {
    "ask_amount": "amount",
    "ask_purpose": "purpose",
    "ask_income": "income"
}

logger = logging.getLogger("Orchestrator")

class ScenarioOrchestrator:
    
    async def process_turn(
        self,
        session_id: str,
        scenario_id: str,
        user_text: str,
        history: List[Dict[str, str]],
        stt_data: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Any, None]:
        
        # 1. Load Graph
        graph = get_scenario_graph(scenario_id)
        if not graph:
            yield f"Error: Scenario '{scenario_id}' not found."
            return

        # 2. Load State
        is_cold_start = user_text.strip() == "[START]"
        session_data = state_manager.get_state(session_id)

        if is_cold_start:
            # Clear all session data on start
            slot_manager.clear_slots(session_id)
            norm_manager.clear_norms(session_id)
            signal_manager.clear_signals(session_id)
            
            current_node_id = graph.initial_state_id
            state_manager.update_state(session_id, scenario_id, current_node_id)
        elif session_data:
            if session_data.scenario_id != scenario_id:
                logger.warning(
                    f"Session {session_id} scenario mismatch ({session_data.scenario_id} != {scenario_id}); resetting state."
                )
                current_node_id = graph.initial_state_id
                state_manager.update_state(session_id, scenario_id, current_node_id)
            else:
                current_node_id = session_data.current_node_id
        else:
            current_node_id = graph.initial_state_id
            state_manager.update_state(session_id, scenario_id, current_node_id)

        current_state = graph.states.get(current_node_id)
        if not current_state:
            logger.warning(
                f"Invalid state '{current_node_id}' for scenario '{scenario_id}'; resetting to initial state."
            )
            current_node_id = graph.initial_state_id
            state_manager.update_state(session_id, scenario_id, current_node_id)
            current_state = graph.states.get(current_node_id)
            if not current_state:
                yield "Error: Invalid state configuration."
                return

        # --- SPECIAL CASE: INITIALIZATION ---
        if is_cold_start:
            logger.info(f"🎬 Initializing conversation in state: {current_node_id}")
            # Skip evaluation, just act out the initial state
            async for token in RolePlayAgent.generate_response(
                user_text="[START]", # Pass strict signal
                base_persona=graph.base_persona,
                state=current_state,
                history=[], # No history for start
                eval_result=None
            ):
                yield token
            return

        # --- STEP 1: CONTEXTUAL UNDERSTANDING (LLM CALL #1) ---
        logger.info(f"🧠 Analyzing context for turn in state: {current_node_id}")
        llm_analysis = await ContextAnalyzerAgent.analyze_context(user_text, current_state, history)

        # 3. New Pipeline: Metrics -> Rules -> Decision (The "Gate")
        logger.info(f"🧐 Evaluating turn in state: {current_node_id}")
        
        # Calculate Metrics
        metrics = MetricsEngine.compute_metrics(user_text, stt_data or {})
        
        # Merge LLM Understanding with Deterministic Metrics
        llm_slots = llm_analysis.get("extracted_slots", {})
        for slot_key, slot_val in llm_slots.items():
            if slot_val:
                metrics.extracted_slots[slot_key] = slot_val

        # --- MEMORY UPDATE ---
        if metrics.extracted_slots:
            slot_manager.update_slots(session_id, metrics.extracted_slots)
        
        current_slots = slot_manager.get_slots(session_id)
        
        # --- FRUSTRATION & SIGNAL DETECTION ---
        llm_signals_list = llm_analysis.get("signals", [])
        readiness = llm_analysis.get("readiness", "ready")
        intent = llm_analysis.get("intent", "unknown")
        
        is_frustrated = (
            metrics.lemma_repetition_ratio > 0.4 
            or "frustration" in llm_signals_list
            or "anger" in llm_signals_list
        )
        is_confused = (
            "confusion" in llm_signals_list 
            or intent == "clarification_request"
        )
        
        # --- OBSERVABILITY: READINESS ---
        # Using intent and signals for reasoning as 'reasoning' field was removed from schema
        logger.info(f"[READINESS] value={readiness} intent={intent} signals={llm_signals_list}")
        
        # Apply Decision Logic
        decision = DecisionEngine.decide(metrics, current_state, raw_text=user_text, session_id=str(session_id))
        
        # --- SOFT READINESS CHECK (Orchestrator Authority) ---
        # If the Gate passed (no hard violations) but Aya says 'not_ready' (greeting/confusion),
        # we HOLD the state transition to be polite.
        if decision.gate_passed and readiness == "not_ready":
            logger.info(f"[ORCHESTRATOR] Readiness Check: User is PASS but NOT_READY. Switching to HOLD.")
            decision.gate_passed = False
            decision.label = "HOLD"
        
        # --- SIGNAL & NORM UPDATE ---
        signal_data = {
            "decision_label": decision.label,
            "current_state": current_node_id,
            "turn_frustration": is_frustrated,
            "repair_given": decision.label in ["BLOCK", "HOLD"] or is_confused
        }
        signal_manager.update_signals(session_id, signal_data)
        
        # Mark Norms Taught (If violation triggered a block)
        if decision.label == "BLOCK":
            norm_manager.mark_as_taught(session_id, "imperative")
            
        current_norms = norm_manager.get_norms(session_id)
        current_signals = signal_manager.get_signals(session_id)

        # Prepare Feedback for Agent
        feedback_context = decision.label
        if is_frustrated:
             feedback_context += ". USER SEEMS FRUSTRATED or REPEATING. Acknowledge known info."
        
        if decision.label == "HOLD":
             feedback_context += ". User is valid but NOT READY (e.g., greeting). Respond socially/helpfully. Do NOT ask for new info yet."

        # Append Memory Context
        memory_str = f"Known Info: {current_slots.dict(exclude_none=True)}"
        
        # --- BUILD LLM CONTEXT ---
        missing_slots = []
        required_slot_for_state = STATE_SLOT_MAP.get(target_state.id) if 'target_state' in locals() else STATE_SLOT_MAP.get(current_state.id)
        # Wait, target_state is calculated later. Use current_state for now.
        required_slot_for_state = STATE_SLOT_MAP.get(current_state.id)
        
        if required_slot_for_state and not getattr(current_slots, required_slot_for_state):
            missing_slots.append(required_slot_for_state)

        llm_context = {
            "session_id": str(session_id),
            "scenario_id": str(scenario_id),
            "state": current_state.id,
            "decision": {
                "label": decision.label,
                "reason": "; ".join(decision.reasons),
                "passed": decision.gate_passed
            },
            "slots": {
                "filled": current_slots.dict(exclude_none=True),
                "missing": missing_slots
            },
            "signals": {
                "user_frustrated": is_frustrated,
                "repetition_score": metrics.lemma_repetition_ratio,
                "user_confused": is_confused or current_signals.confusion_streak > 0,
                "progress_stalled": current_signals.progress_stalled,
                "readiness": readiness,
                "intent": intent,
                "emotional_tone": llm_analysis.get("emotional_tone", "neutral")
            },
            "norms_taught": list(current_norms.taught_norms)
        }
        
        # --- OBSERVABILITY ---
        # Compact context log
        logger.info(f"[LLM_CONTEXT] session={session_id} state={current_state.id} decision={decision.label} missing={missing_slots} signals={llm_context['signals']} norms={llm_context['norms_taught']}")
        
        # Convert to AgentOutput for compatibility with RolePlayAgent
        eval_result = AgentOutput(
            passed=decision.gate_passed,
            reasoning=f"{llm_analysis.get('reasoning', '')} | {'; '.join(decision.reasons)}",
            feedback=feedback_context,
            next_state_id=None,
            sentiment="neutral"
        )
        
        # Yield metadata about the evaluation
        yield {
            "type": "analysis",
            "sentiment": "neutral", 
            "decision": decision.label,
            "reasons": decision.reasons,
            "metrics": metrics.dict(),
            "passed": decision.gate_passed,
            "current_state": current_node_id,
            "slots": current_slots.dict(exclude_none=True)
        }

        # 4. State Transition Logic
        target_state = current_state # Default: stay put
        
        logger.info(f"[STATE] current={current_node_id}")
        logger.info(f"[STATE] decision={decision.label}")

        if eval_result.passed:
            # Simple linear transition for now: take first available
            if current_state.transitions:
                next_id = current_state.transitions[0].target_state_id
                if next_id in graph.states:
                    logger.info(f"[STATE] transition={current_node_id} -> {next_id}")
                    logger.info(f"🚀 Transitioning: {current_node_id} -> {next_id}")
                    current_node_id = next_id
                    target_state = graph.states[next_id]
                    state_manager.update_state(session_id, scenario_id, current_node_id)
                    
                    # Notify frontend of transition (optional)
                    yield {"type": "transition", "from": current_state.id, "to": next_id}
            else:
                logger.info("Terminal state reached or no transitions.")
        
        # --- SLOT-BASED SKIP LOGIC ---
        # Check if we landed in a state where we ALREADY know the info
        required_slot = STATE_SLOT_MAP.get(target_state.id)
        if required_slot:
            slot_val = getattr(current_slots, required_slot)
            if slot_val:
                logger.info(f"[MEMORY] Slot '{required_slot}' already filled ({slot_val}). Attempting to skip state {target_state.id}.")
                # Try to skip forward using the first transition (Success path)
                if target_state.transitions:
                     skip_next_id = target_state.transitions[0].target_state_id
                     if skip_next_id in graph.states:
                         logger.info(f"⏩ SKIPPING: {target_state.id} -> {skip_next_id}")
                         # Update state again
                         current_node_id = skip_next_id
                         target_state = graph.states[skip_next_id]
                         state_manager.update_state(session_id, scenario_id, current_node_id)
                         
                         # Notify skip (optional)
                         yield {"type": "transition", "from": "skip", "to": skip_next_id}

        # 5. Generate Response (The "Actor")
        # The actor generates response based on the TARGET state (where we are now)
        logger.info(f"🎭 Generating response for state: {target_state.id}")
        
        # Update context state to target_state for LLM
        llm_context["state"] = target_state.id
        
        # LLM Call Log
        logger.info(f"[LLM_CALL] model=aya:8b state={target_state.id} missing_slots={missing_slots} decision={decision.label}")
        
        async for token in RolePlayAgent.generate_response(
            user_text,
            graph.base_persona,
            target_state,
            history,
            eval_result, # Pass result so actor knows if user failed (GATE_PASSED=False)
            llm_context=llm_context
        ):
            yield token

# Singleton
orchestrator = ScenarioOrchestrator()
