"""
Start RAG Service
Author: Kanwarraj Singh

Simple startup script for the RAG service.
Run: python start_rag_service.py
"""

import os
import sys
from pathlib import Path

def main():
    print("=" * 60)
    print("Starting RAG Service")
    print("=" * 60)
    print()
    
    # Add app to path
    app_dir = Path(__file__).parent
    sys.path.insert(0, str(app_dir))
    
    # Import config
    from app.config import config
    
    print(f"Configuration:")
    print(f"  RAG Service: http://{config.RAG_SERVICE_HOST}:{config.RAG_SERVICE_PORT}")
    print(f"  LLM Server:  {config.LLAMA_SERVER_URL}")
    print(f"  Embedding:   {config.EMBEDDING_MODEL} (device: {config.EMBEDDING_DEVICE})")
    print(f"  LanceDB:     {config.LANCEDB_PATH}")
    print(f"  SQLite:      {config.SQLITE_PATH}")
    print()
    print("Endpoints:")
    print(f"  Documents:   http://{config.RAG_SERVICE_HOST}:{config.RAG_SERVICE_PORT}/documents")
    print(f"  Search:      http://{config.RAG_SERVICE_HOST}:{config.RAG_SERVICE_PORT}/search")
    print(f"  Chat (RAG):  http://{config.RAG_SERVICE_HOST}:{config.RAG_SERVICE_PORT}/v1/chat/completions")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)
    print()
    
    # Start server
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=config.RAG_SERVICE_HOST,
        port=config.RAG_SERVICE_PORT,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    main()
