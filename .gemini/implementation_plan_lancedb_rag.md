# Implementation Plan: LanceDB RAG Integration

## Overview

Add a **LanceDB-based RAG (Retrieval-Augmented Generation)** system to the existing Local_SLM project.
This enables users to upload documents of **any size**, index them, and ask questions with intelligent
context retrieval — all **100% offline**.

## Current Architecture

```
Local_SLM/
├── start_server.py              ← Starts llama.cpp server (port 7777)
├── models/                      ← GGUF models (Model A, B, C)
├── models-preset.ini            ← Model preload config
├── llama-bin/                   ← llama.cpp binary
├── llama-cpp-custom/            ← Custom web UI (Svelte)
│   └── tools/server/webui/
│       └── src/lib/
│           ├── services/chat.ts        ← Sends messages to llama.cpp
│           ├── services/database.ts    ← IndexedDB via Dexie
│           ├── utils/pdf-processing.ts ← PDF.js text extraction (browser)
│           └── utils/convert-files-to-extra.ts ← File → message extra
├── webui-config.json            ← UI config (appName: "WorkplaceSLM")
└── requirements.txt             ← huggingface-hub, requests, pywin32
```

**Current PDF flow:** Browser (PDF.js) → Extract ALL text → Stuff into prompt → Fails if > 32K tokens

## Target Architecture

```
Local_SLM/
├── start_server.py              ← Modified: also starts RAG service
├── rag_service/                 ← NEW: Python RAG backend
│   ├── __init__.py
│   ├── server.py                ← FastAPI server (port 8877)
│   ├── indexer.py               ← Document ingestion + chunking
│   ├── embeddings.py            ← Embedding model wrapper
│   ├── retriever.py             ← LanceDB search
│   ├── document_processor.py    ← PDF/DOCX/TXT text extraction
│   └── config.py                ← Configuration
├── data/                        ← NEW: Persistent storage
│   ├── lance/                   ← LanceDB vector store
│   ├── uploads/                 ← Original uploaded files
│   └── app.db                   ← SQLite metadata
├── embedding_model/             ← NEW: Downloaded embedding model
├── download_embedding_model.py  ← NEW: One-time model download script
├── requirements.txt             ← Updated with new dependencies
└── (everything else stays the same)
```

**New PDF flow:** Upload to Python → PyMuPDF extracts text → Chunk → Embed → Store in LanceDB →
On query: search top 5 chunks → Send only relevant context to llama.cpp → ✅ Works for ANY size PDF

---

## Phases

### Phase 1: Foundation — Dependencies & Embedding Model
### Phase 2: Core RAG Backend — Python Service
### Phase 3: Document Processing Pipeline
### Phase 4: LanceDB Storage & Search
### Phase 5: FastAPI Server (REST API)
### Phase 6: Web UI Integration
### Phase 7: Start Script Integration
### Phase 8: Testing & Polish

---

## Phase 1: Foundation — Dependencies & Embedding Model

### Goal
Set up all dependencies and download the embedding model.

### Tasks

#### 1.1 Update `requirements.txt`

Add the following dependencies:

```
# Existing
huggingface-hub
requests
pywin32; sys_platform == 'win32'

# NEW — RAG Service
fastapi                    # REST API framework
uvicorn                    # ASGI server for FastAPI
lancedb                    # Vector database (embedded, serverless)
sentence-transformers      # Embedding model runtime
PyMuPDF                    # PDF text extraction (fitz)
python-docx                # DOCX text extraction
openpyxl                   # XLSX text extraction
python-multipart           # File upload support for FastAPI
```

#### 1.2 Create `download_embedding_model.py`

Script to download the embedding model once (similar to `1_download_model.py`):

```python
# Downloads: all-MiniLM-L6-v2 (~80MB)
# Saves to: ./embedding_model/
# Run once, then works offline forever
```

**Model choice:** `all-MiniLM-L6-v2`
- Size: ~80MB
- Dimensions: 384
- Speed: ~14,000 sentences/sec on CPU
- Quality: Excellent for English text search
- License: Apache 2.0

#### 1.3 Create `data/` directory structure

```
data/
├── lance/         ← LanceDB will create files here
├── uploads/       ← Original uploaded files stored here
└── app.db         ← SQLite for metadata (created by code)
```

### Files Changed/Created
| File | Action |
|------|--------|
| `requirements.txt` | MODIFY — add new dependencies |
| `download_embedding_model.py` | CREATE — embedding model download script |
| `data/` | CREATE — directory structure |

---

## Phase 2: Core RAG Backend — Configuration & Embeddings

### Goal
Create the RAG service package with config and embedding model wrapper.

### Tasks

#### 2.1 Create `rag_service/config.py`

Configuration constants:

```python
# Paths
DATA_DIR = "./data"
LANCE_DIR = "./data/lance"
UPLOADS_DIR = "./data/uploads"
SQLITE_DB = "./data/app.db"
EMBEDDING_MODEL_DIR = "./embedding_model"

# Chunking
CHUNK_SIZE = 500          # tokens per chunk
CHUNK_OVERLAP = 50        # overlapping tokens between chunks

# Search
TOP_K = 5                 # number of chunks to retrieve
EMBEDDING_DIM = 384       # all-MiniLM-L6-v2 output dimensions

# Server
RAG_PORT = 8877
RAG_HOST = "127.0.0.1"
```

#### 2.2 Create `rag_service/embeddings.py`

Wrapper around sentence-transformers:

```python
class EmbeddingService:
    def __init__(self, model_path: str):
        """Load embedding model from local path (offline)"""
        self.model = SentenceTransformer(model_path)
    
    def embed_text(self, text: str) -> list[float]:
        """Convert single text to 384-dim vector"""
    
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Convert multiple texts to vectors (batched for speed)"""
```

### Files Created
| File | Action |
|------|--------|
| `rag_service/__init__.py` | CREATE |
| `rag_service/config.py` | CREATE |
| `rag_service/embeddings.py` | CREATE |

---

## Phase 3: Document Processing Pipeline

### Goal
Build text extraction and chunking for PDF, DOCX, TXT, XLSX files.

### Tasks

#### 3.1 Create `rag_service/document_processor.py`

Text extraction from various file types:

```python
class DocumentProcessor:
    @staticmethod
    def extract_text(file_path: str) -> str:
        """Route to correct extractor based on file extension"""
    
    @staticmethod
    def extract_pdf(file_path: str) -> str:
        """Use PyMuPDF (fitz) to extract text from PDF"""
    
    @staticmethod
    def extract_docx(file_path: str) -> str:
        """Use python-docx to extract text from Word docs"""
    
    @staticmethod
    def extract_txt(file_path: str) -> str:
        """Read plain text files"""
    
    @staticmethod
    def extract_xlsx(file_path: str) -> str:
        """Use openpyxl to extract text from Excel files"""
```

#### 3.2 Create `rag_service/indexer.py`

Chunking + indexing pipeline:

```python
class DocumentIndexer:
    def __init__(self, embedding_service, lance_db):
        self.embeddings = embedding_service
        self.db = lance_db
    
    def chunk_text(self, text: str, chunk_size: int, overlap: int) -> list[str]:
        """Split text into overlapping chunks"""
        # Uses token-aware splitting (not just character count)
    
    def index_document(self, file_path: str, filename: str) -> dict:
        """Full pipeline: extract → chunk → embed → store"""
        # 1. Extract text from file
        # 2. Split into chunks
        # 3. Generate embeddings for each chunk
        # 4. Store in LanceDB
        # 5. Save metadata in SQLite
        # Returns: { doc_id, filename, num_chunks, status }
    
    def delete_document(self, doc_id: str):
        """Remove document and all its chunks from LanceDB"""
```

### Files Created
| File | Action |
|------|--------|
| `rag_service/document_processor.py` | CREATE |
| `rag_service/indexer.py` | CREATE |

---

## Phase 4: LanceDB Storage & Search

### Goal
Set up LanceDB for vector storage and implement semantic search.

### Tasks

#### 4.1 Create `rag_service/retriever.py`

LanceDB operations:

```python
class DocumentRetriever:
    def __init__(self, embedding_service):
        self.db = lancedb.connect(LANCE_DIR)
        self.embeddings = embedding_service
        self._ensure_table()
    
    def _ensure_table(self):
        """Create documents table if not exists"""
        # Schema:
        # - id: str (chunk ID)
        # - doc_id: str (parent document ID)
        # - text: str (chunk text)
        # - vector: vector(384) (embedding)
        # - source: str (filename)
        # - page: int (page number, if applicable)
        # - chunk_index: int (position within document)
        # - created_at: str (timestamp)
    
    def add_chunks(self, chunks: list[dict]):
        """Add chunks with vectors to LanceDB"""
    
    def search(self, query: str, top_k: int = 5, filter_doc_ids: list = None) -> list[dict]:
        """Semantic search: query → embed → find similar chunks"""
        # 1. Embed the query text
        # 2. Search LanceDB for nearest vectors
        # 3. Return top_k results with text, source, score
    
    def delete_by_doc_id(self, doc_id: str):
        """Delete all chunks for a document"""
    
    def list_documents(self) -> list[dict]:
        """Get unique document list with chunk counts"""
    
    def get_stats(self) -> dict:
        """Get total documents, chunks, storage size"""
```

#### 4.2 SQLite metadata storage

SQLite tables for document metadata (stored in `data/app.db`):

```sql
CREATE TABLE documents (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER,
    file_type TEXT,           -- pdf, docx, txt, xlsx
    num_chunks INTEGER,
    num_pages INTEGER,
    status TEXT DEFAULT 'indexed',  -- indexed, error
    created_at TEXT,
    updated_at TEXT
);
```

### Files Created
| File | Action |
|------|--------|
| `rag_service/retriever.py` | CREATE |

---

## Phase 5: FastAPI Server (REST API)

### Goal
Create the REST API that the web UI will call.

### Tasks

#### 5.1 Create `rag_service/server.py`

FastAPI application with endpoints:

```
API Endpoints:
──────────────────────────────────────────────────────────────
POST   /api/rag/upload          Upload & index a document
GET    /api/rag/documents       List all indexed documents
DELETE /api/rag/documents/{id}  Delete a document
POST   /api/rag/search          Search for relevant chunks
GET    /api/rag/stats           Get storage statistics
GET    /api/rag/health          Health check
──────────────────────────────────────────────────────────────
```

**Endpoint details:**

```python
# POST /api/rag/upload
# Upload a file, extract text, chunk, embed, store
# Request: multipart/form-data (file)
# Response: { doc_id, filename, num_chunks, status }

# POST /api/rag/search
# Search indexed documents for relevant chunks
# Request: { "query": "What is the leave policy?", "top_k": 5 }
# Response: { "results": [{ "text": "...", "source": "policy.pdf", "score": 0.92 }] }

# GET /api/rag/documents
# List all indexed documents
# Response: { "documents": [{ "id": "...", "filename": "policy.pdf", "num_chunks": 42 }] }

# DELETE /api/rag/documents/{id}
# Delete a document and all its chunks
# Response: { "status": "deleted" }
```

#### 5.2 Add CORS middleware

Allow requests from the llama.cpp web UI (localhost:7777) to the RAG service (localhost:8877).

### Files Created
| File | Action |
|------|--------|
| `rag_service/server.py` | CREATE |

---

## Phase 6: Web UI Integration

### Goal
Modify the Svelte web UI to use the RAG service for document upload and context retrieval.

### Tasks

#### 6.1 Add RAG service client

Create a new service file in the web UI to communicate with the RAG API:

```
File: llama-cpp-custom/tools/server/webui/src/lib/services/rag.ts

class RagService:
    static async uploadDocument(file: File): Promise<UploadResult>
    static async searchDocuments(query: string, topK?: number): Promise<SearchResult[]>
    static async listDocuments(): Promise<Document[]>
    static async deleteDocument(docId: string): Promise<void>
    static async getStats(): Promise<RagStats>
    static async checkHealth(): Promise<boolean>
```

#### 6.2 Create RAG Documents Panel

New UI component: a sidebar panel or tab showing indexed documents:

```
┌─────────────────────────────────────┐
│  📚 Knowledge Base                   │
│                                     │
│  [+ Upload Document]                │
│                                     │
│  📄 company_policy.pdf    42 chunks │
│     Indexed 2 hours ago      [🗑️]   │
│                                     │
│  📄 employee_handbook.docx 128 chunks│
│     Indexed 1 day ago        [🗑️]   │
│                                     │
│  📄 meeting_notes.txt     15 chunks │
│     Indexed 3 days ago       [🗑️]   │
│                                     │
│  ─────────────────────────          │
│  Total: 3 docs, 185 chunks          │
│  Storage: 12.4 MB                   │
└─────────────────────────────────────┘
```

#### 6.3 Modify chat flow for RAG

Modify the chat store to:
1. **Before sending a message**, if RAG has indexed documents:
   - Call `POST /api/rag/search` with the user's question
   - Get top 5 relevant chunks
   - Prepend the chunks as context in the prompt
2. **Send to llama.cpp** with the relevant context only

Modified prompt format:

```
System: You are a helpful assistant. Use the following context to answer questions.

Context from indexed documents:
---
[Source: policy.pdf, Page 12]
Employees are entitled to 24 days of paid leave per year...

[Source: policy.pdf, Page 13]
Unused leave can be carried forward up to 10 days...

[Source: handbook.docx, Page 5]
Leave requests must be submitted 3 days in advance...
---

User: What is the leave policy?
```

#### 6.4 Add RAG toggle

Add a setting to enable/disable RAG search per conversation:
- Toggle in chat settings: "🔍 Search Knowledge Base"
- When ON: Every user message triggers a RAG search before sending to model
- When OFF: Normal chat without document search (current behavior)

### Files Changed/Created
| File | Action |
|------|--------|
| `.../services/rag.ts` | CREATE — RAG API client |
| `.../components/rag/` | CREATE — Knowledge Base UI components |
| `.../stores/chat.svelte.ts` | MODIFY — Add RAG search before sending |
| `.../stores/settings.svelte.ts` | MODIFY — Add RAG toggle setting |

---

## Phase 7: Start Script Integration

### Goal
Make the RAG service start automatically with the llama.cpp server.

### Tasks

#### 7.1 Modify `start_server.py`

Add RAG service startup alongside the existing llama.cpp server:

```python
def start_multi_model_server():
    # ... existing code ...
    
    # NEW: Start RAG service in background
    rag_process = start_rag_service()
    
    # Existing: Start llama.cpp server
    subprocess.run(cmd)
    
    # Cleanup
    rag_process.terminate()

def start_rag_service():
    """Start the RAG FastAPI service in background"""
    # Check if embedding model is downloaded
    # Start uvicorn on port 8877
    # Return process handle for cleanup
```

#### 7.2 Create startup banner

```
============================================================
  WORKPLACESLM — Multi-Model Server + RAG
  
  🤖 LLM Server:     http://localhost:7777  (llama.cpp)
  📚 RAG Service:     http://localhost:8877  (LanceDB)
  🔍 Embedding Model: all-MiniLM-L6-v2 (loaded)
  📄 Indexed Docs:    3 documents, 185 chunks
  
  Use the model dropdown to switch models!
  Upload documents in the Knowledge Base tab!
============================================================
```

### Files Changed
| File | Action |
|------|--------|
| `start_server.py` | MODIFY — add RAG service startup |

---

## Phase 8: Testing & Polish

### Goal
Test the full pipeline and handle edge cases.

### Tasks

#### 8.1 Test document ingestion
- [ ] Upload small PDF (1-5 pages) — verify chunking and indexing
- [ ] Upload large PDF (100+ pages) — verify it works without issues
- [ ] Upload DOCX, TXT, XLSX files
- [ ] Upload scanned PDF — verify graceful handling (no text extracted)
- [ ] Delete document — verify chunks removed from LanceDB

#### 8.2 Test search quality
- [ ] Ask question matching exact text in document
- [ ] Ask question with different wording (semantic search test)
- [ ] Ask question with no relevant documents — verify graceful response
- [ ] Test with multiple documents indexed

#### 8.3 Test edge cases
- [ ] Start server with no embedding model — show helpful error
- [ ] Start server with no indexed documents — RAG disabled gracefully
- [ ] Upload duplicate file — handle appropriately
- [ ] Upload very large file (500+ pages) — test memory usage
- [ ] Upload non-text file (image, video) — reject with clear message

#### 8.4 Performance optimization
- [ ] Batch embedding generation for chunked documents
- [ ] Lazy-load embedding model (only when first document uploaded)
- [ ] Index progress feedback in UI (for large documents)

---

## Summary — All Files to Create/Modify

| # | File | Action | Phase |
|---|------|--------|-------|
| 1 | `requirements.txt` | MODIFY | 1 |
| 2 | `download_embedding_model.py` | CREATE | 1 |
| 3 | `data/` directory | CREATE | 1 |
| 4 | `rag_service/__init__.py` | CREATE | 2 |
| 5 | `rag_service/config.py` | CREATE | 2 |
| 6 | `rag_service/embeddings.py` | CREATE | 2 |
| 7 | `rag_service/document_processor.py` | CREATE | 3 |
| 8 | `rag_service/indexer.py` | CREATE | 3 |
| 9 | `rag_service/retriever.py` | CREATE | 4 |
| 10 | `rag_service/server.py` | CREATE | 5 |
| 11 | `.../services/rag.ts` | CREATE | 6 |
| 12 | `.../components/rag/` (multiple) | CREATE | 6 |
| 13 | `.../stores/chat.svelte.ts` | MODIFY | 6 |
| 14 | `.../stores/settings.svelte.ts` | MODIFY | 6 |
| 15 | `start_server.py` | MODIFY | 7 |

## Dependencies to Install (One-time)

| Package | Size | Purpose |
|---------|------|---------|
| `fastapi` | ~2MB | REST API framework |
| `uvicorn` | ~1MB | ASGI server |
| `lancedb` | ~150MB | Vector database |
| `sentence-transformers` | ~100MB | Embedding model runtime |
| `PyMuPDF` | ~15MB | PDF text extraction |
| `python-docx` | ~1MB | DOCX text extraction |
| `openpyxl` | ~5MB | XLSX text extraction |
| `python-multipart` | ~1MB | File upload support |
| `all-MiniLM-L6-v2` model | ~80MB | Embedding model weights |
| **Total** | **~355MB** | **One-time download** |

## Estimated Implementation Effort

| Phase | Description | Estimated Effort |
|-------|-------------|-----------------|
| 1 | Dependencies & Model | ~30 min |
| 2 | Config & Embeddings | ~30 min |
| 3 | Document Processing | ~45 min |
| 4 | LanceDB Storage & Search | ~45 min |
| 5 | FastAPI Server | ~1 hour |
| 6 | Web UI Integration | ~2 hours |
| 7 | Start Script Integration | ~30 min |
| 8 | Testing & Polish | ~1 hour |
| **Total** | | **~7 hours** |
