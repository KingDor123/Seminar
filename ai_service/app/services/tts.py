import logging
import asyncio
import io
from gtts import gTTS
from typing import AsyncGenerator

logger = logging.getLogger(__name__)

class TTSService:
    """
    Text-to-Speech (TTS) Service using Google TTS (gTTS).
    Switched to gTTS exclusively due to container connectivity issues with Edge TTS.
    """

    def __init__(self):
        # gTTS language default
        self.lang = "en"

    async def stream_audio(self, text: str, voice: str = None) -> AsyncGenerator[bytes, None]:
        """
        Generates audio for the given text using gTTS.
        Note: 'voice' parameter is ignored as gTTS uses 'lang'.
        """
        try:
            logger.info(f"🎤 Generating TTS for: '{text[:30]}...' using gTTS")
            
            # gTTS is synchronous, so run in executor to avoid blocking the event loop
            loop = asyncio.get_running_loop()
            audio_data = await loop.run_in_executor(None, self._generate_gtts, text)
            
            yield audio_data

        except Exception as e:
            logger.error(f"❌ gTTS Error: {e}")

    def _generate_gtts(self, text: str) -> bytes:
        tts = gTTS(text, lang=self.lang)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        return fp.getvalue()
