"""
Download llama.cpp pre-built binary for Windows
This script handles:
1. Detecting x64 vs ARM64 architecture
2. Downloading the correct CPU binary from GitHub releases
3. Extracting and flattening the directory structure
"""

import os
import platform
import shutil
import zipfile
from pathlib import Path


def get_architecture():
    """Detect Windows architecture"""
    machine = platform.machine().lower()
    if 'arm' in machine or 'aarch64' in machine:
        return "arm64", "ARM64 (Snapdragon / WoA)"
    else:
        return "x64", "x64 (Intel / AMD)"


def download_with_urllib(url, output_file):
    """Download file using urllib (built into Python, no extra dependencies)"""
    import urllib.request
    import ssl

    print(f"Downloading from: {url}")
    print("This may take a few minutes...")
    print()

    # Create SSL context that works on most Windows installations
    ctx = ssl.create_default_context()

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, context=ctx) as response:
            total_size = int(response.headers.get('Content-Length', 0))
            block_size = 8192
            downloaded = 0

            with open(output_file, 'wb') as f:
                while True:
                    chunk = response.read(block_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        mb = downloaded / (1024 * 1024)
                        total_mb = total_size / (1024 * 1024)
                        print(f"\rProgress: {percent:.1f}% ({mb:.1f}/{total_mb:.1f} MB)", end='', flush=True)
        print()
        return True
    except Exception as e:
        print(f"urllib download failed: {e}")
        return False


def download_with_requests(url, output_file):
    """Download file using requests library (fallback)"""
    try:
        import requests
    except ImportError:
        print("requests library not available, skipping fallback.")
        return False

    print(f"Downloading from: {url}")
    print("This may take a few minutes...")
    print()

    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        block_size = 8192
        downloaded = 0

        with open(output_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        mb = downloaded / (1024 * 1024)
                        total_mb = total_size / (1024 * 1024)
                        print(f"\rProgress: {percent:.1f}% ({mb:.1f}/{total_mb:.1f} MB)", end='', flush=True)
        print()
        return True
    except Exception as e:
        print(f"requests download failed: {e}")
        return False


def extract_zip(zip_file, extract_dir):
    """Extract zip file and flatten if needed"""
    print("Extracting...")

    # Remove existing directory
    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)

    os.makedirs(extract_dir, exist_ok=True)

    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)

    # Flatten if zip had a single top-level folder
    extract_path = Path(extract_dir)
    subdirs = [d for d in extract_path.iterdir() if d.is_dir()]

    if len(subdirs) == 1:
        subdir = subdirs[0]
        # Check if llama-server.exe is inside the subfolder
        if (subdir / "llama-server.exe").exists() or any(subdir.glob("llama-*.exe")):
            print("Flattening directory structure...")
            for item in subdir.iterdir():
                dest = extract_path / item.name
                if dest.exists():
                    if dest.is_file():
                        dest.unlink()
                    else:
                        shutil.rmtree(dest)
                shutil.move(str(item), str(dest))
            subdir.rmdir()

    # Clean up zip file
    os.remove(zip_file)
    print("✓ Extraction complete")


def download_llama_cpp():
    """Main download function for Windows"""
    print()
    print("=" * 55)
    print("  llama.cpp Binary Downloader for Windows")
    print("=" * 55)
    print()

    # Check if running on Windows
    if platform.system() != "Windows":
        print("⚠ Warning: This script is designed for Windows")
        print(f"  Detected OS: {platform.system()}")
        print("  For macOS, use: python 2_download_llama_macos.py")
        print()

    # Detect architecture
    arch, arch_name = get_architecture()
    print(f"Detected: {arch_name}")
    print()

    # Download URL - CPU build (works on all Windows machines)
    # Check https://github.com/ggml-org/llama.cpp/releases for alternatives
    # (CUDA, Vulkan, etc.)
    release = "b8036"
    url = f"https://github.com/ggml-org/llama.cpp/releases/download/{release}/llama-{release}-bin-win-cpu-{arch}.zip"

    zip_file = "llama-cpp-windows.zip"
    extract_dir = "llama-bin"

    # Clean up any existing failed download
    if os.path.exists(zip_file):
        os.remove(zip_file)

    # Download (try urllib first — built-in, then requests as fallback)
    success = download_with_urllib(url, zip_file)
    if not success:
        success = download_with_requests(url, zip_file)

    if not success:
        print()
        print("✗ Download failed!")
        print()
        print("Manual download instructions:")
        print(f"1. Open in browser: https://github.com/ggml-org/llama.cpp/releases")
        print(f"2. Find a release with 'win-cpu-{arch}.zip' binary")
        print(f"3. Download and extract to: {extract_dir}\\")
        return False

    # Verify it's actually a zip file (not an HTML error page)
    if not zipfile.is_zipfile(zip_file):
        print()
        print("✗ Downloaded file is not a valid zip!")
        print("  This usually means the release doesn't have pre-built Windows binaries.")
        print()
        print("Manual download:")
        print(f"1. Go to: https://github.com/ggml-org/llama.cpp/releases")
        print(f"2. Look for a release with 'bin-win-cpu-{arch}.zip' in the assets")
        print(f"3. Download and extract to llama-bin\\")
        os.remove(zip_file)
        return False

    print("✓ Download complete!")
    print()

    # Extract
    extract_zip(zip_file, extract_dir)

    print()
    print("=" * 55)
    print("✓ Setup complete!")
    print("=" * 55)
    print()
    print(f"Binaries installed to: {os.path.abspath(extract_dir)}")
    print()

    # Verify
    server_path = Path(extract_dir) / "llama-server.exe"
    if server_path.exists():
        print("✓ llama-server.exe found!")
        print()
        print("Next step: Run the server with:")
        print("  python start_server.py")
        print("  OR double-click Start_Qwen_Server.bat")
    else:
        # Check in subdirectories
        found = list(Path(extract_dir).rglob("llama-server.exe"))
        if found:
            print(f"✓ llama-server.exe found at: {found[0]}")
        else:
            print("⚠ llama-server.exe not found in expected location")
            print("Check the llama-bin folder contents")

    return True


if __name__ == "__main__":
    try:
        download_llama_cpp()
    except KeyboardInterrupt:
        print("\n\nDownload cancelled.")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nManual download: https://github.com/ggml-org/llama.cpp/releases")