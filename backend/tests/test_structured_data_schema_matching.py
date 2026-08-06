import unittest

from checks.structured_data import score_schemas_found


class StructuredDataSchemaMatchingTests(unittest.TestCase):
    def test_case_insensitive_schema_matching(self):
        found_types = {"faqpage", "organization"}
        expected_types = {"FAQPage", "LocalBusiness"}

        score, found_expected, missing_expected = score_schemas_found(found_types, expected_types)

        self.assertEqual(score, 16)
        self.assertEqual(found_expected, {"faqpage"})
        self.assertEqual(missing_expected, {"localbusiness"})


if __name__ == "__main__":
    unittest.main()
