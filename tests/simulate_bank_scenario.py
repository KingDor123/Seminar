import sys
import os

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# Also add ai_service for internal 'app' imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../ai_service')))

import asyncio
from unittest.mock import MagicMock, AsyncMock

from ai_service.pipeline import HybridPipeline

async def simulate_bank_scenario():
    print("\nBANK SCENARIO SIMULATION: ADAPTIVE DIFFICULTY TEST")
    print("=======================================================")

    # 1. Initialize Pipeline
    # Using CPU to avoid potential GPU conflicts during rapid testing
    pipeline = HybridPipeline(device="cpu")

    # 2. Mocking the LLM Client
    pipeline.llm_client = AsyncMock()

    # Define mock responses for the two cases to simulate what Aya MIGHT say
    mock_responses = {
        "easy": "אני מבין שזה מצב מלחיץ, אדוני. בוא נשב רגע ונבדוק יחד אילו אפשרויות עומדות בפנינו כדי לפתור את זה.",
        "hard": "אדוני, הנהלים ברורים. יש חריגה ואין אישור למשיכה. אני לא יכול לעקוף את המערכת."
    }

    def side_effect(*args, **kwargs):
        # Determine which response to return based on the difficulty found in the prompt
        messages = kwargs.get('messages', [])
        system_prompt = messages[0]['content']
        
        # Use more specific matching to avoid 'soften your tone' matching 'Do not soften your tone'
        if "soften your tone significantly" in system_prompt:
            content = mock_responses["easy"]
        elif "Maintain a strict and professional persona" in system_prompt:
            content = mock_responses["hard"]
        else:
            content = "תגובה גנרית."
            
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content=content))]
        return mock_response

    pipeline.llm_client.chat.completions.create.side_effect = side_effect


    # --- SCENARIO SETUP ---
    base_system_prompt = "אתה פקיד בנק עייף אך מקצועי. המטרה שלך היא להסביר ללקוח שיש לו חריגה בחשבון ושאי אפשר למשוך מזומן."
    user_input = "אני לא מבין מה קורה, אני חייב את הכסף הזה לקניות, אני ממש בלחץ מזה! תעזור לי!"
    
    print(f"\nBase Persona: \"{base_system_prompt}\"")
    print(f"User Input:  \"{user_input}\"")


    # --- TEST CASE A: EASY MODE ---
    print("\n\n--- TEST CASE A: DIFFICULTY = 'EASY' ---")
    
    # Run Pipeline
    response_easy = await pipeline.process_user_message(
        text=user_input, 
        base_system_prompt=base_system_prompt, 
        difficulty_level="easy"
    )

    # Inspect Internal State
    call_args_easy = pipeline.llm_client.chat.completions.create.call_args_list[-1]
    _, kwargs_easy = call_args_easy
    sent_messages_easy = kwargs_easy['messages']
    final_system_prompt_easy = sent_messages_easy[0]['content']

    # Extract Injection part
    injection_start = final_system_prompt_easy.find("--- DYNAMIC BEHAVIORAL ADJUSTMENT ---")
    injection_end = final_system_prompt_easy.find("-------------------------------------")
    injected_instruction_easy = final_system_prompt_easy[injection_start:injection_end+37]

    # Print Report
    print(f"[INJECTED INSTRUCTION]:\n{injected_instruction_easy.strip()}")
    print(f"[AYA RESPONSE]:\n{response_easy}")


    # --- TEST CASE B: HARD MODE ---
    print("\n\n--- TEST CASE B: DIFFICULTY = 'HARD' ---")

    # Run Pipeline
    response_hard = await pipeline.process_user_message(
        text=user_input, 
        base_system_prompt=base_system_prompt, 
        difficulty_level="hard"
    )

    # Inspect Internal State
    call_args_hard = pipeline.llm_client.chat.completions.create.call_args_list[-1]
    _, kwargs_hard = call_args_hard
    sent_messages_hard = kwargs_hard['messages']
    final_system_prompt_hard = sent_messages_hard[0]['content']

    # Extract Injection part
    injection_start = final_system_prompt_hard.find("--- DYNAMIC BEHAVIORAL ADJUSTMENT ---")
    injection_end = final_system_prompt_hard.find("-------------------------------------")
    injected_instruction_hard = final_system_prompt_hard[injection_start:injection_end+37]

    # Print Report
    print(f"[INJECTED INSTRUCTION]:\n{injected_instruction_hard.strip()}")
    print(f"[AYA RESPONSE]:\n{response_hard}")

    print("\nSimulation Complete.")

if __name__ == "__main__":
    asyncio.run(simulate_bank_scenario())
