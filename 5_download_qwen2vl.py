"""
Download Qwen2-VL-2B-Instruct-GGUF model from Hugging Face
This script downloads the Q8_0 quantized GGUF model files for vision/image support.

Two files are required:
  - Qwen2-VL-2B-Instruct-Q8_0.gguf     (main language model, ~1.65 GB)
  - mmproj-Qwen2-VL-2B-Instruct-Q8_0.gguf (multimodal projector, ~710 MB)

The files are placed inside "models/Model D (Vision)" so that llama-server's
--models-dir auto-detection picks up the mmproj file correctly.

Source: https://huggingface.co/ggml-org/Qwen2-VL-2B-Instruct-GGUF
"""

import os
from pathlib import Path

try:
    from huggingface_hub import hf_hub_download
except ImportError:
    print("Installing huggingface_hub...")
    os.system("pip install huggingface_hub")
    from huggingface_hub import hf_hub_download

# Configuration
REPO_ID = "ggml-org/Qwen2-VL-2B-Instruct-GGUF"
MODEL_FILES = [
    "Qwen2-VL-2B-Instruct-Q8_0.gguf",          # Main model (~1.65 GB)
    "mmproj-Qwen2-VL-2B-Instruct-Q8_0.gguf",    # Multimodal projector (~710 MB)
]

# Place inside a subdirectory so llama-server auto-associates the mmproj file
MODELS_DIR = Path(__file__).resolve().parent / "models" / "Model D (Vision)"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


def download_qwen2vl():
    print("=" * 60)
    print("  Downloading Qwen2-VL-2B-Instruct Q8_0 (Vision Model)")
    print("=" * 60)
    print()
    print(f"Repository : {REPO_ID}")
    print(f"Destination: {MODELS_DIR.absolute()}")
    print(f"Total size : ~2.36 GB (1.65 GB model + 710 MB projector)")
    print()

    for filename in MODEL_FILES:
        dest_file = MODELS_DIR / filename
        if dest_file.exists():
            print(f"[OK] Already exists: {filename}")
            print()
            continue

        print(f"Downloading {filename}...")
        try:
            file_path = hf_hub_download(
                repo_id=REPO_ID,
                filename=filename,
                local_dir=str(MODELS_DIR),
                local_dir_use_symlinks=False,
                resume_download=True,
            )
            print(f"[OK] Downloaded: {file_path}")
            print()
        except Exception as e:
            print(f"[FAIL] Error downloading {filename}: {e}")
            print()
            return

    print("=" * 60)
    print("  Download complete!")
    print(f"  Model files are in: {MODELS_DIR.absolute()}")
    print()
    print("  Next: run 'python start_server.py' to start the server.")
    print("  Select 'Model D (Vision)' in the UI dropdown to use it.")
    print("=" * 60)


if __name__ == "__main__":
    download_qwen2vl()
