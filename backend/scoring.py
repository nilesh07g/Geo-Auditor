"""Weighted GEO score calculator. Implemented in Milestone M7."""

from typing import List, Dict, Any, Union
from models import CheckResult


def calculate_weighted_geo_score(check_results: List[CheckResult]) -> Dict[str, Any]:
    """Calculate the weighted GEO score from multiple check results.

    Args:
        check_results: List of CheckResult objects from all four checks

    Returns:
        Dict containing total score, weighted score, max score, and individual breakdown
    """
    total_score = 0
    max_possible_score = 0
    weighted_total = 0
    weighted_max = 0
    breakdown = []

    for check in check_results:
        total_score += check.score
        max_possible_score += check.max_score
        weighted_total += check.weighted_score
        weighted_max += check.weight

        breakdown.append({
            "check_id": check.check_id,
            "check_name": check.check_name,
            "score": check.score,
            "max_score": check.max_score,
            "weight": check.weight,
            "weighted_score": check.weighted_score,
            "weight_percentage": round((check.weight / 100) * 100)
        })

    # Calculate overall weighted score (normalized to 100)
    if weighted_max > 0:
        overall_score = round((weighted_total / weighted_max) * 100)
    else:
        overall_score = 0

    # Calculate grade based on score
    grade = get_geo_grade(overall_score)

    return {
        "total_score": total_score,
        "max_possible_score": max_possible_score,
        "weighted_score": weighted_total,
        "max_weighted_score": weighted_max,
        "overall_score": overall_score,
        "grade": grade,
        "breakdown": breakdown
    }


def get_geo_grade(score: int) -> str:
    """Convert numeric score to letter grade."""
    if score >= 80:
        return "Strong"
    elif score >= 60:
        return "Moderate gaps"
    elif score >= 40:
        return "At Risk"
    else:
        return "Critical"