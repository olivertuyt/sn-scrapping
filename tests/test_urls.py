"""Tests for URL normalization, dedup keys, and domain policy."""

from src.urls import (
    canon_key,
    is_crawlable,
    is_same_site,
    normalize_url,
    registrable_domain,
)


class TestNormalize:
    def test_resolves_relative(self):
        assert normalize_url("/profile/", "https://www.nissui.co.jp/") == "https://www.nissui.co.jp/profile/"

    def test_strips_fragment(self):
        assert normalize_url("https://a.co.jp/x#section") == "https://a.co.jp/x"

    def test_strips_tracking_params(self):
        assert normalize_url("https://a.co.jp/x?utm_source=tw&id=2") == "https://a.co.jp/x?id=2"

    def test_sorts_remaining_params(self):
        assert normalize_url("https://a.co.jp/x?b=2&a=1") == "https://a.co.jp/x?a=1&b=2"

    def test_mailto_invalid(self):
        assert normalize_url("mailto:info@example.com", "https://a.co.jp/") == ""

    def test_javascript_invalid(self):
        assert normalize_url("javascript:void(0)", "https://a.co.jp/") == ""

    def test_collapses_double_slash(self):
        assert normalize_url("https://a.co.jp//x//y") == "https://a.co.jp/x/y"

    def test_empty_path_becomes_root(self):
        assert normalize_url("https://a.co.jp") == "https://a.co.jp/"


class TestCanonKey:
    def test_http_https_same(self):
        assert canon_key("http://a.co.jp/x") == canon_key("https://a.co.jp/x")

    def test_www_same(self):
        assert canon_key("https://www.a.co.jp/x") == canon_key("https://a.co.jp/x")

    def test_trailing_slash_same(self):
        assert canon_key("https://a.co.jp/x/") == canon_key("https://a.co.jp/x")

    def test_index_html_same(self):
        assert canon_key("https://a.co.jp/profile/index.html") == canon_key("https://a.co.jp/profile/")

    def test_tracking_params_same(self):
        assert canon_key("https://a.co.jp/x?utm_campaign=1") == canon_key("https://a.co.jp/x")

    def test_different_path_differs(self):
        assert canon_key("https://a.co.jp/x") != canon_key("https://a.co.jp/y")


class TestSameSite:
    def test_subdomain_same_site(self):
        # Sakata Seed: corporate data on another subdomain of the official domain
        assert is_same_site("https://www.sakataseed.co.jp/profile/", "https://www.sakataseed.co.jp/")
        assert is_same_site("https://corp.sakataseed.co.jp/", "https://www.sakataseed.co.jp/")

    def test_jp_domain_correct_registrable(self):
        # nissui.co.jp and other.co.jp differ
        assert not is_same_site("https://www.nissui.co.jp/", "https://other.co.jp/")

    def test_external_domain_excluded(self):
        assert not is_same_site("https://twitter.com/nissui", "https://www.nissui.co.jp/")

    def test_non_http_excluded(self):
        assert not is_same_site("mailto:x@y.jp", "https://www.nissui.co.jp/")


class TestRegistrable:
    def test_jp_co(self):
        assert registrable_domain("www.nissui.co.jp") == "nissui.co.jp"

    def test_plain_com(self):
        assert registrable_domain("shop.example.com") == "example.com"

    def test_localhost(self):
        assert registrable_domain("localhost") == "localhost"


class TestCrawlable:
    def test_pdf_excluded(self):
        assert not is_crawlable("https://a.co.jp/doc.pdf")

    def test_html_ok(self):
        assert is_crawlable("https://a.co.jp/profile/")

    def test_empty_invalid(self):
        assert not is_crawlable("")
