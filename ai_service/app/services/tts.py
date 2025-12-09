import logging
import edge_tts
import asyncio
import io
from gtts import gTTS
from typing import AsyncGenerator
from app.core.config import settings

logger = logging.getLogger(__name__)

class TTSService:
    """
    Text-to-Speech (TTS) Service.
    
    Primary: EdgeTTS (Microsoft Azure Cognitive Services free tier wrapper).
    Fallback: gTTS (Google Translate TTS).
    """

    def __init__(self):
        self.voice = settings.TTS_VOICE

    async def stream_audio(self, text: str) -> AsyncGenerator[bytes, None]:
        """
        Generates audio for the given text and yields it in chunks.
        
        Attempts to use EdgeTTS first. If it fails (network, timeout), 
        falls back to gTTS.
        
        Args:
            text: The text to convert to speech.
            
        Yields:
            bytes: Audio data chunks (usually mp3 format).
        """
        try:
            communicate = edge_tts.Communicate(text, self.voice)
            stream = communicate.stream().__aiter__()
            
            # --- Health Check / Fast Fail ---
            # Attempt to get the first chunk with a strict timeout.
            # This prevents the stream from hanging indefinitely if the service is unreachable.
            first_chunk = await asyncio.wait_for(stream.__anext__(), timeout=5.0)
            
            if first_chunk["type"] == "audio":
                yield first_chunk["data"]
            
            # --- Stream Remaining Chunks ---
            async for chunk in stream:
                 if chunk["type"] == "audio":
                    yield chunk["data"]

        except Exception as e:
            logger.warning(f"⚠️ EdgeTTS failed or timed out: {e}. Attempting fallback to gTTS.")
            
            # Fallback strategy
            try:
                loop = asyncio.get_running_loop()
                # Run blocking gTTS generation in a separate thread
                audio_data = await loop.run_in_executor(None, self._generate_gtts, text)
                yield audio_data
            except Exception as e2:
                logger.error(f"❌ gTTS fallback also failed: {e2}")

    def _generate_gtts(self, text: str) -> bytes:
        """
        Internal helper for gTTS generation.
        Returns the full audio bytes (not streaming).
        """
        fp = io.BytesIO()
        tts = gTTS(text=text, lang='en')
        tts.write_to_fp(fp)
        return fp.getvalue()