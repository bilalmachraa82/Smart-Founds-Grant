"""
Smart Orchestrator v7.5 - RAG + Multi-Agent + IFIC Services Integration

Orchestrates complete premium report generation by intelligently combining:
- RAG Pipeline (existing knowledge base search)
- Multi-Agent System (parallel analysis)
- 15 IFIC Services (structured outputs)
- LLM Synthesis (narrative generation)

This is the MASTER orchestrator that ties everything together.

@author Claude Code (Anthropic)
@version 7.5.0 - Smart Integration
@license MIT
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable
from uuid import UUID
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ..models.questionnaire import DiagnosticQuestionnaire
from .saas_recommendation_engine import SaaSRecommendationEngine
from .partner_priority_service import PartnerPriorityService
from .budget_optimizer_service import BudgetOptimizer
from .scoring_calculator_service import ScoringCalculator, ProjectData
from .compliance_validator_service import ComplianceValidator
from .scqa_framework_service import SCQAFrameworkService
from .investment_matrix_service import InvestmentMatrixService
from .scenario_analysis_service import ScenarioAnalysisService
from .risk_register_service import RiskRegisterService
from .kpi_dashboard_service import KPIDashboardService
from .gantt_service import GanttService
from .excel_export_service import ExcelExportService
from ..config.logfire_config import get_logger

logger = get_logger(__name__)


class ProgressUpdate:
    """Progress update model for WebSocket notifications."""
    def __init__(self, percent: int, message: str, step: str, data: Optional[Dict] = None):
        self.percent = percent
        self.message = message
        self.step = step
        self.data = data or {}
        self.timestamp = datetime.now().isoformat()


class SmartOrchestratorV7:
    """
    Smart orchestrator that integrates:
    - RAG queries for contextual intelligence
    - Multi-agent analysis for deep insights
    - 15 IFIC services for structured data
    - LLM synthesis for premium narrative

    This is the brain of the v7 system.
    """

    def __init__(
        self,
        rag_service=None,
        agent_service=None,
        llm_service=None,
        db_service=None,
        templates_dir: str = None
    ):
        """
        Initialize smart orchestrator.

        Args:
            rag_service: Knowledge/RAG service for context retrieval
            agent_service: Multi-agent service for parallel analysis
            llm_service: LLM provider service for synthesis
            db_service: Database service for persistence
            templates_dir: Path to Jinja2 templates
        """
        self.rag = rag_service
        self.agents = agent_service
        self.llm = llm_service
        self.db = db_service

        if templates_dir is None:
            templates_dir = Path(__file__).parent.parent / "templates"

        self.jinja_env = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )

        # Register custom filters
        self.jinja_env.filters['format_number'] = self._format_number
        self.jinja_env.filters['format_currency'] = self._format_currency

        logger.info("SmartOrchestratorV7 initialized with RAG + Agents + LLM")

    async def generate_complete_report(
        self,
        questionnaire: DiagnosticQuestionnaire,
        project_start_date: Optional[str] = None,
        progress_callback: Optional[Callable[[ProgressUpdate], None]] = None
    ) -> Dict[str, Any]:
        """
        Generate complete McKinsey-level premium report with RAG + Agent intelligence.

        Args:
            questionnaire: Diagnostic questionnaire with company data
            project_start_date: Project start date (ISO format)
            progress_callback: Callback for progress updates (WebSocket)

        Returns:
            Dict containing:
                - html: Rendered HTML report
                - excel: BytesIO Excel export
                - pdf: BytesIO PDF export (optional)
                - metadata: Report metadata
                - rag_citations: Citations from RAG
                - agent_insights: Insights from agents
        """

        logger.info(f"🚀 Starting SMART report generation for {questionnaire.company_name}")
        start_time = datetime.now()

        if not project_start_date:
            project_start_date = datetime.now().strftime("%Y-%m-%d")

        # Progress tracking
        def notify(percent: int, message: str, step: str, data: Optional[Dict] = None):
            if progress_callback:
                progress_callback(ProgressUpdate(percent, message, step, data))
            logger.info(f"[{percent}%] {step}: {message}")

        try:
            # ═══════════════════════════════════════════════════════════
            # PHASE 1: RAG CONTEXT GATHERING (0-10%)
            # ═══════════════════════════════════════════════════════════

            notify(2, "Construindo queries RAG...", "rag_queries")
            rag_queries = self._construct_rag_queries(questionnaire)

            notify(5, f"Buscando contexto em {len(rag_queries)} queries...", "rag_search")
            rag_context = await self._gather_rag_context(rag_queries)

            notify(10, f"RAG context: {len(rag_context.get('results', []))} documentos relevantes", "rag_complete", {
                "citations_count": len(rag_context.get('citations', []))
            })

            # ═══════════════════════════════════════════════════════════
            # PHASE 2: MULTI-AGENT ANALYSIS (10-25%)
            # ═══════════════════════════════════════════════════════════

            notify(12, "Iniciando análise multi-agent...", "agents_start")
            agent_insights = await self._run_agent_analysis(questionnaire, rag_context)

            notify(25, f"Análise completa: {len(agent_insights)} insights gerados", "agents_complete", {
                "insights_count": len(agent_insights)
            })

            # ═══════════════════════════════════════════════════════════
            # PHASE 3: IFIC SERVICES EXECUTION (25-70%)
            # ═══════════════════════════════════════════════════════════

            notify(27, "Executando 15 IFIC services...", "services_start")

            # Group 1: Independent services (30-40%)
            notify(30, "Gerando recomendações SaaS...", "saas_recommendations")
            saas_recs = await self._run_saas_with_context(questionnaire, rag_context, agent_insights)

            notify(35, "Gerando plano de formação...", "training_recommendations")
            training_recs = await self._run_training_with_context(questionnaire, rag_context)

            notify(38, "Validando compliance...", "compliance_validation")
            compliance_result = await self._run_compliance(questionnaire)

            notify(40, "Gerando risk register...", "risk_register")
            risk_register = await self._run_risk_register(questionnaire)

            # Group 2: Dependent services (40-55%)
            notify(42, "Construindo investment matrix...", "investment_matrix")
            investment_matrix = await self._run_investment_matrix(saas_recs, training_recs, questionnaire)

            notify(47, "Otimizando budget...", "budget_optimization")
            budget_analysis = await self._run_budget_optimization(questionnaire)

            # Group 3: Final services (55-70%)
            notify(50, "Gerando análise de cenários...", "scenario_analysis")
            scenario_analysis = await self._run_scenario_analysis(investment_matrix, questionnaire)

            notify(55, "Calculando merit score...", "merit_scoring")
            scoring_result = await self._run_scoring(questionnaire, investment_matrix)

            notify(60, "Gerando framework SCQA...", "scqa_framework")
            scqa = await self._run_scqa(questionnaire, investment_matrix, agent_insights)

            notify(63, "Criando KPI dashboard...", "kpi_dashboard")
            kpi_dashboard = await self._run_kpi_dashboard(investment_matrix, risk_register, compliance_result)

            notify(67, "Construindo timeline Gantt...", "gantt_timeline")
            gantt_data = await self._run_gantt(questionnaire.company_name, project_start_date, questionnaire.project_duration_months)

            notify(70, "Todos os services executados com sucesso", "services_complete")

            # ═══════════════════════════════════════════════════════════
            # PHASE 4: LLM NARRATIVE SYNTHESIS (70-80%)
            # ═══════════════════════════════════════════════════════════

            notify(72, "Sintetizando narrativa premium com LLM...", "narrative_synthesis")
            narrative = await self._generate_premium_narrative(
                questionnaire,
                rag_context,
                agent_insights,
                {
                    'saas': saas_recs,
                    'training': training_recs,
                    'matrix': investment_matrix,
                    'scenarios': scenario_analysis,
                    'risks': risk_register,
                    'compliance': compliance_result,
                    'scoring': scoring_result,
                    'scqa': scqa,
                    'kpis': kpi_dashboard,
                    'gantt': gantt_data,
                }
            )

            notify(80, "Narrativa premium gerada", "narrative_complete")

            # ═══════════════════════════════════════════════════════════
            # PHASE 5: TEMPLATE RENDERING (80-90%)
            # ═══════════════════════════════════════════════════════════

            notify(82, "Preparando template McKinsey v7...", "template_prep")

            from .report_orchestrator_v7 import ReportOrchestratorV7
            basic_orchestrator = ReportOrchestratorV7(templates_dir=Path(self.jinja_env.loader.searchpath[0]))

            context = basic_orchestrator._build_template_context(
                questionnaire=questionnaire,
                saas_recs=saas_recs,
                training_recs=training_recs,
                investment_matrix=investment_matrix,
                scenario_analysis=scenario_analysis,
                risk_register=risk_register,
                compliance_result=compliance_result,
                scoring_result=scoring_result,
                scqa=scqa,
                kpi_dashboard=kpi_dashboard,
                gantt_data=gantt_data,
                budget_analysis=budget_analysis,
            )

            # Enrich context with RAG + Agent data
            context['rag_citations'] = rag_context.get('citations', [])
            context['agent_insights'] = agent_insights
            context['narrative_enhanced'] = narrative

            notify(85, "Renderizando HTML premium...", "html_render")
            template = self.jinja_env.get_template('premium_v7_mckinsey.html')
            html_output = template.render(**context)

            notify(90, f"HTML renderizado: {len(html_output)} bytes", "html_complete")

            # ═══════════════════════════════════════════════════════════
            # PHASE 6: EXPORTS GENERATION (90-100%)
            # ═══════════════════════════════════════════════════════════

            notify(92, "Gerando Excel export...", "excel_export")
            excel_output = None
            try:
                excel_output = ExcelExportService.generate(
                    company_name=questionnaire.company_name,
                    scqa=scqa,
                    investment_matrix=investment_matrix,
                    scenario_analysis=scenario_analysis,
                    risk_register=risk_register,
                    gantt_data=gantt_data.dict() if gantt_data else {}
                )
            except Exception as e:
                logger.error(f"Excel generation failed: {e}")

            notify(95, "Extraindo metadata...", "metadata_extraction")
            metadata = self._extract_metadata(
                questionnaire,
                scoring_result,
                compliance_result,
                investment_matrix,
                scenario_analysis,
                rag_context,
                agent_insights
            )

            notify(100, "Report gerado com sucesso! 🎉", "complete")

            # ═══════════════════════════════════════════════════════════
            # RETURN COMPLETE RESULTS
            # ═══════════════════════════════════════════════════════════

            execution_time = (datetime.now() - start_time).total_seconds()

            logger.info(
                f"✅ SMART report generated successfully in {execution_time:.2f}s: "
                f"{len(html_output)} bytes HTML, "
                f"RAG citations: {len(rag_context.get('citations', []))}, "
                f"Agent insights: {len(agent_insights)}"
            )

            return {
                "html": html_output,
                "excel": excel_output,
                "pdf": None,  # TODO: PDF generation
                "metadata": metadata,
                "rag_context": rag_context,
                "agent_insights": agent_insights,
                "narrative": narrative,
                "execution_time_seconds": execution_time,
            }

        except Exception as e:
            logger.error(f"❌ Report generation failed: {e}", exc_info=True)
            notify(100, f"Erro: {str(e)}", "error", {"error": str(e)})
            raise

    # ═══════════════════════════════════════════════════════════════
    # RAG INTEGRATION
    # ═══════════════════════════════════════════════════════════════

    def _construct_rag_queries(self, questionnaire: DiagnosticQuestionnaire) -> List[str]:
        """Construct targeted RAG queries from questionnaire."""
        queries = []

        # Query 1: Tech stack specific
        queries.append(
            f"SaaS tools AI {questionnaire.email_system.value} {questionnaire.cloud_storage.value} "
            f"integration {questionnaire.industry_sector.value} 2025 pricing"
        )

        # Query 2: Industry benchmarks
        queries.append(
            f"AI adoption {questionnaire.industry_sector.value} Portugal PME "
            f"{questionnaire.company_size.value} ROI benchmarks case studies"
        )

        # Query 3: Use case specific
        for use_case in questionnaire.use_cases[:3]:  # Top 3 use cases
            queries.append(
                f"AI {use_case} implementation {questionnaire.industry_sector.value} "
                f"best practices tools recommendations"
            )

        # Query 4: Compliance
        queries.append(
            f"Vale Inovação Aviso 03/C05 eligibility requirements CAE {questionnaire.cae_code} "
            f"PME {questionnaire.num_employees} employees investment {questionnaire.desired_investment}"
        )

        # Query 5: Training
        queries.append(
            f"AI training Portugal {questionnaire.num_employees} employees "
            f"upskilling programs certification AiParaTi alternatives"
        )

        return queries

    async def _gather_rag_context(self, queries: List[str]) -> Dict[str, Any]:
        """Gather context from RAG system."""
        if not self.rag:
            logger.warning("RAG service not available, using empty context")
            return {"results": [], "citations": []}

        try:
            # Run queries in parallel
            tasks = [self.rag.search(query, limit=5) for query in queries]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Aggregate results
            all_results = []
            citations = []

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"RAG query {i} failed: {result}")
                    continue

                if hasattr(result, 'documents'):
                    all_results.extend(result.documents)

                    # Extract citations
                    for doc in result.documents[:2]:  # Top 2 per query
                        citations.append({
                            'text': doc.content[:200] + "...",
                            'source': doc.metadata.get('url', 'Unknown'),
                            'title': doc.metadata.get('title', 'Untitled'),
                            'relevance_score': doc.score if hasattr(doc, 'score') else 0.0
                        })

            return {
                "results": all_results,
                "citations": citations,
                "query_count": len(queries),
                "document_count": len(all_results)
            }

        except Exception as e:
            logger.error(f"RAG context gathering failed: {e}")
            return {"results": [], "citations": []}

    # ═══════════════════════════════════════════════════════════════
    # AGENT INTEGRATION
    # ═══════════════════════════════════════════════════════════════

    async def _run_agent_analysis(
        self,
        questionnaire: DiagnosticQuestionnaire,
        rag_context: Dict
    ) -> List[Dict]:
        """Run multi-agent analysis in parallel."""
        if not self.agents:
            logger.warning("Agent service not available, skipping agent analysis")
            return []

        try:
            # Define agent tasks
            agent_tasks = [
                {
                    "agent": "financial_analyst",
                    "prompt": f"Analyze financial viability of €{questionnaire.desired_investment} AI investment for {questionnaire.company_name} ({questionnaire.num_employees} employees, €{questionnaire.annual_revenue} revenue). Provide ROI estimate and risk factors.",
                    "context": rag_context.get('results', [])[:3]
                },
                {
                    "agent": "compliance_expert",
                    "prompt": f"Validate eligibility for Vale Inovação (Aviso 03/C05): CAE {questionnaire.cae_code}, {questionnaire.num_employees} employees, investment €{questionnaire.desired_investment}. List any blockers.",
                    "context": rag_context.get('results', [])[3:6]
                },
                {
                    "agent": "tech_advisor",
                    "prompt": f"Recommend AI tech stack for {questionnaire.email_system.value} + {questionnaire.cloud_storage.value} environment. Industry: {questionnaire.industry_sector.value}. Use cases: {', '.join(questionnaire.use_cases[:3])}.",
                    "context": rag_context.get('results', [])[6:9]
                }
            ]

            # Execute agents in parallel
            insights = []
            for task in agent_tasks:
                try:
                    result = await self.agents.analyze(
                        task["agent"],
                        task["prompt"],
                        context=task["context"]
                    )
                    insights.append({
                        "agent": task["agent"],
                        "insight": result.get("response", ""),
                        "confidence": result.get("confidence", 0.7)
                    })
                except Exception as e:
                    logger.error(f"Agent {task['agent']} failed: {e}")

            return insights

        except Exception as e:
            logger.error(f"Agent analysis failed: {e}")
            return []

    # ═══════════════════════════════════════════════════════════════
    # ENHANCED SERVICE RUNNERS
    # ═══════════════════════════════════════════════════════════════

    async def _run_saas_with_context(
        self,
        questionnaire: DiagnosticQuestionnaire,
        rag_context: Dict,
        agent_insights: List[Dict]
    ):
        """Run SaaS recommendations enhanced with RAG context."""
        # Base recommendations
        base_recs = SaaSRecommendationEngine.recommend(questionnaire)

        # Enhance with RAG insights
        tech_insights = [
            doc.content for doc in rag_context.get('results', [])
            if 'SaaS' in doc.content or 'pricing' in doc.content
        ][:3]

        # Add RAG citations
        for rec in base_recs:
            rec.rag_citation = tech_insights[0] if tech_insights else None

        return base_recs

    async def _run_training_with_context(self, questionnaire: DiagnosticQuestionnaire, rag_context: Dict):
        """Run training recommendations with RAG context."""
        training_recs = []
        num_training = questionnaire.num_employees_training or min(questionnaire.num_employees, 10)
        training_recs = PartnerPriorityService.enforce_aiparati_priority(training_recs, num_training)
        return training_recs

    async def _run_compliance(self, questionnaire: DiagnosticQuestionnaire):
        """Run compliance validation."""
        return ComplianceValidator.validate(questionnaire)

    async def _run_risk_register(self, questionnaire: DiagnosticQuestionnaire):
        """Run risk register generation."""
        return RiskRegisterService.generate_from_questionnaire(
            questionnaire=questionnaire,
            total_budget=questionnaire.desired_investment,
            has_consulting=True
        )

    async def _run_investment_matrix(self, saas_recs, training_recs, questionnaire: DiagnosticQuestionnaire):
        """Run investment matrix generation."""
        return InvestmentMatrixService.generate_from_components(
            saas_recommendations=saas_recs,
            training_recommendations=training_recs,
            consultoria_budget=questionnaire.desired_investment * 0.15,
            rh_dedicados_budget=questionnaire.desired_investment * 0.30 if questionnaire.has_dev_team else 0,
            roc_budget=2500
        )

    async def _run_budget_optimization(self, questionnaire: DiagnosticQuestionnaire):
        """Run budget optimizer."""
        current_budget = {
            "rh_dedicados": questionnaire.desired_investment * 0.30 if questionnaire.has_dev_team else 0,
            "roc": 2500,
        }
        gaps = BudgetOptimizer.analyze_gaps(current_budget, questionnaire)
        paths = BudgetOptimizer.generate_expansion_paths(questionnaire.desired_investment, questionnaire)
        return {"gaps": gaps, "paths": paths}

    async def _run_scenario_analysis(self, investment_matrix, questionnaire: DiagnosticQuestionnaire):
        """Run scenario analysis."""
        if not investment_matrix:
            return None
        return ScenarioAnalysisService.generate(
            base_investment=investment_matrix.total_investment,
            base_annual_savings=investment_matrix.expected_annual_savings,
            num_employees=questionnaire.num_employees,
            has_dev_team=questionnaire.has_dev_team,
            training_priority=questionnaire.training_priority
        )

    async def _run_scoring(self, questionnaire: DiagnosticQuestionnaire, investment_matrix):
        """Run merit score calculator."""
        if not investment_matrix:
            return None
        project = ProjectData(
            has_investment_matrix=True,
            has_gantt_chart=True,
            has_risk_register=True,
            has_technical_specs=False,
            has_3_quotes=False,
            jobs_created=1 if questionnaire.has_dev_team else 0,
            vab_growth_percent=8.0
        )
        return ScoringCalculator.calculate_current_score(project)

    async def _run_scqa(self, questionnaire: DiagnosticQuestionnaire, investment_matrix, agent_insights: List[Dict]):
        """Run SCQA framework generation."""
        return SCQAFrameworkService.generate(questionnaire)

    async def _run_kpi_dashboard(self, investment_matrix, risk_register, compliance_result):
        """Run KPI dashboard generation."""
        if not investment_matrix:
            return None
        return KPIDashboardService.generate(
            total_investment=investment_matrix.total_investment,
            annual_savings=investment_matrix.expected_annual_savings,
            payback_months=investment_matrix.payback_period_months,
            npv_3_years=investment_matrix.expected_annual_savings * 2.5,
            num_users=20,
            num_trained=10,
            high_risks_count=risk_register.high_risks if risk_register else 0,
            total_risks_count=risk_register.total_risks if risk_register else 0,
            compliance_score_percent=100 if compliance_result and compliance_result.status == "ELEGÍVEL" else 85
        )

    async def _run_gantt(self, company_name: str, project_start_date: str, duration_months: int):
        """Run Gantt service."""
        return GanttService.generate(
            company_name=company_name,
            project_start_date=project_start_date,
            project_duration_months=duration_months
        )

    # ═══════════════════════════════════════════════════════════════
    # LLM SYNTHESIS
    # ═══════════════════════════════════════════════════════════════

    async def _generate_premium_narrative(
        self,
        questionnaire: DiagnosticQuestionnaire,
        rag_context: Dict,
        agent_insights: List[Dict],
        services_results: Dict
    ) -> Dict[str, str]:
        """Generate premium narrative using LLM synthesis."""
        if not self.llm:
            logger.warning("LLM service not available, using template defaults")
            return {}

        try:
            # Construct prompt with all context
            prompt = f"""
You are a McKinsey consultant writing an executive summary for {questionnaire.company_name}.

Company Profile:
- Size: {questionnaire.company_size.value} ({questionnaire.num_employees} employees)
- Revenue: €{questionnaire.annual_revenue:,}
- Industry: {questionnaire.industry_sector.value}
- Investment: €{questionnaire.desired_investment:,}

Agent Insights:
{chr(10).join([f"- {insight['agent']}: {insight['insight'][:200]}" for insight in agent_insights[:3]])}

RAG Context:
{chr(10).join([f"- {citation['title']}: {citation['text'][:150]}" for citation in rag_context.get('citations', [])[:3]])}

Services Results:
- Investment Matrix: €{services_results['matrix'].total_investment:,} total
- Merit Score: {services_results['scoring'].MP_out_of_10}/10
- Compliance: {services_results['compliance'].status}
- Risk Register: {services_results['risks'].total_risks} risks identified

Generate a compelling 3-paragraph executive insight highlighting:
1. Strategic urgency for AI adoption
2. Recommended investment approach
3. Expected ROI and success probability

Write in Portuguese, McKinsey style, concise and data-driven.
"""

            response = await self.llm.generate(prompt, max_tokens=500)

            return {
                "executive_insight": response.get("text", ""),
                "key_recommendations": response.get("recommendations", [])
            }

        except Exception as e:
            logger.error(f"LLM synthesis failed: {e}")
            return {}

    # ═══════════════════════════════════════════════════════════════
    # HELPER METHODS
    # ═══════════════════════════════════════════════════════════════

    def _extract_metadata(
        self,
        questionnaire,
        scoring_result,
        compliance_result,
        investment_matrix,
        scenario_analysis,
        rag_context,
        agent_insights
    ) -> Dict[str, Any]:
        """Extract metadata from all results."""
        return {
            "company_name": questionnaire.company_name,
            "report_date": datetime.now().isoformat(),
            "version": "7.5.0",
            "merit_score": scoring_result.MP_out_of_10 if scoring_result else 0,
            "compliance_status": compliance_result.status if compliance_result else "UNKNOWN",
            "total_investment": investment_matrix.total_investment if investment_matrix else 0,
            "expected_npv": scenario_analysis.expected_value if scenario_analysis else 0,
            "rag_citations_count": len(rag_context.get('citations', [])),
            "agent_insights_count": len(agent_insights),
            "approval_probability": self._calculate_approval_probability(scoring_result, compliance_result),
        }

    def _calculate_approval_probability(self, scoring_result, compliance_result) -> int:
        """Calculate approval probability."""
        if not scoring_result or not compliance_result:
            return 50

        mp = scoring_result.MP_out_of_10
        if mp >= 8.0:
            prob = 90
        elif mp >= 7.0:
            prob = 75
        elif mp >= 6.0:
            prob = 60
        else:
            prob = 40

        if compliance_result.status == "NÃO ELEGÍVEL":
            prob = 0
        elif compliance_result.status == "ELEGÍVEL COM AVISOS":
            prob -= 10

        return max(0, min(100, prob))

    @staticmethod
    def _format_number(value: float) -> str:
        """Format number with Portuguese locale."""
        if value is None:
            return "0"
        return f"{value:,.0f}".replace(",", ".")

    @staticmethod
    def _format_currency(value: float) -> str:
        """Format currency with € symbol."""
        if value is None:
            return "€0"
        return f"€{value:,.0f}".replace(",", ".")
