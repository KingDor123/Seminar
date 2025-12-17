import logging
import io
import re
from typing import Dict, Any, List
from faster_whisper import WhisperModel
import numpy as np
from app.core.config import settings

logger = logging.getLogger(__name__)

class STTService:
    """
    Speech-to-Text (STT) Service using Faster-Whisper.
    Returns structured behavioral data.
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

    def transcribe(self, audio_bytes: bytes) -> Dict[str, Any]:
        """
        Transcribes audio file bytes (WAV/WebM) to structured behavioral data.
        Returns:
            Dict containing:
            - raw_text: Original text including fillers
            - clean_text: Text without fillers
            - word_count: Number of words in clean text
            - total_speech_duration_sec: Duration from first word to last word
            - pauses: List of pause objects {start, end, duration}
            - pause_count: Number of pauses > 0.5s
            - pause_total_time_sec: Total duration of all pauses
            - speech_rate_wpm: Words per minute
            - filler_word_count: Count of 'um', 'uh', etc.
        """
        try:
            # Wrap bytes in BytesIO to let faster-whisper handle decoding (via ffmpeg)
            audio_file = io.BytesIO(audio_bytes)
            
            # Transcription (beam_size=5 for accuracy)
            segments, info = self.model.transcribe(audio_file, beam_size=5)
            
            # Collect segments to list to iterate
            segments_list = list(segments)

            if not segments_list:
                return {
                    "raw_text": "",
                    "clean_text": "",
                    "word_count": 0,
                    "total_speech_duration_sec": 0.0,
                    "pauses": [],
                    "pause_count": 0,
                    "pause_total_time_sec": 0.0,
                    "speech_rate_wpm": 0.0,
                    "filler_word_count": 0
                }

            # 1. Raw Text
            raw_text = " ".join([s.text.strip() for s in segments_list]).strip()
            
            # 2. Filler Word Detection
            # Common fillers: um, uh, erm, ah, like, you know (simplified list)
            filler_pattern = r"\b(um|uh|erm|ah|umm|uhh)\b"
            fillers = re.findall(filler_pattern, raw_text, re.IGNORECASE)
            filler_word_count = len(fillers)
            
            # 3. Clean Text
            clean_text = re.sub(filler_pattern, "", raw_text, flags=re.IGNORECASE).strip()
            clean_text = re.sub(r"\s+", " ", clean_text) # Normalize spaces

            # 4. Timing & Pauses
            total_speech_duration_sec = 0.0
            pauses = []
            
            first_start = segments_list[0].start
            last_end = segments_list[-1].end
            total_turn_duration = last_end - first_start
            
            # Count words (naive split of clean text)
            word_count = len(clean_text.split())

            # Detect Pauses
            for i in range(1, len(segments_list)):
                prev_end = segments_list[i-1].end
                curr_start = segments_list[i].start
                gap = curr_start - prev_end
                if gap > 0.5:
                    pauses.append({
                        "start": prev_end,
                        "end": curr_start,
                        "duration": gap
                    })
            
            # Speech Rate (WPM)
            speech_rate_wpm = 0.0
            if total_turn_duration > 0.1: # Avoid div by zero or tiny durations
                speech_rate_wpm = (word_count / total_turn_duration) * 60.0

            result = {
                "raw_text": raw_text,
                "clean_text": clean_text,
                "word_count": word_count,
                "total_speech_duration_sec": round(total_turn_duration, 2),
                "pauses": pauses,
                "pause_count": len(pauses),
                "pause_total_time_sec": round(sum(p["duration"] for p in pauses), 2),
                "speech_rate_wpm": round(speech_rate_wpm, 2),
                "filler_word_count": filler_word_count
            }
            
            if raw_text:
                logger.info(f"🗣️  Analyzed Speech: {word_count} words, {result['speech_rate_wpm']} WPM, {filler_word_count} fillers.")
            
            return result

        except Exception as e:
            logger.error(f"❌ STT Error: {e}")
            return {
                "raw_text": "", 
                "clean_text": "", 
                "word_count": 0,
                "error": str(e)
            }