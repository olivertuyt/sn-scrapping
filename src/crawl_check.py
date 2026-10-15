"""One-off crawl-test evidence report (crawl-test skill). Not part of the pipeline."""

from __future__ import annotations

from src import urls as U
from src.companies import COMPANIES
from src.crawler import Crawler


def main() -> int:
    print(f"{'Company':<22} {'Pages':>5} {'Dups':>4} {'Ext':>4}  Top candidate")
    all_pass = True
    for c in COMPANIES:
        r = Crawler(max_pages=30, max_depth=2).crawl(c["url"])
        fetched = [p.url for p in r.pages]
        keys = [U.canon_key(u) for u in fetched]
        dups = len(keys) - len(set(keys))
        ext = sum(1 for u in fetched if not U.is_same_site(u, c["url"]))
        top = r.ranked[0][1] if r.ranked else ""
        ok = dups == 0 and ext == 0 and len(fetched) <= 30
        all_pass &= ok
        flag = "OK " if ok else "BAD"
        print(f"{c['name']:<22} {len(fetched):>5} {dups:>4} {ext:>4}  {flag} {top}")
        for u, reason in r.failures:
            print(f"   fail: {u} ({reason})")
    print("OVERALL:", "PASS" if all_pass else "FAIL")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
