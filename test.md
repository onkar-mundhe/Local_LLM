# 1. Go to project folder
cd ~/Desktop/Qwen   # (or wherever the project is)

# 2. Completely delete llama-bin
rm -rf llama-bin

# 3. Create fresh folder
mkdir llama-bin

# 4. Download macOS binary directly (Apple Silicon M1/M2/M3)
curl -L "https://github.com/ggml-org/llama.cpp/releases/download/b5604/llama-b5604-bin-macos-arm64.zip" -o llama.zip

# OR for Intel Mac, use this instead:
# curl -L "https://github.com/ggml-org/llama.cpp/releases/download/b5604/llama-b5604-bin-macos-x64.zip" -o llama.zip

# 5. Unzip
unzip llama.zip -d llama-bin

# 6. Check what's inside
ls -la llama-bin/