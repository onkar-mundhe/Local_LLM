"""
Download Qwen2.5-0.5B model (NO thinking/reasoning)
This model responds directly without chain-of-thought
"""

import os
from huggingface_hub import hf_hub_download

def download_qwen25():
    print("=" * 50)
    print("Downloading Qwen2.5-0.5B-Instruct (No Thinking)")
    print("=" * 50)
    print()
    
    # Create models directory
    os.makedirs("models", exist_ok=True)
    
    # Model details - Qwen2.5-0.5B-Instruct Q4_K_M
    repo_id = "Qwen/Qwen2.5-0.5B-Instruct-GGUF"
    filename = "qwen2.5-0.5b-instruct-q4_k_m.gguf"
    local_filename = "Qwen2.5-0.5B-Instruct-Q4_K_M.gguf"
    model_path = f"models/{local_filename}"
    
    if os.path.exists(model_path):
        print(f"✓ Model already exists: {model_path}")
        return model_path
    
    print(f"Repository: {repo_id}")
    print(f"File: {filename}")
    print(f"Size: ~400 MB")
    print()
    print("Downloading... (this may take a few minutes)")
    print()
    
    try:
        downloaded_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            local_dir="./models",
            resume_download=True
        )
        
        # Rename to consistent naming if needed
        if os.path.exists(downloaded_path) and downloaded_path != model_path:
            actual_file = os.path.join("models", filename)
            if os.path.exists(actual_file) and actual_file != model_path:
                os.rename(actual_file, model_path)
        
        print()
        print(f"✓ Download complete: {model_path}")
        print()
        print("Next steps:")
        print("1. Update 3_start_server.py to use this model")
        print("2. Or run: python 5_start_qwen25.py")
        return model_path
        
    except Exception as e:
        print(f"\n✗ Download failed: {e}")
        return None

if __name__ == "__main__":
    try:
        download_qwen25()
    except ImportError:
        print("Error: huggingface_hub not installed")
        print("Run: pip install huggingface_hub")
