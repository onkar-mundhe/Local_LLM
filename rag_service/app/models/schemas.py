"""
Pydantic Schemas
Author: Kanwarraj Singh

Request/Response models for the RAG Service API.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────────────────────
# Document Schemas
# ─────────────────────────────────────────────────────────────────────────────

class DocumentResponse(BaseModel):
    """Response for a single document"""
    id: int
    filename: str
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    chunk_count: int = 0
    upload_date: Optional[str] = None
    status: str = "active"
    collection_name: str = "documents"
    enabled: bool = True


class DocumentListResponse(BaseModel):
    """Response for document list"""
    documents: List[DocumentResponse]
    total: int
    collection_name: Optional[str] = None


class DocumentUploadResponse(BaseModel):
    """Response after document upload"""
    success: bool
    id: int
    filename: str
    chunks: int
    message: str = "Document processed successfully"


class DocumentDeleteResponse(BaseModel):
    """Response after document deletion"""
    success: bool
    id: int
    message: str


class DocumentToggleRequest(BaseModel):
    """Request to toggle document enabled state"""
    enabled: bool = Field(..., description="Whether the document should be enabled for RAG queries")


class DocumentToggleResponse(BaseModel):
    """Response after toggling document enabled state"""
    success: bool
    id: int
    enabled: bool
    message: str


# ─────────────────────────────────────────────────────────────────────────────
# Search Schemas
# ─────────────────────────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    """Request for document search"""
    query: str = Field(..., description="Search query text")
    k: int = Field(default=5, ge=1, le=20, description="Number of results to return")
    collection_name: Optional[str] = Field(default=None, description="Collection to search in")
    sources: Optional[List[str]] = Field(default=None, description="Filter by source filenames")


class SearchResult(BaseModel):
    """Single search result"""
    content: str
    source: str
    page: int = 0
    chunk_index: int = 0
    score: float
    metadata: Dict[str, Any] = {}


class SearchResponse(BaseModel):
    """Response for search query"""
    query: str
    results: List[SearchResult]
    total: int
    context: Optional[str] = None  # Formatted context for LLM


# ─────────────────────────────────────────────────────────────────────────────
# Chat Schemas (OpenAI-compatible)
# ─────────────────────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    """Single chat message"""
    role: str = Field(..., description="Role: 'user', 'assistant', or 'system'")
    content: Union[str, List[Dict[str, Any]]] = Field(..., description="Message content")


class ChatCompletionRequest(BaseModel):
    """OpenAI-compatible chat completion request"""
    messages: List[ChatMessage]
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    stream: bool = False
    
    # RAG-specific options
    use_rag: bool = Field(default=True, description="Whether to use RAG context")
    rag_k: int = Field(default=5, description="Number of RAG results to include")
    rag_sources: Optional[List[str]] = Field(default=None, description="Filter RAG by sources")
    
    # Pass-through options for llama-server
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    repeat_penalty: Optional[float] = None


class ChatCompletionChoice(BaseModel):
    """Single completion choice"""
    index: int = 0
    message: ChatMessage
    finish_reason: str = "stop"


class ChatCompletionUsage(BaseModel):
    """Token usage statistics"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatCompletionResponse(BaseModel):
    """OpenAI-compatible chat completion response"""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: Optional[ChatCompletionUsage] = None
    
    # RAG-specific additions
    rag_context_used: bool = False
    rag_sources: Optional[List[str]] = None


# ─────────────────────────────────────────────────────────────────────────────
# Health/Stats Schemas
# ─────────────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    service: str = "rag-service"
    llama_server_url: str
    embedding_model: str
    document_count: int = 0
    chunk_count: int = 0


class StatsResponse(BaseModel):
    """Service statistics"""
    document_count: int
    chunk_count: int
    collections: List[str]
    vector_db_stats: Dict[str, Any]
