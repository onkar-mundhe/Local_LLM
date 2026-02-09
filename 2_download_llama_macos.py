"""
Download llama.cpp pre-built binary for macOS
This script handles:
1. Detecting Apple Silicon vs Intel Mac
2. Downloading the correct binary
3. Removing macOS quarantine flags (fixes "Apple cannot verify" error)
4. Making binaries executable
"""

import os
import platform
import subprocess
import sys
from pathlib import Path


def get_architecture():
    """Detect Mac architecture"""
    machine = platform.machine().lower()
    if 'arm' in machine or 'aarch64' in machine:
        return "arm64", "Apple Silicon (M1/M2/M3/M4)"
    else:
        return "x64", "Intel Mac"


def download_with_curl(url, output_file):
    """Download file using curl (built into macOS)"""
    print(f"Downloading from: {url}")
    print("This may take a few minutes...")
    print()
    
    try:
        result = subprocess.run(
            ["curl", "-L", "-o", output_file, "--progress-bar", url],
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"curl failed: {e}")
        return False
    except FileNotFoundError:
        print("curl not found, trying Python requests...")
        return False


def download_with_requests(url, output_file):
    """Download file using Python requests library"""
    try:
        import requests
    except ImportError:
        print("requests library not installed.")
        print("Run: pip3 install requests")
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
        print(f"Download failed: {e}")
        return False


def remove_quarantine(path):
    """Remove macOS quarantine attribute (fixes 'Apple cannot verify' error)"""
    print("Removing macOS quarantine flags...")
    try:
        subprocess.run(["xattr", "-cr", path], check=True)
        print("✓ Quarantine flags removed")
        return True
    except Exception as e:
        print(f"Warning: Could not remove quarantine: {e}")
        print("You may need to run: xattr -cr llama-bin")
        return False


def make_executable(path):
    """Make binaries executable"""
    print("Making binaries executable...")
    bin_path = Path(path)
    count = 0
    for binary in bin_path.rglob("llama-*"):
        if binary.is_file():
            os.chmod(binary, 0o755)
            count += 1
    print(f"✓ Made {count} binaries executable")


def extract_zip(zip_file, extract_dir):
    """Extract zip file"""
    import zipfile
    import shutil
    
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
    
    # Check if there's only one subfolder and llama-server is inside it
    if len(subdirs) == 1:
        subdir = subdirs[0]
        # Check if the binary is inside the subfolder
        if (subdir / "llama-server").exists() or any(subdir.glob("llama-*")):
            print(f"Flattening directory structure...")
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
    """Main download function for macOS"""
    print()
    print("=" * 55)
    print("  llama.cpp Binary Downloader for macOS")
    print("=" * 55)
    print()
    
    # Check if running on macOS
    if platform.system() != "Darwin":
        print("⚠ Warning: This script is designed for macOS")
        print(f"  Detected OS: {platform.system()}")
        print()
    
    # Detect architecture
    arch, arch_name = get_architecture()
    print(f"Detected: {arch_name} ({arch})")
    print()
    
    # Download URL - use a known working release with macOS binaries
    # Not all releases have pre-built binaries, so we use a tested one
    # Check https://github.com/ggml-org/llama.cpp/releases for alternatives
    release = "b3963"  # Known working release with macOS binaries
    url = f"https://github.com/ggml-org/llama.cpp/releases/download/{release}/llama-{release}-bin-macos-{arch}.zip"
    
    zip_file = "llama-cpp-macos.zip"
    extract_dir = "llama-bin"
    
    # Clean up any existing failed download
    if os.path.exists(zip_file):
        os.remove(zip_file)
    
    # Download
    success = download_with_curl(url, zip_file)
    if not success:
        success = download_with_requests(url, zip_file)
    
    if not success:
        print()
        print("✗ Download failed!")
        print()
        print("Manual download instructions:")
        print(f"1. Open in browser: https://github.com/ggml-org/llama.cpp/releases")
        print(f"2. Find a release with 'macos-{arch}.zip' binary")
        print(f"3. Download and extract to: {extract_dir}/")
        print(f"4. Run: xattr -cr {extract_dir}")
        print(f"5. Run: chmod +x {extract_dir}/llama-server")
        return False
    
    # Verify it's actually a zip file (not an HTML error page)
    import zipfile
    if not zipfile.is_zipfile(zip_file):
        print()
        print("✗ Downloaded file is not a valid zip!")
        print("  This usually means the release doesn't have pre-built macOS binaries.")
        print()
        print("Manual download:")
        print(f"1. Go to: https://github.com/ggml-org/llama.cpp/releases")
        print(f"2. Look for a release with 'bin-macos-{arch}.zip' in the assets")
        print(f"3. Download, extract to llama-bin/, then run:")
        print(f"   xattr -cr llama-bin && chmod +x llama-bin/llama-server")
        os.remove(zip_file)
        return False
    
    print("✓ Download complete!")
    print()
    
    # Extract
    extract_zip(zip_file, extract_dir)
    
    # Remove quarantine (IMPORTANT - fixes "Apple cannot verify" error)
    remove_quarantine(extract_dir)
    
    # Make executable
    make_executable(extract_dir)
    
    print()
    print("=" * 55)
    print("✓ Setup complete!")
    print("=" * 55)
    print()
    print(f"Binaries installed to: {os.path.abspath(extract_dir)}")
    print()
    
    # Verify
    server_path = Path(extract_dir) / "llama-server"
    if server_path.exists():
        print("✓ llama-server found!")
        print()
        print("Next step: Run the server with:")
        print("  python3 start_server.py")
    else:
        # Check in subdirectories
        found = list(Path(extract_dir).rglob("llama-server"))
        if found:
            print(f"✓ llama-server found at: {found[0]}")
        else:
            print("⚠ llama-server not found in expected location")
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
