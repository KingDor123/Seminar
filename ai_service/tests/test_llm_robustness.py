
import pytest
from unittest.mock import MagicMock, patch
from app.services.llm import LLMService

# Mock settings to avoid needing environment variables or real connections
@patch('app.services.llm.settings')
@patch('app.services.llm.OpenAI')
def test_analyze_behavior_robustness(mock_openai, mock_settings):
    # Setup
    mock_settings.OLLAMA_HOST = "http://localhost:11434"
    mock_settings.OLLAMA_MODEL = "llama3.2"
    
    service = LLMService()
    
    # Mock the API response to simulate a "chatty" LLM that doesn't just return JSON
    mock_response = MagicMock()
    mock_response.choices[0].message.content = """
    Here is the analysis you requested:
    ```json
    {
        "sentiment": 0.8,
        "topic_adherence": 0.95,
        "clarity": 1.0
    }
    ```
    I hope this helps!
    """
    service.client.chat.completions.create.return_value = mock_response

    # Execute
    result = service.analyze_behavior("I am doing great!", "How are you?")

    # Assert
    assert result['sentiment'] == 0.8
    assert result['topic_adherence'] == 0.95
    assert result['clarity'] == 1.0
    print("\n✅ Test Passed: Successfully extracted JSON from chatty markdown response.")

@patch('app.services.llm.settings')
@patch('app.services.llm.OpenAI')
def test_analyze_behavior_raw_json(mock_openai, mock_settings):
    # Setup
    mock_settings.OLLAMA_HOST = "http://localhost:11434"
    mock_settings.OLLAMA_MODEL = "llama3.2"
    
    service = LLMService()
    
    # Mock response with JUST JSON (no markdown)
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '{"sentiment": -0.5, "topic_adherence": 0.2, "clarity": 0.5}'
    service.client.chat.completions.create.return_value = mock_response

    # Execute
    result = service.analyze_behavior("I hate this.", "How are you?")

    # Assert
    assert result['sentiment'] == -0.5
    print("✅ Test Passed: Successfully extracted raw JSON.")

@patch('app.services.llm.settings')
@patch('app.services.llm.OpenAI')
def test_analyze_behavior_failure_handling(mock_openai, mock_settings):
    # Setup
    mock_settings.OLLAMA_HOST = "http://localhost:11434"
    mock_settings.OLLAMA_MODEL = "llama3.2"
    
    service = LLMService()
    
    # Mock response with BROKEN JSON
    mock_response = MagicMock()
    mock_response.choices[0].message.content = 'This is not JSON at all.'
    service.client.chat.completions.create.return_value = mock_response

    # Execute
    result = service.analyze_behavior("What?", "Context")

    # Assert - should return default safety values
    assert result['sentiment'] == 0.0
    assert result['topic_adherence'] == 0.0
    print("✅ Test Passed: gracefully handled invalid JSON.")

