import logging
from faster_whisper import WhisperModel
import numpy as np
from app.core.config import settings

logger = logging.getLogger(__name__)

class STTService:
    """
    Speech-to-Text (STT) Service using Faster-Whisper.
    
    Optimized for running locally on CPU (or GPU if configured).
    """

    def __init__(self):
        logger.info(f"Initializing Whisper Model: {settings.WHISPER_MODEL_SIZE} "
                    f"on {settings.WHISPER_DEVICE} ({settings.WHISPER_COMPUTE_TYPE})")
        try:
            self.model = WhisperModel(
                settings.WHISPER_MODEL_SIZE, 
                device=settings.WHISPER_DEVICE, 
                compute_type=settings.WHISPER_COMPUTE_TYPE
            )
            logger.info("✅ Whisper Model loaded successfully.")
        except Exception as e:
            logger.critical(f"❌ Failed to load Whisper model: {e}")
            raise e

    def transcribe(self, audio_bytes: bytes) -> str:
        """
        Transcribes raw PCM audio bytes to text.
        
        Args:
            audio_bytes: Raw audio data (expected to be Float32 little-endian).
            
        Returns:
            str: The transcribed text.
        """
        try:
            # Convert raw bytes to numpy array (Float32) as expected by faster-whisper
            audio_array = np.frombuffer(audio_bytes, dtype=np.float32)
            
            return self._run_transcription(audio_array)
        except Exception as e:
            logger.error(f"Transcription error (bytes): {e}")
            return ""

    def transcribe_numpy(self, audio_array: np.ndarray) -> str:
        """
        Transcribes directly from a numpy array.
        
        Args:
            audio_array: Numpy array containing audio data.
            
        Returns:
            str: The transcribed text.
        """
        return self._run_transcription(audio_array)

    def _run_transcription(self, audio_array: np.ndarray) -> str:
        """
        Internal helper to run the transcription on the model.
        """
        try:
            # beam_size=5 is a standard trade-off for better accuracy.
            segments, info = self.model.transcribe(audio_array, beam_size=5)

            # Combine all segments into a single string
            text = " ".join([segment.text for segment in segments]).strip()
            
            if text:
                logger.info(f"🗣️  Transcribed: '{text}' (Conf: {info.language_probability:.2f})")
            
            return text
        except Exception as e:
            logger.error(f"Transcription execution error: {e}")
            return ""