"""
Questionnaire API Routes

Handles diagnostic questionnaire submission and RAG query construction.

Endpoints:
    POST /api/questionnaire/submit - Submit questionnaire, trigger RAG search
    GET /api/questionnaire/{id} - Retrieve questionnaire + recommendations
    POST /api/questionnaire/autofill - Auto-fill from NIF (eInforma API)

Integration:
    - Stores questionnaire in PostgreSQL (archon_questionnaires table)
    - Constructs targeted RAG queries from answers
    - Triggers LLM synthesis for personalized recommendations
    - Returns recommendations in structured format

Example:
    POST /api/questionnaire/submit
    {
        "company_name": "CodeLab Portugal",
        "nif": "123456789",
        "email_system": "google",
        ...
    }

    Response:
    {
        "questionnaire_id": "uuid",
        "status": "processing",
        "rag_queries": ["..."],
        "estimated_completion_seconds": 45
    }
"""

from typing import Dict, List, Any
from uuid import uuid4
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime

from ..models.questionnaire import (
    DiagnosticQuestionnaire,
    QuestionnaireResponse,
    CompanyData,
    EmailProvider,
    CloudStorage,
    ProductivitySuite,
    CRMSystem,
    ProjectManagement,
    CommunicationPlatform,
    InvestmentRange
)
from ..services.credential_service import credential_service
from ..services.llm_provider_service import get_llm_client
from ..config.logfire_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/questionnaire", tags=["questionnaire"])


# ===== HELPER: RAG QUERY CONSTRUCTION =====

def construct_rag_queries(questionnaire: DiagnosticQuestionnaire) -> List[str]:
    """
    Transform questionnaire into targeted RAG queries (IFIC pattern).

    Strategy:
        - Query 1: Tech stack-specific SaaS recommendations
        - Query 2: Industry-specific AI use cases (CAE-based)
        - Query 3: Budget optimization patterns
        - Query 4: Training catalog (AiParaTi priority)
        - Query 5: Compliance rules (Aviso 03/C05)

    Returns:
        List of 5 RAG query strings optimized for hybrid search
    """

    queries = []

    # Query 1: SaaS Recommendations (ecosystem-driven using new enums)
    if questionnaire.email_system == EmailProvider.GMAIL:
        queries.append(
            f"Melhores ferramentas SaaS 2025 Google Workspace integration "
            f"Gemini Business pricing {questionnaire.num_employees} users"
        )
    elif questionnaire.email_system == EmailProvider.MICROSOFT_365:
        queries.append(
            f"Microsoft 365 Copilot SaaS tools 2025 pricing Azure integration "
            f"{questionnaire.num_employees} users Office 365"
        )
    else:
        queries.append(
            f"Best SaaS AI tools 2025 agnostic stack ChatGPT Claude Copilot "
            f"{questionnaire.num_employees} users productivity gains ROI"
        )

    # Developers? Add GitHub Copilot query
    if questionnaire.has_dev_team and questionnaire.num_developers:
        queries.append(
            f"GitHub Copilot Business pricing 2025 {questionnaire.num_developers} developers "
            f"productivity gains ROI code completion acceptance rates study"
        )

    # Query 2: Industry-Specific Use Cases (CAE-based)
    queries.append(
        f"Casos uso IA setor {questionnaire.industry_sector.value} CAE {questionnaire.cae_code} "
        f"Portugal 2025 success stories PME {questionnaire.company_size.value} "
        f"revenue {questionnaire.annual_revenue}€ implementation patterns"
    )

    # Query 3: Budget Optimization
    queries.append(
        f"Otimização orçamento €{questionnaire.desired_investment:,.0f} grant funding "
        f"Vale Inovação Vale Formação IFIC distribuição SaaS formação consultoria "
        f"RH dedicados equipamentos maximização incentivo 75%"
    )

    # Query 4: Training Recommendations (AiParaTi priority)
    if questionnaire.training_priority and questionnaire.num_employees_training:
        training_areas_str = ", ".join(questionnaire.training_areas) if questionnaire.training_areas else "AI fundamentals, prompt engineering"
        queries.append(
            f"Formação IA {training_areas_str} {questionnaire.num_employees_training} colaboradores "
            f"certificação DGERT Portugal 2025 AiParaTi cursos pricing "
            f"Azure OpenAI Microsoft Learn Google Cloud Skills"
        )

    # Query 5: Compliance & Eligibility
    queries.append(
        f"Aviso 03/C05 elegibilidade PME {questionnaire.num_employees} colaboradores "
        f"CAE {questionnaire.cae_code} investimento €{questionnaire.desired_investment:,.0f} "
        f"duração {questionnaire.project_duration_months} meses compliance checklist "
        f"despesas elegíveis RH software formação consultoria equipamentos limites"
    )

    logger.info(f"Constructed {len(queries)} RAG queries from questionnaire")
    return queries


# ===== ENDPOINTS =====

@router.post("/submit", response_model=QuestionnaireResponse)
async def submit_questionnaire(questionnaire: DiagnosticQuestionnaire):
    """
    Submit diagnostic questionnaire and trigger personalized analysis.

    Flow:
        1. Validate questionnaire (Pydantic auto-validation)
        2. Generate unique questionnaire_id
        3. Store in PostgreSQL (archon_questionnaires table)
        4. Construct RAG queries from answers
        5. Return questionnaire_id + status

    Notes:
        - RAG search + LLM synthesis happens asynchronously
        - Use GET /api/questionnaire/{id} to poll for results
        - Estimated completion: 45-60 seconds
    """

    try:
        # Generate unique ID
        questionnaire_id = str(uuid4())

        logger.info(
            f"Received questionnaire submission: {questionnaire.company_name} "
            f"(NIF: {questionnaire.nif}, Investment: €{questionnaire.desired_investment:,.0f})"
        )

        # Construct RAG queries
        rag_queries = construct_rag_queries(questionnaire)

        # Store in PostgreSQL
        supabase = credential_service._get_supabase_client()

        questionnaire_data = {
            "id": questionnaire_id,
            "company_name": questionnaire.company_name,
            "nif": questionnaire.nif,
            "data": questionnaire.dict(),  # Full questionnaire as JSONB
            "rag_queries": rag_queries,
            "status": "pending_processing",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        result = supabase.table("archon_questionnaires").insert(questionnaire_data).execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to store questionnaire in database")

        logger.info(f"Questionnaire {questionnaire_id} stored successfully with {len(rag_queries)} RAG queries")

        # Trigger async RAG search + LLM synthesis (background task)
        # Note: In production, use Celery/Redis queue for background processing
        # For now, return immediately with pending status

        return QuestionnaireResponse(
            questionnaire_id=questionnaire_id,
            company_name=questionnaire.company_name,
            investment_range=questionnaire.investment_range.value,
            status="pending_processing",
            message=f"Questionário recebido. A processar {len(rag_queries)} queries RAG. Estimativa: 45-60 segundos."
        )

    except Exception as e:
        logger.error(f"Error submitting questionnaire: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing questionnaire: {str(e)}")


@router.get("/{questionnaire_id}", response_model=Dict[str, Any])
async def get_questionnaire(questionnaire_id: str):
    """
    Retrieve questionnaire + recommendations by ID.

    Returns:
        {
            "questionnaire_id": "uuid",
            "company_name": "...",
            "status": "pending_processing" | "rag_search_completed" | "recommendations_ready",
            "data": {...},  # Original questionnaire
            "rag_results": {...},  # RAG search results (if completed)
            "recommendations": {...},  # LLM-generated recommendations (if ready)
            "created_at": "2025-01-15T10:30:00Z",
            "updated_at": "2025-01-15T10:31:45Z"
        }
    """

    try:
        supabase = credential_service._get_supabase_client()

        result = supabase.table("archon_questionnaires") \
            .select("*") \
            .eq("id", questionnaire_id) \
            .execute()

        if not result.data or len(result.data) == 0:
            raise HTTPException(status_code=404, detail=f"Questionnaire {questionnaire_id} not found")

        questionnaire_record = result.data[0]

        logger.info(f"Retrieved questionnaire {questionnaire_id} with status: {questionnaire_record.get('status')}")

        return questionnaire_record

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving questionnaire {questionnaire_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving questionnaire: {str(e)}")


@router.post("/autofill", response_model=CompanyData)
async def autofill_from_nif(nif: str):
    """
    Auto-fill company data from NIF using external data sources.

    Strategy (fallback cascade):
        1. eInforma API (primary, €20/report)
        2. Racius scraping (fallback, €5/report)
        3. Manual input (user confirms)

    Example:
        POST /api/questionnaire/autofill
        {
            "nif": "123456789"
        }

        Response:
        {
            "nif": "123456789",
            "legal_name": "CodeLab Portugal Lda",
            "cae_primary": "62010",
            "address": "Rua X, Lisboa",
            "revenue_estimate": 980000,
            "employees_estimate": 18,
            "source": "einforma"
        }

    Notes:
        - This endpoint will be implemented in data_sources_service.py
        - For MVP, returns mock data
        - Production: integrate eInforma API (requires API key)
    """

    # TODO: Implement DataSourcesService.auto_fill_from_nif(nif)
    # For now, return mock data for testing

    logger.warning(f"Auto-fill from NIF {nif} - using MOCK data (eInforma integration pending)")

    # Mock data (CodeLab Portugal example)
    mock_data = CompanyData(
        nif=nif,
        legal_name="CodeLab Portugal Lda (MOCK DATA)",
        cae_primary="62010",
        address="Rua de São Bento 123, 1200-109 Lisboa (MOCK)",
        revenue_estimate=980000,
        employees_estimate=18,
        founded_date="2018-03-15",
        risk_rating="LOW",
        source="mock"
    )

    return mock_data


@router.delete("/{questionnaire_id}")
async def delete_questionnaire(questionnaire_id: str):
    """
    Delete questionnaire by ID (for testing/cleanup).

    Returns:
        {"message": "Questionnaire deleted successfully"}
    """

    try:
        supabase = credential_service._get_supabase_client()

        result = supabase.table("archon_questionnaires") \
            .delete() \
            .eq("id", questionnaire_id) \
            .execute()

        if not result.data or len(result.data) == 0:
            raise HTTPException(status_code=404, detail=f"Questionnaire {questionnaire_id} not found")

        logger.info(f"Deleted questionnaire {questionnaire_id}")

        return {"message": f"Questionnaire {questionnaire_id} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting questionnaire {questionnaire_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting questionnaire: {str(e)}")
