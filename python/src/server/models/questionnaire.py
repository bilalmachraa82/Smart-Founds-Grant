"""
Diagnostic Questionnaire Models for Grant Applications

Based on IFIC McKinsey-level best practices:
- 20 structured questions across 5 sections
- Auto-calculated fields (investment_range, company_size)
- Pydantic validation for data integrity
- Integration with RAG query construction

Usage:
    questionnaire = DiagnosticQuestionnaire(
        company_name="CodeLab Portugal",
        nif="123456789",
        ...
    )

    # Auto-fill from NIF via data sources
    enriched = await DataSourcesService.enrich(questionnaire)
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, validator


# ===== ENUMS =====

# Category-Specific Tech Stack Enums (v7.0 Fix)
class EmailProvider(str, Enum):
    """Email systems used by Portuguese SMEs"""
    GMAIL = "gmail"
    MICROSOFT_365 = "microsoft_365"
    ZOHO_MAIL = "zoho_mail"
    CUSTOM_DOMAIN = "custom_domain"
    OTHER = "other"
    NONE = "none"


class CloudStorage(str, Enum):
    """Cloud storage solutions"""
    GOOGLE_DRIVE = "google_drive"
    ONEDRIVE = "onedrive"
    DROPBOX = "dropbox"
    LOCAL_NAS = "local_nas"
    OTHER = "other"
    NONE = "none"


class ProductivitySuite(str, Enum):
    """Office productivity suites"""
    MICROSOFT_365 = "microsoft_365"
    GOOGLE_WORKSPACE = "google_workspace"
    LIBREOFFICE = "libreoffice"
    APPLE_IWORK = "apple_iwork"
    OTHER = "other"
    NONE = "none"


class CRMSystem(str, Enum):
    """Customer relationship management systems"""
    SALESFORCE = "salesforce"
    HUBSPOT = "hubspot"
    PIPEDRIVE = "pipedrive"
    ZOHO_CRM = "zoho_crm"
    EXCEL_SHEETS = "excel_sheets"
    OTHER = "other"
    NONE = "none"


class ProjectManagement(str, Enum):
    """Project management tools"""
    TRELLO = "trello"
    ASANA = "asana"
    MONDAY = "monday"
    JIRA = "jira"
    MICROSOFT_PROJECT = "microsoft_project"
    CLICKUP = "clickup"
    NOTION = "notion"
    OTHER = "other"
    NONE = "none"


class CommunicationPlatform(str, Enum):
    """Team communication platforms"""
    MICROSOFT_TEAMS = "microsoft_teams"
    SLACK = "slack"
    WHATSAPP_BUSINESS = "whatsapp_business"
    ZOOM = "zoom"
    GOOGLE_MEET = "google_meet"
    DISCORD = "discord"
    OTHER = "other"
    NONE = "none"


class CompanySize(str, Enum):
    """PME classification by employee count"""
    MICRO = "micro"          # < 10 employees
    SMALL = "small"          # 10-49 employees
    MEDIUM = "medium"        # 50-249 employees


class InvestmentRange(str, Enum):
    """Investment tier for budget optimization"""
    TIER_1 = "20k-50k"
    TIER_2 = "50k-100k"
    TIER_3 = "100k-200k"
    TIER_4 = "200k-500k"


class IntensityLevel(str, Enum):
    """AI usage intensity level"""
    LIGHT = "light"           # Occasional use
    MODERATE = "moderate"     # Regular use
    INTENSE = "intense"       # Daily intensive use
    MISSION_CRITICAL = "mission_critical"  # Core business dependency


class IndustrySector(str, Enum):
    """Industry sectors for CAE mapping"""
    TECHNOLOGY = "technology"
    CONSULTING = "consulting"
    MANUFACTURING = "manufacturing"
    RETAIL = "retail"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    FINANCE = "finance"
    OTHER = "other"


class UseCase(str, Enum):
    """AI/Automation use cases"""
    CUSTOMER_SERVICE = "customer_service"
    AUTOMATION = "automation"
    ANALYTICS = "analytics"
    CONTENT_CREATION = "content_creation"
    CODE_ASSISTANCE = "code_assistance"
    RESEARCH = "research"
    MARKETING = "marketing"
    SALES = "sales"
    HR = "hr"
    OTHER = "other"


# ===== MAIN MODEL =====

class DiagnosticQuestionnaire(BaseModel):
    """
    20-question intake questionnaire for personalized grant recommendations.

    Sections:
        A. Tech Stack (Q1-4): Ecosystem identification
        B. Company Profile (Q5-10): Sizing, CAE, revenue
        C. Use Cases (Q11-13): Priorities, intensity, compliance
        D. Budget (Q14-17): Investment range, current tools
        E. Training (Q18-20): Formação needs, partner preference

    Auto-calculated:
        - company_size (from num_employees)
        - investment_range (from desired_investment)
    """

    # ===== SECTION A: TECH STACK (Q1-6) - v7.0 Fixed =====

    email_system: EmailProvider = Field(
        ...,
        description="Q1: Sistema de email principal (Gmail, Outlook, Zoho, etc)"
    )

    cloud_storage: CloudStorage = Field(
        ...,
        description="Q2: Armazenamento cloud (Google Drive, OneDrive, Dropbox, etc)"
    )

    productivity_suite: ProductivitySuite = Field(
        ...,
        description="Q3: Suite de produtividade (Microsoft 365, Google Workspace, etc)"
    )

    crm_system: CRMSystem = Field(
        ...,
        description="Q4: Sistema CRM (Salesforce, HubSpot, Pipedrive, etc)"
    )

    project_management: ProjectManagement = Field(
        ...,
        description="Q5: Gestão de projetos (Trello, Asana, Jira, etc)"
    )

    communication_platform: CommunicationPlatform = Field(
        ...,
        description="Q6: Plataforma de comunicação (Teams, Slack, Zoom, etc)"
    )

    # ===== SECTION B: COMPANY PROFILE (Q5-10) =====

    company_name: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Q5: Nome completo da empresa"
    )

    nif: str = Field(
        ...,
        min_length=9,
        max_length=9,
        pattern=r"^\d{9}$",
        description="Q6: NIF (9 dígitos) - trigger auto-fill via eInforma API"
    )

    cae_code: str = Field(
        ...,
        min_length=5,
        max_length=5,
        description="Q7: CAE principal (5 dígitos, ex: 62010)"
    )

    num_employees: int = Field(
        ...,
        ge=1,
        le=249,
        description="Q8: Número de colaboradores (1-249 para PME)"
    )

    annual_revenue: float = Field(
        ...,
        ge=0,
        le=50_000_000,
        description="Q9: Faturação anual em € (máximo €50M para PME)"
    )

    industry_sector: IndustrySector = Field(
        ...,
        description="Q10: Setor de atividade principal"
    )

    # Auto-calculated fields
    company_size: Optional[CompanySize] = Field(
        None,
        description="Auto-calculated: Micro/Small/Medium based on num_employees"
    )

    # ===== SECTION C: USE CASES & NEEDS (Q11-13) =====

    use_cases: List[str] = Field(
        ...,
        min_items=1,
        max_items=3,
        description="Q11: Top 3 casos uso IA prioritários (coding, content, data analysis, research, chatbots, design)"
    )

    intensity_level: IntensityLevel = Field(
        ...,
        description="Q12: Intensidade uso IA esperada (light/moderate/intense/mission-critical)"
    )

    rgpd_sensitive_data: bool = Field(
        ...,
        description="Q13: Processa dados sensíveis RGPD? (saúde, financeiros, crianças)"
    )

    # ===== SECTION D: BUDGET & CURRENT STATE (Q14-17) =====

    desired_investment: float = Field(
        ...,
        ge=20_000,
        le=500_000,
        description="Q14: Montante investimento desejado em € (€20k-500k Aviso 03/C05)"
    )

    current_tools_paid: bool = Field(
        ...,
        description="Q15: Já utiliza ferramentas IA pagas? (não / free only / algumas pagas / enterprise)"
    )

    current_tools_list: Optional[List[str]] = Field(
        default=[],
        description="Q16: Se sim em Q15, liste ferramentas atuais (ex: ChatGPT Plus, GitHub Copilot)"
    )

    budget_per_user_month: Optional[float] = Field(
        None,
        ge=0,
        le=200,
        description="Q17: Budget disponível por utilizador/mês em € (se conhecido)"
    )

    # Auto-calculated fields
    investment_range: Optional[InvestmentRange] = Field(
        None,
        description="Auto-calculated: Investment tier (20k-50k, 50k-100k, etc.)"
    )

    # ===== SECTION E: TRAINING & PARTNERS (Q18-20) =====

    training_priority: bool = Field(
        ...,
        description="Q18: Formação equipa é prioridade? (>50% precisa upskilling IA)"
    )

    training_areas: List[str] = Field(
        default=[],
        description="Q19: Áreas formação desejadas (AI fundamentals, prompt engineering, Azure AI, RGPD, ética)"
    )

    num_employees_training: Optional[int] = Field(
        None,
        ge=0,
        description="Q20: Número colaboradores para formação (se training_priority=True)"
    )

    preferred_training_partner: Optional[str] = Field(
        None,
        description="Q21: Parceiro formação preferido (resposta aberta, ex: AiParaTi, Microsoft Learn)"
    )

    # ===== METADATA =====

    has_dev_team: bool = Field(
        default=False,
        description="Derived: Tem equipa desenvolvimento? (inferido de use_cases contém 'coding')"
    )

    num_developers: Optional[int] = Field(
        None,
        ge=0,
        description="Se has_dev_team=True, quantos developers?"
    )

    project_duration_months: int = Field(
        default=12,
        ge=6,
        le=12,
        description="Duração prevista projeto em meses (6-12, máximo 12 Aviso 03/C05)"
    )

    # ===== VALIDATORS =====

    @validator('company_size', pre=True, always=True)
    def calculate_company_size(cls, v, values):
        """Auto-calculate company size from num_employees"""
        num_employees = values.get('num_employees')
        if num_employees is None:
            return None

        if num_employees < 10:
            return CompanySize.MICRO
        elif num_employees < 50:
            return CompanySize.SMALL
        else:
            return CompanySize.MEDIUM

    @validator('investment_range', pre=True, always=True)
    def calculate_investment_range(cls, v, values):
        """Auto-calculate investment tier from desired_investment"""
        amount = values.get('desired_investment')
        if amount is None:
            return None

        if amount < 50_000:
            return InvestmentRange.TIER_1
        elif amount < 100_000:
            return InvestmentRange.TIER_2
        elif amount < 200_000:
            return InvestmentRange.TIER_3
        else:
            return InvestmentRange.TIER_4

    @validator('has_dev_team', pre=True, always=True)
    def infer_has_dev_team(cls, v, values):
        """Infer dev team from use_cases"""
        use_cases = values.get('use_cases', [])
        return any('coding' in uc.lower() or 'development' in uc.lower() for uc in use_cases)

    @validator('num_employees_training')
    def validate_training_count(cls, v, values):
        """If training_priority=True, num_employees_training must be > 0"""
        training_priority = values.get('training_priority', False)
        if training_priority and (v is None or v <= 0):
            raise ValueError("Se training_priority=True, num_employees_training deve ser > 0")
        return v

    @validator('nif')
    def validate_nif_checksum(cls, v):
        """Validate Portuguese NIF checksum algorithm"""
        if len(v) != 9 or not v.isdigit():
            raise ValueError("NIF deve ter 9 dígitos numéricos")

        # Portuguese NIF checksum validation
        # https://pt.wikipedia.org/wiki/N%C3%BAmero_de_identifica%C3%A7%C3%A3o_fiscal
        digits = [int(d) for d in v]
        check = sum(digits[i] * (9 - i) for i in range(8)) % 11

        if check == 0 or check == 1:
            expected = 0
        else:
            expected = 11 - check

        if digits[8] != expected:
            raise ValueError(f"NIF checksum inválido (esperado {expected}, obtido {digits[8]})")

        return v

    class Config:
        """Pydantic config"""
        use_enum_values = True
        validate_assignment = True
        json_schema_extra = {
            "example": {
                "email_system": "gmail",
                "cloud_storage": "google_drive",
                "productivity_suite": "microsoft_365",
                "crm_system": "hubspot",
                "project_management": "trello",
                "communication_platform": "microsoft_teams",
                "company_name": "CodeLab Portugal Lda",
                "nif": "123456789",
                "cae_code": "62010",
                "num_employees": 18,
                "annual_revenue": 980000,
                "industry_sector": "technology",
                "use_cases": ["coding", "documentation", "client_chatbot"],
                "intensity_level": "intense",
                "rgpd_sensitive_data": False,
                "desired_investment": 95000,
                "current_tools_paid": True,
                "current_tools_list": ["ChatGPT Plus", "GitHub Copilot"],
                "budget_per_user_month": 30,
                "training_priority": True,
                "training_areas": ["AI fundamentals", "Prompt engineering", "Azure AI"],
                "num_employees_training": 15,
                "preferred_training_partner": "AiParaTi",
                "num_developers": 5,
                "project_duration_months": 12
            }
        }


# ===== RESPONSE MODELS =====

class CompanyData(BaseModel):
    """
    Enriched company data from external sources (eInforma API, Racius).
    Used to auto-fill questionnaire fields from NIF.
    """
    nif: str
    legal_name: str
    cae_primary: str
    address: str
    revenue_estimate: Optional[float] = None
    employees_estimate: Optional[int] = None
    founded_date: Optional[str] = None
    risk_rating: Optional[str] = None  # eInforma failure score
    source: str  # "einforma", "racius", "manual"


class QuestionnaireResponse(BaseModel):
    """API response after questionnaire submission"""
    questionnaire_id: str
    company_name: str
    investment_range: str
    status: str  # "pending_processing", "rag_search_completed", "recommendations_ready"
    message: str
