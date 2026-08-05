"""HTML parser using BeautifulSoup4 - Implements Milestone M4 of PROJECT_BLUEPRINT.md."""

import json
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from models import NavLink, PageData


def extract_json_ld(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """Extract and parse all JSON-LD structured data scripts from HTML soup."""
    json_ld_list: List[Dict[str, Any]] = []
    scripts = soup.find_all("script", type="application/ld+json")
    for script in scripts:
        if not script.string:
            continue
        try:
            raw_text = script.string.strip()
            data = json.loads(raw_text)
            if isinstance(data, list):
                json_ld_list.extend([item for item in data if isinstance(item, dict)])
            elif isinstance(data, dict):
                json_ld_list.append(data)
        except Exception:
            # Ignore invalid/malformed JSON-LD scripts gracefully
            continue
    return json_ld_list


def detect_js_shell(soup: BeautifulSoup, body_text: str) -> bool:
    """Detect if server-delivered HTML is a thin JavaScript shell (<500 chars or empty SPA container)."""
    if len(body_text.strip()) < 500:
        return True
    
    # Check for common SPA root elements with minimal content
    root_div = soup.find("div", id=re.compile(r"^(root|app|__next)$", re.IGNORECASE))
    if root_div and len(root_div.get_text(strip=True)) < 200:
        return True

    return False


def parse_page(url: str, html: str, status_code: int = 200) -> PageData:
    """Parse raw HTML into a structured PageData object."""
    if not html:
        return PageData(url=url, status_code=status_code)

    soup = BeautifulSoup(html, "html.parser")

    # 1. Title
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""

    # 2. Meta description
    meta_desc_tag = (
        soup.find("meta", attrs={"name": "description"})
        or soup.find("meta", attrs={"property": "og:description"})
    )
    meta_description = meta_desc_tag.get("content", "").strip() if meta_desc_tag else ""

    # 3. Headings
    h1s = [h1.get_text(strip=True) for h1 in soup.find_all("h1") if h1.get_text(strip=True)]
    h2s = [h2.get_text(strip=True) for h2 in soup.find_all("h2") if h2.get_text(strip=True)]

    # 4. JSON-LD Schemas
    json_ld_schemas = extract_json_ld(soup)

    # 5. Extract links for nav discovery
    links: List[NavLink] = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        text = a.get_text(strip=True)
        if href and not href.startswith(("javascript:", "mailto:", "tel:", "#")):
            full_url = urljoin(url, href)
            links.append(NavLink(text=text, href=full_url))

    # 6. Body text (clean copy without scripts, styles, header/footer boilerplate)
    soup_copy = BeautifulSoup(html, "html.parser")
    for element in soup_copy(["script", "style", "nav", "footer", "header", "svg", "noscript"]):
        element.decompose()

    body_text = soup_copy.get_text(separator=" ", strip=True)
    body_text = re.sub(r"\s+", " ", body_text)

    # 7. JS shell detection
    is_js_shell = detect_js_shell(soup, body_text)

    return PageData(
        url=url,
        status_code=status_code,
        html=html,
        title=title,
        h1s=h1s,
        h2s=h2s,
        meta_description=meta_description,
        json_ld_schemas=json_ld_schemas,
        body_text=body_text,
        is_js_shell=is_js_shell,
        links=links,
    )


def find_about_url(homepage_data: PageData, base_url: str) -> Optional[str]:
    """Pattern match navigation and body links to locate the About page URL."""
    about_patterns = [
        r"/about/?$",
        r"/about-us/?$",
        r"/company/?$",
        r"/who-we-are/?$",
        r"/our-story/?$",
        r"/about$",
    ]
    base_domain = urlparse(base_url).netloc.lower()

    # First check exact path pattern matches
    for link in homepage_data.links:
        parsed = urlparse(link.href)
        if parsed.netloc.lower() != base_domain:
            continue
        path = parsed.path.lower()
        for pat in about_patterns:
            if re.search(pat, path):
                return link.href

    # Fallback to link anchor text check
    for link in homepage_data.links:
        parsed = urlparse(link.href)
        if parsed.netloc.lower() != base_domain:
            continue
        text_lower = link.text.lower()
        if "about" in text_lower or "who we are" in text_lower or "our story" in text_lower:
            return link.href

    return None


def find_service_url(homepage_data: PageData, base_url: str, exclude_urls: List[str]) -> Optional[str]:
    """Pattern match navigation links to locate one relevant service/product page URL."""
    service_patterns = [
        r"/services?/",
        r"/products?/",
        r"/solutions?/",
        r"/what-we-do/",
        r"/capabilities/",
        r"/offering/",
    ]
    base_domain = urlparse(base_url).netloc.lower()
    excluded_set = {u.rstrip("/").lower() for u in exclude_urls}

    # 1. Match specific service directory paths
    for link in homepage_data.links:
        clean_href = link.href.rstrip("/").lower()
        if clean_href in excluded_set:
            continue
        parsed = urlparse(link.href)
        if parsed.netloc.lower() != base_domain:
            continue
        path = parsed.path.lower()
        for pat in service_patterns:
            if re.search(pat, path) and path not in ("/", "/services", "/services/", "/products", "/products/"):
                return link.href

    # 2. Match anchor text or subpage under /services/ or /products/
    for link in homepage_data.links:
        clean_href = link.href.rstrip("/").lower()
        if clean_href in excluded_set:
            continue
        parsed = urlparse(link.href)
        if parsed.netloc.lower() != base_domain:
            continue
        path = parsed.path.lower()

        # Skip generic top-level hubs if subpages exist, or non-content pages
        if path in ("/", "", "/contact", "/privacy", "/terms", "/blog", "/news"):
            continue
        
        text_lower = link.text.lower()
        if any(kw in text_lower for kw in ["service", "product", "cleaning", "repair", "installation", "solution", "feature"]):
            return link.href

    # 3. Fallback to first non-excluded internal link with a path depth >= 1
    for link in homepage_data.links:
        clean_href = link.href.rstrip("/").lower()
        if clean_href in excluded_set:
            continue
        parsed = urlparse(link.href)
        if parsed.netloc.lower() == base_domain and len(parsed.path.strip("/").split("/")) >= 1:
            path = parsed.path.lower()
            if path not in ("/", "", "/contact", "/privacy", "/terms", "/blog"):
                return link.href

    return None
