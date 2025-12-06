import json
import random
import os

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
SCENARIO_FILE = os.path.join(DATA_DIR, "bank_Scenario_Dataset", "Bank_scenrio.json")
PROMPT_FILE = os.path.join(DATA_DIR, "bank_Scenario_Dataset", "bank_system_prompt.json")
OUTPUT_TRAIN = os.path.join(DATA_DIR, "bank_train.jsonl")
OUTPUT_VALID = os.path.join(DATA_DIR, "bank_valid.jsonl")

def load_system_prompt():
    with open(PROMPT_FILE, 'r') as f:
        content = f.read().strip()
        # Remove the wrapper {CRITICAL DIRECTIVE: ... }
        if content.startswith("{CRITICAL DIRECTIVE:"):
            content = content[len("{CRITICAL DIRECTIVE:"):].strip()
        if content.endswith("}"):
            content = content[:-1].strip()
        return content

def load_scenario_steps():
    steps = []
    with open(SCENARIO_FILE, 'r') as f:
        for line in f:
            if line.strip():
                steps.append(json.loads(line))
    return steps

def format_llama_entry(system, conversation):
    # conversation is a list of {"role": "...", "content": "..."}
    text = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system}<|eot_id|>"
    for turn in conversation:
        text += f"<|start_header_id|>{turn['role']}<|end_header_id|>\n\n{turn['content']}<|eot_id|>"
    return {"text": text}

def generate_dataset():
    print(f"Loading data from {DATA_DIR}...")
    
    try:
        system_prompt = load_system_prompt()
    except Exception as e:
        print(f"Error loading system prompt: {e}")
        # Fallback or exit
        return

    scenario_steps = load_scenario_steps()
    
    # Group steps by stage for easier chain generation
    stages = {}
    for step in scenario_steps:
        s = step.get('stage', 0)
        if s not in stages:
            stages[s] = []
        stages[s].append(step)

    dataset = []
    
    # 1. Generate Full Linear "Happy Path" Conversations
    # We can generate many variations by picking different variations for each stage.
    NUM_HAPPY_PATHS = 50 
    
    sorted_stage_keys = sorted(stages.keys())
    
    for _ in range(NUM_HAPPY_PATHS):
        conversation = []
        
        # Start the conversation
        # Usually the assistant starts in this scenario: "Hello, my name is Dana..."
        # But Llama models usually expect User first? 
        # Actually, the system prompt says "Begin every conversation with: 'Hello...'"
        # So the assistant speaks first.
        # However, standard chat templates often expect User first.
        # To make it work for training, we can have a dummy user start like "(Connects to video call)" 
        # or just have the Assistant start. Llama 3 supports Assistant starting if the prompt is set right,
        # but often it's safer to have a User "trigger".
        # Let's assume a User "trigger" of "Hi" or "Start" or similar isn't strictly in the dataset.
        # Let's look at the existing train.jsonl... 
        # Existing: User: "Does this bus go to the mall?" -> Assistant: "I think so..."
        # In our case, Dana speaks FIRST. 
        # We can model this by having the USER says "Hello" or "Joining call" and then Dana gives the Stage 1 message.
        
        conversation.append({"role": "user", "content": "(User joins the video call)"})
        
        for i, stage_num in enumerate(sorted_stage_keys):
            # Pick a random variation for this stage
            step_variation = random.choice(stages[stage_num])
            
            # Dana speaks
            conversation.append({"role": "assistant", "content": step_variation['message']})
            
            # User responds (using one of the OK examples)
            # We need a response for all stages except maybe the very last one if it ends the call.
            # But the dataset seems to go up to Stage 8.
            user_response = random.choice(step_variation['examples_ok'])
            conversation.append({"role": "user", "content": user_response})
        
        dataset.append(format_llama_entry(system_prompt, conversation))

    # 2. Generate "Correction" Short-Form Conversations
    # These teach the model to handle bad inputs.
    # Context: (Optional: Stage N-1) -> Dana: Stage N Message -> User: Bad Input -> Dana: Redirect -> User: Good Input -> Dana: Stage N+1 (or acknowledgment)
    
    for stage_num in sorted_stage_keys:
        steps = stages[stage_num]
        for step in steps:
            for bad_input in step.get('examples_bad', []):
                conversation = []
                
                # Context: User joins
                conversation.append({"role": "user", "content": "(User joins the video call)"})
                
                # Optional: Add previous history to make it deeper? 
                # For simplicity, let's jump straight to the current stage or maybe 1 stage back.
                # Let's just do current stage interaction to focus the gradient on the Redirect.
                
                # Actually, it's better if we have the history up to this point, 
                # otherwise the model might not know WHY we are at Stage 3.
                # Let's generate a "prefix" history.
                
                # PREFIX GENERATION
                if stage_num > 1:
                    # Generate random history up to stage_num - 1
                    for prev_s in sorted_stage_keys:
                        if prev_s >= stage_num: break
                        prev_step = random.choice(stages[prev_s])
                        conversation.append({"role": "assistant", "content": prev_step['message']})
                        conversation.append({"role": "user", "content": random.choice(prev_step['examples_ok'])})
                
                # CURRENT STAGE (The 'Bad' Interaction)
                conversation.append({"role": "assistant", "content": step['message']})
                conversation.append({"role": "user", "content": bad_input})
                conversation.append({"role": "assistant", "content": step['redirect_message']})
                
                # Complete the loop with a good input + next stage (rewarding the user)
                conversation.append({"role": "user", "content": random.choice(step['examples_ok'])})
                
                # If there is a next stage, add it
                next_stage_idx = sorted_stage_keys.index(stage_num) + 1
                if next_stage_idx < len(sorted_stage_keys):
                    next_stage_num = sorted_stage_keys[next_stage_idx]
                    next_step = random.choice(stages[next_stage_num])
                    conversation.append({"role": "assistant", "content": next_step['message']})
                
                dataset.append(format_llama_entry(system_prompt, conversation))

    # Shuffle and Split
    random.shuffle(dataset)
    split_idx = int(len(dataset) * 0.9)
    train_data = dataset[:split_idx]
    valid_data = dataset[split_idx:]

    print(f"Generated {len(dataset)} conversations.")
    print(f"Training samples: {len(train_data)}")
    print(f"Validation samples: {len(valid_data)}")

    with open(OUTPUT_TRAIN, 'w') as f:
        for entry in train_data:
            f.write(json.dumps(entry) + "\n")
            
    with open(OUTPUT_VALID, 'w') as f:
        for entry in valid_data:
            f.write(json.dumps(entry) + "\n")

    print(f"Saved to {OUTPUT_TRAIN} and {OUTPUT_VALID}")

if __name__ == "__main__":
    generate_dataset()
