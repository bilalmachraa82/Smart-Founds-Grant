"""
Scoring Calculator Service

Calculates Merit Score (MP) and identifies quick wins for score optimization.
Implements IFIC formula: MP = 0.50 × A + 0.50 × B

Scoring Formula:
    MP = 0.50 × A + 0.50 × B

    Where:
        A = Coerência investimentos (0-5 scale)
            - Investment justification matrix quality
            - Timeline realism (Gantt chart)
            - Risk mitigation strategies
            - Technical specifications completeness

        B = Impacto (0-5 scale)
            B = (B1 + B2) / 2

            B1 = Criação emprego (0-5 scale)
                - 0 jobs → 1 point
                - 1 job → 2 points
                - 2+ jobs → 5 points (maximum)

            B2 = Crescimento VAB (0-5 scale)
                - <5% growth → 1 point
                - 5-7% growth → 2 points
                - 7-10% growth → 3 points
                - 10-12% growth → 4 points
                - >12% growth → 5 points

Example:
    scoring = ScoringCalculator.calculate_current_score(project_data)
    # Returns: ScoringBreakdown(
    #     A_coherence=3.5,
    #     B1_employment=2,
    #     B2_vab_growth=3,
    #     B_impact=2.5,
    #     MP_total=3.0,
    #     MP_out_of_10=6.0,
    #     class_rating="B"
    # )

    quick_wins = ScoringCalculator.identify_quick_wins(scoring, project_data)
    # Returns: [
    #     QuickWin(action="Contratar 2 RH", mp_increase=0.25, roi_per_euro=inf),
    #     QuickWin(action="Investment Matrix + Gantt", mp_increase=0.50, roi_per_euro=inf),
    #     ...
    # ]
"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from enum import Enum

from ..config.logfire_config import get_logger

logger = get_logger(__name__)


# ===== MODELS =====

class ClassRating(str, Enum):
    """Merit score classification"""
    A_PLUS = "A+"      # 9.0-10.0
    A = "A"            # 8.0-8.9
    B_PLUS = "B+"      # 7.0-7.9
    B = "B"            # 6.0-6.9
    C = "C"            # 5.0-5.9
    D = "D"            # 4.0-4.9
    E = "E"            # 0.0-3.9


class ScoringBreakdown(BaseModel):
    """Detailed scoring breakdown"""

    # Critério A: Coerência
    A_coherence: float = Field(..., ge=0, le=5, description="Coerência investimentos (0-5)")
    A_details: Optional[Dict[str, float]] = Field(None, description="Sub-scores: matrix, gantt, risk, specs")

    # Critério B1: Emprego
    B1_employment: float = Field(..., ge=0, le=5, description="Criação emprego (0-5)")
    jobs_created: int = Field(..., description="Number of permanent jobs created")

    # Critério B2: VAB Growth
    B2_vab_growth: float = Field(..., ge=0, le=5, description="Crescimento VAB (0-5)")
    vab_growth_percent: float = Field(..., description="VAB growth % (e.g., 10.5 for 10.5%)")

    # Critério B: Impacto
    B_impact: float = Field(..., ge=0, le=5, description="Impacto (B1 + B2) / 2")

    # Merit Score
    MP_total: float = Field(..., ge=0, le=5, description="MP = 0.50×A + 0.50×B")
    MP_out_of_10: float = Field(..., ge=0, le=10, description="MP converted to 0-10 scale")
    class_rating: ClassRating = Field(..., description="Classification (A+, A, B+, B, C, D, E)")

    # Probability
    approval_probability: float = Field(..., ge=0, le=100, description="Estimated approval probability %")


class QuickWin(BaseModel):
    """Single optimization action"""

    id: str = Field(..., description="Unique ID (e.g., 'QW1')")
    action: str = Field(..., description="Action description")
    criteria_affected: str = Field(..., description="Which criteria improves (A, B1, or B2)")

    # Scoring impact
    current_score: float = Field(..., description="Current score in affected criteria")
    potential_score: float = Field(..., description="Potential score after action")
    score_increase: float = Field(..., description="Score increase in criteria")
    mp_increase: float = Field(..., description="Overall MP increase (weighted)")

    # Implementation
    implementation_cost: float = Field(..., description="Implementation cost (€), 0 if documentation only")
    roi_per_euro: float = Field(..., description="MP points per € invested (inf if cost=0)")
    timeline: str = Field(..., description="Implementation timeline (e.g., '1-2 semanas')")

    # Details
    details: str = Field(..., description="Detailed explanation of action")


class ProjectData(BaseModel):
    """Project data for scoring calculation"""

    # Investment
    investment_total: float = Field(..., description="Total investment (€)")

    # Employment
    jobs_created: int = Field(0, description="Permanent jobs created")

    # VAB growth
    vab_growth_percent: float = Field(0, description="Expected VAB growth %")
    vab_baseline: float = Field(..., description="Baseline VAB (€)")

    # Coherence indicators (for A score)
    has_investment_matrix: bool = Field(False, description="Has investment justification matrix?")
    has_gantt_chart: bool = Field(False, description="Has detailed Gantt chart?")
    has_risk_register: bool = Field(False, description="Has risk register with mitigation?")
    has_technical_specs: bool = Field(False, description="Has technical specifications?")
    has_3_quotes: bool = Field(False, description="Has 3 quotes for major expenses?")

    # Duration
    duration_months: int = Field(12, ge=6, le=12, description="Project duration (months)")


# ===== SCORING CALCULATOR SERVICE =====

class ScoringCalculator:
    """
    Merit score calculator and optimizer.

    Scoring logic (IFIC pattern):
        MP = 0.50 × A + 0.50 × B

        A (Coerência, 0-5):
            - Investment matrix: 1.0 point
            - Gantt chart: 1.0 point
            - Risk register: 1.0 point
            - Technical specs: 1.0 point
            - 3 quotes: 1.0 point
            MAX: 5.0 points

        B1 (Emprego, 0-5):
            - 0 jobs: 1.0 point (minimum)
            - 1 job: 2.0 points
            - 2+ jobs: 5.0 points (maximum)

        B2 (VAB Growth, 0-5):
            - <5%: 1.0 point
            - 5-7%: 2.0 points
            - 7-10%: 3.0 points
            - 10-12%: 4.0 points
            - >12%: 5.0 points

        B = (B1 + B2) / 2

        MP = 0.50 × A + 0.50 × B (scale 0-5, multiply by 2 for 0-10)
    """

    @staticmethod
    def calculate_current_score(project: ProjectData) -> ScoringBreakdown:
        """
        Calculate current merit score from project data.

        Args:
            project: ProjectData with investment, jobs, VAB, coherence indicators

        Returns:
            ScoringBreakdown with detailed scores and classification
        """

        # ===== CRITÉRIO A: COERÊNCIA INVESTIMENTOS =====

        A_score = 0.0
        A_details = {}

        if project.has_investment_matrix:
            A_score += 1.0
            A_details["investment_matrix"] = 1.0
        else:
            A_details["investment_matrix"] = 0.0

        if project.has_gantt_chart:
            A_score += 1.0
            A_details["gantt_chart"] = 1.0
        else:
            A_details["gantt_chart"] = 0.0

        if project.has_risk_register:
            A_score += 1.0
            A_details["risk_register"] = 1.0
        else:
            A_details["risk_register"] = 0.0

        if project.has_technical_specs:
            A_score += 1.0
            A_details["technical_specs"] = 1.0
        else:
            A_details["technical_specs"] = 0.0

        if project.has_3_quotes:
            A_score += 1.0
            A_details["3_quotes"] = 1.0
        else:
            A_details["3_quotes"] = 0.0

        # ===== CRITÉRIO B1: CRIAÇÃO EMPREGO =====

        B1_score = ScoringCalculator._score_employment(project.jobs_created)

        # ===== CRITÉRIO B2: CRESCIMENTO VAB =====

        B2_score = ScoringCalculator._score_vab_growth(project.vab_growth_percent)

        # ===== CRITÉRIO B: IMPACTO =====

        B_score = (B1_score + B2_score) / 2

        # ===== MERIT SCORE (MP) =====

        MP = 0.50 * A_score + 0.50 * B_score
        MP_out_of_10 = MP * 2

        # ===== CLASSIFICATION =====

        class_rating = ScoringCalculator._get_class(MP_out_of_10)

        # ===== APPROVAL PROBABILITY =====

        # Empirical formula (IFIC data):
        # 9.0+: 95%
        # 8.0-8.9: 85%
        # 7.0-7.9: 75%
        # 6.0-6.9: 60%
        # 5.0-5.9: 40%
        # 4.0-4.9: 20%
        # <4.0: 10%

        if MP_out_of_10 >= 9.0:
            probability = 95
        elif MP_out_of_10 >= 8.0:
            probability = 85
        elif MP_out_of_10 >= 7.0:
            probability = 75
        elif MP_out_of_10 >= 6.0:
            probability = 60
        elif MP_out_of_10 >= 5.0:
            probability = 40
        elif MP_out_of_10 >= 4.0:
            probability = 20
        else:
            probability = 10

        logger.info(
            f"Scoring calculated: MP={MP:.2f} ({MP_out_of_10:.1f}/10), Class {class_rating.value}, "
            f"Probability {probability}% | A={A_score:.1f}, B1={B1_score:.1f}, B2={B2_score:.1f}, B={B_score:.1f}"
        )

        return ScoringBreakdown(
            A_coherence=A_score,
            A_details=A_details,
            B1_employment=B1_score,
            jobs_created=project.jobs_created,
            B2_vab_growth=B2_score,
            vab_growth_percent=project.vab_growth_percent,
            B_impact=B_score,
            MP_total=MP,
            MP_out_of_10=MP_out_of_10,
            class_rating=class_rating,
            approval_probability=probability
        )

    @staticmethod
    def _score_employment(jobs_created: int) -> float:
        """
        Score employment creation (B1 criteria).

        Logic:
            - 0 jobs: 1.0 point (minimum)
            - 1 job: 2.0 points
            - 2+ jobs: 5.0 points (maximum)
        """

        if jobs_created == 0:
            return 1.0
        elif jobs_created == 1:
            return 2.0
        else:  # 2+ jobs
            return 5.0

    @staticmethod
    def _score_vab_growth(vab_growth_percent: float) -> float:
        """
        Score VAB growth (B2 criteria).

        Logic:
            - <5%: 1.0 point
            - 5-7%: 2.0 points
            - 7-10%: 3.0 points
            - 10-12%: 4.0 points
            - >12%: 5.0 points
        """

        if vab_growth_percent < 5:
            return 1.0
        elif vab_growth_percent < 7:
            return 2.0
        elif vab_growth_percent < 10:
            return 3.0
        elif vab_growth_percent < 12:
            return 4.0
        else:  # >= 12%
            return 5.0

    @staticmethod
    def _get_class(mp_out_of_10: float) -> ClassRating:
        """
        Get classification from MP score (0-10 scale).
        """

        if mp_out_of_10 >= 9.0:
            return ClassRating.A_PLUS
        elif mp_out_of_10 >= 8.0:
            return ClassRating.A
        elif mp_out_of_10 >= 7.0:
            return ClassRating.B_PLUS
        elif mp_out_of_10 >= 6.0:
            return ClassRating.B
        elif mp_out_of_10 >= 5.0:
            return ClassRating.C
        elif mp_out_of_10 >= 4.0:
            return ClassRating.D
        else:
            return ClassRating.E

    @staticmethod
    def identify_quick_wins(
        current: ScoringBreakdown,
        project: ProjectData,
        max_wins: int = 3
    ) -> List[QuickWin]:
        """
        Identify top optimization actions (IFIC pattern).

        Quick wins are sorted by:
            1. MP increase (highest first)
            2. ROI per € (free improvements prioritized)
            3. Timeline (faster first)

        Args:
            current: Current scoring breakdown
            project: Project data
            max_wins: Maximum number of wins to return (default 3)

        Returns:
            List of QuickWin objects sorted by impact
        """

        wins = []

        # ===== QUICK WIN 1: CRIAR 2 RH DEDICADOS (B1) =====

        if project.jobs_created < 2:
            jobs_gap = 2 - project.jobs_created
            B1_potential = 5.0  # Maximum score (2+ jobs)
            B1_increase = B1_potential - current.B1_employment
            B_increase = B1_increase / 2  # B1 is 50% of B
            MP_increase = 0.50 * B_increase  # B is 50% of MP

            implementation_cost = 160000  # €80k × 2 positions
            roi_per_euro = MP_increase / implementation_cost

            wins.append(QuickWin(
                id="QW1",
                action=f"Contratar {jobs_gap} RH dedicado{'s' if jobs_gap > 1 else ''} (AI/ML Engineer + Data Scientist)",
                criteria_affected="B1 (Criação Emprego)",
                current_score=current.B1_employment,
                potential_score=B1_potential,
                score_increase=B1_increase,
                mp_increase=MP_increase,
                implementation_cost=implementation_cost,
                roi_per_euro=roi_per_euro,
                timeline="3-6 meses (recruitment + onboarding)",
                details=(
                    f"Contratar {jobs_gap} posição/posições permanente(s) dedicada(s) ao projeto 24 meses. "
                    f"B1 score: {current.B1_employment:.1f} → {B1_potential:.1f} (+{B1_increase:.1f} pontos). "
                    f"MP increase: +{MP_increase:.2f} pontos ({current.MP_out_of_10:.1f} → {current.MP_out_of_10 + MP_increase * 2:.1f}/10). "
                    f"Custo: €{implementation_cost:,.0f} elegível (€80k cap por posição). "
                    f"ROI: {roi_per_euro * 1000:.2f} MP points per €1,000 invested."
                )
            ))

        # ===== QUICK WIN 2: FORTALECER COERÊNCIA INVESTIMENTOS (A) =====

        A_potential = 5.0  # Maximum score (all 5 elements)
        A_increase = A_potential - current.A_coherence
        MP_increase = 0.50 * A_increase  # A is 50% of MP

        if A_increase > 0:
            missing_elements = []
            if not project.has_investment_matrix:
                missing_elements.append("Investment Justification Matrix (cada € → capability → KPI)")
            if not project.has_gantt_chart:
                missing_elements.append("Gantt Chart 24 meses (5 workstreams, 20 milestones)")
            if not project.has_risk_register:
                missing_elements.append("Risk Register (7 risks + mitigation)")
            if not project.has_technical_specs:
                missing_elements.append("Technical Specifications (equipamentos/software)")
            if not project.has_3_quotes:
                missing_elements.append("3 Cotações (despesas principais >€5k)")

            wins.append(QuickWin(
                id="QW2",
                action="Fortalecer documentação coerência investimentos (A)",
                criteria_affected="A (Coerência Investimentos)",
                current_score=current.A_coherence,
                potential_score=A_potential,
                score_increase=A_increase,
                mp_increase=MP_increase,
                implementation_cost=0,  # Documentation only
                roi_per_euro=float('inf'),  # Free improvement!
                timeline="1-2 semanas (documentação)",
                details=(
                    f"Adicionar elementos faltantes coerência: {', '.join(missing_elements)}. "
                    f"A score: {current.A_coherence:.1f} → {A_potential:.1f} (+{A_increase:.1f} pontos). "
                    f"MP increase: +{MP_increase:.2f} pontos ({current.MP_out_of_10:.1f} → {current.MP_out_of_10 + MP_increase * 2:.1f}/10). "
                    f"Custo: €0 (apenas documentação). ROI: INFINITO (free score boost)."
                )
            ))

        # ===== QUICK WIN 3: PROJEÇÕES VAB AMBICIOSAS (B2) =====

        if current.B2_vab_growth < 4.0:  # If not already high
            B2_potential = 4.5  # Target 10-12% VAB growth (realistic, not 5.0)
            B2_increase = B2_potential - current.B2_vab_growth
            B_increase = B2_increase / 2  # B2 is 50% of B
            MP_increase = 0.50 * B_increase  # B is 50% of MP

            target_vab_growth = 11.0  # 11% VAB growth target

            wins.append(QuickWin(
                id="QW3",
                action="Projeções VAB ambiciosas mas fundamentadas (B2)",
                criteria_affected="B2 (Crescimento VAB)",
                current_score=current.B2_vab_growth,
                potential_score=B2_potential,
                score_increase=B2_increase,
                mp_increase=MP_increase,
                implementation_cost=0,  # Financial projections
                roi_per_euro=float('inf'),
                timeline="1 semana (Excel model + benchmarks)",
                details=(
                    f"Financial model 3 anos com VAB growth target {target_vab_growth:.1f}% (vs. atual {project.vab_growth_percent:.1f}%). "
                    f"Fundamentação: ROI quantificado (€X saved productivity + €Y revenue increase), "
                    f"benchmarks industry (cite studies), scenario analysis (conservador/base/otimista). "
                    f"B2 score: {current.B2_vab_growth:.1f} → {B2_potential:.1f} (+{B2_increase:.1f} pontos). "
                    f"MP increase: +{MP_increase:.2f} pontos ({current.MP_out_of_10:.1f} → {current.MP_out_of_10 + MP_increase * 2:.1f}/10). "
                    f"Custo: €0 (projeções financeiras). ROI: INFINITO."
                )
            ))

        # ===== QUICK WIN 4: 3 COTAÇÕES PARA DESPESAS PRINCIPAIS (A sub-element) =====

        if not project.has_3_quotes:
            # This is already covered in QW2, but can be separate if user wants granular
            pass

        # Sort by MP increase (descending), then by ROI (descending)
        wins.sort(key=lambda w: (-w.mp_increase, -w.roi_per_euro if w.roi_per_euro != float('inf') else float('inf')))

        # Return top N wins
        top_wins = wins[:max_wins]

        logger.info(
            f"Identified {len(top_wins)} quick wins: "
            f"{[f'{w.id}: {w.action} (+{w.mp_increase:.2f} MP)' for w in top_wins]}"
        )

        return top_wins

    @staticmethod
    def project_score_after_improvements(
        current: ScoringBreakdown,
        quick_wins: List[QuickWin]
    ) -> ScoringBreakdown:
        """
        Project score after implementing quick wins.

        Args:
            current: Current scoring
            quick_wins: List of quick wins to implement

        Returns:
            Projected ScoringBreakdown after improvements
        """

        total_mp_increase = sum(qw.mp_increase for qw in quick_wins)
        new_mp = current.MP_total + total_mp_increase
        new_mp_out_of_10 = new_mp * 2

        # Recalculate individual components (simplified)
        # In reality, each QW affects specific components

        logger.info(
            f"Projected score after {len(quick_wins)} quick wins: "
            f"MP {current.MP_total:.2f} → {new_mp:.2f} ({current.MP_out_of_10:.1f} → {new_mp_out_of_10:.1f}/10), "
            f"increase +{total_mp_increase:.2f} MP points"
        )

        # Note: This is simplified - in production, recalculate A, B1, B2 individually
        return ScoringBreakdown(
            A_coherence=min(5.0, current.A_coherence + sum(qw.score_increase for qw in quick_wins if "A" in qw.criteria_affected)),
            A_details=current.A_details,
            B1_employment=min(5.0, current.B1_employment + sum(qw.score_increase for qw in quick_wins if "B1" in qw.criteria_affected)),
            jobs_created=current.jobs_created + sum(1 for qw in quick_wins if "B1" in qw.criteria_affected),
            B2_vab_growth=min(5.0, current.B2_vab_growth + sum(qw.score_increase for qw in quick_wins if "B2" in qw.criteria_affected)),
            vab_growth_percent=current.vab_growth_percent,  # Would be updated with new target
            B_impact=min(5.0, current.B_impact + sum(qw.mp_increase for qw in quick_wins) / 0.50),  # Reverse weight
            MP_total=min(5.0, new_mp),
            MP_out_of_10=min(10.0, new_mp_out_of_10),
            class_rating=ScoringCalculator._get_class(min(10.0, new_mp_out_of_10)),
            approval_probability=ScoringCalculator._calculate_probability(min(10.0, new_mp_out_of_10))
        )

    @staticmethod
    def _calculate_probability(mp_out_of_10: float) -> float:
        """Calculate approval probability from MP score"""
        if mp_out_of_10 >= 9.0:
            return 95
        elif mp_out_of_10 >= 8.0:
            return 85
        elif mp_out_of_10 >= 7.0:
            return 75
        elif mp_out_of_10 >= 6.0:
            return 60
        elif mp_out_of_10 >= 5.0:
            return 40
        elif mp_out_of_10 >= 4.0:
            return 20
        else:
            return 10
