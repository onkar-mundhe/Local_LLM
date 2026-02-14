"""
RAG Service - Main Application
Author: Kanwarraj Singh

FastAPI application for local RAG (Retrieval-Augmented Generation) service.
Integrates with llama-cpp server for LLM inference.

Features:
- Document upload and processing (PDF, DOCX, TXT, MD)
- Vector search using LanceDB
- Local embeddings using sentence-transformers
- RAG-enhanced chat completions
- OpenAI-compatible API
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import config
from app.database.sqlite_db import document_db
from app.database.vector_db import vector_db
from app.routes.documents import router as documents_router
from app.routes.chat import router as chat_router
from app.models.schemas import HealthResponse, StatsResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    logger.info("=" * 60)
    logger.info("RAG Service Starting")
    logger.info("=" * 60)
    logger.info(f"LLM Server: {config.LLAMA_SERVER_URL}")
    logger.info(f"Embedding Model: {config.EMBEDDING_MODEL}")
    logger.info(f"LanceDB Path: {config.LANCEDB_PATH}")
    logger.info(f"SQLite Path: {config.SQLITE_PATH}")
    
    # Initialize vector DB (loads embedding model)
    _ = vector_db.embeddings  # Trigger initialization
    logger.info("Embedding model loaded")
    
    doc_count = document_db.get_document_count()
    chunk_count = document_db.get_total_chunks()
    logger.info(f"Knowledge base: {doc_count} documents, {chunk_count} chunks")
    logger.info("=" * 60)
    
    yield
    
    # Shutdown
    logger.info("RAG Service Shutting Down")


# Create FastAPI app
app = FastAPI(
    title="RAG Service",
    description="Local RAG service with LanceDB and llama-cpp integration",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents_router)
app.include_router(chat_router)


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint"""
    return {
        "service": "RAG Service",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        service="rag-service",
        llama_server_url=config.LLAMA_SERVER_URL,
        embedding_model=config.EMBEDDING_MODEL,
        document_count=document_db.get_document_count(),
        chunk_count=document_db.get_total_chunks()
    )


@app.get("/stats", response_model=StatsResponse, tags=["Health"])
async def get_stats():
    """Get service statistics"""
    vector_stats = vector_db.get_table_stats()
    
    return StatsResponse(
        document_count=document_db.get_document_count(),
        chunk_count=document_db.get_total_chunks(),
        collections=[config.DEFAULT_COLLECTION],
        vector_db_stats=vector_stats
    )
