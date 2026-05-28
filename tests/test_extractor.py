import unittest
from unittest.mock import patch

from acronyms.extractor import extract_acronyms_from_pdf_bytes, find_acronyms


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

    def test_ignores_all_caps_diagram_label_before_parentheses(self):
        text = "MAXIMUM ALLOWABLE SET PRESSURE FOR A SINGLE VALVE BLOWDOWN (TYPICAL) SEE NOTE 6"

        self.assertEqual(find_acronyms([(1, text)]), [])

    def test_ignores_parenthesized_uppercase_label_without_definition(self):
        text = "GASOLINE WATER BENZENE ACETONE (LIQUID) AMMONIA (LIQUID) OXYGEN"

        self.assertEqual(find_acronyms([(1, text)]), [])

    def test_keeps_multiword_acronym_with_definition(self):
        text = "Goddard Earth Sciences Data Information Services Center (GES DISC) hosts the data."

        results = {result.acronym: result for result in find_acronyms([(1, text)])}

        self.assertEqual(
            results["GES DISC"].definition,
            "Goddard Earth Sciences Data Information Services Center",
        )

    def test_ignores_variable_style_reverse_parenthetical(self):
        text = "HYDRAULIC JUMP SUPERCRITICAL FLOW (Fr1 > 1) SUBCRITICAL FLOW (Fr2 < 1)"

        self.assertEqual(find_acronyms([(1, text)]), [])

    def test_ignores_formula_fragment_inside_larger_formula(self):
        text = "Ether Diethyl ether (C2H3)2O and Urea Urea (NH2)2CO are listed."

        self.assertEqual(find_acronyms([(1, text)]), [])

    def test_ignores_long_plain_label_without_definition(self):
        text = "SINGLE SPIRAL RINGS GRID TILE (CERAMIC) CHECKER BRICK"

        self.assertEqual(find_acronyms([(1, text)]), [])


class ExtractPdfBytesTests(unittest.TestCase):
    @patch('acronyms.extractor.find_acronyms')
    @patch('acronyms.extractor.PdfReader')
    def test_extracts_acronyms_from_pdf_bytes(self, pdf_reader_mock, find_acronyms_mock):
        page = type('Page', (), {'extract_text': lambda self: 'National Aeronautics and Space Administration (NASA)'})()
        pdf_reader_mock.return_value.pages = [page]
        find_acronyms_mock.return_value = ['sentinel']

        results = extract_acronyms_from_pdf_bytes(b'%PDF-1.4 sample')

        self.assertEqual(results, ['sentinel'])
        pdf_reader_mock.assert_called_once()
        stream = pdf_reader_mock.call_args.args[0]
        self.assertEqual(stream.read(), b'%PDF-1.4 sample')
        find_acronyms_mock.assert_called_once_with(
            [(1, 'National Aeronautics and Space Administration (NASA)')]
        )

    def test_raises_for_invalid_pdf_bytes(self):
        with self.assertRaises(Exception):
            extract_acronyms_from_pdf_bytes(b'not a pdf')


if __name__ == "__main__":
    unittest.main()
