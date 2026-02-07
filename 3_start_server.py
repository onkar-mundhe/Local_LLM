"""
Start Qwen3-0.6B server on port 7777
"""

import os
import subprocess
import sys
from pathlib import Path

def find_llama_server():
    """Find llama-server.exe in various possible locations"""
    possible_paths = [
        "llama-server.exe",
        "llama-bin/llama-server.exe",
        "llama-bin/build/bin/Release/llama-server.exe",
        "llama.cpp/build/bin/Release/llama-server.exe",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # Search in llama-bin directory recursively
    llama_bin = Path("llama-bin")
    if llama_bin.exists():
        for file in llama_bin.rglob("llama-server.exe"):
            return str(file)
    
    return None

def start_server():
    print("=" * 50)
    print("Starting Qwen3-0.6B Server on Port 7777")
    print("=" * 50)
    print()
    
    # Configuration
    model_path = "./models/Qwen3-0.6B-Q4_K_M.gguf"
    port = 7777
    host = "127.0.0.1"
    context_size = 40960
    threads = os.cpu_count() or 4
    
    # Check if model exists
    if not os.path.exists(model_path):
        print(f"✗ Error: Model not found at {model_path}")
        print("Run: python 1_download_model.py")
        return
    
    # Find llama-server
    server_path = find_llama_server()
    if not server_path:
        print("✗ Error: llama-server.exe not found")
        print()
        print("Run: python 2_download_llama_binary.py")
        print("Or download manually from:")
        print("https://github.com/ggerganov/llama.cpp/releases")
        return
    
    print(f"Configuration:")
    print(f"  Server: {server_path}")
    print(f"  Model: {model_path}")
    print(f"  Port: {port}")
    print(f"  Host: {host}")
    print(f"  Context: {context_size} tokens")
    print(f"  Threads: {threads}")
    print()
    print(f"Starting server...")
    print(f"Access at: http://localhost:{port}")
    print(f"API: http://localhost:{port}/v1/chat/completions")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 50)
    print()
    
    # Use same UI as llama-cpp-custom; --path when present, --webui-config-file for appName.
    project_dir = Path(__file__).resolve().parent
    webui_config = project_dir / "webui-config.json"
    custom_public = project_dir / "llama-cpp-custom" / "tools" / "server" / "public"

    # Build command
    cmd = [
        server_path,
        "--model", model_path,
        "--port", str(port),
        "--host", host,
        "--ctx-size", str(context_size),
        "--threads", str(threads),
        "--n-predict", "1024",
        "--temp", "0.1",
        "--top-p", "0.8",
        "--top-k", "20",
        "--chat-template", "chatml",
        "--reasoning-budget", "0",
        "--reasoning-format", "none",
        "--webui-config-file", str(webui_config),
    ]
    if custom_public.is_dir() and (custom_public / "index.html").exists():
        cmd.extend(["--path", str(custom_public)])
    
    try:
        # Start the server
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
    except Exception as e:
        print(f"\n✗ Error starting server: {e}")

if __name__ == "__main__":
    start_server()