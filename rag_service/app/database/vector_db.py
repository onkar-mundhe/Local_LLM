"""
LanceDB Vector Store
Author: Kanwarraj Singh

Vector storage using LanceDB with LangChain integration.
Uses local HuggingFace embeddings (all-MiniLM-L6-v2) for CPU inference.
"""

import logging
from typing import List, Optional, Dict, Any
from pathlib import Path

import lancedb
from langchain_community.vectorstores import LanceDB as LangChainLanceDB
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document

from app.config import config

logger = logging.getLogger(__name__)


class VectorDB:
    """
    LanceDB Vector Store wrapper with LangChain integration.
    
    Features:
    - Local embeddings using sentence-transformers
    - Hybrid search support (LanceDB native)
    - Metadata filtering
    - Persistent storage
    """
    
    _instance = None
    _embeddings = None
    _db_connection = None
    
    def __new__(cls):
        """Singleton pattern to reuse connections and embeddings"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._init_embeddings()
        self._init_db()
    
    def _init_embeddings(self):
        """Initialize local embedding model"""
        logger.info(f"Loading embedding model: {config.EMBEDDING_MODEL}")
        
        self._embeddings = HuggingFaceEmbeddings(
            model_name=config.EMBEDDING_MODEL,
            model_kwargs={'device': config.EMBEDDING_DEVICE},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        logger.info(f"Embedding model loaded on {config.EMBEDDING_DEVICE}")
    
    def _init_db(self):
        """Initialize LanceDB connection"""
        db_path = Path(config.LANCEDB_PATH)
        db_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Connecting to LanceDB at: {db_path}")
        self._db_connection = lancedb.connect(str(db_path))
    
    @property
    def embeddings(self):
        """Get the embeddings model"""
        return self._embeddings
    
    @property
    def db(self):
        """Get the LanceDB connection"""
        return self._db_connection
    
    def get_or_create_table(self, table_name: str = None) -> LangChainLanceDB:
        """
        Get or create a LangChain LanceDB vector store for a table.
        
        Args:
            table_name: Name of the table/collection (default: config.DEFAULT_COLLECTION)
        
        Returns:
            LangChainLanceDB vector store instance
        """
        table_name = table_name or config.DEFAULT_COLLECTION
        
        return LangChainLanceDB(
            connection=self._db_connection,
            embedding=self._embeddings,
            table_name=table_name
        )
    
    def add_documents(
        self,
        documents: List[Document],
        table_name: str = None
    ) -> List[str]:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of LangChain Document objects
            table_name: Target table name
        
        Returns:
            List of document IDs
        """
        table_name = table_name or config.DEFAULT_COLLECTION
        vector_store = self.get_or_create_table(table_name)
        
        # Add documents and get IDs
        ids = vector_store.add_documents(documents)
        logger.info(f"Added {len(documents)} documents to table '{table_name}'")
        
        return ids
    
    def similarity_search(
        self,
        query: str,
        k: int = None,
        table_name: str = None,
        filter_dict: Dict[str, Any] = None
    ) -> List[Document]:
        """
        Perform similarity search.
        
        Args:
            query: Search query text
            k: Number of results (default: config.TOP_K_RESULTS)
            table_name: Table to search in
            filter_dict: Metadata filter (e.g., {"source": "doc.pdf"})
        
        Returns:
            List of matching Document objects
        """
        k = k or config.TOP_K_RESULTS
        table_name = table_name or config.DEFAULT_COLLECTION
        
        vector_store = self.get_or_create_table(table_name)
        
        if filter_dict:
            # Build filter string for LanceDB
            # LanceDB uses SQL-like syntax: "source = 'doc.pdf'"
            filter_conditions = []
            for key, value in filter_dict.items():
                if isinstance(value, str):
                    filter_conditions.append(f"{key} = '{value}'")
                elif isinstance(value, list):
                    # IN clause for multiple values
                    values_str = ", ".join([f"'{v}'" for v in value])
                    filter_conditions.append(f"{key} IN ({values_str})")
                else:
                    filter_conditions.append(f"{key} = {value}")
            
            filter_str = " AND ".join(filter_conditions)
            results = vector_store.similarity_search(query, k=k, filter=filter_str)
        else:
            results = vector_store.similarity_search(query, k=k)
        
        return results
    
    def similarity_search_with_score(
        self,
        query: str,
        k: int = None,
        table_name: str = None,
        filter_dict: Dict[str, Any] = None
    ) -> List[tuple[Document, float]]:
        """
        Perform similarity search with relevance scores.
        
        Returns:
            List of (Document, score) tuples
        """
        k = k or config.TOP_K_RESULTS
        table_name = table_name or config.DEFAULT_COLLECTION
        
        vector_store = self.get_or_create_table(table_name)
        
        if filter_dict:
            filter_conditions = []
            for key, value in filter_dict.items():
                if isinstance(value, str):
                    filter_conditions.append(f"{key} = '{value}'")
                elif isinstance(value, list):
                    values_str = ", ".join([f"'{v}'" for v in value])
                    filter_conditions.append(f"{key} IN ({values_str})")
                else:
                    filter_conditions.append(f"{key} = {value}")
            
            filter_str = " AND ".join(filter_conditions)
            results = vector_store.similarity_search_with_score(query, k=k, filter=filter_str)
        else:
            results = vector_store.similarity_search_with_score(query, k=k)
        
        return results
    
    def delete_by_source(self, source: str, table_name: str = None) -> bool:
        """
        Delete all documents from a specific source file.
        
        Args:
            source: Source filename to delete
            table_name: Table to delete from
        
        Returns:
            bool: True if deletion was successful
        """
        table_name = table_name or config.DEFAULT_COLLECTION
        
        try:
            # Get the table directly from LanceDB
            if table_name in self._db_connection.table_names():
                table = self._db_connection.open_table(table_name)
                # Delete rows where source matches
                table.delete(f"source = '{source}'")
                logger.info(f"Deleted documents with source '{source}' from table '{table_name}'")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting documents: {e}")
            return False
    
    def get_table_stats(self, table_name: str = None) -> Dict[str, Any]:
        """
        Get statistics about a table.
        
        Returns:
            Dict with row_count, schema info, etc.
        """
        table_name = table_name or config.DEFAULT_COLLECTION
        
        try:
            if table_name in self._db_connection.table_names():
                table = self._db_connection.open_table(table_name)
                return {
                    "table_name": table_name,
                    "row_count": table.count_rows(),
                    "exists": True
                }
            return {
                "table_name": table_name,
                "row_count": 0,
                "exists": False
            }
        except Exception as e:
            logger.error(f"Error getting table stats: {e}")
            return {
                "table_name": table_name,
                "row_count": 0,
                "exists": False,
                "error": str(e)
            }
    
    def table_exists(self, table_name: str = None) -> bool:
        """Check if a table exists"""
        table_name = table_name or config.DEFAULT_COLLECTION
        return table_name in self._db_connection.table_names()
    
    def get_retriever(self, table_name: str = None, k: int = None):
        """
        Get a LangChain retriever for use in chains.
        
        Returns:
            VectorStoreRetriever
        """
        k = k or config.TOP_K_RESULTS
        table_name = table_name or config.DEFAULT_COLLECTION
        
        vector_store = self.get_or_create_table(table_name)
        return vector_store.as_retriever(search_kwargs={"k": k})


# Global instance
vector_db = VectorDB()
