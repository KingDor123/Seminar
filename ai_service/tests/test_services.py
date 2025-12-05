import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from app.services.stt import STTService
from app.services.llm import LLMService
from app.services.tts import TTSService

# --- STT Service Tests ---
def test_stt_service_transcribe():
    # Mock the WhisperModel
    with patch("app.services.stt.WhisperModel") as MockModel:
        # Setup the mock instance
        mock_instance = MockModel.return_value
        
        # Setup return value for transcribe
        # It returns (segments, info)
        Segment = MagicMock()
        Segment.text = "Hello world"
        
        Info = MagicMock()
        Info.language_probability = 0.99
        
        mock_instance.transcribe.return_value = ([Segment], Info)

        service = STTService()
        
        # Test with dummy bytes
        result = service.transcribe(b"dummy_audio_data")
        
        assert result == "Hello world"
        mock_instance.transcribe.assert_called_once()

# --- LLM Service Tests ---
def test_llm_service_chat_stream():
    with patch("app.services.llm.ollama.Client") as MockClient:
        mock_client_instance = MockClient.return_value
        
        # Mock the chat method to return an iterator/generator
        mock_stream_response = [
            {'message': {'content': 'Hello'}},
            {'message': {'content': ' world'}}
        ]
        mock_client_instance.chat.return_value = iter(mock_stream_response)

        service = LLMService()
        generator = service.chat_stream([{"role": "user", "content": "hi"}])
        
        results = list(generator)
        assert results == ["Hello", " world"]

# --- TTS Service Tests ---
@pytest.mark.asyncio
async def test_tts_service_stream():
    # Mock edge_tts.Communicate
    with patch("app.services.tts.edge_tts.Communicate") as MockCommunicate:
        mock_comm_instance = MockCommunicate.return_value
        
        # Mock stream() to be an async generator
        async def async_gen():
            yield {"type": "audio", "data": b"chunk1"}
            yield {"type": "other", "data": b"ignore"}
            yield {"type": "audio", "data": b"chunk2"}
        
        mock_comm_instance.stream.return_value = async_gen()

        service = TTSService()
        chunks = []
        async for chunk in service.stream_audio("Hello"):
            chunks.append(chunk)
            
        assert chunks == [b"chunk1", b"chunk2"]
