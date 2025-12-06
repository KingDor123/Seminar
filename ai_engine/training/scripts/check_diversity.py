import json

data = []
with open('ai_engine/training/data/bank_train.jsonl', 'r') as f:
    for line in f:
        data.append(json.loads(line))

print(f"Total samples: {len(data)}")
print(f"First 50 chars of sample 1: {data[0]['text'][:50]}")
print(f"First 50 chars of sample 2: {data[1]['text'][:50]}")

# Check uniqueness of the CONVERSATION part (after the system prompt)
conversations = set()
for entry in data:
    # Split by user/assistant tokens to ignore the system prompt part
    parts = entry['text'].split("<|start_header_id|>user<|end_header_id|>")
    if len(parts) > 1:
        conversations.add(parts[1])

print(f"Unique conversations (excluding system prompt): {len(conversations)}")
