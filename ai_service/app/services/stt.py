import logging
from faster_whisper import WhisperModel
import numpy as np
import io
import soundfile as sf
from app.core.config import settings

logger = logging.getLogger(__name__)

class STTService:
    def __init__(self):
        logger.info(f"Loading Whisper Model: {settings.WHISPER_MODEL_SIZE} on {settings.WHISPER_DEVICE}...")
        try:
            self.model = WhisperModel(
                settings.WHISPER_MODEL_SIZE, 
                device=settings.WHISPER_DEVICE, 
                compute_type=settings.WHISPER_COMPUTE_TYPE
            )
            logger.info("Whisper Model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise e

    def transcribe(self, audio_bytes: bytes) -> str:
        """
        Transcribes raw PCM audio bytes (Float32) to text.
        """
        try:
            # Convert raw bytes to numpy array (Float32)
            # The frontend sends Float32Array, which is little-endian by default on most systems.
            audio_array = np.frombuffer(audio_bytes, dtype=np.float32)
            
            # Transcribe
            # beam_size=5 provides better accuracy at slight cost of speed
            segments, info = self.model.transcribe(audio_array, beam_size=5)

            text = " ".join([segment.text for segment in segments]).strip()
            
            if text:
                logger.info(f"Transcribed: '{text}' (Prob: {info.language_probability:.2f})")
            
            return text
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return ""

    def transcribe_numpy(self, audio_array: np.ndarray, sampling_rate: int = 16000) -> str:
        """
        Transcribes from numpy array (more efficient if we are streaming chunks).
        """
        try:
            segments, info = self.model.transcribe(audio_array, beam_size=5)
            text = " ".join([segment.text for segment in segments]).strip()
            return text
        except Exception as e:
            logger.error(f"Transcription error (numpy): {e}")
            return ""
