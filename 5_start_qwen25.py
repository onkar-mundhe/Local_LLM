"""
Start Qwen2.5-0.5B server on port 7777
This model does NOT have thinking/reasoning - responds directly!
"""

import os
import subprocess
import sys
import platform
from pathlib import Path

def find_llama_server():
    """Find llama-server executable (cross-platform)"""
    is_windows = platform.system() == "Windows"
    
    if is_windows:
        # Windows: look for .exe files
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
                if file.is_file():
                    return str(file)
    else:
        # macOS/Linux: look for binary WITHOUT .exe extension
        possible_paths = [
            "llama-server",
            "llama-bin/llama-server",
            "llama-bin/build/bin/Release/llama-server",
            "llama.cpp/build/bin/Release/llama-server",
        ]
        
        for path in possible_paths:
            if os.path.exists(path) and not path.endswith('.exe'):
                return path
        
        llama_bin = Path("llama-bin")
        if llama_bin.exists():
            for file in llama_bin.rglob("llama-server"):
                if file.is_file() and not str(file).endswith('.exe'):
                    return str(file)
    
    return None

def start_server():
    print("=" * 50)
    print("Starting Qwen2.5-0.5B Server on Port 7777")
    print("(NO THINKING - Direct responses!)")
    print("=" * 50)
    print()
    
    # Configuration - Qwen2.5 (no thinking)
    model_path = "./models/Qwen2.5-0.5B-Instruct-Q4_K_M.gguf"
    port = 7777
    host = "127.0.0.1"
    context_size = 32768
    threads = os.cpu_count() or 4
    
    # Check if model exists
    if not os.path.exists(model_path):
        print(f"✗ Error: Model not found at {model_path}")
        print("Run: python 4_download_qwen25.py")
        return
    
    # Find llama-server
    server_path = find_llama_server()
    if not server_path:
        print("✗ Error: llama-server not found")
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

    # Make executable on macOS/Linux
    if platform.system() != "Windows":
        try:
            os.chmod(server_path, 0o755)
        except:
            pass

    # Build command - Qwen2.5 doesn't need reasoning flags
    cmd = [
        server_path,
        "--model", model_path,
        "--port", str(port),
        "--host", host,
        "--ctx-size", str(context_size),
        "--threads", str(threads),
        "--n-predict", "8192",  # Max output tokens (can be up to 32768)
        "--temp", "0.7",
        "--top-p", "0.9",
        "--top-k", "40",
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
