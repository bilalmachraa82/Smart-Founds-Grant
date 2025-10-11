"""
Investment Matrix Service

Generates investment justification matrix linking each € to specific capabilities and outcomes.
Implements IFIC best practice: rigorous ROI documentation for all expenses.

Matrix Structure (per IFIC report pattern):
    Tool/Service → Objective → Capability Gained → Expected Outcome → KPI → Timeline

Example:
    Gemini Business (€14,400) → Automate Content → AI generation → 30% time saved → 48h/month saved → 3 months

Usage:
    matrix = InvestmentMatrixService.generate_from_components(
        saas_recs, training_recs, consultoria_budget=28500, rh_budget=16950
    )
    html = InvestmentMatrixService.render_to_html(matrix)
"""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from enum import Enum

from .saas_recommendation_engine import SaaSRecommendation
from .partner_priority_service import TrainingRecommendation
from ..config.logfire_config import get_logger

logger = get_logger(__name__)


# ===== MODELS =====

class InvestmentCategory(str, Enum):
    """Investment categories aligned with Aviso 03/C05"""
    SAAS = "saas"
    TRAINING = "training"
    CONSULTING = "consulting"
    RH_DEDICADOS = "rh_dedicados"
    EQUIPMENT = "equipment"
    ROC = "roc"


class InvestmentItem(BaseModel):
    """Single row in investment matrix"""

    category: InvestmentCategory
    tool_or_service: str = Field(..., description="Name of tool/service/resource")
    amount_eur: float = Field(..., ge=0, description="Investment amount (€)")

    # IFIC matrix columns
    objective: str = Field(..., description="What business problem this solves")
    capability_gained: str = Field(..., description="What new capability company gets")
    expected_outcome: str = Field(..., description="Measurable outcome")
    kpi: str = Field(..., description="Key Performance Indicator")
    timeline_months: int = Field(..., ge=1, le=12, description="When benefit materializes")

    # Supporting data
    roi_calculation: Optional[str] = Field(None, description="ROI formula/justification")
    rag_citation: Optional[str] = Field(None, description="Citation from RAG search")
    priority: str = Field("MÉDIO", description="CRÍTICO | ALTO | MÉDIO | BAIXO")


class InvestmentMatrix(BaseModel):
    """Complete investment matrix"""

    items: List[InvestmentItem]

    # Aggregations
    total_investment: float = Field(..., ge=0)
    total_by_category: Dict[InvestmentCategory, float] = Field(default_factory=dict)

    # ROI summary
    expected_annual_savings: float = Field(default=0, ge=0, description="Total annual savings (€)")
    payback_period_months: float = Field(default=24, ge=0, description="When investment breaks even")
    roi_percent: float = Field(default=0, ge=0, description="ROI % over 3 years")


# ===== INVESTMENT MATRIX SERVICE =====

class InvestmentMatrixService:
    """
    Generate investment justification matrix.

    Process:
        1. Collect all budget components (SaaS, training, consultoria, RH)
        2. For each item, map: tool → objective → capability → outcome → KPI
        3. Calculate ROI per item
        4. Aggregate totals and render matrix
    """

    @staticmethod
    def generate_from_components(
        saas_recommendations: List[SaaSRecommendation],
        training_recommendations: List[TrainingRecommendation],
        consultoria_budget: float = 0,
        rh_dedicados_budget: float = 0,
        equipment_budget: float = 0,
        roc_budget: float = 2500
    ) -> InvestmentMatrix:
        """
        Generate investment matrix from budget components.

        Args:
            saas_recommendations: SaaS tools from recommendation engine
            training_recommendations: Training from partner priority service
            consultoria_budget: Total consultoria expenses (€)
            rh_dedicados_budget: Total dedicated HR expenses (€)
            equipment_budget: Hardware/equipment expenses (€)
            roc_budget: ROC certification expenses (€, max 2500)

        Returns:
            InvestmentMatrix with all items + aggregations
        """

        items = []

        # ===== SAAS TOOLS =====
        for saas_rec in saas_recommendations:
            items.append(InvestmentItem(
                category=InvestmentCategory.SAAS,
                tool_or_service=saas_rec.tool_name,
                amount_eur=saas_rec.annual_cost,
                objective=f"Aumentar produtividade {saas_rec.recommended_users} colaboradores",
                capability_gained=f"IA generativa nativa {saas_rec.use_cases[0] if saas_rec.use_cases else 'automação'}",
                expected_outcome=f"30% redução tempo tarefas repetitivas → {saas_rec.recommended_users * 48}h/mês saved",
                kpi=f"{saas_rec.recommended_users * 48}h/mês produtividade recuperada",
                timeline_months=3,
                roi_calculation=saas_rec.roi_calculation,
                rag_citation=saas_rec.rag_citation if hasattr(saas_rec, 'rag_citation') else None,
                priority="ALTO" if saas_rec.native_integration else "MÉDIO"
            ))

        # ===== TRAINING =====
        for training_rec in training_recommendations:
            # Estimate trained employees (assume €2,466 per employee for AiParaTi, €1,500 for others)
            if training_rec.provider.value == "aiparati":
                num_trained = int(training_rec.cost_total / 2466)
                capability = "Upskilling 64h completo IA (5 módulos)"
                outcome = f"{num_trained} colaboradores certificados IA"
                kpi_value = f"{num_trained * 8}h/mês produtividade nova"
            else:
                num_trained = int(training_rec.cost_total / 1500)
                capability = "Formação básica IA"
                outcome = f"{num_trained} colaboradores com skills IA"
                kpi_value = f"{num_trained * 4}h/mês produtividade nova"

            items.append(InvestmentItem(
                category=InvestmentCategory.TRAINING,
                tool_or_service=f"{training_rec.provider.value.upper()} - {training_rec.course_name}",
                amount_eur=training_rec.cost_total,
                objective=f"Capacitar equipa para usar IA eficazmente",
                capability_gained=capability,
                expected_outcome=outcome,
                kpi=kpi_value,
                timeline_months=6,
                roi_calculation=f"€{training_rec.cost_total:,.0f} training → {num_trained} FTE @ 30% productivity = €{num_trained * 35 * 0.30 * 160 * 12:,.0f}/ano",
                priority="CRÍTICO" if training_rec.provider.value == "aiparati" else "ALTO"
            ))

        # ===== CONSULTORIA =====
        if consultoria_budget > 0:
            # Estimate consulting services (€150/hour typical rate)
            consulting_hours = consultoria_budget / 150

            items.append(InvestmentItem(
                category=InvestmentCategory.CONSULTING,
                tool_or_service="Consultoria Implementação IA",
                amount_eur=consultoria_budget,
                objective="Garantir implementação técnica bem-sucedida",
                capability_gained=f"Arquitetura IA customizada + integração sistemas ({consulting_hours:.0f}h especialista)",
                expected_outcome="Zero falhas implementação, roadmap 12 meses executável",
                kpi=f"{consulting_hours:.0f}h consultoria → 5 casos uso implementados",
                timeline_months=12,
                roi_calculation=f"€{consultoria_budget:,.0f} consulting prevents €{consultoria_budget * 3:,.0f} failed project costs",
                priority="ALTO"
            ))

        # ===== RH DEDICADOS =====
        if rh_dedicados_budget > 0:
            # Estimate FTE (€40k/year salary + charges)
            num_fte = rh_dedicados_budget / 40000

            items.append(InvestmentItem(
                category=InvestmentCategory.RH_DEDICADOS,
                tool_or_service=f"RH Dedicados Projeto IA ({num_fte:.1f} FTE)",
                amount_eur=rh_dedicados_budget,
                objective="Equipa dedicada implementação e manutenção IA",
                capability_gained=f"{num_fte:.1f} FTE especialistas IA internos",
                expected_outcome=f"Capacidade interna sustentável IA (não dependente externos)",
                kpi=f"{num_fte:.1f} FTE → {int(num_fte * 1600)}h/ano desenvolvimento IA",
                timeline_months=12,
                roi_calculation=f"{num_fte:.1f} FTE @ €40k/ano vs €80/h freelancer (€{int(num_fte * 1600 * 80):,} saved)",
                priority="CRÍTICO"
            ))

        # ===== EQUIPMENT =====
        if equipment_budget > 0:
            items.append(InvestmentItem(
                category=InvestmentCategory.EQUIPMENT,
                tool_or_service="Equipamento Hardware (servidores/GPUs)",
                amount_eur=equipment_budget,
                objective="Infraestrutura computação IA (inferência/training)",
                capability_gained="Capacidade processar LLMs localmente (privacy/performance)",
                expected_outcome="Redução latência 80% vs cloud, dados sensíveis on-premise",
                kpi=f"€{equipment_budget:,.0f} equipment → {int(equipment_budget / 5000)} GPUs/servidores",
                timeline_months=6,
                roi_calculation=f"€{equipment_budget:,.0f} capex vs €{int(equipment_budget * 0.4)}/ano cloud (payback 2.5 anos)",
                priority="MÉDIO"
            ))

        # ===== ROC =====
        if roc_budget > 0:
            items.append(InvestmentItem(
                category=InvestmentCategory.ROC,
                tool_or_service="Certificação ROC (Revisor Oficial Contas)",
                amount_eur=roc_budget,
                amount_eur=min(roc_budget, 2500),  # HARD LIMIT
                objective="Validação financeira projeto (obrigatório regulamento)",
                capability_gained="Compliance Aviso 03/C05 Art. 6.1.e",
                expected_outcome="Candidatura elegível para submissão",
                kpi="ROC certificate issued (binary: yes/no)",
                timeline_months=1,
                roi_calculation="Mandatory compliance cost (€2,500 max)",
                priority="CRÍTICO"
            ))

        # ===== AGGREGATIONS =====
        total_investment = sum(item.amount_eur for item in items)

        total_by_category = {}
        for category in InvestmentCategory:
            total_by_category[category] = sum(
                item.amount_eur for item in items if item.category == category
            )

        # Calculate expected annual savings (from SaaS + Training productivity gains)
        expected_annual_savings = 0

        # SaaS savings: 30% productivity × users × €35/hour × 160h/month × 12 months
        for saas_rec in saas_recommendations:
            expected_annual_savings += saas_rec.recommended_users * 35 * 0.30 * 160 * 12

        # Training savings: 20% productivity × trained employees × €35/hour × 160h/month × 12 months
        for training_rec in training_recommendations:
            if training_rec.provider.value == "aiparati":
                num_trained = int(training_rec.cost_total / 2466)
                expected_annual_savings += num_trained * 35 * 0.20 * 160 * 12
            else:
                num_trained = int(training_rec.cost_total / 1500)
                expected_annual_savings += num_trained * 35 * 0.15 * 160 * 12

        # Payback period: total_investment / expected_annual_savings × 12
        payback_period_months = (total_investment / expected_annual_savings * 12) if expected_annual_savings > 0 else 24

        # ROI % over 3 years: (3 × annual_savings - total_investment) / total_investment × 100
        roi_percent = ((3 * expected_annual_savings - total_investment) / total_investment * 100) if total_investment > 0 else 0

        logger.info(
            f"Generated investment matrix: {len(items)} items, "
            f"€{total_investment:,.0f} total, ROI {roi_percent:.1f}% over 3 years"
        )

        return InvestmentMatrix(
            items=items,
            total_investment=total_investment,
            total_by_category=total_by_category,
            expected_annual_savings=expected_annual_savings,
            payback_period_months=payback_period_months,
            roi_percent=roi_percent
        )

    @staticmethod
    def render_to_html(matrix: InvestmentMatrix) -> str:
        """
        Render investment matrix as HTML table.

        Design:
            - Sortable table with 8 columns
            - Color-coded by priority (CRÍTICO=red, ALTO=orange, MÉDIO=yellow, BAIXO=green)
            - Summary row with totals
            - ROI summary callout
        """

        html = '<div class="investment-matrix">\n'

        # ROI Summary callout
        html += '  <div class="callout callout-success">\n'
        html += '    <h4>💰 ROI Summary</h4>\n'
        html += f'    <p><strong>Total Investment:</strong> €{matrix.total_investment:,.0f}</p>\n'
        html += f'    <p><strong>Expected Annual Savings:</strong> €{matrix.expected_annual_savings:,.0f}/ano</p>\n'
        html += f'    <p><strong>Payback Period:</strong> {matrix.payback_period_months:.1f} meses</p>\n'
        html += f'    <p><strong>ROI (3 anos):</strong> {matrix.roi_percent:.1f}%</p>\n'
        html += '  </div>\n\n'

        # Table
        html += '  <table class="data-table investment-table">\n'
        html += '    <thead>\n'
        html += '      <tr>\n'
        html += '        <th>Prioridade</th>\n'
        html += '        <th>Categoria</th>\n'
        html += '        <th>Ferramenta/Serviço</th>\n'
        html += '        <th>Valor (€)</th>\n'
        html += '        <th>Objetivo</th>\n'
        html += '        <th>Capacidade Adquirida</th>\n'
        html += '        <th>Outcome Esperado</th>\n'
        html += '        <th>KPI</th>\n'
        html += '        <th>Timeline</th>\n'
        html += '      </tr>\n'
        html += '    </thead>\n'
        html += '    <tbody>\n'

        # Sort items by priority (CRÍTICO → ALTO → MÉDIO → BAIXO)
        priority_order = {"CRÍTICO": 0, "ALTO": 1, "MÉDIO": 2, "BAIXO": 3}
        sorted_items = sorted(matrix.items, key=lambda x: priority_order.get(x.priority, 4))

        for item in sorted_items:
            # Priority badge color
            priority_color = {
                "CRÍTICO": "#EF4444",
                "ALTO": "#F59E0B",
                "MÉDIO": "#EAB308",
                "BAIXO": "#10B981"
            }.get(item.priority, "#6B7280")

            html += '      <tr>\n'
            html += f'        <td><span class="badge" style="background-color: {priority_color}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">{item.priority}</span></td>\n'
            html += f'        <td>{item.category.value.replace("_", " ").title()}</td>\n'
            html += f'        <td><strong>{item.tool_or_service}</strong></td>\n'
            html += f'        <td style="text-align: right;">€{item.amount_eur:,.0f}</td>\n'
            html += f'        <td>{item.objective}</td>\n'
            html += f'        <td>{item.capability_gained}</td>\n'
            html += f'        <td>{item.expected_outcome}</td>\n'
            html += f'        <td>{item.kpi}</td>\n'
            html += f'        <td>{item.timeline_months} meses</td>\n'
            html += '      </tr>\n'

        html += '    </tbody>\n'

        # Summary row
        html += '    <tfoot>\n'
        html += '      <tr style="background-color: #F3F4F6; font-weight: 600;">\n'
        html += '        <td colspan="3" style="text-align: right;">TOTAL</td>\n'
        html += f'        <td style="text-align: right;">€{matrix.total_investment:,.0f}</td>\n'
        html += '        <td colspan="5"></td>\n'
        html += '      </tr>\n'
        html += '    </tfoot>\n'

        html += '  </table>\n'
        html += '</div>\n'

        return html

    @staticmethod
    def render_to_markdown(matrix: InvestmentMatrix) -> str:
        """
        Render investment matrix as Markdown (for exports).
        """

        md = "# Investment Matrix\n\n"

        md += "## 💰 ROI Summary\n\n"
        md += f"- **Total Investment:** €{matrix.total_investment:,.0f}\n"
        md += f"- **Expected Annual Savings:** €{matrix.expected_annual_savings:,.0f}/ano\n"
        md += f"- **Payback Period:** {matrix.payback_period_months:.1f} meses\n"
        md += f"- **ROI (3 anos):** {matrix.roi_percent:.1f}%\n\n"

        md += "## Investment Details\n\n"
        md += "| Prioridade | Categoria | Ferramenta/Serviço | Valor (€) | Objetivo | KPI | Timeline |\n"
        md += "|------------|-----------|-------------------|-----------|----------|-----|----------|\n"

        priority_order = {"CRÍTICO": 0, "ALTO": 1, "MÉDIO": 2, "BAIXO": 3}
        sorted_items = sorted(matrix.items, key=lambda x: priority_order.get(x.priority, 4))

        for item in sorted_items:
            md += f"| {item.priority} | {item.category.value} | {item.tool_or_service} | €{item.amount_eur:,.0f} | {item.objective} | {item.kpi} | {item.timeline_months}m |\n"

        md += f"\n**TOTAL:** €{matrix.total_investment:,.0f}\n"

        return md
