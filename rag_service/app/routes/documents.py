"""
Document Routes
Author: Kanwarraj Singh

API endpoints for document management (upload, list, delete).
"""

import logging
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query

from app.config import config
from app.database.sqlite_db import document_db
from app.services.document_processor import document_processor
from app.models.schemas import (
    DocumentResponse,
    DocumentListResponse,
    DocumentUploadResponse,
    DocumentDeleteResponse,
    DocumentToggleRequest,
    DocumentToggleResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    collection_name: Optional[str] = Form(default=None)
):
    """
    Upload and process a document.
    
    Supported formats: PDF, DOCX, TXT, MD
    
    The document will be:
    1. Loaded and parsed
    2. Split into chunks
    3. Embedded using local model
    4. Stored in LanceDB vector store
    5. Tracked in SQLite database
    """
    collection_name = collection_name or config.DEFAULT_COLLECTION
    
    # Validate file type
    if not document_processor.is_supported(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Supported: {list(document_processor.SUPPORTED_EXTENSIONS.keys())}"
        )
    
    try:
        doc_id, chunk_count = document_processor.process_file(
            file=file.file,
            filename=file.filename,
            collection_name=collection_name
        )
        
        return DocumentUploadResponse(
            success=True,
            id=doc_id,
            filename=file.filename,
            chunks=chunk_count,
            message=f"Document processed successfully: {chunk_count} chunks created"
        )
    
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process document: {str(e)}"
        )


@router.get("", response_model=DocumentListResponse)
@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    collection_name: Optional[str] = Query(default=None),
    status: str = Query(default="active")
):
    """
    List all documents in the knowledge base.
    
    Args:
        collection_name: Filter by collection (optional)
        status: Filter by status ('active' or 'deleted')
    """
    documents = document_db.get_all_documents(
        collection_name=collection_name,
        status=status
    )
    
    return DocumentListResponse(
        documents=[DocumentResponse(**doc) for doc in documents],
        total=len(documents),
        collection_name=collection_name
    )


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: int):
    """Get details of a specific document"""
    doc = document_db.get_document(doc_id)
    
    if not doc:
        raise HTTPException(
            status_code=404,
            detail=f"Document {doc_id} not found"
        )
    
    return DocumentResponse(**doc)


@router.delete("/{doc_id}", response_model=DocumentDeleteResponse)
async def delete_document(
    doc_id: int,
    collection_name: Optional[str] = Query(default=None)
):
    """
    Delete a document from the knowledge base.
    
    This removes the document from both the vector store and SQLite tracker.
    """
    collection_name = collection_name or config.DEFAULT_COLLECTION
    
    # Check if document exists
    doc = document_db.get_document(doc_id)
    if not doc:
        raise HTTPException(
            status_code=404,
            detail=f"Document {doc_id} not found"
        )
    
    success = document_processor.delete_document(doc_id, collection_name)
    
    if success:
        return DocumentDeleteResponse(
            success=True,
            id=doc_id,
            message=f"Document '{doc['filename']}' deleted successfully"
        )
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to delete document"
        )


@router.patch("/{doc_id}/toggle", response_model=DocumentToggleResponse)
async def toggle_document(doc_id: int, request: DocumentToggleRequest):
    """
    Toggle whether a document is enabled for RAG queries.
    
    When disabled, the document remains in the knowledge base but is
    excluded from search results and RAG context.
    """
    # Check if document exists
    doc = document_db.get_document(doc_id)
    if not doc:
        raise HTTPException(
            status_code=404,
            detail=f"Document {doc_id} not found"
        )
    
    success = document_db.toggle_document_enabled(doc_id, request.enabled)
    
    if success:
        state = "enabled" if request.enabled else "disabled"
        return DocumentToggleResponse(
            success=True,
            id=doc_id,
            enabled=request.enabled,
            message=f"Document '{doc['filename']}' {state} for knowledge search"
        )
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to update document state"
        )


@router.post("/text", response_model=DocumentUploadResponse)
async def upload_text(
    text: str = Form(...),
    source_name: str = Form(...),
    collection_name: Optional[str] = Form(default=None)
):
    """
    Upload raw text directly as a document.
    
    Useful for adding content without a file.
    """
    collection_name = collection_name or config.DEFAULT_COLLECTION
    
    try:
        doc_id, chunk_count = document_processor.process_text(
            text=text,
            source_name=source_name,
            collection_name=collection_name
        )
        
        return DocumentUploadResponse(
            success=True,
            id=doc_id,
            filename=source_name,
            chunks=chunk_count,
            message=f"Text processed successfully: {chunk_count} chunks created"
        )
    
    except Exception as e:
        logger.error(f"Error processing text: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process text: {str(e)}"
        )
