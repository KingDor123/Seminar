from typing import Optional
from pydantic import BaseModel
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
