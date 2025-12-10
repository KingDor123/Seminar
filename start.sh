#!/bin/bash

# Define cleanup function
cleanup() {
    echo ""
    echo "🛑 Stopping SoftSkill v2 Stack..."
    docker-compose down
    exit
}

# Trap SIGINT (Ctrl+C)
trap cleanup SIGINT

echo "🚀 Starting SoftSkill v2 Stack (Docker Only)..."

# Start Docker Stack
# The 'ollama' container inside docker-compose will handle the model download/serving.
docker-compose up --build

# Wait for docker to exit
wait