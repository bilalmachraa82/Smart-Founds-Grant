"""
Budget Optimizer Service

Analyzes current budget and proposes expansion paths based on eligible expenses.
Implements IFIC best practice: €95k → €220k expansion with category-by-category justification.

Key Features:
    - Gap analysis: identifies unexploited eligible expenses
    - 3 expansion paths: Conservador, Moderado (recommended), Agressivo
    - Compliance: ensures all expenses within Aviso 03/C05 limits
    - ROI calculation: subsidy increase vs. implementation effort

Example:
    gaps = BudgetOptimizer.analyze_gaps(current_budget)
    # Returns: [
    #     BudgetGap(category="rh_dedicados", gap=€144k, priority="CRÍTICO"),
    #     BudgetGap(category="outras_despesas", gap=€50k, priority="CRÍTICO"),
    #     ...
    # ]

    paths = BudgetOptimizer.generate_expansion_paths(current=95000, gaps=gaps)
    # Returns: {
    #     "conservador": BudgetPath(target=165000, subsidy=€123,750),
    #     "moderado": BudgetPath(target=230000, subsidy=€172,500),  # RECOMMENDED
    #     "agressivo": BudgetPath(target=280000, subsidy=€210,000)
    # }
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum

from ..models.questionnaire import DiagnosticQuestionnaire
from ..config.logfire_config import get_logger

logger = get_logger(__name__)


# ===== MODELS =====

class BudgetCategory(str, Enum):
    """Budget expense categories (Aviso 03/C05)"""
    RH_DEDICADOS = "rh_dedicados"           # Dedicated human resources
    OUTRAS_DESPESAS = "outras_despesas"     # Other expenses (cloud, APIs, data, certs)
    EQUIPAMENTOS = "equipamentos"           # Equipment (GPU servers, workstations)
    SOFTWARE = "software"                   # SaaS/Software licenses
    CONSULTORIA = "consultoria"             # Consulting services
    FORMACAO = "formacao"                   # Training
    ROC = "roc"                             # Statutory auditor (fixed limit)


class PriorityLevel(str, Enum):
    """Gap priority levels"""
    CRITICAL = "CRÍTICO"      # Must fix (compliance blocker or huge opportunity)
    HIGH = "ALTO"             # Should fix (significant budget opportunity)
    MEDIUM = "MÉDIO"          # Nice to have (moderate opportunity)
    LOW = "BAIXO"             # Optional (small opportunity)


class BudgetGap(BaseModel):
    """Identified gap in eligible expenses"""

    category: BudgetCategory
    current: float = Field(..., description="Current budget allocated (€)")
    maximum: float = Field(..., description="Maximum eligible (€)")
    gap: float = Field(..., description="Gap amount (€), negative if overbudget")
    priority: PriorityLevel
    action: str = Field(..., description="Recommended action to close gap")
    examples: List[str] = Field(..., description="Concrete expense examples")

    # ROI analysis
    subsidy_increase: Optional[float] = Field(None, description="Additional subsidy if gap closed (75% × gap)")
    implementation_effort: Optional[str] = Field(None, description="Effort to implement (LOW/MEDIUM/HIGH)")

    class Config:
        use_enum_values = True


class BudgetChange(BaseModel):
    """Single category budget change"""
    from_amount: float
    to_amount: float
    delta: float
    justification: str


class BudgetPath(BaseModel):
    """Budget expansion scenario"""

    name: str = Field(..., description="Path name (Conservador/Moderado/Agressivo)")
    current_total: float = Field(..., description="Current total budget (€)")
    target_total: float = Field(..., description="Target total budget (€)")
    increase: float = Field(..., description="Total increase (€)")

    # Category changes
    changes: Dict[str, BudgetChange] = Field(..., description="Per-category changes")

    # Financial analysis
    subsidy_75_percent: float = Field(..., description="Subsidy at 75% (€)")
    subsidy_increase: float = Field(..., description="Additional subsidy vs current (€)")

    # Implementation
    justification: str = Field(..., description="Why this path? (viability, ROI, risk)")
    implementation_effort: str = Field(..., description="Effort level (LOW/MEDIUM/HIGH)")
    timeline_weeks: int = Field(..., description="Time to implement (weeks)")
    risk_level: str = Field(..., description="Risk level (LOW/MEDIUM/HIGH)")


# ===== BUDGET LIMITS (Aviso 03/C05) =====

BUDGET_LIMITS = {
    BudgetCategory.RH_DEDICADOS: {
        "maximum": 160000,  # €80k × 2 positions max
        "notes": "€80k cap per position (24 months). Max 2 positions realistic for PME."
    },
    BudgetCategory.OUTRAS_DESPESAS: {
        "maximum": 50000,
        "notes": "Cloud compute, APIs, data licensing, certifications (ISO 42001, etc.)"
    },
    BudgetCategory.EQUIPAMENTOS: {
        "maximum": 40000,
        "notes": "GPU servers/workstations. Depreciation: full if 100% dedicated, else prorata."
    },
    BudgetCategory.SOFTWARE: {
        "maximum": 70000,
        "notes": "SaaS licenses (Copilot, Gemini, ChatGPT, etc.), ML platforms"
    },
    BudgetCategory.CONSULTORIA: {
        "maximum": 70000,
        "notes": "AI strategy, implementation, change management, legal compliance"
    },
    BudgetCategory.FORMACAO: {
        "maximum": 50000,
        "notes": "Training courses (AiParaTi, Microsoft Learn, etc.)"
    },
    BudgetCategory.ROC: {
        "maximum": 2500,
        "notes": "HARD LIMIT Art. 6.1.e - Statutory auditor certification"
    }
}


# ===== BUDGET OPTIMIZER SERVICE =====

class BudgetOptimizer:
    """
    Budget gap analysis and expansion path generation.

    Key principles (IFIC pattern):
        1. Analyze gaps: current vs maximum eligible
        2. Prioritize: CRÍTICO (compliance + big opportunity) > ALTO > MÉDIO
        3. Generate 3 paths: Conservador (safe), Moderado (recommended), Agressivo (ambitious)
        4. ROI: subsidy increase vs implementation effort
    """

    @staticmethod
    def analyze_gaps(
        current_budget: Dict[str, float],
        questionnaire: Optional[DiagnosticQuestionnaire] = None
    ) -> List[BudgetGap]:
        """
        Identify unexploited eligible expenses (IFIC Table pattern).

        Args:
            current_budget: Current budget allocation by category (€)
            questionnaire: Diagnostic questionnaire (optional, for context-aware recommendations)

        Returns:
            List of BudgetGap objects sorted by priority (CRÍTICO first)

        Example:
            current = {
                "rh_dedicados": 16000,
                "outras_despesas": 0,
                "software": 40000,
                "consultoria": 36000,
                "formacao": 0,
                "roc": 3100  # ⚠️ EXCEEDS LIMIT!
            }

            gaps = BudgetOptimizer.analyze_gaps(current)
            # Returns: [
            #     BudgetGap(category="roc", gap=-600, priority="CRÍTICO"),  # Overbudget!
            #     BudgetGap(category="rh_dedicados", gap=144000, priority="CRÍTICO"),
            #     BudgetGap(category="outras_despesas", gap=50000, priority="CRÍTICO"),
            #     ...
            # ]
        """

        gaps = []

        # ===== ROC COMPLIANCE CHECK (CRITICAL) =====

        roc_current = current_budget.get(BudgetCategory.ROC.value, 0)
        roc_limit = BUDGET_LIMITS[BudgetCategory.ROC]["maximum"]

        if roc_current > roc_limit:
            gaps.append(BudgetGap(
                category=BudgetCategory.ROC,
                current=roc_current,
                maximum=roc_limit,
                gap=roc_limit - roc_current,  # Negative = overbudget
                priority=PriorityLevel.CRITICAL,
                action=f"REDUZIR ROC de €{roc_current:,.0f} para €{roc_limit:,.0f} (risco rejeição Art. 6.1.e)",
                examples=[
                    "Renegociar contrato ROC para €2,500 máximo",
                    "Reduzir scope auditoria (remover fases opcionais)",
                    "CRÍTICO: Candidatura pode ser rejeitada se exceder €2,500"
                ],
                subsidy_increase=0,  # No subsidy gain, just compliance
                implementation_effort="LOW"
            ))

        # ===== RH DEDICADOS (BIGGEST OPPORTUNITY) =====

        rh_current = current_budget.get(BudgetCategory.RH_DEDICADOS.value, 0)
        rh_limit = BUDGET_LIMITS[BudgetCategory.RH_DEDICADOS]["maximum"]
        rh_gap = rh_limit - rh_current

        if rh_gap > 0:
            # Calculate subsidy increase (75% of gap)
            subsidy_increase = rh_gap * 0.75

            # Context-aware recommendation
            if questionnaire and questionnaire.num_employees < 10:
                # Small team → 1 RH dedicated
                recommended_rh = 80000  # 1 position
                action_text = "Contratar 1 AI/ML Engineer full-time 24 meses (€80k elegível)"
                examples = [
                    "AI/ML Engineer full-time 24m: €40k salary × 2 anos + SS €19k = €99k → €80k elegível (cap)",
                    "Perfil: Develop/fine-tune models, integrate AI solutions, train team, MLOps",
                    "Job description linkado a objetivos projeto (compliance requirement)"
                ]
            else:
                # Larger team → 2 RH dedicated
                recommended_rh = 160000  # 2 positions
                action_text = "Contratar 2 RH dedicados (AI/ML Engineer + Data Scientist 75% allocation)"
                examples = [
                    "AI/ML Engineer full-time 24m: €40k × 2 + SS = €99k → €80k elegível",
                    "Data Scientist 75% allocation 24m: €50k × 75% × 2 + SS = €93k → €80k elegível",
                    "TOTAL: €160k (máximo categoria, scoring máximo Critério B1 Emprego)"
                ]

            gaps.append(BudgetGap(
                category=BudgetCategory.RH_DEDICADOS,
                current=rh_current,
                maximum=rh_limit,
                gap=min(rh_gap, recommended_rh - rh_current),  # Don't exceed recommended
                priority=PriorityLevel.CRITICAL,
                action=action_text,
                examples=examples,
                subsidy_increase=min(rh_gap, recommended_rh - rh_current) * 0.75,
                implementation_effort="HIGH"  # Recruitment + onboarding 3-6 months
            ))

        # ===== OUTRAS DESPESAS (CRITICAL - often €0 current) =====

        outras_current = current_budget.get(BudgetCategory.OUTRAS_DESPESAS.value, 0)
        outras_limit = BUDGET_LIMITS[BudgetCategory.OUTRAS_DESPESAS]["maximum"]
        outras_gap = outras_limit - outras_current

        if outras_gap > 0:
            # Context-aware: if has_dev_team, recommend more cloud GPU
            if questionnaire and questionnaire.has_dev_team:
                recommended_outras = 35000  # Higher for dev teams (GPUs, APIs)
                examples = [
                    "Cloud GPU compute (AWS p3.2xlarge training bursts): €15k",
                    "APIs OpenAI/Anthropic (1M tokens/mês development): €10k",
                    "Data licensing (datasets industry-specific): €5k",
                    "Certificação ISO 42001 AI Management: €5k"
                ]
            else:
                recommended_outras = 20000  # Lower for non-dev teams
                examples = [
                    "Cloud storage/compute (Azure/AWS standard instances): €8k",
                    "APIs OpenAI/Anthropic (500k tokens/mês): €5k",
                    "Data quality tools (annotation, cleaning): €4k",
                    "Certificação ISO 42001 AI Management: €3k"
                ]

            gaps.append(BudgetGap(
                category=BudgetCategory.OUTRAS_DESPESAS,
                current=outras_current,
                maximum=outras_limit,
                gap=min(outras_gap, recommended_outras - outras_current),
                priority=PriorityLevel.CRITICAL,
                action=f"Adicionar outras despesas (cloud, APIs, data, certificações): €{recommended_outras - outras_current:,.0f}",
                examples=examples,
                subsidy_increase=min(outras_gap, recommended_outras - outras_current) * 0.75,
                implementation_effort="MEDIUM"
            ))

        # ===== EQUIPAMENTOS (HIGH - if has_dev_team or data-intensive) =====

        equip_current = current_budget.get(BudgetCategory.EQUIPAMENTOS.value, 0)
        equip_limit = BUDGET_LIMITS[BudgetCategory.EQUIPAMENTOS]["maximum"]
        equip_gap = equip_limit - equip_current

        if equip_gap > 0 and questionnaire:
            # Only recommend equipment if has_dev_team OR data-intensive use cases
            if questionnaire.has_dev_team or "data" in " ".join(questionnaire.use_cases).lower():
                # Recommend workstations (lower risk than GPU server)
                recommended_equip = 24000  # 3× workstations @ €8k each
                examples = [
                    "3× AI Workstations (RTX 4090 24GB, 128GB RAM, 2TB NVMe) @ €8k each = €24k",
                    "Justificação: 3 AI engineers parallel development, local training 1-7B models, IDE performance",
                    "Alternative: 1× GPU Server (4× NVIDIA A100) @ €30k (higher risk, requires justification 100% dedicação)"
                ]

                gaps.append(BudgetGap(
                    category=BudgetCategory.EQUIPAMENTOS,
                    current=equip_current,
                    maximum=equip_limit,
                    gap=min(equip_gap, recommended_equip - equip_current),
                    priority=PriorityLevel.HIGH,
                    action=f"Adicionar equipamentos (workstations AI): €{recommended_equip - equip_current:,.0f}",
                    examples=examples,
                    subsidy_increase=min(equip_gap, recommended_equip - equip_current) * 0.75,
                    implementation_effort="MEDIUM"
                ))

        # ===== SOFTWARE (MEDIUM - often already allocated) =====

        software_current = current_budget.get(BudgetCategory.SOFTWARE.value, 0)
        software_limit = BUDGET_LIMITS[BudgetCategory.SOFTWARE]["maximum"]
        software_gap = software_limit - software_current

        if software_gap > 10000:  # Only suggest if gap > €10k (significant)
            recommended_software_increase = min(software_gap, 20000)  # Cap at €20k increase
            examples = [
                "Upgrade SaaS tiers (ex: ChatGPT Team → Business, Gemini Standard → Advanced)",
                "Adicionar ML platforms (Azure ML Studio: €4k, AWS SageMaker: €3k)",
                "Power BI Premium / Tableau: €5k (se data analysis use case)"
            ]

            gaps.append(BudgetGap(
                category=BudgetCategory.SOFTWARE,
                current=software_current,
                maximum=software_limit,
                gap=recommended_software_increase,
                priority=PriorityLevel.MEDIUM,
                action=f"Expandir software/SaaS: +€{recommended_software_increase:,.0f}",
                examples=examples,
                subsidy_increase=recommended_software_increase * 0.75,
                implementation_effort="LOW"
            ))

        # ===== CONSULTORIA (MEDIUM) =====

        consult_current = current_budget.get(BudgetCategory.CONSULTORIA.value, 0)
        consult_limit = BUDGET_LIMITS[BudgetCategory.CONSULTORIA]["maximum"]
        consult_gap = consult_limit - consult_current

        if consult_gap > 10000:
            recommended_consult_increase = min(consult_gap, 15000)  # Conservative increase
            examples = [
                "AI strategy consulting (roadmap, use case prioritization): €5k",
                "Change management (adoption, resistance mitigation): €5k",
                "Legal compliance AI (RGPD audit, EU AI Act readiness): €5k"
            ]

            gaps.append(BudgetGap(
                category=BudgetCategory.CONSULTORIA,
                current=consult_current,
                maximum=consult_limit,
                gap=recommended_consult_increase,
                priority=PriorityLevel.MEDIUM,
                action=f"Expandir consultoria (strategy, change mgmt, legal): +€{recommended_consult_increase:,.0f}",
                examples=examples,
                subsidy_increase=recommended_consult_increase * 0.75,
                implementation_effort="LOW"
            ))

        # ===== FORMACAO (HIGH - if training_priority) =====

        formacao_current = current_budget.get(BudgetCategory.FORMACAO.value, 0)
        formacao_limit = BUDGET_LIMITS[BudgetCategory.FORMACAO]["maximum"]
        formacao_gap = formacao_limit - formacao_current

        if formacao_gap > 5000 and questionnaire and questionnaire.training_priority:
            # Calculate realistic formação budget based on num_employees_training
            num_training = questionnaire.num_employees_training or 10
            cost_per_participant = 2466  # AiParaTi 64h package
            recommended_formacao = min(num_training * cost_per_participant, formacao_limit)
            recommended_increase = min(recommended_formacao - formacao_current, formacao_gap)

            examples = [
                f"AiParaTi Pacote Completo 64h: {num_training} participants × €{cost_per_participant:,.0f} = €{recommended_formacao:,.0f}",
                "Módulos: AI Fundamentals (16h), Prompt Eng (12h), Azure AI (20h), RGPD (8h), Ethics (8h)",
                "Certificação DGERT garantida (único provider IA certificado Portugal)"
            ]

            gaps.append(BudgetGap(
                category=BudgetCategory.FORMACAO,
                current=formacao_current,
                maximum=formacao_limit,
                gap=recommended_increase,
                priority=PriorityLevel.HIGH,
                action=f"Expandir formação (AiParaTi prioridade): +€{recommended_increase:,.0f}",
                examples=examples,
                subsidy_increase=recommended_increase * 0.75,
                implementation_effort="MEDIUM"
            ))

        # Sort by priority (CRÍTICO first)
        priority_order = {
            PriorityLevel.CRITICAL: 0,
            PriorityLevel.HIGH: 1,
            PriorityLevel.MEDIUM: 2,
            PriorityLevel.LOW: 3
        }
        gaps.sort(key=lambda g: (priority_order[g.priority], -abs(g.gap)))

        total_gap = sum(g.gap for g in gaps if g.gap > 0)
        total_subsidy_increase = sum(g.subsidy_increase for g in gaps if g.subsidy_increase and g.gap > 0)

        logger.info(
            f"Budget gap analysis complete: {len(gaps)} gaps identified, "
            f"total opportunity €{total_gap:,.0f} (subsidy increase €{total_subsidy_increase:,.0f})"
        )

        return gaps

    @staticmethod
    def generate_expansion_paths(
        current_total: float,
        gaps: List[BudgetGap],
        questionnaire: Optional[DiagnosticQuestionnaire] = None
    ) -> Dict[str, BudgetPath]:
        """
        Generate 3 budget expansion scenarios (IFIC pattern).

        Paths:
            - Conservador: Fix compliance + 1 critical gap (safe)
            - Moderado: Fix compliance + 2-3 critical gaps (RECOMMENDED)
            - Agressivo: Maximize all categories (ambitious)

        Args:
            current_total: Current total budget (€)
            gaps: List of BudgetGap from analyze_gaps()
            questionnaire: Optional context for recommendations

        Returns:
            Dict with 3 BudgetPath objects (conservador, moderado, agressivo)
        """

        # Calculate current subsidy (75%)
        current_subsidy = current_total * 0.75

        # ===== CONSERVADOR PATH: Fix ROC + 1 RH =====

        conservador_changes = {}
        conservador_total = current_total

        # Fix ROC if overbudget
        roc_gap = next((g for g in gaps if g.category == BudgetCategory.ROC), None)
        if roc_gap and roc_gap.gap < 0:  # Overbudget
            conservador_changes[BudgetCategory.ROC.value] = BudgetChange(
                from_amount=roc_gap.current,
                to_amount=roc_gap.maximum,
                delta=roc_gap.gap,  # Negative
                justification="Compliance Art. 6.1.e (limite €2,500)"
            )
            conservador_total += roc_gap.gap  # Subtract overbudget amount

        # Add 1 RH dedicated (if gap exists)
        rh_gap = next((g for g in gaps if g.category == BudgetCategory.RH_DEDICADOS), None)
        if rh_gap and rh_gap.gap > 0:
            rh_increase = 64000  # 1 position (~€80k but conservative)
            conservador_changes[BudgetCategory.RH_DEDICADOS.value] = BudgetChange(
                from_amount=rh_gap.current,
                to_amount=rh_gap.current + rh_increase,
                delta=rh_increase,
                justification="1 AI Engineer contratado (mínimo viável scoring B1)"
            )
            conservador_total += rh_increase

        # Add small outras_despesas
        outras_gap = next((g for g in gaps if g.category == BudgetCategory.OUTRAS_DESPESAS), None)
        if outras_gap and outras_gap.gap > 0:
            outras_increase = 15000  # Conservative
            conservador_changes[BudgetCategory.OUTRAS_DESPESAS.value] = BudgetChange(
                from_amount=outras_gap.current,
                to_amount=outras_gap.current + outras_increase,
                delta=outras_increase,
                justification="Cloud + APIs básicos (€15k)"
            )
            conservador_total += outras_increase

        conservador_subsidy = conservador_total * 0.75

        conservador_path = BudgetPath(
            name="Conservador",
            current_total=current_total,
            target_total=conservador_total,
            increase=conservador_total - current_total,
            changes=conservador_changes,
            subsidy_75_percent=conservador_subsidy,
            subsidy_increase=conservador_subsidy - current_subsidy,
            justification="Mínimo viável: compliance ROC + 1 AI Engineer + cloud básico. Baixo risco aprovação.",
            implementation_effort="MEDIUM",
            timeline_weeks=8,
            risk_level="LOW"
        )

        # ===== MODERADO PATH: 1.5 RH + Outras + Equipamentos (RECOMMENDED) =====

        moderado_changes = {}
        moderado_total = current_total

        # Fix ROC
        if roc_gap and roc_gap.gap < 0:
            moderado_changes[BudgetCategory.ROC.value] = conservador_changes[BudgetCategory.ROC.value]
            moderado_total += roc_gap.gap

        # Add 1.5 RH (120k)
        if rh_gap and rh_gap.gap > 0:
            rh_increase = 104000  # From 16k → 120k (1.5 FTE)
            moderado_changes[BudgetCategory.RH_DEDICADOS.value] = BudgetChange(
                from_amount=rh_gap.current,
                to_amount=120000,
                delta=rh_increase,
                justification="1 AI Engineer full + 1 Data Scientist 75% allocation"
            )
            moderado_total += rh_increase

        # Outras despesas (35k)
        if outras_gap and outras_gap.gap > 0:
            outras_increase = 35000
            moderado_changes[BudgetCategory.OUTRAS_DESPESAS.value] = BudgetChange(
                from_amount=outras_gap.current,
                to_amount=35000,
                delta=outras_increase,
                justification="Cloud GPU €15k + APIs €10k + Data €5k + Certs €5k"
            )
            moderado_total += outras_increase

        # Equipamentos (25k)
        equip_gap = next((g for g in gaps if g.category == BudgetCategory.EQUIPAMENTOS), None)
        if equip_gap and equip_gap.gap > 0:
            equip_increase = 25000
            moderado_changes[BudgetCategory.EQUIPAMENTOS.value] = BudgetChange(
                from_amount=equip_gap.current,
                to_amount=25000,
                delta=equip_increase,
                justification="3× AI Workstations RTX 4090"
            )
            moderado_total += equip_increase

        # Software expansion (10k)
        software_gap = next((g for g in gaps if g.category == BudgetCategory.SOFTWARE), None)
        if software_gap and software_gap.gap > 10000:
            software_increase = 10000
            moderado_changes[BudgetCategory.SOFTWARE.value] = BudgetChange(
                from_amount=software_gap.current,
                to_amount=software_gap.current + software_increase,
                delta=software_increase,
                justification="Upgrade SaaS tiers + ML platforms"
            )
            moderado_total += software_increase

        # Consultoria (9k)
        consult_gap = next((g for g in gaps if g.category == BudgetCategory.CONSULTORIA), None)
        if consult_gap and consult_gap.gap > 10000:
            consult_increase = 9000
            moderado_changes[BudgetCategory.CONSULTORIA.value] = BudgetChange(
                from_amount=consult_gap.current,
                to_amount=consult_gap.current + consult_increase,
                delta=consult_increase,
                justification="Strategy + Change mgmt consulting"
            )
            moderado_total += consult_increase

        moderado_subsidy = moderado_total * 0.75

        moderado_path = BudgetPath(
            name="Moderado (RECOMENDADO)",
            current_total=current_total,
            target_total=moderado_total,
            increase=moderado_total - current_total,
            changes=moderado_changes,
            subsidy_75_percent=moderado_subsidy,
            subsidy_increase=moderado_subsidy - current_subsidy,
            justification=f"Sweet spot IFIC: ambicioso mas justificável. Target €220-230k maximiza ROI vs. esforço. Subsídio aumenta €{moderado_subsidy - current_subsidy:,.0f} (vs. esforço moderado 12-16 semanas).",
            implementation_effort="MEDIUM",
            timeline_weeks=14,
            risk_level="MEDIUM"
        )

        # ===== AGRESSIVO PATH: Maximize all categories =====

        agressivo_changes = {}
        agressivo_total = current_total

        # Fix ROC
        if roc_gap and roc_gap.gap < 0:
            agressivo_changes[BudgetCategory.ROC.value] = conservador_changes[BudgetCategory.ROC.value]
            agressivo_total += roc_gap.gap

        # Maximize RH (160k)
        if rh_gap and rh_gap.gap > 0:
            agressivo_changes[BudgetCategory.RH_DEDICADOS.value] = BudgetChange(
                from_amount=rh_gap.current,
                to_amount=160000,
                delta=160000 - rh_gap.current,
                justification="2× AI Engineers full-time 24m (máximo elegível)"
            )
            agressivo_total += (160000 - rh_gap.current)

        # Maximize outras_despesas (45k)
        if outras_gap and outras_gap.gap > 0:
            agressivo_changes[BudgetCategory.OUTRAS_DESPESAS.value] = BudgetChange(
                from_amount=outras_gap.current,
                to_amount=45000,
                delta=45000 - outras_gap.current,
                justification="Cloud €15k + APIs €16k + Data €12k + Certs €8k (near maximum)"
            )
            agressivo_total += (45000 - outras_gap.current)

        # Maximize equipamentos (40k)
        if equip_gap and equip_gap.gap > 0:
            agressivo_changes[BudgetCategory.EQUIPAMENTOS.value] = BudgetChange(
                from_amount=equip_gap.current,
                to_amount=40000,
                delta=40000 - equip_gap.current,
                justification="GPU Server 4× A100 (requer justificação 100% dedicação)"
            )
            agressivo_total += (40000 - equip_gap.current)

        # Maximize software (60k)
        if software_gap and software_gap.gap > 0:
            software_target = min(software_gap.current + 20000, 60000)
            agressivo_changes[BudgetCategory.SOFTWARE.value] = BudgetChange(
                from_amount=software_gap.current,
                to_amount=software_target,
                delta=software_target - software_gap.current,
                justification="Enterprise SaaS tiers + ML platforms completos"
            )
            agressivo_total += (software_target - software_gap.current)

        # Maximize consultoria (50k)
        if consult_gap and consult_gap.gap > 0:
            consult_target = min(consult_gap.current + 14000, 50000)
            agressivo_changes[BudgetCategory.CONSULTORIA.value] = BudgetChange(
                from_amount=consult_gap.current,
                to_amount=consult_target,
                delta=consult_target - consult_gap.current,
                justification="Strategy + Implementation + Change mgmt + Legal"
            )
            agressivo_total += (consult_target - consult_gap.current)

        agressivo_subsidy = agressivo_total * 0.75

        agressivo_path = BudgetPath(
            name="Agressivo",
            current_total=current_total,
            target_total=agressivo_total,
            increase=agressivo_total - current_total,
            changes=agressivo_changes,
            subsidy_75_percent=agressivo_subsidy,
            subsidy_increase=agressivo_subsidy - current_subsidy,
            justification=f"Máximo elegível: near-limits todas categorias. Alto risco documentação (requer justificação extensa cada € gasto). Subsídio €{agressivo_subsidy:,.0f} mas esforço muito alto.",
            implementation_effort="HIGH",
            timeline_weeks=20,
            risk_level="HIGH"
        )

        logger.info(
            f"Generated 3 expansion paths: Conservador (€{conservador_total:,.0f}), "
            f"Moderado (€{moderado_total:,.0f}), Agressivo (€{agressivo_total:,.0f})"
        )

        return {
            "conservador": conservador_path,
            "moderado": moderado_path,
            "agressivo": agressivo_path
        }

    @staticmethod
    def calculate_roi(path: BudgetPath, current_subsidy: float) -> Dict[str, float]:
        """
        Calculate ROI of expansion path.

        ROI = (Subsidy Increase) / (Implementation Effort Cost)

        Implementation effort costs (estimates):
            - LOW: €2k (documentation only, 1-2 weeks)
            - MEDIUM: €8k (recruitment, setup, 8-14 weeks)
            - HIGH: €20k (full recruitment, complex procurement, 16-20 weeks)
        """

        effort_costs = {
            "LOW": 2000,
            "MEDIUM": 8000,
            "HIGH": 20000
        }

        implementation_cost = effort_costs.get(path.implementation_effort, 8000)
        subsidy_increase = path.subsidy_increase

        roi = subsidy_increase / implementation_cost if implementation_cost > 0 else 0

        return {
            "subsidy_increase": subsidy_increase,
            "implementation_cost": implementation_cost,
            "roi_multiple": roi,
            "roi_percent": (roi - 1) * 100 if roi > 1 else 0
        }
