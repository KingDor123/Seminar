from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field

class EvaluationCriteria(BaseModel):
    """Rules for the Coach to evaluate the user's input."""
    criteria: List[str] = Field(..., description="List of requirements to pass this step")
    pass_condition: str = Field(..., description="Description of what constitutes a successful turn")
    failure_feedback_guidance: str = Field(..., description="How to guide the user if they fail")

class Transition(BaseModel):
    """A possible move from one state to another."""
    target_state_id: str
    condition: str = Field(..., description="Natural language condition for this transition (e.g. 'User greeted back')")

class ScenarioState(BaseModel):
    """A node in the conversation graph."""
    id: str
    description: str = Field(..., description="Internal description of what happens here")
    
    # Instructions for the Role-Play Agent
    actor_instruction: str = Field(..., description="System prompt supplement for the character in this state")
    
    # Instructions for the Coach/Evaluator
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

class AgentOutput(BaseModel):
    """Structured output from the Evaluator Agent."""
    passed: bool
    reasoning: str
    feedback: Optional[str] = None
    next_state_id: Optional[str] = None
    sentiment: str = "neutral"
