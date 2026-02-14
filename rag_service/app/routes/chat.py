"""
Chat Routes (RAG-enhanced)
Author: Kanwarraj Singh

RAG-enhanced chat completion endpoint that:
1. Searches for relevant context
2. Augments the prompt
3. Forwards to llama-server
"""

import logging
import time
import uuid
from typing import Optional, List

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.config import config
from app.services.retriever import retriever
from app.models.schemas import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChoice,
    ChatMessage,
    SearchRequest,
    SearchResponse,
    SearchResult
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Chat"])


# System prompt template for RAG
RAG_SYSTEM_TEMPLATE = """You are a helpful assistant. Use the following context from the knowledge base to answer the user's question. If the context doesn't contain relevant information, say so and provide a general response.

Context from knowledge base:
{context}

Instructions:
- Answer based on the context provided above when relevant
- If the context doesn't help, you can use your general knowledge
- Be concise and accurate
- Cite sources when possible (e.g., "According to [source]...")
"""


@router.post("/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """
    Search the knowledge base.
    
    Returns relevant document chunks matching the query.
    """
    results = retriever.search(
        query=request.query,
        k=request.k,
        collection_name=request.collection_name,
        sources=request.sources
    )
    
    context = retriever.format_context(results) if results else None
    
    return SearchResponse(
        query=request.query,
        results=[SearchResult(**r) for r in results],
        total=len(results),
        context=context
    )


@router.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """
    RAG-enhanced chat completions endpoint.
    
    OpenAI-compatible API that:
    1. Extracts the user's query
    2. Searches knowledge base for relevant context
    3. Augments the system message with context
    4. Forwards to llama-server
    5. Returns the response
    
    Set use_rag=false to bypass RAG and proxy directly.
    """
    
    # Extract user's last message for RAG query
    user_query = None
    for msg in reversed(request.messages):
        if msg.role == "user":
            if isinstance(msg.content, str):
                user_query = msg.content
            elif isinstance(msg.content, list):
                # Handle multimodal content - extract text
                for part in msg.content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        user_query = part.get("text", "")
                        break
            break
    
    rag_sources_used = []
    
    # Augment with RAG context if enabled
    if request.use_rag and user_query:
        context, results = retriever.get_rag_context(
            query=user_query,
            k=request.rag_k,
            sources=request.rag_sources
        )
        
        if context:
            # Get unique sources
            rag_sources_used = list(set(r['source'] for r in results))
            
            # Create augmented messages
            augmented_messages = []
            
            # Find or create system message
            has_system = any(m.role == "system" for m in request.messages)
            
            if has_system:
                # Prepend context to existing system message
                for msg in request.messages:
                    if msg.role == "system":
                        augmented_content = RAG_SYSTEM_TEMPLATE.format(context=context)
                        if isinstance(msg.content, str) and msg.content.strip():
                            augmented_content += f"\n\nAdditional instructions: {msg.content}"
                        augmented_messages.append(ChatMessage(
                            role="system",
                            content=augmented_content
                        ))
                    else:
                        augmented_messages.append(msg)
            else:
                # Add new system message with context
                augmented_messages.append(ChatMessage(
                    role="system",
                    content=RAG_SYSTEM_TEMPLATE.format(context=context)
                ))
                augmented_messages.extend(request.messages)
            
            request.messages = augmented_messages
            logger.info(f"RAG: Added context from {len(results)} chunks ({len(rag_sources_used)} sources)")
    
    # Prepare request for llama-server
    llama_request = {
        "messages": [{"role": m.role, "content": m.content} for m in request.messages],
        "stream": request.stream
    }
    
    # Add optional parameters
    if request.model:
        llama_request["model"] = request.model
    if request.temperature is not None:
        llama_request["temperature"] = request.temperature
    if request.max_tokens is not None:
        llama_request["max_tokens"] = request.max_tokens
    if request.top_p is not None:
        llama_request["top_p"] = request.top_p
    if request.top_k is not None:
        llama_request["top_k"] = request.top_k
    if request.repeat_penalty is not None:
        llama_request["repeat_penalty"] = request.repeat_penalty
    
    # Forward to llama-server
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            if request.stream:
                # Streaming response
                async def stream_response():
                    async with client.stream(
                        "POST",
                        f"{config.LLAMA_SERVER_URL}/v1/chat/completions",
                        json=llama_request
                    ) as response:
                        async for chunk in response.aiter_bytes():
                            yield chunk
                
                return StreamingResponse(
                    stream_response(),
                    media_type="text/event-stream"
                )
            else:
                # Non-streaming response
                response = await client.post(
                    f"{config.LLAMA_SERVER_URL}/v1/chat/completions",
                    json=llama_request
                )
                
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"LLM server error: {response.text}"
                    )
                
                result = response.json()
                
                # Add RAG metadata to response
                result["rag_context_used"] = bool(rag_sources_used)
                result["rag_sources"] = rag_sources_used if rag_sources_used else None
                
                return result
    
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail=f"Cannot connect to LLM server at {config.LLAMA_SERVER_URL}. Is llama-server running?"
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="LLM server request timed out"
        )
    except Exception as e:
        logger.error(f"Error forwarding to LLM server: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error communicating with LLM server: {str(e)}"
        )


@router.get("/v1/models")
async def list_models():
    """
    Proxy /v1/models to llama-server.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{config.LLAMA_SERVER_URL}/v1/models")
            return response.json()
    except Exception as e:
        logger.error(f"Error fetching models: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Cannot connect to LLM server: {str(e)}"
        )
