"""
Download Qwen3-0.6B-GGUF model from Hugging Face
"""

import os
from huggingface_hub import hf_hub_download

def download_model():
    print("=" * 50)
    print("Downloading Qwen3-0.6B-Q4_K_M Model")
    print("=" * 50)
    print()
    
    # Create models directory
    os.makedirs("./models", exist_ok=True)
    
    # Model details
    repo_id = "unsloth/Qwen3-0.6B-GGUF"
    filename = "Qwen3-0.6B-Q4_K_M.gguf"
    
    print(f"Repository: {repo_id}")
    print(f"File: {filename}")
    print(f"Size: ~397 MB")
    print()
    print("Downloading...")
    print()
    
    try:
        model_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            local_dir="./models",
            resume_download=True
        )
        
        print()
        print("✓ Download complete!")
        print(f"Model saved to: {os.path.abspath(model_path)}")
        
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    try:
        download_model()
    except ImportError:
        print("Error: huggingface_hub not installed")
        print("Run: pip install huggingface_hub")