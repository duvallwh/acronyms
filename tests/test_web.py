import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from acronyms.extractor import AcronymResult
from acronyms.web import create_app


class WebApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_app())

    @patch("acronyms.web.extract_acronyms_from_pdf_bytes")
    def test_extracts_acronyms_from_uploaded_pdf(self, extract_mock):
        extract_mock.return_value = [
            AcronymResult(
                acronym="NASA",
                count=2,
                pages={1, 3},
                definition="National Aeronautics and Space Administration",
                examples=["National Aeronautics and Space Administration (NASA)"],
            )
        ]

        response = self.client.post(
            "/api/extract",
            files={"file": ("paper.pdf", b"%PDF-1.4 sample", "application/pdf")},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            [
                {
                    "acronym": "NASA",
                    "definition": "National Aeronautics and Space Administration",
                    "count": 2,
                    "first_page": 1,
                    "pages": [1, 3],
                    "examples": ["National Aeronautics and Space Administration (NASA)"],
                }
            ],
        )
        extract_mock.assert_called_once_with(b"%PDF-1.4 sample")

    def test_rejects_non_pdf_uploads(self):
        response = self.client.post(
            "/api/extract",
            files={"file": ("notes.txt", b"not a pdf", "text/plain")},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Please upload a PDF file.")

    @patch("acronyms.web.extract_acronyms_from_pdf_bytes", side_effect=ValueError("bad pdf"))
    def test_returns_extraction_errors(self, _extract_mock):
        response = self.client.post(
            "/api/extract",
            files={"file": ("paper.pdf", b"broken", "application/pdf")},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Unable to extract acronyms: bad pdf")


if __name__ == "__main__":
    unittest.main()
