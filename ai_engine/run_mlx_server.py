import os
import sys

# Path to the newly trained model
MODEL_PATH = "ai_engine/models/softskill-llama3.2-3b"
PORT = 8081

def main():
    print(f"🚀 Starting MLX Server with model: {MODEL_PATH}")
    print(f"📡 Listening on port: {PORT}")
    
    # Construct the command
    # Using sys.executable ensures we use the same python environment
    cmd = f"{sys.executable} -m mlx_lm.server --model {MODEL_PATH} --port {PORT}"
    
    try:
        os.system(cmd)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped.")

if __name__ == "__main__":
    main()