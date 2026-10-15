"""Milestone 1 spike: crawl spike sites (no LLM), verify ranking finds profile pages.

Usage: python -m src.spike [company names ...]   (defaults to the 3 spike sites)
"""

from __future__ import annotations

import logging
import sys

from .companies import COMPANIES, SPIKE_NAMES
from .crawler import Crawler


def main(argv: list[str]) -> int:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    names = argv or SPIKE_NAMES
    selected = [c for c in COMPANIES if c["name"] in names]
    missing = set(names) - {c["name"] for c in selected}
    if missing:
        print(f"Unknown company: {', '.join(sorted(missing))}", file=sys.stderr)
        return 2

    failures = 0
    for company in selected:
        crawler = Crawler(max_pages=30, max_depth=2)
        result = crawler.crawl(company["url"])
        print(f"\n=== {company['name']} ===")
        print(f"seed: {result.seed}")
        print(f"pages fetched: {len(result.pages)}  failures: {len(result.failures)}")
        for url, reason in result.failures[:5]:
            print(f"  FAIL {url} ({reason})")
        print("top 5 candidates:")
        for score, url, text in result.ranked[:5]:
            print(f"  {score:3d}  {url}  [{text[:30]}]")
        profile_in_top5 = any(
            _looks_like_profile(u, t) for _, u, t in result.ranked[:5]
        )
        print(f"profile in top 5: {'YES' if profile_in_top5 else 'NO'}")
        if not profile_in_top5:
            failures += 1
    return 1 if failures else 0


def _looks_like_profile(url: str, text: str) -> bool:
    return any(k in f"{url} {text}" for k in ("会社概要", "企業情報", "会社情報", "company", "profile", "概要"))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
