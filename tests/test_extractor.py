import unittest

from acronyms.extractor import find_acronyms


class FindAcronymsTests(unittest.TestCase):
    def test_finds_parenthesized_acronyms_and_definitions(self):
        text = (
            "Advanced Analytics Application (AAA) works with "
            "National Aeronautics and Space Administration (NASA)."
        )

        results = {result.acronym: result for result in find_acronyms([(1, text)])}

        self.assertEqual(results["AAA"].definition, "Advanced Analytics Application")
        self.assertEqual(results["NASA"].definition, "National Aeronautics Space Administration")

    def test_ignores_lowercase_parentheses(self):
        text = "This has a normal parenthetical phrase (not an acronym)."

        self.assertEqual(find_acronyms([(1, text)]), [])

    def test_finds_acronym_before_parenthesized_definition(self):
        text = "PRISMA (PRecipitation Inference from Satellite Modalities via generAtive modeling) works."

        results = {result.acronym: result for result in find_acronyms([(1, text)])}

        self.assertEqual(
            results["PRISMA"].definition,
            "PRecipitation Inference from Satellite Modalities via generAtive modeling",
        )


if __name__ == "__main__":
    unittest.main()