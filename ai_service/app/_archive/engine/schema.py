from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field

# --- Static Configuration (The Graph) ---

class EvaluationCriteria(BaseModel):
    """Rules for the Analyzer to evaluate the user's input."""
    criteria: List[str] = Field(..., description="List of requirements to pass this step")
    # List of allowed signals this state can emit (e.g. ["POSITIVE_RESPONSE", "NEGATIVE_RESPONSE"])
    allowed_signals: List[str] = Field(default_factory=list, description="List of possible signals the analyzer can emit")
    
    pass_condition: str = Field(..., description="Description of what constitutes a successful turn (Legacy/Reference)")
    failure_feedback_guidance: str = Field(..., description="How to guide the user if they fail")

class Transition(BaseModel):
    """A possible move from one state to another."""
    target_state_id: str
    condition: str = Field(..., description="Natural language condition (Legacy/Doc)")
    
    # NEW: Deterministic Routing Key
    condition_id: str = Field(..., description="Strict signal ID required to trigger this transition (e.g. 'CONFIRMED')")
    priority: int = Field(0, description="Higher priority checked first if multiple signals match")

class ScenarioState(BaseModel):
    """A node in the conversation graph."""
    id: str
    description: str = Field(..., description="Internal description of what happens here")
    
    # Instructions for the Role-Play Agent (Persona)
    actor_instruction: str = Field(..., description="System prompt supplement for the character in this state")
    
    # Instructions for the Analyzer
    evaluation: EvaluationCriteria
    
    # Possible Next States
    transitions: List[Transition] = []
    
    # If true, the scenario ends here
    is_terminal: bool = False

class ScenarioGraph(BaseModel):
    """The full definition of a scripted scenario."""
    id: str
    name: str
    base_persona: str = Field(..., description="The immutable core personality")
    goal: str
    states: Dict[str, ScenarioState]
    initial_state_id: str

# --- Runtime Data (The Pipeline) ---

class InteractionFeatures(BaseModel):
    """
    Deterministic features extracted from Input (Text + Audio).
    This is the ONLY input the Analyzer LLM receives about the user's latest turn.
    """
    text: str
    
    # Linguistic Features (Stanza)
    sentiment_score: float = 0.0 # -1.0 to 1.0
    sentiment_label: str = "neutral" # positive, negative, neutral
    pos_tags: List[str] = [] # List of significant parts of speech (e.g. ["VERB", "NOUN"])
    named_entities: List[str] = []
    dependency_root: Optional[str] = None # The root verb/action of the sentence
    
    # Speech/Prosody Features (Whisper/Audio analysis)
    wpm: float = 0.0 # Words per minute
    silence_duration: float = 0.0 # Seconds of silence before speech
    filler_word_count: int = 0
    
    # Metadata
    processing_latency_ms: float = 0.0

class CriterionAssessment(BaseModel):
    """Result of evaluating a single criterion."""
    criterion_text: str
    met: bool
    reasoning: str

class SituationState(BaseModel):
    """
    The STRICT output of the Analyzer, serving as the input for the Persona.
    Diagnostic ONLY. No routing directives (passed, next_node).
    """
    session_id: str
    scenario_id: str
    current_node_id: str # Where the user *was* when they spoke
    
    # Diagnostic Analysis
    criteria_assessments: List[CriterionAssessment]
    
    # NEW: Emitted Signals (Diagnostic tags for routing)
    signals: List[str] = Field(default_factory=list, description="Detected signals (e.g. ['CONFIRMED', 'POLITE'])")
    
    # NEW: Social Appropriateness (Separated from emotional sentiment)
    # Values: "high", "medium", "low"
    social_appropriateness: str = Field("medium", description="Pragmatic appropriateness (politeness/norms), distinct from emotion.")

    general_summary: str = Field(..., description="Summary of user's action and intent")
    
    # Directives for the Persona (Acting cues, not routing)
    guidance_directive: str = Field(..., description="Explicit instruction for the persona")
    suggested_sentiment: str = "neutral"
    
    # Meta
    turn_count: int = 0
    is_terminal: bool = False

class AgentOutput(BaseModel):
    """Legacy/Generic output (kept for compatibility)."""
    passed: bool
    reasoning: str
    feedback: Optional[str] = None
    next_state_id: Optional[str] = None
    sentiment: str = "neutral"
