"""
Multi-Model Qwen Server
Load multiple models and switch between them in the Web UI!
"""

import os
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

import platform

def find_llama_server():
    """Find llama-server executable (cross-platform)"""
    is_windows = platform.system() == "Windows"
    
    if is_windows:
        possible_paths = [
            "llama-server.exe",
            "llama-bin/llama-server.exe",
            "llama-bin/bin/llama-server.exe",
            "llama-bin/build/bin/Release/llama-server.exe",
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        llama_bin = Path("llama-bin")
        if llama_bin.exists():
            for file in llama_bin.rglob("llama-server.exe"):
                if file.is_file():
                    return str(file)
    else:
        possible_paths = [
            "llama-server",
            "llama-bin/llama-server",
            "llama-bin/bin/llama-server",
            "llama-bin/build/bin/llama-server",
            "llama-bin/build/bin/Release/llama-server",
            "llama.cpp/build/bin/Release/llama-server",
        ]
        
        for path in possible_paths:
            if os.path.exists(path) and not path.endswith('.exe'):
                return path
        
        llama_bin = Path("llama-bin")
        if llama_bin.exists():
            for file in llama_bin.rglob("*"):
                if file.is_file() and file.name == "llama-server":
                    return str(file)
    
    return None

def start_multi_model_server():
    print()
    print("=" * 60)
    print("  MULTI-MODEL QWEN SERVER")
    print("  Switch models directly in the Web UI dropdown!")
    print("=" * 60)
    print()
    
    # Configuration
    port = 7777
    host = "127.0.0.1"
    threads = os.cpu_count() or 4
    
    # Check models directory
    models_dir = Path("models")
    if not models_dir.exists():
        print("✗ Error: 'models' folder not found")
        print("Run: python 1_download_model.py")
        return
    
    # Count available models
    gguf_files = list(models_dir.glob("*.gguf"))
    if not gguf_files:
        print("✗ No .gguf models found in models/ folder")
        print("Run: python 1_download_model.py")
        return
    
    print(f"Found {len(gguf_files)} model(s):")
    for f in gguf_files:
        print(f"  ✓ {f.name}")
    print()
    
    # Find server
    server_path = find_llama_server()
    if not server_path:
        print("✗ Error: llama-server not found")
        print("Run: python 2_download_llama_macos.py (macOS)")
        print("Or:  python 2_download_llama_binary.py (Windows)")
        return
    
    # Make executable on macOS/Linux
    if platform.system() != "Windows":
        try:
            os.chmod(server_path, 0o755)
        except:
            pass
    
    print(f"Server: {server_path}")
    print(f"Models: {len(gguf_files)} loaded from ./models/")
    print(f"Port: {port}")
    print()
    print(f"Access UI at: http://localhost:{port}")
    print("Use the model dropdown in the UI to switch between models!")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)
    print()
    
    # Paths for UI customization
    project_dir = Path(__file__).resolve().parent
    webui_config = project_dir / "webui-config.json"
    custom_public = project_dir / "llama-cpp-custom" / "tools" / "server" / "public"

    # Build command - Multi-model mode with PRELOADING
    # Using --model for each file preloads them into memory at startup
    cmd = [
        server_path,
        "--port", str(port),
        "--host", host,
        "--threads", str(threads),
        "--n-predict", "8192",
    ]
    
    # Add each model explicitly to PRELOAD them (not lazy load)
    for model_file in gguf_files:
        cmd.extend(["--model", str(model_file)])
    
    # Add custom UI config if available
    if webui_config.exists():
        cmd.extend(["--webui-config-file", str(webui_config)])
    
    # Use custom UI if available
    if custom_public.is_dir() and (custom_public / "index.html").exists():
        cmd.extend(["--path", str(custom_public)])

    url = f"http://localhost:{port}"
    opened = [False]

    def open_browser_once():
        time.sleep(8)
        if not opened[0]:
            opened[0] = True
            try:
                webbrowser.open(url)
            except Exception:
                pass

    t = threading.Thread(target=open_browser_once, daemon=True)
    t.start()

    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
    except Exception as e:
        print(f"\nError: {e}")
        print("\nIf you see 'invalid argument', your llama-server version")
        print("may not support multi-model mode. Options:")
        print("1. Download a newer llama-server version")
        print("2. Use 3_start_server.py for single-model mode")

if __name__ == "__main__":
    start_multi_model_server()
