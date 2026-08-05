"""Check 4: Answer-Ready Content Structure. Implemented in Milestone M6."""

import re
import uuid
from typing import List, Optional, Tuple

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
DATE_PATTERN = r'\d{4}[-/]\d{1,2}[-/]\d{1,2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}'
ADDRESS_PATTERN = r'\d+\s+(?:[A-Za-z]+\.?)+\s+(?:Street|Avenue|Boulevard|Drive|Road|Lane|Way|Court|Place|Ave|St|Rd|Blvd|Dr)\b'
PHONE_PATTERN = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'

def detect_definitional_sentence(text: str) -> Tuple[int, str, str]:
    """Detect quality of entity definition in text.

    Returns (pts 0/4/8, matched_text, explanation).
    """
    # Check H1s first (strongest signal)
    if text.strip().startswith('<h1>') or text.strip().startswith('<h1 '):
        # Extract H1 content
        h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', text, re.IGNORECASE)
        if h1_match:
            h1_text = h1_match.group(1).lower()
            # Check for vague / filler H1
            if any(re.search(pat, h1_text) for pat in VAGUE_PHRASES):
                return 0, h1_match.group(1), "vague_h1"
            # Check for strong definitional pattern in H1
            for pat in DEFINITION_PATTERNS:
                if re.search(pat, h1_match.group(1), re.IGNORECASE):
                    return 8, h1_match.group(1), "strong_definition_in_h1"
            # H1 exists but is just not a definition
            return 4, h1_match.group(1), "h1_exists_not_definitional"

    # Check first 600 words of body text for definition (simplified)
    first_chunk = ' '.join(text.split()[:600]).lower()
    for pat in DEFINITION_PATTERNS:
        match = re.search(pat, first_chunk, re.IGNORECASE)
        if match:
            snippet = ' '.join(text.split()[max(0, match.start()//10-3):match.end()//10+6])
            return 4, snippet.strip(), "definition_in_body_not_h1"

    # Check for vague phrases in text
    for phrase in VAGUE_PHRASES:
        if phrase.lower() in text.lower():
            return 0, phrase, "vague_phrase"

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

    Returns (pts 0/8, list_of_facts_found).
    """
    facts = []

    # Look for numbers
    num_matches = re.findall(NUMBER_PATTERN, text)
    facts.extend(num_matches)

    # Look for dates
    date_matches = re.findall(DATE_PATTERN, text)
    facts.extend(date_matches)

    # Look for addresses
    address_matches = re.findall(ADDRESS_PATTERN, text)
    facts.extend(address_matches)

    # Look for phone numbers
    phone_matches = re.findall(PHONE_PATTERN, text)
    facts.extend(phone_matches)

    # Score based on number of facts found (up to 8 points)
    if len(facts) >= 10:
        return 8, facts  # 8 points for many specific facts
    elif len(facts) >= 5:
        return 4, facts  # 4 points for some facts
    elif len(facts) >= 2:
        return 2, facts  # 2 points for a few facts
    else:
        return 0, facts  # 0 points for few facts

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

            if reason == "vague_phrase":
                findings.append(Finding(
                    id=str(uuid.uuid4()),
                    check_id=CHECK_ID,
                    title="Generic marketing copy detected",
                    severity=Severity.medium,
                    confidence=Confidence.high,
                    page_url=page.url,
                    evidence=f"Generic phrase: '{matched_text}'",
                    why_it_matters=(
                        "Generic marketing copy has low extractable value for AI engines. "
                        "AI prefers specific, factual statements about your business for accurate citations."
                    ),
                    recommended_fix=(
                        f"<!-- Replace generic marketing copy with specific, factual content -->\n"
                        f"Original: \"{matched_text}\"\\n\\n"
                        f"Suggested: \"Our [service type] business has served [number] clients since [year] in [location].\""
                    ),
                ))

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

        score, facts_found = detect_specific_facts(page.body_text)

        if facts_found:
            # Add finding about specific facts found
            if score > 0:
                findings.append(Finding(
                    id=str(uuid.uuid4()),
                    check_id=CHECK_ID,
                    title="Extractable specific facts detected",
                    severity=Severity.low,
                    confidence=Confidence.high,
                    page_url=page.url,
                    evidence=f"Facts found: {', '.join(facts_found[:3])}{'...' if len(facts_found) > 3 else ''}",
                    why_it_matters=(
                        "Specific facts (numbers, dates, locations, credentials) provide extractable content "
                        "that AI engines can quote directly in answers about your business."
                    ),
                    recommended_fix=(
                        f"<!-- These facts demonstrate your business has specific, verifiable information -->\n"
                        f"* Founded: {facts_found[0] if facts_found else '[year]'}\\n"
                        f"* Customers served: {facts_found[1] if len(facts_found) > 1 else '[number]'}\\n"
                        f"* Service area: {facts_found[2] if len(facts_found) > 2 else '[location]'}\\n"
                    ),
                ))
        else:
            # Add finding about lack of specific facts
            findings.append(Finding(
                id=str(uuid.uuid4()),
                check_id=CHECK_ID,
                title="No specific facts found",
                severity=Severity.high,
                confidence=Confidence.high,
                page_url=page.url,
                evidence="No numbers, dates, addresses, or credentials detected in page content",
                why_it_matters=(
                    "Without specific facts, AI engines must rely on generic marketing copy to describe your business, "
                    "leading to incomplete or inaccurate AI-generated answers."
                ),
                recommended_fix=(
                    f"<!-- Add specific factual content to your service page -->\n"
                    f"* Founded: [Year your business was established]\\n"
                    f"* Customers served: [Number of customers]\\n"
                    f"* Service area: [City, State, or region you serve]\\n"
                    f"* Certifications: [Relevant certifications or licenses]\\n"
                    f"* Revenue: $[Annual revenue or typical project size]"
                ),
            ))

    # Calculate generic filler ratio score (up to 6 points)
    filler_score = calculate_generic_filler_ratio(' '.join(all_text_chunks))
    score += filler_score

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