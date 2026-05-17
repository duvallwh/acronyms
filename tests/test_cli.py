import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from acronyms.cli import _resolve_output_path


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


if __name__ == "__main__":
    unittest.main()