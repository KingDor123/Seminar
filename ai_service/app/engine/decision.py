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
    
            logger.info(f"  - imperative_raw: {metrics.imperative_raw}")
    
            logger.info(f"  - mitigation: {metrics.mitigation_present}")
    
            logger.info(f"  - imperative_social: {metrics.imperative_social} (Raw + No Mitigation)")
    
            logger.info(f"  - directness_score: {metrics.directness_score}")
    
            logger.info(f"  - starts_with_verb: {metrics.starts_with_verb}")
    
            logger.info(f"  - fragmentation: {metrics.sentence_fragmentation}")
    
            logger.info(f"  - repetition: {metrics.lemma_repetition_ratio}")
    
            logger.info(f"  - slots_found: {metrics.extracted_slots}")
    
            
    
            # Rule Evaluation
    
            logger.info("[DECISION_TREE] Rules Evaluation:")
    
    
    
            # Rule 1: Clarity Check
    
            logger.info(f"  [Rule: Clarity]")
    
            logger.info(f"    condition: sentence_fragmentation ({metrics.sentence_fragmentation})")
    
            if metrics.sentence_fragmentation:
    
                logger.info("    result: FAIL")
    
                logger.info("[DECISION_TREE] Final Decision:")
    
                logger.info("  - label: UNCLEAR")
    
                logger.info("  - reason: Sentence fragment detected")
    
                logger.info("[DECISION_TREE] ─────────────────────────────")
    
                return DecisionResult(gate_passed=False, label="UNCLEAR", reasons=["Sentence fragment detected."])
    
            else:
    
                logger.info("    result: PASS")
    
    
    
            # Rule 2: Behavioral State Validation
    
            logger.info(f"  [Rule: State Expectations ({state.id})]")
    
            expectations = STATE_EXPECTATIONS.get(state.id, {})
    
            forbidden = expectations.get("forbidden", [])
    
            
    
            # Use imperative_social for decision
    
            is_forbidden_imperative = "imperative" in forbidden and metrics.imperative_social
    
            
    
            logger.info(f"    forbidden_behaviors: {forbidden}")
    
            logger.info(f"    imperative_social: {metrics.imperative_social}")
    
            
    
            if is_forbidden_imperative:
    
                logger.info("    result: FAIL")
    
                logger.info("[DECISION_TREE] Final Decision:")
    
                logger.info("  - label: INAPPROPRIATE_FOR_CONTEXT")
    
                logger.info(f"  - reason: Socially imperative behavior forbidden in {state.id}")
    
                logger.info("[DECISION_TREE] ─────────────────────────────")
    
                return DecisionResult(
    
                    gate_passed=False,
    
                    label="INAPPROPRIATE_FOR_CONTEXT",
    
                    reasons=[f"Imperative/Commanding language is inappropriate for this stage ({state.id})."]
    
                )
    
            else:
    
                logger.info("    result: PASS")
    
    
    
            # Rule 3: Global Politeness (Fallback)
    
            # If imperative_social is true (Imperative AND No Mitigation), it's generally rude unless context allows.
    
            # We enforce it if not explicitly handled above.
    
            logger.info(f"  [Rule: Global Politeness]")
    
            if metrics.imperative_social:
    
                 logger.info("    result: FAIL (Imperative without mitigation)")
    
                 logger.info("[DECISION_TREE] Final Decision:")
    
                 logger.info("  - label: INAPPROPRIATE_FOR_CONTEXT")
    
                 logger.info("  - reason: Global politeness check")
    
                 logger.info("[DECISION_TREE] ─────────────────────────────")
    
                 return DecisionResult(
    
                    gate_passed=False,
    
                    label="INAPPROPRIATE_FOR_CONTEXT",
    
                    reasons=["Imperative language used without mitigation."]
    
                )
    
            else:
    
                logger.info("    result: PASS")
    
                
    
            # Gate Passed
    
            logger.info("[DECISION_TREE] Final Decision:")
    
            logger.info("  - label: GATE_PASSED")
    
            logger.info("  - reason: Input is clear and appropriate")
    
            logger.info("[DECISION_TREE] ─────────────────────────────")
    
            
    
            return DecisionResult(gate_passed=True, label="GATE_PASSED", reasons=["Input is clear and appropriate."])
    
    
