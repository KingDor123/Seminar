import json
import os
import logging
from typing import Dict, Optional
from pydantic import BaseModel

logger = logging.getLogger("SessionStateManager")

class SessionStateData(BaseModel):
    scenario_id: str
    current_node_id: str
    variables: Dict[str, str] = {} # For future use (e.g. name, collected info)

class SessionStateManager:
    """
    Manages the current state of active sessions.
    Currently uses an in-memory dict backed by a local JSON file.
    """
    
    def __init__(self, persistence_file: str = "session_store.json"):
        self.persistence_file = persistence_file
        self.sessions: Dict[str, SessionStateData] = {}
        self._load()

    def _load(self):
        if os.path.exists(self.persistence_file):
            try:
                with open(self.persistence_file, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                    for sid, data in raw.items():
                        self.sessions[sid] = SessionStateData(**data)
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

    def update_state(self, session_id: str, scenario_id: str, node_id: str):
        sid = str(session_id)
        self.sessions[sid] = SessionStateData(
            scenario_id=scenario_id,
            current_node_id=node_id
        )
        self._save()

    def clear_session(self, session_id: str):
        sid = str(session_id)
        if sid in self.sessions:
            del self.sessions[sid]
            self._save()

# Global Singleton
state_manager = SessionStateManager()
