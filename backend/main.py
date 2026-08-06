"""FastAPI application entry point - GEO Auditor API."""

import re
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from models import AuditRequest, AuditResponse, AIVisibilityRequest, AIVisibilityResponse, Finding, Severity, Confidence


def is_positive_finding(finding: Finding) -> bool:
    """Return True only for findings that clearly represent positive signals."""
    if finding.severity != Severity.low or finding.confidence != Confidence.high:
        return False

    action_text = (finding.recommended_fix or "").strip().lower()
    if not action_text:
        return False

    positive_markers = (
        "no action required",
        "no action needed",
        "no action necessary",
        "well-formed factual content",
    )
    if any(marker in action_text for marker in positive_markers):
        return True

    return False


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Generative Engine Optimization audit API",
    version=settings.VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)


@app.get("/health")
def health() -> dict[str, str]:
    """Sanity check for README setup."""
    return {"status": "ok", "version": settings.VERSION}


@app.post("/api/audit", response_model=AuditResponse)
async def run_audit(request: AuditRequest):
    """Run a 4-check deterministic GEO audit on a target business URL."""
    from fetcher import crawl_site
    from checks.crawler_access import evaluate_crawler_access
    from checks.entity_clarity import evaluate_entity_clarity
    from checks.structured_data import evaluate_structured_data
    from checks.answer_ready import evaluate_answer_ready
    from scoring import calculate_weighted_geo_score
    from models import Finding, Severity, Confidence, ActionPlanItem, Impact, Effort
    import uuid
    from datetime import datetime

    # Crawl the site
    crawl_result = await crawl_site(request.url)

    # Run all 4 checks
    check1 = evaluate_crawler_access(
        robots_txt_content=crawl_result.robots_txt_content,
        robots_txt_status=crawl_result.robots_txt_status,
        llms_txt_content=crawl_result.llms_txt_content,
        llms_txt_status=crawl_result.llms_txt_status,
        homepage_html=crawl_result.homepage.html if crawl_result.homepage else "",
        target_url=crawl_result.target_url,
    )

    check2 = evaluate_entity_clarity(
        homepage=crawl_result.homepage,
        about_page=crawl_result.about_page,
        service_page=crawl_result.service_page,
        business_name_hint=request.business_name,
    )

    check3 = evaluate_structured_data(
        homepage=crawl_result.homepage,
        about_page=crawl_result.about_page,
        service_page=crawl_result.service_page,
    )

    check4 = evaluate_answer_ready(
        homepage=crawl_result.homepage,
        about_page=crawl_result.about_page,
        service_page=crawl_result.service_page,
    )

    # Calculate overall score and grade
    score_result = calculate_weighted_geo_score([check1, check2, check3, check4])

    # Create executive summary from findings
    all_findings = []
    for check in [check1, check2, check3, check4]:
        all_findings.extend(check.findings)

    critical_findings = [f for f in all_findings if f.severity == Severity.critical]
    high_findings = [f for f in all_findings if f.severity == Severity.high]
    medium_findings = [f for f in all_findings if f.severity == Severity.medium]
    low_findings = [f for f in all_findings if f.severity == Severity.low]

    strengths = []
    for finding in all_findings:
        if is_positive_finding(finding):
            strengths.append(finding.title)

    executive_summary = f"GEO audit completed for {request.url}. "
    if strengths:
        executive_summary += f"Strongest positive signal: {strengths[0]}. "

    if critical_findings:
        executive_summary += f"Highest-impact issue: {critical_findings[0].title}. "
    elif high_findings:
        executive_summary += f"Priority improvement: {high_findings[0].title}. "
    elif medium_findings:
        executive_summary += f"The site shows moderate issues around {medium_findings[0].title}. "
    else:
        executive_summary += "The site has no major issues, but continued content and crawl visibility improvements are recommended. "

    if score_result["overall_score"] >= 80:
        executive_summary += "Overall GEO visibility is strong with only minor optimization opportunities."
    elif score_result["overall_score"] >= 60:
        executive_summary += "Overall visibility is decent, but there are clear opportunities to improve AI extractability."
    elif score_result["overall_score"] >= 40:
        executive_summary += "Overall visibility is at risk without addressing higher-priority technical and content gaps."
    else:
        executive_summary += "Overall visibility is critical and requires prioritized fixes across the audit scope."

    # Create prioritized action plan from findings
    action_plan = []
    seen_actions: set[str] = set()
    severity_order = {
        Severity.critical: 1,
        Severity.high: 2,
        Severity.medium: 3,
        Severity.low: 4,
    }
    def is_actionable_fix(text: str) -> bool:
        if not text:
            return False
        return not bool(re.search(r"\bno action required\b|\bno action needed\b|\bno action necessary\b", text, re.I))

    sorted_findings = sorted(
        all_findings,
        key=lambda f: (severity_order.get(f.severity, 99), f.title, f.recommended_fix)
    )
    for rank, finding in enumerate(sorted_findings, start=1):
        action_text = finding.recommended_fix.strip()
        if not action_text or action_text in seen_actions or not is_actionable_fix(action_text):
            continue
        seen_actions.add(action_text)
        impact = Impact.high if finding.severity in [Severity.critical, Severity.high] else Impact.medium
        effort = Effort.medium if finding.severity in [Severity.critical, Severity.high] else Effort.low
        action_plan.append(ActionPlanItem(
            rank=rank,
            action=action_text if len(action_text) <= 250 else action_text[:250] + "...",
            impact=impact,
            effort=effort,
            source_finding_title=finding.title
        ))
        if len(action_plan) >= 8:
            break

    # Create strengths from positive findings
    strengths = []
    for finding in all_findings:
        if is_positive_finding(finding):
            strengths.append(f"Strong {finding.title}")

    # Create limitations from crawl limitations
    limitations = []
    for lim in crawl_result.limitations:
        limitations.append(lim)

    return AuditResponse(
        url=request.url,
        business_name=request.business_name,
        audited_at=datetime.utcnow(),
        geo_score=score_result["overall_score"],
        grade=score_result["grade"],
        executive_summary=executive_summary,
        aha_line=(critical_findings[0].why_it_matters if critical_findings else
              high_findings[0].why_it_matters if high_findings else
              medium_findings[0].why_it_matters if medium_findings else
              (f"Strong content observed: {strengths[0]}." if strengths else "No major issues detected in the deterministic audit.")),
        score_breakdown=[
            {
                "check_id": c.check_id,
                "check_name": c.check_name,
                "score": c.score,
                "max_score": c.max_score,
                "weight": c.weight,
                "weighted_score": c.weighted_score,
            }
            for c in [check1, check2, check3, check4]
        ],
        check_results=[check1, check2, check3, check4],
        action_plan=action_plan,
        strengths=strengths,
        limitations=limitations,
        pages_analyzed=crawl_result.pages_analyzed,
    )


@app.post("/api/audit/ai-visibility", response_model=AIVisibilityResponse)
async def run_ai_visibility_probe(request: AIVisibilityRequest):
    """Run an experimental live AI visibility probe (Gemini 2.5 Flash)."""
    raise HTTPException(status_code=501, detail="Experimental AI visibility probe ready - wiring logic in M10")
