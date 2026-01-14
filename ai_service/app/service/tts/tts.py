from gtts import gTTS
import io
import base64
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class TTSService:
    def __init__(self, lang: str = "he"):
        self.default_lang = lang

    def text_to_speech_base64(self, text: str, lang: Optional[str] = None) -> str:
        """
        Converts text to speech and returns the audio as a base64 encoded string.
        """
        try:
            language = lang or self.default_lang
            logger.info(f"Generating TTS for text: {text[:50]}... in {language}")
            
            tts = gTTS(text=text, lang=language)
            
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            
            audio_data = fp.read()
            base64_audio = base64.b64encode(audio_data).decode('utf-8')
            
            return base64_audio
        except Exception as e:
            logger.error(f"Error in TTS generation: {e}")
            raise
