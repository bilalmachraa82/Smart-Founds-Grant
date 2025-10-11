"""
Risk Register Service

Generates project risk register with mitigation strategies and probability/impact matrix.
Implements IFIC best practice: comprehensive risk management with quantified likelihood/impact.

Risk Structure (per IFIC report pattern):
    Risk ID → Category → Description → Probability → Impact → Mitigation → Owner

Risk Matrix:
    Probability: LOW (0-30%) | MEDIUM (30-60%) | HIGH (60-100%)
    Impact: LOW (€0-10k) | MEDIUM (€10k-50k) | HIGH (€50k+)
    Overall Risk Score: Probability × Impact

Example:
    risks = RiskRegisterService.generate_from_questionnaire(
        questionnaire, budget=95000, has_dev_team=True
    )
    # Returns: 12 identified risks with mitigations
"""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from enum import Enum

from ..models.questionnaire import DiagnosticQuestionnaire
from ..config.logfire_config import get_logger

logger = get_logger(__name__)


# ===== MODELS =====

class RiskCategory(str, Enum):
    """Risk categories aligned with IFIC report"""
    TECHNICAL = "technical"  # Technical implementation risks
    ADOPTION = "adoption"  # User adoption risks
    FINANCIAL = "financial"  # Budget/financial risks
    COMPLIANCE = "compliance"  # Regulatory/compliance risks
    EXECUTION = "execution"  # Project execution risks
    MARKET = "market"  # External market risks


class ProbabilityLevel(str, Enum):
    """Probability levels"""
    LOW = "low"  # 0-30%
    MEDIUM = "medium"  # 30-60%
    HIGH = "high"  # 60-100%


class ImpactLevel(str, Enum):
    """Impact levels (financial)"""
    LOW = "low"  # €0-10k loss
    MEDIUM = "medium"  # €10k-50k loss
    HIGH = "high"  # €50k+ loss


class Risk(BaseModel):
    """Single risk item"""

    risk_id: str = Field(..., description="Unique risk ID (R001, R002, etc.)")
    category: RiskCategory
    title: str = Field(..., description="Short risk title")
    description: str = Field(..., description="Detailed risk description")

    # Probability & Impact
    probability: ProbabilityLevel
    probability_percent: float = Field(..., ge=0, le=100, description="Probability %")
    impact: ImpactLevel
    impact_eur: float = Field(..., ge=0, description="Financial impact if risk materializes (€)")

    # Risk score (probability × impact)
    risk_score: float = Field(..., ge=0, le=100, description="Overall risk score (0-100)")

    # Mitigation
    mitigation_strategy: str = Field(..., description="How to mitigate this risk")
    contingency_plan: Optional[str] = Field(None, description="Backup plan if risk occurs")
    owner: str = Field(..., description="Who is responsible for managing this risk")

    # Tracking
    status: str = Field(default="ACTIVE", description="ACTIVE | MITIGATED | OCCURRED")
    residual_risk_score: float = Field(default=0, ge=0, le=100, description="Risk score after mitigation")


class RiskRegister(BaseModel):
    """Complete risk register"""

    risks: List[Risk]

    # Aggregations
    total_risks: int = Field(..., ge=0)
    high_risks: int = Field(default=0, ge=0, description="Number of HIGH probability risks")
    total_exposure: float = Field(default=0, ge=0, description="Sum of all risk impacts (€)")

    # Risk matrix summary
    risk_matrix: Dict[str, Dict[str, int]] = Field(
        default_factory=dict,
        description="2D matrix: probability × impact counts"
    )


# ===== RISK REGISTER SERVICE =====

class RiskRegisterService:
    """
    Generate project risk register.

    Process:
        1. Identify risks based on questionnaire (tech stack, company size, use cases)
        2. Calculate probability × impact for each risk
        3. Define mitigation strategies
        4. Assign owners
        5. Render risk matrix
    """

    @staticmethod
    def generate_from_questionnaire(
        questionnaire: DiagnosticQuestionnaire,
        total_budget: float,
        has_consulting: bool = True
    ) -> RiskRegister:
        """
        Generate risk register from questionnaire + budget.

        Args:
            questionnaire: Diagnostic questionnaire
            total_budget: Total project budget (€)
            has_consulting: Whether project includes consulting services

        Returns:
            RiskRegister with identified risks + mitigations
        """

        risks = []
        risk_counter = 1

        # ===== TECHNICAL RISKS =====

        # R001: Integration complexity
        if questionnaire.email_system.value != questionnaire.cloud_storage.value:
            # Mixed ecosystem = higher integration risk
            risks.append(Risk(
                risk_id=f"R{risk_counter:03d}",
                category=RiskCategory.TECHNICAL,
                title="Integração multi-ecosystem complexa",
                description=f"Empresa usa {questionnaire.email_system.value} email + {questionnaire.cloud_storage.value} storage. Integração ferramentas IA pode requerer middleware adicional.",
                probability=ProbabilityLevel.MEDIUM,
                probability_percent=40,
                impact=ImpactLevel.MEDIUM,
                impact_eur=15000,
                risk_score=40 * 0.40,  # probability × impact_weight (medium=0.4)
                mitigation_strategy="Contratar consultoria especializada integração cross-platform. Usar API wrappers (Zapier/Make). Piloto 2 semanas antes rollout.",
                contingency_plan="Se integração falhar: migrar para single ecosystem (Google ou Microsoft completo)",
                owner="CTO / Lead Developer",
                status="ACTIVE",
                residual_risk_score=15  # After mitigation
            ))
            risk_counter += 1

        # R002: Technical debt
        if not questionnaire.has_dev_team:
            risks.append(Risk(
                risk_id=f"R{risk_counter:03d}",
                category=RiskCategory.TECHNICAL,
                title="Sem equipa dev interna - dependência externa",
                description="Empresa sem developers internos. Manutenção/customização IA dependerá sempre de fornecedores externos (custo/tempo).",
                probability=ProbabilityLevel.HIGH,
                probability_percent=70,
                impact=ImpactLevel.LOW,
                impact_eur=8000,
                risk_score=70 * 0.20,
                mitigation_strategy="Contratar 1 developer júnior (RH Dedicados). Formação intensiva 3 meses. Documentação técnica exaustiva.",
                contingency_plan="SLA com fornecedor SaaS para suporte 24/7 (€200/mês extra)",
                owner="CEO / HR Manager",
                status="ACTIVE",
                residual_risk_score=8
            ))
            risk_counter += 1

        # ===== ADOPTION RISKS =====

        # R003: User adoption resistance
        adoption_risk_prob = 60 if questionnaire.training_priority else 40
        risks.append(Risk(
            risk_id=f"R{risk_counter:03d}",
            category=RiskCategory.ADOPTION,
            title="Resistência colaboradores adoção IA",
            description=f"{questionnaire.num_employees} colaboradores precisam adoptar novas ferramentas IA. Risco: 30-40% não usam ferramentas regularmente (\"fica na gaveta\").",
            probability=ProbabilityLevel.MEDIUM if questionnaire.training_priority else ProbabilityLevel.HIGH,
            probability_percent=adoption_risk_prob,
            impact=ImpactLevel.HIGH,
            impact_eur=total_budget * 0.30,  # 30% budget wasted if low adoption
            risk_score=adoption_risk_prob * 0.60,
            mitigation_strategy="Formação obrigatória 64h (AiParaTi). Champions internos (2-3 early adopters). Gamification (leaderboard uso ferramentas). KPIs individuais uso IA.",
            contingency_plan="Se adoção <50% após 3 meses: workshops presenciais semanais + incentivos financeiros",
            owner="HR Manager / Team Leads",
            status="ACTIVE",
            residual_risk_score=20
        ))
        risk_counter += 1

        # R004: Training ineffective
        if questionnaire.training_priority and questionnaire.num_employees_training:
            risks.append(Risk(
                risk_id=f"R{risk_counter:03d}",
                category=RiskCategory.ADOPTION,
                title="Formação não traduz em skills práticos",
                description=f"{questionnaire.num_employees_training} colaboradores treinados mas não aplicam skills no dia-a-dia (teoria vs prática gap).",
                probability=ProbabilityLevel.MEDIUM,
                probability_percent=35,
                impact=ImpactLevel.MEDIUM,
                impact_eur=questionnaire.num_employees_training * 2466 * 0.50,  # 50% training budget wasted
                risk_score=35 * 0.40,
                mitigation_strategy="Training hands-on (70% prática). Projetos reais durante formação. Follow-up 30/60/90 dias. Mentoring interno.",
                contingency_plan="Retraining targeted (só tópicos críticos). Contratar freelancers temporários preencher gaps.",
                owner="Training Manager",
                status="ACTIVE",
                residual_risk_score=12
            ))
            risk_counter += 1

        # ===== FINANCIAL RISKS =====

        # R005: Budget overrun
        risks.append(Risk(
            risk_id=f"R{risk_counter:03d}",
            category=RiskCategory.FINANCIAL,
            title="Overrun orçamento (scope creep)",
            description=f"Orçamento aprovado €{total_budget:,.0f}. Risco: requirements adicionais durante implementação (+15-25% custos típicos).",
            probability=ProbabilityLevel.MEDIUM,
            probability_percent=45,
            impact=ImpactLevel.MEDIUM,
            impact_eur=total_budget * 0.20,  # 20% overrun
            risk_score=45 * 0.40,
            mitigation_strategy="Contingency buffer 10% orçamento. Change control rigoroso (approval CEO para extras). Sprints curtos 2 semanas (pivot rápido).",
            contingency_plan="Priorizar use cases críticos. Fase 2 para features nice-to-have.",
            owner="CFO / Project Manager",
            status="ACTIVE",
            residual_risk_score=18
        ))
        risk_counter += 1

        # R006: Subsidy not approved
        risks.append(Risk(
            risk_id=f"R{risk_counter:03d}",
            category=RiskCategory.FINANCIAL,
            title="Candidatura rejeitada IAPMEI",
            description=f"Subsídio €{total_budget * 0.75:,.0f} (75%) não aprovado. Empresa precisa financiar 100% projeto (€{total_budget:,.0f}).",
            probability=ProbabilityLevel.LOW,
            probability_percent=15,
            impact=ImpactLevel.HIGH,
            impact_eur=total_budget * 0.75,
            risk_score=15 * 0.60,
            mitigation_strategy="Otimizar scoring mérito (target >7.0/10). Compliance validator 8 regras. Documentação rigorosa (3 cotações, Gantt, Risk Register). ROC validação.",
            contingency_plan="Reduzir scope para €50k (bootstrap sem subsídio). Ou aguardar próximo aviso (Q2 2025).",
            owner="CEO / Finance Director",
            status="ACTIVE",
            residual_risk_score=5
        ))
        risk_counter += 1

        # ===== COMPLIANCE RISKS =====

        # R007: ROC validation issues
        risks.append(Risk(
            risk_id=f"R{risk_counter:03d}",
            category=RiskCategory.COMPLIANCE,
            title="ROC identifica problemas contabilísticos",
            description="Revisor Oficial Contas (obrigatório Art. 6.1.e) identifica irregularidades contabilidade empresa → candidatura inelegível.",
            probability=ProbabilityLevel.LOW,
            probability_percent=10,
            impact=ImpactLevel.HIGH,
            impact_eur=total_budget * 0.75,  # Lose subsidy
            risk_score=10 * 0.60,
            mitigation_strategy="Contratar ROC certificado OROC early (antes candidatura). Audit prévio contabilidade Q4 2024. Corrigir issues antes submissão.",
            contingency_plan="Se ROC rejeita: corrigir contabilidade + resubmeter próximo aviso.",
            owner="CFO / Accountant",
            status="ACTIVE",
            residual_risk_score=3
        ))
        risk_counter += 1

        # R008: RGPD compliance (if handling sensitive data)
        if any(uc in ["customer_service_chatbot", "document_analysis"] for uc in questionnaire.use_cases):
            risks.append(Risk(
                risk_id=f"R{risk_counter:03d}",
                category=RiskCategory.COMPLIANCE,
                title="RGPD: dados sensíveis enviados para LLMs cloud",
                description="Casos uso (chatbot/document analysis) podem processar dados pessoais clientes. Risco: violação RGPD se dados enviados para OpenAI/Google sem consentimento.",
                probability=ProbabilityLevel.MEDIUM,
                probability_percent=50,
                impact=ImpactLevel.MEDIUM,
                impact_eur=25000,  # CNPD fines
                risk_score=50 * 0.40,
                mitigation_strategy="Azure OpenAI (GDPR-compliant) ou Ollama local. Anonimização automática dados (PII detection). Formação RGPD 8h equipa.",
                contingency_plan="Rollback para LLMs locais (Ollama). Ou segregar dados sensíveis (não enviar para cloud).",
                owner="DPO / Legal",
                status="ACTIVE",
                residual_risk_score=10
            ))
            risk_counter += 1

        # ===== EXECUTION RISKS =====

        # R009: Timeline delays
        risks.append(Risk(
            risk_id=f"R{risk_counter:03d}",
            category=RiskCategory.EXECUTION,
            title="Atrasos cronograma implementação",
            description=f"Projeto {questionnaire.project_duration_months} meses. Risco: atrasos 2-4 meses típicos (vendor delays, sick leave, scope changes).",
            probability=ProbabilityLevel.MEDIUM,
            probability_percent=40,
            impact=ImpactLevel.LOW,
            impact_eur=5000,  # Opportunity cost
            risk_score=40 * 0.20,
            mitigation_strategy="Buffer 20% timeline. Gantt chart com milestones semanais. Daily standups. Vendor SLAs penalizantes (€500/semana atraso).",
            contingency_plan="Reduzir scope (MVP first). Contratar freelancers temporários acelerar.",
            owner="Project Manager",
            status="ACTIVE",
            residual_risk_score=8
        ))
        risk_counter += 1

        # R010: Key person risk
        if questionnaire.num_employees < 20:
            risks.append(Risk(
                risk_id=f"R{risk_counter:03d}",
                category=RiskCategory.EXECUTION,
                title="Key person risk (empresa pequena)",
                description=f"Empresa {questionnaire.num_employees} colaboradores. Se gestor projeto/CTO sai, projeto fica bloqueado (conhecimento concentrado).",
                probability=ProbabilityLevel.LOW,
                probability_percent=15,
                impact=ImpactLevel.MEDIUM,
                impact_eur=20000,
                risk_score=15 * 0.40,
                mitigation_strategy="Documentação rigorosa (Notion wiki). 2 pessoas por workstream (redundância). Contratos retenção key people (+10% bonus se ficam 12 meses).",
                contingency_plan="Contratar PM externo temporário. Consultoria fornecedor assume gestão.",
                owner="CEO / HR",
                status="ACTIVE",
                residual_risk_score=5
            ))
            risk_counter += 1

        # ===== MARKET RISKS =====

        # R011: Competitor moves faster
        risks.append(Risk(
            risk_id=f"R{risk_counter:03d}",
            category=RiskCategory.MARKET,
            title="Concorrência adopta IA mais rápido",
            description=f"Setor {questionnaire.industry_sector.value}: 60-75% concorrência já usa IA. Risco: late mover disadvantage (quota mercado perdida).",
            probability=ProbabilityLevel.MEDIUM,
            probability_percent=50,
            impact=ImpactLevel.MEDIUM,
            impact_eur=30000,  # Lost revenue
            risk_score=50 * 0.40,
            mitigation_strategy="Fast-track implementação (6 meses MVP vs 12 meses completo). Comunicação externa early (LinkedIn/PR sobre IA adoption). Diferenciação (não copiar concorrência).",
            contingency_plan="Pivot para nicho underserved (onde IA ainda não chegou).",
            owner="CEO / Marketing",
            status="ACTIVE",
            residual_risk_score=15
        ))
        risk_counter += 1

        # R012: Technology obsolescence
        risks.append(Risk(
            risk_id=f"R{risk_counter:03d}",
            category=RiskCategory.MARKET,
            title="Tecnologia IA obsoleta em 12-18 meses",
            description="IA evolui rapidamente (GPT-3→GPT-4→GPT-5). Risco: ferramentas escolhidas hoje obsoletas em 18 meses (vendor lock-in).",
            probability=ProbabilityLevel.MEDIUM,
            probability_percent=35,
            impact=ImpactLevel.LOW,
            impact_eur=10000,
            risk_score=35 * 0.20,
            mitigation_strategy="Preferir standards abertos (OpenAI API format). Evitar vendor lock-in (usar Ollama fallback). Review trimestral stack IA.",
            contingency_plan="Migração para novo LLM (API compatibility garante switching rápido).",
            owner="CTO",
            status="ACTIVE",
            residual_risk_score=7
        ))
        risk_counter += 1

        # ===== AGGREGATIONS =====

        total_risks = len(risks)
        high_risks = sum(1 for r in risks if r.probability == ProbabilityLevel.HIGH)
        total_exposure = sum(r.impact_eur * (r.probability_percent / 100) for r in risks)

        # Risk matrix (probability × impact counts)
        risk_matrix = {
            "low": {"low": 0, "medium": 0, "high": 0},
            "medium": {"low": 0, "medium": 0, "high": 0},
            "high": {"low": 0, "medium": 0, "high": 0}
        }

        for risk in risks:
            risk_matrix[risk.probability.value][risk.impact.value] += 1

        logger.info(
            f"Generated risk register: {total_risks} risks identified, "
            f"{high_risks} HIGH probability, total exposure €{total_exposure:,.0f}"
        )

        return RiskRegister(
            risks=risks,
            total_risks=total_risks,
            high_risks=high_risks,
            total_exposure=total_exposure,
            risk_matrix=risk_matrix
        )

    @staticmethod
    def render_to_html(register: RiskRegister) -> str:
        """
        Render risk register as HTML table + risk matrix heatmap.

        Design:
            - Sortable table (by risk_score DESC)
            - Color-coded by probability/impact
            - Risk matrix heatmap (3×3 grid)
        """

        html = '<div class="risk-register">\n'

        # Header
        html += '  <h3>⚠️ Risk Register</h3>\n'
        html += f'  <p>{register.total_risks} risks identificados, {register.high_risks} HIGH probability, exposure total €{register.total_exposure:,.0f}</p>\n\n'

        # Risk matrix heatmap
        html += '  <h4>Risk Matrix (Probability × Impact)</h4>\n'
        html += '  <table class="risk-matrix" style="border-collapse: collapse; margin: 20px 0;">\n'
        html += '    <thead>\n'
        html += '      <tr>\n'
        html += '        <th style="border: 1px solid #E5E7EB; padding: 8px; background-color: #F9FAFB;">Probability \\ Impact</th>\n'
        html += '        <th style="border: 1px solid #E5E7EB; padding: 8px; background-color: #F0FDF4;">LOW</th>\n'
        html += '        <th style="border: 1px solid #E5E7EB; padding: 8px; background-color: #FEF3C7;">MEDIUM</th>\n'
        html += '        <th style="border: 1px solid #E5E7EB; padding: 8px; background-color: #FEE2E2;">HIGH</th>\n'
        html += '      </tr>\n'
        html += '    </thead>\n'
        html += '    <tbody>\n'

        for prob_level in ["high", "medium", "low"]:
            html += '      <tr>\n'
            html += f'        <td style="border: 1px solid #E5E7EB; padding: 8px; font-weight: 600; text-transform: uppercase;">{prob_level}</td>\n'
            for impact_level in ["low", "medium", "high"]:
                count = register.risk_matrix[prob_level][impact_level]
                bg_color = "#F0FDF4" if count == 0 else "#FEF3C7" if count <= 2 else "#FEE2E2"
                html += f'        <td style="border: 1px solid #E5E7EB; padding: 8px; text-align: center; background-color: {bg_color};">{count}</td>\n'
            html += '      </tr>\n'

        html += '    </tbody>\n'
        html += '  </table>\n\n'

        # Risk table
        html += '  <h4>Risk Details</h4>\n'
        html += '  <table class="data-table risk-table">\n'
        html += '    <thead>\n'
        html += '      <tr>\n'
        html += '        <th>ID</th>\n'
        html += '        <th>Category</th>\n'
        html += '        <th>Risk</th>\n'
        html += '        <th>Probability</th>\n'
        html += '        <th>Impact (€)</th>\n'
        html += '        <th>Score</th>\n'
        html += '        <th>Mitigation</th>\n'
        html += '        <th>Owner</th>\n'
        html += '      </tr>\n'
        html += '    </thead>\n'
        html += '    <tbody>\n'

        # Sort by risk_score DESC
        sorted_risks = sorted(register.risks, key=lambda r: r.risk_score, reverse=True)

        for risk in sorted_risks:
            # Color coding
            prob_color = {"low": "#10B981", "medium": "#F59E0B", "high": "#EF4444"}[risk.probability.value]
            impact_color = {"low": "#10B981", "medium": "#F59E0B", "high": "#EF4444"}[risk.impact.value]

            html += '      <tr>\n'
            html += f'        <td><strong>{risk.risk_id}</strong></td>\n'
            html += f'        <td>{risk.category.value.title()}</td>\n'
            html += f'        <td>\n'
            html += f'          <strong>{risk.title}</strong><br>\n'
            html += f'          <small style="color: #6B7280;">{risk.description}</small>\n'
            html += f'        </td>\n'
            html += f'        <td><span style="color: {prob_color}; font-weight: 600;">{risk.probability.value.upper()}</span><br><small>{risk.probability_percent:.0f}%</small></td>\n'
            html += f'        <td><span style="color: {impact_color}; font-weight: 600;">{risk.impact.value.upper()}</span><br><small>€{risk.impact_eur:,.0f}</small></td>\n'
            html += f'        <td><strong>{risk.risk_score:.1f}</strong></td>\n'
            html += f'        <td>{risk.mitigation_strategy}</td>\n'
            html += f'        <td>{risk.owner}</td>\n'
            html += '      </tr>\n'

        html += '    </tbody>\n'
        html += '  </table>\n'
        html += '</div>\n'

        return html

    @staticmethod
    def render_to_markdown(register: RiskRegister) -> str:
        """Render risk register as Markdown."""

        md = "# Risk Register\n\n"

        md += f"**Total Risks:** {register.total_risks}  \n"
        md += f"**HIGH Probability Risks:** {register.high_risks}  \n"
        md += f"**Total Exposure:** €{register.total_exposure:,.0f}\n\n"

        md += "## Risk Matrix\n\n"
        md += "| Probability \\ Impact | LOW | MEDIUM | HIGH |\n"
        md += "|----------------------|-----|--------|------|\n"
        for prob_level in ["high", "medium", "low"]:
            md += f"| **{prob_level.upper()}** | "
            md += f"{register.risk_matrix[prob_level]['low']} | "
            md += f"{register.risk_matrix[prob_level]['medium']} | "
            md += f"{register.risk_matrix[prob_level]['high']} |\n"
        md += "\n"

        md += "## Risk Details\n\n"

        sorted_risks = sorted(register.risks, key=lambda r: r.risk_score, reverse=True)

        for risk in sorted_risks:
            md += f"### {risk.risk_id}: {risk.title}\n\n"
            md += f"**Category:** {risk.category.value.title()}  \n"
            md += f"**Description:** {risk.description}\n\n"
            md += f"- **Probability:** {risk.probability.value.upper()} ({risk.probability_percent:.0f}%)\n"
            md += f"- **Impact:** {risk.impact.value.upper()} (€{risk.impact_eur:,.0f})\n"
            md += f"- **Risk Score:** {risk.risk_score:.1f}\n"
            md += f"- **Mitigation:** {risk.mitigation_strategy}\n"
            md += f"- **Owner:** {risk.owner}\n\n"

        return md
