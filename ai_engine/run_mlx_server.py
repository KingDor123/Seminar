import os
import sys
import argparse
import subprocess

# Default Configuration
DEFAULT_MODEL_PATH = "ai_engine/models/softskill-llama3.2-3b"
DEFAULT_PORT = 8081
DEFAULT_HOST = "0.0.0.0"

def main():
    parser = argparse.ArgumentParser(description="Run MLX Server")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL_PATH, help="Path to the model")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to listen on")
    parser.add_argument("--host", type=str, default=DEFAULT_HOST, help="Host to bind to")
    args = parser.parse_args()

    print(f"🚀 Starting MLX Server...")
    print(f"   Model: {args.model}")
    print(f"   Host: {args.host}")
    print(f"   Port: {args.port}")
    
    # Construct the command
    # Using sys.executable ensures we use the same python environment
    cmd = [
        sys.executable, "-m", "mlx_lm.server",
        "--model", args.model,
        "--port", str(args.port),
        "--host", args.host
    ]
    
    try:
        # Use subprocess.call or run to execute and wait (so we can handle signals if needed)
        # But for a server script, we might want to just replace the process or wait.
        # os.execv would replace, but subprocess is fine.
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user.")
    except Exception as e:
        print(f"\n❌ Server failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()