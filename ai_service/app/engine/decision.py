from typing import List, Optional
from pydantic import BaseModel
from app.engine.metrics import TurnMetrics
from app.engine.schema import ScenarioState

class DecisionResult(BaseModel):
    gate_passed: bool
    label: str # "UNCLEAR", "INAPPROPRIATE_FOR_CONTEXT", "GATE_PASSED"
    reasons: List[str] = []

class DecisionEngine:
    
    @staticmethod
    def decide(metrics: TurnMetrics, state: ScenarioState) -> DecisionResult:
        reasons = []
        
        # 1. Clarity Check
        # If fragmented (no verb, short) -> Unclear
        if metrics.sentence_fragmentation:
            return DecisionResult(
                gate_passed=False, 
                label="UNCLEAR", 
                reasons=["Sentence fragment detected (missing verb, too short)."]
            )
        
        # 2. Situational Appropriateness
        is_appropriate = True
        
        # Rule: Imperative + No Mitigation -> Inappropriate (Politeness check)
        if metrics.imperative_form and not metrics.mitigation_present:
            is_appropriate = False
            reasons.append("Imperative language used without mitigation (politeness).")
            
        # Rule: Role Mismatch (Placeholder - requires knowing user role constraint)
        # For now, we assume implicit customer role. 
        # If we had explicit 'user_role' in state, we would check it.
        
        if not is_appropriate:
            return DecisionResult(
                gate_passed=False,
                label="INAPPROPRIATE_FOR_CONTEXT",
                reasons=reasons
            )
            
        # 3. Gate Passed
        # Note: We do NOT evaluate if they 'passed' the scenario goal here.
        # The prompt says: "Decision Engine (Gate Only)... Do NOT evaluate 'quality'".
        # Wait, if we don't evaluate quality/goal, how do we move to the next state?
        # The Target Architecture diagram shows:
        # [Decision Engine] -> [Orchestrator]
        # And "Orchestrator reacts ONLY to: UNCLEAR, INAPPROPRIATE, GATE_PASSED".
        # If GATE_PASSED, does the Orchestrator then move state?
        # The prompt says: "Replace any LLM-based pass/fail with Decision Engine output".
        # This implies the Decision Engine MUST determine if the step is passed.
        # BUT the prompt also says: "Do NOT evaluate 'quality'".
        # AND "Do NOT delegate decisions to LLM".
        
        # Clarification from prompt: "Decision Engine (Rule-Based)... Rules: ... Else -> GATE_PASSED".
        # This implies GATE_PASSED just means "You made a valid, appropriate turn".
        # It does NOT mean "You achieved the goal".
        # However, the previous `EvaluatorAgent` (LLM) decided `passed=True/False` based on `criteria`.
        # If I remove that, who decides if we move to the next node?
        
        # Re-reading Prompt:
        # "6. Orchestrator Integration... Replace any LLM-based pass/fail with Decision Engine output... Orchestrator reacts ONLY to: UNCLEAR, INAPPROPRIATE, GATE_PASSED".
        # This suggests a strict gating mechanism. 
        # If "GATE_PASSED", maybe we assume the user *succeeded* in the interaction?
        # OR maybe we just stay in the same state unless logic says move?
        # The prompt says: "Rules module... is_appropriate".
        # It does NOT mention checking `criteria` (like "User must mention interest rate").
        # If the Decision Engine is purely rule-based (politeness, clarity), it cannot semantic check "Did they ask for a loan?".
        
        # CONTRADICTION CHECK:
        # "Replace any LLM-based pass/fail" vs "Do NOT delegate decisions to LLM" vs "Decision Engine is Rule-Based".
        # If I cannot use LLM to check semantics ("Did he ask about X?"), and Rules are only Politeness/Clarity,
        # then we lose the ability to check semantic goals.
        # UNLESS "Situational Appropriateness" implies checking specific keywords defined in the state?
        # The prompt "Target Architecture" doesn't explicitly show a "Goal Checker".
        # BUT, "Orchestrator Integration" says "Replace... with Decision Engine output".
        
        # INTERPRETATION:
        # The user wants a strict behavioral pipeline. 
        # For this refactor, "GATE_PASSED" likely translates to "Valid Turn, proceed".
        # But if the scenario requires specific semantic milestones, we might be dropping that feature if we remove the LLM Evaluator completely.
        # However, the instruction "Do NOT remove or break... ScenarioState / Orchestrator logic" implies the conversation flow must work.
        # If I strictly follow "No LLM for decision", I can't check complex semantic goals.
        # BUT, "Situational Appropriateness Rules" are the ONLY decision logic mentioned.
        # I will strictly follow the "Decision Engine" rules provided:
        # Rules: Clarity -> UNCLEAR, Appropriateness -> INAPPROPRIATE, Else -> GATE_PASSED.
        
        # What about state transition?
        # If GATE_PASSED, the Orchestrator usually needs to know "Did we finish this state?".
        # If I can't check that, the user is stuck forever.
        # MAYBE "GATE_PASSED" implies "You pass this state".
        # Or maybe the Orchestrator keeps the old LLM for "Goal Checking" but uses Decision Engine for "Gating"?
        # Prompt: "Replace any LLM-based pass/fail with Decision Engine output".
        # This is strong. It suggests the DE determines the outcome.
        # This means if I speak clearly and politely, I PASS the state.
        # This might be the intended behavior for this specific "SoftSkill AI Trainer" refactor (focus on form over content?).
        # I will proceed with this assumption: GATE_PASSED = Success (Transition).
        
        return DecisionResult(gate_passed=True, label="GATE_PASSED", reasons=["Input is clear and appropriate."])
