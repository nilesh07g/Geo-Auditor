"""Pydantic models for GEO Auditor API - aligned with PROJECT_BLUEPRINT.md Section 12."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Severity(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"


class Confidence(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class Impact(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class Effort(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class Grade(str, Enum):
    strong = "Strong"
    moderate_gaps = "Moderate gaps"
    at_risk = "At Risk"
    critical = "Critical"


CHECK_WEIGHTS: Dict[str, int] = {
    "crawler_access": 20,
    "entity_clarity": 25,
    "structured_data": 25,
    "answer_ready": 30,
}

CHECK_NAMES: Dict[str, str] = {
    "crawler_access": "AI Crawler Access",
    "entity_clarity": "Entity Clarity",
    "structured_data": "Structured Data",
    "answer_ready": "Answer-Ready Content",
}


class NavLink(BaseModel):
    text: str
    href: str


class PageData(BaseModel):
    url: str
    status_code: int = 200
    html: str = ""
    title: str = ""
    h1s: List[str] = Field(default_factory=list)
    h2s: List[str] = Field(default_factory=list)
    meta_description: str = ""
    json_ld_schemas: List[Dict[str, Any]] = Field(default_factory=list)
    body_text: str = ""
    is_js_shell: bool = False
    links: List[NavLink] = Field(default_factory=list)


class Limitation(BaseModel):
    description: str


class CrawlResult(BaseModel):
    target_url: str
    homepage: Optional[PageData] = None
    about_page: Optional[PageData] = None
    service_page: Optional[PageData] = None
    robots_txt_content: Optional[str] = None
    robots_txt_status: int = 404
    llms_txt_content: Optional[str] = None
    llms_txt_status: int = 404
    pages_analyzed: List[str] = Field(default_factory=list)
    limitations: List[Limitation] = Field(default_factory=list)


class Finding(BaseModel):
    id: Optional[str] = None
    title: str
    severity: Severity
    confidence: Confidence
    evidence: str
    why_it_matters: str
    recommended_fix: str
    page_url: Optional[str] = None
    check_id: str


class CheckResult(BaseModel):
    check_id: str
    check_name: str
    score: int
    max_score: int
    weight: int
    weighted_score: int
    findings: List[Finding] = Field(default_factory=list)


class ScoreBreakdownItem(BaseModel):
    check_id: str
    check_name: str
    score: int
    max_score: int
    weight: int
    weighted_score: int


class ActionPlanItem(BaseModel):
    rank: int
    action: str
    impact: Impact
    effort: Effort
    source_finding_title: Optional[str] = None


class AuditRequest(BaseModel):
    url: str
    business_name: Optional[str] = None


class AuditResponse(BaseModel):
    url: str
    business_name: Optional[str] = None
    audited_at: datetime = Field(default_factory=datetime.utcnow)
    geo_score: int = Field(ge=0, le=100)
    grade: Grade
    executive_summary: str
    aha_line: str
    score_breakdown: List[ScoreBreakdownItem]
    check_results: List[CheckResult]
    action_plan: List[ActionPlanItem] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    limitations: List[Limitation] = Field(default_factory=list)
    pages_analyzed: List[str] = Field(default_factory=list)


class AIVisibilityPromptResult(BaseModel):
    prompt: str
    mentioned: bool
    cited: bool
    response_excerpt: str
    competitors_mentioned: List[str] = Field(default_factory=list)


class AIVisibilityRequest(BaseModel):
    url: str
    business_name: str


class AIVisibilityResponse(BaseModel):
    url: str
    business_name: str
    results: List[AIVisibilityPromptResult] = Field(default_factory=list)
    experimental: bool = True
    note: str = "Experimental - not included in your GEO Score"
