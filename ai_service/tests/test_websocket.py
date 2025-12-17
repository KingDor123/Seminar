import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
import asyncio

# We need to import the app to test it
# We assume the structure is: ai_service/main.py
from main import app

@pytest.mark.asyncio
async def test_websocket_conversation_flow():
    """
    Smart integration test:
    Simulates a user connecting via WebSocket, sending audio, 
    and verifying the sequence of responses (Transcripts, Status updates, Audio).
    """
    
    # Patch the get_services function to return our mocks
    with patch("app.routers.conversation.get_services") as mock_get_services:
        
        # 1. Setup Mock Services
        mock_stt = MagicMock()
        mock_llm = MagicMock()
        mock_tts = MagicMock()
        
        # Configure get_services to return them
        mock_get_services.return_value = (mock_stt, mock_llm, mock_tts)

        # 2. Setup Mock Behaviors
        
        # STT: Returns "Hello AI" when called
        # Note: transcribe returns a dict now, not a string
        mock_stt.transcribe.return_value = {
            "clean_text": "Hello AI",
            "raw_text": "Hello AI",
            "word_count": 2,
            "speech_rate_wpm": 120.0,
            "pause_count": 0,
            "filler_word_count": 0
        }
        
        # LLM: Yields tokens "Hi", " there", "."
        # We need to mock the generator properly
        def llm_gen(history):
            yield "Hi"
            yield " there"
            yield "."
        mock_llm.chat_stream.side_effect = llm_gen
        
        # TTS: Yields audio bytes
        async def tts_gen(text, voice=None):
            yield b"audio_chunk_1"
            yield b"audio_chunk_2"
        mock_tts.stream_audio.side_effect = tts_gen

        # 3. Start TestClient
        client = TestClient(app)
        
        with client.websocket_connect("/ai/stream") as websocket:
            
            # 4. Simulate sending Audio (dummy bytes)
            websocket.send_bytes(b"fake_wav_header_and_pcm")
            
            # 5. Verify Response Sequence
            
            # Expect: Transcript (User)
            data = websocket.receive_json()
            assert data["type"] == "transcript"
            assert data["role"] == "user"
            assert data["text"] == "Hello AI"
            
            # Expect: Status (Processing)
            data = websocket.receive_json()
            assert data["type"] == "status"
            assert data["status"] == "processing"
            
            # The logic in conversation.py accumulates tokens until punctuation.
            # LLM yields: "Hi", " there", "." -> Sentence: "Hi there."
            # Then it sends transcript & audio.
            
            # Expect: Transcript (Assistant) - Partial
            data = websocket.receive_json()
            assert data["type"] == "transcript"
            assert data["role"] == "assistant"
            assert "Hi there" in data["text"]
            
            # Expect: Audio chunks
            # We mocked TTS to yield 2 chunks
            audio1 = websocket.receive_bytes()
            assert audio1 == b"audio_chunk_1"
            
            audio2 = websocket.receive_bytes()
            assert audio2 == b"audio_chunk_2"
            
            # Expect: Status (Listening/Done)
            data = websocket.receive_json()
            assert data["type"] == "status"
            assert data["status"] == "listening"
            
            # Close connection
            websocket.close()
