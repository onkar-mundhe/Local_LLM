"""
Retriever Service
Author: Kanwarraj Singh

Handles document retrieval and search operations.
Provides simple interface for RAG queries.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple

from langchain_core.documents import Document

from app.config import config
from app.database.vector_db import vector_db

logger = logging.getLogger(__name__)


class Retriever:
    """
    Document retrieval service for RAG.
    
    Provides:
    - Similarity search
    - Filtered search by source documents
    - Context formatting for LLM prompts
    """
    
    def __init__(self):
        self.default_k = config.TOP_K_RESULTS
        self.similarity_threshold = config.SIMILARITY_THRESHOLD
    
    def search(
        self,
        query: str,
        k: int = None,
        collection_name: str = None,
        sources: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant documents.
        
        Args:
            query: Search query
            k: Number of results to return
            collection_name: Collection to search in
            sources: Optional list of source filenames to filter by
        
        Returns:
            List of result dictionaries with content, source, score, etc.
        """
        k = k or self.default_k
        collection_name = collection_name or config.DEFAULT_COLLECTION
        
        # Build filter if sources specified
        filter_dict = None
        if sources:
            filter_dict = {"source": sources}
        
        # Perform search with scores
        results = vector_db.similarity_search_with_score(
            query=query,
            k=k,
            table_name=collection_name,
            filter_dict=filter_dict
        )
        
        # Format results
        formatted_results = []
        for doc, score in results:
            # LanceDB returns distance, convert to similarity
            # Lower distance = higher similarity
            similarity = 1.0 / (1.0 + score) if score >= 0 else 1.0
            
            formatted_results.append({
                "content": doc.page_content,
                "source": doc.metadata.get("source", "unknown"),
                "page": doc.metadata.get("page", 0),
                "chunk_index": doc.metadata.get("chunk_index", 0),
                "score": similarity,
                "metadata": doc.metadata
            })
        
        logger.info(f"Search for '{query[:50]}...' returned {len(formatted_results)} results")
        return formatted_results
    
    def search_documents(
        self,
        query: str,
        k: int = None,
        collection_name: str = None,
        sources: List[str] = None
    ) -> List[Document]:
        """
        Search and return LangChain Document objects.
        
        Useful for integration with LangChain chains.
        """
        k = k or self.default_k
        collection_name = collection_name or config.DEFAULT_COLLECTION
        
        filter_dict = None
        if sources:
            filter_dict = {"source": sources}
        
        return vector_db.similarity_search(
            query=query,
            k=k,
            table_name=collection_name,
            filter_dict=filter_dict
        )
    
    def format_context(
        self,
        results: List[Dict[str, Any]],
        include_sources: bool = True,
        max_length: int = None
    ) -> str:
        """
        Format search results as context for LLM prompt.
        
        Args:
            results: Search results from search()
            include_sources: Whether to include source citations
            max_length: Maximum context length (chars)
        
        Returns:
            Formatted context string
        """
        if not results:
            return ""
        
        context_parts = []
        
        for i, result in enumerate(results, 1):
            if include_sources:
                source_info = f"[Source: {result['source']}"
                if result.get('page'):
                    source_info += f", Page {result['page']}"
                source_info += "]"
                
                context_parts.append(f"{source_info}\n{result['content']}")
            else:
                context_parts.append(result['content'])
        
        context = "\n\n---\n\n".join(context_parts)
        
        # Truncate if needed
        if max_length and len(context) > max_length:
            context = context[:max_length] + "..."
        
        return context
    
    def get_rag_context(
        self,
        query: str,
        k: int = None,
        collection_name: str = None,
        sources: List[str] = None
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Convenience method: search and format context in one call.
        
        Returns:
            Tuple of (formatted_context, raw_results)
        """
        results = self.search(
            query=query,
            k=k,
            collection_name=collection_name,
            sources=sources
        )
        
        context = self.format_context(results)
        
        return context, results


# Global instance
retriever = Retriever()
