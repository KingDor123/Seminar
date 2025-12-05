import os
import sys

# Configuration
MODEL_NAME = "mlx-community/Llama-3.2-3B-Instruct-4bit" # Optimized for M2
DATA_PATH = "ai_engine/training/data"
ADAPTER_PATH = "ai_engine/adapters"
OUTPUT_MODEL_PATH = "ai_engine/models/softskill-llama3.2-3b"

def main():
    print(f"🚀 Starting Fine-Tuning on Apple Silicon (MLX)")
    print(f"Model: {MODEL_NAME}")
    
    # 1. Train
    # We use the python module execution to call mlx_lm.lora directly
    cmd = (
        f"{sys.executable} -m mlx_lm.lora "
        f"--model {MODEL_NAME} "
        f"--train "
        f"--data {DATA_PATH} "
        f"--iters 600 " # Increased iterations for better learning
        f"--batch-size 4 "
        f"--num-layers 16 " # Train more layers for better adaptation
        f"--adapter-path {ADAPTER_PATH} "
        f"--learning-rate 1e-4"
    )
    
    print(f"Executing: {cmd}")
    ret = os.system(cmd)
    
    if ret != 0:
        print("❌ Training Failed.")
        return
    
    print("\n✅ Training Complete.")
    print(f"Adapters saved to {ADAPTER_PATH}")
    
    # 2. Fuse (Optional - merging adapter back into base model)
    print("\n🔗 Fusing adapter into base model...")
    fuse_cmd = (
        f"{sys.executable} -m mlx_lm.fuse "
        f"--model {MODEL_NAME} "
        f"--adapter-path {ADAPTER_PATH} "
        f"--save-path {OUTPUT_MODEL_PATH}"
    )
    os.system(fuse_cmd)
    
    print(f"\n🎉 Model fused and saved to {OUTPUT_MODEL_PATH}")
    print("You can now serve this model using mlx-lm or convert to GGUF.")

if __name__ == "__main__":
    main()