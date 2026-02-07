"""
Download Qwen2.5-0.5B model (NO thinking/reasoning)
This model responds directly without chain-of-thought
"""

import os
import urllib.request
import sys

def download_qwen25():
    print("=" * 50)
    print("Downloading Qwen2.5-0.5B-Instruct (No Thinking)")
    print("=" * 50)
    print()
    
    # Create models directory
    os.makedirs("models", exist_ok=True)
    
    # Qwen2.5-0.5B-Instruct Q4_K_M - fast and no thinking
    model_url = "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf"
    model_path = "models/Qwen2.5-0.5B-Instruct-Q4_K_M.gguf"
    
    if os.path.exists(model_path):
        print(f"✓ Model already exists: {model_path}")
        return model_path
    
    print(f"Downloading from: {model_url}")
    print(f"Saving to: {model_path}")
    print()
    print("This may take a few minutes...")
    print()
    
    def progress_hook(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            percent = min(100, downloaded * 100 / total_size)
            mb_downloaded = downloaded / (1024 * 1024)
            mb_total = total_size / (1024 * 1024)
            sys.stdout.write(f"\rProgress: {percent:.1f}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)")
            sys.stdout.flush()
    
    try:
        urllib.request.urlretrieve(model_url, model_path, progress_hook)
        print()
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
    download_qwen25()
