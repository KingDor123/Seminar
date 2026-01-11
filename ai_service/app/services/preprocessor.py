import re
import unicodedata
import logging

logger = logging.getLogger(__name__)

class Preprocessor:
    """
    Handles raw text and audio preprocessing.
    Restored to fix missing dependency in STT pipeline.
    """
    
    # Common Hebrew filler words for basic counting
    FILLERS = {"כאילו", "אממ", "אה", "כזה", "בקיצור", "נו"}

    @staticmethod
    async def normalize_audio(audio_bytes: bytes) -> bytes:
        """
        Ensures audio is in the correct format (16kHz WAV).
        Currently a pass-through to avoid external dependency breakage (ffmpeg).
        """
        # TODO: Implement actual ffmpeg normalization if needed.
        # faster-whisper handles most formats internally.
        return audio_bytes

    @staticmethod
    def process_text(raw_text: str):
        """
        Normalizes text for analysis.
        Returns: (raw_text, analysis_text, filler_count)
        """
        if not raw_text:
            return "", "", 0

        # 1. Unicode Normalization (NFC)
        text = unicodedata.normalize("NFC", raw_text)
        
        # 2. Remove non-printable characters (keep newlines/spaces)
        text = "".join(ch for ch in text if unicodedata.category(ch)[0] != "C" or ch in "\n\r\t")
        
        # 3. Basic whitespace cleanup
        analysis_text = " ".join(text.split())

        # 4. Count fillers (simple token match)
        tokens = analysis_text.split()
        filler_count = sum(1 for t in tokens if t in Preprocessor.FILLERS)

        # Note: We do NOT remove fillers from analysis_text per strict "Text Contract".
        # analysis_text is minimal normalization.

        return raw_text, analysis_text, filler_count
