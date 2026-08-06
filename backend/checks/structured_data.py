"""Check 3: Structured Data for AI Extraction. Implemented in Milestone M6."""

import json
import uuid
from typing import Dict, List, Optional, Tuple, Set

from models import (
    CheckResult,
    Confidence,
    Finding,
    PageData,
    Severity,
)

CHECK_ID = "structured_data"
CHECK_NAME = "Structured Data for AI Extraction"
MAX_SCORE = 25
WEIGHT = 25

# Expected schema types for different business categories
# This is a simplified mapping - in practice, you'd want more comprehensive categories
EXPECTED_SCHEMAS_BY_CATEGORY = {
    "local_service": {"LocalBusiness", "Service", "FAQPage"},
    "saas": {"SoftwareApplication", "FAQPage", "Article"},
    "ecommerce": {"Product", "Offer", "FAQPage", "AggregateRating"},
    "default": {"Organization", "LocalBusiness", "FAQPage"}  # fallback/default
}


def extract_jsonld_types(page: Optional[PageData], preserve_case: bool = False) -> Set[str]:
    """Extract all JSON-LD @type values from a page."""
    if not page:
        return set()

    types = set()
    for schema in page.json_ld_schemas:
        schema_type = schema.get("@type")
        if isinstance(schema_type, list):
            for t in schema_type:
                if isinstance(t, str):
                    types.add(t if preserve_case else t.lower())
        elif isinstance(schema_type, str):
            types.add(schema_type if preserve_case else schema_type.lower())
    return types


def normalize_schema_types(schema_types: Set[str]) -> Set[str]:
    """Normalize schema type names to a consistent case for comparison."""
    return {schema_type.lower() for schema_type in schema_types if isinstance(schema_type, str)}


def score_schemas_found(found_types: Set[str], expected_types: Set[str]) -> Tuple[int, Set[str], Set[str]]:
    """
    Score based on how many expected schema types are found.
    Returns (score, found_expected, missing_expected)
    """
    normalized_found_types = normalize_schema_types(found_types)
    normalized_expected_types = normalize_schema_types(expected_types)

    found_expected = normalized_found_types.intersection(normalized_expected_types)
    missing_expected = normalized_expected_types - normalized_found_types

    # Score: 0 if none found, 8 if <50% found, 16 if >=50% found, 25 if all found
    if not expected_types:
        return 25, found_expected, missing_expected

    ratio = len(found_expected) / len(expected_types)
    if ratio == 0:
        score = 0
    elif ratio < 0.5:
        score = 8
    elif ratio < 1.0:
        score = 16
    else:
        score = 25

    return score, found_expected, missing_expected


def infer_business_category(pages: List[Optional[PageData]]) -> str:
    """Simple heuristic to infer business category from page content."""
    # This is a simplified implementation - in practice you'd use more sophisticated NLP
    # For now, we'll default to local_service as it's the most common case
    # A real implementation might look for keywords in text, schema types, etc.
    return "local_service"


def evaluate_structured_data(
    homepage: Optional[PageData],
    about_page: Optional[PageData],
    service_page: Optional[PageData],
) -> CheckResult:
    """Evaluate Check 3: Structured Data for AI Extraction.

    Inputs come from M4 CrawlResult fields. Each is a PageData or None.

    Returns:
        CheckResult with score, weighted_score, and findings.
    """
    findings: List[Finding] = []
    score = 0

    all_pages: List[Optional[PageData]] = [homepage, about_page, service_page]
    business_category = infer_business_category(all_pages)
    expected_types = EXPECTED_SCHEMAS_BY_CATEGORY.get(business_category, EXPECTED_SCHEMAS_BY_CATEGORY["default"])

    # Collect all JSON-LD types found across the 3 pages
    all_found_types: Set[str] = set()
    all_display_found_types: Set[str] = set()
    pages_with_schemas: List[Tuple[str, Set[str]]] = []  # (url, types_found)

    for page in all_pages:
        if page and page.json_ld_schemas:
            found_types = extract_jsonld_types(page)
            display_found_types = extract_jsonld_types(page, preserve_case=True)
            all_found_types.update(found_types)
            all_display_found_types.update(display_found_types)
            if found_types:
                pages_with_schemas.append((page.url, found_types))

    # Score based on schema coverage
    schema_score, found_expected, missing_expected = score_schemas_found(all_found_types, expected_types)
    score += schema_score

    # Preserve original display names for findings while using normalized values for matching
    display_missing_expected = {schema_type for schema_type in expected_types if schema_type.lower() in missing_expected}
    display_found_types = sorted(all_display_found_types) if all_display_found_types else []
    missing_display_types = sorted(display_missing_expected)

    # Generate findings
    if not pages_with_schemas:
        # No JSON-LD schemas found at all
        findings.append(Finding(
            id=str(uuid.uuid4()),
            check_id=CHECK_ID,
            title="No JSON-LD structured data found on any crawled page",
            severity=Severity.high,
            confidence=Confidence.high,
            page_url=homepage.url if homepage else "unknown",
            evidence="Searched Homepage, About page, and Service page. No <script type=\"application/ld+json\"> tags found.",
            why_it_matters=(
                "Without structured data, AI engines must rely solely on unstructured text to understand "
                "your business, products, services, and content. This increases the risk of misinterpretation "
                "and reduces your chances of being cited in AI-generated answers."
            ),
            recommended_fix=(
                "# Add JSON-LD structured data to your homepage:\n"
                '<script type="application/ld+json">\n'
                '{ "@context": "https://schema.org",\n'
                '  "@type": "LocalBusiness",\n'
                '  "name": "Your Business Name",\n'
                '  "url": "https://yourwebsite.com",\n'
                '  "telephone": "+1-234-567-8900",\n'
                '  "address": {\n'
                '    "@type": "PostalAddress",\n'
                '    "streetAddress": "123 Main St",\n'
                '    "addressLocality": "Your City",\n'
                '    "addressRegion": "ST",\n'
                '    "postalCode": "00000"\n'
                '  },\n'
                '  "description": "Clear description of your business and services."\n'
                '}\n'
                '</script>'
            ),
        ))
    elif missing_expected:
        # Some expected schemas are missing
        missing_str = ", ".join(missing_display_types)
        found_str = ", ".join(display_found_types) if display_found_types else "none"

        severity = Severity.medium if len(all_display_found_types) > len(display_missing_expected) else Severity.high

        findings.append(Finding(
            id=str(uuid.uuid4()),
            check_id=CHECK_ID,
            title=f"Missing expected structured data types: {missing_str}",
            severity=severity,
            confidence=Confidence.high,
            page_url=pages_with_schemas[0][0] if pages_with_schemas else (homepage.url if homepage else "unknown"),
            evidence=(
                f"Detected schema types: {found_str or 'none'}. "
                f"Missing expected schema types: {missing_str or 'none'}."
            ),
            why_it_matters=(
                f"Missing schema types like {missing_str.split(',')[0].strip()} reduce AI engines' ability "
                f"to accurately extract specific information about your {business_category.replace('_', ' ')} business. "
                f"This can lead to incomplete or incorrect representations in AI-generated answers."
            ),
            recommended_fix=(
                "\n\n".join(
                    [
                        f"# Add {schema_type} schema markup to your JSON-LD.\n"
                        f'<script type="application/ld+json">\n'
                        f'{{ "@context": "https://schema.org", "@type": "{schema_type}" }}\n'
                        f'</script>'
                        for schema_type in missing_display_types
                    ]
                )
            ),
        ))
    else:
        # All expected schemas found - no findings needed for this aspect
        pass

    # Check for schema validation errors (basic check)
    validation_errors = []
    for page in all_pages:
        if page and page.json_ld_schemas:
            for i, schema in enumerate(page.json_ld_schemas):
                # Basic validation: check for required @context and @type
                if "@context" not in schema:
                    validation_errors.append(f"Missing @context in schema #{i+1} on {page.url}")
                if "@type" not in schema:
                    validation_errors.append(f"Missing @type in schema #{i+1} on {page.url}")

    if validation_errors:
        findings.append(Finding(
            id=str(uuid.uuid4()),
            check_id=CHECK_ID,
            title="Structured data validation errors found",
            severity=Severity.medium,
            confidence=Confidence.high,
            page_url=validation_errors[0].split("on ")[-1] if "on " in validation_errors[0] else (homepage.url if homepage else "unknown"),
            evidence="; ".join(validation_errors[:3]),  # Show first 3 errors
            why_it_matters=(
                "Invalid structured data may be ignored by AI engines or cause parsing errors, "
                "wasting the opportunity to provide clear machine-readable signals about your business."
            ),
            recommended_fix=(
                "# Validate your JSON-LD using Google's Rich Results Test:\n"
                "# https://search.google.com/test/rich-results\n"
                "# Common fixes:\n"
                '# - Ensure "@context": "https://schema.org" is present\n'
                '# - Ensure "@type" is a valid schema.org type\n'
                '# - Remove trailing commas\n'
                '# - Use quotes around property names and string values'
            ),
        ))

    # Bonus points for having any schemas (even if not all expected)
    if all_found_types and schema_score < 25:
        # Give some credit for having schemas, even if not all expected ones
        bonus = min(5, len(all_found_types))  # Up to 5 bonus points for diversity
        score = min(score + bonus, MAX_SCORE)

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