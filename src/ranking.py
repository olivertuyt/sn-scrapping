"""Candidate page ranking: score URLs by how likely they hold company-profile data.

Deterministic keyword scoring over link text and URL path, developed test-first
(tests/test_ranking.py). No site-specific selectors.
"""

from __future__ import annotations

import re
from urllib.parse import unquote, urlsplit

# (pattern, weight). Japanese corporate-info vocabulary, weighted by specificity.
_KEYWORDS: list[tuple[re.Pattern[str], int]] = [
    (re.compile(r"会社概要|會社概要|企業情報|会社情報|company\s*profile|corporate\s*profile", re.IGNORECASE), 10),
    (re.compile(r"会社紹介|企業紹介|会社案内|corporate\s*info", re.IGNORECASE), 8),
    (re.compile(r"沿革|history|沿 革", re.IGNORECASE), 7),
    (re.compile(r"q\s*&\s*a|faq|質問と回答|よくある質問", re.IGNORECASE), 8),
    (re.compile(r"概要|outline|profile", re.IGNORECASE), 5),
    (re.compile(r"company|corporate", re.IGNORECASE), 3),
    (re.compile(r"ir|投資家情報| investor", re.IGNORECASE), 4),
    (re.compile(r"採用|recruit", re.IGNORECASE), 2),  # often repeats profile links
]

# URL path patterns that lower the score (unlikely to hold profile data).
_PENALTIES: list[tuple[re.Pattern[str], int]] = [
    (re.compile(r"/news|/ir/library|/ir[_-]library/qa|/release|/press|/topics|/info", re.IGNORECASE), 6),
    (re.compile(r"/recruit|/careers?|/採用", re.IGNORECASE), 4),
    (re.compile(r"/products?|/item|/goods|/商品|/製品", re.IGNORECASE), 4),
    (re.compile(r"/contact|/問い合わせ|/お問い合わせ|/access|/privacy|/policy|/sitemap", re.IGNORECASE), 5),
]


def score_url(url: str, link_text: str) -> int:
    """Score one link: keyword hits in link text and URL path, minus penalties."""
    text = f"{link_text} {unquote(urlsplit(url).path)}"
    score = 0
    for pattern, weight in _KEYWORDS:
        if pattern.search(text):
            score += weight
    for pattern, penalty in _PENALTIES:
        if pattern.search(text):
            score -= penalty
    return score


def rank_candidates(links: list[tuple[str, str]]) -> list[tuple[int, str, str]]:
    """Rank (url, link_text) pairs by score, descending; stable for ties.

    Returns (score, url, link_text) triples sorted best first.
    A URL seen on many pages counts once (keeps its first, highest-scoring text).
    """
    best: dict[str, tuple[int, str]] = {}
    for url, text in links:
        s = score_url(url, text)
        if url not in best or s > best[url][0]:
            best[url] = (s, text)
    scored = [(s, u, t) for u, (s, t) in best.items()]
    scored.sort(key=lambda x: (-x[0], x[1]))
    return scored
