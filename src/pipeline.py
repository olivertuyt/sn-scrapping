"""Main pipeline: crawl 10 companies -> clean top pages -> LLM extract -> validate -> JSON/CSV.

Usage: python -m src.pipeline [--spike]
Writes result/companies.json, result/companies_readable.json, and result/companies.csv.
"""

from __future__ import annotations

import csv
import json
import logging
import re
import sys
from pathlib import Path

import httpx

from . import ranking
from . import urls as U
from .cleaner import clean_html
from .companies import COMPANIES, SPIKE_NAMES
from .crawler import Crawler, Page, extract_links, fetch
from .extract import extract_company
from .schema import CompanyData, FieldDecision, validate_company

log = logging.getLogger("pipeline")

RESULT_DIR = Path("result")
FIELDS = ("head_office_address", "representative", "capital", "established_year_month")
_TOP_PAGES = 4  # reserve two context slots for detailed history pages
# profile pages often show the establishment year only; the month is usually on a
# history page, so always include the best-ranked history-like candidate too
_HISTORY = re.compile(r"沿革|history|rekishi|enkaku|りれき", re.IGNORECASE)


def _history_child_urls(html: str, base_url: str, seed_url: str, excluded_urls: set[str]) -> list[str]:
    """Return discovered same-site history links, ranked and canonically deduplicated."""
    excluded = {U.canon_key(url) for url in excluded_urls}
    links = []
    seen: set[str] = set()
    for url, label in extract_links(html, base_url):
        key = U.canon_key(url)
        if not key or key in excluded or key in seen or not U.is_same_site(url, seed_url):
            continue
        if _HISTORY.search(f"{url} {label}"):
            seen.add(key)
            links.append((url, label))
    return [url for _score, url, _label in ranking.rank_candidates(links)]


def _load_candidate_pages(
    urls: list[str],
    pages_by_url: dict[str, Page],
    html_by_url: dict[str, str],
    texts: dict[str, str],
    client: httpx.Client,
    company_name: str,
) -> None:
    """Load selected pages from the crawl cache or one direct HTTP fetch."""
    for url in urls:
        if url in html_by_url:
            continue
        page = pages_by_url.get(url)
        if page is not None:
            html = page.html
            final_url = page.url
        else:
            try:
                response = fetch(client, url)
            except httpx.HTTPError as exc:
                log.warning("%s: fetch of candidate %s failed: %s", company_name, url, exc)
                continue
            if response.status_code != 200:
                log.warning(
                    "%s: fetch of candidate %s -> HTTP %s",
                    company_name, url, response.status_code,
                )
                continue
            html = response.text
            final_url = str(response.url)

        cleaned = clean_html(html)
        html_by_url[url] = html
        texts[url] = cleaned
        if final_url:
            html_by_url[final_url] = html
            texts[final_url] = cleaned


def run(names: list[str] | None = None) -> list[CompanyData]:
    selected = COMPANIES if names is None else [c for c in COMPANIES if c["name"] in names]
    results: list[CompanyData] = []
    for company in selected:
        log.info("crawling %s", company["name"])
        crawl = Crawler(max_pages=30, max_depth=2).crawl(company["url"])

        eligible: list[tuple[str, str]] = []
        seen_candidates: set[str] = set()
        for _score, url, label in crawl.ranked:
            key = U.canon_key(url)
            if not key or key in seen_candidates or not U.is_same_site(url, company["url"]):
                continue
            seen_candidates.add(key)
            eligible.append((url, label))

        candidate_urls = [url for url, _label in eligible]
        history_urls = [url for url, label in eligible if _HISTORY.search(f"{url} {label}")]
        primary_urls = [url for url, label in eligible if not _HISTORY.search(f"{url} {label}")]
        if history_urls:
            discovery_urls = primary_urls[:_TOP_PAGES] + history_urls[:1]
            for url in candidate_urls:
                if len(discovery_urls) >= _TOP_PAGES + 1:
                    break
                if url not in discovery_urls:
                    discovery_urls.append(url)
        else:
            discovery_urls = candidate_urls[:_TOP_PAGES + 2]

        texts: dict[str, str] = {}
        html_by_url: dict[str, str] = {}
        by_url: dict[str, Page] = {}
        for page in crawl.pages:
            by_url[page.requested_url] = page
            by_url[page.url] = page

        import ssl

        try:
            import truststore
            ctx = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        except ImportError:
            ctx = None
        with httpx.Client(verify=ctx or True) as client:
            _load_candidate_pages(
                discovery_urls, by_url, html_by_url, texts, client, company["name"]
            )
            history_children: list[str] = []
            if history_urls:
                history_root = history_urls[0]
                history_html = html_by_url.get(history_root)
                if history_html:
                    history_children = _history_child_urls(
                        history_html, history_root, company["url"], set(discovery_urls)
                    )

            if history_children:
                chosen = primary_urls[:_TOP_PAGES] + history_children[:2]
            else:
                chosen = primary_urls[:_TOP_PAGES + 1] + history_urls[:1]
            selected_keys = {U.canon_key(url) for url in chosen}
            for url in candidate_urls:
                if len(chosen) >= _TOP_PAGES + 2:
                    break
                key = U.canon_key(url)
                if key and key not in selected_keys:
                    selected_keys.add(key)
                    chosen.append(url)
            _load_candidate_pages(chosen, by_url, html_by_url, texts, client, company["name"])

        extraction_pages = [(u, texts[u]) for u in chosen if u in texts]
        for attempt in range(2):
            raw = extract_company(company["name"], extraction_pages)
            data = CompanyData(company_name=company["name"], seed_url=company["url"])
            for f in FIELDS:
                fd = raw.get(f) or {}
                setattr(data, f, FieldDecision(
                    value=fd.get("value"),
                    status=fd.get("status", "NOT_FOUND"),
                    source_url=fd.get("source_url"),
                    evidence=fd.get("evidence"),
                ))
            problems = validate_company(data, texts)
            if not problems:
                break
            if attempt == 0:
                log.warning("%s: invalid extraction; retrying once: %s", company["name"], "; ".join(problems))
            else:
                raise RuntimeError(f"{company['name']}: validation failed: {'; '.join(problems)}")
        results.append(data)
    return results


def _as_list(value: str | list[str] | None) -> list[str]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def to_readable_company(company: CompanyData) -> dict[str, object]:
    """Project one validated company record into a compact, reader-friendly view."""
    field_decisions = {
        "head_offices": company.head_office_address,
        "representatives": company.representative,
        "capital": company.capital,
        "established": company.established_year_month,
    }
    profile_urls = list(dict.fromkeys(
        d.source_url for name, d in field_decisions.items()
        if name != "established" and d.source_url
    ))
    profile_source: str | list[str] | None
    if len(profile_urls) == 1:
        profile_source = profile_urls[0]
    elif profile_urls:
        profile_source = profile_urls
    else:
        profile_source = None

    return {
        "company_name": company.company_name,
        "website": company.seed_url,
        "head_offices": _as_list(company.head_office_address.value),
        "representatives": _as_list(company.representative.value),
        "capital": company.capital.value,
        "established": company.established_year_month.value,
        "sources": {
            "profile": profile_source,
            "established": company.established_year_month.source_url,
        },
        "field_sources": {
            name: decision.source_url for name, decision in field_decisions.items()
        },
        "evidence": {
            name: decision.evidence for name, decision in field_decisions.items()
        },
        "statuses": {
            name: decision.status for name, decision in field_decisions.items()
        },
    }


def write_readable_output(results: list[CompanyData], output_path: Path | None = None) -> None:
    """Write the compact view without changing the detailed audit outputs."""
    path = output_path or RESULT_DIR / "companies_readable.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump([to_readable_company(r) for r in results], f, ensure_ascii=False, indent=2)


def write_outputs(results: list[CompanyData]) -> None:
    RESULT_DIR.mkdir(exist_ok=True)
    out = [r.model_dump() for r in results]
    with open(RESULT_DIR / "companies.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    write_readable_output(results)

    with open(RESULT_DIR / "companies.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["company", "seed_url", "field", "value", "status", "source_url", "evidence"])
        for r in results:
            for field in FIELDS:
                d = getattr(r, field)
                value = d.value if not isinstance(d.value, list) else " | ".join(d.value)
                w.writerow([r.company_name, r.seed_url, field, value, d.status, d.source_url, d.evidence])


def main(argv: list[str]) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    names = None
    if argv and argv[0] == "--spike":
        names = SPIKE_NAMES
    elif argv:
        names = argv
    results = run(names)
    write_outputs(results)
    print(
        f"processed {len(results)} companies -> {RESULT_DIR}/companies.json, "
        f"companies_readable.json, companies.csv"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
