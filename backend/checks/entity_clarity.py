"""Check 2: Entity Clarity - Milestone M5.

Scoring (max 25 points):
  - Definitional entity sentence (H1/intro): 0/4/8 pts  [heuristic]
  - Organization JSON-LD schema quality:     0/4/8 pts  [deterministic]
  - About page presence & alignment:         0 or 5 pts [deterministic]
  - NAP / contact clarity:                   0/2/4 pts  [deterministic+heuristic]

Confidence: High for schema/About page checks; Medium for heuristic content checks.
"""

import re
import uuid
from typing import Dict, List, Optional, Tuple

from models import (
    CheckResult,
    Confidence,
    Finding,
    PageData,
    Severity,
)

CHECK_ID = "entity_clarity"
CHECK_NAME = "Entity Clarity"
MAX_SCORE = 25
WEIGHT = 25

# Schema @type values that count as Organization-equivalent
ORGANIZATION_SCHEMA_TYPES = {
    "organization",
    "localbusiness",
    "plumbingservice",
    "electrician",
    "hvacbusiness",
    "legalservice",
    "accountingservice",
    "dentist",
    "physician",
    "restaurant",
    "store",
    "automotivebusiness",
    "beautysalon",
    "financialservice",
    "realestateagent",
    "softwareapplication",
    "corporation",
    "professionalservice",
    "homeandconstructionbusiness",
    "healthandbeautybuisness",
    "foodestablishment",
    "lodgingbusiness",
    "medicalorganization",
    "sportsorganization",
    "educationalorganization",
    "governmentorganization",
    "ngo",
    "newsmediacorganization",
}

# Filler / vague H1 patterns to detect weak entity positioning
VAGUE_H1_PATTERNS = [
    r"^welcome\b",
    r"^home\b",
    r"^quality services?$",
    r"^we are the best",
    r"^leading provider",
    r"^innovative solution",
    r"^our (company|team|services?)$",
    r"^(get started|let's talk|hello|hi there)$",
    r"^(transforming|revolutionizing|empowering)",
    r"^your (partner|solution|trusted)",
    r"^(the future|next generation|world.class)",
]

# Regex for explicit definitional sentence
DEFINITION_PATTERNS = [
    r"\b\w[\w\s]{1,40}\s+is\s+a(?:n)?\s+[\w\s]{3,60}(?:company|service|provider|agency|platform|firm|specialist|business|store|practice|clinic|restaurant|contractor|consultancy|studio|shop)",
    r"\b\w[\w\s]{1,40}\s+are\s+(?:a(?:n)?\s+)?[\w\s]{3,60}(?:company|service|provider|agency|platform|firm|specialist|business|store)",
    r"(?:we\s+are|we're)\s+a(?:n)?\s+[\w\s]{3,60}(?:company|service|provider|agency|firm|business)\s+(?:serving|based|located|in|specializing)",
]

# Phone number pattern
PHONE_PATTERN = re.compile(
    r"(?:\+?\d[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?){1,2}\d{3,4}[\s.-]?\d{4}"
)

# Physical address pattern (street address heuristic)
# Requires full street suffix words (not abbreviations) to reduce false positives
ADDRESS_PATTERN = re.compile(
    r"\b\d{1,5}\s+(?:[A-Z][a-z]+\s+){1,4}(?:Street|Avenue|Boulevard|Drive|Road|Lane|Way|Court|Place|Plaza)\b",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalize_type(schema_type) -> str:
    """Normalize schema @type to lowercase, handling list or string."""
    if isinstance(schema_type, list):
        return " ".join(str(t).lower() for t in schema_type)
    return str(schema_type).lower()


def find_org_schema(pages: List[Optional[PageData]]) -> Tuple[Optional[Dict], str]:
    """Search crawled pages for an Organization-equivalent JSON-LD schema.

    Returns (schema_dict_or_None, page_url_where_found).
    """
    for page in pages:
        if not page:
            continue
        for schema in page.json_ld_schemas:
            raw_type = schema.get("@type", "")
            normalized = _normalize_type(raw_type)
            for org_type in ORGANIZATION_SCHEMA_TYPES:
                if org_type in normalized:
                    return schema, page.url
    return None, ""


def score_org_schema(schema: Optional[Dict]) -> Tuple[int, List[str]]:
    """Score Organization schema completeness. Returns (pts 0/4/8, missing_fields)."""
    if schema is None:
        return 0, ["@type", "name", "url", "address/telephone"]

    present_fields: List[str] = []
    missing_fields: List[str] = []

    key_fields = ["name", "url", "telephone", "address", "description", "email"]
    for field in key_fields:
        if schema.get(field):
            present_fields.append(field)
        else:
            missing_fields.append(field)

    if len(present_fields) >= 4:
        return 8, missing_fields
    elif len(present_fields) >= 2:
        return 4, missing_fields
    else:
        return 0, missing_fields


def detect_definitional_sentence(text: str, h1s: List[str]) -> Tuple[int, str, str]:
    """Detect quality of entity definition in H1s and opening body copy.

    Returns (pts 0/4/8, matched_text, explanation).
    """
    # Check H1s first (strongest signal)
    for h1 in h1s:
        h1_lower = h1.lower().strip()
        # Check for vague / filler H1
        if any(re.search(pat, h1_lower) for pat in VAGUE_H1_PATTERNS):
            return 0, h1, "vague_h1"

        # Check for strong definitional pattern in H1
        for pat in DEFINITION_PATTERNS:
            if re.search(pat, h1, re.IGNORECASE):
                return 8, h1, "strong_definition_in_h1"

    # Check first 600 words of body text for definition
    first_chunk = " ".join(text.split()[:600])
    for pat in DEFINITION_PATTERNS:
        match = re.search(pat, first_chunk, re.IGNORECASE)
        if match:
            snippet = first_chunk[max(0, match.start()-30):match.end()+60]
            return 4, snippet.strip(), "definition_in_body_not_h1"

    # H1 exists but is just not a definition
    if h1s and not any(re.search(pat, h1s[0].lower()) for pat in VAGUE_H1_PATTERNS):
        return 4, h1s[0], "h1_exists_not_definitional"

    return 0, h1s[0] if h1s else "(no H1 found)", "vague_h1"


def detect_nap(pages: List[Optional[PageData]], org_schema: Optional[Dict]) -> Tuple[int, List[str]]:
    """Detect Name, Address, Phone presence across pages and schema.

    Returns (pts 0/2/4, evidence_list).
    """
    evidence: List[str] = []
    has_phone = False
    has_address = False

    # Check schema first
    if org_schema:
        if org_schema.get("telephone"):
            has_phone = True
            evidence.append(f"Phone in schema: {org_schema['telephone']}")
        if org_schema.get("address"):
            has_address = True
            addr = org_schema["address"]
            if isinstance(addr, dict):
                addr_str = ", ".join(filter(None, [
                    addr.get("streetAddress", ""),
                    addr.get("addressLocality", ""),
                    addr.get("addressRegion", ""),
                    addr.get("postalCode", ""),
                ]))
                evidence.append(f"Address in schema: {addr_str}")
            else:
                evidence.append(f"Address in schema: {addr}")

    # Also scan body text of all pages
    for page in pages:
        if not page or not page.body_text:
            continue
        if not has_phone:
            phone_match = PHONE_PATTERN.search(page.body_text)
            if phone_match:
                has_phone = True
                evidence.append(f"Phone in body text ({page.url}): {phone_match.group()}")
        if not has_address:
            addr_match = ADDRESS_PATTERN.search(page.body_text)
            if addr_match:
                has_address = True
                evidence.append(f"Address in body text ({page.url}): {addr_match.group()}")

    if has_phone and has_address:
        return 4, evidence
    elif has_phone or has_address:
        return 2, evidence
    else:
        return 0, evidence


def get_business_name_hint(pages: List[Optional[PageData]], hint: Optional[str]) -> str:
    """Best-effort business name from hint, OG tag, or page title."""
    if hint:
        return hint

    for page in pages:
        if not page:
            continue
        # Try og:site_name or JSON-LD name first
        for schema in page.json_ld_schemas:
            name = schema.get("name")
            if name and isinstance(name, str):
                return name.strip()
        # Fallback to title (strip trailing site suffix)
        if page.title:
            title = re.sub(r"\s*[|\-–—].*$", "", page.title).strip()
            return title

    return "this business"


# ---------------------------------------------------------------------------
# Main evaluation function
# ---------------------------------------------------------------------------

def evaluate_entity_clarity(
    homepage: Optional[PageData],
    about_page: Optional[PageData],
    service_page: Optional[PageData],
    business_name_hint: Optional[str] = None,
) -> CheckResult:
    """Evaluate Check 2: Entity Clarity.

    Inputs come from M4 CrawlResult fields. Each is a PageData or None.

    Returns:
        CheckResult with score, weighted_score, and findings.
    """
    findings: List[Finding] = []
    score = 0

    all_pages: List[Optional[PageData]] = [homepage, about_page, service_page]
    business_name = get_business_name_hint(all_pages, business_name_hint)

    homepage_url = homepage.url if homepage else "homepage"
    about_url = about_page.url if about_page else None

    # ------------------------------------------------------------------ #
    # Signal 1: Definitional entity sentence in H1 / opening copy (8 pts) #
    # ------------------------------------------------------------------ #

    if homepage:
        def_pts, def_evidence, def_reason = detect_definitional_sentence(
            homepage.body_text, homepage.h1s
        )
        score += def_pts

        if def_reason == "vague_h1":
            findings.append(Finding(
                id=str(uuid.uuid4()),
                check_id=CHECK_ID,
                title="Vague homepage H1 heading — missing explicit entity definition",
                severity=Severity.high,
                confidence=Confidence.medium,
                page_url=homepage_url,
                evidence=f"H1 text found: '{def_evidence}'",
                why_it_matters=(
                    "AI language models require clear, self-contained definitional statements "
                    "(\"[Business] is a [type] serving [location]\") to categorize your entity "
                    "accurately in knowledge graphs and answer generation pipelines."
                ),
                recommended_fix=(
                    f"<!-- Replace vague headline with a clear entity definition statement -->\n"
                    f"<h1>{business_name}: [Type of Business] in [City / Market]</h1>\n"
                    f"<p>{business_name} is a [licensed/certified] [service type] "
                    f"serving [location] since [founding year]. We specialize in [core service 1], "
                    f"[core service 2], and [core service 3].</p>"
                ),
            ))
        elif def_reason == "definition_in_body_not_h1":
            findings.append(Finding(
                id=str(uuid.uuid4()),
                check_id=CHECK_ID,
                title="Entity definition present in body copy but missing from H1 heading",
                severity=Severity.medium,
                confidence=Confidence.medium,
                page_url=homepage_url,
                evidence=f"Definition found in body: '{def_evidence[:200]}'",
                why_it_matters=(
                    "AI crawlers weight H1 headings heavily for entity categorization. "
                    "Moving your definitional statement into the H1 tag increases citation probability."
                ),
                recommended_fix=(
                    f"<!-- Promote the entity definition to the H1 heading -->\n"
                    f"<h1>{business_name}: [Clear Service Category] in [Location]</h1>"
                ),
            ))
        # If strong definition in H1: no finding generated (clean pass)
    else:
        # Homepage unavailable - can't evaluate this signal
        findings.append(Finding(
            id=str(uuid.uuid4()),
            check_id=CHECK_ID,
            title="Homepage unavailable — entity clarity check skipped",
            severity=Severity.medium,
            confidence=Confidence.low,
            page_url=homepage_url,
            evidence="Homepage fetch returned no parseable HTML.",
            why_it_matters="Entity clarity signals cannot be evaluated without homepage content.",
            recommended_fix="Ensure the homepage is publicly accessible and returns HTTP 200.",
        ))

    # ------------------------------------------------------------------ #
    # Signal 2: Organization JSON-LD schema quality (max 8 pts)            #
    # ------------------------------------------------------------------ #

    org_schema, schema_found_on_url = find_org_schema(all_pages)
    schema_pts, missing_fields = score_org_schema(org_schema)
    score += schema_pts

    if org_schema is None:
        findings.append(Finding(
            id=str(uuid.uuid4()),
            check_id=CHECK_ID,
            title="No Organization or LocalBusiness JSON-LD schema found on any crawled page",
            severity=Severity.high,
            confidence=Confidence.high,
            page_url=about_url or homepage_url,
            evidence=(
                "Searched Homepage, About page, and Service page. "
                "No <script type=\"application/ld+json\"> containing Organization, "
                "LocalBusiness, or equivalent schema type was found."
            ),
            why_it_matters=(
                "Without Organization schema, AI models must guess your business type, "
                "location, phone number, and service catalog from unstructured text — "
                "leading to incomplete or incorrect AI-generated answers about your business."
            ),
            recommended_fix=(
                '<script type="application/ld+json">\n'
                '{ "@context": "https://schema.org",\n'
                f'  "@type": "LocalBusiness",\n'
                f'  "name": "{business_name}",\n'
                f'  "url": "{homepage_url}",\n'
                '  "telephone": "+1-XXX-XXX-XXXX",\n'
                '  "address": {\n'
                '    "@type": "PostalAddress",\n'
                '    "streetAddress": "123 Main St",\n'
                '    "addressLocality": "Your City",\n'
                '    "addressRegion": "ST",\n'
                '    "postalCode": "00000"\n'
                '  },\n'
                '  "description": "One clear sentence about what you do and where."\n'
                '}\n'
                '</script>'
            ),
        ))
    elif schema_pts == 4:
        # Partial schema — found but incomplete
        missing_str = ", ".join(missing_fields[:4])
        findings.append(Finding(
            id=str(uuid.uuid4()),
            check_id=CHECK_ID,
            title=f"Incomplete Organization schema — missing key fields: {missing_str}",
            severity=Severity.medium,
            confidence=Confidence.high,
            page_url=schema_found_on_url,
            evidence=(
                f"Schema @type \"{org_schema.get('@type', 'Unknown')}\' found on {schema_found_on_url}. "
                f"Missing fields: {missing_str}."
            ),
            why_it_matters=(
                "Partial schema provides some entity signal but missing fields "
                "(especially address, telephone, and description) reduce AI model confidence "
                "when generating answers about your business."
            ),
            recommended_fix=(
                f"# Add missing fields to your existing JSON-LD schema block:\n"
                + ('  "telephone": "+1-XXX-XXX-XXXX",\n' if "telephone" in missing_fields else "")
                + ('  "address": {\n    "@type": "PostalAddress",\n    "streetAddress": "...",\n    "addressLocality": "City",\n    "addressRegion": "ST"\n  },\n' if "address" in missing_fields else "")
                + ('  "description": "Clear one-sentence entity description here."\n' if "description" in missing_fields else "")
            ),
        ))

    # ------------------------------------------------------------------ #
    # Signal 3: About page presence and alignment (max 5 pts)              #
    # ------------------------------------------------------------------ #

    if about_page and about_page.status_code == 200 and about_page.body_text:
        score += 5  # About page found and has content
    else:
        findings.append(Finding(
            id=str(uuid.uuid4()),
            check_id=CHECK_ID,
            title="No About page found within 3-page crawl scope",
            severity=Severity.medium,
            confidence=Confidence.high,
            page_url=homepage_url,
            evidence=(
                "Pattern matching on navigation links found no URL matching "
                "/about, /about-us, /company, /who-we-are, or /our-story patterns."
                if not about_page
                else f"About page URL found but returned HTTP {about_page.status_code}."
            ),
            why_it_matters=(
                "A dedicated About page is one of the most commonly cited sources in "
                "AI-generated business answers. It provides a concentrated, authoritative "
                "entity description that AI models use to build business knowledge."
            ),
            recommended_fix=(
                f"# Create /about or /about-us page with these key elements:\n\n"
                f"1. Clear H1: \"{business_name}: [Type] in [Location] Since [Year]\"\n"
                f"2. Opening paragraph: explicit 'is a' definition sentence\n"
                f"3. Organization JSON-LD schema in <head>\n"
                f"4. Credentials, certifications, awards\n"
                f"5. Founding story with specific facts (year, founder, first client)\n"
                f"6. NAP: physical address, phone, email"
            ),
        ))

    # ------------------------------------------------------------------ #
    # Signal 4: NAP / Contact clarity (max 4 pts)                          #
    # ------------------------------------------------------------------ #

    nap_pts, nap_evidence = detect_nap(all_pages, org_schema)
    score += nap_pts

    if nap_pts == 0:
        findings.append(Finding(
            id=str(uuid.uuid4()),
            check_id=CHECK_ID,
            title="No Name, Address, or Phone (NAP) contact information detected",
            severity=Severity.medium,
            confidence=Confidence.medium,
            page_url=homepage_url,
            evidence=(
                "Scanned Homepage, About page, and Service page body text and JSON-LD schema. "
                "No phone number pattern or physical address pattern detected."
            ),
            why_it_matters=(
                "AI models rely on NAP consistency to confidently identify and locate local businesses. "
                "Missing contact details cause AI engines to omit or misattribute your business "
                "in local and geographic queries."
            ),
            recommended_fix=(
                "# Add NAP to your site footer and Organization schema:\n\n"
                f"**{business_name}**\n"
                "123 Main Street, City, ST 00000\n"
                "Phone: (555) 555-5555\n"
                "Email: info@yourdomain.com\n\n"
                "# And in JSON-LD schema:\n"
                '  "telephone": "(555) 555-5555",\n'
                '  "address": {"@type": "PostalAddress", "streetAddress": "123 Main St", ...}'
            ),
        ))
    elif nap_pts == 2:
        nap_ev_str = "; ".join(nap_evidence) if nap_evidence else "Partial contact info detected."
        findings.append(Finding(
            id=str(uuid.uuid4()),
            check_id=CHECK_ID,
            title="Partial contact information — missing either phone or physical address",
            severity=Severity.low,
            confidence=Confidence.medium,
            page_url=homepage_url,
            evidence=nap_ev_str,
            why_it_matters=(
                "Full NAP (Name, Address, Phone) consistency is a key signal for AI local business citations. "
                "Incomplete contact info reduces AI model confidence in your business entity."
            ),
            recommended_fix=(
                "# Ensure both phone and physical address are present in your site footer:\n\n"
                "Phone: +1-XXX-XXX-XXXX\n"
                "Address: [Full street address, City, State, ZIP]"
            ),
        ))

    # Clamp score
    score = min(score, MAX_SCORE)
    weighted_score = round((score / MAX_SCORE) * WEIGHT)

    return CheckResult(
        check_id=CHECK_ID,
        check_name=CHECK_NAME,
        score=score,
        max_score=MAX_SCORE,
        weight=WEIGHT,
        weighted_score=weighted_score,
        findings=findings,
    )
