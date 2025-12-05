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

# 1. Start MLX Server (Host)
echo "🧠 Booting AI Brain (MLX on M2)..."
python3 -m mlx_lm.server --model ai_engine/models/softskill-llama3.2-3b --port 8081 --host 0.0.0.0 > mlx_server.log 2>&1 &
MLX_PID=$!

# Wait for MLX to be ready
echo "⏳ Waiting for Brain to load..."
sleep 5
# Optional: Check if port 8081 is listening
while ! lsof -i :8081 > /dev/null; do
    sleep 1
done
echo "✅ Brain is Online (PID: $MLX_PID)"

# 2. Start Docker Stack
echo "🐳 Starting Backend & Frontend..."
docker-compose up --build

# Wait for docker to exit
wait
