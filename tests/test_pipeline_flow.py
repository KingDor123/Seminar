import pytest
import sys
import os
import asyncio
from unittest.mock import MagicMock, AsyncMock

# Add ai_service to path so we can import the pipeline
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from ai_service.pipeline import HybridPipeline

@pytest.mark.asyncio
async def test_hebrew_pipeline_flow():
    print("\n\n🧪 INITIALIZING PIPELINE TEST 🧪")
    print("==================================")
    
    # 1. Initialize Pipeline (Force CPU for test stability if GPU busy, or let it auto-detect)
    # We mock the LLM client to avoid actual API calls and to inspect the prompt
    pipeline = HybridPipeline() 
    pipeline.llm_client = AsyncMock()
    
    # Setup Mock Response for Aya
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="תגובה מסומלצת מאיה: אני מבינה שאתה לחוץ, זה טבעי להרגיש ככה לפני פגישה חשובה."))]
    pipeline.llm_client.chat.completions.create.return_value = mock_response

    # 2. Simulate User Input
    input_text = "אני ממש לחוץ מהפגישה מחר, כואבת לי הבטן מרוב לחץ."
    print(f"\n📥 User Input: \"{input_text}\"")

    # 3. DEBUG: Inspect HeBERT Output directly (Unit Test Style)
    print("\n--- [DEBUG] Step B: HeBERT Raw Output ---")
    sentiment_data = pipeline._analyze_sentiment(input_text)
    print(f"Sentiment Label: {sentiment_data['sentiment']}")
    print(f"Confidence:      {sentiment_data['confidence']}")
    print(f"Logits Shape:    {len(sentiment_data['logits'][0])} classes")

    # 4. Run Full Flow
    final_response = await pipeline.process_user_message(input_text)

    # 5. CRITICAL: Inspect the Prompt sent to Aya
    # We grab the arguments the mock was called with
    calls = pipeline.llm_client.chat.completions.create.call_args
    
    if calls:
        _, kwargs = calls
        messages = kwargs.get('messages', [])
        
        print("\n--- [CRITICAL] Step C: Final Constructed Prompt ---")
        for msg in messages:
            role = msg['role'].upper()
            content = msg['content']
            print(f"[{role}]:\n{content}\n")
            
            # Verification Logic
            if role == "USER":
                assert f"User sentiment is {sentiment_data['sentiment']}" in content, "❌ Prompt missed the sentiment injection!"
                assert input_text in content, "❌ Prompt missed the original text!"

    # 6. Final Response
    print("--- [DEBUG] Step D: Final Response ---")
    print(final_response)
    print("\n✅ Test Complete")

if __name__ == "__main__":
    asyncio.run(test_hebrew_pipeline_flow())
