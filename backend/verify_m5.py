"""
End-to-end M5 verification: crawl real sites and run Check 1 + Check 2.
"""
import asyncio
from fetcher import crawl_site
from checks.crawler_access import evaluate_crawler_access
from checks.entity_clarity import evaluate_entity_clarity


def print_check_result(res):
    grade = "PASS" if res.score >= res.max_score * 0.75 else ("WARN" if res.score >= res.max_score * 0.5 else "FAIL")
    print(f"\n  [{grade}] {res.check_name}: {res.score}/{res.max_score} pts (weighted: {res.weighted_score})")
    if res.findings:
        for f in res.findings:
            print(f"    • [{f.severity.upper()}|{f.confidence.upper()}] {f.title}")
            print(f"      Evidence: {f.evidence[:120]}")
    else:
        print("    • No issues found — clean pass.")


async def test_site(url: str, business_name: str):
    print(f"\n{'='*60}")
    print(f"SITE: {url}  ({business_name})")
    print(f"{'='*60}")

    crawl = await crawl_site(url)

    # Check 1
    c1 = evaluate_crawler_access(
        robots_txt_content=crawl.robots_txt_content,
        robots_txt_status=crawl.robots_txt_status,
        llms_txt_content=crawl.llms_txt_content,
        llms_txt_status=crawl.llms_txt_status,
        homepage_html=crawl.homepage.html if crawl.homepage else "",
        target_url=crawl.target_url,
    )
    print_check_result(c1)

    # Check 2
    c2 = evaluate_entity_clarity(
        homepage=crawl.homepage,
        about_page=crawl.about_page,
        service_page=crawl.service_page,
        business_name_hint=business_name,
    )
    print_check_result(c2)

    total = c1.score + c2.score
    print(f"\n  Combined Score (Check 1+2): {total}/{c1.max_score + c2.max_score}")


async def main():
    await test_site("https://stripe.com", "Stripe")
    await test_site("https://python.org", "Python Software Foundation")

if __name__ == "__main__":
    asyncio.run(main())
