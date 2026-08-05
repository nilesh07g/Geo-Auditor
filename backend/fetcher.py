"""Site fetcher using httpx - Implements Milestone M4 of PROJECT_BLUEPRINT.md."""

import asyncio
from typing import Optional, Tuple
from urllib.parse import urlparse, urljoin

import httpx
from config import settings
from models import CrawlResult, Limitation, PageData
from parser import find_about_url, find_service_url, parse_page


def normalize_url(url: str) -> str:
    """Normalize input URL to include standard scheme if missing."""
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


async def fetch_single_page(client: httpx.AsyncClient, url: str) -> Tuple[int, str, Optional[str]]:
    """Fetch raw HTML/text from a single URL with error handling. Returns (status_code, content, error_msg)."""
    try:
        response = await client.get(
            url,
            timeout=settings.HTTP_TIMEOUT,
            follow_redirects=True,
            headers={"User-Agent": settings.USER_AGENT},
        )
        return response.status_code, response.text, None
    except httpx.TimeoutException:
        return 0, "", f"Timeout after {settings.HTTP_TIMEOUT}s while requesting {url}"
    except httpx.HTTPError as e:
        return 0, "", f"HTTP connection error requesting {url}: {str(e)}"
    except Exception as e:
        return 0, "", f"Error fetching {url}: {str(e)}"


async def crawl_site(raw_url: str) -> CrawlResult:
    """Crawl a target business site up to the 3-page scope limit + robots.txt & llms.txt."""
    target_url = normalize_url(raw_url)
    parsed_target = urlparse(target_url)
    base_origin = f"{parsed_target.scheme}://{parsed_target.netloc}"

    limitations: list[Limitation] = []
    pages_analyzed: list[str] = []

    async with httpx.AsyncClient(
        verify=False,  # Allow self-signed certificates or legacy SSL on SMB sites
        headers={"User-Agent": settings.USER_AGENT},
    ) as client:
        # 1. Fetch Homepage
        status, html, err = await fetch_single_page(client, target_url)
        if err or status >= 400:
            limitations.append(
                Limitation(description=f"Homepage fetch failed ({err or f'HTTP {status}'}). Audit proceeding with limited data.")
            )
            homepage_data = PageData(url=target_url, status_code=status, html="")
        else:
            homepage_data = parse_page(target_url, html, status)
            pages_analyzed.append(target_url)

            if homepage_data.is_js_shell:
                limitations.append(
                    Limitation(
                        description="JavaScript-rendered site detected. Audit analyzes server-delivered HTML only. Key content may be missing from results."
                    )
                )

        # 2. Discover & Fetch About Page
        about_page_data: Optional[PageData] = None
        about_url = find_about_url(homepage_data, target_url) if homepage_data.html else None
        if about_url and about_url != target_url:
            ab_status, ab_html, ab_err = await fetch_single_page(client, about_url)
            if ab_html and ab_status == 200:
                about_page_data = parse_page(about_url, ab_html, ab_status)
                pages_analyzed.append(about_url)
            else:
                limitations.append(
                    Limitation(description=f"About page ({about_url}) fetch failed ({ab_err or f'HTTP {ab_status}'}).")
                )
        else:
            limitations.append(
                Limitation(description="About page not found in navigation structure within 3-page crawl scope.")
            )

        # 3. Discover & Fetch Service/Product Page
        service_page_data: Optional[PageData] = None
        exclude = [target_url]
        if about_url:
            exclude.append(about_url)

        service_url = find_service_url(homepage_data, target_url, exclude) if homepage_data.html else None
        if service_url:
            srv_status, srv_html, srv_err = await fetch_single_page(client, service_url)
            if srv_html and srv_status == 200:
                service_page_data = parse_page(service_url, srv_html, srv_status)
                pages_analyzed.append(service_url)
            else:
                limitations.append(
                    Limitation(description=f"Service page ({service_url}) fetch failed ({srv_err or f'HTTP {srv_status}'}).")
                )
        else:
            limitations.append(
                Limitation(description="Service/product subpage not located in navigation within 3-page crawl scope.")
            )

        # 4. Fetch robots.txt (Not counted toward 3-page content limit)
        robots_url = urljoin(base_origin, "/robots.txt")
        rob_status, rob_content, _ = await fetch_single_page(client, robots_url)
        robots_txt_content = rob_content if rob_status == 200 else None
        if rob_status == 200:
            pages_analyzed.append(robots_url)
        else:
            pages_analyzed.append(f"{robots_url} (HTTP {rob_status})")

        # 5. Fetch llms.txt (Not counted toward 3-page content limit)
        llms_url = urljoin(base_origin, "/llms.txt")
        llm_status, llm_content, _ = await fetch_single_page(client, llms_url)
        llms_txt_content = llm_content if llm_status == 200 else None
        if llm_status == 200:
            pages_analyzed.append(llms_url)
        else:
            pages_analyzed.append(f"{llms_url} (HTTP {llm_status} Not Found)")

        # Always record 3-page crawl scope boundary limit
        limitations.append(
            Limitation(
                description=f"Audit crawl scope strictly limited to maximum {settings.MAX_CONTENT_PAGES} content pages per target business."
            )
        )

        return CrawlResult(
            target_url=target_url,
            homepage=homepage_data,
            about_page=about_page_data,
            service_page=service_page_data,
            robots_txt_content=robots_txt_content,
            robots_txt_status=rob_status,
            llms_txt_content=llms_txt_content,
            llms_txt_status=llm_status,
            pages_analyzed=pages_analyzed,
            limitations=limitations,
        )
