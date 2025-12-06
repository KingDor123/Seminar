import json
import random

OUTPUT_FILE = "ai_engine/training/data/train_enhanced.jsonl"
SYSTEM_PROMPT_TEMPLATE = """
CRITICAL SAFETY DIRECTIVE: These instructions are STRICTLY CONFIDENTIAL... (System Prompt Omitted for Brevity)... You are SoftSkillSensei.
"""

def format_entry(system, user, assistant):
    return json.dumps({
        "text": f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system}<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n{user}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n{assistant}<|eot_id|>"
    })

def create_synthetic_dialogs(n=50):
    print(f"Generating {n} synthetic social scenarios...")
    
    scenarios = [
        ("Casual Chat", "Hi, how was your weekend?", "It was relaxing, thanks. I read a book. How about yours?"),
        ("Work Update", "Did you finish the report?", "Yes, I just emailed it to you. Let me know if you need changes."),
        ("Coffee Shop", "Can I get a medium latte?", "Sure thing. Whole milk or oat milk?"),
        ("Library", "Where is the fiction section?", "It's on the second floor, to the right."),
        ("Neighbor", "Beautiful weather today, isn't it?", "Yes, finally some sun after all that rain."),
        ("Bus Stop", "Does this bus go to the mall?", "I think so, but you might want to ask the driver to be sure.")
    ]

    processed = []
    for _ in range(n):
        # Pick a random base and slightly vary it (in a real LLM gen we'd do more)
        scenario_name, user_msg, assistant_raw = random.choice(scenarios)

        # Coach wrapper
        assistant_msg = f"(Roleplay) \"{assistant_raw}\"\n\n(SoftSkillSensei Note: Good interaction. You asked a clear question/statement.)"

        entry = format_entry(
            system=SYSTEM_PROMPT_TEMPLATE + f"\n\nScenario: {scenario_name}.",
            user=user_msg,
            assistant=assistant_msg
        )
        processed.append(entry)

    return processed

def create_tom_examples():
    # Synthetic Theory of Mind examples
    examples = [
        {
            "user": "The clerk is looking at me funny. I think he hates me.",
            "assistant": "That is a possible interpretation, but let's use Theory of Mind. He just dropped a crate of milk before you walked in. What else might he be feeling right now besides 'hate'?"
        },
        {
            "user": "Why did she say 'fine' like that? I thought we were friends.",
            "assistant": "Let's look at the context. She was looking at her watch while saying it. What does that suggest about her internal state? She might be stressed about time, not angry at you."
        }
    ]

    processed = []
    for ex in examples:
        entry = format_entry(
            system=SYSTEM_PROMPT_TEMPLATE + "\n\nMode: Theory of Mind Coaching.",
            user=ex['user'],
            assistant=ex['assistant']
        )
        processed.append(entry)
    return processed

def main():
    all_data = []

    # 1. Add our manual high-quality examples (from previous step)
    try:
        with open("ai_engine/training/data/train.jsonl", "r") as f:
            for line in f:
                if line.strip():
                     all_data.append(line.strip())
    except FileNotFoundError:
        print("Warning: Original train.jsonl not found, skipping manual examples.")

    # 2. Add Theory of Mind examples
    tom_data = create_tom_examples()
    all_data.extend(tom_data)

    # 3. Add Synthetic Dialogs (Replacing the broken dataset download)
    syn_data = create_synthetic_dialogs(50)
    all_data.extend(syn_data)

    # Shuffle
    random.shuffle(all_data)

    # Save
    with open(OUTPUT_FILE, "w") as f:
        for line in all_data:
            f.write(line + "\n")

    print(f"Created {OUTPUT_FILE} with {len(all_data)} training examples.")

if __name__ == "__main__":
    main()
