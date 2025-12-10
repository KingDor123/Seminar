import logging
from faster_whisper import WhisperModel
import numpy as np
from app.core.config import settings

logger = logging.getLogger(__name__)

class STTService:
    """
    Speech-to-Text (STT) Service using Faster-Whisper.
    """

    def __init__(self):
        logger.info(f"🎧 Initializing Whisper ({settings.WHISPER_MODEL_SIZE}) on {settings.WHISPER_DEVICE}...")
        try:
            self.model = WhisperModel(
                settings.WHISPER_MODEL_SIZE, 
                device=settings.WHISPER_DEVICE, 
                compute_type=settings.WHISPER_COMPUTE_TYPE
            )
            logger.info("✅ Whisper Ready.")
        except Exception as e:
            logger.critical(f"❌ Whisper Failed: {e}")
            raise e

    def transcribe(self, audio_bytes: bytes) -> str:
        """
        Transcribes raw Float32 audio bytes to text.
        """
        try:
            # Convert raw bytes to numpy array (Float32)
            audio_array = np.frombuffer(audio_bytes, dtype=np.float32)
            
            # Transcription (beam_size=5 for accuracy)
            segments, info = self.model.transcribe(audio_array, beam_size=5)

            text = " ".join([segment.text for segment in segments]).strip()
            
            if text:
                logger.info(f"🗣️  User said: '{text}' (Conf: {info.language_probability:.2f})")
            
            return text
        except Exception as e:
            logger.error(f"❌ STT Error: {e}")
            return ""