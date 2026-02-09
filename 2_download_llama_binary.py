"""
Download llama.cpp pre-built binary for macOS
"""

import os
import platform
import shutil
import zipfile
import requests
from pathlib import Path

def download_llama_cpp():
    print("=" * 50)
    print("Downloading llama.cpp binary for macOS")
    print("=" * 50)
    print()
    
    # Detect architecture
    machine = platform.machine().lower()
    if 'arm' in machine or 'aarch64' in machine:
        arch = "arm64"  # Apple Silicon (M1/M2/M3)
        print("Detected: Apple Silicon (ARM64)")
    else:
        arch = "x64"    # Intel Mac
        print("Detected: Intel Mac (x64)")
    print()
    
    # Use ggml-org/llama.cpp (has Qwen3 architecture support).
    # Latest at: https://github.com/ggml-org/llama.cpp/releases
    url = f"https://github.com/ggml-org/llama.cpp/releases/download/b7898/llama-b7898-bin-macos-{arch}.zip"
    
    zip_file = "llama-cpp.zip"
    extract_dir = "llama-bin"
    
    print("Downloading from GitHub releases...")
    print("This may take a few minutes...")
    print()
    
    try:
        # Download
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        block_size = 8192
        downloaded = 0
        
        with open(zip_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\rProgress: {percent:.1f}%", end='', flush=True)
        
        print("\n✓ Download complete!")
        
        # Extract
        print("Extracting...")
        os.makedirs(extract_dir, exist_ok=True)
        
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        # Clean up zip file
        os.remove(zip_file)
        
        # If zip had a single top-level folder, flatten so binaries are in llama-bin/
        extract_path = Path(extract_dir)
        subdirs = [d for d in extract_path.iterdir() if d.is_dir()]
        if len(subdirs) == 1 and not (extract_path / "llama-server").exists():
            subdir = subdirs[0]
            for f in subdir.iterdir():
                dest = extract_path / f.name
                if dest.exists():
                    if dest.is_file():
                        dest.unlink()
                    else:
                        shutil.rmtree(dest)
                shutil.move(str(f), str(dest))
            subdir.rmdir()
        
        # Make binaries executable
        for binary in extract_path.glob("llama-*"):
            if binary.is_file():
                os.chmod(binary, 0o755)
        
        print(f"✓ Extracted to: {os.path.abspath(extract_dir)}")
        print()
        print("Look for 'llama-server' in the extracted folder")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print()
        print("Manual download:")
        print("1. Visit: https://github.com/ggml-org/llama.cpp/releases")
        print(f"2. Download: llama-bXXXX-bin-macos-{arch}.zip (latest build)")
        print("3. Extract to llama-bin/ so llama-server is under llama-bin/")
        print("4. Run: chmod +x llama-bin/llama-server")

if __name__ == "__main__":
    try:
        download_llama_cpp()
    except ImportError as e:
        print(f"Error: Missing module - {e}")
        print("Run: pip install requests")