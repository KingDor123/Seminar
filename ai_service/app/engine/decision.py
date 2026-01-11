from typing import List, Optional, Dict
from pydantic import BaseModel
from app.engine.metrics import TurnMetrics
from app.engine.schema import ScenarioState
from app.engine.norms import norm_manager
from app.engine.signals import signal_manager
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
    label: str # "PASS", "HOLD", "BLOCK"
    reasons: List[str] = []

class DecisionEngine:
    
    @staticmethod
    def decide(metrics: TurnMetrics, state: ScenarioState, raw_text: str = "", session_id: str = "unknown") -> DecisionResult:
        logger = logging.getLogger("DecisionEngine")
        reasons = []
        
        # Context Retrieval
        norms = norm_manager.get_norms(session_id)
        
        # --- DECISION TREE START ---
        logger.info("[DECISION_TREE] ──────────────────────────────────────────────")
        logger.info(f"[DECISION_TREE] Session: {session_id}")
        logger.info(f"[DECISION_TREE] State: {state.id}")
        logger.info(f"[DECISION_TREE] Input: \"{raw_text}\"")
        
        # Metrics Snapshot (Logging only)
        logger.info("[DECISION_TREE] Metrics:")
        logger.info(f"  - imperative_social: {metrics.imperative_social} (Raw + No Mitigation)")
        logger.info(f"  - slots_found: {metrics.extracted_slots}")
        
        # Rule Evaluation
        logger.info("[DECISION_TREE] Rules Evaluation:")

        # Rule: Behavioral State Validation (Hard Social Constraint)
        logger.info(f"  [Rule: Social Constraint ({state.id})]")
        expectations = STATE_EXPECTATIONS.get(state.id, {})
        forbidden = expectations.get("forbidden", [])
        
        # Use imperative_social for decision
        is_forbidden_imperative = "imperative" in forbidden and metrics.imperative_social
        
        # Normative Memory Check
        imperative_taught = "imperative" in norms.taught_norms
        
        logger.info(f"    forbidden_behaviors: {forbidden}")
        logger.info(f"    imperative_social: {metrics.imperative_social}")
        logger.info(f"    norm_taught(imperative): {imperative_taught}")
        
        if is_forbidden_imperative:
            if imperative_taught:
                logger.info("    result: PASS (Violation ignored: Norm already taught)")
            else:
                logger.info("    result: BLOCK")
                logger.info("[DECISION_TREE] Final Decision:")
                logger.info("  - label: BLOCK")
                logger.info(f"  - reason: Socially imperative behavior forbidden in {state.id}")
                logger.info("[DECISION_TREE] ─────────────────────────────")
                return DecisionResult(
                    gate_passed=False,
                    label="BLOCK",
                    reasons=[f"Imperative/Commanding language is inappropriate for this stage ({state.id})."]
                )
        else:
            logger.info("    result: PASS")

        # Default Pass
        logger.info("[DECISION_TREE] Final Decision:")
        logger.info("  - label: PASS")
        logger.info("  - reason: No hard violations found")
        logger.info("[DECISION_TREE] ─────────────────────────────")
        
        return DecisionResult(gate_passed=True, label="PASS", reasons=["No hard violations found."])