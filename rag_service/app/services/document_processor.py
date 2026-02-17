"""
Document Processor Service
Author: Kanwarraj Singh

Handles document loading, chunking, and ingestion into the vector store.
Uses LangChain's built-in loaders and text splitters.
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple, BinaryIO

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    UnstructuredMarkdownLoader
)

from app.config import config
from app.database.sqlite_db import document_db
from app.database.vector_db import vector_db

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Document processing service for ingesting documents into the RAG system.
    
    Supports:
    - PDF files
    - Word documents (.docx)
    - Text files (.txt)
    - Markdown files (.md)
    """
    
    SUPPORTED_EXTENSIONS = {
        '.pdf': 'pdf',
        '.docx': 'docx',
        '.doc': 'doc',
        '.txt': 'txt',
        '.md': 'markdown',
        '.markdown': 'markdown'
    }
    
    def __init__(self):
        # ── Character-based chunking (commented out for testing page-wise) ──
        # self.text_splitter = RecursiveCharacterTextSplitter(
        #     chunk_size=config.CHUNK_SIZE,
        #     chunk_overlap=config.CHUNK_OVERLAP,
        #     length_function=len,
        #     separators=["\n\n", "\n", ". ", " ", ""]
        # )
        pass
    
    def get_file_type(self, filename: str) -> Optional[str]:
        """Get file type from filename extension"""
        ext = Path(filename).suffix.lower()
        return self.SUPPORTED_EXTENSIONS.get(ext)
    
    def is_supported(self, filename: str) -> bool:
        """Check if file type is supported"""
        return self.get_file_type(filename) is not None
    
    def load_document(self, file_path: str, filename: str) -> List[Document]:
        """
        Load a document using the appropriate loader.
        
        Args:
            file_path: Path to the file
            filename: Original filename (for type detection)
        
        Returns:
            List of Document objects
        """
        file_type = self.get_file_type(filename)
        
        if file_type == 'pdf':
            loader = PyPDFLoader(file_path)
        elif file_type in ('docx', 'doc'):
            loader = Docx2txtLoader(file_path)
        elif file_type == 'markdown':
            loader = UnstructuredMarkdownLoader(file_path)
        elif file_type == 'txt':
            loader = TextLoader(file_path, encoding='utf-8')
        else:
            raise ValueError(f"Unsupported file type: {filename}")
        
        documents = loader.load()
        logger.info(f"Loaded {len(documents)} pages from {filename}")
        
        return documents
    
    def chunk_documents(self, documents: List[Document], source: str) -> List[Document]:
        """
        Split documents into chunks.
        
        Args:
            documents: List of Document objects
            source: Source filename to add to metadata
        
        Returns:
            List of chunked Document objects
        """
        # ── Character-based chunking (commented out for testing page-wise) ──
        # chunks = self.text_splitter.split_documents(documents)

        # ── Page-wise chunking: 1 page = 1 chunk ──
        chunks = documents  # Use pages directly as chunks
        
        # Normalize metadata to only include fields that match the LanceDB schema
        # PDF loaders may add extra fields (author, creator, etc.) that cause schema mismatch
        for i, chunk in enumerate(chunks):
            normalized_metadata = {
                'source': source,
                'chunk_index': i,
                'page': chunk.metadata.get('page', i)
            }
            chunk.metadata = normalized_metadata
        
        logger.info(f"Page-wise chunking: {len(documents)} pages → {len(chunks)} chunks")
        return chunks
    
    def process_file(
        self,
        file: BinaryIO,
        filename: str,
        collection_name: str = None
    ) -> Tuple[int, int]:
        """
        Process a file: load, chunk, embed, and store.
        
        Args:
            file: File-like object
            filename: Original filename
            collection_name: Collection to store in
        
        Returns:
            Tuple of (document_id, chunk_count)
        """
        collection_name = collection_name or config.DEFAULT_COLLECTION
        file_type = self.get_file_type(filename)
        
        if not file_type:
            raise ValueError(f"Unsupported file type: {filename}")
        
        # Check if document already exists
        existing = document_db.get_document_by_filename(filename, collection_name)
        if existing:
            # Delete existing document first
            logger.info(f"Document '{filename}' already exists, replacing...")
            self.delete_document(existing['id'], collection_name)
        
        # Save file to temp location
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix) as tmp:
            content = file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            # Load document
            documents = self.load_document(tmp_path, filename)
            
            # Chunk documents
            chunks = self.chunk_documents(documents, filename)
            
            if not chunks:
                raise ValueError(f"No content extracted from {filename}")
            
            # Add to vector store
            vector_db.add_documents(chunks, collection_name)
            
            # Record in SQLite
            doc_id = document_db.add_document(
                filename=filename,
                file_type=file_type,
                file_size=len(content),
                chunk_count=len(chunks),
                collection_name=collection_name
            )
            
            logger.info(f"Processed '{filename}': {len(chunks)} chunks, doc_id={doc_id}")
            
            return doc_id, len(chunks)
        
        finally:
            # Clean up temp file
            os.unlink(tmp_path)
    
    def process_text(
        self,
        text: str,
        source_name: str,
        collection_name: str = None
    ) -> Tuple[int, int]:
        """
        Process raw text directly.
        
        Args:
            text: Text content
            source_name: Name to use as source
            collection_name: Collection to store in
        
        Returns:
            Tuple of (document_id, chunk_count)
        """
        collection_name = collection_name or config.DEFAULT_COLLECTION
        
        # Create document
        documents = [Document(
            page_content=text,
            metadata={"source": source_name}
        )]
        
        # Chunk
        chunks = self.chunk_documents(documents, source_name)
        
        if not chunks:
            raise ValueError("No content to process")
        
        # Add to vector store
        vector_db.add_documents(chunks, collection_name)
        
        # Record in SQLite
        doc_id = document_db.add_document(
            filename=source_name,
            file_type="text",
            file_size=len(text),
            chunk_count=len(chunks),
            collection_name=collection_name
        )
        
        return doc_id, len(chunks)
    
    def delete_document(self, doc_id: int, collection_name: str = None) -> bool:
        """
        Delete a document from both vector store and SQLite.
        
        Args:
            doc_id: Document ID to delete
            collection_name: Collection to delete from
        
        Returns:
            bool: True if successful
        """
        collection_name = collection_name or config.DEFAULT_COLLECTION
        
        # Get document info
        doc = document_db.get_document(doc_id)
        if not doc:
            return False
        
        # Delete from vector store
        vector_db.delete_by_source(doc['filename'], collection_name)
        
        # Delete from SQLite
        document_db.delete_document(doc_id, soft_delete=True)
        
        logger.info(f"Deleted document {doc_id}: {doc['filename']}")
        return True


# Global instance
document_processor = DocumentProcessor()
