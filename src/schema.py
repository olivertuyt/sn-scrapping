"""Pydantic schema and deterministic post-extraction validation.

Each field decision: value, status (FOUND/NOT_FOUND/CONFLICT/MULTIPLE_CANDIDATES),
source_url, evidence (verbatim). Validation enforces the project hard rules:
no month inference from a year, evidence must be verbatim in the source text.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, Field

FieldStatus = str  # FOUND | NOT_FOUND | CONFLICT | MULTIPLE_CANDIDATES

# 設立 followed by year only, no month anywhere near (checked by caller with evidence)
_YEAR_ONLY = re.compile(r"^\s*(明治|大正|昭和|平成|令和)?\s*\d{1,4}\s*年\s*$")
_MONTH = re.compile(r"\d{1,2}\s*月|[一二三四五六七八九十]{1,3}月|睦月|如月|弥生|卯月|皐月|水無月|文月|葉月|長月|神無月|霜月|師走")
_ERA_YEAR = re.compile(r"(明治|大正|昭和|平成|令和)\s*\d{1,2}\s*年")
_GREGORIAN_YEAR_MONTH = re.compile(r"(\d{4})年(\d{1,2})月")
_ERA_YEAR_MONTH = re.compile(r"(明治|大正|昭和|平成|令和)(\d{1,2})年(\d{1,2})月")
_ERA_BASE_YEAR = {"明治": 1867, "大正": 1911, "昭和": 1925, "平成": 1988, "令和": 2018}
# Unicode whitespace incl. em-space (U+2003) and ideographic space (U+3000),
# which Japanese pages use inside addresses; the model normalizes these to " ".
_WS = re.compile("[\\s\\u2000-\\u200f\\u3000]+")


def _norm(s: str) -> str:
    return _WS.sub(" ", s).strip()


def _value_supported(field: str, value: str, evidence: str) -> bool:
    """Match a value to its quote, allowing only explicit year/month normalization."""
    compact_value = _WS.sub("", value)
    compact_evidence = _WS.sub("", evidence)
    if compact_value:
        for match in re.finditer(re.escape(compact_value), compact_evidence):
            before = compact_evidence[match.start() - 1:match.start()]
            after = compact_evidence[match.end():match.end() + 1]
            if compact_value[0].isdigit() and before and (before.isdigit() or before in ",."):
                continue
            if field == "capital" and after.isdigit():
                continue
            return True
    if field != "established_year_month":
        return False

    date = _GREGORIAN_YEAR_MONTH.fullmatch(compact_value)
    if not date:
        return False
    year, month = (int(part) for part in date.groups())
    # A parenthesized era year may separate the Gregorian year and month.
    for match in re.finditer(r"(\d{4})年(?:(?!\d{4}年).){0,25}?(\d{1,2})月", compact_evidence):
        if (int(match[1]), int(match[2])) == (year, month):
            return True
    for match in _ERA_YEAR_MONTH.finditer(compact_evidence):
        if (_ERA_BASE_YEAR[match[1]] + int(match[2]), int(match[3])) == (year, month):
            return True
    return False


class FieldDecision(BaseModel):
    value: str | list[str] | None = None
    status: FieldStatus = "NOT_FOUND"
    source_url: str | None = None
    evidence: str | None = None


class CompanyData(BaseModel):
    company_name: str
    seed_url: str
    head_office_address: FieldDecision = Field(default_factory=FieldDecision)
    representative: FieldDecision = Field(default_factory=FieldDecision)
    capital: FieldDecision = Field(default_factory=FieldDecision)
    established_year_month: FieldDecision = Field(default_factory=FieldDecision)


def validate_decision(field: str, d: FieldDecision, page_text: str | None) -> list[str]:
    """Deterministic checks for one field decision; returns problem list."""
    problems: list[str] = []

    if d.value is None or (isinstance(d.value, str) and not d.value.strip()):
        if d.status not in ("NOT_FOUND", "CONFLICT", "MULTIPLE_CANDIDATES"):
            problems.append(f"{field}: null value must have status NOT_FOUND/CONFLICT/MULTIPLE_CANDIDATES, got {d.status}")
        if d.status == "NOT_FOUND" and (d.source_url or d.evidence):
            problems.append(f"{field}: NOT_FOUND must not carry source_url/evidence")
        return problems

    # non-null value from here on
    if d.status not in ("FOUND", "MULTIPLE_CANDIDATES"):
        problems.append(f"{field}: non-null value needs status FOUND/MULTIPLE_CANDIDATES, got {d.status}")
    if not d.source_url:
        problems.append(f"{field}: non-null value missing source_url")
    if not d.evidence:
        problems.append(f"{field}: non-null value missing evidence")
    elif page_text is not None and _norm(d.evidence) not in _norm(page_text):
        problems.append(f"{field}: evidence is not a verbatim substring of the source page text")

    values = d.value if isinstance(d.value, list) else [d.value]
    if d.evidence:
        for value in values:
            if not _value_supported(field, value, d.evidence):
                problems.append(f"{field}: value '{value}' is not supported by evidence")

    # hard rule: never infer month from year alone
    if field == "established_year_month":
        for v in values:
            if _MONTH.search(v) and d.evidence and not _MONTH.search(d.evidence):
                problems.append(f"{field}: month present in value '{v}' but not in evidence — possible month inference")
            if _YEAR_ONLY.match(v) and d.evidence and _MONTH.search(d.evidence):
                problems.append(f"{field}: year-only value but evidence has a month — verify")
    return problems


def validate_company(c: CompanyData, texts_by_url: dict[str, str]) -> list[str]:
    """Validate all 4 field decisions against fetched page texts."""
    problems: list[str] = []
    for field in ("head_office_address", "representative", "capital", "established_year_month"):
        d = getattr(c, field)
        if d.value is not None and d.source_url and d.source_url not in texts_by_url:
            problems.append(f"{field}: source_url was never fetched: {d.source_url}")
        text = texts_by_url.get(d.source_url or "", None) if d.source_url else None
        problems.extend(validate_decision(field, d, text))
    return problems
