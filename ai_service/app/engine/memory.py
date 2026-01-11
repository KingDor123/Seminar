from typing import Dict, Optional, Any
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

class ConversationSlots(BaseModel):
    """
    Slot-based memory structure per session.
    Tracks critical information extracted during the conversation.
    """
    amount: Optional[str] = None # Stored as string to handle Hebrew text numbers
    purpose: Optional[str] = None
    income: Optional[str] = None
    # Add other slots as needed for different scenarios

class SlotManager:
    """
    Manages session-based slot memory.
    Currently in-memory, but could be persisted.
    """
    def __init__(self):
        self._slots: Dict[str, ConversationSlots] = {}

    def get_slots(self, session_id: str) -> ConversationSlots:
        if session_id not in self._slots:
            self._slots[session_id] = ConversationSlots()
        return self._slots[session_id]

    def update_slots(self, session_id: str, updates: Dict[str, Any]):
        slots = self.get_slots(session_id)
        updated = False
        for key, value in updates.items():
            if hasattr(slots, key) and value is not None:
                # Only update if value is meaningful (simple check)
                if getattr(slots, key) != value:
                    setattr(slots, key, value)
                    updated = True
        
        if updated:
            logger.info(f"[MEMORY] Updated slots for {session_id}: {updates}")
            self._slots[session_id] = slots

    def clear_slots(self, session_id: str):
        if session_id in self._slots:
            del self._slots[session_id]

# Singleton instance
slot_manager = SlotManager()
