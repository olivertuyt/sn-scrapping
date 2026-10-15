"""Generic same-site crawler: seed homepage -> discovered internal links.

No LLM, no site-specific selectors. HTTP-first per the fixed architecture;
Playwright is a documented fallback only. Retries, timeouts, failure logging
are required by the project contract (AGENTS.md hard rules).
"""

from __future__ import annotations

import logging
import ssl
import time
from dataclasses import dataclass, field

import httpx
from bs4 import BeautifulSoup

from . import ranking
from . import urls as U

log = logging.getLogger("crawl")

# Corporate TLS-intercepting proxy: certifi lacks the corporate CA, so use the
# Windows system store when truststore is available (verified: curl OK, httpx FAIL).
try:
    import truststore
    _SSL_CONTEXT: ssl.SSLContext | None = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
except ImportError:  # pragma: no cover - fallback when truststore not installed
    _SSL_CONTEXT = None

_HEADERS = {
    # shortcut: no browser UA — the corporate Zscaler proxy intercepts browser-UAs
    # with a SAML wall; the default httpx UA passes. Revisit if a site 403s it.
    "User-Agent": "python-httpx/company-research-crawler (assignment)",
    "Accept-Language": "ja,en;q=0.8",
}

_RETRY_STATUS = {429, 500, 502, 503, 504}


@dataclass
class Page:
    url: str  # final (post-redirect) URL
    requested_url: str  # URL as queued pre-fetch (differs after redirects)
    status: int
    html: str
    links: list[tuple[str, str]] = field(default_factory=list)  # (url, link_text)


@dataclass
class CrawlResult:
    seed: str
    pages: list[Page] = field(default_factory=list)
    failures: list[tuple[str, str]] = field(default_factory=list)  # (url, reason)
    ranked: list[tuple[int, str, str]] = field(default_factory=list)


def fetch(client: httpx.Client, url: str, retries: int = 2) -> httpx.Response:
    """GET with retry on network errors and 429/5xx. Raises httpx.HTTPError on final failure."""
    delay = 1.0
    for attempt in range(retries + 1):
        try:
            r = client.get(url, headers=_HEADERS, follow_redirects=True, timeout=20.0)
            if r.status_code in _RETRY_STATUS and attempt < retries:
                raise httpx.TransportError(f"retryable status {r.status_code}")
            return r
        except httpx.HTTPError as e:
            if attempt >= retries:
                raise
            log.warning("fetch retry %s/%s for %s: %s", attempt + 1, retries, url, e)
            time.sleep(delay)
            delay *= 2
    raise AssertionError("unreachable")


def extract_links(html: str, base_url: str) -> list[tuple[str, str]]:
    """All <a href> links as (normalized_url, link_text); empty for non-page content."""
    soup = BeautifulSoup(html, "lxml")
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for a in soup.find_all("a", href=True):
        text = a.get_text(" ", strip=True)
        href = a["href"]
        if not isinstance(href, str):
            continue
        url = U.normalize_url(href, base=base_url)
        if not url or not U.is_crawlable(url):
            continue
        if url in seen:
            continue
        seen.add(url)
        out.append((url, text))
    return out


class Crawler:
    """Breadth-first, same-registrable-domain crawl with depth and page limits."""

    def __init__(self, max_pages: int = 30, max_depth: int = 2) -> None:
        self.max_pages = max_pages
        self.max_depth = max_depth

    def crawl(self, seed_url: str) -> CrawlResult:
        result = CrawlResult(seed=seed_url)
        seen: set[str] = {U.canon_key(seed_url)}
        fetched_keys: set[str] = set()
        queue: list[tuple[str, int]] = [(seed_url, 0)]
        with httpx.Client(verify=_SSL_CONTEXT or True) as client:
            while queue and len(result.pages) < self.max_pages:
                url, depth = queue.pop(0)
                try:
                    resp = fetch(client, url)
                except httpx.HTTPError as e:
                    result.failures.append((url, str(e)))
                    continue
                if resp.status_code != 200:
                    result.failures.append((url, f"HTTP {resp.status_code}"))
                    continue
                page = Page(url=str(resp.url), requested_url=url, status=200, html=resp.text)
                page.links = extract_links(page.html, page.url)
                # post-redirect dedup: a queued URL can land on an already-fetched page
                final_key = U.canon_key(page.url)
                if final_key in fetched_keys:
                    log.info("skip duplicate landing %s -> %s", url, page.url)
                    continue
                fetched_keys.add(final_key)
                result.pages.append(page)
                seen.add(final_key)

                for link, _text in page.links:
                    if len(result.pages) + len(queue) >= self.max_pages:
                        break
                    if not U.is_same_site(link, seed_url):
                        continue
                    key = U.canon_key(link)
                    if key in seen:
                        continue
                    seen.add(key)
                    if depth < self.max_depth:
                        queue.append((link, depth + 1))
        # Rank all discovered links (not only fetched ones) by profile likelihood.
        all_links: dict[str, tuple[str, str]] = {}
        for p in result.pages:
            for link, text in p.links:
                key = U.canon_key(link)
                if key and key not in all_links:
                    all_links[key] = (link, text)
        result.ranked = ranking.rank_candidates(list(all_links.values()))
        return result
