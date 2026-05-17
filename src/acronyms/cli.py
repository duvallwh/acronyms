from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

from .extractor import AcronymResult, extract_acronyms_from_pdf


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Extract acronyms from a PDF using parenthesized uppercase terms like (AAA)."
    )
    parser.add_argument("pdf", type=Path, help="Path to the PDF file to scan.")
    parser.add_argument("--json", action="store_true", help="Print results as JSON.")
    parser.add_argument("--csv", type=Path, help="Write results to a CSV file.")
    args = parser.parse_args(argv)

    try:
        results = extract_acronyms_from_pdf(args.pdf)
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    if args.csv:
        _write_csv(args.csv, results)

    if args.json:
        print(json.dumps([result.as_dict() for result in results], indent=2))
    else:
        _print_table(results)

    return 0


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


def _print_table(results: list[AcronymResult]) -> None:
    if not results:
        print("No acronyms found.")
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