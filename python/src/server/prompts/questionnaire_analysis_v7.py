"""
Comprehensive LLM Prompt Template for Archon v7.0 Questionnaire Analysis

This module generates structured prompts for LLM-based analysis of diagnostic
questionnaires, ensuring ALL 31 fields are utilized for personalized IFIC grant
recommendations.

Usage:
    prompt = generate_questionnaire_analysis_prompt(questionnaire_data)
    response = await llm_provider.call(prompt, model="claude-sonnet-4-5")

@author Claude Code (Anthropic)
@version 7.0.0
@license MIT
"""

from typing import Dict, Any
from ..models.questionnaire import DiagnosticQuestionnaire


def generate_questionnaire_analysis_prompt(questionnaire: DiagnosticQuestionnaire) -> str:
    """
    Generate comprehensive LLM analysis prompt using ALL 31 questionnaire fields.

    This prompt is designed for McKinsey-level analysis quality, incorporating:
    - Complete company profile (7 fields)
    - Detailed tech stack ecosystem (12 fields including *_other)
    - Use case prioritization (7 fields)
    - Budget constraints and RH planning (6 fields)
    - Training requirements (5 fields)

    Args:
        questionnaire: Complete diagnostic questionnaire with all 31 fields

    Returns:
        Structured prompt string for LLM analysis
    """

    # Extract all fields for clarity
    company_name = questionnaire.company_name
    nif = questionnaire.nif
    cae_code = questionnaire.cae_code
    num_employees = questionnaire.num_employees
    annual_revenue = questionnaire.annual_revenue
    industry_sector = questionnaire.industry_sector.value
    company_size = questionnaire.company_size.value if questionnaire.company_size else "unknown"

    # Tech Stack (with conditional "other" details)
    tech_stack_summary = []
    tech_stack_summary.append(f"Email: {questionnaire.email_system.value}")
    if questionnaire.email_system_other:
        tech_stack_summary.append(f"  └─ Detalhe: {questionnaire.email_system_other}")

    tech_stack_summary.append(f"Armazenamento: {questionnaire.cloud_storage.value}")
    if questionnaire.cloud_storage_other:
        tech_stack_summary.append(f"  └─ Detalhe: {questionnaire.cloud_storage_other}")

    tech_stack_summary.append(f"Produtividade: {questionnaire.productivity_suite.value}")
    if questionnaire.productivity_suite_other:
        tech_stack_summary.append(f"  └─ Detalhe: {questionnaire.productivity_suite_other}")

    tech_stack_summary.append(f"CRM: {questionnaire.crm_system.value}")
    if questionnaire.crm_system_other:
        tech_stack_summary.append(f"  └─ Detalhe: {questionnaire.crm_system_other}")

    tech_stack_summary.append(f"Gestão Projetos: {questionnaire.project_management.value}")
    if questionnaire.project_management_other:
        tech_stack_summary.append(f"  └─ Detalhe: {questionnaire.project_management_other}")

    tech_stack_summary.append(f"Comunicação: {questionnaire.communication_platform.value}")
    if questionnaire.communication_platform_other:
        tech_stack_summary.append(f"  └─ Detalhe: {questionnaire.communication_platform_other}")

    tech_stack_text = "\n".join(tech_stack_summary)

    # Use Cases
    use_cases_text = ", ".join(questionnaire.use_cases) if questionnaire.use_cases else "Não especificado"
    intensity_level = questionnaire.intensity_level.value
    rgpd_sensitive = "Sim" if questionnaire.rgpd_sensitive_data else "Não"

    # Budget
    desired_investment = questionnaire.desired_investment
    investment_range = questionnaire.investment_range.value if questionnaire.investment_range else "unknown"
    current_tools_paid = "Sim" if questionnaire.current_tools_paid else "Não"
    rh_dedicados_count = questionnaire.rh_dedicados_count
    rh_custo_por_posto = questionnaire.rh_custo_por_posto

    # Training
    training_priority = "Sim" if questionnaire.training_priority else "Não"
    num_employees_training = questionnaire.num_employees_training

    # Build the comprehensive prompt
    prompt = f"""# Análise Diagnóstica de Candidatura IFIC - Vale Inovação
**Cliente:** {company_name} (NIF: {nif})
**Setor:** {industry_sector} (CAE: {cae_code})
**Dimensão:** {num_employees} colaboradores, {company_size.upper()} empresa
**Faturação:** €{annual_revenue:,.0f}/ano

---

## 🎯 MISSÃO
Você é um consultor estratégico sénior especializado em transformação digital para PMEs portuguesas, com expertise em candidaturas ao programa Vale Inovação (Aviso 03/C05-i01 IFIC - Inteligência Artificial).

**Objetivo:** Analisar o questionário diagnóstico completo desta empresa e gerar recomendações personalizadas de classe McKinsey (€1M quality) para maximizar as suas hipóteses de aprovação de incentivo IFIC.

---

## 📊 DADOS COMPLETOS DO QUESTIONÁRIO (31 CAMPOS)

### SECTION A: TECH STACK ECOSYSTEM (12 campos)
```
{tech_stack_text}
```

**Análise Requerida:**
1. Identificar gaps críticos no stack tecnológico atual
2. Avaliar maturidade digital (escala 1-10)
3. Determinar compatibilidade com soluções IA enterprise
4. Recomendar integrações prioritárias (APIs, webhooks, SSO)

---

### SECTION B: PERFIL EMPRESARIAL (7 campos)
- **Nome:** {company_name}
- **NIF:** {nif} (validado com checksum português)
- **CAE:** {cae_code} (setor: {industry_sector})
- **Colaboradores:** {num_employees} (classificação PME: {company_size})
- **Faturação Anual:** €{annual_revenue:,.0f}
- **Setor Atividade:** {industry_sector}

**Análise Requerida:**
1. Avaliar elegibilidade PME (< €50M, < 250 colaboradores)
2. Identificar especificidades setoriais para recomendações
3. Calcular company_size automated: MICRO/SMALL/MEDIUM
4. Verificar histórico creditício potencial (via NIF)

---

### SECTION C: CASOS DE USO & NECESSIDADES (7 campos)
- **Top 3 Prioridades:** {use_cases_text}
- **Intensidade Uso IA:** {intensity_level}
- **Dados Sensíveis RGPD:** {rgpd_sensitive}
- **Caso Uso Principal:** {questionnaire.primary_use_case.value}
- **Casos Secundários:** {', '.join([uc.value for uc in questionnaire.secondary_use_cases])}
- **Desafios Atuais:** {questionnaire.current_pain_points[:200]}...
- **Resultados Esperados:** {questionnaire.expected_outcomes[:200]}...

**Análise Requerida:**
1. Mapear casos de uso para produtos SaaS específicos
2. Avaliar realismo dos resultados esperados (flag over-ambition)
3. Identificar riscos de implementação por intensidade de uso
4. Recomendar compliance RGPD se dados sensíveis = Sim
5. Cruzar use cases com tech stack para recomendar ferramentas complementares

---

### SECTION D: ORÇAMENTO & INVESTIMENTO (6 campos)
- **Investimento Desejado:** €{desired_investment:,.0f} (tier: {investment_range})
- **Orçamento Aprovado:** {questionnaire.has_budget_approved}
- **Data Início:** {questionnaire.project_start_date}
- **Ferramentas IA Pagas Atuais:** {current_tools_paid}
- **RH Dedicados:** {rh_dedicados_count} postos × €{rh_custo_por_posto:,.0f}/posto = €{rh_dedicados_count * rh_custo_por_posto:,.0f}
- **Duração Projeto:** {questionnaire.project_duration_months} meses

**Análise Requerida:**
1. Validar investment range dentro de limites IFIC (€5k-€500k)
2. Distribuir orçamento otimizado:
   - SaaS: 41.6% (€{desired_investment * 0.416:,.0f})
   - Consultoria: 30% (€{desired_investment * 0.30:,.0f})
   - Formação: 8% (€{desired_investment * 0.08:,.0f})
   - RH Dedicados: 17.8% (€{desired_investment * 0.178:,.0f})
   - ROC/Certificação: 2.6% (€{desired_investment * 0.026:,.0f})
3. Calcular incentivo esperado (75% do investimento elegível)
4. Validar RH Dedicados (máximo 2 postos, €80k/posto)
5. Identificar riscos orçamentários (custo mensal vs. annual budget)

---

### SECTION E: FORMAÇÃO & CAPACITAÇÃO (5 campos)
- **Formação é Prioridade:** {training_priority}
- **Colaboradores em Formação:** {num_employees_training}
- **Proficiência Atual:** {questionnaire.team_tech_proficiency}
- **Formato Preferido:** {questionnaire.preferred_training_format}
- **Idioma:** {questionnaire.training_language}

**Análise Requerida:**
1. Calcular orçamento formação: {num_employees_training} × €950 = €{num_employees_training * 950:,.0f}
2. Recomendar parceiro certificado (prioridade: **AiParaTi** - comissão 15%)
3. Sugerir tópicos formação baseados em:
   - Proficiência atual ({questionnaire.team_tech_proficiency})
   - Casos de uso prioritários ({use_cases_text})
   - Intensidade de uso esperada ({intensity_level})
4. Validar % de colaboradores em formação vs. total ({num_employees_training}/{num_employees} = {num_employees_training/num_employees*100:.1f}%)

---

## 📋 DELIVERABLES ESPERADOS

### 1. EXECUTIVE SUMMARY (200 palavras)
- Síntese da situação atual da empresa
- Gap analysis crítico (3-5 gaps principais)
- Recomendação estratégica high-level
- Probabilidade aprovação IFIC (0-100%)

### 2. RECOMENDAÇÕES SaaS PERSONALIZADAS
Para cada caso de uso prioritário ({use_cases_text}):
- **Produto recomendado:** Nome, vendor, pricing
- **Justificação técnica:** Compatibilidade com tech stack atual
- **ROI estimado:** Payback period, KPIs esperados
- **Riscos de implementação:** Timeline, curva de aprendizagem
- **Alternativas:** 2-3 opções backup caso 1ª escolha não disponível

### 3. PLANO DE INVESTIMENTO OTIMIZADO
```
CATEGORIA          | MONTANTE    | % TOTAL | ELEGÍVEL IFIC
-------------------|-------------|---------|---------------
SaaS Licenses      | €X          | 41.6%   | 100%
Consultoria        | €X          | 30.0%   | 100%
Formação           | €X          |  8.0%   | 100%
RH Dedicados       | €X          | 17.8%   | 100%
ROC/Certificação   | €X          |  2.6%   | 100%
-------------------|-------------|---------|---------------
TOTAL              | €{desired_investment:,.0f} | 100%    | €{desired_investment * 0.75:,.0f} (75%)
```

### 4. RECOMENDAÇÃO PARCEIROS
- **Formação:** AiParaTi (comissão 15%, {num_employees_training} colaboradores × €950)
- **Consultoria:** [Analisar perfil e recomendar parceiro certificado]
- **ROC:** [Recomendar ROC com expertise IFIC]

### 5. PONTUAÇÃO MÉRITO TÉCNICO
Calcular MP (Mérito Técnico) baseado em:
- Clareza dos objetivos (20%)
- Adequação do orçamento (20%)
- Capacidade de execução (20%)
- Inovação proposta (20%)
- Sustentabilidade (20%)

**Resultado:** MP = X/10 (threshold mínimo IFIC: 5.0)

### 6. COMPLIANCE & RISK ANALYSIS
- **Elegibilidade PME:** ✅/❌
- **RGPD Compliance:** {rgpd_sensitive} → Recomendações específicas
- **Riscos Técnicos:** Identificar top 3 riscos + mitigação
- **Timeline Feasibility:** {questionnaire.project_duration_months} meses é realista?

### 7. PRÓXIMOS PASSOS (ACTION PLAN)
Roadmap de 5 passos concretos para candidatura IFIC:
1. [Ação 1 - prazo, responsável]
2. [Ação 2 - prazo, responsável]
3. [...]

---

## 🎯 CRITÉRIOS DE QUALIDADE

Sua análise deve ser:
- **Data-Driven:** Referências numéricas precisas (todos os 31 campos)
- **Specific:** Nomes de produtos reais, não genéricos ("Microsoft 365 Copilot", não "ferramenta IA")
- **Actionable:** Cada recomendação com próximos passos claros
- **IFIC-Optimized:** Maximizar elegibilidade e scoring de mérito
- **Realistic:** Flagged over-ambition, prazos realistas
- **Portuguese SME Context:** Considerar realidade portuguesa (maturidade digital, orçamentos, mercado)

---

## 🚀 COMECE A ANÁLISE AGORA

Analise os 31 campos fornecidos acima e gere um relatório completo seguindo a estrutura dos Deliverables.

**IMPORTANTE:**
- Use TODOS os 31 campos na análise (não omita nenhum)
- Cite números específicos do questionário
- Recomende produtos SaaS reais com pricing
- Calcule todos os valores numéricos (budgets, ROI, scores)
- Formate output em markdown limpo e profissional

---

**Output esperado:** Markdown estruturado pronto para HTML rendering (3000-5000 palavras)
"""

    return prompt


def generate_rag_queries_from_questionnaire(questionnaire: DiagnosticQuestionnaire) -> list[str]:
    """
    Generate RAG search queries based on questionnaire data.

    This function extracts key information from the questionnaire to construct
    targeted search queries for retrieving relevant IFIC grant information from
    the knowledge base.

    Args:
        questionnaire: Complete diagnostic questionnaire

    Returns:
        List of 5-10 targeted RAG queries for knowledge retrieval
    """

    queries = []

    # Query 1: Industry-specific IFIC eligibility
    queries.append(
        f"IFIC Vale Inovação elegibilidade setor {questionnaire.industry_sector.value} "
        f"CAE {questionnaire.cae_code} PME {questionnaire.company_size.value if questionnaire.company_size else 'micro'}"
    )

    # Query 2: Budget range and investment limits
    queries.append(
        f"IFIC investimento {questionnaire.investment_range.value if questionnaire.investment_range else '50k-100k'} "
        f"limites máximos despesas elegíveis SaaS consultoria formação"
    )

    # Query 3: Use case specific recommendations
    for use_case in questionnaire.use_cases[:2]:  # Top 2 use cases
        queries.append(
            f"Soluções IA {use_case} para PME {questionnaire.industry_sector.value} "
            f"produtos SaaS recomendados caso de uso"
        )

    # Query 4: Tech stack integration
    queries.append(
        f"Integração IA com {questionnaire.productivity_suite.value} "
        f"{questionnaire.email_system.value} {questionnaire.cloud_storage.value} "
        f"APIs compatibilidade enterprise"
    )

    # Query 5: Training requirements
    if questionnaire.training_priority:
        queries.append(
            f"Formação IA para {questionnaire.num_employees_training} colaboradores "
            f"nível {questionnaire.team_tech_proficiency} parceiros certificados Portugal"
        )

    # Query 6: RGPD compliance (if sensitive data)
    if questionnaire.rgpd_sensitive_data:
        queries.append(
            f"IFIC compliance RGPD dados sensíveis {questionnaire.industry_sector.value} "
            f"requisitos certificação proteção dados"
        )

    # Query 7: RH Dedicados rules (if applicable)
    if questionnaire.rh_dedicados_count > 0:
        queries.append(
            f"IFIC RH dedicados {questionnaire.rh_dedicados_count} postos "
            f"custos elegíveis máximo por posto regras Aviso 03/C05"
        )

    # Query 8: Merit scoring criteria
    queries.append(
        "IFIC mérito técnico pontuação critérios avaliação threshold mínimo aprovação"
    )

    # Query 9: Partner recommendations
    queries.append(
        f"Parceiros formação IA Portugal AiParaTi certificados {questionnaire.preferred_training_format} "
        f"{questionnaire.training_language}"
    )

    # Query 10: Timeline and milestones
    queries.append(
        f"IFIC cronograma projeto {questionnaire.project_duration_months} meses "
        f"milestones deliverables candidatura aprovação"
    )

    return queries


# ═══════════════════════════════════════════════════════════════════
# USAGE EXAMPLE
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Example usage (for testing)
    from ..models.questionnaire import (
        DiagnosticQuestionnaire,
        EmailProvider,
        CloudStorage,
        ProductivitySuite,
        CRMSystem,
        ProjectManagement,
        CommunicationPlatform,
        IndustrySector,
        IntensityLevel,
        UseCase,
    )

    example_questionnaire = DiagnosticQuestionnaire(
        email_system=EmailProvider.GMAIL,
        cloud_storage=CloudStorage.GOOGLE_DRIVE,
        productivity_suite=ProductivitySuite.MICROSOFT_365,
        crm_system=CRMSystem.HUBSPOT,
        project_management=ProjectManagement.TRELLO,
        communication_platform=CommunicationPlatform.MICROSOFT_TEAMS,
        company_name="CodeLab Portugal Lda",
        nif="123456789",
        cae_code="62010",
        num_employees=18,
        annual_revenue=980000,
        industry_sector=IndustrySector.TECHNOLOGY,
        use_cases=["coding", "documentation", "client_chatbot"],
        intensity_level=IntensityLevel.INTENSE,
        rgpd_sensitive_data=False,
        desired_investment=95000,
        current_tools_paid=True,
        training_priority=True,
        num_employees_training=15,
        primary_use_case=UseCase.CODE_ASSISTANCE,
        secondary_use_cases=[UseCase.CONTENT_CREATION, UseCase.CUSTOMER_SERVICE],
        current_pain_points="Produtividade baixa em documentação técnica",
        expected_outcomes="Aumentar velocidade desenvolvimento 40%",
        has_budget_approved=True,
        project_start_date="2025-11-01",
        rh_dedicados_count=1,
        rh_custo_por_posto=60000,
        project_duration_months=12,
        team_tech_proficiency="intermediate",
        preferred_training_format="hybrid",
        training_language="pt",
    )

    # Generate prompt
    prompt = generate_questionnaire_analysis_prompt(example_questionnaire)
    print(prompt)

    # Generate RAG queries
    queries = generate_rag_queries_from_questionnaire(example_questionnaire)
    print("\n\n=== RAG QUERIES ===")
    for i, query in enumerate(queries, 1):
        print(f"{i}. {query}")
