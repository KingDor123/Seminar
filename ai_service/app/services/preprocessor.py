import logging
import asyncio
import re
from typing import Tuple, List

logger = logging.getLogger(__name__)

class PreprocessingError(Exception):
    """Custom exception for preprocessing failures."""
    pass

# --- Module-Level Regex Constants ---
FILLER_WORDS = [
    "um", "uh", "erm", "ah", "umm", "uhh", 
    "you know", "i mean", "sort of", "kind of"
]

# Compiled regex for generic fillers (consumes optional trailing comma/space)
_FILLER_REGEX = re.compile(
    r"\b(" + "|".join(FILLER_WORDS) + r")\b[\s,]*", 
    re.IGNORECASE
)

# Smart Like Patterns
_LIKE_COMMA_REGEX = re.compile(r",\s*like\s*,", re.IGNORECASE)
_LIKE_AFTER_FILLER_REGEX = re.compile(r"\b(um|uh|erm|ah)\s+like\b", re.IGNORECASE)
_LIKE_BEFORE_FILLER_REGEX = re.compile(r"\blike\s+(um|uh|erm|ah)\b", re.IGNORECASE)

# Cleanup Patterns
_WHITESPACE_REGEX = re.compile(r'\s+')
_DOUBLE_COMMA_REGEX = re.compile(r',+')
_LEADING_PUNCT_REGEX = re.compile(r'^[\s,.]+')
_TRAILING_PUNCT_REGEX = re.compile(r'[\s,]+$')
_GLUE_PUNCT_REGEX = re.compile(r'\s+([?.!,])')

class Preprocessor:
    """
    Centralized Pre-processing Service.
    Ensures all inputs (Audio & Text) are normalized to a strict standard
    before reaching AI models (Whisper/LLM).
    """

    @staticmethod
    async def normalize_audio(audio_bytes: bytes) -> bytes:
        """
        Converts arbitrary input audio (WebM, MP4, AAC, etc.) to 
        Standard 16kHz Mono WAV (PCM S16LE) asynchronously.
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
            
            process = await asyncio.create_subprocess_exec(
                *command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            out_bytes, err_bytes = await process.communicate(input=audio_bytes)
            
            if process.returncode != 0:
                err_msg = err_bytes.decode().strip()
                logger.error(f"❌ FFmpeg Error: {err_msg}")
                raise PreprocessingError(f"Audio normalization failed: {err_msg}")
                
            return out_bytes
            
        except PreprocessingError:
            raise
        except Exception as e:
            logger.error(f"❌ Preprocessor Critical Error: {e}")
            raise PreprocessingError(f"Unexpected error during audio normalization: {str(e)}")

    @classmethod
    def process_text(cls, raw_text: str) -> Tuple[str, str, int]:
        """
        Centralized text cleaning pipeline with Smart 'Like' detection 
        and punctuation cleanup.
        """
        if not raw_text:
            return "", "", 0

        # 1. Basic Normalization (Whitespace)
        text = _WHITESPACE_REGEX.sub(' ', raw_text).strip()
        raw_normalized = text
        filler_count = 0

        # 2. Smart Like Removal
        matches = _LIKE_COMMA_REGEX.findall(text)
        filler_count += len(matches)
        text = _LIKE_COMMA_REGEX.sub(" ", text)

        matches = _LIKE_AFTER_FILLER_REGEX.findall(text)
        filler_count += len(matches)
        text = _LIKE_AFTER_FILLER_REGEX.sub(r"\1", text)

        matches = _LIKE_BEFORE_FILLER_REGEX.findall(text)
        filler_count += len(matches)
        text = _LIKE_BEFORE_FILLER_REGEX.sub(r"\1", text)

        # 3. Generic Filler Removal
        fillers = _FILLER_REGEX.findall(text)
        filler_count += len(fillers)
        text = _FILLER_REGEX.sub("", text)

        # 4. Punctuation & Artifact Cleanup
        # Collapse spaces first
        text = _WHITESPACE_REGEX.sub(' ', text)
        
        # Aggressive comma/period cleanup (handles ", ," or ", , ,")
        text = re.sub(r'([,.])(?:\s*[,.])+', r'\1', text)
        
        # Remove leading/trailing artifacts
        text = _LEADING_PUNCT_REGEX.sub('', text)
        text = _TRAILING_PUNCT_REGEX.sub('', text)
        
        # Fix glue punctuation "word ." -> "word."
        text = _GLUE_PUNCT_REGEX.sub(r'\1', text)
        
        # Final trim of any leftover edge characters
        text = text.strip(' ,')

        # 5. Capitalization Fix
        if text and text[0].islower():
            text = text[0].upper() + text[1:]

        return raw_normalized, text, filler_count
