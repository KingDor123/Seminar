import logging
from typing import List, Dict
from app.engine.schema import ScenarioGraph
from app.engine.scenarios import SCENARIO_REGISTRY

logger = logging.getLogger("GraphValidator")

class GraphValidationError(Exception):
    pass

class ScenarioValidator:
    @staticmethod
    def validate_all():
        errors = []
        for key, graph in SCENARIO_REGISTRY.items():
            try:
                ScenarioValidator.validate_graph(graph)
                logger.info(f"✅ Scenario '{key}' is valid.")
            except GraphValidationError as e:
                errors.append(f"Scenario '{key}': {str(e)}")
        
        if errors:
            raise GraphValidationError("\n".join(errors))
        return True

    @staticmethod
    def validate_graph(graph: ScenarioGraph):
        # 1. Check Initial State
        if graph.initial_state_id not in graph.states:
            raise GraphValidationError(f"Initial state '{graph.initial_state_id}' not found in states.")

        # 2. Check Reachability & Structure
        for state_id, state in graph.states.items():
            # ID Mismatch
            if state.id != state_id:
                raise GraphValidationError(f"State key '{state_id}' does not match internal ID '{state.id}'.")

            # Terminal vs Transitions
            if state.is_terminal and state.transitions:
                logger.warning(f"State '{state_id}' is terminal but has transitions. They will never be used.")
            
            if not state.is_terminal and not state.transitions:
                logger.warning(f"State '{state_id}' is NOT terminal but has NO transitions. It is a dead end.")

            # 3. Validate Transitions & Signals
            seen_conditions = {}
            allowed_signals_set = set(state.evaluation.allowed_signals)
            
            for idx, trans in enumerate(state.transitions):
                # Target Check
                if trans.target_state_id not in graph.states:
                    raise GraphValidationError(
                        f"State '{state_id}' transition #{idx} targets unknown state '{trans.target_state_id}'."
                    )
                
                # Condition ID Check
                if trans.condition_id not in allowed_signals_set:
                    raise GraphValidationError(
                        f"State '{state_id}' transition #{idx} uses condition_id '{trans.condition_id}' "
                        f"which is NOT in allowed_signals: {allowed_signals_set}"
                    )
                
                # Ambiguity Check (Same condition, same priority)
                key = (trans.condition_id, trans.priority)
                if key in seen_conditions:
                     raise GraphValidationError(
                        f"State '{state_id}' has duplicate transition for condition '{trans.condition_id}' "
                        f"at priority {trans.priority}. This creates ambiguity."
                    )
                seen_conditions[key] = True

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        ScenarioValidator.validate_all()
        print("🎉 All scenarios passed validation.")
    except Exception as e:
        print(f"❌ Validation Failed:\n{e}")
        exit(1)