"""URL normalization, dedup, and official-domain policy.

Pure deterministic logic, developed test-first (tests/test_urls.py).
"""

from __future__ import annotations

from urllib.parse import urljoin, urlsplit, urlunsplit

# Query params that never change page content (tracking).
_TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "gclid", "fbclid", "utm_reader", "utm_site", "ref", "referrer",
}

# Extensions we never parse as HTML candidates.
_NON_PAGE_SUFFIXES = {
    ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".ico",
    ".zip", ".rar", ".7z", ".mp3", ".mp4", ".wmv", ".avi", ".mov",
    ".css", ".js", ".json", ".xml", ".rss", ".doc", ".docx", ".xls",
    ".xlsx", ".ppt", ".pptx", ".exe", ".dmg",
}

# Second-level labels that make a Japanese public suffix (e.g. 'co.jp').
_JP_SLD = {"co", "or", "ne", "go", "ac", "ad", "ed"}


def is_same_site(url: str, seed_url: str) -> bool:
    """True if url is on the seed's registrable domain (subdomains count as same site).

    Handles the Sakata Seed case: corporate data lives on another subdomain
    of the official domain, which must still be crawled.
    """
    u = urlsplit(url)
    s = urlsplit(seed_url)
    if u.scheme not in ("http", "https"):
        return False
    return registrable_domain(u.hostname or "") == registrable_domain(s.hostname or "")


def registrable_domain(host: str) -> str:
    """Approximate the registrable domain: 'www.nissui.co.jp' -> 'nissui.co.jp'.

    shortcut: fixed JP second-level suffix list instead of the full Public
    Suffix List; sufficient for the 10 known seed domains, revisit if a seed
    uses an exotic suffix.
    """
    host = host.lower().rstrip(".")
    if not host:
        return ""
    parts = host.split(".")
    if len(parts) >= 3 and parts[-2] in _JP_SLD:
        return ".".join(parts[-3:])
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return host


def normalize_url(url: str, base: str = "") -> str:
    """Resolve against base, drop fragment, drop tracking params, sort remaining.

    Non-http(s) schemes (mailto:, tel:, javascript:) return "" (invalid candidate).
    """
    if base:
        url = urljoin(base, url)
    p = urlsplit(url)
    if p.scheme not in ("http", "https") or not p.hostname:
        return ""
    host = p.hostname.lower()
    netloc = host if not p.port else f"{host}:{p.port}"
    query = "&".join(sorted(
        kv for kv in p.query.split("&") if kv and kv.split("=", 1)[0] not in _TRACKING_PARAMS
    ))
    path = p.path or "/"
    while "//" in path:  # collapse duplicate slashes
        path = path.replace("//", "/")
    return urlunsplit((p.scheme, netloc, path, query, ""))


def is_crawlable(url: str) -> bool:
    """Filter out non-HTML assets and obvious non-page paths."""
    if not url:
        return False
    return not urlsplit(url).path.lower().endswith(tuple(_NON_PAGE_SUFFIXES))


def canon_key(url: str) -> str:
    """Dedup key: https + no www + no trailing slash + normalized query."""
    key = normalize_url(url)
    if not key:
        return ""
    p = urlsplit(key)
    path = p.path.rstrip("/")
    # /x/ and /x/index.html are the same page for dedup purposes
    if path.endswith(("/index.html", "/index.htm")):
        path = path.rsplit("/", 1)[0]
    host = p.netloc.rsplit("@", 1)[-1]
    host = host.removeprefix("www.")
    return urlunsplit(("https", host, path, p.query, ""))
