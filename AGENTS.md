# Project Rules

## Objective
Complete the web scraping + Generative AI extraction assignment within 9 hours.
Correctness, traceability, completion, and simplicity beat architectural sophistication.

## Architecture
Seed homepage → official-domain link discovery → URL normalization/dedup
→ candidate ranking → HTTP retrieval → HTML cleaning
→ LLM structured extraction → deterministic validation → CSV/JSON.
Playwright is fallback only after a demonstrated HTTP-content failure.

## Hard Rules
1. Start crawling from the supplied homepage for every company.
2. Do not hardcode company-profile URLs as the normal solution.
3. No site-specific selectors unless generic logic demonstrably fails; document any exception.
4. Never fabricate company information.
5. Every non-null field must have source_url and verbatim evidence.
6. Never infer establishment month from a year alone.
7. Do not silently resolve multiple representatives, multiple addresses, or conflicts.
8. HTTP 200 is not proof of useful content.
9. Code existing is not completion. Execute it and inspect output.
10. Tests are PASS only if actually run.
11. No new framework without a concrete observed blocker.
12. Never commit secrets, API keys, cookies, browser profiles.

## Known data edge cases (from research)
- Nissui, Hokuto: profile page has year only; month is on the history page.
- Sakata Seed: corporate data is on a separate corporate subdomain.
- Sakata Seed, Tama Home: two representative directors.
- Yukiguni Factory: two head offices.

## Definition of Done
10 companies processed, 40 field decisions, evidence + source for every non-null value,
valid JSON/CSV, tests passing, Japanese README, report.md, prompt history, no secrets, committed.
