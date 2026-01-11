from typing import Dict, Any
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

class ConversationSignals(BaseModel):
    """
    Tracks long-term conversation health signals.
    """
    confusion_streak: int = 0
    repeated_unclear_count: int = 0
    repeated_same_state_count: int = 0
    repairs_given: int = 0
    progress_stalled: bool = False
    frustration_detected: bool = False
    last_state: str = ""

class SignalManager:
    """
    Aggregates signals across turns.
    """
    def __init__(self):
        self._signals: Dict[str, ConversationSignals] = {}

    def get_signals(self, session_id: str) -> ConversationSignals:
        if session_id not in self._signals:
            self._signals[session_id] = ConversationSignals()
        return self._signals[session_id]

    def update_signals(self, session_id: str, turn_data: Dict[str, Any]):
        signals = self.get_signals(session_id)
        
        # Unclear Streak
        if turn_data.get("decision_label") == "UNCLEAR":
            signals.confusion_streak += 1
            signals.repeated_unclear_count += 1
        else:
            signals.confusion_streak = 0
            
        # State Repetition
        current_state = turn_data.get("current_state", "")
        if current_state == signals.last_state:
            signals.repeated_same_state_count += 1
        else:
            signals.repeated_same_state_count = 0
            signals.last_state = current_state
            
        # Stalled Progress
        if signals.repeated_same_state_count > 2 or signals.confusion_streak > 2:
            signals.progress_stalled = True
        else:
            signals.progress_stalled = False
            
        # Frustration (merged with turn-level metric)
        if turn_data.get("turn_frustration", False):
            signals.frustration_detected = True
            
        # Repairs
        if turn_data.get("repair_given", False):
            signals.repairs_given += 1
            
        logger.info(f"[SIGNALS] Session {session_id}: confusion={signals.confusion_streak}, stalled={signals.progress_stalled}")

    def clear_signals(self, session_id: str):
        if session_id in self._signals:
            del self._signals[session_id]

# Singleton
signal_manager = SignalManager()
