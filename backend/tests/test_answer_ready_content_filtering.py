import unittest

from checks.answer_ready import extract_business_owned_text


class AnswerReadyContentFilteringTests(unittest.TestCase):
    def test_review_content_is_excluded_from_business_owned_text(self):
        html = (
            "<main>"
            "<p>We are a full-service electrical contractor serving the greater Seattle area.</p>"
            "<div>"
            "<p>What our customers say</p>"
            "<p>I would highly recommend this company for their professionalism.</p>"
            "</div>"
            "</main>"
        )

        cleaned_text = extract_business_owned_text(html)

        self.assertIn("We are a full-service electrical contractor", cleaned_text)
        self.assertNotIn("I would highly recommend", cleaned_text)
        self.assertNotIn("What our customers say", cleaned_text)


if __name__ == "__main__":
    unittest.main()
