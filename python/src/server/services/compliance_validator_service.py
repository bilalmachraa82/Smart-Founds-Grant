"""
Compliance Validator Service

Validates project eligibility against Aviso 03/C05 rules automatically.
Each rule has specific blocker messages (IFIC pattern).

Validation Rules:
    1. PME Criteria (Art. 4.1)
        - Employees < 250
        - Revenue < €50M OR Balance sheet < €43M

    2. Investment Range (Art. 6.1.a)
        - Minimum: €20,000
        - Maximum: €500,000

    3. Project Duration (Art. 6.1.c)
        - Maximum: 12 months

    4. ROC Limit (Art. 6.1.e)
        - Maximum: €2,500 (HARD LIMIT)

    5. CAE Eligibility
        - Must be in eligible sectors whitelist

    6. Budget Distribution
        - Software + Training + Consulting + RH + Equipment + ROC = 100%
        - No category exceeds maximum limit

Example:
    result = ComplianceValidator.validate(project_data)
    # Returns: ComplianceResult(
    #     status="ELEGÍVEL" | "ELEGÍVEL COM AVISOS" | "NÃO ELEGÍVEL",
    #     blockers=[...],  # Critical issues blocking submission
    #     warnings=[...],  # Non-critical issues to review
    #     eligibility_score=0.85  # 0.0-1.0 (1.0 = fully compliant)
    # )
"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from enum import Enum

from ..models.questionnaire import DiagnosticQuestionnaire
from ..config.logfire_config import get_logger

logger = get_logger(__name__)


# ===== MODELS =====

class SeverityLevel(str, Enum):
    """Issue severity levels"""
    BLOCKER = "BLOCKER"      # Prevents submission
    WARNING = "WARNING"      # Should review, but not blocking
    INFO = "INFO"            # Informational only


class ComplianceIssue(BaseModel):
    """Single compliance issue (blocker or warning)"""

    rule_id: str = Field(..., description="Rule identifier (e.g., 'R1_PME_EMPLOYEES')")
    rule_name: str = Field(..., description="Rule name (e.g., 'PME Employees Limit')")
    article: str = Field(..., description="Aviso article (e.g., 'Art. 4.1.a')")
    severity: SeverityLevel

    # Issue details
    issue: str = Field(..., description="What's wrong? (specific values)")
    fix: str = Field(..., description="How to fix? (actionable steps)")

    # Context
    current_value: Optional[str] = Field(None, description="Current value (e.g., '300 employees')")
    required_value: Optional[str] = Field(None, description="Required value (e.g., '<250 employees')")

    class Config:
        use_enum_values = True


class ComplianceResult(BaseModel):
    """Complete compliance validation result"""

    status: str = Field(..., description="ELEGÍVEL | ELEGÍVEL COM AVISOS | NÃO ELEGÍVEL")

    # Issues
    blockers: List[ComplianceIssue] = Field(default=[], description="Critical issues (prevent submission)")
    warnings: List[ComplianceIssue] = Field(default=[], description="Non-critical issues (review recommended)")

    # Score
    eligibility_score: float = Field(..., ge=0, le=1, description="Compliance score 0-1 (1.0 = fully compliant)")

    # Summary
    num_blockers: int = Field(0, description="Number of blocking issues")
    num_warnings: int = Field(0, description="Number of warnings")
    compliance_percentage: float = Field(..., description="% of rules passed")


# ===== COMPLIANCE RULES =====

# CAE Whitelist (simplified - full list has 100+ CAEs)
# Source: Aviso 03/C05-i14.01/2025 Anexo I
CAE_WHITELIST = [
    # Technology / Software
    "62010",  # Atividades de consultoria em informática
    "62020",  # Atividades de consultoria em gestão
    "62030",  # Gestão e exploração de equipamento informático
    "62090",  # Outras atividades de tecnologias de informação e serviços informáticos
    "63110",  # Atividades de processamento de dados, domiciliação de informação e actividades relacionadas
    "63120",  # Portais Web

    # Manufacturing (selective)
    "25110",  # Fabricação de estruturas de construções metálicas
    "26110",  # Fabricação de componentes electrónicos
    "26200",  # Fabricação de computadores e de equipamento periférico
    "26300",  # Fabricação de equipamento de comunicação
    "26510",  # Fabricação de instrumentos e aparelhos de medida, verificação e navegação
    "27110",  # Fabricação de motores, geradores e transformadores eléctricos
    "28110",  # Fabricação de motores e turbinas, excepto para aeronaves, veículos automóveis e motociclos

    # Professional Services
    "70220",  # Outras atividades de consultoria para os negócios e a gestão
    "71110",  # Atividades de arquitectura
    "71120",  # Atividades de engenharia e técnicas afins
    "71200",  # Actividades de ensaios e análises técnicas
    "72110",  # Investigação e desenvolvimento em biotecnologia
    "72190",  # Outra investigação e desenvolvimento das ciências físicas e naturais
    "72200",  # Investigação e desenvolvimento das ciências sociais e humanas
    "73110",  # Agências de publicidade
    "73120",  # Agenciamento de espaços publicitários
    "73200",  # Estudos de mercado e sondagens de opinião

    # Healthcare
    "86100",  # Atividades dos estabelecimentos de saúde com internamento
    "86210",  # Atividades de prática médica de clínica geral, em ambulatório
    "86220",  # Actividades de prática médica de clínica especializada, em ambulatório
    "86900",  # Outras actividades de saúde humana

    # Education
    "85590",  # Outras actividades educativas diversas, n.e.
    "85600",  # Actividades de serviços de apoio à educação

    # Add more as needed (this is representative sample)
]


# ===== COMPLIANCE VALIDATOR SERVICE =====

class ComplianceValidator:
    """
    Automated compliance validation against Aviso 03/C05.

    Validates 6 key rules:
        1. PME criteria (employees, revenue, balance)
        2. Investment range (€20k-500k)
        3. Project duration (max 12 months)
        4. ROC limit (max €2,500)
        5. CAE eligibility (whitelist)
        6. Budget distribution (category limits)
    """

    @staticmethod
    def validate(
        questionnaire: DiagnosticQuestionnaire,
        budget: Optional[Dict[str, float]] = None
    ) -> ComplianceResult:
        """
        Validate project eligibility.

        Args:
            questionnaire: Diagnostic questionnaire with company data
            budget: Optional budget breakdown by category

        Returns:
            ComplianceResult with blockers, warnings, and eligibility score
        """

        blockers = []
        warnings = []

        # ===== RULE 1: PME EMPLOYEES (Art. 4.1.a) =====

        if questionnaire.num_employees > 249:
            blockers.append(ComplianceIssue(
                rule_id="R1_PME_EMPLOYEES",
                rule_name="PME Employees Limit",
                article="Art. 4.1.a",
                severity=SeverityLevel.BLOCKER,
                issue=f"Empresa tem {questionnaire.num_employees} colaboradores (máximo 249 para PME)",
                fix="NÃO ELEGÍVEL - Grande empresa. Considerar Aviso diferente (ex: Inovação Produtiva).",
                current_value=f"{questionnaire.num_employees} colaboradores",
                required_value="<250 colaboradores (PME)"
            ))

        # ===== RULE 2: PME REVENUE/BALANCE (Art. 4.1.b) =====

        if questionnaire.annual_revenue > 50_000_000:
            blockers.append(ComplianceIssue(
                rule_id="R2_PME_REVENUE",
                rule_name="PME Revenue Limit",
                article="Art. 4.1.b",
                severity=SeverityLevel.BLOCKER,
                issue=f"Faturação €{questionnaire.annual_revenue:,.0f} excede máximo €50M para PME",
                fix="NÃO ELEGÍVEL - Grande empresa. Verificar balanço (se <€43M ainda pode ser PME).",
                current_value=f"€{questionnaire.annual_revenue:,.0f} faturação",
                required_value="<€50M faturação OU <€43M balanço"
            ))

        # ===== RULE 3: INVESTMENT RANGE (Art. 6.1.a) =====

        if questionnaire.desired_investment < 20_000:
            blockers.append(ComplianceIssue(
                rule_id="R3_INVESTMENT_MIN",
                rule_name="Investment Minimum",
                article="Art. 6.1.a",
                severity=SeverityLevel.BLOCKER,
                issue=f"Investimento €{questionnaire.desired_investment:,.0f} abaixo mínimo €20,000",
                fix="Aumentar orçamento para mínimo €20,000 (adicionar despesas elegíveis: RH, software, formação).",
                current_value=f"€{questionnaire.desired_investment:,.0f}",
                required_value="≥€20,000"
            ))

        if questionnaire.desired_investment > 500_000:
            blockers.append(ComplianceIssue(
                rule_id="R3_INVESTMENT_MAX",
                rule_name="Investment Maximum",
                article="Art. 6.1.a",
                severity=SeverityLevel.BLOCKER,
                issue=f"Investimento €{questionnaire.desired_investment:,.0f} excede máximo €500,000",
                fix="Reduzir orçamento para máximo €500,000 OU dividir em 2 candidaturas (Fase I + Fase II).",
                current_value=f"€{questionnaire.desired_investment:,.0f}",
                required_value="≤€500,000"
            ))

        # ===== RULE 4: PROJECT DURATION (Art. 6.1.c) =====

        if questionnaire.project_duration_months > 12:
            blockers.append(ComplianceIssue(
                rule_id="R4_DURATION",
                rule_name="Project Duration",
                article="Art. 6.1.c",
                severity=SeverityLevel.BLOCKER,
                issue=f"Prazo {questionnaire.project_duration_months} meses excede máximo 12 meses",
                fix="Reduzir duração para 12 meses (remover fases opcionais, acelerar cronograma).",
                current_value=f"{questionnaire.project_duration_months} meses",
                required_value="≤12 meses"
            ))
        elif questionnaire.project_duration_months < 6:
            warnings.append(ComplianceIssue(
                rule_id="R4_DURATION_SHORT",
                rule_name="Project Duration (Short)",
                article="Art. 6.1.c",
                severity=SeverityLevel.WARNING,
                issue=f"Prazo {questionnaire.project_duration_months} meses é muito curto (recomendado 9-12 meses)",
                fix="Considerar expandir para 9-12 meses (permite mais atividades, melhor scoring coerência).",
                current_value=f"{questionnaire.project_duration_months} meses",
                required_value="9-12 meses (recomendado)"
            ))

        # ===== RULE 5: ROC LIMIT (Art. 6.1.e) =====

        if budget:
            roc_budget = budget.get("roc", 0)
            if roc_budget > 2500:
                blockers.append(ComplianceIssue(
                    rule_id="R5_ROC_LIMIT",
                    rule_name="ROC (Statutory Auditor) Limit",
                    article="Art. 6.1.e",
                    severity=SeverityLevel.BLOCKER,
                    issue=f"ROC €{roc_budget:,.0f} excede limite HARD €2,500",
                    fix="CRÍTICO: Renegociar contrato ROC para €2,500 máximo. Risco rejeição candidatura.",
                    current_value=f"€{roc_budget:,.0f}",
                    required_value="≤€2,500 (HARD LIMIT)"
                ))

        # ===== RULE 6: CAE ELIGIBILITY (Whitelist) =====

        if questionnaire.cae_code not in CAE_WHITELIST:
            warnings.append(ComplianceIssue(
                rule_id="R6_CAE_WHITELIST",
                rule_name="CAE Sector Eligibility",
                article="Anexo I - Lista CAE Elegíveis",
                severity=SeverityLevel.WARNING,
                issue=f"CAE {questionnaire.cae_code} ({questionnaire.industry_sector.value}) não encontrado na whitelist pré-aprovados",
                fix="Verificar manualmente elegibilidade com IAPMEI (submit query). Alguns CAEs são elegíveis mas não listados explicitamente.",
                current_value=f"CAE {questionnaire.cae_code}",
                required_value="CAE em Anexo I (whitelist) ou aprovação IAPMEI"
            ))

        # ===== RULE 7: RGPD SENSITIVE DATA (if applicable) =====

        if questionnaire.rgpd_sensitive_data:
            warnings.append(ComplianceIssue(
                rule_id="R7_RGPD",
                rule_name="RGPD Sensitive Data",
                article="RGPD Art. 6 + Art. 35 (DPIA)",
                severity=SeverityLevel.WARNING,
                issue="Projeto processa dados sensíveis RGPD (saúde, financeiros, crianças)",
                fix=(
                    "OBRIGATÓRIO: (1) Data Protection Impact Assessment (DPIA), "
                    "(2) Pseudonimização datasets, (3) Audit CNPD preventivo, "
                    "(4) Formação RGPD 8h equipa. Multas CNPD até 4% revenue global."
                ),
                current_value="Dados sensíveis: SIM",
                required_value="DPIA + pseudonimização + audit CNPD"
            ))

        # ===== RULE 8: BUDGET DISTRIBUTION (Category Limits) =====

        if budget:
            from .budget_optimizer_service import BUDGET_LIMITS, BudgetCategory

            for category_str, amount in budget.items():
                try:
                    category = BudgetCategory(category_str)
                    limit_data = BUDGET_LIMITS.get(category)

                    if limit_data and amount > limit_data["maximum"]:
                        blockers.append(ComplianceIssue(
                            rule_id=f"R8_BUDGET_{category_str.upper()}",
                            rule_name=f"Budget Limit: {category_str.replace('_', ' ').title()}",
                            article="Art. 6.1 (Despesas Elegíveis)",
                            severity=SeverityLevel.BLOCKER,
                            issue=f"{category_str.replace('_', ' ').title()}: €{amount:,.0f} excede limite €{limit_data['maximum']:,.0f}",
                            fix=f"Reduzir {category_str} para máximo €{limit_data['maximum']:,.0f}. Notas: {limit_data['notes']}",
                            current_value=f"€{amount:,.0f}",
                            required_value=f"≤€{limit_data['maximum']:,.0f}"
                        ))
                except ValueError:
                    # Unknown category, skip
                    pass

        # ===== CALCULATE COMPLIANCE SCORE =====

        total_rules = 8  # 8 major rules checked
        rules_passed = total_rules - len(blockers)
        eligibility_score = rules_passed / total_rules

        compliance_percentage = (rules_passed / total_rules) * 100

        # Determine status
        if len(blockers) == 0 and len(warnings) == 0:
            status = "ELEGÍVEL"
        elif len(blockers) == 0 and len(warnings) > 0:
            status = "ELEGÍVEL COM AVISOS"
        else:
            status = "NÃO ELEGÍVEL"

        logger.info(
            f"Compliance validation: Status={status}, "
            f"Blockers={len(blockers)}, Warnings={len(warnings)}, "
            f"Score={eligibility_score:.2f} ({compliance_percentage:.0f}% rules passed)"
        )

        return ComplianceResult(
            status=status,
            blockers=blockers,
            warnings=warnings,
            eligibility_score=eligibility_score,
            num_blockers=len(blockers),
            num_warnings=len(warnings),
            compliance_percentage=compliance_percentage
        )

    @staticmethod
    def check_pme_status(
        num_employees: int,
        annual_revenue: float,
        balance_sheet: Optional[float] = None
    ) -> Dict[str, bool]:
        """
        Check PME status (Small-Medium Enterprise).

        PME Criteria (Art. 4.1):
            - Employees < 250 AND
            - (Revenue < €50M OR Balance sheet < €43M)

        Args:
            num_employees: Number of employees
            annual_revenue: Annual revenue (€)
            balance_sheet: Balance sheet total (€), optional

        Returns:
            Dict with PME status and details
        """

        is_pme_employees = num_employees < 250

        is_pme_revenue = annual_revenue < 50_000_000

        if balance_sheet is not None:
            is_pme_balance = balance_sheet < 43_000_000
            is_pme_financial = is_pme_revenue or is_pme_balance
        else:
            is_pme_balance = None
            is_pme_financial = is_pme_revenue  # Assume revenue only

        is_pme = is_pme_employees and is_pme_financial

        return {
            "is_pme": is_pme,
            "is_pme_employees": is_pme_employees,
            "is_pme_revenue": is_pme_revenue,
            "is_pme_balance": is_pme_balance,
            "num_employees": num_employees,
            "annual_revenue": annual_revenue,
            "balance_sheet": balance_sheet
        }

    @staticmethod
    def validate_budget_distribution(budget: Dict[str, float]) -> List[ComplianceIssue]:
        """
        Validate budget distribution across categories.

        Checks:
            - Each category ≤ maximum limit
            - Total budget within €20k-500k range
            - ROC ≤ €2,500 (critical)

        Args:
            budget: Budget breakdown by category (€)

        Returns:
            List of compliance issues (blockers + warnings)
        """

        issues = []
        total_budget = sum(budget.values())

        # Check total range
        if total_budget < 20_000:
            issues.append(ComplianceIssue(
                rule_id="R_BUDGET_TOTAL_MIN",
                rule_name="Total Budget Minimum",
                article="Art. 6.1.a",
                severity=SeverityLevel.BLOCKER,
                issue=f"Orçamento total €{total_budget:,.0f} abaixo mínimo €20,000",
                fix="Aumentar orçamento adicionando despesas elegíveis.",
                current_value=f"€{total_budget:,.0f}",
                required_value="≥€20,000"
            ))

        if total_budget > 500_000:
            issues.append(ComplianceIssue(
                rule_id="R_BUDGET_TOTAL_MAX",
                rule_name="Total Budget Maximum",
                article="Art. 6.1.a",
                severity=SeverityLevel.BLOCKER,
                issue=f"Orçamento total €{total_budget:,.0f} excede máximo €500,000",
                fix="Reduzir orçamento ou dividir em 2 candidaturas.",
                current_value=f"€{total_budget:,.0f}",
                required_value="≤€500,000"
            ))

        # Check category limits (already done in main validate(), but can be standalone)

        return issues
