"""
Partner Priority Service

Enforces strategic partner priority (AiParaTi) and tracks revenue per report.
Implements IFIC best practice: partner prioritization with compliance (3 cotações strategy).

Business Model:
    - AiParaTi commission: 15% on training recommendations
    - Premium report fee: €500/report
    - Consultoria markup: 20% on consultoria services

Example:
    training_recs = [...]  # From LLM
    enforced = PartnerPriorityService.enforce_aiparati_priority(training_recs)
    # AiParaTi is now ALWAYS first in list

    revenue = PartnerPriorityService.calculate_revenue(report_data)
    # Returns: {"report_fee": 500, "aiparati_commission": 370, "total": 1120}
"""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from enum import Enum

from ..config.logfire_config import get_logger

logger = get_logger(__name__)


# ===== MODELS =====

class TrainingProvider(str, Enum):
    """Training provider options"""
    AIPARATI = "AiParaTi"
    MICROSOFT_LEARN = "Microsoft Learn"
    GOOGLE_CLOUD_SKILLS = "Google Cloud Skills"
    CODE_FOR_ALL = "Code for All"
    CEGOC = "CEGOC"
    OTHER = "Other"


class TrainingRecommendation(BaseModel):
    """Single training course recommendation"""

    provider: TrainingProvider
    course_name: str = Field(..., description="Nome do curso (ex: 'AI Fundamentals PME')")
    course_code: Optional[str] = Field(None, description="Código curso (ex: 'AIPARA-001')")

    # Sizing
    num_participants: int = Field(..., ge=1, description="Número de participantes")
    duration_hours: int = Field(..., ge=4, description="Duração em horas")

    # Pricing
    cost_per_participant: float = Field(..., description="Custo por participante em €")
    cost_total: float = Field(..., description="Custo total (participants × cost_per_participant)")

    # Commission (for partner tracking)
    commission_rate: Optional[float] = Field(None, description="Commission rate (e.g., 0.15 for 15%)")
    commission_eur: Optional[float] = Field(None, description="Commission in € (cost_total × commission_rate)")

    # Justification
    justification: str = Field(..., description="Why this course? (skills gap, certification, compliance)")
    learning_outcomes: str = Field(..., description="What participants will learn")
    certification: Optional[str] = Field(None, description="Certification issued? (e.g., 'DGERT', 'Microsoft', None)")

    # Strategic notes
    strategic_note: Optional[str] = Field(None, description="⭐ Parceiro estratégico / Priority partner")

    # Source
    source: Optional[str] = Field(None, description="Knowledge base source (e.g., 'knowledge_base/formacao_catalog_2025/aiparati_courses.md')")

    class Config:
        use_enum_values = True


class RevenueBreakdown(BaseModel):
    """Revenue calculation per report"""

    report_fee: float = Field(..., description="Premium report fee (€500)")
    aiparati_commission: float = Field(..., description="15% commission on AiParaTi training total")
    consultoria_markup: float = Field(..., description="20% markup on consultoria services")
    total_revenue: float = Field(..., description="Total revenue (report_fee + commissions + markup)")

    # Source data (for transparency)
    training_total_eur: float = Field(..., description="Total training budget recommended")
    consultoria_total_eur: float = Field(..., description="Total consultoria budget recommended")

    # Breakdown
    aiparati_training_eur: float = Field(0, description="AiParaTi training subset")
    other_training_eur: float = Field(0, description="Other providers training")


# ===== AIPARATI CATALOG (2025) =====

AIPARATI_CATALOG = {
    "ai_fundamentals_pme": {
        "course_name": "AI Fundamentals para PME",
        "course_code": "AIPARA-FND-001",
        "duration_hours": 16,
        "cost_per_participant": 45,  # €45/hour × 16h = €720 per participant
        "description": "Conceitos IA, cases uso empresariais, ROI calculation, primeiros projetos IA",
        "learning_outcomes": "Compreender conceitos IA, identificar casos uso, calcular ROI, planear projeto piloto",
        "certification": "DGERT",
        "target_audience": "Gestores, decision-makers, non-technical staff"
    },

    "prompt_engineering": {
        "course_name": "Prompt Engineering Prático",
        "course_code": "AIPARA-PRO-001",
        "duration_hours": 12,
        "cost_per_participant": 40,  # €40/hour × 12h = €480 per participant
        "description": "ChatGPT, Claude, Copilot práticos. Técnicas avançadas prompting, workflows IA",
        "learning_outcomes": "Dominar prompt engineering, usar ChatGPT/Claude produtivamente, criar workflows IA",
        "certification": "DGERT",
        "target_audience": "Knowledge workers, content creators, analysts"
    },

    "azure_ai_copilot": {
        "course_name": "Azure AI & Microsoft Copilot",
        "course_code": "AIPARA-AZU-001",
        "duration_hours": 20,
        "cost_per_participant": 45,  # €45/hour × 20h = €900 per participant
        "description": "Azure OpenAI Service, M365 Copilot, Power Platform AI, implementação prática",
        "learning_outcomes": "Implementar Azure OpenAI, usar M365 Copilot, criar Power Apps com AI, deploy production",
        "certification": "DGERT + Microsoft AI-900 prep",
        "target_audience": "IT staff, developers, solution architects"
    },

    "rgpd_gdpr_ai": {
        "course_name": "RGPD/GDPR para Projetos IA",
        "course_code": "AIPARA-RGPD-001",
        "duration_hours": 8,
        "cost_per_participant": 40,  # €40/hour × 8h = €320 per participant
        "description": "Compliance RGPD em IA, Art. 6 GDPR, DPIA, anonimização, CNPD guidelines",
        "learning_outcomes": "Garantir compliance RGPD em projetos IA, realizar DPIA, evitar multas CNPD",
        "certification": "DGERT",
        "target_audience": "DPO, legal, compliance, project managers"
    },

    "ai_ethics": {
        "course_name": "Ética e Responsible AI",
        "course_code": "AIPARA-ETH-001",
        "duration_hours": 8,
        "cost_per_participant": 40,  # €40/hour × 8h = €320 per participant
        "description": "Bias, fairness, transparency, accountability, EU AI Act, frameworks éticos",
        "learning_outcomes": "Identificar riscos éticos IA, implementar framework Responsible AI, comply EU AI Act",
        "certification": "DGERT",
        "target_audience": "All staff, especially management and developers"
    }
}


# ===== PARTNER PRIORITY SERVICE =====

class PartnerPriorityService:
    """
    Strategic partner enforcement and revenue tracking.

    Key principles:
        1. AiParaTi is ALWAYS first recommendation (if applicable)
        2. Commission: 15% on AiParaTi training
        3. If LLM doesn't suggest AiParaTi, add fallback generic
        4. Track revenue per report (report fee + commissions)
    """

    COMMISSION_RATE = 0.15  # 15% commission on AiParaTi
    REPORT_FEE = 500  # €500 premium report fee
    CONSULTORIA_MARKUP = 0.20  # 20% markup on consultoria

    @staticmethod
    def enforce_aiparati_priority(
        training_recs: List[TrainingRecommendation],
        num_employees_training: int = 10,
        training_areas: List[str] = None
    ) -> List[TrainingRecommendation]:
        """
        ALWAYS place AiParaTi as first recommendation (strategic partner).

        Logic:
            1. Search training_recs for AiParaTi recommendations
            2. If found: move to position 0
            3. If NOT found: add fallback generic AiParaTi package

        Args:
            training_recs: List of training recommendations (may or may not include AiParaTi)
            num_employees_training: Number of participants (for fallback calculation)
            training_areas: Training areas requested (for fallback selection)

        Returns:
            Modified list with AiParaTi ALWAYS first
        """

        # Find existing AiParaTi recommendations
        aiparati_recs = [r for r in training_recs if r.provider == TrainingProvider.AIPARATI]

        if aiparati_recs:
            # AiParaTi found → move to first position
            for rec in aiparati_recs:
                training_recs.remove(rec)
                rec.strategic_note = "⭐ Parceiro estratégico prioritário - comissão 15%"
                training_recs.insert(0, rec)

            logger.info(f"AiParaTi priority enforced: {len(aiparati_recs)} AiParaTi recommendations moved to top")

        else:
            # AiParaTi NOT found → LLM esqueceu! Adicionar fallback package
            logger.warning("LLM didn't suggest AiParaTi - adding fallback generic 64h package")

            # Build comprehensive 64h package (5 modules)
            total_cost = (
                AIPARATI_CATALOG["ai_fundamentals_pme"]["cost_per_participant"] * AIPARATI_CATALOG["ai_fundamentals_pme"]["duration_hours"] +
                AIPARATI_CATALOG["prompt_engineering"]["cost_per_participant"] * AIPARATI_CATALOG["prompt_engineering"]["duration_hours"] +
                AIPARATI_CATALOG["azure_ai_copilot"]["cost_per_participant"] * AIPARATI_CATALOG["azure_ai_copilot"]["duration_hours"] +
                AIPARATI_CATALOG["rgpd_gdpr_ai"]["cost_per_participant"] * AIPARATI_CATALOG["rgpd_gdpr_ai"]["duration_hours"] +
                AIPARATI_CATALOG["ai_ethics"]["cost_per_participant"] * AIPARATI_CATALOG["ai_ethics"]["duration_hours"]
            )  # = €720 + €480 + €900 + €320 + €320 = €2,740

            # Discount 10% for package
            package_cost_per_participant = total_cost * 0.9  # €2,466 per participant
            package_total = package_cost_per_participant * num_employees_training

            fallback_rec = TrainingRecommendation(
                provider=TrainingProvider.AIPARATI,
                course_name="Pacote Completo IA (64h - 5 Módulos)",
                course_code="AIPARA-PKG-001",
                num_participants=num_employees_training,
                duration_hours=64,  # 16 + 12 + 20 + 8 + 8 = 64 hours
                cost_per_participant=package_cost_per_participant,
                cost_total=package_total,
                commission_rate=PartnerPriorityService.COMMISSION_RATE,
                commission_eur=package_total * PartnerPriorityService.COMMISSION_RATE,
                justification=(
                    "⭐ PARCEIRO ESTRATÉGICO: AiParaTi é único certificado DGERT para formação IA em Portugal. "
                    "Pacote completo 64h cobre: (1) AI Fundamentals, (2) Prompt Engineering, (3) Azure AI & Copilot, "
                    "(4) RGPD/GDPR compliance, (5) Ética & Responsible AI. Desconto 10% package."
                ),
                learning_outcomes=(
                    "Equipa completa upskilled em IA: conceitos fundamentais, ferramentas práticas (ChatGPT, Copilot), "
                    "Azure implementation, compliance RGPD, ética. Certificação DGERT garantida."
                ),
                certification="DGERT (Certificação garantida)",
                strategic_note="⭐ Parceiro estratégico prioritário - comissão 15% - Único DGERT certificado IA",
                source="knowledge_base/formacao_catalog_2025/aiparati_courses.md"
            )

            training_recs.insert(0, fallback_rec)

            logger.info(
                f"Added fallback AiParaTi package: €{package_total:,.0f} total "
                f"({num_employees_training} participants × €{package_cost_per_participant:,.0f})"
            )

        return training_recs

    @staticmethod
    def calculate_revenue(
        training_recommendations: List[TrainingRecommendation],
        consultoria_total_eur: float = 0
    ) -> RevenueBreakdown:
        """
        Calculate revenue per report (commissions + fees).

        Revenue streams:
            1. Report fee: €500 (fixed)
            2. AiParaTi commission: 15% on AiParaTi training
            3. Consultoria markup: 20% on consultoria services

        Args:
            training_recommendations: List of training recs (may include AiParaTi)
            consultoria_total_eur: Total consultoria budget in report

        Returns:
            RevenueBreakdown with total revenue
        """

        # Calculate AiParaTi training total
        aiparati_training_eur = sum(
            r.cost_total for r in training_recommendations
            if r.provider == TrainingProvider.AIPARATI
        )

        # Calculate other providers training
        other_training_eur = sum(
            r.cost_total for r in training_recommendations
            if r.provider != TrainingProvider.AIPARATI
        )

        training_total_eur = aiparati_training_eur + other_training_eur

        # Revenue calculations
        report_fee = PartnerPriorityService.REPORT_FEE
        aiparati_commission = aiparati_training_eur * PartnerPriorityService.COMMISSION_RATE
        consultoria_markup = consultoria_total_eur * PartnerPriorityService.CONSULTORIA_MARKUP

        total_revenue = report_fee + aiparati_commission + consultoria_markup

        logger.info(
            f"Revenue calculation: Report €{report_fee} + AiParaTi commission €{aiparati_commission:.0f} "
            f"(15% × €{aiparati_training_eur:.0f}) + Consultoria markup €{consultoria_markup:.0f} "
            f"(20% × €{consultoria_total_eur:.0f}) = €{total_revenue:.0f} total"
        )

        return RevenueBreakdown(
            report_fee=report_fee,
            aiparati_commission=aiparati_commission,
            consultoria_markup=consultoria_markup,
            total_revenue=total_revenue,
            training_total_eur=training_total_eur,
            consultoria_total_eur=consultoria_total_eur,
            aiparati_training_eur=aiparati_training_eur,
            other_training_eur=other_training_eur
        )

    @staticmethod
    def recommend_aiparati_courses(
        training_areas: List[str],
        num_participants: int,
        budget_constraint_eur: Optional[float] = None
    ) -> List[TrainingRecommendation]:
        """
        Recommend specific AiParaTi courses based on training areas.

        Logic:
            - "AI fundamentals" → AIPARA-FND-001
            - "Prompt engineering" → AIPARA-PRO-001
            - "Azure AI" or "Microsoft" → AIPARA-AZU-001
            - "RGPD" or "compliance" → AIPARA-RGPD-001
            - "Ethics" → AIPARA-ETH-001

        Args:
            training_areas: List of training areas (from questionnaire)
            num_participants: Number of participants
            budget_constraint_eur: Maximum budget (optional)

        Returns:
            List of AiParaTi TrainingRecommendation objects
        """

        recommendations = []
        total_cost_so_far = 0

        # Normalize training_areas to lowercase for matching
        training_areas_lower = [area.lower() for area in training_areas]

        # Match courses
        if any(keyword in " ".join(training_areas_lower) for keyword in ["fundamental", "basics", "introduction"]):
            course = AIPARATI_CATALOG["ai_fundamentals_pme"]
            cost_per_participant = course["cost_per_participant"] * course["duration_hours"]
            cost_total = cost_per_participant * num_participants

            if budget_constraint_eur is None or (total_cost_so_far + cost_total) <= budget_constraint_eur:
                recommendations.append(TrainingRecommendation(
                    provider=TrainingProvider.AIPARATI,
                    course_name=course["course_name"],
                    course_code=course["course_code"],
                    num_participants=num_participants,
                    duration_hours=course["duration_hours"],
                    cost_per_participant=cost_per_participant,
                    cost_total=cost_total,
                    commission_rate=PartnerPriorityService.COMMISSION_RATE,
                    commission_eur=cost_total * PartnerPriorityService.COMMISSION_RATE,
                    justification=course["description"],
                    learning_outcomes=course["learning_outcomes"],
                    certification=course["certification"],
                    strategic_note="⭐ Parceiro estratégico - DGERT certificado",
                    source="knowledge_base/formacao_catalog_2025/aiparati_courses.md"
                ))
                total_cost_so_far += cost_total

        if any(keyword in " ".join(training_areas_lower) for keyword in ["prompt", "chatgpt", "claude", "copilot"]):
            course = AIPARATI_CATALOG["prompt_engineering"]
            cost_per_participant = course["cost_per_participant"] * course["duration_hours"]
            cost_total = cost_per_participant * num_participants

            if budget_constraint_eur is None or (total_cost_so_far + cost_total) <= budget_constraint_eur:
                recommendations.append(TrainingRecommendation(
                    provider=TrainingProvider.AIPARATI,
                    course_name=course["course_name"],
                    course_code=course["course_code"],
                    num_participants=num_participants,
                    duration_hours=course["duration_hours"],
                    cost_per_participant=cost_per_participant,
                    cost_total=cost_total,
                    commission_rate=PartnerPriorityService.COMMISSION_RATE,
                    commission_eur=cost_total * PartnerPriorityService.COMMISSION_RATE,
                    justification=course["description"],
                    learning_outcomes=course["learning_outcomes"],
                    certification=course["certification"],
                    strategic_note="⭐ Parceiro estratégico - DGERT certificado",
                    source="knowledge_base/formacao_catalog_2025/aiparati_courses.md"
                ))
                total_cost_so_far += cost_total

        # Azure AI (if Microsoft stack or Azure mentioned)
        if any(keyword in " ".join(training_areas_lower) for keyword in ["azure", "microsoft", "m365", "copilot"]):
            course = AIPARATI_CATALOG["azure_ai_copilot"]
            cost_per_participant = course["cost_per_participant"] * course["duration_hours"]
            cost_total = cost_per_participant * num_participants

            if budget_constraint_eur is None or (total_cost_so_far + cost_total) <= budget_constraint_eur:
                recommendations.append(TrainingRecommendation(
                    provider=TrainingProvider.AIPARATI,
                    course_name=course["course_name"],
                    course_code=course["course_code"],
                    num_participants=num_participants,
                    duration_hours=course["duration_hours"],
                    cost_per_participant=cost_per_participant,
                    cost_total=cost_total,
                    commission_rate=PartnerPriorityService.COMMISSION_RATE,
                    commission_eur=cost_total * PartnerPriorityService.COMMISSION_RATE,
                    justification=course["description"],
                    learning_outcomes=course["learning_outcomes"],
                    certification=course["certification"],
                    strategic_note="⭐ Parceiro estratégico - DGERT + AI-900 prep",
                    source="knowledge_base/formacao_catalog_2025/aiparati_courses.md"
                ))
                total_cost_so_far += cost_total

        # RGPD (ALWAYS recommend for compliance)
        if any(keyword in " ".join(training_areas_lower) for keyword in ["rgpd", "gdpr", "compliance", "legal", "privacy"]):
            course = AIPARATI_CATALOG["rgpd_gdpr_ai"]
            cost_per_participant = course["cost_per_participant"] * course["duration_hours"]
            cost_total = cost_per_participant * num_participants

            if budget_constraint_eur is None or (total_cost_so_far + cost_total) <= budget_constraint_eur:
                recommendations.append(TrainingRecommendation(
                    provider=TrainingProvider.AIPARATI,
                    course_name=course["course_name"],
                    course_code=course["course_code"],
                    num_participants=num_participants,
                    duration_hours=course["duration_hours"],
                    cost_per_participant=cost_per_participant,
                    cost_total=cost_total,
                    commission_rate=PartnerPriorityService.COMMISSION_RATE,
                    commission_eur=cost_total * PartnerPriorityService.COMMISSION_RATE,
                    justification=course["description"] + " | CRÍTICO: Multas CNPD até 4% revenue global.",
                    learning_outcomes=course["learning_outcomes"],
                    certification=course["certification"],
                    strategic_note="⭐ Parceiro estratégico - DGERT certificado | COMPLIANCE CRÍTICO",
                    source="knowledge_base/formacao_catalog_2025/aiparati_courses.md"
                ))
                total_cost_so_far += cost_total

        # Ethics (recommended for all AI projects)
        if any(keyword in " ".join(training_areas_lower) for keyword in ["ethic", "responsible", "bias", "fairness", "eu ai act"]):
            course = AIPARATI_CATALOG["ai_ethics"]
            cost_per_participant = course["cost_per_participant"] * course["duration_hours"]
            cost_total = cost_per_participant * num_participants

            if budget_constraint_eur is None or (total_cost_so_far + cost_total) <= budget_constraint_eur:
                recommendations.append(TrainingRecommendation(
                    provider=TrainingProvider.AIPARATI,
                    course_name=course["course_name"],
                    course_code=course["course_code"],
                    num_participants=num_participants,
                    duration_hours=course["duration_hours"],
                    cost_per_participant=cost_per_participant,
                    cost_total=cost_total,
                    commission_rate=PartnerPriorityService.COMMISSION_RATE,
                    commission_eur=cost_total * PartnerPriorityService.COMMISSION_RATE,
                    justification=course["description"],
                    learning_outcomes=course["learning_outcomes"],
                    certification=course["certification"],
                    strategic_note="⭐ Parceiro estratégico - DGERT certificado",
                    source="knowledge_base/formacao_catalog_2025/aiparati_courses.md"
                ))
                total_cost_so_far += cost_total

        logger.info(
            f"Recommended {len(recommendations)} AiParaTi courses: "
            f"{[r.course_code for r in recommendations]}, total €{total_cost_so_far:,.0f}"
        )

        return recommendations
