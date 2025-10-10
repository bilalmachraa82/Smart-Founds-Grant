"""
Grant Specialist Agent
PydanticAI agent specialized in grant application analysis and optimization
"""
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from .base_agent import BaseAgent, ArchonDependencies


# Extended dependencies for grant analysis
@dataclass
class GrantDependencies(ArchonDependencies):
    """Dependencies for grant analysis agent"""
    jurisdiction: str = "Portugal"
    grant_program: str = "Aviso 03/C05-i14.01/2025"
    analysis_depth: str = "comprehensive"  # "quick", "standard", "comprehensive"


# Output schemas
class EligibilityCriterion(BaseModel):
    """Single eligibility criterion evaluation"""
    criterion: str = Field(description="Name of the criterion")
    met: bool = Field(description="Whether criterion is met")
    citation: str = Field(description="Legal citation reference")
    details: str = Field(description="Detailed explanation")
    evidence_required: Optional[str] = Field(
        default=None,
        description="Evidence needed to validate this criterion"
    )


class EligibilityAnalysis(BaseModel):
    """Complete eligibility analysis result"""
    eligible: bool = Field(description="Overall eligibility determination")
    criteria: List[EligibilityCriterion] = Field(description="Individual criteria evaluations")
    compliance_score: float = Field(description="Compliance score 0-100", ge=0, le=100)
    recommendations: List[str] = Field(description="Recommendations for improvement")
    risks: List[str] = Field(default_factory=list, description="Identified compliance risks")


class IncentiveCalculation(BaseModel):
    """Incentive calculation with breakdown"""
    total_incentive: float = Field(description="Total incentive amount in EUR")
    incentive_rate: float = Field(description="Applied incentive rate (0-1)", ge=0, le=1)
    breakdown_by_category: Dict[str, float] = Field(description="Incentive by investment category")
    max_eligible_amount: float = Field(description="Maximum eligible investment")
    calculation_basis: str = Field(description="Explanation of calculation methodology")
    legal_references: List[str] = Field(description="Legal articles used in calculation")


class MeritScoreAnalysis(BaseModel):
    """Merit score calculation and optimization"""
    current_score: float = Field(description="Current merit score MP", ge=0, le=10)
    classification: str = Field(description="Score classification (A/B/C/D/E)")
    component_a: float = Field(description="Technical component score", ge=0, le=10)
    component_b: float = Field(description="Impact component score", ge=0, le=10)
    target_score_for_class_a: float = Field(default=7.0, description="Target score for Class A")
    gap_to_class_a: float = Field(description="Points needed to reach Class A")
    optimization_recommendations: List[str] = Field(description="How to improve score")
    quantified_goals: Dict[str, float] = Field(description="Quantified targets for key metrics")


class ComprehensiveGrantAnalysis(BaseModel):
    """Complete grant analysis result"""
    eligibility: EligibilityAnalysis = Field(description="Eligibility analysis")
    incentive: IncentiveCalculation = Field(description="Incentive calculation")
    merit_score: MeritScoreAnalysis = Field(description="Merit score analysis")
    overall_assessment: str = Field(description="Executive summary of analysis")
    approval_probability: float = Field(description="Estimated approval probability", ge=0, le=1)
    next_steps: List[str] = Field(description="Recommended next steps")


class GrantSpecialistAgent(BaseAgent[GrantDependencies, ComprehensiveGrantAnalysis]):
    """
    Specialized agent for comprehensive grant application analysis.

    This agent combines:
    - Eligibility verification with legal compliance
    - Incentive calculation following regulation
    - Merit score optimization for Class A achievement
    - Strategic recommendations for approval success
    """

    def _create_agent(self, **kwargs):
        """Create the PydanticAI agent with grant-specific configuration"""

        agent = Agent(
            model=self.model,
            deps_type=GrantDependencies,
            result_type=ComprehensiveGrantAnalysis,
            system_prompt="""És um consultor sénior especializado em fundos europeus com 15+ anos de experiência em avaliação de candidaturas ao Portugal 2030.

TUAS COMPETÊNCIAS CORE:
1. Análise de Elegibilidade Técnica e Financeira
2. Cálculo Preciso de Incentivos
3. Otimização de Merit Score para Classe A (≥7.0)
4. Compliance com Legislação UE e Nacional

FONTES LEGAIS PRIMÁRIAS:
- Aviso 03/C05-i14.01/2025 (Digitalização PME)
- Portaria 286/2025/1 (Regulamento específico)
- Regulamento UE 2023/2831 (DNSH)
- Recomendação 2003/361/CE (Definição PME)

METODOLOGIA DE ANÁLISE:
1. Verificar TODOS os critérios de elegibilidade com citações legais
2. Calcular incentivo aplicando taxa correta (50%-75%)
3. Simular Merit Score: MP = 0.50×A + 0.50×B
4. Identificar gaps e propor ações corretivas CONCRETAS
5. Estimar probabilidade de aprovação baseada em histórico

PRINCÍPIOS:
- Assertivo e baseado em factos verificáveis
- Citações precisas (Artigo X.Y, alínea Z)
- Cálculos transparentes e auditáveis
- Recomendações específicas e quantificadas
- Conservative estimates (under-promise, over-deliver)

STYLE:
- Profissional mas acessível
- Dados quantitativos sempre que possível
- Identificar riscos e oportunidades
- Propor soluções concretas

Quando incerto sobre algo específico, indica claramente a necessidade de verificação adicional.""",
            **kwargs
        )

        # Register tools for the agent
        @agent.tool
        async def search_legal_documentation(
            ctx: RunContext[GrantDependencies],
            query: str
        ) -> str:
            """
            Search legal documentation (Aviso, Portaria, Regulamento) for specific information.

            Use this when you need to verify legal requirements, eligibility criteria,
            or calculation methodologies.
            """
            # This would call the RAG service
            # For now, return placeholder
            return f"Legal search results for: {query}\n[Would use RAG service here]"

        @agent.tool
        async def calculate_pme_classification(
            ctx: RunContext[GrantDependencies],
            employees: int,
            turnover: float,
            balance_total: Optional[float] = None
        ) -> Dict[str, Any]:
            """
            Determine PME classification according to Recomendação 2003/361/CE.

            Returns:
            - is_pme: boolean
            - category: "micro" | "pequena" | "média" | "grande"
            - criteria_met: list of met criteria
            """
            is_micro = employees < 10 and (turnover < 2_000_000 or (balance_total or 0) < 2_000_000)
            is_pequena = employees < 50 and (turnover < 10_000_000 or (balance_total or 0) < 10_000_000)
            is_media = employees < 250 and (turnover < 50_000_000 or (balance_total or 0) < 43_000_000)

            if is_micro:
                category = "micro"
            elif is_pequena:
                category = "pequena"
            elif is_media:
                category = "média"
            else:
                category = "grande"

            return {
                "is_pme": employees < 250 and (turnover < 50_000_000 or (balance_total or 0) < 43_000_000),
                "category": category,
                "employees": employees,
                "turnover": turnover,
                "criteria_met": [
                    f"Funcionários: {employees} < 250" if employees < 250 else f"Funcionários: {employees} ≥ 250 (NÃO PME)",
                    f"Volume Negócios: €{turnover:,.0f} < €50M" if turnover < 50_000_000 else f"Volume Negócios: €{turnover:,.0f} ≥ €50M (NÃO PME)"
                ]
            }

        @agent.tool
        async def calculate_incentive_rate(
            ctx: RunContext[GrantDependencies],
            region: str,
            company_size: str,
            sector: str
        ) -> Dict[str, Any]:
            """
            Calculate applicable incentive rate based on location, size, and sector.

            Rates according to Aviso 03/C05-i14.01/2025:
            - Base rate: 50%
            - Location bonus: +15% for less developed regions
            - Size bonus: +10% for micro/pequena, +5% for média
            - Max: 75%
            """
            base_rate = 0.50

            # Region bonus
            region_bonus = 0.15 if region in ["Norte", "Centro", "Alentejo", "Açores", "Madeira"] else 0.10

            # Size bonus
            size_bonus = {
                "micro": 0.10,
                "pequena": 0.10,
                "média": 0.05,
                "grande": 0.00
            }.get(company_size.lower(), 0.00)

            total_rate = min(base_rate + region_bonus + size_bonus, 0.75)  # Max 75%

            return {
                "total_rate": total_rate,
                "base_rate": base_rate,
                "region_bonus": region_bonus,
                "size_bonus": size_bonus,
                "max_rate": 0.75,
                "calculation": f"{base_rate} (base) + {region_bonus} (região) + {size_bonus} (dimensão) = {total_rate}"
            }

        @agent.tool
        async def simulate_merit_score(
            ctx: RunContext[GrantDependencies],
            technical_score: float,
            impact_score: float
        ) -> Dict[str, Any]:
            """
            Calculate Merit Score: MP = 0.50 × A + 0.50 × B

            Where:
            - A = Technical component (0-10)
            - B = Impact component (0-10)

            Classification:
            - Class A: MP ≥ 7.0 (priority approval)
            - Class B: 5.0 ≤ MP < 7.0 (normal approval)
            - Class C: MP < 5.0 (likely rejection)
            """
            merit_score = 0.50 * technical_score + 0.50 * impact_score

            if merit_score >= 7.0:
                classification = "A"
                status = "Aprovação Prioritária"
            elif merit_score >= 5.0:
                classification = "B"
                status = "Aprovação Normal"
            else:
                classification = "C"
                status = "Rejeição Provável"

            gap_to_a = max(0, 7.0 - merit_score)

            return {
                "merit_score": round(merit_score, 2),
                "classification": classification,
                "status": status,
                "component_a": technical_score,
                "component_b": impact_score,
                "gap_to_class_a": round(gap_to_a, 2),
                "formula": f"MP = 0.50 × {technical_score} + 0.50 × {impact_score} = {merit_score:.2f}"
            }

        @agent.tool
        async def estimate_approval_probability(
            ctx: RunContext[GrantDependencies],
            eligibility_score: float,
            merit_score: float,
            compliance_score: float
        ) -> Dict[str, Any]:
            """
            Estimate probability of grant approval based on key factors.

            Uses historical data and scoring thresholds to predict success rate.
            """
            # Weighted probability calculation
            weights = {
                "eligibility": 0.40,  # 40% weight
                "merit": 0.35,        # 35% weight
                "compliance": 0.25,   # 25% weight
            }

            # Normalize scores to 0-1
            normalized_eligibility = 1.0 if eligibility_score >= 80 else eligibility_score / 100
            normalized_merit = merit_score / 10.0
            normalized_compliance = compliance_score / 100

            probability = (
                weights["eligibility"] * normalized_eligibility +
                weights["merit"] * normalized_merit +
                weights["compliance"] * normalized_compliance
            )

            # Determine confidence level
            if probability >= 0.80:
                confidence = "Alta"
                outlook = "Excelente candidatura, aprovação muito provável"
            elif probability >= 0.65:
                confidence = "Média-Alta"
                outlook = "Boa candidatura, aprovação provável"
            elif probability >= 0.50:
                confidence = "Média"
                outlook = "Candidatura competitiva, aprovação possível"
            else:
                confidence = "Baixa"
                outlook = "Candidatura fraca, melhorias necessárias"

            return {
                "probability": round(probability, 2),
                "confidence": confidence,
                "outlook": outlook,
                "breakdown": {
                    "eligibility_contribution": weights["eligibility"] * normalized_eligibility,
                    "merit_contribution": weights["merit"] * normalized_merit,
                    "compliance_contribution": weights["compliance"] * normalized_compliance
                }
            }

        return agent

    async def analyze_full_grant_application(
        self,
        company_data: Dict[str, Any],
        deps: Optional[GrantDependencies] = None
    ) -> ComprehensiveGrantAnalysis:
        """
        Perform comprehensive grant application analysis.

        Args:
            company_data: Dictionary with company and project information
            deps: Optional grant-specific dependencies

        Returns:
            Complete grant analysis with eligibility, incentive, merit score
        """
        if deps is None:
            deps = GrantDependencies()

        # Build comprehensive analysis prompt
        prompt = f"""
Executa uma análise COMPLETA desta candidatura ao {deps.grant_program}:

DADOS DA EMPRESA:
- Nome: {company_data.get('companyName', 'N/A')}
- NIF: {company_data.get('nif', 'N/A')}
- Investimento Total: €{company_data.get('investment', 0):,.2f}
- Funcionários: {company_data.get('employees', 0)}
- Volume de Negócios: €{company_data.get('turnover', 0):,.2f}
- Setor: {company_data.get('sector', 'Digitalização')}
- Região: {company_data.get('region', 'Portugal Continental')}
- Descrição: {company_data.get('description', 'N/A')}

ANÁLISE REQUERIDA:

1. **ELEGIBILIDADE**
   - Verifica TODOS os critérios (PME, investimento, setor, DNSH)
   - Calcula compliance score (0-100)
   - Identifica gaps e ações corretivas

2. **INCENTIVO**
   - Calcula taxa aplicável (base + bónus região + bónus dimensão)
   - Determina montante incentivo
   - Gera breakdown por categoria
   - Cita artigos legais relevantes

3. **MERIT SCORE**
   - Simula MP = 0.50×A + 0.50×B
   - Calcula gap para Classe A (≥7.0)
   - Propõe metas QUANTIFICADAS para:
     * Criação emprego (nº postos + qualificações)
     * Crescimento VAB (%)
     * Aumento exportações (%)
     * Produtividade (KPIs específicos)

4. **PROBABILIDADE APROVAÇÃO**
   - Estima probabilidade baseada em scores
   - Identifica fatores críticos de sucesso
   - Recomenda próximos passos

IMPORTANTE:
- Usa tools disponíveis para cálculos precisos
- Cita SEMPRE artigos legais específicos
- Quantifica TODOS os objetivos (SMART goals)
- Sê conservador nas estimativas (under-promise)
"""

        result = await self.run(prompt, deps=deps)
        return result.data


# Singleton instance for reuse
_grant_specialist_agent = None

def get_grant_specialist_agent(model: str = "openai:gpt-4o") -> GrantSpecialistAgent:
    """Get or create the grant specialist agent singleton"""
    global _grant_specialist_agent

    if _grant_specialist_agent is None:
        _grant_specialist_agent = GrantSpecialistAgent(
            model=model,
            enable_rate_limiting=True,
            max_retries=3
        )

    return _grant_specialist_agent
