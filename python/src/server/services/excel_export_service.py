"""
Excel Export Service

Generates multi-sheet Excel export with formatting, charts, and data validation.
Implements IFIC best practice: professional Excel deliverable for CFO/board review.

Excel Structure (5 sheets):
    1. Executive Summary (SCQA + key metrics)
    2. Budget Breakdown (investment matrix)
    3. Scenarios (3 scenarios comparison)
    4. Risk Register (risks table + matrix)
    5. Implementation Timeline (Gantt chart)

Uses openpyxl for Excel generation with:
    - Professional formatting (brand colors)
    - Data validation
    - Conditional formatting
    - Charts (bar, pie, Gantt)
    - Formulas for calculations

Example:
    excel_bytes = ExcelExportService.generate(
        scqa, investment_matrix, scenarios, risk_register, gantt_data
    )
    # Returns: BytesIO object with Excel file
"""

from typing import List, Dict, Optional, BinaryIO
from io import BytesIO
from datetime import datetime, timedelta
import logging

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from openpyxl.utils import get_column_letter
    from openpyxl.chart import BarChart, PieChart, Reference
    from openpyxl.worksheet.datavalidation import DataValidation
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False
    logging.warning("openpyxl not installed. Excel export will not work. Install: pip install openpyxl")

from .scqa_framework_service import SCQA
from .investment_matrix_service import InvestmentMatrix
from .scenario_analysis_service import ScenarioAnalysis, Scenario
from .risk_register_service import RiskRegister
from ..config.logfire_config import get_logger

logger = get_logger(__name__)


# ===== BRAND COLORS (from design system) =====

BRAND_COLORS = {
    "primary": "0066CC",  # Blue
    "success": "10B981",  # Green
    "warning": "F59E0B",  # Orange
    "danger": "EF4444",   # Red
    "gray": "6B7280",
    "light_gray": "F3F4F6"
}


# ===== EXCEL EXPORT SERVICE =====

class ExcelExportService:
    """
    Generate multi-sheet Excel export.

    Process:
        1. Create workbook with 5 sheets
        2. Sheet 1: Executive Summary (SCQA + KPIs)
        3. Sheet 2: Budget Breakdown (investment matrix table)
        4. Sheet 3: Scenarios (3 scenarios comparison + chart)
        5. Sheet 4: Risk Register (risks table + matrix heatmap)
        6. Sheet 5: Implementation Timeline (Gantt chart)
        7. Apply formatting (fonts, colors, borders)
        8. Return BytesIO object
    """

    @staticmethod
    def generate(
        company_name: str,
        scqa: SCQA,
        investment_matrix: InvestmentMatrix,
        scenario_analysis: ScenarioAnalysis,
        risk_register: RiskRegister,
        gantt_data: Optional[Dict] = None
    ) -> BytesIO:
        """
        Generate Excel export with 5 sheets.

        Args:
            company_name: Company name for header
            scqa: SCQA framework
            investment_matrix: Investment matrix
            scenario_analysis: Scenario analysis
            risk_register: Risk register
            gantt_data: Gantt chart data (optional)

        Returns:
            BytesIO object containing Excel file

        Raises:
            ImportError: If openpyxl not installed
        """

        if not OPENPYXL_AVAILABLE:
            raise ImportError(
                "openpyxl not installed. Cannot generate Excel. "
                "Install with: pip install openpyxl"
            )

        logger.info(f"Generating Excel export for {company_name}")

        # Create workbook
        wb = Workbook()
        wb.remove(wb.active)  # Remove default sheet

        # ===== SHEET 1: EXECUTIVE SUMMARY =====
        ws_summary = wb.create_sheet("Executive Summary", 0)
        ExcelExportService._build_summary_sheet(ws_summary, company_name, scqa, investment_matrix, scenario_analysis)

        # ===== SHEET 2: BUDGET BREAKDOWN =====
        ws_budget = wb.create_sheet("Budget Breakdown", 1)
        ExcelExportService._build_budget_sheet(ws_budget, investment_matrix)

        # ===== SHEET 3: SCENARIOS =====
        ws_scenarios = wb.create_sheet("Scenarios", 2)
        ExcelExportService._build_scenarios_sheet(ws_scenarios, scenario_analysis)

        # ===== SHEET 4: RISK REGISTER =====
        ws_risks = wb.create_sheet("Risk Register", 3)
        ExcelExportService._build_risk_sheet(ws_risks, risk_register)

        # ===== SHEET 5: IMPLEMENTATION TIMELINE =====
        if gantt_data:
            ws_gantt = wb.create_sheet("Implementation Timeline", 4)
            ExcelExportService._build_gantt_sheet(ws_gantt, gantt_data)

        # Save to BytesIO
        excel_buffer = BytesIO()
        wb.save(excel_buffer)
        excel_buffer.seek(0)

        logger.info(f"Excel export generated: {len(wb.sheetnames)} sheets, {excel_buffer.getbuffer().nbytes} bytes")

        return excel_buffer

    @staticmethod
    def _build_summary_sheet(ws, company_name: str, scqa: SCQA, investment_matrix: InvestmentMatrix, scenario_analysis: ScenarioAnalysis):
        """Build Sheet 1: Executive Summary."""

        # Header
        ws.merge_cells('A1:F1')
        ws['A1'] = f"{company_name} - Vale Inovação AI Strategy"
        ws['A1'].font = Font(size=16, bold=True, color="FFFFFF")
        ws['A1'].fill = PatternFill(start_color=BRAND_COLORS["primary"], end_color=BRAND_COLORS["primary"], fill_type="solid")
        ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
        ws.row_dimensions[1].height = 30

        # Subheader
        ws.merge_cells('A2:F2')
        ws['A2'] = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        ws['A2'].font = Font(size=10, italic=True, color=BRAND_COLORS["gray"])
        ws['A2'].alignment = Alignment(horizontal='center')

        # SCQA Framework
        row = 4
        ws[f'A{row}'] = "EXECUTIVE SUMMARY (SCQA Framework)"
        ws[f'A{row}'].font = Font(size=14, bold=True)
        row += 2

        # Situation
        ws[f'A{row}'] = "Situation:"
        ws[f'A{row}'].font = Font(bold=True)
        ws.merge_cells(f'B{row}:F{row}')
        ws[f'B{row}'] = scqa.situation
        ws[f'B{row}'].alignment = Alignment(wrap_text=True)
        ws.row_dimensions[row].height = 40
        row += 2

        # Complication
        ws[f'A{row}'] = "Complication:"
        ws[f'A{row}'].font = Font(bold=True, color=BRAND_COLORS["danger"])
        ws.merge_cells(f'B{row}:F{row}')
        ws[f'B{row}'] = scqa.complication
        ws[f'B{row}'].alignment = Alignment(wrap_text=True)
        ws.row_dimensions[row].height = 40
        row += 2

        # Question
        ws[f'A{row}'] = "Question:"
        ws[f'A{row}'].font = Font(bold=True, color=BRAND_COLORS["warning"])
        ws.merge_cells(f'B{row}:F{row}')
        ws[f'B{row}'] = scqa.question
        ws[f'B{row}'].alignment = Alignment(wrap_text=True)
        ws.row_dimensions[row].height = 30
        row += 2

        # Answer
        ws[f'A{row}'] = "Answer:"
        ws[f'A{row}'].font = Font(bold=True, color=BRAND_COLORS["success"])
        ws.merge_cells(f'B{row}:F{row}')
        ws[f'B{row}'] = scqa.answer
        ws[f'B{row}'].alignment = Alignment(wrap_text=True)
        ws.row_dimensions[row].height = 60
        row += 3

        # Key Metrics
        ws[f'A{row}'] = "KEY METRICS"
        ws[f'A{row}'].font = Font(size=14, bold=True)
        row += 2

        # Metrics table
        metrics_data = [
            ["Metric", "Value"],
            ["Total Investment", f"€{investment_matrix.total_investment:,.0f}"],
            ["Subsidy (75%)", f"€{investment_matrix.total_investment * 0.75:,.0f}"],
            ["Net Investment (25%)", f"€{investment_matrix.total_investment * 0.25:,.0f}"],
            ["Expected Annual Savings", f"€{investment_matrix.expected_annual_savings:,.0f}"],
            ["Payback Period", f"{investment_matrix.payback_period_months:.1f} months"],
            ["ROI (3 years)", f"{investment_matrix.roi_percent:.1f}%"],
            ["Expected NPV", f"€{scenario_analysis.expected_value:,.0f}"],
            ["Risk-Adjusted ROI", f"{scenario_analysis.risk_adjusted_roi:.1f}%"]
        ]

        for i, row_data in enumerate(metrics_data):
            for j, value in enumerate(row_data):
                cell = ws.cell(row=row+i, column=j+1, value=value)
                if i == 0:  # Header
                    cell.font = Font(bold=True, color="FFFFFF")
                    cell.fill = PatternFill(start_color=BRAND_COLORS["primary"], end_color=BRAND_COLORS["primary"], fill_type="solid")
                cell.border = Border(
                    left=Side(style='thin'),
                    right=Side(style='thin'),
                    top=Side(style='thin'),
                    bottom=Side(style='thin')
                )

        # Column widths
        ws.column_dimensions['A'].width = 25
        ws.column_dimensions['B'].width = 60
        for col in ['C', 'D', 'E', 'F']:
            ws.column_dimensions[col].width = 15

    @staticmethod
    def _build_budget_sheet(ws, investment_matrix: InvestmentMatrix):
        """Build Sheet 2: Budget Breakdown."""

        # Header
        ws.merge_cells('A1:I1')
        ws['A1'] = "Investment Matrix"
        ws['A1'].font = Font(size=14, bold=True, color="FFFFFF")
        ws['A1'].fill = PatternFill(start_color=BRAND_COLORS["primary"], end_color=BRAND_COLORS["primary"], fill_type="solid")
        ws['A1'].alignment = Alignment(horizontal='center')

        # Table headers
        headers = ["Priority", "Category", "Tool/Service", "Amount (€)", "Objective", "Capability", "Outcome", "KPI", "Timeline"]
        for col_idx, header in enumerate(headers, start=1):
            cell = ws.cell(row=3, column=col_idx, value=header)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color=BRAND_COLORS["gray"], end_color=BRAND_COLORS["gray"], fill_type="solid")
            cell.alignment = Alignment(horizontal='center')

        # Data rows
        row = 4
        for item in sorted(investment_matrix.items, key=lambda x: {"CRÍTICO": 0, "ALTO": 1, "MÉDIO": 2, "BAIXO": 3}.get(x.priority, 4)):
            ws.cell(row=row, column=1, value=item.priority)
            ws.cell(row=row, column=2, value=item.category.value.replace("_", " ").title())
            ws.cell(row=row, column=3, value=item.tool_or_service)
            ws.cell(row=row, column=4, value=item.amount_eur).number_format = '€#,##0.00'
            ws.cell(row=row, column=5, value=item.objective)
            ws.cell(row=row, column=6, value=item.capability_gained)
            ws.cell(row=row, column=7, value=item.expected_outcome)
            ws.cell(row=row, column=8, value=item.kpi)
            ws.cell(row=row, column=9, value=f"{item.timeline_months} months")

            # Priority color coding
            priority_colors = {"CRÍTICO": BRAND_COLORS["danger"], "ALTO": BRAND_COLORS["warning"], "MÉDIO": "EAB308", "BAIXO": BRAND_COLORS["success"]}
            ws.cell(row=row, column=1).fill = PatternFill(start_color=priority_colors.get(item.priority, BRAND_COLORS["gray"]), end_color=priority_colors.get(item.priority, BRAND_COLORS["gray"]), fill_type="solid")
            ws.cell(row=row, column=1).font = Font(color="FFFFFF", bold=True)

            row += 1

        # Total row
        ws.cell(row=row, column=1, value="TOTAL").font = Font(bold=True)
        ws.merge_cells(f'A{row}:C{row}')
        ws.cell(row=row, column=4, value=investment_matrix.total_investment).number_format = '€#,##0.00'
        ws.cell(row=row, column=4).font = Font(bold=True)
        ws.cell(row=row, column=4).fill = PatternFill(start_color=BRAND_COLORS["light_gray"], end_color=BRAND_COLORS["light_gray"], fill_type="solid")

        # Column widths
        ws.column_dimensions['A'].width = 12
        ws.column_dimensions['B'].width = 18
        ws.column_dimensions['C'].width = 30
        ws.column_dimensions['D'].width = 15
        for col in ['E', 'F', 'G', 'H']:
            ws.column_dimensions[col].width = 35
        ws.column_dimensions['I'].width = 12

        # Add pie chart for budget by category
        chart = PieChart()
        chart.title = "Budget by Category"
        chart.style = 10
        chart.height = 10
        chart.width = 16

        # Chart data (categories and amounts)
        category_row = row + 3
        ws.cell(row=category_row, column=1, value="Category")
        ws.cell(row=category_row, column=2, value="Amount (€)")

        data_row = category_row + 1
        for category, amount in investment_matrix.total_by_category.items():
            if amount > 0:
                ws.cell(row=data_row, column=1, value=category.value.replace("_", " ").title())
                ws.cell(row=data_row, column=2, value=amount)
                data_row += 1

        data = Reference(ws, min_col=2, min_row=category_row, max_row=data_row-1)
        cats = Reference(ws, min_col=1, min_row=category_row+1, max_row=data_row-1)
        chart.add_data(data, titles_from_data=True)
        chart.set_categories(cats)

        ws.add_chart(chart, f"E{category_row}")

    @staticmethod
    def _build_scenarios_sheet(ws, scenario_analysis: ScenarioAnalysis):
        """Build Sheet 3: Scenarios."""

        # Header
        ws.merge_cells('A1:H1')
        ws['A1'] = "Scenario Analysis (Conservative / Moderate / Aggressive)"
        ws['A1'].font = Font(size=14, bold=True, color="FFFFFF")
        ws['A1'].fill = PatternFill(start_color=BRAND_COLORS["primary"], end_color=BRAND_COLORS["primary"], fill_type="solid")
        ws['A1'].alignment = Alignment(horizontal='center')

        # Expected value callout
        ws.merge_cells('A3:H3')
        ws['A3'] = f"Expected Value (Probability-Weighted): €{scenario_analysis.expected_value:,.0f} NPV | {scenario_analysis.risk_adjusted_roi:.1f}% ROI"
        ws['A3'].font = Font(size=12, bold=True, color=BRAND_COLORS["success"])
        ws['A3'].alignment = Alignment(horizontal='center')
        ws['A3'].fill = PatternFill(start_color=BRAND_COLORS["light_gray"], end_color=BRAND_COLORS["light_gray"], fill_type="solid")

        # Table headers
        headers = ["Scenario", "Total Investment", "Subsidy (75%)", "Net Investment", "Savings Y1", "Savings Y2", "Savings Y3", "Payback (months)", "NPV (3y)", "ROI %", "Success Probability"]
        row = 5
        for col_idx, header in enumerate(headers, start=1):
            cell = ws.cell(row=row, column=col_idx, value=header)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color=BRAND_COLORS["gray"], end_color=BRAND_COLORS["gray"], fill_type="solid")
            cell.alignment = Alignment(horizontal='center', wrap_text=True)

        # Data rows
        row = 6
        scenario_colors = {
            "conservative": "FEE2E2",  # Red tint
            "moderate": "F0FDF4",      # Green tint
            "aggressive": "DBEAFE"     # Blue tint
        }

        for scenario in scenario_analysis.scenarios:
            recommended = " ⭐" if scenario.scenario_type == scenario_analysis.recommended else ""

            ws.cell(row=row, column=1, value=scenario.label + recommended)
            ws.cell(row=row, column=2, value=scenario.total_investment).number_format = '€#,##0'
            ws.cell(row=row, column=3, value=scenario.subsidy_75_percent).number_format = '€#,##0'
            ws.cell(row=row, column=4, value=scenario.net_investment).number_format = '€#,##0'
            ws.cell(row=row, column=5, value=scenario.annual_savings_y1).number_format = '€#,##0'
            ws.cell(row=row, column=6, value=scenario.annual_savings_y2).number_format = '€#,##0'
            ws.cell(row=row, column=7, value=scenario.annual_savings_y3).number_format = '€#,##0'
            ws.cell(row=row, column=8, value=scenario.payback_period_months).number_format = '0.0'
            ws.cell(row=row, column=9, value=scenario.npv_3_years).number_format = '€#,##0'
            ws.cell(row=row, column=10, value=scenario.roi_percent).number_format = '0.0"%"'
            ws.cell(row=row, column=11, value=scenario.success_probability).number_format = '0%'

            # Color row by scenario type
            fill_color = scenario_colors.get(scenario.scenario_type.value, "FFFFFF")
            for col in range(1, 12):
                ws.cell(row=row, column=col).fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")

            row += 1

        # Column widths
        for col in range(1, 12):
            ws.column_dimensions[get_column_letter(col)].width = 15

        # Add bar chart comparing NPV across scenarios
        chart = BarChart()
        chart.title = "NPV Comparison (3 Years)"
        chart.style = 10
        chart.x_axis.title = "Scenario"
        chart.y_axis.title = "NPV (€)"

        data = Reference(ws, min_col=9, min_row=5, max_row=8)
        cats = Reference(ws, min_col=1, min_row=6, max_row=8)
        chart.add_data(data, titles_from_data=True)
        chart.set_categories(cats)

        ws.add_chart(chart, "A12")

    @staticmethod
    def _build_risk_sheet(ws, risk_register: RiskRegister):
        """Build Sheet 4: Risk Register."""

        # Header
        ws.merge_cells('A1:I1')
        ws['A1'] = "Risk Register"
        ws['A1'].font = Font(size=14, bold=True, color="FFFFFF")
        ws['A1'].fill = PatternFill(start_color=BRAND_COLORS["primary"], end_color=BRAND_COLORS["primary"], fill_type="solid")
        ws['A1'].alignment = Alignment(horizontal='center')

        # Summary
        ws.merge_cells('A3:I3')
        ws['A3'] = f"Total Risks: {risk_register.total_risks} | HIGH Probability: {risk_register.high_risks} | Total Exposure: €{risk_register.total_exposure:,.0f}"
        ws['A3'].font = Font(size=11, bold=True)
        ws['A3'].alignment = Alignment(horizontal='center')
        ws['A3'].fill = PatternFill(start_color=BRAND_COLORS["light_gray"], end_color=BRAND_COLORS["light_gray"], fill_type="solid")

        # Risk matrix
        row = 5
        ws.merge_cells(f'A{row}:D{row}')
        ws[f'A{row}'] = "Risk Matrix (Probability × Impact)"
        ws[f'A{row}'].font = Font(size=12, bold=True)
        row += 2

        matrix_headers = ["Probability \\ Impact", "LOW", "MEDIUM", "HIGH"]
        for col_idx, header in enumerate(matrix_headers, start=1):
            cell = ws.cell(row=row, column=col_idx, value=header)
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')

        row += 1
        for prob_level in ["HIGH", "MEDIUM", "LOW"]:
            ws.cell(row=row, column=1, value=prob_level).font = Font(bold=True)
            for col_idx, impact_level in enumerate(["low", "medium", "high"], start=2):
                count = risk_register.risk_matrix[prob_level.lower()][impact_level]
                cell = ws.cell(row=row, column=col_idx, value=count)
                cell.alignment = Alignment(horizontal='center')
                # Color coding (green → yellow → red)
                if count == 0:
                    cell.fill = PatternFill(start_color="D1FAE5", end_color="D1FAE5", fill_type="solid")
                elif count <= 2:
                    cell.fill = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")
                else:
                    cell.fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
            row += 1

        # Risk table
        row += 2
        ws[f'A{row}'] = "Risk Details"
        ws[f'A{row}'].font = Font(size=12, bold=True)
        row += 2

        headers = ["ID", "Category", "Risk Title", "Probability", "Impact (€)", "Score", "Mitigation", "Owner", "Status"]
        for col_idx, header in enumerate(headers, start=1):
            cell = ws.cell(row=row, column=col_idx, value=header)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color=BRAND_COLORS["gray"], end_color=BRAND_COLORS["gray"], fill_type="solid")

        row += 1
        sorted_risks = sorted(risk_register.risks, key=lambda r: r.risk_score, reverse=True)

        for risk in sorted_risks:
            ws.cell(row=row, column=1, value=risk.risk_id)
            ws.cell(row=row, column=2, value=risk.category.value.title())
            ws.cell(row=row, column=3, value=risk.title)
            ws.cell(row=row, column=4, value=f"{risk.probability.value.upper()} ({risk.probability_percent:.0f}%)")
            ws.cell(row=row, column=5, value=risk.impact_eur).number_format = '€#,##0'
            ws.cell(row=row, column=6, value=risk.risk_score).number_format = '0.0'
            ws.cell(row=row, column=7, value=risk.mitigation_strategy)
            ws.cell(row=row, column=8, value=risk.owner)
            ws.cell(row=row, column=9, value=risk.status)

            row += 1

        # Column widths
        ws.column_dimensions['A'].width = 8
        ws.column_dimensions['B'].width = 15
        ws.column_dimensions['C'].width = 35
        ws.column_dimensions['D'].width = 18
        ws.column_dimensions['E'].width = 12
        ws.column_dimensions['F'].width = 8
        ws.column_dimensions['G'].width = 50
        ws.column_dimensions['H'].width = 20
        ws.column_dimensions['I'].width = 12

    @staticmethod
    def _build_gantt_sheet(ws, gantt_data: Dict):
        """Build Sheet 5: Implementation Timeline (Gantt)."""

        # Header
        ws.merge_cells('A1:F1')
        ws['A1'] = "Implementation Timeline (Gantt Chart)"
        ws['A1'].font = Font(size=14, bold=True, color="FFFFFF")
        ws['A1'].fill = PatternFill(start_color=BRAND_COLORS["primary"], end_color=BRAND_COLORS["primary"], fill_type="solid")
        ws['A1'].alignment = Alignment(horizontal='center')

        # Table headers
        headers = ["Milestone", "Start Date", "End Date", "Duration (days)", "Owner", "Status"]
        row = 3
        for col_idx, header in enumerate(headers, start=1):
            cell = ws.cell(row=row, column=col_idx, value=header)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color=BRAND_COLORS["gray"], end_color=BRAND_COLORS["gray"], fill_type="solid")

        # Data rows (placeholder - will be populated by GanttService)
        row = 4
        milestones = gantt_data.get("milestones", [])

        for milestone in milestones:
            ws.cell(row=row, column=1, value=milestone.get("title", ""))
            ws.cell(row=row, column=2, value=milestone.get("start_date", "")).number_format = 'YYYY-MM-DD'
            ws.cell(row=row, column=3, value=milestone.get("end_date", "")).number_format = 'YYYY-MM-DD'
            ws.cell(row=row, column=4, value=milestone.get("duration_days", 0))
            ws.cell(row=row, column=5, value=milestone.get("owner", ""))
            ws.cell(row=row, column=6, value=milestone.get("status", "Pending"))

            # Status color coding
            status = milestone.get("status", "Pending")
            if status == "Completed":
                ws.cell(row=row, column=6).fill = PatternFill(start_color=BRAND_COLORS["success"], end_color=BRAND_COLORS["success"], fill_type="solid")
            elif status == "In Progress":
                ws.cell(row=row, column=6).fill = PatternFill(start_color=BRAND_COLORS["warning"], end_color=BRAND_COLORS["warning"], fill_type="solid")

            row += 1

        # Column widths
        ws.column_dimensions['A'].width = 40
        for col in ['B', 'C']:
            ws.column_dimensions[col].width = 15
        ws.column_dimensions['D'].width = 15
        ws.column_dimensions['E'].width = 20
        ws.column_dimensions['F'].width = 15
