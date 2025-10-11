"""
SCQA Framework Service

Generates executive summary using McKinsey SCQA (Situation-Complication-Question-Answer) framework.
Implements IFIC best practice: storytelling for executive engagement.

SCQA Components:
    S (Situation): Facts everyone agrees on
        - Company profile, market context, baseline state

    C (Complication): Problem disrupting situation
        - Competitive pressure, market changes, risk of inaction

    Q (Question): What should we do?
        - Central question project answers

    A (Answer): Solution + action plan
        - Project summary, investment, outcomes, timeline

Example:
    scqa = SCQAFrameworkService.generate(questionnaire, market_context)
    # Returns: SCQA(
    #     situation="CodeLab Portugal opera setor TI com 18 colaboradores...",
    #     complication="Concorrência adotou IA (75% mercado), risco perda quota...",
    #     question="Como acelerar adoção IA em 12 meses minimizando risco?",
    #     answer="Candidatura Vale Inovação €95k implementa 5 casos uso IA..."
    # )

    html = SCQAFrameworkService.render_to_html(scqa)
    # Returns: 4 colored blocks (S/C/Q/A) with visual framework
"""

from typing import Optional, Dict, List
from pydantic import BaseModel, Field

from ..models.questionnaire import DiagnosticQuestionnaire
from ..services.budget_optimizer_service import BudgetPath
from ..services.scoring_calculator_service import ScoringBreakdown
from ..config.logfire_config import get_logger

logger = get_logger(__name__)


# ===== MODELS =====

class SCQA(BaseModel):
    """SCQA framework components"""

    situation: str = Field(..., description="Situation: Facts everyone agrees (company, market)")
    situation_bullets: List[str] = Field(default=[], description="Key facts as bullet points")

    complication: str = Field(..., description="Complication: Problem disrupting situation")
    complication_bullets: List[str] = Field(default=[], description="Key problems as bullets")

    question: str = Field(..., description="Question: Central question project answers")

    answer: str = Field(..., description="Answer: Solution + action plan summary")
    answer_bullets: List[str] = Field(default=[], description="Key outcomes as bullets")

    # Supporting data
    urgency_score: float = Field(default=7.0, ge=0, le=10, description="Urgency level (0-10)")
    market_context: Optional[Dict[str, str]] = Field(None, description="Market statistics/context")


# ===== SCQA FRAMEWORK SERVICE =====

class SCQAFrameworkService:
    """
    Generate SCQA-based executive summary.

    Process:
        1. Extract facts from questionnaire → Situation
        2. Identify market pressures/risks → Complication
        3. Frame central question → Question
        4. Summarize project solution → Answer
    """

    @staticmethod
    def generate(
        questionnaire: DiagnosticQuestionnaire,
        scoring: Optional[ScoringBreakdown] = None,
        budget_path: Optional[BudgetPath] = None,
        market_context: Optional[Dict[str, str]] = None
    ) -> SCQA:
        """
        Generate SCQA framework from questionnaire + project data.

        Args:
            questionnaire: Diagnostic questionnaire
            scoring: Optional scoring breakdown
            budget_path: Optional budget expansion path
            market_context: Optional market statistics (from RAG search)

        Returns:
            SCQA object with S/C/Q/A components
        """

        # ===== SITUATION: Facts everyone agrees =====

        situation_bullets = [
            f"{questionnaire.company_name} opera no setor {questionnaire.industry_sector.value}",
            f"{questionnaire.num_employees} colaboradores, faturação anual €{questionnaire.annual_revenue:,.0f}",
            f"CAE {questionnaire.cae_code}, {questionnaire.company_size.value.upper()} empresa (PME)",
            f"Tech stack: {questionnaire.email_system.value.title()} ecosystem ({questionnaire.productivity_suite.value})"
        ]

        if questionnaire.has_dev_team:
            situation_bullets.append(f"Equipa desenvolvimento: {questionnaire.num_developers} developers")

        # Add market context if available
        if market_context:
            for key, value in market_context.items():
                situation_bullets.append(f"{key}: {value}")
        else:
            # Default market context (from IFIC report)
            situation_bullets.append("Mercado português PME: 68% sem adoção IA (INE 2024)")
            situation_bullets.append("Setor TI crescimento 12% anual, pressão competitiva elevada")

        situation = (
            f"{questionnaire.company_name} é uma {questionnaire.company_size.value.upper()} empresa do setor "
            f"{questionnaire.industry_sector.value} com {questionnaire.num_employees} colaboradores e faturação anual "
            f"€{questionnaire.annual_revenue:,.0f}. Opera no mercado português onde 68% das PME ainda não adotaram IA, "
            f"criando janela de oportunidade competitiva mas também risco de ficar para trás."
        )

        # ===== COMPLICATION: Problem disrupting situation =====

        complication_bullets = []

        # Identify competitive pressure based on industry
        if questionnaire.industry_sector.value == "technology":
            competitor_adoption = "75% concorrência TI já usa IA"
            risk_quota = "15-20% quota mercado em risco 12-18 meses"
        else:
            competitor_adoption = "60% concorrência adotou IA"
            risk_quota = "10-15% quota mercado em risco 12-18 meses"

        complication_bullets.append(f"{competitor_adoption} (early adopters advantage)")
        complication_bullets.append(f"Risco perda quota mercado: {risk_quota}")

        # Identify internal gaps
        if not questionnaire.current_tools_paid:
            complication_bullets.append("Sem ferramentas IA pagas → produtividade inferior concorrência 25-40%")

        if questionnaire.training_priority:
            complication_bullets.append(f"{questionnaire.num_employees_training or 'Muitos'} colaboradores precisam upskilling IA urgente")

        # Digital maturity gap
        if questionnaire.intensity_level.value in ["light", "moderate"]:
            complication_bullets.append("Maturidade digital baixa/moderada → dificuldade competir em licitações")

        # Urgency factor
        complication_bullets.append("Janela competitiva fecha em 12-18 meses (tipping point adoção mercado)")

        complication = (
            f"{competitor_adoption}, criando pressão competitiva intensa. Risco perda {risk_quota} se não acelerar "
            f"adoção IA nos próximos 12 meses. Equipa precisa upskilling urgente ({questionnaire.num_employees_training or questionnaire.num_employees} colaboradores) "
            f"e ferramentas adequadas. Janela oportunidade fecha em 12-18 meses quando adoção IA se tornar commodity."
        )

        # ===== QUESTION: Central question =====

        question = (
            f"Como pode {questionnaire.company_name} acelerar adoção IA em {questionnaire.project_duration_months} meses, "
            f"minimizando risco técnico/financeiro, para manter posição competitiva e capturar quota mercado?"
        )

        # ===== ANSWER: Solution + action plan =====

        # Determine aviso based on use cases
        if questionnaire.training_priority:
            aviso_name = "Vale Formação + Vale Inovação"
        else:
            aviso_name = "Vale Inovação (Aviso 03/C05)"

        # Investment amount (use budget_path if available)
        if budget_path:
            investment_amount = budget_path.target_total
            subsidy_amount = budget_path.subsidy_75_percent
        else:
            investment_amount = questionnaire.desired_investment
            subsidy_amount = investment_amount * 0.75

        # Identify use cases count
        num_use_cases = len(questionnaire.use_cases)

        answer_bullets = [
            f"Investimento: €{investment_amount:,.0f} (subsídio 75% = €{subsidy_amount:,.0f})",
            f"{num_use_cases} casos uso IA prioritários: {', '.join(questionnaire.use_cases[:3])}",
        ]

        # Add jobs created if available
        if scoring:
            if scoring.jobs_created > 0:
                answer_bullets.append(f"Criação emprego: {scoring.jobs_created} postos trabalho permanentes")

            # Add VAB growth if available
            if scoring.vab_growth_percent > 0:
                answer_bullets.append(f"Crescimento VAB: {scoring.vab_growth_percent:.1f}% (Year 2)")

            # Add scoring
            answer_bullets.append(f"Score mérito: {scoring.MP_out_of_10:.1f}/10 (Classe {scoring.class_rating.value})")
            answer_bullets.append(f"Probabilidade aprovação: {scoring.approval_probability:.0f}%")
        else:
            # Defaults if no scoring
            answer_bullets.append(f"Duração: {questionnaire.project_duration_months} meses")
            answer_bullets.append("Probabilidade aprovação: 70-80% (com otimizações)")

        answer = (
            f"Candidatura {aviso_name} com investimento €{investment_amount:,.0f} (subsídio 75% = €{subsidy_amount:,.0f}) "
            f"implementa {num_use_cases} casos uso IA em {questionnaire.project_duration_months} meses: "
            f"{', '.join(questionnaire.use_cases[:3])}. "
        )

        if scoring:
            answer += (
                f"Cria {scoring.jobs_created} postos trabalho permanentes, crescimento VAB {scoring.vab_growth_percent:.1f}%. "
                f"Score mérito {scoring.MP_out_of_10:.1f}/10 (Classe {scoring.class_rating.value}), "
                f"probabilidade aprovação {scoring.approval_probability:.0f}%."
            )
        else:
            answer += (
                f"Projeto estruturado com formação equipa ({questionnaire.num_employees_training or 10} colaboradores), "
                f"ferramentas SaaS adequadas, e consultoria implementação. ROI esperado 18-24 meses."
            )

        # Calculate urgency score
        urgency_score = SCQAFrameworkService._calculate_urgency(
            competitor_adoption_percent=75 if questionnaire.industry_sector.value == "technology" else 60,
            has_current_tools=questionnaire.current_tools_paid,
            training_gap_percent=(questionnaire.num_employees_training or 0) / questionnaire.num_employees if questionnaire.num_employees > 0 else 0.5
        )

        logger.info(
            f"Generated SCQA framework: {questionnaire.company_name}, "
            f"investment €{investment_amount:,.0f}, urgency {urgency_score:.1f}/10"
        )

        return SCQA(
            situation=situation,
            situation_bullets=situation_bullets,
            complication=complication,
            complication_bullets=complication_bullets,
            question=question,
            answer=answer,
            answer_bullets=answer_bullets,
            urgency_score=urgency_score,
            market_context=market_context
        )

    @staticmethod
    def _calculate_urgency(
        competitor_adoption_percent: float,
        has_current_tools: bool,
        training_gap_percent: float
    ) -> float:
        """
        Calculate urgency score (0-10).

        Factors:
            - Competitor adoption (0-4 points): 0% → 0, 100% → 4
            - Current tools gap (0-3 points): has tools → 0, no tools → 3
            - Training gap (0-3 points): 0% gap → 0, 100% gap → 3
        """

        urgency = 0.0

        # Competitor pressure
        urgency += (competitor_adoption_percent / 100) * 4.0

        # Tools gap
        if not has_current_tools:
            urgency += 3.0

        # Training gap
        urgency += training_gap_percent * 3.0

        return min(urgency, 10.0)

    @staticmethod
    def render_to_html(scqa: SCQA) -> str:
        """
        Render SCQA as HTML with 4 colored blocks.

        Design:
            - Situation: Blue (#F0F9FF / #0EA5E9)
            - Complication: Red (#FEF2F2 / #EF4444)
            - Question: Yellow (#FEF3C7 / #F59E0B)
            - Answer: Green (#F0FDF4 / #10B981)
        """

        html = '<div class="scqa-summary">\n'

        # Situation block
        html += '  <div class="scqa-block situation">\n'
        html += '    <span class="scqa-label">📍 SITUAÇÃO</span>\n'
        html += f'    <p>{scqa.situation}</p>\n'
        if scqa.situation_bullets:
            html += '    <ul>\n'
            for bullet in scqa.situation_bullets:
                html += f'      <li>{bullet}</li>\n'
            html += '    </ul>\n'
        html += '  </div>\n'

        # Complication block
        html += '  <div class="scqa-block complication">\n'
        html += '    <span class="scqa-label">⚠️ COMPLICAÇÃO</span>\n'
        html += f'    <p>{scqa.complication}</p>\n'
        if scqa.complication_bullets:
            html += '    <ul>\n'
            for bullet in scqa.complication_bullets:
                html += f'      <li>{bullet}</li>\n'
            html += '    </ul>\n'
        html += f'    <div class="urgency-indicator">Urgência: <strong>{scqa.urgency_score:.1f}/10</strong></div>\n'
        html += '  </div>\n'

        # Question block
        html += '  <div class="scqa-block question">\n'
        html += '    <span class="scqa-label">❓ PERGUNTA</span>\n'
        html += f'    <p><strong>{scqa.question}</strong></p>\n'
        html += '  </div>\n'

        # Answer block
        html += '  <div class="scqa-block answer">\n'
        html += '    <span class="scqa-label">✅ RESPOSTA</span>\n'
        html += f'    <p>{scqa.answer}</p>\n'
        if scqa.answer_bullets:
            html += '    <ul>\n'
            for bullet in scqa.answer_bullets:
                html += f'      <li>{bullet}</li>\n'
            html += '    </ul>\n'
        html += '  </div>\n'

        html += '</div>\n'

        return html

    @staticmethod
    def render_to_markdown(scqa: SCQA) -> str:
        """
        Render SCQA as Markdown (for documentation/exports).
        """

        md = "# SCQA Framework - Executive Summary\n\n"

        md += "## 📍 SITUAÇÃO\n\n"
        md += f"{scqa.situation}\n\n"
        if scqa.situation_bullets:
            for bullet in scqa.situation_bullets:
                md += f"- {bullet}\n"
            md += "\n"

        md += "## ⚠️ COMPLICAÇÃO\n\n"
        md += f"{scqa.complication}\n\n"
        if scqa.complication_bullets:
            for bullet in scqa.complication_bullets:
                md += f"- {bullet}\n"
            md += "\n"
        md += f"**Urgência:** {scqa.urgency_score:.1f}/10\n\n"

        md += "## ❓ PERGUNTA\n\n"
        md += f"**{scqa.question}**\n\n"

        md += "## ✅ RESPOSTA\n\n"
        md += f"{scqa.answer}\n\n"
        if scqa.answer_bullets:
            for bullet in scqa.answer_bullets:
                md += f"- {bullet}\n"
            md += "\n"

        return md
