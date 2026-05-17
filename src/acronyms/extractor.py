from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re

from pypdf import PdfReader


ACRONYM_RE = re.compile(r"\(([A-Z][A-Z0-9&./ -]{1,24}[A-Z0-9])\)")
ACRONYM_WITH_DEFINITION_RE = re.compile(r"\b([A-Z][A-Z0-9&./ -]{1,24}[A-Z0-9])\s*\(([^()]{3,250})\)")
WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9'-]*")
CONNECTOR_WORDS = {"a", "an", "and", "for", "in", "of", "on", "or", "the", "to"}


@dataclass
class AcronymResult:
    acronym: str
    count: int = 0
    pages: set[int] = field(default_factory=set)
    definition: str | None = None
    examples: list[str] = field(default_factory=list)

    @property
    def first_page(self) -> int | None:
        return min(self.pages) if self.pages else None

    def as_dict(self) -> dict[str, object]:
        return {
            "acronym": self.acronym,
            "definition": self.definition,
            "count": self.count,
            "first_page": self.first_page,
            "pages": sorted(self.pages),
            "examples": self.examples,
        }


def extract_acronyms_from_pdf(pdf_path: str | Path) -> list[AcronymResult]:
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    reader = PdfReader(path)
    page_text = []
    for page_number, page in enumerate(reader.pages, start=1):
        page_text.append((page_number, page.extract_text() or ""))

    return find_acronyms(page_text)


def find_acronyms(page_text: list[tuple[int, str]]) -> list[AcronymResult]:
    results: dict[str, AcronymResult] = {}

    for page_number, text in page_text:
        normalized_text = _normalize_whitespace(text)
        for match in ACRONYM_WITH_DEFINITION_RE.finditer(normalized_text):
            acronym = _normalize_acronym(match.group(1))
            if not _looks_like_acronym(acronym):
                continue

            definition = _normalize_definition(match.group(2))
            result = _record_acronym(results, acronym, page_number, normalized_text, match.start(), match.end())
            if result.definition is None:
                result.definition = definition

        for match in ACRONYM_RE.finditer(normalized_text):
            acronym = _normalize_acronym(match.group(1))
            if not _looks_like_acronym(acronym):
                continue

            result = _record_acronym(results, acronym, page_number, normalized_text, match.start(), match.end())
            if result.definition is None:
                result.definition = _guess_definition(normalized_text[: match.start()], acronym)

    return sorted(results.values(), key=lambda item: item.acronym)


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _normalize_acronym(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def _normalize_definition(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def _record_acronym(
    results: dict[str, AcronymResult],
    acronym: str,
    page_number: int,
    text: str,
    start: int,
    end: int,
) -> AcronymResult:
    result = results.setdefault(acronym, AcronymResult(acronym=acronym))
    result.count += 1
    result.pages.add(page_number)

    context = _context_around(text, start, end)
    if context and context not in result.examples:
        result.examples.append(context)

    return result


def _looks_like_acronym(value: str) -> bool:
    letters = [character for character in value if character.isalpha()]
    return len(letters) >= 2 and all(character.upper() == character for character in letters)


def _context_around(text: str, start: int, end: int, radius: int = 80) -> str:
    context_start = max(0, start - radius)
    context_end = min(len(text), end + radius)
    return text[context_start:context_end].strip()


def _guess_definition(text_before_acronym: str, acronym: str) -> str | None:
    compact_acronym = re.sub(r"[^A-Z0-9]", "", acronym.upper())
    if not compact_acronym:
        return None

    words = WORD_RE.findall(text_before_acronym[-500:])
    if not words:
        return None

    selected: list[str] = []
    acronym_index = len(compact_acronym) - 1

    for word in reversed(words):
        if word.lower() in CONNECTOR_WORDS:
            continue

        initial = word[0].upper()
        if initial == compact_acronym[acronym_index]:
            selected.append(word)
            acronym_index -= 1
            if acronym_index < 0:
                return " ".join(reversed(selected))
        elif selected and len(selected) > len(compact_acronym) * 2:
            break

    return None
