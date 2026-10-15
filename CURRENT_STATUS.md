# Current Status

## Milestone 0: Environment + contract scaffold (DONE)

Date: 2026-10-15

### Environment
- Python 3.14.8 (`python --version`), venv at `.venv/`
- Installed via pip: httpx 0.28.1, beautifulsoup4 4.15.0, lxml 6.1.3, pydantic 2.14.1,
  pytest 9.1.1, pytest-cov 7.1.0, ruff 0.17.0, mypy 2.4.0
  (no LLM provider SDK yet — added at the extraction milestone)
- Node v26.10.0 / npm 11.19.1 / git 2.56.0 (Windows 11)
- Active model: z-ai/glm-5.3 (verified in session environment)

### Smoke test (setup.md §3)
- Command: `python -m pytest test_smoke.py -v` (throwaway dir, cleaned up after)
- Output: `test_smoke.py::test_add PASSED [100%]` — 1 passed in 0.24s
- PASS conditions met: agent edits files ✓, runs commands ✓, skills available ✓

### Skills
- Superpowers plugin: already installed (marketplace), constrained via CLAUDE.md policy
- Ponytail: INSTALLED at `.claude/skills/ponytail/SKILL.md` (commit 5734b94).
  Security review done per setup.md §4.3: shallow-cloned repo, read SKILL.md in full
  (pure instructions, MIT, no executable code), copied ONLY the SKILL.md —
  the repo's hooks/ and scripts/ were deliberately NOT installed.
  SHA256 of installed file verified identical to reviewed source:
  FC12A0B9588A7FA3543D31DDC41541F735A5626105781643873110F2DA1BD52A
- Custom project skills created: crawl-test, extraction-audit, quality-gate, submission-audit
  at `.claude/skills/`

### Git
- Branch `main`, commit fd31786 "chore: initialize project structure and agent contract"
  (20 files), commit 5734b94 "chore: install ponytail skill (...)".

### Contract files
- AGENTS.md, CLAUDE.md (@AGENTS.md + policies), ACCEPTANCE_CRITERIA.md,
  .gitignore, .env.example, requirements.txt — created from documents/setup.md

### Next
- ~~`/ponytail lite`~~ invoked this session (2026-10-15), active at lite level.
- 3-site spike: done, see below.

## Milestone 1: 3-site spike (DONE)

Date: 2026-10-15. `/ponytail lite` invoked and active.

### Implemented (src/, tests/)
- `src/urls.py` — URL normalization (fragment/tracking-param removal, path collapsing),
  canon_key dedup (https + no-www + no trailing slash + index.html equivalence),
  registrable-domain policy (JP co.jp suffix handling; subdomains count as same site —
  Sakata corporate subdomain reachable), asset-extension filter.
- `src/ranking.py` — keyword scoring (会社概要/企業情報/沿革/…) with penalties
  (news/recruit/product/contact), URL-path keywords counted, per-URL best-score dedup.
- `src/crawler.py` — BFS same-site crawl (max_pages=30, max_depth=2), retries with
  exponential backoff on network errors + 429/5xx, timeout 20s, failure logging,
  truststore SSL (Windows system CA), plain httpx UA (see below).
- `src/spike.py` — spike CLI (`python -m src.spike`).
- Tests: `tests/test_urls.py` (17), `tests/test_ranking.py` (7),
  `tests/test_crawler.py` (6, mocked transport) — 37 total, all via pytest.

### Environment blockers found and fixed (root-cause evidence)
1. **SSL CERTIFICATE_VERIFY_FAILED on all sites** (httpx; curl/Schannel OK):
   corporate TLS-intercepting proxy; corporate CA is in the Windows store but not
   in Python's certifi bundle. Fix: `pip install truststore` + `verify=truststore
   .SSLContext(...)` in the client (recorded in requirements.txt).
2. **Zscaler "Directory Authentication" SAML page (HTTP 200, 16KB) returned instead
   of real content** when a browser-like User-Agent was sent; plain httpx UA gets
   the real page. Reproduced 3/3 with browser UA, 0/3 with plain UA. Fix: use a
   plain identifying UA (`python-httpx/company-research-crawler (assignment)`).
   Both are documented in code comments as `shortcut:` notes.

### Spike results (`python -m src.spike`, exit 0 = all PASS)
| Company | Pages | Failures | Top candidate | PASS |
|---|---|---|---|---|
| Nissui | 30 | 0 | https://www.nissui.co.jp/corporate/index.html [会社概要] | YES |
| Sakata Seed | 30 | 3 (product-item 404s) | https://corporate.sakataseed.co.jp/company/profile.html [会社概要] | YES |
| Mirait One | 30 | 0 | https://www.mirait-one.com/corporate/profile/ [会社概要] | YES |

Edge cases verified: Nissui 沿革 page ranks #3 (month is there per research);
Sakata Seed reached corporate subdomain `corporate.sakataseed.co.jp` (no hardcode);
no external domains crawled (facebook.com etc. appear in ranking only, never fetched).

### Quality gate (after M1)
- `ruff check .` → All checks passed!
- `mypy src` → Success: no issues found in 6 source files
- `pytest -q` → 37 passed in 0.62s
- Secret scan (api_key|sk-…|Authorization|token) → docs-only matches, no secrets.

### Next
- M2: generic-crawler hardening (crawl-test for all 10), then M3 LLM extraction. Commit M1.

## Milestone 2: 10-company crawl-test (DONE)

Date: 2026-10-15.

### Change
- Post-redirect dedup fix (`src/crawler.py`): queued URL landing on an already-fetched
  final page is skipped (`fetched_keys` set); `Page.requested_url` records the
  pre-redirect URL. Root cause: seed redirects (`umios.com/` → `umios.com/jp/`) and
  links like `customer.tamahome.jp/shokai_p/` → homepage left duplicates in fetch order.
- `src/crawl_check.py`: evidence report (pages/dups/external/top candidate) for the
  crawl-test skill.

### Crawl-test evidence (`python -X utf8 -m src.crawl_check`, OVERALL: PASS)
All 10: pages=30, dups=0, ext=0, ≤30 pages, no hardcoded URLs; profile page in top 5
(rank #1 for 9, rank #2 for Kyokuyo). Nissui 沿革 #3, Hokuto 歴史 ranked
(`/corporate/kigyou/rekishi/`), Sakata reached `corporate.sakataseed.co.jp` organically.
Sakata 3 product-item 404s recorded as failures and crawl continued (by design).

### Quality gate (after M2)
- `ruff check .` → All checks passed!
- `mypy src` → Success: no issues found in 7 source files
- `pytest -q` → 37 passed in 1.08s

### Next
- M3: LLM extraction + validation + conflicts.

## Milestone 3: LLM extraction + validation (DONE)

Date: 2026-10-15.

### Change
- `src/extract.py` — Anthropic-compatible Messages API call via plain httpx
  (endpoint/key/model from env: LLM_API_KEY/ANTHROPIC_AUTH_TOKEN etc.), truststore SSL,
  3 retries with backoff, markdown-fence tolerant JSON parsing, top 6 pages per call.
- `src/schema.py` — pydantic `FieldDecision`/`CompanyData` + deterministic validation:
  null/status rules, source_url-must-be-fetched, verbatim evidence (Unicode-whitespace
  normalized), month-inference ban (month in value must appear in evidence).
- `src/cleaner.py` — script/style/nav/header/footer stripping + whitespace squeeze.
- `prompts/05_extraction_system_prompt.txt` — strict extraction rules.
- `tests/test_validation.py` (16), `tests/test_extract.py` (7) — 61 total.

### Bug fixed this milestone (root cause)
- Full-rerun failure `KeyError: 'text'`: API returned HTTP 200 with a thinking block
  before the text block. Fix: join all `type: "text"` blocks (`_response_text`),
  2 regression tests added.

### Quality gate (after M3)
- `ruff check .` → All checks passed!
- `mypy src` → Success: no issues found in 11 source files
- `pytest -q` → 61 passed in 0.98s

## Milestone 4: 10-company full run (DONE)

Date: 2026-10-15.

### Change
- `src/pipeline.py` — crawl → top-5 ranked same-site pages + history-page boost
  (沿革/history candidate always included: profile pages often show year only) →
  clean → LLM extract → validate → `result/companies.json` + `companies.csv` (UTF-8 BOM).

### Run evidence (`python -m src.pipeline`, exit 0)
- 10 companies, 40 field decisions, **zero validation warnings** in the log.
- All 40 fields FOUND or MULTIPLE_CANDIDATES with source_url + verbatim evidence.
- Edge cases (per AGENTS.md known list):
  - Yukiguni Factory: 2 head offices → MULTIPLE_CANDIDATES (新潟本社/東京本社).
  - Sakata Seed + Tama Home: 2 representative directors each → MULTIPLE_CANDIDATES.
  - Hokuto: establishment month found via history-page boost:
    value 昭和39年7月, source `/corporate/kigyou/rekishi/`,
    evidence "昭和39年 7月 …デラップス商事株式会社を設立".
  - Nissui: official site publishes 設立 as year-only (昭和18年（1943年）) on both the
    profile page and the history page (verified by direct fetch of both pages on
    2026-10-15; no 1943/昭和18 entry with a month exists). Per hard rule 6 the month
    is NOT inferred; value is year-only with verbatim evidence. Documented decision.

### Extraction audit (per /extraction-audit skill) — PASS
All 8 checks pass: fetched source_urls; verbatim evidence; value supported by evidence;
month only when in evidence; 設立 not 創業; multiple representatives/addresses preserved
explicitly; missing values null (none missing); no "" / "N/A" / guesses.

### Quality gate (after M4)
- `ruff check .` → All checks passed!
- `mypy src` → Success: no issues found in 11 source files
- `pytest -q` → 61 passed
- Result files: 10 records, 40 field decisions, 0 violations; CSV 41 rows, correct header.
- Secret scan (`git grep sk-or-|Bearer …`) → none; `.env.example` placeholder only.

## Milestone 5: Task B — anti-bot site (DONE)

Date: 2026-10-15. Target: https://vn.indeed.com/jobs?q=remote

### Findings (evidence in report.md §5)
- Cloudflare bot protection: `Server: cloudflare`, `CF-RAY`, `__cf_bm` cookie,
  403 page title "Blocked - Indeed.com" loading `/cdn-cgi/challenge-platform/scripts/jsd/main.js`.
- Attempt 1 (plain UA): HTTP 403 challenge page (25,743 bytes).
- Attempt 2 (browser UA): corporate Zscaler proxy 307-redirects to gateway.zscloud.net
  SAML auth before the request reaches Indeed.
- Attempt 3 (plain UA + browser Accept/Accept-Language headers): HTTP 403, same page —
  header spoofing insufficient.
- Conclusion: JS challenge requires a real browser; corporate proxy additionally
  intercepts browser-identified traffic. Documented as required (optional task).

## Milestone 6: Final review and Gemini rerun (CURRENT)

Date: 2026-10-15. This supersedes the provisional Nissui and Hokuto decisions
recorded in Milestone 4. The final `result/` files are the authoritative output.

- Re-ran the complete 10-company Gemini pipeline from the supplied homepages:
  10 records, 40 field decisions, 37 FOUND, 3 MULTIPLE_CANDIDATES.
- Nissui's final establishment value is `1943年3月`, supported by an official
  company Q&A quote with the month. Hokuto's final value is `1964年7月`, supported
  by an official history quote. No month was inferred from a year-only profile.
- The prior audit re-fetched 14 distinct official source pages. After the final
  run, a separate fetch checked all 40 saved quotes on 12 distinct official
  source pages; no mismatches were found. JSON and CSV content matched.
- Final review found that the validator did not ensure each extracted value was
  in its quote, and validation errors did not stop output. Both were fixed with
  regression tests. One validation retry handles transient non-verbatim quotes;
  a second failure stops output. The final run used one retry and exited 0.
  `pytest -q`: 76 passed; `ruff check .`: passed; `mypy src tests`: passed.
- The ChatGPT planning share link and a redacted Codex prompt/response export are
  in `prompts/`. The user confirmed `prompts/03` contains all Claude Code prompts;
  its AI responses are summarized, so the original responses or conversation
  share link are still needed for the assignment's conversation-history rule.
- The Gemini key is in local ignored `.env`; it is absent from tracked files.
