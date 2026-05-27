import unittest
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from contextlib import redirect_stdout

from acronyms.cli import _print_table, _resolve_output_path
from acronyms.extractor import AcronymResult


class OutputPathTests(unittest.TestCase):
    def test_uses_pdf_name_when_output_path_is_blank(self):
        pdf_path = Path("paper.pdf")

        self.assertEqual(_resolve_output_path("", pdf_path, ".csv"), Path("paper.csv"))
        self.assertEqual(_resolve_output_path("", pdf_path, ".json"), Path("paper.json"))

    def test_uses_explicit_output_path(self):
        self.assertEqual(
            _resolve_output_path("results/acronyms.csv", Path("paper.pdf"), ".csv"),
            Path("results/acronyms.csv"),
        )

    def test_dash_means_stdout_for_json(self):
        self.assertIsNone(_resolve_output_path("-", Path("paper.pdf"), ".json"))

    def test_preserves_pdf_directory_for_default_output(self):
        with TemporaryDirectory() as directory:
            pdf_path = Path(directory) / "paper.pdf"

            self.assertEqual(_resolve_output_path("", pdf_path, ".csv"), pdf_path.with_suffix(".csv"))


class PrintTableTests(unittest.TestCase):
    def test_uses_tabular_output_for_wide_terminal(self):
        output = StringIO()
        with redirect_stdout(output):
            _print_table([AcronymResult(acronym="NASA", count=1, pages={1}, definition="National Aeronautics Space Administration")], terminal_width=120)

        rendered = output.getvalue()
        self.assertIn("Acronym", rendered)
        self.assertIn("NASA", rendered)

    def test_uses_compact_output_for_narrow_terminal(self):
        output = StringIO()
        with redirect_stdout(output):
            _print_table([AcronymResult(acronym="NASA", count=2, pages={1, 3}, definition="National Aeronautics Space Administration")], terminal_width=60)

        rendered = output.getvalue()
        self.assertIn("NASA (count=2, first_page=1)", rendered)
        self.assertIn("  Definition: National Aeronautics Space Administration", rendered)
        self.assertIn("  Pages: 1, 3", rendered)


if __name__ == "__main__":
    unittest.main()