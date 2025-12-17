import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from app.services.stt import STTService
from app.services.llm import LLMService
from app.services.tts import TTSService

# --- STT Service Tests ---
def test_stt_service_transcribe():
    # Mock the WhisperModel at the class level within the module
    with patch("app.services.stt.WhisperModel") as MockModel:
        # Setup the mock instance
        mock_instance = MockModel.return_value
        
        # Setup return value for transcribe
        # It returns (segments, info)
        Segment = MagicMock()
        Segment.text = "Hello world"
        Segment.start = 0.0
        Segment.end = 1.0
        
        Info = MagicMock()
        Info.language_probability = 0.99
        
        mock_instance.transcribe.return_value = ([Segment], Info)

        service = STTService()
        
        # Test with dummy bytes
        result = service.transcribe(b"dummy_audio_data")
        
        # The service cleans text, so "Hello world" stays "Hello world"
        assert result["clean_text"] == "Hello world"
        mock_instance.transcribe.assert_called_once()

# --- LLM Service Tests ---
def test_llm_service_chat_stream():
    # Mock the OpenAI client
    with patch("app.services.llm.OpenAI") as MockClient:
        mock_client_instance = MockClient.return_value
        
        # Mock the chat.completions.create method
        mock_stream = MagicMock()
        
        # Create chunk objects that mimic OpenAI response
        chunk1 = MagicMock()
        chunk1.choices[0].delta.content = "Hello"
        chunk2 = MagicMock()
        chunk2.choices[0].delta.content = " world"
        
        mock_stream.__iter__.return_value = [chunk1, chunk2]
        
        mock_client_instance.chat.completions.create.return_value = mock_stream

        service = LLMService()
        generator = service.chat_stream([{"role": "user", "content": "hi"}])
        
        results = list(generator)
        assert results == ["Hello", " world"]

# --- TTS Service Tests ---
@pytest.mark.asyncio
async def test_tts_service_stream():
    # Mock gTTS since we switched to it
    with patch("app.services.tts.gTTS") as MockGTTS:
        mock_gtts_instance = MockGTTS.return_value
        
        # Mock write_to_fp to write some bytes to the file pointer
        def side_effect(fp):
            fp.write(b"gtts_audio_data")
        
        mock_gtts_instance.write_to_fp.side_effect = side_effect

        service = TTSService()
        chunks = []
        async for chunk in service.stream_audio("Hello"):
            chunks.append(chunk)
            
        assert chunks == [b"gtts_audio_data"]
        MockGTTS.assert_called_with("Hello", lang="en")
