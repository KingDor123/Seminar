from typing import Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime

class MessageRead(BaseModel):
    id: int
    role: str
    content: str
    sentiment: Optional[str] = None
    created_at: Optional[datetime] = None

class SessionRead(BaseModel):
    id: int
    scenario_id: str
    start_time: datetime
    message_count: int
    last_sentiment: Optional[str] = None

class AyaAnalysis(BaseModel):
    sentiment: Literal["positive", "negative", "neutral"]
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    detected_intent: str
    social_impact: str

    class Config:
        extra = "forbid"
