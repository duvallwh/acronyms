from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from .extractor import extract_acronyms_from_pdf_bytes

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIST_DIR = REPOSITORY_ROOT / "frontend" / "dist"


def create_app() -> FastAPI:
    app = FastAPI(title="Acronym Extractor API")

    @app.post("/api/extract")
    async def extract(file: UploadFile = File(...)) -> list[dict[str, object]]:
        if not file.filename:
            raise HTTPException(status_code=400, detail="Please choose a PDF file.")

        if not _is_pdf_upload(file):
            raise HTTPException(status_code=400, detail="Please upload a PDF file.")

        payload = await file.read()
        if not payload:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        try:
            results = extract_acronyms_from_pdf_bytes(payload)
        except Exception as error:
            raise HTTPException(status_code=400, detail=f"Unable to extract acronyms: {error}") from error

        return [result.as_dict() for result in results]

    if FRONTEND_DIST_DIR.exists():
        app.mount(
            "/assets",
            StaticFiles(directory=FRONTEND_DIST_DIR / "assets"),
            name="frontend-assets",
        )

        @app.get("/{path:path}", include_in_schema=False)
        async def frontend(path: str) -> FileResponse:
            candidate = FRONTEND_DIST_DIR / path
            if path and candidate.exists() and candidate.is_file():
                return FileResponse(candidate)
            return FileResponse(FRONTEND_DIST_DIR / "index.html")

    return app


def _is_pdf_upload(file: UploadFile) -> bool:
    content_type = (file.content_type or "").lower()
    if content_type in {"application/pdf", "application/x-pdf"}:
        return True

    return bool(file.filename) and file.filename.lower().endswith(".pdf")


def main() -> int:
    uvicorn.run("acronyms.web:create_app", factory=True, host="127.0.0.1", port=8000)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
