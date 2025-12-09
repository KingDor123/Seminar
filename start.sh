#!/bin/bash

# Define cleanup function
cleanup() {
    echo ""
    echo "🛑 Stopping MLX Server..."
    if [ -n "$MLX_PID" ]; then
        kill $MLX_PID
    fi
    echo "🛑 Stopping Docker Containers..."
    docker-compose down
    exit
}

# Trap SIGINT (Ctrl+C)
trap cleanup SIGINT

echo "🚀 Starting SoftSkill v2 Stack..."

# 0. Auto-Download Model if Missing
MODEL_DIR="ai_engine/models/softskill-llama3.2-3b"
REPO_ID="KingDor/softskill-llama3.2-3b"

if [ ! -f "$MODEL_DIR/config.json" ]; then
    echo "📥 Model not found locally. Downloading from Hugging Face ($REPO_ID)..."
    mkdir -p "$MODEL_DIR"
    # Use huggingface-cli to download
    huggingface-cli download $REPO_ID --local-dir $MODEL_DIR --local-dir-use-symlinks False
    echo "✅ Download Complete."
else
    echo "✅ Model found locally."
fi

# 1. Start MLX Server (Host)
echo "🧠 Booting AI Brain (MLX on M2)..."
python3 ai_engine/run_mlx_server.py --model ai_engine/models/softskill-llama3.2-3b --port 8081 --host 0.0.0.0 > mlx_server.log 2>&1 &
MLX_PID=$!

# Wait for MLX to be ready
echo "⏳ Waiting for Brain to load..."
sleep 5
# Optional: Check if port 8081 is listening
while ! lsof -i :8081 > /dev/null; do
    sleep 1
done
echo "✅ Brain is Online (PID: $MLX_PID)"

# 2. Start Docker Stack (Backend now runs in TypeScript via Dockerfile)
echo "🐳 Starting Backend & Frontend..."
docker-compose up --build

# Wait for docker to exit
wait
