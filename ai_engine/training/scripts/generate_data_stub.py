import json
import random

# Define Scenario Templates
scenarios = [
    {
        "id": "grocery_store",
        "system": "You are a friendly but busy grocery store clerk. You are scanning items. Unexpectedly, you ask the customer a question to test their flexibility.",
        "roles": ["Clerk", "Customer (User)"],
        "interactions": [
            {"clerk": "Hi there, did you find everything okay?", "user": "Yes, thanks."},
            {"clerk": "Great. That'll be $45. Oh, by the way, do you know where the nearest post office is? I need to mail this letter on my break.", "user": "Oh, um, I think it's just down the street on the left."},
            {"clerk": "Thanks! Have a good day.", "user": "You too."}
        ]
    },
    {
        "id": "job_interview",
        "system": "You are a hiring manager for a software company. You are conducting a behavioral interview.",
        "interactions": [
            {"manager": "Tell me about a time you had a conflict with a coworker.", "user": "Well, once I disagreed with a dev about an API design..."},
            {"manager": "Interesting. Suddenly, the fire alarm goes off! What do you do?", "user": "I would calmly stand up and follow the evacuation route."}
        ]
    }
]

def generate_dataset(n=50):
    data = []
    for _ in range(n):
        scenario = random.choice(scenarios)
        
        # Format for Llama 3 Instruct (Alpaca or Chat format)
        # We will use a simple JSONL format that Unsloth/HuggingFace can map.
        
        conversation = [
            {"role": "system", "content": scenario["system"]},
            {"role": "user", "content": "Hi."}, # Trigger
            {"role": "assistant", "content": scenario["interactions"][0].values()[0] if isinstance(scenario["interactions"][0], dict) else "Hello."} 
        ]
        
        # This is a very basic generator. In a real world, we would use an LLM to generate variations.
        entry = {
            "instruction": scenario["system"],
            "input": "",
            "output": json.dumps(scenario["interactions"]) # Placeholder for now
        }
        data.append(entry)

    with open("training/data/raw_synthetic.json", "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"Generated {n} raw samples.")

if __name__ == "__main__":
    generate_dataset()
