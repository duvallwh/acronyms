# Acronym Extractor

This project now includes a React frontend backed by the existing Python PDF acronym extractor. You can still use the CLI, but the primary interface is a web app for uploading PDFs, reviewing results, filtering acronyms, and exporting JSON or CSV.

## Components

- **Python API and extractor** in `/tmp/workspace/duvallwh/acronyms/src/acronyms`
- **React frontend** in `/tmp/workspace/duvallwh/acronyms/frontend`
- **CLI** in `/tmp/workspace/duvallwh/acronyms/src/acronyms/cli.py`

## Backend setup

Install the package in editable mode:

```bash
python -m pip install -e .
```

Start the API server:

```bash
python -m acronyms.web
```

The API exposes `POST /api/extract` and expects a multipart upload named `file` containing a PDF.

## Frontend setup

Install frontend dependencies and start the React dev server:

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server proxies API requests to `http://127.0.0.1:8000`, so run the backend and frontend in separate terminals during local development.

## CLI usage

Run the extractor with a PDF path:

```bash
python -m acronyms "path/to/file.pdf"
```

Write JSON using the PDF filename:

```bash
python -m acronyms "path/to/file.pdf" --json
```

Write CSV using the PDF filename:

```bash
python -m acronyms "path/to/file.pdf" --csv
```

## Testing

Backend tests:

```bash
python -m unittest discover -s tests
```

Frontend tests and build:

```bash
cd frontend
npm test
npm run build
```
