"""Tests for pipeline candidate selection beyond the first crawl depth."""

import json

import pytest

from src import pipeline
from src.crawler import CrawlResult
from src.schema import CompanyData, FieldDecision


def test_history_child_urls_follow_same_site_timeline_links():
    helper = getattr(pipeline, "_history_child_urls", None)
    assert callable(helper), "pipeline must expand discovered history pages"

    seed = "https://example.co.jp/"
    current = "https://example.co.jp/company/history/index.html"
    html = """
    <a href="/company/history/02.html">1937年～1949年</a>
    <a href="/company/history/03.html">1950年～1976年</a>
    <a href="/company/history/02.html#timeline">same page</a>
    <a href="https://outside.example/history/04.html">outside history</a>
    <a href="/company/profile.html">company profile</a>
    """

    assert helper(html, current, seed, {current}) == [
        "https://example.co.jp/company/history/02.html",
        "https://example.co.jp/company/history/03.html",
    ]


def test_readable_company_output_groups_values_and_keeps_audit_details():
    company = CompanyData(
        company_name="Nissui",
        seed_url="https://www.nissui.co.jp/",
        head_office_address=FieldDecision(
            value="東京都港区西新橋1-3-1 西新橋スクエア",
            status="FOUND",
            source_url="https://www.nissui.co.jp/corporate/index.html",
            evidence="本社 東京都港区西新橋1-3-1 西新橋スクエア",
        ),
        representative=FieldDecision(
            value=["田中輝", "山田花子"],
            status="MULTIPLE_CANDIDATES",
            source_url="https://www.nissui.co.jp/corporate/index.html",
            evidence="代表取締役社長 田中輝、代表取締役 山田花子",
        ),
        capital=FieldDecision(
            value="30,685百万円",
            status="FOUND",
            source_url="https://www.nissui.co.jp/corporate/index.html",
            evidence="資本金 30,685百万円",
        ),
        established_year_month=FieldDecision(
            value="1943年3月31日",
            status="FOUND",
            source_url="https://www.nissui.co.jp/ir/ir_qa/index.html",
            evidence="創業 1943年3月31日",
        ),
    )

    readable = pipeline.to_readable_company(company)

    assert readable["company_name"] == "Nissui"
    assert readable["website"] == "https://www.nissui.co.jp/"
    assert readable["head_offices"] == ["東京都港区西新橋1-3-1 西新橋スクエア"]
    assert readable["representatives"] == ["田中輝", "山田花子"]
    assert readable["capital"] == "30,685百万円"
    assert readable["established"] == "1943年3月31日"
    assert readable["sources"] == {
        "profile": "https://www.nissui.co.jp/corporate/index.html",
        "established": "https://www.nissui.co.jp/ir/ir_qa/index.html",
    }
    assert readable["field_sources"]["head_offices"] == readable["sources"]["profile"]
    assert readable["field_sources"]["established"] == readable["sources"]["established"]
    assert readable["evidence"]["representatives"] == "代表取締役社長 田中輝、代表取締役 山田花子"
    assert readable["statuses"]["representatives"] == "MULTIPLE_CANDIDATES"


def test_readable_company_output_keeps_different_profile_sources_unambiguous():
    company = CompanyData(
        company_name="Example",
        seed_url="https://example.co.jp/",
        head_office_address=FieldDecision(
            value="本社住所",
            status="FOUND",
            source_url="https://example.co.jp/profile/",
            evidence="本社住所",
        ),
        representative=FieldDecision(
            value="代表者",
            status="FOUND",
            source_url="https://example.co.jp/officers/",
            evidence="代表者",
        ),
    )

    readable = pipeline.to_readable_company(company)

    assert readable["sources"]["profile"] == [
        "https://example.co.jp/profile/",
        "https://example.co.jp/officers/",
    ]
    assert readable["field_sources"]["head_offices"] == "https://example.co.jp/profile/"
    assert readable["field_sources"]["representatives"] == "https://example.co.jp/officers/"
    assert readable["head_offices"] == ["本社住所"]
    assert readable["representatives"] == ["代表者"]
    assert readable["capital"] is None
    assert readable["established"] is None


def test_write_outputs_creates_readable_json(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "RESULT_DIR", tmp_path)
    company = CompanyData(
        company_name="Example",
        seed_url="https://example.co.jp/",
        head_office_address=FieldDecision(
            value="本社住所",
            status="FOUND",
            source_url="https://example.co.jp/profile/",
            evidence="本社住所",
        ),
    )

    pipeline.write_outputs([company])

    readable = json.loads((tmp_path / "companies_readable.json").read_text(encoding="utf-8"))
    assert len(readable) == 1
    assert readable[0]["head_offices"] == ["本社住所"]
    assert readable[0]["field_sources"]["head_offices"] == "https://example.co.jp/profile/"


def test_pipeline_stops_when_extracted_data_fails_validation(monkeypatch):
    monkeypatch.setattr(
        pipeline.Crawler,
        "crawl",
        lambda self, seed: CrawlResult(seed=seed),
    )
    calls = []

    def extract(company, pages):
        calls.append(company)
        return {
            "capital": {"value": "999億円", "status": "FOUND", "source_url": None, "evidence": None}
        }

    monkeypatch.setattr(pipeline, "extract_company", extract)

    with pytest.raises(RuntimeError, match="validation failed"):
        pipeline.run(["Nissui"])
    assert calls == ["Nissui", "Nissui"]


def test_pipeline_retries_once_after_invalid_evidence(monkeypatch):
    monkeypatch.setattr(
        pipeline.Crawler,
        "crawl",
        lambda self, seed: CrawlResult(seed=seed),
    )
    replies = iter([
        {"capital": {"value": "999億円", "status": "FOUND", "source_url": None, "evidence": None}},
        {},
    ])
    calls = []

    def extract(company, pages):
        calls.append(company)
        return next(replies)

    monkeypatch.setattr(pipeline, "extract_company", extract)

    assert len(pipeline.run(["Nissui"])) == 1
    assert calls == ["Nissui", "Nissui"]
