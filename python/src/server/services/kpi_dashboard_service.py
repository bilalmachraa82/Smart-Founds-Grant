"""
KPI Dashboard Service

Generates interactive KPI dashboard with 15 key metrics and traffic light indicators.
Implements IFIC best practice: real-time performance monitoring with visual indicators.

KPI Structure (15 metrics across 5 categories):
    1. Financial KPIs (4): ROI, Payback, NPV, Cost per User
    2. Adoption KPIs (3): Active Users %, Tool Usage Frequency, Training Completion %
    3. Productivity KPIs (3): Time Saved, Tasks Automated, Output Quality
    4. Risk KPIs (3): High Risks Open, Compliance Score, Budget Variance %
    5. Strategic KPIs (2): Market Position, Innovation Score

Traffic Lights:
    - GREEN: Target achieved (≥90% target)
    - YELLOW: Warning (70-90% target)
    - RED: Critical (<70% target)

Example:
    dashboard = KPIDashboardService.generate(
        investment_matrix, scenario_analysis, risk_register, adoption_data
    )
    html = KPIDashboardService.render_to_html(dashboard)
"""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime

from ..config.logfire_config import get_logger

logger = get_logger(__name__)


# ===== MODELS =====

class KPICategory(str, Enum):
    """KPI categories"""
    FINANCIAL = "financial"
    ADOPTION = "adoption"
    PRODUCTIVITY = "productivity"
    RISK = "risk"
    STRATEGIC = "strategic"


class TrafficLight(str, Enum):
    """Traffic light status"""
    GREEN = "green"   # ≥90% target
    YELLOW = "yellow"  # 70-90% target
    RED = "red"        # <70% target
    GRAY = "gray"      # Not applicable / no data


class KPIMetric(BaseModel):
    """Single KPI metric"""

    metric_id: str = Field(..., description="Unique metric ID (KPI01, KPI02, etc.)")
    category: KPICategory
    name: str = Field(..., description="Metric name")
    description: str = Field(..., description="What this metric measures")

    # Values
    current_value: float = Field(..., description="Current value")
    target_value: float = Field(..., description="Target value")
    unit: str = Field(..., description="Unit (€, %, hours, count)")

    # Performance
    progress_percent: float = Field(..., ge=0, le=100, description="Progress towards target (%)")
    status: TrafficLight = Field(..., description="Traffic light status")

    # Context
    benchmark: Optional[float] = Field(None, description="Industry benchmark value")
    trend: Optional[str] = Field(None, description="Trend: ↑ improving, ↓ declining, → stable")
    last_updated: datetime = Field(default_factory=datetime.now)


class KPIDashboard(BaseModel):
    """Complete KPI dashboard with 15 metrics"""

    metrics: List[KPIMetric] = Field(..., min_items=15, max_items=15)

    # Summary
    total_green: int = Field(default=0, ge=0)
    total_yellow: int = Field(default=0, ge=0)
    total_red: int = Field(default=0, ge=0)
    overall_health_percent: float = Field(..., ge=0, le=100, description="Overall project health %")

    # Insights
    top_performers: List[str] = Field(default_factory=list, description="Top 3 performing KPIs")
    areas_of_concern: List[str] = Field(default_factory=list, description="KPIs needing attention")


# ===== KPI DASHBOARD SERVICE =====

class KPIDashboardService:
    """
    Generate KPI dashboard with 15 metrics.

    Process:
        1. Define 15 KPIs across 5 categories
        2. Calculate current vs target for each
        3. Assign traffic light status
        4. Identify top performers and areas of concern
        5. Render as HTML dashboard
    """

    @staticmethod
    def generate(
        total_investment: float,
        annual_savings: float,
        payback_months: float,
        npv_3_years: float,
        num_users: int,
        num_trained: int,
        high_risks_count: int,
        total_risks_count: int,
        budget_variance_percent: float = 0,
        adoption_rate_percent: float = 70,
        tool_usage_frequency_per_week: float = 12,
        training_completion_percent: float = 85,
        time_saved_hours_per_month: float = 320,
        tasks_automated_count: int = 45,
        output_quality_score: float = 8.2,
        compliance_score_percent: float = 95,
        market_position_score: float = 7.5,
        innovation_score: float = 8.0
    ) -> KPIDashboard:
        """
        Generate KPI dashboard with 15 metrics.

        Args:
            total_investment: Total investment (€)
            annual_savings: Expected annual savings (€)
            payback_months: Payback period (months)
            npv_3_years: NPV over 3 years (€)
            num_users: Number of users
            num_trained: Number of trained employees
            high_risks_count: Number of HIGH probability risks
            total_risks_count: Total number of risks
            budget_variance_percent: Budget variance % (negative = under budget, positive = over budget)
            adoption_rate_percent: Active users adoption rate %
            tool_usage_frequency_per_week: How many times per week users use tools
            training_completion_percent: % employees who completed training
            time_saved_hours_per_month: Total time saved per month (hours)
            tasks_automated_count: Number of tasks automated
            output_quality_score: Output quality score (0-10)
            compliance_score_percent: Compliance validation score %
            market_position_score: Market position score (0-10)
            innovation_score: Innovation score (0-10)

        Returns:
            KPIDashboard with 15 metrics + traffic light status
        """

        metrics = []

        # ===== FINANCIAL KPIs (4) =====

        # KPI01: ROI %
        roi_percent = ((annual_savings * 3 - total_investment * 0.25) / (total_investment * 0.25) * 100) if total_investment > 0 else 0
        roi_target = 300  # 300% ROI over 3 years
        roi_progress = min((roi_percent / roi_target) * 100, 100)
        metrics.append(KPIMetric(
            metric_id="KPI01",
            category=KPICategory.FINANCIAL,
            name="ROI (3 anos)",
            description="Return on Investment over 3 years",
            current_value=roi_percent,
            target_value=roi_target,
            unit="%",
            progress_percent=roi_progress,
            status=TrafficLight.GREEN if roi_progress >= 90 else TrafficLight.YELLOW if roi_progress >= 70 else TrafficLight.RED,
            benchmark=250,
            trend="↑"
        ))

        # KPI02: Payback Period
        payback_target = 18  # 18 months target
        payback_progress = max(100 - ((payback_months - payback_target) / payback_target * 100), 0)
        metrics.append(KPIMetric(
            metric_id="KPI02",
            category=KPICategory.FINANCIAL,
            name="Payback Period",
            description="Time to recover net investment",
            current_value=payback_months,
            target_value=payback_target,
            unit="months",
            progress_percent=payback_progress,
            status=TrafficLight.GREEN if payback_months <= 18 else TrafficLight.YELLOW if payback_months <= 24 else TrafficLight.RED,
            benchmark=24,
            trend="↓"
        ))

        # KPI03: NPV (3 years)
        npv_target = total_investment * 0.50  # Target: 50% NPV over 3 years
        npv_progress = min((npv_3_years / npv_target) * 100, 100) if npv_target > 0 else 0
        metrics.append(KPIMetric(
            metric_id="KPI03",
            category=KPICategory.FINANCIAL,
            name="NPV (3 anos)",
            description="Net Present Value (8% discount rate)",
            current_value=npv_3_years,
            target_value=npv_target,
            unit="€",
            progress_percent=npv_progress,
            status=TrafficLight.GREEN if npv_progress >= 90 else TrafficLight.YELLOW if npv_progress >= 70 else TrafficLight.RED,
            benchmark=npv_target * 0.80,
            trend="↑"
        ))

        # KPI04: Cost per User
        cost_per_user = (total_investment / num_users) if num_users > 0 else 0
        cost_per_user_target = 5000  # €5,000 per user target
        cost_per_user_progress = max(100 - ((cost_per_user - cost_per_user_target) / cost_per_user_target * 100), 0)
        metrics.append(KPIMetric(
            metric_id="KPI04",
            category=KPICategory.FINANCIAL,
            name="Cost per User",
            description="Total investment divided by number of users",
            current_value=cost_per_user,
            target_value=cost_per_user_target,
            unit="€/user",
            progress_percent=cost_per_user_progress,
            status=TrafficLight.GREEN if cost_per_user <= 5000 else TrafficLight.YELLOW if cost_per_user <= 7000 else TrafficLight.RED,
            benchmark=6000,
            trend="→"
        ))

        # ===== ADOPTION KPIs (3) =====

        # KPI05: Active Users %
        adoption_target = 80  # 80% adoption target
        adoption_progress = (adoption_rate_percent / adoption_target) * 100
        metrics.append(KPIMetric(
            metric_id="KPI05",
            category=KPICategory.ADOPTION,
            name="Active Users %",
            description="% of users actively using AI tools (at least 1x per week)",
            current_value=adoption_rate_percent,
            target_value=adoption_target,
            unit="%",
            progress_percent=adoption_progress,
            status=TrafficLight.GREEN if adoption_rate_percent >= 72 else TrafficLight.YELLOW if adoption_rate_percent >= 56 else TrafficLight.RED,
            benchmark=65,
            trend="↑"
        ))

        # KPI06: Tool Usage Frequency
        usage_target = 15  # 15 times per week target
        usage_progress = (tool_usage_frequency_per_week / usage_target) * 100
        metrics.append(KPIMetric(
            metric_id="KPI06",
            category=KPICategory.ADOPTION,
            name="Tool Usage Frequency",
            description="Average number of times per week users interact with AI tools",
            current_value=tool_usage_frequency_per_week,
            target_value=usage_target,
            unit="times/week",
            progress_percent=usage_progress,
            status=TrafficLight.GREEN if tool_usage_frequency_per_week >= 13.5 else TrafficLight.YELLOW if tool_usage_frequency_per_week >= 10.5 else TrafficLight.RED,
            benchmark=12,
            trend="↑"
        ))

        # KPI07: Training Completion %
        training_target = 90  # 90% training completion target
        training_progress = (training_completion_percent / training_target) * 100
        metrics.append(KPIMetric(
            metric_id="KPI07",
            category=KPICategory.ADOPTION,
            name="Training Completion %",
            description="% of employees who completed full AI training program",
            current_value=training_completion_percent,
            target_value=training_target,
            unit="%",
            progress_percent=training_progress,
            status=TrafficLight.GREEN if training_completion_percent >= 81 else TrafficLight.YELLOW if training_completion_percent >= 63 else TrafficLight.RED,
            benchmark=75,
            trend="→"
        ))

        # ===== PRODUCTIVITY KPIs (3) =====

        # KPI08: Time Saved (hours/month)
        time_saved_target = 400  # 400 hours per month target
        time_saved_progress = (time_saved_hours_per_month / time_saved_target) * 100
        metrics.append(KPIMetric(
            metric_id="KPI08",
            category=KPICategory.PRODUCTIVITY,
            name="Time Saved",
            description="Total hours saved per month through AI automation",
            current_value=time_saved_hours_per_month,
            target_value=time_saved_target,
            unit="hours/month",
            progress_percent=time_saved_progress,
            status=TrafficLight.GREEN if time_saved_hours_per_month >= 360 else TrafficLight.YELLOW if time_saved_hours_per_month >= 280 else TrafficLight.RED,
            benchmark=350,
            trend="↑"
        ))

        # KPI09: Tasks Automated
        tasks_target = 50  # 50 tasks automated target
        tasks_progress = (tasks_automated_count / tasks_target) * 100
        metrics.append(KPIMetric(
            metric_id="KPI09",
            category=KPICategory.PRODUCTIVITY,
            name="Tasks Automated",
            description="Number of repetitive tasks successfully automated with AI",
            current_value=float(tasks_automated_count),
            target_value=float(tasks_target),
            unit="tasks",
            progress_percent=tasks_progress,
            status=TrafficLight.GREEN if tasks_automated_count >= 45 else TrafficLight.YELLOW if tasks_automated_count >= 35 else TrafficLight.RED,
            benchmark=40,
            trend="↑"
        ))

        # KPI10: Output Quality Score
        quality_target = 9.0  # 9.0/10 quality target
        quality_progress = (output_quality_score / quality_target) * 100
        metrics.append(KPIMetric(
            metric_id="KPI10",
            category=KPICategory.PRODUCTIVITY,
            name="Output Quality Score",
            description="Quality score of AI-generated outputs (0-10 scale)",
            current_value=output_quality_score,
            target_value=quality_target,
            unit="/10",
            progress_percent=quality_progress,
            status=TrafficLight.GREEN if output_quality_score >= 8.1 else TrafficLight.YELLOW if output_quality_score >= 6.3 else TrafficLight.RED,
            benchmark=8.0,
            trend="→"
        ))

        # ===== RISK KPIs (3) =====

        # KPI11: High Risks Open
        high_risks_target = 2  # Maximum 2 HIGH risks acceptable
        high_risks_progress = max(100 - ((high_risks_count - high_risks_target) / max(high_risks_target, 1) * 100), 0)
        metrics.append(KPIMetric(
            metric_id="KPI11",
            category=KPICategory.RISK,
            name="High Risks Open",
            description="Number of HIGH probability risks still active",
            current_value=float(high_risks_count),
            target_value=float(high_risks_target),
            unit="risks",
            progress_percent=high_risks_progress,
            status=TrafficLight.GREEN if high_risks_count <= 2 else TrafficLight.YELLOW if high_risks_count <= 4 else TrafficLight.RED,
            benchmark=3,
            trend="↓"
        ))

        # KPI12: Compliance Score
        compliance_target = 100  # 100% compliance target
        compliance_progress = (compliance_score_percent / compliance_target) * 100
        metrics.append(KPIMetric(
            metric_id="KPI12",
            category=KPICategory.RISK,
            name="Compliance Score",
            description="% of compliance rules validated (Aviso 03/C05)",
            current_value=compliance_score_percent,
            target_value=compliance_target,
            unit="%",
            progress_percent=compliance_progress,
            status=TrafficLight.GREEN if compliance_score_percent >= 90 else TrafficLight.YELLOW if compliance_score_percent >= 70 else TrafficLight.RED,
            benchmark=95,
            trend="→"
        ))

        # KPI13: Budget Variance %
        budget_variance_target = 0  # 0% variance target
        budget_variance_progress = max(100 - abs(budget_variance_percent), 0)
        metrics.append(KPIMetric(
            metric_id="KPI13",
            category=KPICategory.RISK,
            name="Budget Variance %",
            description="% deviation from approved budget (negative = under, positive = over)",
            current_value=budget_variance_percent,
            target_value=budget_variance_target,
            unit="%",
            progress_percent=budget_variance_progress,
            status=TrafficLight.GREEN if abs(budget_variance_percent) <= 5 else TrafficLight.YELLOW if abs(budget_variance_percent) <= 10 else TrafficLight.RED,
            benchmark=5,
            trend="↓" if budget_variance_percent < 0 else "↑"
        ))

        # ===== STRATEGIC KPIs (2) =====

        # KPI14: Market Position Score
        market_target = 8.5  # 8.5/10 market position target
        market_progress = (market_position_score / market_target) * 100
        metrics.append(KPIMetric(
            metric_id="KPI14",
            category=KPICategory.STRATEGIC,
            name="Market Position Score",
            description="Competitive positioning score (0-10 scale)",
            current_value=market_position_score,
            target_value=market_target,
            unit="/10",
            progress_percent=market_progress,
            status=TrafficLight.GREEN if market_position_score >= 7.65 else TrafficLight.YELLOW if market_position_score >= 5.95 else TrafficLight.RED,
            benchmark=7.0,
            trend="↑"
        ))

        # KPI15: Innovation Score
        innovation_target = 9.0  # 9.0/10 innovation target
        innovation_progress = (innovation_score / innovation_target) * 100
        metrics.append(KPIMetric(
            metric_id="KPI15",
            category=KPICategory.STRATEGIC,
            name="Innovation Score",
            description="Innovation maturity score (0-10 scale)",
            current_value=innovation_score,
            target_value=innovation_target,
            unit="/10",
            progress_percent=innovation_progress,
            status=TrafficLight.GREEN if innovation_score >= 8.1 else TrafficLight.YELLOW if innovation_score >= 6.3 else TrafficLight.RED,
            benchmark=7.5,
            trend="↑"
        ))

        # ===== AGGREGATIONS =====

        total_green = sum(1 for m in metrics if m.status == TrafficLight.GREEN)
        total_yellow = sum(1 for m in metrics if m.status == TrafficLight.YELLOW)
        total_red = sum(1 for m in metrics if m.status == TrafficLight.RED)

        overall_health_percent = (total_green * 100 + total_yellow * 70 + total_red * 30) / len(metrics)

        # Top performers (top 3 GREEN with highest progress)
        top_performers = sorted(
            [m.name for m in metrics if m.status == TrafficLight.GREEN],
            key=lambda name: next(m.progress_percent for m in metrics if m.name == name),
            reverse=True
        )[:3]

        # Areas of concern (all RED + YELLOW with lowest progress)
        areas_of_concern = [m.name for m in sorted(metrics, key=lambda m: m.progress_percent) if m.status in [TrafficLight.RED, TrafficLight.YELLOW]][:3]

        logger.info(
            f"Generated KPI dashboard: {len(metrics)} metrics, "
            f"{total_green} GREEN, {total_yellow} YELLOW, {total_red} RED, "
            f"overall health {overall_health_percent:.1f}%"
        )

        return KPIDashboard(
            metrics=metrics,
            total_green=total_green,
            total_yellow=total_yellow,
            total_red=total_red,
            overall_health_percent=overall_health_percent,
            top_performers=top_performers,
            areas_of_concern=areas_of_concern
        )

    @staticmethod
    def render_to_html(dashboard: KPIDashboard) -> str:
        """
        Render KPI dashboard as HTML with traffic lights.

        Design:
            - 5 category sections (Financial, Adoption, Productivity, Risk, Strategic)
            - Traffic light indicators (🟢🟡🔴)
            - Progress bars
            - Overall health gauge
        """

        html = '<div class="kpi-dashboard">\n'

        # Header
        html += '  <h3>📊 KPI Dashboard (15 Key Metrics)</h3>\n'
        html += f'  <p>Overall Project Health: <strong style="color: {"#10B981" if dashboard.overall_health_percent >= 80 else "#F59E0B" if dashboard.overall_health_percent >= 60 else "#EF4444"};">{dashboard.overall_health_percent:.0f}%</strong></p>\n'
        html += f'  <p>Status: {dashboard.total_green} 🟢 GREEN | {dashboard.total_yellow} 🟡 YELLOW | {dashboard.total_red} 🔴 RED</p>\n\n'

        # Top performers & areas of concern
        html += '  <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0;">\n'
        html += '    <div class="callout callout-success">\n'
        html += '      <h4>🏆 Top Performers</h4>\n'
        html += '      <ul>\n'
        for performer in dashboard.top_performers:
            html += f'        <li>{performer}</li>\n'
        html += '      </ul>\n'
        html += '    </div>\n'
        html += '    <div class="callout callout-warning">\n'
        html += '      <h4>⚠️ Areas of Concern</h4>\n'
        html += '      <ul>\n'
        for concern in dashboard.areas_of_concern:
            html += f'        <li>{concern}</li>\n'
        html += '      </ul>\n'
        html += '    </div>\n'
        html += '  </div>\n\n'

        # KPIs by category
        categories = [
            (KPICategory.FINANCIAL, "💰 Financial KPIs"),
            (KPICategory.ADOPTION, "👥 Adoption KPIs"),
            (KPICategory.PRODUCTIVITY, "⚡ Productivity KPIs"),
            (KPICategory.RISK, "⚠️ Risk KPIs"),
            (KPICategory.STRATEGIC, "🎯 Strategic KPIs")
        ]

        for category, category_label in categories:
            category_metrics = [m for m in dashboard.metrics if m.category == category]

            html += f'  <h4>{category_label}</h4>\n'
            html += '  <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; margin-bottom: 30px;">\n'

            for metric in category_metrics:
                # Traffic light emoji
                traffic_light = {"green": "🟢", "yellow": "🟡", "red": "🔴", "gray": "⚪"}[metric.status.value]

                # Progress bar color
                bar_color = {"green": "#10B981", "yellow": "#F59E0B", "red": "#EF4444", "gray": "#6B7280"}[metric.status.value]

                html += '    <div style="border: 1px solid #E5E7EB; border-radius: 8px; padding: 16px; background-color: #FFFFFF;">\n'
                html += f'      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">\n'
                html += f'        <strong>{metric.name}</strong>\n'
                html += f'        <span style="font-size: 24px;">{traffic_light}</span>\n'
                html += f'      </div>\n'
                html += f'      <p style="font-size: 12px; color: #6B7280; margin: 4px 0;">{metric.description}</p>\n'
                html += f'      <div style="display: flex; justify-content: space-between; margin: 8px 0;">\n'
                html += f'        <span style="font-size: 18px; font-weight: 600;">{metric.current_value:,.1f}{metric.unit}</span>\n'
                html += f'        <span style="font-size: 12px; color: #6B7280;">Target: {metric.target_value:,.1f}{metric.unit}</span>\n'
                html += f'      </div>\n'

                # Progress bar
                html += f'      <div style="width: 100%; background-color: #E5E7EB; border-radius: 4px; height: 8px; overflow: hidden;">\n'
                html += f'        <div style="width: {min(metric.progress_percent, 100):.0f}%; background-color: {bar_color}; height: 100%;"></div>\n'
                html += f'      </div>\n'
                html += f'      <div style="display: flex; justify-content: space-between; margin-top: 4px; font-size: 11px; color: #6B7280;">\n'
                html += f'        <span>Progress: {metric.progress_percent:.0f}%</span>\n'
                if metric.trend:
                    html += f'        <span>Trend: {metric.trend}</span>\n'
                html += f'      </div>\n'
                html += '    </div>\n'

            html += '  </div>\n'

        html += '</div>\n'

        return html

    @staticmethod
    def render_to_markdown(dashboard: KPIDashboard) -> str:
        """Render KPI dashboard as Markdown."""

        md = "# KPI Dashboard (15 Key Metrics)\n\n"

        md += f"**Overall Project Health:** {dashboard.overall_health_percent:.0f}%  \n"
        md += f"**Status:** {dashboard.total_green} 🟢 GREEN | {dashboard.total_yellow} 🟡 YELLOW | {dashboard.total_red} 🔴 RED\n\n"

        md += "## 🏆 Top Performers\n\n"
        for performer in dashboard.top_performers:
            md += f"- {performer}\n"
        md += "\n"

        md += "## ⚠️ Areas of Concern\n\n"
        for concern in dashboard.areas_of_concern:
            md += f"- {concern}\n"
        md += "\n"

        # KPIs by category
        categories = [
            (KPICategory.FINANCIAL, "💰 Financial KPIs"),
            (KPICategory.ADOPTION, "👥 Adoption KPIs"),
            (KPICategory.PRODUCTIVITY, "⚡ Productivity KPIs"),
            (KPICategory.RISK, "⚠️ Risk KPIs"),
            (KPICategory.STRATEGIC, "🎯 Strategic KPIs")
        ]

        for category, category_label in categories:
            category_metrics = [m for m in dashboard.metrics if m.category == category]

            md += f"## {category_label}\n\n"
            md += "| Metric | Current | Target | Progress | Status |\n"
            md += "|--------|---------|--------|----------|--------|\n"

            for metric in category_metrics:
                traffic_light = {"green": "🟢", "yellow": "🟡", "red": "🔴", "gray": "⚪"}[metric.status.value]
                md += f"| {metric.name} | {metric.current_value:,.1f}{metric.unit} | {metric.target_value:,.1f}{metric.unit} | {metric.progress_percent:.0f}% | {traffic_light} |\n"

            md += "\n"

        return md
