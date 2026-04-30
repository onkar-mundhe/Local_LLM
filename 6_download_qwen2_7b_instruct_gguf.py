"""
Download Qwen2-7B-Instruct GGUF from Hugging Face into ./models

Repository: Qwen/Qwen2-7B-Instruct-GGUF
Default file: qwen2-7b-instruct-q4_k_m.gguf (balanced size and quality)

Author: Onkar Mundhe
"""

import os
import sys

REPO_ID = "Qwen/Qwen2-7B-Instruct-GGUF"
FILENAME = "qwen2-7b-instruct-q4_k_m.gguf"


def download_model():
    print("=" * 50)
    print("Downloading Qwen2-7B-Instruct (GGUF)")
    print("=" * 50)
    print()

    os.makedirs("./models", exist_ok=True)

    print(f"Repository: {REPO_ID}")
    print(f"File: {FILENAME}")
    print(f"Target: ./models/{FILENAME}")
    print()
    print("Downloading (resume supported)...")
    print()

    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        print("Error: huggingface_hub not installed")
        print("Install: pip install huggingface_hub")
        sys.exit(1)

    try:
        model_path = hf_hub_download(
            repo_id=REPO_ID,
            filename=FILENAME,
            local_dir="./models",
            local_dir_use_symlinks=False,
        )
        print()
        print("Download complete.")
        print(f"Model path: {os.path.abspath(model_path)}")
        print()
        print(
            "Optional: other quantizations in the same repo, e.g. "
            "qwen2-7b-instruct-q5_k_m.gguf — download manually or change "
            "FILENAME in this script."
        )
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    download_model()
