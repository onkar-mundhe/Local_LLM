"""
Download LightOnOCR-1B-1025-GGUF model from Hugging Face
This script downloads the quantized GGUF model files needed for OCR inference.

The model files are placed inside a subdirectory "Model C (OCR)" so that
llama-server's --models-dir auto-detection picks up the mmproj file correctly.
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
REPO_ID = "ggml-org/LightOnOCR-1B-1025-GGUF"
MODEL_FILES = [
    "LightOnOCR-1B-1025-Q8_0.gguf",  # Main model file (805 MB)
    "mmproj-LightOnOCR-1B-1025-Q8_0.gguf"  # Multimodal projection (437 MB)
]

# Create the model subdirectory inside models/
# Using a subdirectory allows llama-server to auto-associate the mmproj file
MODELS_DIR = Path(__file__).resolve().parent.parent / "models" / "Model C (OCR)"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

print(f"Downloading model files from {REPO_ID}...")
print(f"Destination: {MODELS_DIR.absolute()}\n")

for filename in MODEL_FILES:
    dest_file = MODELS_DIR / filename
    if dest_file.exists():
        print(f"✓ Already exists: {dest_file}\n")
        continue

    print(f"Downloading {filename}...")
    try:
        file_path = hf_hub_download(
            repo_id=REPO_ID,
            filename=filename,
            local_dir=MODELS_DIR,
            local_dir_use_symlinks=False
        )
        print(f"✓ Downloaded: {file_path}\n")
    except Exception as e:
        print(f"✗ Error downloading {filename}: {e}\n")

print("Download complete!")
print(f"\nModel files are in: {MODELS_DIR.absolute()}")
