from __future__ import annotations

from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
import re

from pypdf import PdfReader


ACRONYM_RE = re.compile(r"\(([A-Z][A-Z0-9&./ -]{1,24}[A-Z0-9])\)")
ACRONYM_WITH_DEFINITION_RE = re.compile(r"\b([A-Z][A-Z0-9&./-]{1,24}[A-Z0-9])\s*\(([^()]{3,250})\)")
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

    return _extract_acronyms_from_reader(PdfReader(path))


def extract_acronyms_from_pdf_bytes(pdf_bytes: bytes) -> list[AcronymResult]:
    return _extract_acronyms_from_reader(PdfReader(BytesIO(pdf_bytes)))


def _extract_acronyms_from_reader(reader: PdfReader) -> list[AcronymResult]:
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
            definition = _normalize_definition(match.group(2))
            if not _looks_like_acronym(acronym) or not _looks_like_reverse_definition(definition):
                continue

            result = _record_acronym(results, acronym, page_number, normalized_text, match.start(), match.end())
            if result.definition is None:
                result.definition = definition

        for match in ACRONYM_RE.finditer(normalized_text):
            acronym = _normalize_acronym(match.group(1))
            if not _looks_like_acronym(acronym):
                continue

            definition = _guess_definition(normalized_text[: match.start()], acronym)
            if not _should_keep_parenthesized_acronym(acronym, definition, normalized_text, match.start(), match.end()):
                continue

            result = _record_acronym(results, acronym, page_number, normalized_text, match.start(), match.end())
            if result.definition is None:
                result.definition = definition

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


def _looks_like_definition(value: str) -> bool:
    words = WORD_RE.findall(value)
    if not words:
        return False

    return any(character.islower() for character in value)


def _looks_like_reverse_definition(value: str) -> bool:
    if not _looks_like_definition(value):
        return False

    if re.search(r"[=<>]", value) or "/g" in value:
        return False

    words = WORD_RE.findall(value)
    if len(words) == 1:
        word = words[0]
        return len(word) > 3 and not word.islower()

    return True


def _should_keep_parenthesized_acronym(
    acronym: str,
    definition: str | None,
    text: str,
    start: int,
    end: int,
) -> bool:
    if end < len(text) and text[end].isalnum():
        return False

    tokens = acronym.split()
    if len(tokens) > 2:
        return False

    if len(tokens) == 2 and any(len(token) == 1 for token in tokens if token.isalpha()):
        return False

    if definition:
        return True

    if " " in acronym:
        return False

    if len(acronym) > 10:
        return False

    if acronym.isalpha() and len(acronym) > 5:
        return False

    return not _is_uppercase_label_context(text, start, end)


def _is_uppercase_label_context(text: str, start: int, end: int, radius: int = 80) -> bool:
    context = text[max(0, start - radius) : min(len(text), end + radius)]
    letters = [character for character in context if character.isalpha()]
    if len(letters) < 12:
        return False

    uppercase = sum(1 for character in letters if character.isupper())
    return uppercase / len(letters) >= 0.75


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
