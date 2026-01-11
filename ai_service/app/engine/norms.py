from typing import Dict, Set, List
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

class ConversationNorms(BaseModel):
    """
    Tracks social norms that have already been explained or enforced in this session.
    Used to prevent repetitive lecturing.
    """
    taught_norms: Set[str] = set()

class NormManager:
    """
    Manages session-based norm memory.
    """
    def __init__(self):
        self._norms: Dict[str, ConversationNorms] = {}

    def get_norms(self, session_id: str) -> ConversationNorms:
        if session_id not in self._norms:
            self._norms[session_id] = ConversationNorms()
        return self._norms[session_id]

    def mark_as_taught(self, session_id: str, norm_id: str):
        norms = self.get_norms(session_id)
        if norm_id not in norms.taught_norms:
            norms.taught_norms.add(norm_id)
            logger.info(f"[NORMS] Marked '{norm_id}' as taught for session {session_id}")

    def is_taught(self, session_id: str, norm_id: str) -> bool:
        return norm_id in self.get_norms(session_id).taught_norms

    def clear_norms(self, session_id: str):
        if session_id in self._norms:
            del self._norms[session_id]

# Singleton
norm_manager = NormManager()
