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
    
    # We need to patch the services that are instantiated in app.routers.conversation
    # Since they are module-level variables in that file, we patch them there.
    
    with patch("app.routers.conversation.stt_service") as mock_stt, \
         patch("app.routers.conversation.llm_service") as mock_llm, \
         patch("app.routers.conversation.tts_service") as mock_tts:

        # 1. Setup Mock Behaviors
        
        # STT: Returns "Hello AI" when called
        mock_stt.transcribe.return_value = "Hello AI"
        
        # LLM: Yields tokens "Hi", " there", "."
        # We need to mock the generator properly
        def llm_gen(history):
            yield "Hi"
            yield " there"
            yield "."
        mock_llm.chat_stream.side_effect = llm_gen
        
        # TTS: Yields audio bytes
        async def tts_gen(text):
            yield b"audio_chunk_1"
            yield b"audio_chunk_2"
        mock_tts.stream_audio.side_effect = tts_gen

        # 2. Start TestClient
        client = TestClient(app)
        
        with client.websocket_connect("/ws/conversation") as websocket:
            
            # 3. Simulate sending Audio (dummy bytes)
            websocket.send_bytes(b"fake_wav_header_and_pcm")
            
            # 4. Verify Response Sequence
            
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
