"""
Gantt Service

Generates interactive Gantt chart for project timeline with ApexCharts integration.
Implements IFIC best practice: detailed timeline visualization with dependencies and milestones.

Gantt Structure:
    - 5 workstreams (SaaS Rollout, Training, Integration, RH Hiring, Compliance)
    - 20+ milestones with start/end dates
    - Dependencies tracking
    - Critical path highlighting
    - Progress indicators

Uses ApexCharts Timeline for visualization:
    - Interactive hover tooltips
    - Color-coded by workstream
    - Milestone markers
    - Today line indicator

Example:
    gantt_data = GanttService.generate(
        project_start_date="2025-01-15",
        project_duration_months=12
    )
    html = GanttService.render_to_html(gantt_data)
"""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from enum import Enum

from ..config.logfire_config import get_logger

logger = get_logger(__name__)


# ===== MODELS =====

class WorkstreamType(str, Enum):
    """Workstream types"""
    SAAS_ROLLOUT = "saas_rollout"
    TRAINING = "training"
    INTEGRATION = "integration"
    RH_HIRING = "rh_hiring"
    COMPLIANCE = "compliance"


class MilestoneStatus(str, Enum):
    """Milestone status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DELAYED = "delayed"


class Milestone(BaseModel):
    """Single milestone/task"""

    milestone_id: str = Field(..., description="Unique milestone ID (M001, M002, etc.)")
    workstream: WorkstreamType
    title: str = Field(..., description="Milestone title")
    description: str = Field(..., description="Detailed description")

    # Dates
    start_date: datetime = Field(..., description="Start date")
    end_date: datetime = Field(..., description="End date")
    duration_days: int = Field(..., ge=1, description="Duration in days")

    # Ownership
    owner: str = Field(..., description="Person responsible")
    status: MilestoneStatus = Field(default=MilestoneStatus.NOT_STARTED)

    # Dependencies
    depends_on: List[str] = Field(default_factory=list, description="List of milestone_ids this depends on")
    is_critical_path: bool = Field(default=False, description="Is this on the critical path?")

    # Progress
    progress_percent: float = Field(default=0, ge=0, le=100, description="Completion %")


class GanttData(BaseModel):
    """Complete Gantt chart data"""

    project_name: str
    project_start_date: datetime
    project_end_date: datetime
    total_duration_days: int

    # Milestones grouped by workstream
    milestones: List[Milestone]

    # Summary by workstream
    workstream_summary: Dict[WorkstreamType, Dict] = Field(
        default_factory=dict,
        description="Summary stats per workstream"
    )

    # Critical path
    critical_path_milestones: List[str] = Field(default_factory=list)


# ===== GANTT SERVICE =====

class GanttService:
    """
    Generate Gantt chart data.

    Process:
        1. Define project start date and duration
        2. Create 5 workstreams
        3. Add 20+ milestones with dates, dependencies
        4. Calculate critical path
        5. Render as ApexCharts timeline HTML
    """

    # Workstream colors (brand colors)
    WORKSTREAM_COLORS = {
        WorkstreamType.SAAS_ROLLOUT: "#0066CC",  # Blue
        WorkstreamType.TRAINING: "#10B981",      # Green
        WorkstreamType.INTEGRATION: "#F59E0B",   # Orange
        WorkstreamType.RH_HIRING: "#8B5CF6",     # Purple
        WorkstreamType.COMPLIANCE: "#EF4444"     # Red
    }

    @staticmethod
    def generate(
        company_name: str,
        project_start_date: str,  # ISO format: "2025-01-15"
        project_duration_months: int = 12
    ) -> GanttData:
        """
        Generate Gantt chart with 5 workstreams and 20+ milestones.

        Args:
            company_name: Company name
            project_start_date: Project start date (ISO format)
            project_duration_months: Total project duration (months)

        Returns:
            GanttData with milestones and dependencies
        """

        start_date = datetime.fromisoformat(project_start_date)
        end_date = start_date + timedelta(days=project_duration_months * 30)
        total_duration_days = (end_date - start_date).days

        logger.info(
            f"Generating Gantt chart for {company_name}: "
            f"{start_date.date()} → {end_date.date()} ({total_duration_days} days)"
        )

        milestones = []

        # ===== WORKSTREAM 1: SAAS ROLLOUT (Months 1-3) =====

        # M001: SaaS Vendor Selection
        m001_start = start_date
        m001_end = m001_start + timedelta(days=14)
        milestones.append(Milestone(
            milestone_id="M001",
            workstream=WorkstreamType.SAAS_ROLLOUT,
            title="SaaS Vendor Selection",
            description="Avaliar e selecionar fornecedores SaaS (Gemini, ChatGPT, etc.)",
            start_date=m001_start,
            end_date=m001_end,
            duration_days=14,
            owner="CTO",
            status=MilestoneStatus.IN_PROGRESS,
            is_critical_path=True,
            progress_percent=60
        ))

        # M002: Contract Negotiation
        m002_start = m001_end
        m002_end = m002_start + timedelta(days=7)
        milestones.append(Milestone(
            milestone_id="M002",
            workstream=WorkstreamType.SAAS_ROLLOUT,
            title="Contract Negotiation",
            description="Negociar contratos SaaS (pricing, SLAs, data residency)",
            start_date=m002_start,
            end_date=m002_end,
            duration_days=7,
            owner="CFO",
            depends_on=["M001"],
            is_critical_path=True,
            progress_percent=0
        ))

        # M003: SaaS Account Setup
        m003_start = m002_end
        m003_end = m003_start + timedelta(days=3)
        milestones.append(Milestone(
            milestone_id="M003",
            workstream=WorkstreamType.SAAS_ROLLOUT,
            title="SaaS Account Setup",
            description="Configurar contas empresariais (SSO, RBAC, billing)",
            start_date=m003_start,
            end_date=m003_end,
            duration_days=3,
            owner="IT Admin",
            depends_on=["M002"],
            is_critical_path=True,
            progress_percent=0
        ))

        # M004: Pilot Rollout (10 users)
        m004_start = m003_end
        m004_end = m004_start + timedelta(days=14)
        milestones.append(Milestone(
            milestone_id="M004",
            workstream=WorkstreamType.SAAS_ROLLOUT,
            title="Pilot Rollout (10 users)",
            description="Piloto com 10 early adopters (feedback collection)",
            start_date=m004_start,
            end_date=m004_end,
            duration_days=14,
            owner="Project Manager",
            depends_on=["M003"],
            is_critical_path=True,
            progress_percent=0
        ))

        # M005: Full Rollout (all users)
        m005_start = m004_end
        m005_end = m005_start + timedelta(days=21)
        milestones.append(Milestone(
            milestone_id="M005",
            workstream=WorkstreamType.SAAS_ROLLOUT,
            title="Full Rollout (all users)",
            description="Rollout completo para todos colaboradores",
            start_date=m005_start,
            end_date=m005_end,
            duration_days=21,
            owner="IT Admin",
            depends_on=["M004"],
            is_critical_path=True,
            progress_percent=0
        ))

        # ===== WORKSTREAM 2: TRAINING (Months 2-6) =====

        # M006: Training Content Development
        m006_start = start_date + timedelta(days=30)
        m006_end = m006_start + timedelta(days=21)
        milestones.append(Milestone(
            milestone_id="M006",
            workstream=WorkstreamType.TRAINING,
            title="Training Content Development",
            description="Desenvolver conteúdo formação customizado (casos uso empresa)",
            start_date=m006_start,
            end_date=m006_end,
            duration_days=21,
            owner="Training Manager",
            depends_on=[],
            progress_percent=0
        ))

        # M007: AiParaTi Training Module 1 (16h)
        m007_start = m006_end
        m007_end = m007_start + timedelta(days=14)
        milestones.append(Milestone(
            milestone_id="M007",
            workstream=WorkstreamType.TRAINING,
            title="AiParaTi Module 1 (16h)",
            description="Módulo 1: Fundamentos IA (16h presencial)",
            start_date=m007_start,
            end_date=m007_end,
            duration_days=14,
            owner="AiParaTi Trainer",
            depends_on=["M006"],
            is_critical_path=True,
            progress_percent=0
        ))

        # M008: AiParaTi Training Module 2-5 (48h)
        m008_start = m007_end
        m008_end = m008_start + timedelta(days=60)
        milestones.append(Milestone(
            milestone_id="M008",
            workstream=WorkstreamType.TRAINING,
            title="AiParaTi Modules 2-5 (48h)",
            description="Módulos 2-5: Prompt Eng, Azure AI, RGPD, Ethics (48h)",
            start_date=m008_start,
            end_date=m008_end,
            duration_days=60,
            owner="AiParaTi Trainer",
            depends_on=["M007"],
            is_critical_path=True,
            progress_percent=0
        ))

        # M009: Certification Exams
        m009_start = m008_end
        m009_end = m009_start + timedelta(days=7)
        milestones.append(Milestone(
            milestone_id="M009",
            workstream=WorkstreamType.TRAINING,
            title="Certification Exams",
            description="Exames certificação AiParaTi (target 85% pass rate)",
            start_date=m009_start,
            end_date=m009_end,
            duration_days=7,
            owner="Training Manager",
            depends_on=["M008"],
            progress_percent=0
        ))

        # ===== WORKSTREAM 3: INTEGRATION (Months 2-8) =====

        # M010: Integration Architecture Design
        m010_start = start_date + timedelta(days=30)
        m010_end = m010_start + timedelta(days=14)
        milestones.append(Milestone(
            milestone_id="M010",
            workstream=WorkstreamType.INTEGRATION,
            title="Integration Architecture Design",
            description="Desenhar arquitetura integração (APIs, webhooks, middleware)",
            start_date=m010_start,
            end_date=m010_end,
            duration_days=14,
            owner="Solutions Architect",
            depends_on=["M001"],
            is_critical_path=True,
            progress_percent=0
        ))

        # M011: API Integrations (Email, Calendar, CRM)
        m011_start = m010_end
        m011_end = m011_start + timedelta(days=45)
        milestones.append(Milestone(
            milestone_id="M011",
            workstream=WorkstreamType.INTEGRATION,
            title="API Integrations",
            description="Integrar LLMs com email, calendar, CRM via APIs",
            start_date=m011_start,
            end_date=m011_end,
            duration_days=45,
            owner="Backend Developer",
            depends_on=["M010"],
            is_critical_path=True,
            progress_percent=0
        ))

        # M012: Custom Workflows (Automation)
        m012_start = m011_end
        m012_end = m012_start + timedelta(days=30)
        milestones.append(Milestone(
            milestone_id="M012",
            workstream=WorkstreamType.INTEGRATION,
            title="Custom Workflows",
            description="Desenvolver workflows automação (Zapier/Make)",
            start_date=m012_start,
            end_date=m012_end,
            duration_days=30,
            owner="Automation Engineer",
            depends_on=["M011"],
            progress_percent=0
        ))

        # M013: User Acceptance Testing (UAT)
        m013_start = m012_end
        m013_end = m013_start + timedelta(days=14)
        milestones.append(Milestone(
            milestone_id="M013",
            workstream=WorkstreamType.INTEGRATION,
            title="User Acceptance Testing",
            description="UAT com 20 users (validar workflows funcionam)",
            start_date=m013_start,
            end_date=m013_end,
            duration_days=14,
            owner="QA Lead",
            depends_on=["M012"],
            is_critical_path=True,
            progress_percent=0
        ))

        # ===== WORKSTREAM 4: RH HIRING (Months 1-4) =====

        # M014: Job Descriptions & Posting
        m014_start = start_date + timedelta(days=7)
        m014_end = m014_start + timedelta(days=7)
        milestones.append(Milestone(
            milestone_id="M014",
            workstream=WorkstreamType.RH_HIRING,
            title="Job Descriptions & Posting",
            description="Criar job descriptions para RH Dedicados (AI Engineer, Data Scientist)",
            start_date=m014_start,
            end_date=m014_end,
            duration_days=7,
            owner="HR Manager",
            depends_on=[],
            progress_percent=0
        ))

        # M015: Candidate Screening
        m015_start = m014_end
        m015_end = m015_start + timedelta(days=21)
        milestones.append(Milestone(
            milestone_id="M015",
            workstream=WorkstreamType.RH_HIRING,
            title="Candidate Screening",
            description="Triagem candidatos (CV review + phone screens)",
            start_date=m015_start,
            end_date=m015_end,
            duration_days=21,
            owner="HR Manager",
            depends_on=["M014"],
            progress_percent=0
        ))

        # M016: Technical Interviews
        m016_start = m015_end
        m016_end = m016_start + timedelta(days=14)
        milestones.append(Milestone(
            milestone_id="M016",
            workstream=WorkstreamType.RH_HIRING,
            title="Technical Interviews",
            description="Entrevistas técnicas (coding challenges, system design)",
            start_date=m016_start,
            end_date=m016_end,
            duration_days=14,
            owner="CTO",
            depends_on=["M015"],
            progress_percent=0
        ))

        # M017: Offers & Onboarding
        m017_start = m016_end
        m017_end = m017_start + timedelta(days=30)
        milestones.append(Milestone(
            milestone_id="M017",
            workstream=WorkstreamType.RH_HIRING,
            title="Offers & Onboarding",
            description="Proposta + onboarding RH Dedicados (30 dias integração)",
            start_date=m017_start,
            end_date=m017_end,
            duration_days=30,
            owner="HR Manager",
            depends_on=["M016"],
            progress_percent=0
        ))

        # ===== WORKSTREAM 5: COMPLIANCE (Months 1-12) =====

        # M018: ROC Engagement
        m018_start = start_date
        m018_end = m018_start + timedelta(days=7)
        milestones.append(Milestone(
            milestone_id="M018",
            workstream=WorkstreamType.COMPLIANCE,
            title="ROC Engagement",
            description="Contratar ROC certificado OROC (€2,500 max)",
            start_date=m018_start,
            end_date=m018_end,
            duration_days=7,
            owner="CFO",
            depends_on=[],
            is_critical_path=True,
            progress_percent=80
        ))

        # M019: Financial Documentation
        m019_start = m018_end
        m019_end = m019_start + timedelta(days=30)
        milestones.append(Milestone(
            milestone_id="M019",
            workstream=WorkstreamType.COMPLIANCE,
            title="Financial Documentation",
            description="Preparar documentação financeira (3 cotações, investment matrix)",
            start_date=m019_start,
            end_date=m019_end,
            duration_days=30,
            owner="Accountant",
            depends_on=["M018"],
            is_critical_path=True,
            progress_percent=0
        ))

        # M020: IAPMEI Application Submission
        m020_start = m019_end
        m020_end = m020_start + timedelta(days=14)
        milestones.append(Milestone(
            milestone_id="M020",
            workstream=WorkstreamType.COMPLIANCE,
            title="IAPMEI Application Submission",
            description="Submeter candidatura Vale Inovação (target MP >7.0)",
            start_date=m020_start,
            end_date=m020_end,
            duration_days=14,
            owner="Project Manager",
            depends_on=["M019"],
            is_critical_path=True,
            progress_percent=0
        ))

        # M021: RGPD Compliance Audit
        m021_start = start_date + timedelta(days=60)
        m021_end = m021_start + timedelta(days=21)
        milestones.append(Milestone(
            milestone_id="M021",
            workstream=WorkstreamType.COMPLIANCE,
            title="RGPD Compliance Audit",
            description="Audit RGPD para dados sensíveis em LLMs (DPO review)",
            start_date=m021_start,
            end_date=m021_end,
            duration_days=21,
            owner="DPO",
            depends_on=[],
            progress_percent=0
        ))

        # M022: Quarterly Progress Reports
        m022_start = start_date + timedelta(days=90)
        m022_end = end_date
        milestones.append(Milestone(
            milestone_id="M022",
            workstream=WorkstreamType.COMPLIANCE,
            title="Quarterly Progress Reports",
            description="Relatórios trimestrais IAPMEI (Q1, Q2, Q3, Q4)",
            start_date=m022_start,
            end_date=m022_end,
            duration_days=(m022_end - m022_start).days,
            owner="Project Manager",
            depends_on=["M020"],
            progress_percent=0
        ))

        # ===== CALCULATE WORKSTREAM SUMMARY =====

        workstream_summary = {}
        for workstream in WorkstreamType:
            workstream_milestones = [m for m in milestones if m.workstream == workstream]
            workstream_summary[workstream] = {
                "total_milestones": len(workstream_milestones),
                "completed": sum(1 for m in workstream_milestones if m.status == MilestoneStatus.COMPLETED),
                "in_progress": sum(1 for m in workstream_milestones if m.status == MilestoneStatus.IN_PROGRESS),
                "not_started": sum(1 for m in workstream_milestones if m.status == MilestoneStatus.NOT_STARTED),
                "total_duration_days": sum(m.duration_days for m in workstream_milestones),
                "color": GanttService.WORKSTREAM_COLORS[workstream]
            }

        # Critical path milestones
        critical_path_milestones = [m.milestone_id for m in milestones if m.is_critical_path]

        logger.info(
            f"Generated Gantt chart: {len(milestones)} milestones, "
            f"{len(critical_path_milestones)} critical path"
        )

        return GanttData(
            project_name=f"{company_name} - Vale Inovação AI Implementation",
            project_start_date=start_date,
            project_end_date=end_date,
            total_duration_days=total_duration_days,
            milestones=milestones,
            workstream_summary=workstream_summary,
            critical_path_milestones=critical_path_milestones
        )

    @staticmethod
    def render_to_html(gantt_data: GanttData) -> str:
        """
        Render Gantt chart as HTML with ApexCharts timeline.

        Design:
            - ApexCharts Timeline chart
            - Color-coded by workstream
            - Interactive tooltips
            - Critical path highlighting
            - Today line indicator
        """

        html = '<div class="gantt-chart">\n'

        # Header
        html += '  <h3>📅 Implementation Timeline (Gantt Chart)</h3>\n'
        html += f'  <p>{gantt_data.project_name}</p>\n'
        html += f'  <p><strong>Duration:</strong> {gantt_data.project_start_date.date()} → {gantt_data.project_end_date.date()} ({gantt_data.total_duration_days} days)</p>\n\n'

        # Workstream legend
        html += '  <div style="display: flex; gap: 20px; margin: 20px 0;">\n'
        for workstream, summary in gantt_data.workstream_summary.items():
            html += f'    <div style="display: flex; align-items: center; gap: 8px;">\n'
            html += f'      <div style="width: 16px; height: 16px; background-color: {summary["color"]}; border-radius: 4px;"></div>\n'
            html += f'      <span>{workstream.value.replace("_", " ").title()} ({summary["total_milestones"]} tasks)</span>\n'
            html += f'    </div>\n'
        html += '  </div>\n\n'

        # ApexCharts timeline (JavaScript)
        html += '  <div id="gantt-chart-container"></div>\n'
        html += '  <script src="https://cdn.jsdelivr.net/npm/apexcharts"></script>\n'
        html += '  <script>\n'
        html += '    var options = {\n'
        html += '      series: [\n'

        # Group milestones by workstream
        for workstream in WorkstreamType:
            workstream_milestones = [m for m in gantt_data.milestones if m.workstream == workstream]
            if not workstream_milestones:
                continue

            html += '        {\n'
            html += f'          name: "{workstream.value.replace("_", " ").title()}",\n'
            html += '          data: [\n'

            for milestone in workstream_milestones:
                start_ms = int(milestone.start_date.timestamp() * 1000)
                end_ms = int(milestone.end_date.timestamp() * 1000)
                critical_marker = " 🔴 CRITICAL" if milestone.is_critical_path else ""

                html += '            {\n'
                html += f'              x: "{milestone.title}{critical_marker}",\n'
                html += f'              y: [{start_ms}, {end_ms}],\n'
                html += f'              fillColor: "{gantt_data.workstream_summary[workstream]["color"]}",\n'
                html += '            },\n'

            html += '          ]\n'
            html += '        },\n'

        html += '      ],\n'
        html += '      chart: {\n'
        html += '        height: 700,\n'
        html += '        type: "rangeBar"\n'
        html += '      },\n'
        html += '      plotOptions: {\n'
        html += '        bar: {\n'
        html += '          horizontal: true,\n'
        html += '          barHeight: "80%",\n'
        html += '          rangeBarGroupRows: true\n'
        html += '        }\n'
        html += '      },\n'
        html += '      xaxis: {\n'
        html += '        type: "datetime"\n'
        html += '      },\n'
        html += '      stroke: {\n'
        html += '        width: 1\n'
        html += '      },\n'
        html += '      fill: {\n'
        html += '        type: "solid",\n'
        html += '        opacity: 0.6\n'
        html += '      },\n'
        html += '      legend: {\n'
        html += '        position: "top"\n'
        html += '      }\n'
        html += '    };\n'
        html += '    var chart = new ApexCharts(document.querySelector("#gantt-chart-container"), options);\n'
        html += '    chart.render();\n'
        html += '  </script>\n'

        # Milestone table
        html += '  <h4 style="margin-top: 40px;">Milestone Details</h4>\n'
        html += '  <table class="data-table">\n'
        html += '    <thead>\n'
        html += '      <tr>\n'
        html += '        <th>ID</th>\n'
        html += '        <th>Workstream</th>\n'
        html += '        <th>Milestone</th>\n'
        html += '        <th>Start Date</th>\n'
        html += '        <th>End Date</th>\n'
        html += '        <th>Duration</th>\n'
        html += '        <th>Owner</th>\n'
        html += '        <th>Status</th>\n'
        html += '        <th>Progress</th>\n'
        html += '      </tr>\n'
        html += '    </thead>\n'
        html += '    <tbody>\n'

        for milestone in sorted(gantt_data.milestones, key=lambda m: m.start_date):
            critical_marker = " 🔴" if milestone.is_critical_path else ""

            # Status color
            status_colors = {
                "not_started": "#6B7280",
                "in_progress": "#F59E0B",
                "completed": "#10B981",
                "delayed": "#EF4444"
            }
            status_color = status_colors.get(milestone.status.value, "#6B7280")

            html += '      <tr>\n'
            html += f'        <td><strong>{milestone.milestone_id}{critical_marker}</strong></td>\n'
            html += f'        <td>{milestone.workstream.value.replace("_", " ").title()}</td>\n'
            html += f'        <td>{milestone.title}</td>\n'
            html += f'        <td>{milestone.start_date.strftime("%Y-%m-%d")}</td>\n'
            html += f'        <td>{milestone.end_date.strftime("%Y-%m-%d")}</td>\n'
            html += f'        <td>{milestone.duration_days} days</td>\n'
            html += f'        <td>{milestone.owner}</td>\n'
            html += f'        <td><span style="color: {status_color}; font-weight: 600;">{milestone.status.value.replace("_", " ").title()}</span></td>\n'
            html += f'        <td>{milestone.progress_percent:.0f}%</td>\n'
            html += '      </tr>\n'

        html += '    </tbody>\n'
        html += '  </table>\n'
        html += '</div>\n'

        return html

    @staticmethod
    def render_to_markdown(gantt_data: GanttData) -> str:
        """Render Gantt chart as Markdown table."""

        md = "# Implementation Timeline (Gantt Chart)\n\n"

        md += f"**Project:** {gantt_data.project_name}  \n"
        md += f"**Duration:** {gantt_data.project_start_date.date()} → {gantt_data.project_end_date.date()} ({gantt_data.total_duration_days} days)\n\n"

        md += "## Workstream Summary\n\n"
        for workstream, summary in gantt_data.workstream_summary.items():
            md += f"- **{workstream.value.replace('_', ' ').title()}**: {summary['total_milestones']} tasks, {summary['total_duration_days']} days\n"
        md += "\n"

        md += "## Milestones\n\n"
        md += "| ID | Workstream | Milestone | Start | End | Duration | Owner | Status | Progress |\n"
        md += "|----|------------|-----------|-------|-----|----------|-------|--------|----------|\n"

        for milestone in sorted(gantt_data.milestones, key=lambda m: m.start_date):
            critical_marker = " 🔴" if milestone.is_critical_path else ""
            md += f"| {milestone.milestone_id}{critical_marker} | {milestone.workstream.value.replace('_', ' ').title()} | {milestone.title} | {milestone.start_date.strftime('%Y-%m-%d')} | {milestone.end_date.strftime('%Y-%m-%d')} | {milestone.duration_days}d | {milestone.owner} | {milestone.status.value.replace('_', ' ').title()} | {milestone.progress_percent:.0f}% |\n"

        return md
