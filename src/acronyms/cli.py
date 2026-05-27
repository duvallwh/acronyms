from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import shutil
import sys

from .extractor import AcronymResult, extract_acronyms_from_pdf


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Extract acronyms from a PDF using parenthesized uppercase terms like (AAA)."
    )
    parser.add_argument("pdf", type=Path, help="Path to the PDF file to scan.")
    parser.add_argument(
        "--json",
        nargs="?",
        const="",
        metavar="PATH",
        help="Write results as JSON. If PATH is omitted, use the PDF filename with .json. Use '-' to print JSON.",
    )
    parser.add_argument(
        "--csv",
        nargs="?",
        const="",
        metavar="PATH",
        help="Write results to a CSV file. If PATH is omitted, use the PDF filename with .csv.",
    )
    args = parser.parse_args(argv)

    try:
        results = extract_acronyms_from_pdf(args.pdf)
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    csv_path = _resolve_output_path(args.csv, args.pdf, ".csv") if args.csv is not None else None
    json_path = _resolve_output_path(args.json, args.pdf, ".json") if args.json is not None else None

    if csv_path is not None:
        _write_csv(csv_path, results)
        print(f"Wrote CSV to {csv_path}")

    if args.json is not None:
        json_text = json.dumps([result.as_dict() for result in results], indent=2)
        if json_path is None:
            print(json_text)
        else:
            _write_text(json_path, json_text)
            print(f"Wrote JSON to {json_path}")
    else:
        _print_table(results)

    return 0


def _resolve_output_path(requested_path: str, pdf_path: Path, suffix: str) -> Path | None:
    if requested_path == "-":
        return None

    if requested_path:
        return Path(requested_path)

    return pdf_path.with_suffix(suffix)


def _write_text(path: Path, text: str) -> None:
    path.write_text(f"{text}\n", encoding="utf-8")


def _write_csv(path: Path, results: list[AcronymResult]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["acronym", "definition", "count", "first_page", "pages", "examples"],
        )
        writer.writeheader()
        for result in results:
            row = result.as_dict()
            row["pages"] = "; ".join(str(page) for page in row["pages"])
            row["examples"] = " | ".join(result.examples)
            writer.writerow(row)


def _print_table(results: list[AcronymResult], terminal_width: int | None = None) -> None:
    if not results:
        print("No acronyms found.")
        return

    width = terminal_width if terminal_width is not None else shutil.get_terminal_size(fallback=(120, 24)).columns
    if width < 100:
        _print_compact(results)
        return

    rows = [
        (
            result.acronym,
            result.definition or "",
            str(result.count),
            str(result.first_page or ""),
            ", ".join(str(page) for page in sorted(result.pages)),
        )
        for result in results
    ]
    headers = ("Acronym", "Definition", "Count", "First page", "Pages")
    widths = [
        max(len(headers[index]), *(len(row[index]) for row in rows))
        for index in range(len(headers))
    ]

    print(_format_row(headers, widths))
    print(_format_row(tuple("-" * width for width in widths), widths))
    for row in rows:
        print(_format_row(row, widths))


def _format_row(row: tuple[str, ...], widths: list[int]) -> str:
    return "  ".join(value.ljust(widths[index]) for index, value in enumerate(row))


def _print_compact(results: list[AcronymResult]) -> None:
    for index, result in enumerate(results):
        print(f"{result.acronym} (count={result.count}, first_page={result.first_page or ''})")
        if result.definition:
            print(f"  Definition: {result.definition}")
        print(f"  Pages: {', '.join(str(page) for page in sorted(result.pages))}")
        if index != len(results) - 1:
            print()