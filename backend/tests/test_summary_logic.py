import unittest

from main import is_positive_finding
from models import Confidence, Finding, Severity


class SummaryLogicTests(unittest.TestCase):
    def test_negative_finding_is_not_treated_as_strength(self):
        finding = Finding(
            title="Generic marketing copy detected",
            severity=Severity.medium,
            confidence=Confidence.high,
            evidence="This is generic marketing copy",
            why_it_matters="It reduces factual clarity.",
            recommended_fix="Replace the marketing-heavy sentence with factual content.",
            check_id="answer_ready",
        )

        self.assertFalse(is_positive_finding(finding))

    def test_positive_finding_with_no_action_recommendation_is_treated_as_strength(self):
        finding = Finding(
            title="Extractable specific facts detected",
            severity=Severity.low,
            confidence=Confidence.high,
            evidence="We have been operating since 2012.",
            why_it_matters="Specific factual sentences provide extractable content.",
            recommended_fix="No action required. This page contains well-formed factual content.",
            check_id="answer_ready",
        )

        self.assertTrue(is_positive_finding(finding))


if __name__ == "__main__":
    unittest.main()
