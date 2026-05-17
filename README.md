# Acronym Extractor

This program loads a PDF file, extracts its text, and finds acronyms introduced with parenthesized terms. It supports both `Definition (AAA)` and `AAA (definition)` patterns, including examples like `(NASA)`, `(SOC 2)`, and `PRISMA (PRecipitation Inference...)`.

## Setup

Install the project dependency:

```powershell
python -m pip install -e .
```

If you use `uv`, this also works:

```powershell
uv pip install -e .
```

## Usage

Run the extractor with a PDF path:

```powershell
python -m acronyms "path\to\file.pdf"
```

Or, after installing the project, use the script command:

```powershell
acronyms "path\to\file.pdf"
```

Output includes each acronym, the first page where it appears, how many times it was found, and a best-effort definition.

## Output Formats

Write JSON using the PDF filename:

```powershell
python -m acronyms "path\to\file.pdf" --json
```

Print JSON to the terminal:

```powershell
python -m acronyms "path\to\file.pdf" --json -
```

Write JSON to a specific file:

```powershell
python -m acronyms "path\to\file.pdf" --json acronyms.json
```

Write CSV using the PDF filename:

```powershell
python -m acronyms "path\to\file.pdf" --csv
```

Write CSV to a specific file:

```powershell
python -m acronyms "path\to\file.pdf" --csv acronyms.csv
```
