"""
Grant Management Feature Module
MCP tools for grant application analysis and optimization
"""

from .grant_tools import (
    GRANT_TOOLS,
    analyze_grant_eligibility,
    optimize_investment_plan,
    generate_professional_documents,
    GrantEligibilityRequest,
    GrantEligibilityResult,
    InvestmentOptimizationRequest,
    OptimizedInvestmentPlan,
    DocumentGenerationRequest,
    GeneratedDocuments,
)

__all__ = [
    "GRANT_TOOLS",
    "analyze_grant_eligibility",
    "optimize_investment_plan",
    "generate_professional_documents",
    "GrantEligibilityRequest",
    "GrantEligibilityResult",
    "InvestmentOptimizationRequest",
    "OptimizedInvestmentPlan",
    "DocumentGenerationRequest",
    "GeneratedDocuments",
]
