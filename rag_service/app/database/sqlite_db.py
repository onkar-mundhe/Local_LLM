"""
SQLite Document Tracker
Author: Kanwarraj Singh

Tracks uploaded documents metadata for knowledge base management.
Uses SQLite for lightweight, serverless document tracking.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from contextlib import contextmanager

from app.config import config


class DocumentDB:
    """SQLite database for document metadata tracking"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.SQLITE_PATH
        self._init_db()
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_db(self):
        """Initialize database schema"""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    original_filename TEXT,
                    file_type TEXT,
                    file_size INTEGER,
                    chunk_count INTEGER DEFAULT 0,
                    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    collection_name TEXT DEFAULT 'documents',
                    metadata TEXT,
                    enabled INTEGER DEFAULT 1
                )
            """)
            
            # Migrate: add 'enabled' column if missing (existing databases)
            try:
                conn.execute("ALTER TABLE documents ADD COLUMN enabled INTEGER DEFAULT 1")
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            # Create index for faster lookups
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_status 
                ON documents(status)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_collection 
                ON documents(collection_name)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_enabled 
                ON documents(enabled)
            """)
    
    def add_document(
        self,
        filename: str,
        file_type: str,
        file_size: int = 0,
        chunk_count: int = 0,
        collection_name: str = "documents",
        original_filename: str = None,
        metadata: str = None
    ) -> int:
        """
        Add a new document record.
        
        Returns:
            int: The ID of the newly created document record
        """
        with self._get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO documents 
                (filename, original_filename, file_type, file_size, chunk_count, collection_name, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                filename,
                original_filename or filename,
                file_type,
                file_size,
                chunk_count,
                collection_name,
                metadata
            ))
            return cursor.lastrowid
    
    def update_chunk_count(self, doc_id: int, chunk_count: int) -> bool:
        """Update the chunk count for a document"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                UPDATE documents 
                SET chunk_count = ?
                WHERE id = ?
            """, (chunk_count, doc_id))
            return cursor.rowcount > 0
    
    def get_document(self, doc_id: int) -> Optional[Dict[str, Any]]:
        """Get a single document by ID"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM documents WHERE id = ?
            """, (doc_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_document_by_filename(self, filename: str, collection_name: str = "documents") -> Optional[Dict[str, Any]]:
        """Get a document by filename"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM documents 
                WHERE filename = ? AND collection_name = ? AND status = 'active'
            """, (filename, collection_name))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all_documents(
        self,
        collection_name: str = None,
        status: str = "active"
    ) -> List[Dict[str, Any]]:
        """
        Get all documents, optionally filtered by collection and status.
        
        Args:
            collection_name: Filter by collection (None = all collections)
            status: Filter by status (default: 'active')
        
        Returns:
            List of document dictionaries
        """
        with self._get_connection() as conn:
            if collection_name:
                cursor = conn.execute("""
                    SELECT * FROM documents 
                    WHERE collection_name = ? AND status = ?
                    ORDER BY upload_date DESC
                """, (collection_name, status))
            else:
                cursor = conn.execute("""
                    SELECT * FROM documents 
                    WHERE status = ?
                    ORDER BY upload_date DESC
                """, (status,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_document(self, doc_id: int, soft_delete: bool = True) -> bool:
        """
        Delete a document record.
        
        Args:
            doc_id: Document ID to delete
            soft_delete: If True, sets status to 'deleted'. If False, permanently removes.
        
        Returns:
            bool: True if document was deleted
        """
        with self._get_connection() as conn:
            if soft_delete:
                cursor = conn.execute("""
                    UPDATE documents 
                    SET status = 'deleted'
                    WHERE id = ?
                """, (doc_id,))
            else:
                cursor = conn.execute("""
                    DELETE FROM documents WHERE id = ?
                """, (doc_id,))
            return cursor.rowcount > 0
    
    def toggle_document_enabled(self, doc_id: int, enabled: bool) -> bool:
        """
        Toggle whether a document is enabled for RAG queries.
        
        Args:
            doc_id: Document ID
            enabled: True to enable, False to disable
        
        Returns:
            bool: True if document was updated
        """
        with self._get_connection() as conn:
            cursor = conn.execute("""
                UPDATE documents 
                SET enabled = ?
                WHERE id = ? AND status = 'active'
            """, (1 if enabled else 0, doc_id))
            return cursor.rowcount > 0
    
    def get_enabled_document_filenames(
        self,
        collection_name: str = None,
        status: str = "active"
    ) -> List[str]:
        """
        Get filenames of all enabled documents.
        
        Returns:
            List of filenames that are enabled for RAG queries
        """
        with self._get_connection() as conn:
            if collection_name:
                cursor = conn.execute("""
                    SELECT filename FROM documents 
                    WHERE collection_name = ? AND status = ? AND enabled = 1
                    ORDER BY upload_date DESC
                """, (collection_name, status))
            else:
                cursor = conn.execute("""
                    SELECT filename FROM documents 
                    WHERE status = ? AND enabled = 1
                    ORDER BY upload_date DESC
                """, (status,))
            return [row["filename"] for row in cursor.fetchall()]
    
    def get_document_count(self, collection_name: str = None, status: str = "active") -> int:
        """Get count of documents"""
        with self._get_connection() as conn:
            if collection_name:
                cursor = conn.execute("""
                    SELECT COUNT(*) as count FROM documents 
                    WHERE collection_name = ? AND status = ?
                """, (collection_name, status))
            else:
                cursor = conn.execute("""
                    SELECT COUNT(*) as count FROM documents 
                    WHERE status = ?
                """, (status,))
            return cursor.fetchone()["count"]
    
    def get_total_chunks(self, collection_name: str = None, status: str = "active") -> int:
        """Get total chunk count across all documents"""
        with self._get_connection() as conn:
            if collection_name:
                cursor = conn.execute("""
                    SELECT COALESCE(SUM(chunk_count), 0) as total FROM documents 
                    WHERE collection_name = ? AND status = ?
                """, (collection_name, status))
            else:
                cursor = conn.execute("""
                    SELECT COALESCE(SUM(chunk_count), 0) as total FROM documents 
                    WHERE status = ?
                """, (status,))
            return cursor.fetchone()["total"]


# Global instance
document_db = DocumentDB()
