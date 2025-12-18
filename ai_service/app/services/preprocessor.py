import logging
import subprocess
import re
from typing import Tuple, List

logger = logging.getLogger(__name__)

class Preprocessor:
    """
    Centralized Pre-processing Service.
    Ensures all inputs (Audio & Text) are normalized to a strict standard
    before reaching AI models (Whisper/LLM).
    """

    # 1. Generic Filler Words (REMOVED 'like' to handle it contextually)
    FILLER_WORDS = [
        "um", "uh", "erm", "ah", "umm", "uhh", 
        "you know", "i mean", "sort of", "kind of"
    ]
    
    # Compiled regex for generic fillers
    _FILLER_REGEX = re.compile(
        r"\b(" + "|".join(FILLER_WORDS) + r")\b", 
        re.IGNORECASE
    )

    # 2. Smart Like Patterns
    # Case A: Surrounded by commas (e.g., "It was, like, huge")
    _LIKE_COMMA_REGEX = re.compile(r",\s*like\s*,", re.IGNORECASE)
    
    # Case B: Preceded by specific fillers (e.g., "um like") - Keep the preceding filler
    _LIKE_AFTER_FILLER_REGEX = re.compile(r"\b(um|uh|erm|ah)\s+like\b", re.IGNORECASE)
    
    # Case C: Followed by specific fillers (e.g., "like um") - Keep the following filler
    _LIKE_BEFORE_FILLER_REGEX = re.compile(r"\blike\s+(um|uh|erm|ah)\b", re.IGNORECASE)

    @staticmethod
    def normalize_audio(audio_bytes: bytes) -> bytes:
        """
        Converts arbitrary input audio (WebM, MP4, AAC, etc.) to 
        Standard 16kHz Mono WAV (PCM S16LE).
        """
        if not audio_bytes:
            return b""

        try:
            command = [
                "ffmpeg",
                "-hide_banner", "-loglevel", "error",
                "-i", "pipe:0",
                "-vn",
                "-ac", "1",
                "-ar", "16000",
                "-f", "wav",
                "pipe:1"
            ]
            
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            out_bytes, err_bytes = process.communicate(input=audio_bytes)
            
            if process.returncode != 0:
                logger.warning(f"⚠️ Audio normalization warning (FFmpeg): {err_bytes.decode().strip()}")
                return audio_bytes
                
            return out_bytes
            
        except Exception as e:
            logger.error(f"❌ Preprocessor Critical Error: {e}")
            return audio_bytes

    @classmethod
    def process_text(cls, raw_text: str) -> Tuple[str, str, int]:
        """
        Centralized text cleaning pipeline with Smart 'Like' detection 
        and punctuation cleanup.
        
        Returns:
            (raw_normalized, clean_text, filler_count)
        """
        if not raw_text:
            return "", "", 0

        # 1. Basic Normalization (Whitespace)
        text = re.sub(r'\s+', ' ', raw_text).strip()
        raw_normalized = text
        filler_count = 0

        # 2. Smart Like Removal
        # Handle ", like," -> replace with space (removes the clause)
        matches = cls._LIKE_COMMA_REGEX.findall(text)
        filler_count += len(matches)
        text = cls._LIKE_COMMA_REGEX.sub(" ", text)

        # Handle "um like" -> replace with "um" (remove like)
        matches = cls._LIKE_AFTER_FILLER_REGEX.findall(text)
        filler_count += len(matches)
        text = cls._LIKE_AFTER_FILLER_REGEX.sub(r"\1", text) # Keep the filler (\1)

        # Handle "like um" -> replace with "um" (remove like)
        matches = cls._LIKE_BEFORE_FILLER_REGEX.findall(text)
        filler_count += len(matches)
        text = cls._LIKE_BEFORE_FILLER_REGEX.sub(r"\1", text) # Keep the filler (\1)

        # 3. Generic Filler Removal
        fillers = cls._FILLER_REGEX.findall(text)
        filler_count += len(fillers)
        text = cls._FILLER_REGEX.sub("", text)

        # 4. Punctuation & Artifact Cleanup
        # Remove double spaces created by removals
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Replace double commas ",," with ","
        text = re.sub(r',+', ',', text)
        
        # Remove leading punctuation (comma/period/space at start)
        # e.g. "Um, hello" -> ", hello" -> "hello"
        text = re.sub(r'^[\s,.]+', '', text)
        
        # Remove trailing punctuation artifacts (orphan commas)
        text = re.sub(r'[\s,]+$', '', text)
        
        # Fix glue punctuation "word ." -> "word."
        text = re.sub(r'\s+([?.!,])', r'\1', text)

        # 5. Capitalization Fix (Optional but good for quality)
        if text and text[0].islower():
            text = text[0].upper() + text[1:]

        return raw_normalized, text, filler_count