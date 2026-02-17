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
from app.database.sqlite_db import document_db

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
    
    def _normalize_source(self, source_value) -> str:
        """
        Normalize a source value to a plain string filename.

        LanceDB may return metadata source as a dict, list, or other
        non-string type depending on schema evolution. This ensures we
        always compare plain filename strings.
        """
        if isinstance(source_value, str):
            return source_value
        if isinstance(source_value, dict):
            return source_value.get("source", str(source_value))
        if isinstance(source_value, (list, tuple)) and len(source_value) > 0:
            return str(source_value[0])
        return str(source_value) if source_value is not None else "unknown"

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
        
        # Get list of enabled document filenames for post-filtering
        if sources:
            allowed_sources = set(sources)
        else:
            enabled_filenames = document_db.get_enabled_document_filenames(
                collection_name=collection_name
            )
            if not enabled_filenames:
                logger.info("No enabled documents in knowledge base")
                return []
            allowed_sources = set(enabled_filenames)
        
        logger.debug(f"Allowed sources for filtering: {allowed_sources}")
        
        # Perform search with scores (fetch extra to account for post-filtering)
        # LanceDB stores metadata as a single column, so we can't use SQL filters
        # on metadata sub-fields. Instead, we post-filter the results.
        fetch_k = k * 5  # Fetch more to have enough after filtering
        results = vector_db.similarity_search_with_score(
            query=query,
            k=fetch_k,
            table_name=collection_name
        )
        
        logger.debug(f"Vector search returned {len(results)} raw results for fetch_k={fetch_k}")
        
        # Format results and filter to only include enabled documents
        formatted_results = []
        skipped_sources = set()
        for doc, score in results:
            raw_source = doc.metadata.get("source", "unknown")
            source = self._normalize_source(raw_source)
            
            # Skip documents that are not in the allowed sources
            if source not in allowed_sources:
                if source not in skipped_sources:
                    skipped_sources.add(source)
                    logger.debug(
                        f"Skipping source '{source}' (raw type: {type(raw_source).__name__}, "
                        f"raw value: {repr(raw_source)}) - not in allowed_sources"
                    )
                continue
            
            # LanceDB returns distance, convert to similarity
            # Lower distance = higher similarity
            similarity = 1.0 / (1.0 + score) if score >= 0 else 1.0
            
            formatted_results.append({
                "content": doc.page_content,
                "source": source,
                "page": doc.metadata.get("page", 0),
                "chunk_index": doc.metadata.get("chunk_index", 0),
                "score": similarity,
                "metadata": doc.metadata
            })
            
            # Stop once we have enough results
            if len(formatted_results) >= k:
                break
        
        if skipped_sources:
            logger.warning(
                f"Post-filter skipped {len(skipped_sources)} source(s) not in enabled list: "
                f"{skipped_sources}. Allowed: {allowed_sources}"
            )
        
        # Fallback: if post-filtering dropped too many results, the metadata source
        # names likely don't match SQLite filenames (LanceDB schema evolution issue).
        # In that case, return unfiltered results from the vector search.
        if len(formatted_results) < k and len(results) >= k and skipped_sources:
            logger.warning(
                f"Post-filter reduced results from {len(results)} to "
                f"{len(formatted_results)} (requested {k}). "
                f"Falling back to unfiltered results."
            )
            formatted_results = []
            for doc, score in results:
                raw_source = doc.metadata.get("source", "unknown")
                source = self._normalize_source(raw_source)
                similarity = 1.0 / (1.0 + score) if score >= 0 else 1.0
                formatted_results.append({
                    "content": doc.page_content,
                    "source": source,
                    "page": doc.metadata.get("page", 0),
                    "chunk_index": doc.metadata.get("chunk_index", 0),
                    "score": similarity,
                    "metadata": doc.metadata
                })
                if len(formatted_results) >= k:
                    break
        
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
