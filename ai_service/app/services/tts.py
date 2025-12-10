import logging
import asyncio
import io
from gtts import gTTS
from typing import AsyncGenerator
from app.core.config import settings

logger = logging.getLogger(__name__)

class TTSService:
    """
    Text-to-Speech (TTS) Service using Google TTS (gTTS).
    """

    def __init__(self):
        self.lang = 'en'

    async def stream_audio(self, text: str) -> AsyncGenerator[bytes, None]:
        """
        Generates audio for the given text.
        """
        try:
            loop = asyncio.get_running_loop()
            # Run gTTS in a thread pool to avoid blocking the event loop
            audio_data = await loop.run_in_executor(None, self._generate_gtts, text)
            
            if audio_data:
                yield audio_data

        except Exception as e:
            logger.error(f"❌ TTS Error: {e}")

    def _generate_gtts(self, text: str) -> bytes:
        fp = io.BytesIO()
        tts = gTTS(text=text, lang=self.lang)
        tts.write_to_fp(fp)
        return fp.getvalue()