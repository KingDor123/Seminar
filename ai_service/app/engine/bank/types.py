from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class IdDetails(BaseModel):
    full_name: Optional[str] = None
    id_number: Optional[str] = None


class BankSlots(BaseModel):
    amount: Optional[int] = None
    purpose: Optional[str] = None
    income: Optional[int] = None
    confirm_accepted: Optional[bool] = None
    id_details: Optional[IdDetails] = None


class BankStrikes(BaseModel):
    rude_strikes: int = 0
    refusal_strikes: int = 0
    threat_strikes: int = 0
    repay_strikes: int = 0


class BankAnalyzerResult(BaseModel):
    user_text: str
    slots: BankSlots
    signals: List[str] = Field(default_factory=list)
    explanations: Dict[str, str] = Field(default_factory=dict)


class BankDecision(BaseModel):
    next_state: str
    next_action: str
    required_question: Optional[str] = None
    coach_tip: Optional[str] = None
    supportive_line: Optional[str] = None
    warning_text: Optional[str] = None
    clarification_text: Optional[str] = None
    termination_text: Optional[str] = None
    greeting_line: Optional[str] = None
    acknowledgement_line: Optional[str] = None
    options: Optional[List[str]] = None


class BankSessionState(BaseModel):
    current_state_id: str = "start"
    slots: BankSlots = Field(default_factory=BankSlots)
    strikes: BankStrikes = Field(default_factory=BankStrikes)
    turn_count: int = 0
    greeted: bool = False
    last_user_text: Optional[str] = None
    last_state_id: Optional[str] = None
    last_question: Optional[str] = None
    retry_counts: Dict[str, int] = Field(default_factory=dict)
    restart_offered: bool = False
    goodbye_prompted: bool = False
    ineligible_prompted: bool = False
