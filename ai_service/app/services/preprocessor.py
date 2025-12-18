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

    # Expanded list of filler words for robust filtering
    FILLER_WORDS = [
        "um", "uh", "erm", "ah", "umm", "uhh", 
        "like", "you know", "i mean", "sort of", "kind of"
    ]
    
    # Compiled regex for performance
    _FILLER_REGEX = re.compile(
        r"\b(" + "|".join(FILLER_WORDS) + r")\b", 
        re.IGNORECASE
    )

    @staticmethod
    def normalize_audio(audio_bytes: bytes) -> bytes:
        """
        Converts arbitrary input audio (WebM, MP4, AAC, etc.) to 
        Standard 16kHz Mono WAV (PCM S16LE).
        
        Why?
        1. Whisper expects 16kHz mono. Providing it directly skips internal resampling.
        2. WebM/Ogg containers from browsers can have variable frame rates.
        3. Standardizes loudness/gain implicitly via clean decoding (further normalization can be added).
        
        Returns:
            bytes: The normalized WAV file content.
        """
        if not audio_bytes:
            return b""

        try:
            # ffmpeg command: Pipe Input -> Convert -> Pipe Output
            command = [
                "ffmpeg",
                "-hide_banner", "-loglevel", "error", # Quiet mode
                "-i", "pipe:0",           # Input from stdin
                "-vn",                    # Discard video
                "-ac", "1",               # Audio Channels: 1 (Mono)
                "-ar", "16000",           # Sample Rate: 16000Hz (Whisper Native)
                "-f", "wav",              # Output Container: WAV
                "pipe:1"                  # Output to stdout
            ]
            
            # Execute FFmpeg as a subprocess
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            out_bytes, err_bytes = process.communicate(input=audio_bytes)
            
            if process.returncode != 0:
                logger.warning(f"⚠️ Audio normalization warning (FFmpeg): {err_bytes.decode().strip()}")
                # If conversion fails, fallback to original bytes (Whisper might still handle it)
                return audio_bytes
                
            return out_bytes
            
        except Exception as e:
            logger.error(f"❌ Preprocessor Critical Error: {e}")
            return audio_bytes

    @classmethod
    def process_text(cls, raw_text: str) -> Tuple[str, str, int]:
        """
        Centralized text cleaning pipeline.
        
        Returns:
            (raw_normalized, clean_text, filler_count)
        """
        if not raw_text:
            return "", "", 0

        # 1. Basic Normalization (Whitespace)
        raw_normalized = re.sub(r'\s+', ' ', raw_text).strip()
        
        # 2. Filler Detection
        fillers = cls._FILLER_REGEX.findall(raw_normalized)
        filler_count = len(fillers)
        
        # 3. Filler Removal
        clean_text = cls._FILLER_REGEX.sub("", raw_normalized)
        
        # 4. Clean up artifacts from removal (double spaces)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        # 5. Punctuation Normalization (fix "word ." -> "word.")
        clean_text = re.sub(r'\s+([?.!,])', r'\1', clean_text)

        return raw_normalized, clean_text, filler_count
