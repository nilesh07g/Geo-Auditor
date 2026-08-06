"""Check 4: Answer-Ready Content Structure. Implemented in Milestone M6."""

import re
import uuid
from typing import List, Optional, Tuple

from bs4 import BeautifulSoup

from models import (
    CheckResult,
    Confidence,
    Finding,
    PageData,
    Severity,
)

CHECK_ID = "answer_ready"
CHECK_NAME = "Answer-Ready Content Structure"
MAX_SCORE = 30
WEIGHT = 30

# Patterns for detecting definitional sentences (from PROJECT_BLUEPRINT.md)
DEFINITION_PATTERNS = [
    r"\b\w[\w\s]{1,40}\s+is\s+a(?:n)?\s+[\w\s]{3,60}(?:company|service|provider|agency|platform|firm|specialist|business|store|practice|clinic|restaurant|contractor|consultancy|studio|shop)",
    r"\b\w[\w\s]{1,40}\s+are\s+(?:a(?:n)?\s+)?[\w\s]{3,60}(?:company|service|provider|agency|platform|firm|specialist|business|store)",
    r"(?:we\s+are|we're)\s+a(?:n)?\s+[\w\s]{3,60}(?:company|service|provider|agency|platform|firm|specialist|business)\s+(?:serving|based|located|in|specializing)",
]

# Patterns for vague/filler content (from PROJECT_BLUEPRINT.md)
VAGUE_PHRASES = [
    "welcome", "home", "quality services", "we are the best",
    "leading provider", "innovative solutions", "our company",
    "we are the leading provider", "world class", "industry leader",
    "premium quality", "best in class", "top-notch", "expert team",
    "highly qualified"
]

# Patterns for FAQ-style headings (from PROJECT_BLUEPRINT.md)
FAQ_HEADING_PATTERNS = [
    r"^q[.]?\s*i\s*\?\s*.*$",  # Question headers
    r"^faq\s*h[1-6]$",  # FAQ headings
]

# Specific facts patterns for Check 4 (from PROJECT_BLUEPRINT.md)
NUMBER_PATTERN = r'\d+(?:,\d\d\d)*(?:\.\d+)?'
DATE_PATTERN = r'\b(?:19|20)\d{2}\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}\b'
ADDRESS_PATTERN = r'\b\d+\s+(?:[A-Za-z]+\.?)+\s+(?:Street|Avenue|Boulevard|Drive|Road|Lane|Way|Court|Place|Ave|St|Rd|Blvd|Dr)\b'
PHONE_PATTERN = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'

MARKETING_ONLY_PATTERNS = [
    re.compile(r"\b(welcome|quality services|we are the best|leading provider|innovative solutions|our company|industry leader|premium quality|best in class|top-notch|expert team|highly qualified|award-winning|passionate|mission statement|vision statement|values|customer-focused|trusted partner|best-in-class|commitment to)\b", re.I),
]

FACT_PATTERNS = [
    ("Founded", re.compile(r"\b(?:founded|established|since)\s+(?:in\s+)?(?:19|20)\d{2}\b", re.I)),
    ("Serving", re.compile(r"\b(?:serving|serves|available in|covering|operating in)\s+[\w\s,+-]{5,80}\b", re.I)),
    ("Employees", re.compile(r"\b(?:\d{1,3}(?:,\d{3})*|\d+)\+?\s+(?:employees|team members|staff|professionals)\b", re.I)),
    ("Certification", re.compile(r"\b(?:ISO\s*\d{3,4}|certified|licensed|registered|accredited)\b", re.I)),
    ("Availability", re.compile(r"\b(?:24/7|24x7|24 hours|around the clock|emergency service)\b", re.I)),
    ("Locations", re.compile(r"\b(?:\d{1,3}(?:,\d{3})*|\d+)\+?\s+(?:locations|cities|regions|areas|states|countries)\b", re.I)),
    ("Address", re.compile(ADDRESS_PATTERN, re.I)),
    ("Phone", re.compile(PHONE_PATTERN, re.I)),
]

SENTENCE_SPLIT_RE = re.compile(r'(?<=[.!?])\s+')


def split_sentences(text: str) -> List[str]:
    return [sentence.strip() for sentence in re.split(SENTENCE_SPLIT_RE, text) if sentence.strip()]


def is_user_generated_sentence(sentence: str) -> bool:
    """Heuristically identify testimonial or review-style sentences in otherwise business-owned content."""
    if not sentence:
        return False

    lower = sentence.lower().strip()
    review_markers = [
        "testimonial",
        "testimonials",
        "review",
        "reviews",
        "customer story",
        "customer stories",
        "what our customers say",
        "what customers say",
        "would highly recommend",
        "highly recommend",
        "i loved",
        "i would recommend",
        "great experience",
        "amazing service",
        "excellent service",
        "five stars",
        "four stars",
        "star rating",
    ]
    if any(marker in lower for marker in review_markers):
        return True

    if re.search(r"\b(i|we|my|our)\b.*\b(recommend|love|loved|great|excellent|amazing|satisfied|happy)\b", lower):
        return True

    return False


def extract_business_owned_text(html: str) -> str:
    """Extract business-owned content from likely editorial sections while skipping reviews and testimonials."""
    if not html:
        return ""

    soup = BeautifulSoup(html, "html.parser")
    for element in soup(["script", "style", "noscript", "svg"]):
        element.decompose()

    main_content = soup.find(["main", "article", "section"])
    if main_content:
        cleaned_text = main_content.get_text(" ", strip=True)
    else:
        cleaned_text = soup.get_text(" ", strip=True)

    kept_sentences = [
        sentence.strip()
        for sentence in split_sentences(cleaned_text)
        if sentence.strip() and not is_user_generated_sentence(sentence)
    ]
    return re.sub(r"\s+", " ", " ".join(kept_sentences)).strip()


def is_boilerplate_sentence(sentence: str) -> bool:
    lower = sentence.lower().strip()
    if len(lower.split()) <= 3:
        return True
    if lower.startswith("cookie") or lower.startswith("privacy") or lower.startswith("terms"):
        return True
    if re.search(r"\b(home|about|contact|menu|follow us|newsletter|subscribe|sign up|login|search|breadcrumb|breadcrumbs|header|footer|navbar|sidebar)\b", lower):
        return True
    return False


def is_marketing_only_sentence(sentence: str) -> bool:
    if is_boilerplate_sentence(sentence):
        return False
    if len(sentence.split()) < 8:
        return False
    return any(pattern.search(sentence) for pattern in MARKETING_ONLY_PATTERNS)


def extract_sentence_containing_phrase(text: str, phrase: str) -> str:
    lower_phrase = phrase.lower()
    for sentence in split_sentences(text):
        if lower_phrase in sentence.lower():
            return sentence
    return phrase


def merge_duplicate_findings(findings: List[Finding]) -> List[Finding]:
    merged: dict[tuple[str, str, str, str], Finding] = {}
    for finding in findings:
        key = (finding.title, finding.severity, finding.confidence, finding.recommended_fix)
        if key not in merged:
            merged[key] = finding
        else:
            existing = merged[key]
            if finding.page_url and finding.page_url.strip():
                pages = set(p.strip() for p in (existing.page_url or "").split(";") if p.strip())
                pages.add(finding.page_url.strip())
                existing.page_url = "; ".join(sorted(pages))
            if finding.evidence and finding.evidence not in existing.evidence:
                existing.evidence = f"{existing.evidence} | {finding.evidence}"
    return list(merged.values())


def detect_definitional_sentence(text: str) -> Tuple[int, str, str]:
    """Detect quality of entity definition in text.

    Returns (pts 0/4/8, matched_text, explanation).
    """
    if not text:
        return 0, "", "none"

    if "<" in text:
        business_owned_text = extract_business_owned_text(text)
    else:
        business_owned_text = text
    # Check H1s first (strongest signal)
    if text.strip().startswith('<h1>') or text.strip().startswith('<h1 '):
        # Extract H1 content
        h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', text, re.IGNORECASE)
        if h1_match:
            h1_text = h1_match.group(1).strip()
            lower_h1 = h1_text.lower()
            if any(re.search(pat, lower_h1) for pat in VAGUE_PHRASES):
                return 0, h1_text, "vague_h1"
            for pat in DEFINITION_PATTERNS:
                if re.search(pat, h1_text, re.IGNORECASE):
                    return 8, h1_text, "strong_definition_in_h1"
            return 4, h1_text, "h1_exists_not_definitional"

    # Check first 600 words of body text for definition (simplified)
    first_chunk = ' '.join(business_owned_text.split()[:600])
    for pat in DEFINITION_PATTERNS:
        match = re.search(pat, first_chunk, re.IGNORECASE)
        if match:
            snippet = extract_sentence_containing_phrase(first_chunk, match.group(0))
            return 4, snippet.strip(), "definition_in_body_not_h1"

    # No explicit vague phrase finding here; detect marketing only on sentence-level
    return 0, '', "none"

def detect_faq_headings(text: str) -> List[str]:
    """Detect FAQ-style headings in HTML text."""
    headings = []
    for pattern in FAQ_HEADING_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
        headings.extend(matches)
    return headings

def detect_specific_facts(text: str) -> Tuple[int, List[str]]:
    """Detect specific factual content for extractable data.

    Returns (pts 0-8, list of factual sentences).
    """
    found_sentences: List[str] = []
    seen: set[str] = set()

    for sentence in split_sentences(text):
        if len(sentence) < 40:
            continue
        if is_boilerplate_sentence(sentence):
            continue
        if is_marketing_only_sentence(sentence):
            continue

        for _, pattern in FACT_PATTERNS:
            if pattern.search(sentence):
                normalized_sentence = sentence.strip()
                if normalized_sentence not in seen:
                    seen.add(normalized_sentence)
                    found_sentences.append(normalized_sentence)
                break

    score = min(8, len(found_sentences) * 2)
    return score, found_sentences

def calculate_generic_filler_ratio(text: str) -> int:
    """Calculate generic filler ratio (0-6 points) for content quality.

    Returns points: 0 (high filler), 2 (medium filler), 4 (low filler), 6 (no filler).
    """
    if not text:
        return 0

    lower_text = text.lower()
    filler_count = 0

    # Count vague/filler phrases
    for phrase in VAGUE_PHRASES:
        if phrase.lower() in lower_text:
            filler_count += 1

    # Score based on how much filler content we found
    if filler_count >= 3:
        return 0  # 0 points for high filler
    elif filler_count == 2:
        return 2  # 2 points for medium filler
    elif filler_count == 1:
        return 4  # 4 points for low filler
    else:
        return 6  # 6 points for no filler

def evaluate_answer_ready(
    homepage: Optional[PageData],
    about_page: Optional[PageData],
    service_page: Optional[PageData],
) -> CheckResult:
    """Evaluate Check 4: Answer-Ready Content Structure.

    Inputs come from M4 CrawlResult fields. Each is a PageData or None.

    Returns:
        CheckResult with score, weighted_score, and findings.
    """
    findings: List[Finding] = []
    score = 0

    # Collect all page content for analysis
    all_pages: List[Optional[PageData]] = [homepage, about_page, service_page]
    all_text_chunks = []

    # Process each page for definitional sentence analysis
    for page in all_pages:
        if not page:
            continue

        # Check H1 and body text for definitional sentences
        if page.h1s:
            for h1 in page.h1s:
                pt, matched_text, reason = detect_definitional_sentence(h1)
                score += pt

                # Generate findings based on detection reason
                if reason == "vague_h1":
                    findings.append(Finding(
                        id=str(uuid.uuid4()),
                        check_id=CHECK_ID,
                        title="Vague homepage H1 heading — missing explicit entity definition",
                        severity=Severity.high,
                        confidence=Confidence.medium,
                        page_url=page.url,
                        evidence=f"Vague H1: '{matched_text}'",
                        why_it_matters=(
                            "AI engines need clear, self-contained definitional statements "
                            "(\"[Business] is a [type] serving [location]\") to categorize your entity "
                            "accurately in knowledge graphs and answer generation pipelines."
                        ),
                        recommended_fix=(
                            f"<!-- Replace vague headline with a clear entity definition statement -->\n"
                            f"<h1>{page.title or 'Your Business'}: [Type of Business] in [City / Market]</h1>\n"
                            f"<p>Your Business is a [licensed/certified] [service type] serving [location] since [founding year]. "
                            f"We specialize in [core service 1], [core service 2], and [core service 3].</p>"
                        ),
                    ))
                elif reason == "definition_in_body_not_h1":
                    findings.append(Finding(
                        id=str(uuid.uuid4()),
                        check_id=CHECK_ID,
                        title="Entity definition present in body copy but missing from H1 heading",
                        severity=Severity.medium,
                        confidence=Confidence.medium,
                        page_url=page.url,
                        evidence=f"Definition in body: '{matched_text[:200]}...'",
                        why_it_matters=(
                            "AI crawlers weight H1 headings heavily for entity categorization. "
                            "Moving your definitional statement into the H1 tag increases citation probability."
                        ),
                        recommended_fix=(
                            f"<!-- Promote the entity definition to the H1 heading -->\n"
                            f"<h1>{page.title or 'Your Business'}: [Clear Service Category] in [Location]</h1>"
                        ),
                    ))

        # Check body text for definitional sentences
        if page.body_text:
            pt, matched_text, reason = detect_definitional_sentence(page.body_text)
            score += pt

            if page.body_text:
                for sentence in split_sentences(page.body_text):
                    if is_marketing_only_sentence(sentence):
                        findings.append(Finding(
                            id=str(uuid.uuid4()),
                            check_id=CHECK_ID,
                            title="Generic marketing copy detected",
                            severity=Severity.medium,
                            confidence=Confidence.high,
                            page_url=page.url,
                            evidence=sentence,
                            why_it_matters=(
                                "AI engines prefer meaningful, factual sentences over generic marketing copy for accurate business extraction."
                            ),
                            recommended_fix=(
                                "Replace this marketing-heavy sentence with a clear, factual statement about your business, "
                                "services, location, or credentials."
                            ),
                        ))
                        break

        # Track all text for filler analysis
        if page.body_text:
            all_text_chunks.append(page.body_text)

    # Evaluate FAQ-style headings across all pages
    for page in all_pages:
        if not page or not page.body_text:
            continue

        faq_headings = detect_faq_headings(page.body_text)
        if faq_headings:
            score += min(8, len(faq_headings) * 2)  # Up to 8 points for FAQ content

            # Create findings for FAQ headings
            for heading in set(faq_headings):  # Deduplicate
                findings.append(Finding(
                    id=str(uuid.uuid4()),
                    check_id=CHECK_ID,
                    title="FAQ-style heading detected",
                    severity=Severity.low,
                    confidence=Confidence.high,
                    page_url=page.url,
                    evidence=f"FAQ heading: '{heading}'",
                    why_it_matters=(
                        "FAQ-style headings indicate Q&A format content that AI engines can extract "
                        "for direct answers to user queries. This improves your business citation potential."
                    ),
                    recommended_fix=(
                        f"<!-- Add proper FAQPage schema for each FAQ heading -->\n"
                        f'<script type="application/ld+json">\n'
                        f'{{\n'
                        f'  "@context": "https://schema.org",\n'
                        f'  "@type": "FAQPage",\n'
                        f'  "mainEntity": [\n'
                        f'    {{\n'
                        f'      "@type": "Question",\n'
                        f'      "name": "{heading}",\n'
                        f'      "acceptedAnswer": {{\n'
                        f'        "@type": "Answer",\n'
                        f'        "text": "Answer to: {heading}"\n'
                        f'      }}\n'
                        f'    }}\n'
                        f'  ]\n'
                        f'}}\n'
                        f'</script>'
                    ),
                ))

    # Evaluate specific facts across all pages
    for page in all_pages:
        if not page or not page.body_text:
            continue

        fact_score, facts_found = detect_specific_facts(page.body_text)
        score += fact_score

        if facts_found:
            findings.append(Finding(
                id=str(uuid.uuid4()),
                check_id=CHECK_ID,
                title="Extractable specific facts detected",
                severity=Severity.low,
                confidence=Confidence.high,
                page_url=page.url,
                evidence=facts_found[0],
                why_it_matters=(
                    "Specific factual sentences provide extractable content that AI engines can cite accurately."
                ),
                recommended_fix="No action required. This page contains well-formed factual content.",
            ))
        else:
            findings.append(Finding(
                id=str(uuid.uuid4()),
                check_id=CHECK_ID,
                title="No specific facts found",
                severity=Severity.high,
                confidence=Confidence.high,
                page_url=page.url,
                evidence="No measurable factual content detected in page copy.",
                why_it_matters=(
                    "Without measurable facts, AI engines must rely on generic copy, which reduces answer precision and business citation value."
                ),
                recommended_fix=(
                    "Add specific, measurable facts such as establishment year, service area, staff size, certifications, or operating hours."
                ),
            ))

    # Calculate generic filler ratio score (up to 6 points)
    filler_score = calculate_generic_filler_ratio(' '.join(all_text_chunks))
    score += filler_score

    # Deduplicate repeated findings before returning
    findings = merge_duplicate_findings(findings)

    # Clamp score to valid range
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