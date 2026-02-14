# RAG Service

**Author:** Kanwarraj Singh

Local RAG (Retrieval-Augmented Generation) service that integrates with your existing llama-cpp setup.

## Features

- **Document Management**: Upload PDF, DOCX, TXT, MD files
- **Vector Search**: LanceDB with local embeddings (all-MiniLM-L6-v2)
- **RAG-Enhanced Chat**: Automatic context injection into chat completions
- **OpenAI-Compatible API**: Works with existing llama-server setup
- **SQLite Tracking**: Document metadata management

## Quick Start

### 1. Install Dependencies

```bash
cd rag_service
pip install -r requirements.txt
```

### 2. Start the Service

```bash
python start_rag_service.py
```

The service runs on `http://127.0.0.1:8000`

### 3. Make sure llama-server is running

```bash
# In another terminal
cd ..
python 3_start_server.py  # or your preferred model
```

## API Endpoints

### Documents

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/documents/upload` | POST | Upload a document |
| `/documents` | GET | List all documents |
| `/documents/{id}` | GET | Get document details |
| `/documents/{id}` | DELETE | Delete a document |
| `/documents/text` | POST | Upload raw text |

### Search

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/search` | POST | Search knowledge base |

### Chat (RAG-Enhanced)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/chat/completions` | POST | RAG-enhanced chat (OpenAI-compatible) |
| `/v1/models` | GET | List available models |

## Usage Examples

### Upload a Document

```bash
curl -X POST "http://localhost:8000/documents/upload" \
  -F "file=@document.pdf"
```

### Search Knowledge Base

```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is machine learning?", "k": 5}'
```

### RAG Chat

```bash
curl -X POST "http://localhost:8000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "What does the document say about X?"}],
    "use_rag": true,
    "rag_k": 5
  }'
```

### Direct Chat (No RAG)

```bash
curl -X POST "http://localhost:8000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello!"}],
    "use_rag": false
  }'
```

## Configuration

Environment variables (optional):

| Variable | Default | Description |
|----------|---------|-------------|
| `RAG_SERVICE_PORT` | 8000 | Service port |
| `LLAMA_SERVER_URL` | http://127.0.0.1:7777 | llama-server URL |
| `EMBEDDING_MODEL` | all-MiniLM-L6-v2 | Embedding model |
| `EMBEDDING_DEVICE` | cpu | Device (cpu/cuda/mps) |
| `CHUNK_SIZE` | 500 | Document chunk size |
| `TOP_K_RESULTS` | 5 | Default search results |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      RAG Service                             │
│                    (Port 8000)                               │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  LanceDB    │  │   SQLite    │  │   Chat Proxy        │ │
│  │  (Vectors)  │  │  (Metadata) │  │   (RAG + Forward)   │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│         │                                    │              │
│         │          Embeddings                │              │
│         │     (all-MiniLM-L6-v2)             │              │
│         └────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ /v1/chat/completions
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    llama-server                              │
│                    (Port 7777)                               │
└─────────────────────────────────────────────────────────────┘
```

## Data Storage

- **Vectors**: `data/lancedb/` (LanceDB tables)
- **Metadata**: `data/documents.db` (SQLite)
