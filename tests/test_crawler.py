"""Crawler unit tests with a mocked transport (no network)."""

from __future__ import annotations

from unittest.mock import patch

import httpx

from src.crawler import Crawler, extract_links

SEED = "https://www.example.co.jp/"


def _make_client(routes: dict[str, str]) -> httpx.Client:
    """Client whose GET returns canned HTML by URL prefix."""
    def handler(request: httpx.Request) -> httpx.Response:
        for prefix, html in routes.items():
            if str(request.url).startswith(prefix):
                return httpx.Response(200, text=html)
        return httpx.Response(404)
    return httpx.Client(transport=httpx.MockTransport(handler))


def _crawl_with(routes: dict[str, str], seed: str = SEED, **kwargs):
    """Run Crawler.crawl against a mocked transport (patched Client factory)."""
    client = _make_client(routes)  # built before patching
    with patch.object(httpx, "Client", return_value=client):
        return Crawler(**kwargs).crawl(seed)


class TestExtractLinks:
    def test_finds_and_normalizes(self):
        html = '<a href="/profile/">会社概要</a><a href="https://www.example.co.jp/x#top">X</a>'
        links = extract_links(html, SEED)
        assert ("https://www.example.co.jp/profile/", "会社概要") in links
        assert ("https://www.example.co.jp/x", "X") in links

    def test_external_links_kept_in_list(self):
        # Domain filtering happens at crawl time, not extraction time
        links = extract_links('<a href="https://twitter.com/x">TW</a>', SEED)
        assert ("https://twitter.com/x", "TW") in links

    def test_dedup_within_page(self):
        links = extract_links('<a href="/a">1</a><a href="/a">2</a>', SEED)
        assert len(links) == 1

    def test_ignores_assets_and_js(self):
        links = extract_links('<a href="/doc.pdf">P</a><a href="javascript:void(0)">J</a>', SEED)
        assert links == []


class TestCrawl:
    def test_follows_internal_links_respects_limits(self):
        routes = {
            SEED: '<a href="/profile/">会社概要</a><a href="/news/">ニュース</a>',
            SEED + "profile/": "<html>プロフィール</html>",
            SEED + "news/": '<a href="/news/2">more</a>',
            SEED + "news/2": "<html></html>",
        }
        result = _crawl_with(routes, max_pages=3, max_depth=2)
        fetched = {p.url for p in result.pages}
        assert SEED in fetched
        assert any("profile" in u for u in fetched)
        assert len(result.pages) <= 3
        ranked_urls = [u for _, u, _ in result.ranked]
        assert any("profile" in u for u in ranked_urls[:5])

    def test_404_recorded_as_failure(self):
        result = _crawl_with({}, max_pages=2)
        assert result.failures and "404" in result.failures[0][1]
