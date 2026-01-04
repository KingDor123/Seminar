import logging
import json
from typing import AsyncGenerator, Dict, Any, List

from app.engine.schema import ScenarioGraph
from app.engine.scenarios import get_scenario_graph
from app.engine.state_manager import state_manager
from app.engine.agents import EvaluatorAgent, RolePlayAgent

logger = logging.getLogger("Orchestrator")

class ScenarioOrchestrator:
    
    async def process_turn(
        self,
        session_id: str,
        scenario_id: str,
        user_text: str,
        history: List[Dict[str, str]]
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

        # 3. Evaluate User Input (The "Coach")
        logger.info(f"🧐 Evaluating turn in state: {current_node_id}")
        eval_result = await EvaluatorAgent.evaluate(user_text, current_state, history)
        
        # Yield metadata about the evaluation
        yield {
            "type": "analysis",
            "sentiment": eval_result.sentiment, 
            "confidence": 1.0 if eval_result.passed else 0.5,
            "detected_intent": "next_step" if eval_result.passed else "retry",
            "social_impact": "progress" if eval_result.passed else "stagnation",
            "reasoning": eval_result.reasoning,
            "passed": eval_result.passed,
            "current_state": current_node_id
        }

        # 4. State Transition Logic
        target_state = current_state # Default: stay put
        
        if eval_result.passed and eval_result.next_state_id:
            next_id = eval_result.next_state_id
            if next_id in graph.states:
                logger.info(f"🚀 Transitioning: {current_node_id} -> {next_id}")
                current_node_id = next_id
                target_state = graph.states[next_id]
                state_manager.update_state(session_id, scenario_id, current_node_id)
                
                # Notify frontend of transition (optional)
                yield {"type": "transition", "from": current_state.id, "to": next_id}
            else:
                logger.warning(f"⚠️ Invalid transition target: {next_id}")

        # 5. Generate Response (The "Actor")
        # The actor generates response based on the TARGET state (where we are now)
        # Exception: If we failed, we are still in the old state, and the prompt includes "Guidance".
        
        logger.info(f"🎭 Generating response for state: {target_state.id}")
        
        async for token in RolePlayAgent.generate_response(
            user_text,
            graph.base_persona,
            target_state,
            history,
            eval_result # Pass result so actor knows if user failed
        ):
            yield token

# Singleton
orchestrator = ScenarioOrchestrator()
