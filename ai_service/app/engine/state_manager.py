import json
import os
import logging
from typing import Dict, Optional
from pydantic import BaseModel
from app.engine.bank.types import BankSessionState

logger = logging.getLogger("SessionStateManager")
DEBUG_LOGS = os.getenv("BANK_DEBUG_LOGS", "false").lower() in ("1", "true", "yes")

class SessionStateData(BaseModel):
    scenario_id: str
    current_node_id: str
    variables: Dict[str, str] = {} # For future use (e.g. name, collected info)
    bank_state: Optional[BankSessionState] = None

class SessionStateManager:
    """
    Manages the current state of active sessions.
    Currently uses an in-memory dict backed by a local JSON file.
    """
    
    def __init__(self, persistence_file: str = "session_store.json"):
        self.persistence_file = persistence_file
        self.sessions: Dict[str, SessionStateData] = {}
        self._loaded_session_ids: set[str] = set()
        self._load()

    def _load(self):
        if os.path.exists(self.persistence_file):
            try:
                with open(self.persistence_file, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                    for sid, data in raw.items():
                        self.sessions[sid] = SessionStateData(**data)
                        self._loaded_session_ids.add(str(sid))
                logger.info(f"Loaded {len(self.sessions)} sessions from disk.")
            except Exception as e:
                logger.error(f"Failed to load session store: {e}")

    def _save(self):
        try:
            data = {k: v.dict() for k, v in self.sessions.items()}
            with open(self.persistence_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save session store: {e}")

    def get_state(self, session_id: str) -> Optional[SessionStateData]:
        return self.sessions.get(str(session_id))

    def was_loaded_from_disk(self, session_id: str) -> bool:
        return str(session_id) in self._loaded_session_ids

    def update_state(self, session_id: str, scenario_id: str, node_id: str):
        sid = str(session_id)
        existing = self.sessions.get(sid)
        self.sessions[sid] = SessionStateData(
            scenario_id=scenario_id,
            current_node_id=node_id,
            bank_state=existing.bank_state if existing else None,
        )
        self._save()

    def get_or_create_bank_state(self, session_id: str, scenario_id: str) -> BankSessionState:
        sid = str(session_id)
        existing = self.sessions.get(sid)
        if existing and existing.bank_state and existing.scenario_id == scenario_id:
            return existing.bank_state
        bank_state = BankSessionState()
        self.sessions[sid] = SessionStateData(
            scenario_id=scenario_id,
            current_node_id=bank_state.current_state_id,
            bank_state=bank_state,
        )
        self._save()
        return bank_state

    def update_bank_state(self, session_id: str, scenario_id: str, bank_state: BankSessionState):
        sid = str(session_id)
        self.sessions[sid] = SessionStateData(
            scenario_id=scenario_id,
            current_node_id=bank_state.current_state_id,
            bank_state=bank_state,
        )
        self._save()

    def reset_bank_state(self, session_id: str, scenario_id: str, reason: str = "reset") -> BankSessionState:
        sid = str(session_id)
        bank_state = BankSessionState()
        self.sessions[sid] = SessionStateData(
            scenario_id=scenario_id,
            current_node_id=bank_state.current_state_id,
            bank_state=bank_state,
        )
        self._save()
        if DEBUG_LOGS:
            logger.info("[BANK][DEBUG] Reset bank state session=%s reason=%s", sid, reason)
        return bank_state

    def clear_session(self, session_id: str):
        sid = str(session_id)
        if sid in self.sessions:
            del self.sessions[sid]
            self._save()

# Global Singleton
state_manager = SessionStateManager()
