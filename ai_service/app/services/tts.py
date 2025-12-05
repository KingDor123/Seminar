import logging
import edge_tts
import asyncio
import tempfile
import os

from app.core.config import settings

logger = logging.getLogger(__name__)

class TTSService:
    def __init__(self):
        self.voice = settings.TTS_VOICE

    async def stream_audio(self, text: str) -> getattr(asyncio, "Queue", object): # Returns a generator actually
        """
        Streams audio chunks from EdgeTTS.
        """
        communicate = edge_tts.Communicate(text, self.voice)
        
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                yield chunk["data"]
