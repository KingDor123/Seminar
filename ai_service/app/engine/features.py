import logging
import time
import os
from typing import Dict, Any
from pydantic import BaseModel

logger = logging.getLogger("FeatureExtractor")

# 3. Add a single DEBUG_MODE flag (environment variable or constant)
# Default: true
DEBUG_MODE = os.getenv("DEBUG_MODE", "true").lower() == "true"

class InteractionFeatures(BaseModel):
    text: str
    wpm: float = 0.0
    silence_duration: float = 0.0
    filler_word_count: int = 0
    word_count: int = 0
    processing_latency_ms: float = 0.0

class FeatureExtractor:
    @classmethod
    def extract(cls, text: str, audio_meta: Dict[str, Any] = {}) -> InteractionFeatures:
        """
        Deterministic extraction of features from text and audio metadata.
        NO LLM calls here.
        """
        start_time = time.time()
        
        # Log raw user text (Phase 1)
        if DEBUG_MODE:
            logger.info(f"[FEATURES] Raw User Text: '{text}'")

        features = InteractionFeatures(
            text=text,
            wpm=audio_meta.get("wpm", 0.0),
            silence_duration=audio_meta.get("silence_duration", 0.0),
            filler_word_count=audio_meta.get("filler_count", 0)
        )

        tokens = text.strip().split()
        features.word_count = len(tokens)
        features.processing_latency_ms = (time.time() - start_time) * 1000
        
        # Log extracted features (Phase 1)
        if DEBUG_MODE:
            logger.info(
                f"[FEATURES] Extracted: WPM={features.wpm}, Pauses={features.silence_duration}s, "
                f"Fillers={features.filler_word_count}, Words={features.word_count}"
            )
            
        return features
