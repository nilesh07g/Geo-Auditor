"""
End-to-end M6 verification: crawl real sites and run Check 3 + Check 4.
"""
import asyncio
from fetcher import crawl_site
from checks.structured_data import evaluate_structured_data
from checks.answer_ready import evaluate_answer_ready


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

    # Check 3
    c3 = evaluate_structured_data(
        homepage=crawl.homepage,
        about_page=crawl.about_page,
        service_page=crawl.service_page,
    )
    print_check_result(c3)

    # Check 4
    c4 = evaluate_answer_ready(
        homepage=crawl.homepage,
        about_page=crawl.about_page,
        service_page=crawl.service_page,
    )
    print_check_result(c4)

    print(f"\n  Combined Score (Check 3+4): {c3.score + c4.score}/{c3.max_score + c4.max_score}")


async def main():
    await test_site("https://stripe.com", "Stripe")
    await test_site("https://python.org", "Python Software Foundation")


if __name__ == "__main__":
    asyncio.run(main())