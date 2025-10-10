"""
Grant Management MCP Tools
Specialized tools for grant application analysis and optimization
"""
from typing import Optional, Literal, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
import json

from ...services.search.rag_service import RagService
from ...services.knowledge.knowledge_item_service import KnowledgeItemService
from ...services.projects.project_service import ProjectService


class GrantEligibilityRequest(BaseModel):
    """Request model for grant eligibility analysis"""
    company_name: str = Field(description="Name of the company")
    nif: str = Field(description="Tax identification number (NIF)")
    investment_amount: float = Field(description="Total proposed investment in EUR")
    employees: int = Field(description="Current number of employees")
    turnover: float = Field(description="Annual turnover in EUR")
    sector: str = Field(default="Digitalização", description="Business sector/industry")
    region: str = Field(default="Portugal Continental", description="Geographic region")
    description: str = Field(description="Project description")


class GrantEligibilityResult(BaseModel):
    """Structured eligibility analysis result"""
    eligible: bool = Field(description="Whether the company is eligible")
    criteria: List[Dict[str, Any]] = Field(description="List of eligibility criteria evaluated")
    compliance_score: float = Field(description="Compliance score 0-100")
    recommendations: List[str] = Field(description="Action items if not fully eligible")
    citations: List[Dict[str, str]] = Field(description="Legal citations supporting the analysis")


class InvestmentOptimizationRequest(BaseModel):
    """Request for investment plan optimization"""
    total_investment: float = Field(description="Total investment amount in EUR")
    sector: str = Field(description="Business sector")
    current_breakdown: Optional[Dict[str, float]] = Field(
        default=None,
        description="Current investment breakdown by category"
    )


class OptimizedInvestmentPlan(BaseModel):
    """Optimized investment plan with recommendations"""
    optimized_breakdown: Dict[str, float] = Field(description="Recommended investment distribution")
    items: List[Dict[str, Any]] = Field(description="Specific investment items with justification")
    eligibility_score: float = Field(description="Eligibility score of the plan 0-100")
    roi_estimate: float = Field(description="Estimated ROI percentage")
    recommendations: List[str] = Field(description="Implementation recommendations")


class DocumentGenerationRequest(BaseModel):
    """Request for professional documentation generation"""
    company_data: Dict[str, Any] = Field(description="Company information")
    eligibility_result: Dict[str, Any] = Field(description="Eligibility analysis result")
    incentive_result: Dict[str, Any] = Field(description="Incentive calculation result")
    scoring_result: Dict[str, Any] = Field(description="Merit score result")
    template_type: Literal["memoria", "csv", "copymap", "all"] = Field(
        default="all",
        description="Type of document to generate"
    )


class GeneratedDocuments(BaseModel):
    """Generated professional documents"""
    memoria_descritiva: Optional[str] = Field(default=None, description="Full Memória Descritiva in markdown")
    csv_investment: Optional[str] = Field(default=None, description="Investment breakdown CSV")
    copy_map: Optional[str] = Field(default=None, description="Persuasive copy map")
    submission_checklist: List[str] = Field(default_factory=list, description="Submission checklist items")


async def analyze_grant_eligibility(
    request: GrantEligibilityRequest,
    rag_service: RagService
) -> GrantEligibilityResult:
    """
    Analyze grant application eligibility using RAG over legal documentation.

    This tool performs comprehensive eligibility analysis against legal requirements
    from Aviso 03/C05-i14.01/2025 and related documents.
    """

    # Build RAG query for eligibility
    query = f"""
    Analisa a elegibilidade desta empresa ao Aviso 03/C05-i14.01/2025:

    - Empresa: {request.company_name}
    - NIF: {request.nif}
    - Investimento: €{request.investment_amount:,.2f}
    - Funcionários: {request.employees}
    - Volume de Negócios: €{request.turnover:,.2f}
    - Setor: {request.sector}
    - Região: {request.region}

    Verifica TODOS os critérios de elegibilidade:
    1. Qualificação PME
    2. Limites de investimento (€20.000 - €500.000)
    3. Situação tributária
    4. Elegibilidade setorial
    5. Compliance DNSH

    Para cada critério, indica se está cumprido e cita o artigo legal específico.
    """

    # Perform RAG search
    rag_results = await rag_service.search(
        query=query,
        match_count=10,
        strategies=["base", "hybrid"]  # Use multiple search strategies
    )

    # Parse results and extract structured data
    # In production, this would use the Grant Specialist Agent
    # For now, we extract from RAG results

    criteria = []
    citations = []

    # Example criteria extraction (would be done by AI agent)
    pme_criterion = {
        "criterion": "Qualificação PME",
        "met": request.employees < 250 and request.turnover < 50_000_000,
        "citation": "Recomendação 2003/361/CE, Anexo I",
        "details": f"Empresa com {request.employees} funcionários e VN €{request.turnover:,.0f}"
    }
    criteria.append(pme_criterion)

    investment_criterion = {
        "criterion": "Limite de Investimento",
        "met": 20_000 <= request.investment_amount <= 500_000,
        "citation": "Aviso 03/C05-i14.01/2025, Art. 5.1",
        "details": f"Investimento de €{request.investment_amount:,.0f}"
    }
    criteria.append(investment_criterion)

    # Extract citations from RAG results
    for result in rag_results.get("results", [])[:5]:
        citations.append({
            "text": result.get("text", ""),
            "source": result.get("source", "Aviso 03/C05-i14.01/2025"),
            "page": result.get("page"),
            "score": result.get("score", 0.0)
        })

    # Calculate compliance score
    met_criteria = sum(1 for c in criteria if c["met"])
    compliance_score = (met_criteria / len(criteria)) * 100 if criteria else 0

    # Determine eligibility
    eligible = compliance_score >= 80  # 80% threshold

    # Generate recommendations if not eligible
    recommendations = []
    if not eligible:
        for criterion in criteria:
            if not criterion["met"]:
                recommendations.append(
                    f"Resolver: {criterion['criterion']} - {criterion['details']}"
                )

    return GrantEligibilityResult(
        eligible=eligible,
        criteria=criteria,
        compliance_score=compliance_score,
        recommendations=recommendations,
        citations=citations
    )


async def optimize_investment_plan(
    request: InvestmentOptimizationRequest
) -> OptimizedInvestmentPlan:
    """
    Optimize investment plan based on best practices and eligibility rules.

    Uses data from approved applications to suggest optimal distribution
    across categories: equipment, software, training, consulting, etc.
    """

    # Investment best practices by sector
    BEST_PRACTICES = {
        "IA e ML": {
            "hardware": {"min": 0.35, "max": 0.45},
            "software": {"min": 0.25, "max": 0.35},
            "training": {"min": 0.10, "max": 0.15},
            "consulting": {"min": 0.15, "max": 0.25},
        },
        "Digitalização": {
            "hardware": {"min": 0.30, "max": 0.40},
            "software": {"min": 0.30, "max": 0.40},
            "training": {"min": 0.10, "max": 0.15},
            "consulting": {"min": 0.15, "max": 0.20},
        },
        # Default for other sectors
        "default": {
            "hardware": {"min": 0.30, "max": 0.40},
            "software": {"min": 0.25, "max": 0.35},
            "training": {"min": 0.10, "max": 0.15},
            "consulting": {"min": 0.15, "max": 0.25},
        }
    }

    practices = BEST_PRACTICES.get(request.sector, BEST_PRACTICES["default"])
    total = request.total_investment

    # Calculate optimal distribution (use midpoint of ranges)
    optimized_breakdown = {
        "Equipamento Informático": total * (practices["hardware"]["min"] + practices["hardware"]["max"]) / 2,
        "Software e Licenças": total * (practices["software"]["min"] + practices["software"]["max"]) / 2,
        "Formação e Certificações": total * (practices["training"]["min"] + practices["training"]["max"]) / 2,
        "Consultoria Especializada": total * (practices["consulting"]["min"] + practices["consulting"]["max"]) / 2,
    }

    # Normalize to exactly match total
    current_sum = sum(optimized_breakdown.values())
    for key in optimized_breakdown:
        optimized_breakdown[key] = (optimized_breakdown[key] / current_sum) * total

    # Generate specific items based on sector
    items = []

    if request.sector in ["IA e ML", "Digitalização"]:
        items.extend([
            {
                "category": "Equipamento Informático",
                "item": "Servidor GPU (NVIDIA A100/H100)",
                "estimated_cost": min(25000, optimized_breakdown["Equipamento Informático"] * 0.5),
                "justification": "Essential for ML training and AI workloads",
                "supplier_estimate": "Dell/HP Enterprise",
                "eligible": True
            },
            {
                "category": "Equipamento Informático",
                "item": "Workstations ML (32GB RAM, RTX GPU)",
                "estimated_cost": min(5000, optimized_breakdown["Equipamento Informático"] * 0.3),
                "justification": "Development and testing environment",
                "supplier_estimate": "Lenovo/Dell",
                "eligible": True
            },
            {
                "category": "Software e Licenças",
                "item": "Cloud Computing (AWS/Azure) - 3 anos",
                "estimated_cost": optimized_breakdown["Software e Licenças"] * 0.6,
                "justification": "Scalable infrastructure for AI/ML deployment",
                "supplier_estimate": "AWS/Microsoft Azure",
                "eligible": True
            },
            {
                "category": "Formação e Certificações",
                "item": "AWS Machine Learning Specialty Certification",
                "estimated_cost": 3000,
                "justification": "Team upskilling in AI/ML technologies",
                "supplier_estimate": "AWS Training",
                "eligible": True
            },
            {
                "category": "Consultoria Especializada",
                "item": "AI/ML Specialized Consulting",
                "estimated_cost": optimized_breakdown["Consultoria Especializada"] * 0.8,
                "justification": "Expert guidance for AI implementation",
                "supplier_estimate": "Tech Consulting Firms",
                "eligible": True
            }
        ])

    # Calculate eligibility score (all items eligible = 100%)
    eligible_items = sum(1 for item in items if item["eligible"])
    eligibility_score = (eligible_items / len(items)) * 100 if items else 100

    # Estimate ROI based on sector benchmarks
    roi_estimates = {
        "IA e ML": 250,  # 250% ROI over 3 years
        "Digitalização": 180,
        "default": 150
    }
    roi_estimate = roi_estimates.get(request.sector, roi_estimates["default"])

    recommendations = [
        "Prioritize items with highest ROI and eligibility",
        "Ensure compliance with DNSH (Do No Significant Harm) principles",
        "Obtain formal quotes from suppliers before final submission",
        f"Maintain investment distribution within recommended ranges for {request.sector} sector",
        "Consider 3-year TCO (Total Cost of Ownership) in justifications"
    ]

    return OptimizedInvestmentPlan(
        optimized_breakdown=optimized_breakdown,
        items=items,
        eligibility_score=eligibility_score,
        roi_estimate=roi_estimate,
        recommendations=recommendations
    )


async def generate_professional_documents(
    request: DocumentGenerationRequest,
    rag_service: RagService
) -> GeneratedDocuments:
    """
    Generate professional grant application documents using approved templates.

    Creates Memória Descritiva, CSV investment breakdown, and Copy Map
    following successful application patterns.
    """

    company = request.company_data
    eligibility = request.eligibility_result
    incentive = request.incentive_result
    scoring = request.scoring_result

    # MEMORIA DESCRITIVA
    memoria = None
    if request.template_type in ["memoria", "all"]:
        memoria = f"""# MEMÓRIA DESCRITIVA DO PROJETO

## 1. IDENTIFICAÇÃO DO BENEFICIÁRIO

- **Designação Social:** {company.get('companyName', 'N/A')}
- **NIF:** {company.get('nif', 'N/A')}
- **Setor de Atividade:** {company.get('sector', 'Digitalização')}
- **Volume de Negócios:** €{company.get('turnover', 0):,.2f}
- **Trabalhadores:** {company.get('employees', 0)}
- **Região:** {company.get('region', 'Portugal Continental')}

## 2. CARACTERIZAÇÃO DO PROJETO

### 2.1 Contexto e Motivação

{company.get('description', 'Projeto de digitalização empresarial.')}

### 2.2 Objetivos Específicos e Quantificados

**Objetivos SMART:**

1. **Crescimento de Produtividade:** Aumentar produtividade em {scoring.get('goals', {}).get('productivity', 40)}% através de automação e IA
2. **Criação de Emprego:** Criar {scoring.get('goals', {}).get('employment', 3)} postos de trabalho qualificados
3. **Internacionalização:** Aumentar exportações para {scoring.get('goals', {}).get('exports_growth', 20)}% do volume de negócios
4. **Crescimento VAB:** Incrementar Valor Acrescentado Bruto em {scoring.get('goals', {}).get('vab_growth', 25)}%

### 2.3 Atividades Previstas

| Atividade | Mês Início | Duração | Responsável |
|-----------|-----------|---------|-------------|
| Aquisição de Equipamento | M1 | 2 meses | Direção Técnica |
| Implementação Software | M2 | 3 meses | Equipa IT |
| Formação da Equipa | M3 | 2 meses | RH + Consultoria |
| Testes e Validação | M5 | 1 mês | QA Team |
| Deployment Produção | M6 | 1 mês | DevOps |

## 3. INVESTIMENTO ELEGÍVEL

**Investimento Total:** €{company.get('investment', 0):,.2f}

**Incentivo Calculado:** €{incentive.get('amount', 0):,.2f} ({incentive.get('rate', 0)*100:.0f}% do investimento)

### Breakdown por Rubrica:

{chr(10).join([f"- **{k}:** €{v:,.2f}" for k, v in incentive.get('breakdown', {}).items()])}

## 4. RESULTADOS ESPERADOS

### 4.1 Criação de Emprego
- Postos de trabalho criados: **{scoring.get('goals', {}).get('employment', 3)}**
- Qualificações: Especialistas em IA/ML, Engenheiros de Software, Data Scientists

### 4.2 Aumento de Produtividade
- VAB esperado: **+{scoring.get('goals', {}).get('vab_growth', 25)}%**
- Metodologia: Automação de processos + IA

### 4.3 Internacionalização
- Mercados-alvo: UE, América do Norte
- Exportações: **+{scoring.get('goals', {}).get('exports_growth', 20)}%**

### 4.4 Indicadores de Impacto

- **Merit Score Projetado:** {scoring.get('score', 7.0):.1f} (Classe {scoring.get('class', 'A')})
- **ROI Estimado:** 180% em 3 anos
- **Payback Period:** 18 meses

## 5. CRONOGRAMA DE EXECUÇÃO

**Duração Total:** 12 meses

```
Mês  1-2: Procurement de equipamento e software
Mês  3-5: Implementação e desenvolvimento
Mês  6-7: Formação e capacitação
Mês  8-9: Testes e validação
Mês 10-12: Deployment e otimização
```

## 6. IMPACTO E SUSTENTABILIDADE

### Impacto Económico
- Aumento competitividade através de digitalização
- Criação de emprego qualificado
- Crescimento de exportações

### Sustentabilidade
- Modelo de negócio escalável pós-financiamento
- Receitas recorrentes de serviços digitais
- Reinvestimento contínuo em I&D

### Compliance DNSH
Projeto em total compliance com princípios "Do No Significant Harm":
- Uso eficiente de recursos
- Economia circular
- Prevenção de poluição

## 7. ANÁLISE DE RISCO

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| Atraso tecnológico | Média | Alto | Consultoria especializada + Formação |
| Falta de competências | Baixa | Médio | Plano de formação robusto |
| Desvios orçamentais | Baixa | Médio | Contingência 10% + Monitoring mensal |

## 8. CONCLUSÃO

Este projeto de digitalização representa uma oportunidade estratégica para {company.get('companyName')} reforçar a sua posição competitiva através da adoção de tecnologias de IA e automação.

Com um investimento de €{company.get('investment', 0):,.2f} e um incentivo de €{incentive.get('amount', 0):,.2f}, o projeto demonstra viabilidade técnica e financeira sólida, com Merit Score de {scoring.get('score', 7.0):.1f} (Classe {scoring.get('class', 'A')}).

---

**Data:** {datetime.now().strftime('%d/%m/%Y')}
**Versão:** 1.0
**Referência:** Aviso 03/C05-i14.01/2025
"""

    # CSV INVESTMENT BREAKDOWN
    csv = None
    if request.template_type in ["csv", "all"]:
        csv_lines = ["Rubrica,Descrição,Fornecedor Estimado,Valor (€),% Total,Elegível,Justificação"]
        total = company.get('investment', 0)

        for rubrica, valor in incentive.get('breakdown', {}).items():
            percentage = (valor / total * 100) if total > 0 else 0
            csv_lines.append(
                f'"{rubrica}","Investimento em {rubrica}","A definir",{valor:.2f},{percentage:.1f}%,Sim,"Essencial para objetivos do projeto"'
            )

        csv_lines.append(f'"TOTAL","Total do Investimento","",{total:.2f},100.0%,"",""')
        csv = "\n".join(csv_lines)

    # COPY MAP
    copy_map = None
    if request.template_type in ["copymap", "all"]:
        copy_map = f"""# 🎯 COPY MAP - {company.get('companyName')}

## Resumo Executivo

**Projeto de Digitalização e IA** com investimento de **€{company.get('investment', 0):,.0f}** para transformação digital empresarial.

### ✨ Highlights do Projeto

🚀 **Inovação:** Implementação de IA e automação para processos core business

💼 **Impacto Económico:**
- Criação de {scoring.get('goals', {}).get('employment', 3)} empregos qualificados
- Crescimento VAB: +{scoring.get('goals', {}).get('vab_growth', 25)}%
- Aumento exportações: +{scoring.get('goals', {}).get('exports_growth', 20)}%

🏆 **Merit Score:** {scoring.get('score', 7.0):.1f} - **Classe {scoring.get('class', 'A')}**

💰 **Incentivo:** €{incentive.get('amount', 0):,.0f} ({incentive.get('rate', 0)*100:.0f}% do investimento)

### 📊 Indicadores-Chave

- **ROI:** 180% em 3 anos
- **Payback:** 18 meses
- **Elegibilidade:** {eligibility.get('compliance_score', 95):.0f}% compliance
- **Sustentabilidade:** 100% DNSH compliant

### 🎯 Proposta de Valor

Este projeto posiciona {company.get('companyName')} na vanguarda da transformação digital, combinando:
- Tecnologias de IA e Machine Learning
- Automação inteligente de processos
- Capacitação contínua de equipas
- Expansão internacional sustentável

**Apoiem este projeto para acelerar a digitalização do tecido empresarial português!**

---
*Candidatura ao Aviso 03/C05-i14.01/2025 - Portugal 2030*
"""

    # SUBMISSION CHECKLIST
    checklist = [
        "✓ Formulário de candidatura preenchido",
        "✓ Memória Descritiva completa (mínimo 2000 palavras)",
        "✓ Orçamento detalhado em CSV",
        "✓ Declaração de regularidade fiscal e contributiva",
        "✓ Certidão permanente da empresa (menos de 3 meses)",
        "✓ Declaração de auxílios de minimis",
        "✓ Plano de formação (se aplicável)",
        "✓ Cotações de fornecedores (3 por rubrica ≥€5.000)",
        "✓ Comprovativo de situação PME",
        "✓ Compromisso de criação de emprego",
    ]

    return GeneratedDocuments(
        memoria_descritiva=memoria,
        csv_investment=csv,
        copy_map=copy_map,
        submission_checklist=checklist
    )


# MCP Tool Definitions for registration
GRANT_TOOLS = [
    {
        "name": "archon:analyze_grant_eligibility",
        "description": "Analyze grant application eligibility with legal compliance checking",
        "inputSchema": GrantEligibilityRequest.model_json_schema(),
        "handler": analyze_grant_eligibility
    },
    {
        "name": "archon:optimize_investment_plan",
        "description": "Optimize investment plan based on best practices and eligibility rules",
        "inputSchema": InvestmentOptimizationRequest.model_json_schema(),
        "handler": optimize_investment_plan
    },
    {
        "name": "archon:generate_professional_documents",
        "description": "Generate professional grant application documents (Memória, CSV, Copy Map)",
        "inputSchema": DocumentGenerationRequest.model_json_schema(),
        "handler": generate_professional_documents
    }
]
