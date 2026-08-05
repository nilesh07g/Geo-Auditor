"""FastAPI application entry point - GEO Auditor API."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from models import AuditRequest, AuditResponse, AIVisibilityRequest, AIVisibilityResponse

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Generative Engine Optimization audit API",
    version=settings.VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

    # Create a concise executive summary
    executive_summary = f"GEO audit completed for {request.url}. "

    if score_result["overall_score"] >= 80:
        executive_summary += "The business shows strong GEO visibility with most critical areas addressed."
    elif score_result["overall_score"] >= 60:
        executive_summary += "The business has moderate GEO gaps that should be addressed for better AI visibility."
    elif score_result["overall_score"] >= 40:
        executive_summary += "The business is at risk of low AI visibility due to significant GEO issues."
    else:
        executive_summary += "The business has critical GEO issues that require immediate attention."

    # Create prioritized action plan from critical findings
    action_plan = []
    for i, finding in enumerate(critical_findings[:3]):  # Top 3 critical issues
        action_plan.append(ActionPlanItem(
            rank=i + 1,
            action=finding.recommended_fix[:200] + "..." if len(finding.recommended_fix) > 200 else finding.recommended_fix,
            impact=Impact.high if finding.severity == Severity.critical else Impact.medium,
            effort=Effort.medium,
            source_finding_title=finding.title
        ))

    # Create strengths from positive findings
    strengths = []
    for finding in all_findings:
        if finding.severity in [Severity.low, Severity.medium] and finding.confidence == Confidence.high:
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
        aha_line=critical_findings[0].why_it_matters if critical_findings else "No critical issues found.",
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
