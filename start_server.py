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

def find_llama_server():
    """Find llama-server.exe"""
    possible_paths = [
        "llama-server.exe",
        "llama-bin/llama-server.exe",
        "llama-bin/build/bin/Release/llama-server.exe",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    llama_bin = Path("llama-bin")
    if llama_bin.exists():
        for file in llama_bin.rglob("llama-server.exe"):
            return str(file)
    
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
    
    # Models to probe for startup messages (router lists every .gguf under ./models)
    models = [
        ("models/Model A (non-thinking).gguf", "Model A (non-thinking)"),
        ("models/Model B (thinking).gguf", "Model B (thinking)"),
        ("models/qwen2-7b-instruct-q4_k_m.gguf", "Qwen2-7B-Instruct Q4_K_M"),
    ]
    
    # Check which models exist
    available_models = []
    for model_path, alias in models:
        if os.path.exists(model_path):
            available_models.append((model_path, alias))
            print(f"  ✓ Found: {alias} ({model_path})")
        else:
            print(f"  ✗ Missing: {alias} ({model_path})")
    
    if not available_models:
        print("\n✗ No models found! Please download models first.")
        return
    
    print()
    
    # Find server
    server_path = find_llama_server()
    if not server_path:
        print("✗ Error: llama-server.exe not found")
        return
    
    print(f"Server: {server_path}")
    print(f"Port: {port}")
    print(f"Models loaded: {len(available_models)}")
    print()
    print(f"Access UI at: http://localhost:{port}")
    print()
    print("In the UI, click the model dropdown to switch between models!")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)
    print()
    
    # Use same UI as llama-cpp-custom (shows appName from webui_settings in both places).
    # --path: serve from llama-cpp-custom/tools/server/public when present.
    # --webui-config-file: server sends webui_settings in /props (appName: WorkplaceSLM).
    project_dir = Path(__file__).resolve().parent
    webui_config = project_dir / "webui-config.json"
    models_preset = project_dir / "models-preset.ini"
    custom_public = project_dir / "llama-cpp-custom" / "tools" / "server" / "public"

    # Build command - router server mode with multiple models
    cmd = [
        server_path,
        "--port", str(port),
        "--host", host,
        "--threads", str(threads),
        "--n-predict", "8192",
        "--temp", "0.7",
        "--top-p", "0.9",
        "--models-dir", "./models",
        "--models-max", str(max(4, len(available_models))),
        "--webui-config-file", str(webui_config),
    ]
    if models_preset.exists():
        cmd.extend(["--models-preset", str(models_preset)])
    if custom_public.is_dir() and (custom_public / "index.html").exists():
        cmd.extend(["--path", str(custom_public)])

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
