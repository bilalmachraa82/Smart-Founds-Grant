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
from ..services.llm_provider_service import get_llm_client
from ..services.credential_service import credential_service
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

        # Generate answer using Claude 4.5
        if not citations:
            answer_text = "No relevant information found in knowledge base."
        else:
            # Get LLM settings
            provider_config = await credential_service.get_active_provider("llm")
            llm_model = provider_config.get("llm_model", "claude-sonnet-4-5-20250929")

            # Build context from citations
            context_text = "\n\n".join([
                f"[Fonte: {c.source}]\n{chunk.get('content', '')}"
                for chunk, c in zip(result.get("results", [])[:5], citations[:5])
            ])

            # Build prompt for Claude
            system_prompt = """És um consultor sénior especializado em candidaturas a fundos europeus em Portugal.
Analisa candidaturas com rigor técnico, citando sempre as fontes legais relevantes.
Responde em Português europeu de forma clara, estruturada e profissional.

ANTES de elaborar qualquer proposta, VALIDA sempre:
1. Teto máximo de investimento (€) e elegibilidade mínima (geralmente ≥ €5.000)
2. Cofinanciamento disponível (tipicamente ≥ 25% do investimento elegível)
3. Distribuição preferencial (SaaS/Software/Consultoria/Formação/Equipamentos/RH)
4. Janela temporal (data início/fim) e restrições específicas (RGPD, cloud/on-prem, setor regulado)

REGRAS DE BLOQUEIO CRÍTICAS:
- Se investimento < mínimo elegível → Explica e sugere como atingir limiar
- Se soma rubricas > teto disponível → NÃO prossegue; emite ALERTA e sugere ajustes
- Se taxa incentivo > máximo regulamentar → Alerta e ajusta automaticamente

QUANDO APLICÁVEL, GERA 3 CENÁRIOS DE INVESTIMENTO:
- **Essencial** (~60-80% do teto): Mínimo viável para cumprir objectivos base
- **Recomendado** (~85-95% do teto): Equilibrado entre qualidade/risco/impacto
- **Completo** (~100% do teto): Maximiza impacto e score de mérito

Itens que excedam o teto → coloca em backlog (fase futura/expansão)."""

            user_prompt = f"""# CONTEXTO DA BASE DE CONHECIMENTO

{context_text}

---

# PERGUNTA DO UTILIZADOR

{request.query}

---

# INSTRUÇÕES DE OUTPUT

Com base EXCLUSIVAMENTE no contexto fornecido, fornece uma análise COMPLETA com as seguintes secções:

## A) DASHBOARD (Resumo Executivo no topo)
Badges com indicadores-chave:
- **Elegibilidade**: ✓ SIM / ✗ NÃO / ⚠️ CONDICIONAL
- **Investimento Elegível**: €X.XXX
- **Incentivo Estimado**: €X.XXX (taxa%)
- **Mérito Projeto (MP)**: X,XX (se aplicável)
- **Risco Global**: BAIXO/MÉDIO/ALTO
- **Deadlines Críticos**: [Data submissão]

## B) AVALIAÇÃO DE ELEGIBILIDADE
Veredito fundamentado + bullets com provas:
- Dimensão PME: status [citar artigo]
- Localização/Região: status [citar]
- Setor/CAE: status [citar]
- Investimento mínimo/máximo: status [citar]
- Prazo execução: status [citar]
- Obrigações pré-candidatura (certificações, declarações)

## C) PROJETO PROPOSTO (adaptado ao CAE/atividade)
- 3-5 casos de uso IA/digitalização (especificar ferramentas)
- Dados necessários e arquitetura técnica
- KPIs mensuráveis (SMART)
- Roadmap faseado (trimestres/marcos)
- Plano de Formação (perfis, módulos, horas)
- Consultoria (marcos, horas, validar 3 cotações)
- Software/SaaS e Equipamentos (quando fizer sentido), com justificativa de elegibilidade [citar]

## D) ORÇAMENTO & INCENTIVO (3 CENÁRIOS SE APLICÁVEL)
Tabelas por rubrica elegível:
- SaaS/Software | Consultoria | Formação | Equipamentos | RH dedicados (≤2) | ROC/CC (≤€2.500) | Outras

**Para CADA cenário** (Essencial/Recomendado/Completo):
- Investimento total elegível
- Cálculo incentivo: min(taxa × elegíveis, máximo) [citar fórmula]
- Co-financiamento necessário
- Distribuição percentual por rubrica

Apontar despesas NÃO elegíveis (se houver).

## E) SCORING DE MÉRITO (MP) — SE APLICÁVEL
- Explicar grelha de avaliação [citar anexo]
- Calcular MP = 0,50A + 0,50B (ou fórmula específica do aviso)
- **Tabela "Impacto de Metas"** (cenários):
  ```
  | Alteração | Score Actual | Score Novo | Impacto MP |
  |-----------|--------------|------------|------------|
  | +1 emprego | X pts       | Y pts      | MP = ?     |
  | +10% VAB   | X pts       | Y pts      | MP = ?     |
  ```

## F) CRONOGRAMA FASEADO
- Gantt simplificado (fases/marcos/meses)
- Prazo máximo: [X] meses [citar]
- Milestones críticos com entregáveis

## G) PLANO DE PAGAMENTOS
- PTA (Pedido Título de Atribuição)
- PTRI (Pedidos de Transferência de Reembolso Intermédios)
- PTRF (Pedido de Transferência de Reembolso Final)
- Tetos e prazos [citar artigo]
- Nota: até 95% do incentivo antes do PTRF [citar]

## H) CHECKLIST SUBMISSÃO
Lista verificação (formato tickable com [ ]) de 12-15 documentos obrigatórios: Certificação PME, Certidão permanente, IES, Situação tributária, RCBE, Orçamentos (3 cotações >€5k), Declarações DNSH/duplo financiamento/co-financiamento, Plano formação, etc. [citar fontes]

## I) MAPA COPY-PASTE SIGA-BF
Tabela 3 colunas (Campo SIGA | Valor | Fonte) com campos chave: NIF, Denominação, CAE, NUTS II, Dimensão, Investimento, Taxa incentivo, Prazo, Datas, Empregos, VAB. [10-15 linhas principais]

## J) RISCOS & MITIGAÇÃO
Matriz 6 colunas (Risco | Prob | €Impacto | Mitigação | Contingência | Owner) com 6-8 riscos críticos: RGPD, DNSH, duplo financiamento, atrasos, fornecedores, adoção. [conciso]

## K) AUDIT TRAIL
Tabela metadados: ID Sessão, Data, Documentos base, Fontes dados empresa, Metodologia estimativas, Autor (Archon + Claude Sonnet 4.5).

## L) PRÓXIMAS AÇÕES
Box 💡 no fim de cada secção relevante com passo concreto seguinte.

---

**FORMATO**: Português pt-PT, Markdown, citações obrigatórias [fonte, p.X], tom profissional/actionable. Cobrir secções A-L. Se faltar info: "❌ Info não disponível: [especificar]"
"""

            # Call Claude 4.5
            try:
                async with get_llm_client() as client:
                    safe_logfire_info(f"Calling LLM | model={llm_model}")

                    # Check if using AnthropicAdapter or OpenAI client
                    if hasattr(client, 'create_completion'):
                        # AnthropicAdapter
                        # Max tokens set to 16000 for balanced output (12 sections)
                        # Supports: Dashboard, Budget Tiers, Checklist, SIGA Map, Audit Trail
                        # Trade-off: Quality over extreme length (optimized for 2-3min generation)
                        response = await client.create_completion(
                            model=llm_model,
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt}
                            ],
                            temperature=0.3,
                            max_tokens=16000
                        )
                        answer_text = response.choices[0].message.content
                    else:
                        # OpenAI client
                        response = await client.chat.completions.create(
                            model=llm_model,
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt}
                            ],
                            temperature=0.3,
                            max_tokens=16000
                        )
                        answer_text = response.choices[0].message.content

                    safe_logfire_info(f"LLM response generated | length={len(answer_text)}")

            except Exception as e:
                safe_logfire_error(f"LLM generation failed | error={str(e)}")
                # Fallback to concatenated context
                answer_text = "\n\n".join([
                    f"From {c.source}: {c.text}"
                    for c in citations[:3]
                ])

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
