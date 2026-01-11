from typing import List, Optional, Dict
from pydantic import BaseModel
from app.engine.metrics import TurnMetrics
from app.engine.schema import ScenarioState
import logging

# Behavioral Constraints Mapping
# Defines forbidden behaviors per state ID (heuristic-based)
STATE_EXPECTATIONS: Dict[str, Dict[str, List[str]]] = {
  "start": {
    "forbidden": ["imperative"],
  },
  "ask_amount": {
    "forbidden": ["imperative"],
  },
  "ask_purpose": {
    "forbidden": ["imperative"],
  },
  "ask_income": {
    "forbidden": ["imperative"],
  }
}

class DecisionResult(BaseModel):
    gate_passed: bool
    label: str # "UNCLEAR", "INAPPROPRIATE_FOR_CONTEXT", "GATE_PASSED"
    reasons: List[str] = []

class DecisionEngine:
    
    @staticmethod
    def decide(metrics: TurnMetrics, state: ScenarioState, raw_text: str = "", session_id: str = "unknown") -> DecisionResult:
        logger = logging.getLogger("DecisionEngine")
        reasons = []
        
        # --- DECISION TREE START ---
        logger.info("[DECISION_TREE] ──────────────────────────────────────────────")
        logger.info(f"[DECISION_TREE] Session: {session_id}")
        logger.info(f"[DECISION_TREE] State: {state.id}")
        logger.info(f"[DECISION_TREE] Input: \"{raw_text}\"")
        
        # Metrics Snapshot
        logger.info("[DECISION_TREE] Metrics:")
        logger.info(f"  - greeting: {metrics.greeting_present}")
        logger.info(f"  - imperative: {metrics.imperative_form} (Stanza/Regex detected)")
        logger.info(f"  - mitigation: {metrics.mitigation_present}")
        logger.info(f"  - starts_with_verb: {metrics.starts_with_verb}")
        logger.info(f"  - fragmentation: {metrics.sentence_fragmentation}")
        logger.info(f"  - repetition: {metrics.lemma_repetition_ratio}")
        logger.info(f"  - avg_dep_depth: {metrics.avg_dependency_depth}")
        
        # Rule Evaluation
        logger.info("[DECISION_TREE] Rules Evaluation:")

        # Rule 1: Clarity Check
        # ... (rest of logic)
        logger.info(f"  Conditions:")
        logger.info(f"    sentence_fragmentation: {metrics.sentence_fragmentation} -> {'FAIL' if metrics.sentence_fragmentation else 'PASS'}")
        
        if metrics.sentence_fragmentation:
            logger.info("  Result: FAIL")
            logger.info("[DECISION_TREE] Final Decision:")
            logger.info("  - label: UNCLEAR")
            logger.info("  - reason: Sentence fragment detected")
            logger.info("[DECISION_TREE] ─────────────────────────────")
            
            # Legacy Logs
            logger.info("[DECISION] rule=sentence_fragmentation -> FAIL")
            logger.info("[DECISION] label=UNCLEAR")
            
            return DecisionResult(
                gate_passed=False, 
                label="UNCLEAR", 
                reasons=["Sentence fragment detected (missing verb, too short)."]
            )
        else:
            logger.info("  Result: PASS")

        # Rule 2: Behavioral State Validation
        logger.info(f"[DECISION_TREE] Rule: State-Specific Behavioral Expectations ({state.id})")
        
        expectations = STATE_EXPECTATIONS.get(state.id, {})
        forbidden_behaviors = expectations.get("forbidden", [])
        
        is_imperative = (metrics.imperative_form or metrics.starts_with_verb) and not metrics.mitigation_present
        
        logger.info("  Conditions:")
        # Log state condition
        has_forbidden_imperative = "imperative" in forbidden_behaviors
        logger.info(f"    state == {state.id} (forbidden: {forbidden_behaviors}) -> {'CHECK' if has_forbidden_imperative else 'SKIP'}")
        
        if has_forbidden_imperative:
            logger.info(f"    is_imperative: {is_imperative} -> {'FAIL' if is_imperative else 'PASS'}")
            if is_imperative:
                logger.info("  Result: FAIL")
                logger.info("[DECISION_TREE] Final Decision:")
                logger.info("  - label: INAPPROPRIATE_FOR_CONTEXT")
                logger.info(f"  - reason: Imperative forbidden in {state.id}")
                logger.info("[DECISION_TREE] ─────────────────────────────")

                # Legacy Logs
                logger.info(f"[DECISION] rule=forbidden_imperative_in_state({state.id}) -> FAIL")
                logger.info("[DECISION] label=INAPPROPRIATE_FOR_CONTEXT")
                
                return DecisionResult(
                    gate_passed=False,
                    label="INAPPROPRIATE_FOR_CONTEXT",
                    reasons=["Behavioral Violation: Imperative/Commanding language is inappropriate for this stage of the conversation (State: " + state.id + ")."]
                )
            else:
                logger.info("  Result: PASS")
        else:
            logger.info("  Result: PASS (No specific constraints)")

        # Rule 3: Global Politeness
        logger.info("[DECISION_TREE] Rule: Global Politeness (Imperative without Mitigation)")
        logger.info("  Conditions:")
        logger.info(f"    is_imperative: {is_imperative} -> {'FAIL' if is_imperative else 'PASS'}")
        
        if is_imperative:
             logger.info("  Result: FAIL")
             reasons.append("Imperative language used without mitigation (politeness).")
             
             logger.info("[DECISION_TREE] Final Decision:")
             logger.info("  - label: INAPPROPRIATE_FOR_CONTEXT")
             logger.info("  - reason: Global imperative check")
             logger.info("[DECISION_TREE] ─────────────────────────────")

             # Legacy Logs
             logger.info("[DECISION] rule=global_imperative_without_mitigation -> FAIL")
             logger.info("[DECISION] label=INAPPROPRIATE_FOR_CONTEXT")
             
             return DecisionResult(
                gate_passed=False,
                label="INAPPROPRIATE_FOR_CONTEXT",
                reasons=reasons
            )
        else:
            logger.info("  Result: PASS")
            
        # Gate Passed
        logger.info("[DECISION_TREE] Final Decision:")
        logger.info("  - label: GATE_PASSED")
        logger.info("  - reason: Input is clear and appropriate")
        logger.info("[DECISION_TREE] ─────────────────────────────")

        # Legacy Logs
        logger.info("[DECISION] all_rules_passed")
        logger.info("[DECISION] label=GATE_PASSED")
        
        return DecisionResult(gate_passed=True, label="GATE_PASSED", reasons=["Input is clear and appropriate."])
