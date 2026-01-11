from app.engine.memory import slot_manager

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
            # Clear slots on new session start
            slot_manager.clear_slots(session_id)
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

        # 3. New Pipeline: Metrics -> Rules -> Decision (The "Gate")
        logger.info(f"🧐 Evaluating turn in state: {current_node_id}")
        
        # Calculate Metrics
        metrics = MetricsEngine.compute_metrics(user_text, stt_data or {})
        
        # --- MEMORY UPDATE ---
        if metrics.extracted_slots:
            slot_manager.update_slots(session_id, metrics.extracted_slots)
        
        current_slots = slot_manager.get_slots(session_id)
        
        # --- FRUSTRATION DETECTION ---
        # Heuristic: Repetition > 0.3 OR User updates a slot with same value? (Too complex for now)
        # We focus on Repetition + "Slot already filled" context implies frustration if we ask again.
        is_frustrated = metrics.lemma_repetition_ratio > 0.4
        
        # Apply Decision Logic
        decision = DecisionEngine.decide(metrics, current_state, raw_text=user_text, session_id=str(session_id))
        
        # Prepare Feedback for Agent
        feedback_context = decision.label
        if is_frustrated:
             feedback_context += ". USER SEEMS FRUSTRATED or REPEATING. Acknowledge known info."
        
        # Append Memory Context
        memory_str = f"Known Info: {current_slots.dict(exclude_none=True)}"
        
        # Convert to AgentOutput for compatibility with RolePlayAgent
        eval_result = AgentOutput(
            passed=decision.gate_passed,
            reasoning=f"{'; '.join(decision.reasons)} | {memory_str}",
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
        logger.info(f"[LLM] generating response for state={target_state.id} persona=bank_clerk")
        
        async for token in RolePlayAgent.generate_response(
            user_text,
            graph.base_persona,
            target_state,
            history,
            eval_result # Pass result so actor knows if user failed (GATE_PASSED=False)
        ):
            yield token

# Singleton
orchestrator = ScenarioOrchestrator()
