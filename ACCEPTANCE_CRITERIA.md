| AC-01 | MUST | Start from all 10 supplied homepages | crawl log | PASS — pipeline log: every company starts `crawling <name>` then GETs its homepage |
| AC-02 | MUST | Follow internal/official links | discovered URLs | PASS — 30 pages/company, same-site BFS; Sakata reached corporate subdomain |
| AC-03 | MUST | Process all 10 companies | result files | PASS — 10 records in result/companies.json + .csv (run 2026-10-15, exit 0) |
| AC-04 | MUST | 4 fields per company (40 decisions) | JSON | PASS — 40 decisions, 0 violations |
| AC-05 | MUST | Generative AI performs extraction | extractor + prompts | PASS — src/extract.py + prompts/05_extraction_system_prompt.txt |
| AC-06 | MUST | Missing values explicit | JSON status | PASS — null ⇒ NOT_FOUND/CONFLICT/MULTIPLE_CANDIDATES rule enforced+tested |
| AC-07 | MUST | Evidence for non-null fields | JSON | PASS — all 40 have verbatim evidence (validation, 0 warnings) |
| AC-08 | MUST | Source URL for non-null fields | JSON | PASS — all 40 have source_url (fetched-page check enforced) |
| AC-09 | MUST | Generalizable approach | code + tests | PASS — no hardcoded profile URLs; 76 tests run (urls/ranking/crawler/validation/extract/pipeline) |
| AC-10 | MUST | CSV or JSON in result/ | result/ | PASS — both companies.json and companies.csv (41 rows incl. header) |
| AC-11 | MUST | Japanese README | README.md | PASS — README.md in Japanese |
| AC-12 | MUST | Technology comparison | report.md | PASS — report.md §4 |
| AC-13 | MUST | Cost evaluated | report.md | PASS — report.md §4 コスト |
| AC-14 | MUST | Speed evaluated | report.md | PASS — report.md §4 速度 |
| AC-15 | MUST | Quality / Completeness evaluated | report.md | PASS — report.md §4 品質 |
| AC-16 | MUST | Conversational AI history (TXT) or share link | prompts/ | PARTIAL — user confirms 03 contains all Claude Code prompts, but its AI responses are summarized rather than recorded; ChatGPT share link is in 01 and Codex prompt/response export is in 07 |
| AC-17 | MUST | No secrets in Git | audit | PASS — local `.env` is ignored; no key-like token found in tracked files |
| AC-18 | MUST | All committed before deadline | git log | PARTIAL — reviewed local artifacts are included in the final local commit; the Claude transcript is pending and no remote/push is configured |
| AC-19 | OPTIONAL | Task B anti-bot report | report.md | PASS — report.md §5 (Cloudflare JS challenge; 3 attempts documented) |
