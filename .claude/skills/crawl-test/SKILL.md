---
name: crawl-test
description: Verify the generic crawler for the company-information assignment. Use after any change to crawling, URL normalization, domain policy, or candidate ranking.
---

# Crawl Test

Run the crawler (no LLM calls) for: Nissui, Sakata Seed, Mirait One first.
After those pass, run all 10 companies.

Verify and report evidence for each company:
1. Crawling started from the supplied homepage.
2. At least one internal link was followed.
3. The company-profile page appears in the top 5 ranked candidates.
4. For Nissui and Hokuto, a history/沿革 page is also a candidate.
5. Sakata Seed reached its official corporate subdomain.
6. No unrelated external domains were crawled.
7. No duplicate URLs (fragments, tracking params) were fetched twice.
8. Depth and page limits were respected.
9. No company-specific URL or selector was hardcoded.

Output a table: company | pages fetched | top candidate URL | PASS/FAIL | evidence.
Do not mark PASS without showing the log line or output that proves it.
