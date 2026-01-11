import logging
import json
from typing import AsyncGenerator, Dict, Any, List, Optional

from app.engine.schema import ScenarioGraph, AgentOutput
from app.engine.scenarios import get_scenario_graph
from app.engine.state_manager import state_manager
from app.engine.agents import RolePlayAgent
from app.engine.metrics import MetricsEngine
from app.engine.decision import DecisionEngine

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
        
        # Apply Decision Logic
        decision = DecisionEngine.decide(metrics, current_state, raw_text=user_text)
        
        # Convert to AgentOutput for compatibility with RolePlayAgent
        eval_result = AgentOutput(
            passed=decision.gate_passed,
            reasoning="; ".join(decision.reasons),
            feedback=decision.label,
            next_state_id=None, # Decision Engine doesn't select next state ID logic yet, defaults to transition[0] logic below
            sentiment="neutral" # No sentiment analysis per instructions
        )
        
        # Yield metadata about the evaluation
        yield {
            "type": "analysis",
            "sentiment": "neutral", 
            "decision": decision.label,
            "reasons": decision.reasons,
            "metrics": metrics.dict(),
            "passed": decision.gate_passed,
            "current_state": current_node_id
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

        # 5. Generate Response (The "Actor")
        # The actor generates response based on the TARGET state (where we are now)
        logger.info(f"🎭 Generating response for state: {target_state.id}")
        logger.info(f"[LLM] generating response for state={target_state.id} persona=bank_clerk") # Persona is generic here as graph.base_persona is large text
        
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
