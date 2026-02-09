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
    # Detect OS - use .exe on Windows, no extension on macOS/Linux
    is_windows = platform.system() == "Windows"
    
    if is_windows:
        # Windows: look for .exe files
        possible_paths = [
            "llama-server.exe",
            "llama-bin/llama-server.exe",
            "llama-bin/bin/llama-server.exe",
            "llama-bin/build/bin/Release/llama-server.exe",
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # Recursive search for .exe
        llama_bin = Path("llama-bin")
        if llama_bin.exists():
            for file in llama_bin.rglob("llama-server.exe"):
                if file.is_file():
                    return str(file)
    else:
        # macOS/Linux: look for binary WITHOUT .exe extension
        possible_paths = [
            "llama-server",
            "llama-bin/llama-server",
            "llama-bin/bin/llama-server",
            "llama-bin/build/bin/llama-server",
            "llama-bin/build/bin/Release/llama-server",
            "llama.cpp/build/bin/Release/llama-server",
        ]
        
        for path in possible_paths:
            # Make sure it's not the .exe file!
            if os.path.exists(path) and not path.endswith('.exe'):
                return path
        
        # Recursive search - find llama-server but NOT llama-server.exe
        llama_bin = Path("llama-bin")
        if llama_bin.exists():
            for file in llama_bin.rglob("*"):
                # Look for llama-server binary (exact name match, not .exe)
                if file.is_file() and file.name == "llama-server":
                    return str(file)
    
    # Debug: show what's in llama-bin if not found
    llama_bin = Path("llama-bin")
    if llama_bin.exists():
        print("Debug: Contents of llama-bin folder:")
        for item in llama_bin.rglob("*"):
            if item.is_file():
                print(f"  - {item}")
    
    return None

def start_multi_model_server():
    print()
    print("=" * 60)
    print("  MULTI-MODEL QWEN SERVER")
    print("  Switch models directly in the Web UI!")
    print("=" * 60)
    print()
    
    # Configuration
    port = 7777
    host = "127.0.0.1"
    threads = os.cpu_count() or 4
    context_size = 32768
    
    # Models to check
    model_configs = [
        ("models/Model A (non-thinking).gguf", "Model A - Non-thinking (direct responses)"),
        ("models/Model B (thinking).gguf", "Model B - Thinking (chain-of-thought)"),
        ("models/Qwen3-0.6B-Q4_K_M.gguf", "Qwen3 0.6B"),
        ("models/Qwen2.5-0.5B-Instruct-Q4_K_M.gguf", "Qwen2.5 0.5B Instruct"),
    ]
    
    # Find available models
    available_models = []
    print("Checking for models...")
    for path, name in model_configs:
        if os.path.exists(path):
            available_models.append((path, name))
            print(f"  ✓ Found: {name}")
        else:
            print(f"  ✗ Not found: {name}")
    
    # Also check for any other .gguf files in models folder
    models_dir = Path("models")
    if models_dir.exists():
        known_paths = [p for p, _ in model_configs]
        for gguf in models_dir.glob("*.gguf"):
            if str(gguf) not in known_paths:
                available_models.append((str(gguf), gguf.stem))
                print(f"  ✓ Found: {gguf.stem}")
    
    if not available_models:
        print("\n✗ No models found! Please download a model first.")
        print("Run: python 1_download_model.py")
        return
    
    print()
    
    # Model selection
    if len(available_models) == 1:
        model_path, model_name = available_models[0]
        print(f"Using: {model_name}")
    else:
        print("=" * 50)
        print("SELECT A MODEL:")
        print("=" * 50)
        for i, (path, name) in enumerate(available_models, 1):
            print(f"  [{i}] {name}")
        print()
        
        while True:
            try:
                choice = input(f"Enter choice (1-{len(available_models)}) or press Enter for [1]: ").strip()
                if choice == "":
                    choice = 1
                else:
                    choice = int(choice)
                
                if 1 <= choice <= len(available_models):
                    model_path, model_name = available_models[choice - 1]
                    break
                else:
                    print(f"Please enter a number between 1 and {len(available_models)}")
            except ValueError:
                print("Please enter a valid number")
            except KeyboardInterrupt:
                print("\n\nCancelled.")
                return
        
        print()
        print(f"Selected: {model_name}")
    
    print()
    
    # Find server
    server_path = find_llama_server()
    if not server_path:
        print("✗ Error: llama-server not found")
        return
    
    print(f"Server: {server_path}")
    print(f"Model: {model_path}")
    print(f"Port: {port}")
    print()
    print(f"Access UI at: http://localhost:{port}")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)
    print()

    # Paths for optional features
    project_dir = Path(__file__).resolve().parent
    webui_config = project_dir / "webui-config.json"
    custom_public = project_dir / "llama-cpp-custom" / "tools" / "server" / "public"

    # Make executable on macOS/Linux
    if platform.system() != "Windows":
        try:
            os.chmod(server_path, 0o755)
        except:
            pass

    # Build command - using core arguments compatible with all llama-server versions
    # Note: --webui-config-file and --path are only available in newer versions
    cmd = [
        server_path,
        "--model", model_path,
        "--port", str(port),
        "--host", host,
        "--threads", str(threads),
        "--ctx-size", str(context_size),
        "--n-predict", "8192",
    ]

    url = f"http://localhost:{port}"
    opened = [False]

    def open_browser_once():
        time.sleep(10)
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

if __name__ == "__main__":
    start_multi_model_server()
