from faster_whisper import WhisperModel
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

class STTService:
    def __init__(self, model_size: str = "medium", device: str = "auto", compute_type: str = "default"):
        """
        Initializes the Faster-Whisper STT service.
        model_size can be "tiny", "base", "small", "medium", "large-v3"
        """
        try:
            logger.info(f"Loading Faster-Whisper model: {model_size} on {device}")
            # Use CUDA if available, otherwise CPU
            if device == "auto":
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
                
            self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
            logger.info("Faster-Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Faster-Whisper model: {e}")
            raise

    def transcribe(self, audio_path: str, language: str = "he") -> str:
        """
        Transcribes an audio file into text.
        """
        if not os.path.exists(audio_path):
            logger.error(f"Audio file not found: {audio_path}")
            return ""

        try:
            segments, info = self.model.transcribe(audio_path, beam_size=5, language=language)
            
            full_text = ""
            for segment in segments:
                full_text += segment.text + " "
                
            return full_text.strip()
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            return ""
