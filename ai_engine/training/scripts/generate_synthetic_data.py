import json
import random
from openai import OpenAI
from tqdm import tqdm
import os

# Configure Ollama Client (using OpenAI compatible API)
client = OpenAI(
    base_url='http://localhost:11434/v1',
    api_key='ollama', # required, but unused
)

MODEL = "llama3.2"

SCENARIO_PROMPTS = [
    "A job interview for a junior developer position where the interviewer asks an unexpected question.",
    "A grocery store interaction where the clerk is chatty but the customer is in a rush.",
    "A first date at a coffee shop where the other person is shy.",
    "Asking a landlord about fixing a leaky faucet.",
    "Returning a defective item to a store without a receipt."
]

SYSTEM_PROMPT = """
You are an expert scriptwriter for soft skills training simulations. 
Generate a realistic, multi-turn dialogue between a User (Student) and an NPC (AI Persona).
The dialogue should demonstrate GOOD social skills: active listening, clear communication, and emotional regulation.
Output ONLY valid JSON in the following format:
{
  "scenario_description": "...",
  "system_prompt_for_ai": "...",
  "conversation": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
"""

def generate_sample(scenario):
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Generate a scenario for: {scenario}"}
            ],
            temperature=0.8,
            max_tokens=1024
        )
        content = response.choices[0].message.content
        # Extract JSON
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
             content = content.split("```")[1].split("```")[0].strip()
        
        return json.loads(content)
    except Exception as e:
        print(f"Error generating sample: {e}")
        return None

def main():
    dataset = []
    TARGET_COUNT = 20  # Let's start with 20 high-quality examples
    
    print(f"Generating {TARGET_COUNT} synthetic conversations using {MODEL}...")
    
    pbar = tqdm(total=TARGET_COUNT)
    while len(dataset) < TARGET_COUNT:
        scenario = random.choice(SCENARIO_PROMPTS)
        sample = generate_sample(scenario)
        if sample and "conversation" in sample:
            dataset.append(sample)
            pbar.update(1)
            
            # Save progressively
            with open("training/data/synthetic_dataset.json", "w") as f:
                json.dump(dataset, f, indent=2)
                
    pbar.close()
    print("Generation Complete. Data saved to training/data/synthetic_dataset.json")

if __name__ == "__main__":
    main()
