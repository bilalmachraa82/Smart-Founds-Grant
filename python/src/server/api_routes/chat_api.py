"""
Chat API - Lovable Integration Endpoints

This module provides endpoints specifically designed for Lovable Edge Functions integration.
Wraps existing RAG functionality with Lovable-compatible request/response formats.
"""

import hashlib
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from ..config.logfire_config import get_logger, safe_logfire_error, safe_logfire_info
from ..services.search.rag_service import RAGService
from ..utils import get_supabase_client

# Get logger
logger = get_logger(__name__)

# Create router
router = APIRouter(prefix="/api", tags=["chat"])


# ===================================================================
# Authentication Middleware (Best Practice 2025)
# ===================================================================

async def verify_api_key(authorization: str | None = Header(None, alias="Authorization")):
    """
    Verify API key from Authorization header.

    Best Practice (2025): Use Depends for authentication instead of middleware
    for more granular control and better error messages.

    Args:
        authorization: Authorization header value (e.g., "Bearer archon_key_...")

    Raises:
        HTTPException: 401 if missing or invalid API key

    Returns:
        str: Validated API key
    """
    import os

    if not authorization:
        safe_logfire_error("Missing Authorization header")
        raise HTTPException(
            status_code=401,
            detail={"error": "Missing Authorization header"}
        )

    # Extract token from "Bearer <token>" format
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail={"error": "Invalid Authorization header format. Expected: Bearer <api_key>"}
        )

    api_key = parts[1]

    # Validate against environment variable
    expected_key = os.getenv("ARCHON_API_KEY")
    if not expected_key:
        safe_logfire_error("ARCHON_API_KEY not configured in environment")
        raise HTTPException(
            status_code=500,
            detail={"error": "Server configuration error"}
        )

    if api_key != expected_key:
        safe_logfire_error(f"Invalid API key attempt | provided={api_key[:20]}...")
        raise HTTPException(
            status_code=403,
            detail={"error": "Invalid API key"}
        )

    safe_logfire_info(f"API key validated successfully")
    return api_key


# ===================================================================
# Request/Response Models
# ===================================================================

class ChatRequest(BaseModel):
    """
    Chat request format expected by Lovable Edge Functions.

    This matches the payload format used in supabase/functions/run-aiparati/index.ts
    """
    query: str = Field(..., description="User query or question")
    stream: bool = Field(default=False, description="Whether to stream response (not yet implemented)")
    rag: bool = Field(default=True, description="Whether to use RAG for context")
    source: str | None = Field(default=None, description="Optional source filter")
    match_count: int = Field(default=5, ge=1, le=20, description="Number of relevant chunks to retrieve")

    class Config:
        schema_extra = {
            "example": {
                "query": "Quais são os critérios de elegibilidade para PME em Portugal?",
                "stream": False,
                "rag": True,
                "match_count": 5
            }
        }


class CitationModel(BaseModel):
    """Citation from source document."""
    source: str = Field(..., description="Source document name")
    page: int | None = Field(None, description="Page number if available")
    text: str = Field(..., description="Relevant excerpt from source")
    score: float | None = Field(None, description="Similarity/relevance score")


class ChatResponse(BaseModel):
    """
    Chat response format expected by Lovable Edge Functions.

    Provides both direct answer and supporting citations.
    """
    answer: str = Field(..., description="Generated answer from RAG pipeline")
    sources: list[CitationModel] = Field(default_factory=list, description="Citations from knowledge base")
    stream: bool = Field(default=False, description="Whether response was streamed")
    query: str = Field(..., description="Original query")
    total_found: int = Field(default=0, description="Total relevant chunks found")
    search_mode: str = Field(default="hybrid", description="Search strategy used (vector, hybrid, agentic)")

    class Config:
        schema_extra = {
            "example": {
                "answer": "Para PME em Portugal, os critérios de elegibilidade incluem...",
                "sources": [
                    {
                        "source": "anexo1.pdf",
                        "page": 5,
                        "text": "As PME devem ter menos de 250 trabalhadores...",
                        "score": 0.92
                    }
                ],
                "stream": False,
                "query": "Quais são os critérios de elegibilidade?",
                "total_found": 5,
                "search_mode": "hybrid"
            }
        }


class KnowledgeVersionResponse(BaseModel):
    """Knowledge base version information."""
    version_hash: str = Field(..., description="Hash of latest knowledge base state")
    last_updated: str = Field(..., description="ISO timestamp of last update")
    total_sources: int = Field(default=0, description="Total number of sources")
    total_chunks: int = Field(default=0, description="Total number of indexed chunks")


# ===================================================================
# Endpoints
# ===================================================================

@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(verify_api_key)])
async def chat_endpoint(request: ChatRequest):
    """
    Chat endpoint for Lovable Edge Functions integration.

    This endpoint wraps the existing /api/rag/query functionality with a Lovable-compatible
    interface. It performs RAG query and formats results as expected by Edge Functions.

    **Best Practices Applied (2025)**:
    - Uses Depends() for authentication (more flexible than middleware)
    - Pydantic models for request/response validation
    - Detailed error messages for debugging
    - Structured logging with Logfire
    - Response transformation for client compatibility

    **Security**:
    - Requires valid API key in Authorization header
    - Rate limiting should be added in production (see comments)

    Args:
        request: ChatRequest with query and RAG parameters

    Returns:
        ChatResponse with answer and citations

    Raises:
        HTTPException: 422 for validation errors, 500 for processing errors
    """
    # Validate query
    if not request.query or not request.query.strip():
        raise HTTPException(
            status_code=422,
            detail={"error": "Query is required and cannot be empty"}
        )

    safe_logfire_info(f"Chat request received | query={request.query[:50]}... | rag={request.rag}")

    try:
        # If RAG disabled, return simple response (edge case)
        if not request.rag:
            return ChatResponse(
                answer="RAG is disabled. Please enable RAG for context-aware responses.",
                sources=[],
                stream=False,
                query=request.query,
                total_found=0,
                search_mode="none"
            )

        # Perform RAG query using existing service
        search_service = RAGService(get_supabase_client())
        success, result = await search_service.perform_rag_query(
            query=request.query,
            source=request.source,
            match_count=request.match_count
        )

        if not success:
            error_msg = result.get("error", "RAG query failed")
            safe_logfire_error(f"RAG query failed | error={error_msg}")
            raise HTTPException(
                status_code=500,
                detail={"error": error_msg}
            )

        # Transform RAG results to Chat response format
        citations = []
        for idx, chunk in enumerate(result.get("results", [])[:request.match_count]):
            # Extract metadata
            metadata = chunk.get("metadata", {})
            url = chunk.get("url", "unknown")

            # Try to extract source name from URL or metadata
            source_name = metadata.get("source_display_name", url.split("/")[-1] if url else "Unknown")

            citations.append(CitationModel(
                source=source_name,
                page=metadata.get("page_number"),
                text=chunk.get("content", "")[:200] + "..." if len(chunk.get("content", "")) > 200 else chunk.get("content", ""),
                score=chunk.get("similarity_score") or chunk.get("rerank_score")
            ))

        # Generate answer from top results
        # TODO: In future, integrate with LLM to generate answer from chunks
        # For now, return concatenated content as answer
        answer_text = "\n\n".join([
            f"From {c.source}: {c.text}"
            for c in citations[:3]  # Top 3 citations
        ])

        if not answer_text:
            answer_text = "No relevant information found in knowledge base."

        response = ChatResponse(
            answer=answer_text,
            sources=citations,
            stream=request.stream,  # Currently always False
            query=request.query,
            total_found=result.get("total_found", 0),
            search_mode=result.get("search_mode", "hybrid")
        )

        safe_logfire_info(
            f"Chat response generated | sources={len(citations)} | mode={response.search_mode}"
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        safe_logfire_error(f"Chat endpoint error | error={str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": f"Internal server error: {str(e)}"}
        )


@router.get("/knowledge/version", response_model=KnowledgeVersionResponse, dependencies=[Depends(verify_api_key)])
async def get_knowledge_version():
    """
    Get knowledge base version information.

    Returns a hash of the current knowledge base state, useful for cache invalidation
    in Edge Functions. The hash changes whenever sources are added/updated/deleted.

    **Best Practices Applied**:
    - Efficient query (only fetches updated_at timestamps)
    - Deterministic hash generation (sorted by timestamp)
    - Includes metadata for debugging (counts, timestamps)

    Returns:
        KnowledgeVersionResponse with version hash and metadata
    """
    try:
        supabase = get_supabase_client()

        # Query sources table for latest updates
        sources_response = supabase.table("archon_sources") \
            .select("source_id,updated_at") \
            .order("updated_at", desc=True) \
            .execute()

        sources = sources_response.data if sources_response.data else []

        # Query crawled_pages for total chunks count
        chunks_response = supabase.table("archon_crawled_pages") \
            .select("id", count="exact") \
            .execute()

        total_chunks = chunks_response.count if chunks_response.count is not None else 0

        # Generate deterministic hash from source timestamps
        if sources:
            # Sort by updated_at to ensure deterministic hash
            sorted_sources = sorted(sources, key=lambda x: x.get("updated_at", ""))
            hash_input = "|".join([
                f"{s.get('source_id')}:{s.get('updated_at')}"
                for s in sorted_sources
            ])
            version_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
            last_updated = sorted_sources[0].get("updated_at", datetime.now().isoformat())
        else:
            # No sources yet - use empty hash
            version_hash = hashlib.sha256(b"empty").hexdigest()[:16]
            last_updated = datetime.now().isoformat()

        response = KnowledgeVersionResponse(
            version_hash=version_hash,
            last_updated=last_updated,
            total_sources=len(sources),
            total_chunks=total_chunks
        )

        safe_logfire_info(
            f"Knowledge version queried | hash={version_hash} | sources={len(sources)} | chunks={total_chunks}"
        )

        return response

    except Exception as e:
        safe_logfire_error(f"Failed to get knowledge version | error={str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": f"Failed to get knowledge version: {str(e)}"}
        )


# ===================================================================
# Rate Limiting (TODO - Production Best Practice)
# ===================================================================

# TODO: Add rate limiting for production
# from slowapi import Limiter
# from slowapi.util import get_remote_address
#
# limiter = Limiter(key_func=get_remote_address)
#
# @router.post("/chat", dependencies=[Depends(verify_api_key)])
# @limiter.limit("10/minute")
# async def chat_endpoint(...):
#     ...
