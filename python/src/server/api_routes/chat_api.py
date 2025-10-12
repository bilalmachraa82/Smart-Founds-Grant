"""
Chat API - Lovable Integration Endpoints

This module provides endpoints specifically designed for Lovable Edge Functions integration.
Wraps existing RAG functionality with Lovable-compatible request/response formats.
"""

import hashlib
from datetime import datetime
from typing import Any, List, Optional

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

async def verify_api_key(authorization: Optional[str] = Header(None, alias="Authorization")):
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
    source: Optional[str] = Field(default=None, description="Optional source filter")
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
    page: Optional[int] = Field(None, description="Page number if available")
    text: str = Field(..., description="Relevant excerpt from source")
    score: Optional[float] = Field(None, description="Similarity/relevance score")


class ChatResponse(BaseModel):
    """
    Chat response format expected by Lovable Edge Functions.

    Provides both direct answer and supporting citations.
    """
    answer: str = Field(..., description="Generated answer from RAG pipeline")
    sources: List[CitationModel] = Field(default_factory=list, description="Citations from knowledge base")
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

Itens que excedam o teto → coloca em backlog (fase futura/expansão).

ADAPTAÇÃO AO SETOR (CAE):
Quando propor use cases IA, adapta ao sector da empresa:
- **CAE 62010 (Programação informática)**: GitHub Copilot, code assistants, automated testing, CI/CD automation, code review IA
- **CAE 70220 (Consultoria gestão)**: Microsoft 365 Copilot, knowledge management (Notion AI), CRM inteligente, análise dados clientes, assistente virtual tarefas
- **CAE 47910 (Comércio online)**: Chatbots atendimento/vendas, motor recomendação produtos (ML), previsão procura/stock inteligente, análise sentimento reviews
- **CAE 56101 (Restaurantes)**: Previsão procura & gestão compras inteligente, chatbot reservas (WhatsApp/IG), otimização pricing dinâmico (happy hours IA)
- **CAE 47190 (Comércio retalho)**: Sistema checkout automático, análise comportamento clientes (computer vision), gestão stock preditiva, personalização ofertas
- **OUTROS SETORES**: Identifica o CAE e propõe ferramentas relevantes (automation, data analysis, customer service, operations optimization)

DATAS ESPECÍFICAS - REGRAS OBRIGATÓRIAS:
- ❌ NUNCA usar "[consultar portal]" ou "Fase I/II" genérico ou "TBD"
- ✅ SEMPRE extrair datas EXATAS do documento RAG quando mencionadas
- ✅ Formato obrigatório: "DD MMM AAAA, HH:MM" (exemplo: 31 Out 2025, 17:59)
- ✅ Se candidaturas contínuas: indicar "Candidaturas contínuas - submeter 48h antes início projeto desejado"
- ✅ Calcular decisão estimada: Data submissão + 40-60 dias úteis (skip weekends)
- ✅ Calcular início projeto: Decisão + 30 dias mobilização

Exemplo cálculo mental dias úteis:
- 40 dias úteis ≈ 8 semanas ≈ 2 meses
- 60 dias úteis ≈ 12 semanas ≈ 3 meses
Se submissão "31 Out 2025" → decisão "meados Dez 2025 a meados Jan 2026 (40-60 dias úteis)"

SEMPRE fornecer data específica OU explicar critério cálculo (não deixar vago)."""

            user_prompt = f"""# CONTEXTO DA BASE DE CONHECIMENTO

{context_text}

---

# PERGUNTA DO UTILIZADOR

{request.query}

---

# INSTRUÇÕES DE OUTPUT

Com base EXCLUSIVAMENTE no contexto fornecido, fornece uma análise COMPLETA com as seguintes secções:

## A0) 🎯 SUMÁRIO EXECUTIVO (1 PÁGINA - SEMPRE PRIMEIRO)

**OBJETIVO:** Fornecer decisores informação crítica em 30 segundos.

┌─────────────────────────────────────────────────────────────┐
│ VEREDITO: [🟢 ELEGÍVEL / 🟡 CONDICIONAL / 🔴 NÃO ELEGÍVEL] │
│ SCORE ESTIMADO: [X.X]/10 (Classe [A/B/C])                  │
│ INVESTIMENTO RECOMENDADO: €[valor cenário recomendado]     │
│ INCENTIVO ESTIMADO: €[valor] ([taxa]%)                      │
│ PROBABILIDADE APROVAÇÃO: [estimativa: X]%                   │
│ PRAZO EXECUÇÃO: [X] meses                                   │
└─────────────────────────────────────────────────────────────┘

### ⚡ TOP 3 AÇÕES CRÍTICAS (PRÓXIMOS 7 DIAS)
Listar as 3 ações mais urgentes com formato:
- [ ] **AÇÃO 1:** [descrição concisa, específica e actionable] | Responsável: [role específico] | Prazo: [DD/MM/AAAA]
- [ ] **AÇÃO 2:** [descrição concisa] | Responsável: [role] | Prazo: [DD/MM/AAAA]
- [ ] **AÇÃO 3:** [descrição concisa] | Responsável: [role] | Prazo: [DD/MM/AAAA]

Exemplos de ações críticas típicas:
- Obter Certificação PME (IAPMEI - 48h)
- Validar IES [ano] disponível
- Solicitar 3 cotações fornecedores principais
- Redigir memória descritiva preliminar
- Contactar consultora RGPD para DPA

### 🚨 BLOQUEADORES CRÍTICOS
[APENAS se existirem bloqueadores que impedem candidatura]
[Se NÃO houver bloqueadores: "✅ Nenhum bloqueador crítico identificado"]
[Máximo 3 bloqueadores, formato bullet point com solução]

Exemplo:
- ❌ **Investimento <€20k elegível** → SOLUÇÃO: Expandir projeto incluir formação + consultoria (alcançar €179k elegível)

### ⏰ TIMELINE DECISÃO
- **Deadline Submissão:** [data ESPECÍFICA: DD MMM AAAA, HH:MM] ou "Candidaturas contínuas - submeter 48h antes início"
- **Decisão Estimada:** [calcular: data submissão + 40-60 dias úteis → DD MMM AAAA]
- **Início Projeto (estimado):** [calcular: decisão + 30 dias mobilização]

IMPORTANTE: NUNCA usar "[consultar portal]" - sempre fornecer data específica ou explicar critério cálculo.

### 💡 RECOMENDAÇÃO ESTRATÉGICA (1-2 frases)
Sintetizar qual cenário recomendado e porquê (trade-off risco/retorno/capacidade financeira).

Exemplo: "Recomendamos Cenário 2 (€227k investimento, €90k incentivo) por equilibrar probabilidade aprovação elevada (85%) com co-financiamento controlado (€137k), vs Cenário 1 (risco rejeição 70%) e Cenário 3 (exige €239k cash)."

---

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

**Crescimento VAB Projetado (no cenário recomendado):**
Incluir subsecção detalhada:

📊 **Fundamentação VAB:**
| Métrica | Valor Atual | Valor Projetado | Variação |
|---------|-------------|-----------------|----------|
| VAB Estimado | €[calc: faturação × 0.4-0.6]* | €[projeção] | +[%] |
| VAB/Trabalhador | €[atual/n_funcionários] | €[projetado/n_funcionários] | +[%] |
| Ref. Setor CAE [X]** | €[INE se disponível] | - | [posição: acima/abaixo média] |

*Margem estimada setor: [fonte INE / Racius / Estimativa conservadora 40-60%]
**Fonte: INE 2023 Contas Nacionais Setoriais (se dados disponíveis para CAE específico)

**Cálculo Detalhado:**
1. VAB atual estimado: Faturação €[X] × Margem setor [Y]% = €[Z]
2. Impacto produtividade: +[X]% output → +€[valor] VAB
3. Impacto qualidade/eficiência: -[Y]% custos → +€[valor economizado]
4. Efeito líquido: €[Z atual] + [ganhos] = €[novo VAB]
5. Crescimento: ([novo] - [atual]) / [atual] × 100 = +[X]%

**Fontes & Pressupostos:**
- Margem setor: [INE 2023 / Racius médias / Estimativa conservadora* com disclaimer]
- Produtividade: [Estudos académicos / Benchmarks indústria / Literatura vendedor]
- Qualidade: [ROI tools similares / Case studies / Estimativa conservadora]

*Se dados oficiais INE indisponíveis para CAE específico, usar estimativa conservadora baseada em CAE agregado superior (ex: CAE 620 se CAE 62010 não disponível) + disclaimer explícito.

💡 **Nota:** Cálculo conservador (cenário base). Upside potencial maior se execução excelente e adoção equipa rápida.

---

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

## H) CHECKLIST SUBMISSÃO (TICKABLE)
Lista verificação com checkboxes [ ]:
- [ ] Certificação PME válida [citar fonte]
- [ ] Certidão permanente empresa
- [ ] IES [ano] (Quadros específicos necessários)
- [ ] Declaração situação tributária/contributiva regularizada
- [ ] Comprovativo RCBE atualizado
- [ ] Memória descritiva projeto detalhada
- [ ] Orçamentos fornecedores (3 cotações para valores >€5k)
- [ ] Plano formação detalhado (se aplicável)
- [ ] Contratos/cartas intenção (se aplicável)
- [ ] Declaração cumprimento DNSH [citar checklist]
- [ ] Declaração não duplicação financiamento UE
- [ ] Declaração capacidade co-financiamento
- [ ] Business case/análise viabilidade económica
- [ ] Política RGPD empresa + DPAs fornecedores
- [ ] Cronograma Gantt detalhado
- [ ] Declaração auxílios de minimis recebidos (últimos 3 anos)
- [ ] Comprovativo titularidade conta bancária
- [ ] Procuração (se representante legal diferente)

## I) COPY MAP SIGA-BF (Mapa Correspondência)
Tabela com 3 colunas para copy-paste direto:
| Campo SIGA-BF | Valor a Copiar | Fonte de Validação |
|---------------|----------------|---------------------|
| NIF Beneficiário | [valor] | Certidão permanente |
| Denominação Social | [valor completo] | Certidão permanente |
| CAE Principal | [código 5 dígitos] | Certidão permanente |
| Região NUTS II | [código] | Código INE [localidade] |
| Dimensão Empresa | [Micro/Pequena/Média] | Certificação PME IAPMEI |
| Investimento Total Elegível | €[valor] | Orçamento detalhado anexo |
| Taxa Incentivo Base | [%] | [Aviso, p.X, art.Y] |
| Incentivo Total Solicitado | €[valor] | Cálculo: Investimento × Taxa |
| Co-financiamento Empresa | €[valor] | Declaração capacidade |
| Prazo Execução (meses) | [X] | Cronograma Gantt |
| Data Início Prevista | [DD/MM/AAAA] | Pós-aprovação estimada |
| Data Fim Prevista | [DD/MM/AAAA] | Cronograma + prazo |
| Postos Trabalho Criados | [nº] | Declaração beneficiário |
| Crescimento VAB Projetado | +[%] | Business case |
| Código Tipologia Investimento | [código] | [Aviso, anexo] |
| Domínio Investimento | [código domínio] | [Aviso, lista] |
| Objetivos Específicos UE | [códigos] | Regulamento UE anexo |

## J) GESTÃO DE RISCOS (Matriz Detalhada)
Tabela 6 colunas para gestão proativa:
| Risco | Probabilidade | Impacto (€) | Mitigação | Contingência | Responsável |
|-------|---------------|-------------|-----------|--------------|-------------|
| RGPD/Privacidade dados | [Baixa/Média/Alta] | €[X] | [ações preventivas] | [plano B] | [role/cargo] |
| DNSH compliance | [Baixa/Média/Alta] | €[X] | [validação prévia] | [alternativas] | [role] |
| Duplo financiamento UE | [Baixa/Média/Alta] | €[X] | [controlo interno] | [correção] | [role] |
| Atraso execução projeto | [Baixa/Média/Alta] | €[X] | [buffer temporal] | [reescalonamento] | [role] |
| Fornecedor falha entrega | [Baixa/Média/Alta] | €[X] | [fornecedores backup] | [alternativas] | [role] |
| Adoção baixa equipa | [Baixa/Média/Alta] | €[X] | [formação intensiva] | [apoio externo] | [role] |
| Mudança legislação | [Baixa/Média/Alta] | €[X] | [monitorização] | [adaptação] | [role] |
| Ultrapassar orçamento | [Baixa/Média/Alta] | €[X] | [margem segurança] | [redução âmbito] | [role] |

## K) 🔍 AUDIT TRAIL & RASTREABILIDADE

### METADADOS SESSÃO
| Atributo | Valor |
|----------|-------|
| **ID Sessão** | [formato: EMPRESA-CAE-YYYYMMDD-v3.0] |
| **Data Geração** | [YYYY-MM-DDTHH:MM:SSZ formato ISO-8601] |
| **Modelo IA** | Claude Sonnet 4.5 (claude-sonnet-4-5-20250929) |
| **Sistema** | Archon Knowledge Engine v3.0 Ultra-Premium |
| **Autor** | Análise automática (validação humana SEMPRE requerida) |

---

### FONTES DOCUMENTAIS
| Tipo | Documento | Versão | Data Publicação |
|------|-----------|--------|-----------------|
| **Aviso** | [Aviso X/C0X-iXX.XX/YYYY] | [versão se aplicável] | [DD/MM/AAAA] |
| **Portaria** | [Portaria nº X/YYYY] | - | [DD/MM/AAAA] |
| **Regulamento UE** | [Reg. (UE) X/YYYY] | - | [DD/MM/AAAA] |
| **Dados Empresa** | [eInforma / Racius / Website oficial / **Declarado cliente**] | - | [data consulta] |

---

### ⚠️ PRESSUPOSTOS ASSUMIDOS & VALIDAÇÃO REQUERIDA

IMPORTANTE: Análise baseada em dados DECLARADOS. Validação obrigatória antes submissão oficial.

| Pressuposto | Fonte Atual | Validação Obrigatória Antes Submissão |
|-------------|-------------|---------------------------------------|
| Faturação €[X] | Declarado cliente | ⚠️ **VALIDAR com IES [ano], Quadro 04 (Vendas + Prestações Serviços)** |
| [N] funcionários | Declarado cliente | ⚠️ **VALIDAR com IES [ano], Quadro 07 (Número médio trabalhadores)** |
| CAE [código] | Declarado cliente | ✅ **CONFIRMAR com Certidão Permanente (secção "Objeto Social")** |
| Investimento €[Y] | Estimativa preliminar | ⚠️ **OBTER cotações formais 3 fornecedores (obrigatório >€5k)** |
| Co-financiamento €[Z] | Capacidade declarada | ⚠️ **VALIDAR com extratos bancários OU pré-aprovação linha crédito** |
| Datas/prazos | Cálculo estimado | ⚠️ **CONFIRMAR no portal oficial PT2030 antes submissão** |

---

### 🔒 DISCLAIMER LEGAL

**ATENÇÃO - LEIA CUIDADOSAMENTE:**

Esta análise é baseada em:
1. **Dados DECLARADOS** pelo cliente (não auditados independentemente)
2. **Interpretação automática** de regulamentação complexa via IA (validação jurídica recomendada)
3. **Knowledge base** atualizada até [mencionar data última atualização RAG se conhecida]
4. **Estimativas probabilísticas** de scoring/aprovação (decisão final EXCLUSIVA da Autoridade Gestão)

**ESTE DOCUMENTO NÃO CONSTITUI:**
- ❌ Aconselhamento jurídico vinculativo (consultar advogado se dúvidas legais)
- ❌ Garantia de aprovação candidatura (decisão é da entidade gestora Portugal 2030)
- ❌ Auditoria financeira certificada (ROC independente necessário para PTRF)
- ❌ Documento oficial para submissão (apenas ferramenta preparação interna)

**RECOMENDAÇÕES OBRIGATÓRIAS:**
- ✅ Validar TODOS os pressupostos acima antes submissão oficial
- ✅ Consultar entidade gestora (linha apoio PT2030) para esclarecimentos específicos aviso
- ✅ Guardar cópia desta análise apenas para referência interna (NÃO submeter como anexo)
- ✅ Contratar consultoria especializada se dúvidas complexidade técnica/legal

---

### 📊 METODOLOGIA ESTIMATIVAS

**Score Mérito Projeto (MP):**
- Fórmula aplicada: MP = 0,50 × Mérito Técnico + 0,50 × Mérito Económico
- Base legal: [Aviso, Anexo II - Grelha Avaliação Candidaturas]
- Calibração: [Benchmarking casos aprovados se disponível / Literatura académica setorial / Experiência histórica]

**Crescimento VAB (Valor Acrescentado Bruto):**
- Base cálculo: Faturação × Margem média setor [fonte: INE / Racius / Estimativa conservadora*]
- Impacto produtividade: [metodologia específica ao projeto, ex: estudos GitHub Copilot]
- Comparação setor: [INE 2023 se disponível, caso contrário disclaimer]

*Se dados oficiais INE indisponíveis para CAE específico, usar estimativa conservadora baseada em CAE agregado superior com disclaimer explícito.

**Probabilidade Aprovação:**
- Inputs considerados: Score MP + Adequação critérios elegibilidade + Completude documentação estimada
- NÃO considera: Fatores políticos, orçamento disponível fase específica, concorrência outras candidaturas
- Interpretação: Probabilística baseada em padrões históricos, NÃO determinística

---

### 🗂️ CONTROLO VERSÕES

| Versão | Data | Alterações Principais | Trigger/Razão |
|--------|------|----------------------|---------------|
| **1.0** | [YYYY-MM-DD HH:MM UTC] | Análise inicial baseada em query cliente | Primeira consulta |
| 1.1 | (Futura) | Atualização pós-validação IES + Certidão | Update dados financeiros auditados |
| 2.0 | (Futura) | Revisão pré-submissão final | Documentação completa obtida + cotações formais |

**Notas controlo versões:**
- Versões X.Y: X = mudanças estruturais projeto, Y = atualizações dados/validações
- Changelog detalhado disponível mediante solicitação
- Recomenda-se gerar v2.0 após obter IES oficial + cotações fornecedores + validação capacidade co-financiamento

## L) PRÓXIMAS AÇÕES
Box 💡 no fim de cada secção relevante com passo concreto seguinte.

## M) 🚀 PLANO AÇÃO CONSOLIDADO (4 SEMANAS)

**OBJETIVO:** Preparação completa documentação para submissão SIGA-BF.

Estrutura obrigatória:

### 📅 SEMANA 1 ([calcular datas: hoje até hoje+7 dias])
**Foco:** Documentação empresa + validações base

- [ ] **Certificação PME** - Obter via IAPMEI online | Prazo: 48h | Responsável: Administrativo
  - Portal: www.iapmei.pt → Serviços Online → Certificação PME
  - Documentos necessários: IES último ano + Certidão Permanente

- [ ] **Certidões Regularização** - AT + Segurança Social | Prazo: imediato online | Responsável: Contabilidade
  - AT: www.portaldasfinancas.gov.pt (validade <30 dias)
  - SS: www.seg-social.pt (validade <30 dias)

- [ ] **RCBE Validação** - Confirmar Registo Central Beneficiário Efetivo atualizado | Responsável: Jurídico/Admin
  - Portal: www.rcbe.justica.gov.pt
  - Validar beneficiários efetivos declarados corretos

[Adicionar 1-2 tarefas específicas do projeto se relevante]

---

### 📅 SEMANA 2-3 ([calcular datas: hoje+7 até hoje+21 dias])
**Foco:** Orçamentos + fornecedores + documentação técnica

- [ ] **3 Cotações Formais** - Obrigatório para items ≥€5.000 | Responsável: [adaptar ao projeto]
  - [Item principal investimento]: contactar 3 fornecedores
  - Formação certificada: contactar 3 entidades acreditadas
  - Consultoria [se aplicável]: contactar 3 empresas especializadas

- [ ] **Memória Descritiva** - Redigir documento 12-15 páginas | Responsável: Gestor Projeto
  - Estrutura: Identificação → Projeto → Investimento → Resultados → DNSH → Riscos
  - Incluir KPIs SMART mensuráveis
  - Fundamentar impacto VAB/emprego com dados

- [ ] **Cronograma Gantt** - Detalhar fases/marcos/entregáveis | Responsável: PM
  - Tool sugerido: MS Project / GanttProject / Excel
  - Incluir milestones críticos com critérios sucesso
  - Validar prazo total ≤ [X meses máximo do aviso]

[Adicionar tarefa específica se houver: ex: DPAs fornecedores cloud, plano formação detalhado]

---

### 📅 SEMANA 4 ([calcular datas: hoje+21 até hoje+28 dias])
**Foco:** Compilação final + revisão + submissão

- [ ] **Checklist Documentação** - Validar 100% documentos obrigatórios presentes | Responsável: PM
  - Usar checklist Secção H ([contar items] items)
  - Confirmar validades certidões (<30 dias)
  - Validar assinaturas digitais (Chave Móvel Digital)

- [ ] **Revisão Final** - CEO/Conselho Administração aprovação | Responsável: CEO
  - Validar orçamento vs capacidade co-financiamento disponível
  - Aprovar compromissos formais (emprego, VAB, prazos)
  - Assinar declarações responsabilidade

- [ ] **SUBMISSÃO SIGA-BF** - Upload plataforma + submissão formal | Responsável: Admin + PM
  - Data target: [calcular: deadline - 2 dias buffer] antes [HH:MM]
  - Realizar submissão teste (validar uploads)
  - Submissão final + guardar comprovativo PDF

---

**PROGRESSO GLOBAL:** 0/[contar tarefas acima] tarefas completas (0%)
**PRÓXIMO MILESTONE:** Certificação PME obtida (Semana 1, dia 3)
**RISCO CRÍTICO:** Atrasos cotações fornecedores → MITIGAÇÃO: Contactar já na Semana 1 para garantir resposta atempada

💡 **DICA:** Criar ficheiro Excel partilhado com equipa (colunas: Tarefa | Responsável | Prazo | Status | Notas) para tracking tempo real e accountability.

---

**FORMATO**: Português pt-PT, Markdown, citações obrigatórias [fonte, p.X], tom profissional/actionable. Cobrir secções A0-M (13 secções). Se faltar info: "❌ Info não disponível: [especificar]"
"""

            # Call Claude 4.5
            try:
                async with get_llm_client() as client:
                    safe_logfire_info(f"Calling LLM | model={llm_model}")

                    # Check if using AnthropicAdapter or OpenAI client
                    if hasattr(client, 'create_completion'):
                        # AnthropicAdapter
                        # Max tokens set to 18000 for PREMIUM quality output (12 sections A-L)
                        # Detailed examples: 18-item checklist, 17-field SIGA map, 8-risk matrix, audit trail
                        # CAE-specific use cases, Budget Gate, 3-tier scenarios
                        # Priority: Quality over speed (accepts 3-4min generation for ultra-premium reports)
                        response = await client.create_completion(
                            model=llm_model,
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt}
                            ],
                            temperature=0.3,
                            max_tokens=18000
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
                            max_tokens=18000
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
