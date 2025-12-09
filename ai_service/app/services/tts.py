import logging
import edge_tts
import asyncio
import io
from gtts import gTTS
from app.core.config import settings

logger = logging.getLogger(__name__)

class TTSService:
    def __init__(self):
        self.voice = settings.TTS_VOICE

    async def stream_audio(self, text: str):
        """
        Streams audio chunks from EdgeTTS, falling back to gTTS if it fails.
        """
        try:
            communicate = edge_tts.Communicate(text, self.voice)
            stream = communicate.stream().__aiter__()
            
            # Get first chunk with strict timeout to verify connectivity
            first_chunk = await asyncio.wait_for(stream.__anext__(), timeout=2.0)
            if first_chunk["type"] == "audio":
                yield first_chunk["data"]
            
            # Stream the rest
            async for chunk in stream:
                 if chunk["type"] == "audio":
                    yield chunk["data"]

        except Exception as e:
            logger.warning(f"EdgeTTS failed/timed out: {e}. Falling back to gTTS.")
            try:
                # Fallback to gTTS
                loop = asyncio.get_running_loop()
                audio_data = await loop.run_in_executor(None, self._generate_gtts, text)
                yield audio_data
            except Exception as e2:
                logger.error(f"gTTS fallback also failed: {e2}")

    def _generate_gtts(self, text: str) -> bytes:
        fp = io.BytesIO()
        tts = gTTS(text=text, lang='en')
        tts.write_to_fp(fp)
        return fp.getvalue()
