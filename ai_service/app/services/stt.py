import logging
import io
from faster_whisper import WhisperModel
import numpy as np
from app.core.config import settings

logger = logging.getLogger(__name__)

class STTService:
    """
    Speech-to-Text (STT) Service using Faster-Whisper.
    """

    def __init__(self):
        device = settings.WHISPER_DEVICE
        compute_type = settings.WHISPER_COMPUTE_TYPE
        
        logger.info(f"🎧 Initializing Whisper ({settings.WHISPER_MODEL_SIZE}) on preferred device: {device}...")

        try:
            # Attempt to initialize with preferred settings
            self.model = WhisperModel(
                settings.WHISPER_MODEL_SIZE, 
                device=device, 
                compute_type=compute_type
            )
        except Exception as e:
            if device == "cuda":
                logger.warning(f"⚠️ Failed to initialize Whisper on CUDA: {e}. Falling back to CPU.")
                try:
                    self.model = WhisperModel(
                        settings.WHISPER_MODEL_SIZE, 
                        device="cpu", 
                        compute_type="int8" # CPU usually needs int8 or float32
                    )
                    device = "cpu"
                except Exception as cpu_e:
                    logger.critical(f"❌ Whisper CPU Fallback Failed: {cpu_e}")
                    raise cpu_e
            else:
                logger.critical(f"❌ Whisper Failed: {e}")
                raise e
        
        logger.info(f"✅ Whisper Ready on {device}.")

    def transcribe(self, audio_bytes: bytes) -> str:
        """
        Transcribes audio file bytes (WAV/WebM) to text.
        """
        try:
            # Wrap bytes in BytesIO to let faster-whisper handle decoding (via ffmpeg)
            audio_file = io.BytesIO(audio_bytes)
            
            # Transcription (beam_size=5 for accuracy)
            segments, info = self.model.transcribe(audio_file, beam_size=5)

            text = " ".join([segment.text for segment in segments]).strip()
            
            if text:
                logger.info(f"🗣️  User said: '{text}' (Conf: {info.language_probability:.2f})")
            
            return text
        except Exception as e:
            logger.error(f"❌ STT Error: {e}")
            return ""