import os
from huggingface_hub import HfApi, create_repo

# Configuration
MODEL_PATH = "ai_engine/models/softskill-llama3.2-3b"
REPO_ID = "KingDor/softskill-llama3.2-3b" # Customize this!

def upload():
    print(f"🚀 Uploading {MODEL_PATH} to Hugging Face Hub ({REPO_ID})...")
    
    api = HfApi()
    
    # Create Repo if it doesn't exist
    try:
        create_repo(repo_id=REPO_ID, private=True, exist_ok=True)
        print("✅ Repository ready.")
    except Exception as e:
        print(f"⚠️ Repo creation note: {e}")

    # Upload Folder
    api.upload_folder(
        folder_path=MODEL_PATH,
        repo_id=REPO_ID,
        repo_type="model"
    )
    
    print("\n🎉 Upload Complete!")
    print(f"Your model is safe at: https://huggingface.co/{REPO_ID}")

if __name__ == "__main__":
    upload()
