# Implementation Plan

Derived from documents/setup.md and documents/Web_Scraping_and_Data_Extraction_Assignment_EN.md.
The architecture is fixed by AGENTS.md; this file tracks the milestone sequence.

## Pipeline (fixed architecture)

Seed homepage → official-domain link discovery → URL normalization/dedup
→ candidate ranking → HTTP retrieval → HTML cleaning
→ LLM structured extraction → deterministic validation → CSV/JSON.

## Milestones

### M0 — Scaffold + contract (00:00–00:30) — DONE
- venv + Python stack, smoke test, skills, contract files, git init + first commit.

### M1 — 3-site spike (00:30–01:15)
- Minimal generic crawler for Nissui, Sakata Seed, Mirait One.
- Verify: starts at homepage, follows internal links, ranks profile page in top 5.
- Skill: /crawl-test (3 sites only). No LLM calls.

### M2 — Generic crawler, ranking, cleaner (01:15–03:00)
- URL normalization + dedup (fragments, tracking params), domain policy,
  candidate ranking (keyword scoring: 会社概要/企業情報/会社情報/IR/沿革 etc.).
- TDD for normalization/domain/ranking (deterministic logic only).
- Skills: /crawl-test, /quality-gate.
- Hard checkpoint 03:00: spike sites work generically, else stop features and fix core.

### Codex review #1 — crawling/generalization (03:00–03:15)
- Process findings with superpowers receiving-code-review.

### M3 — LLM extraction + validation + conflicts (03:15–04:45)
- Provider SDK with structured output, system prompt (see
  prompts/05_extraction_system_prompt.txt), pydantic schema:
  head_office_address, representative, capital, established_year_month.
- Each field: value, status (FOUND/NOT_FOUND/CONFLICT/MULTIPLE_CANDIDATES),
  source_url, evidence (verbatim).
- TDD for validation/conflict logic (month inference ban, 創業≠設立, multi-representative).

### M4 — Full 10-company run (04:45–05:45)
- All 10 companies; /crawl-test + /extraction-audit; systematic-debugging on failures.
- Hard checkpoint 06:00: 10 companies, 40 decisions, evidence present, else skip Task B.

### Codex review #2 — evidence/hallucination (05:45–06:00)

### M5 — Fixes, tests, clean rerun (06:00–07:15)
- /quality-gate, superpowers verification-before-completion before claiming done.

### M6 — Docs (07:15–08:00)
- Japanese README.md (setup + run instructions, actually executed),
  report.md (Cost/Speed/Quality comparison, tech selection, Task B section),
  prompts/ export of AI history.
- /submission-audit (draft). Hard checkpoint 08:00: all MUST criteria PASS.

### M7 — Task B optional (08:00–08:30)
- Only if Task A passes. https://vn.indeed.com/jobs?q=remote — document
  anti-bot measures and attempts/results in report.md.

### M8 — Final audit + commit (08:30–09:00)
- /quality-gate, /submission-audit, Codex final review, commit all.

## Git checkpoints (setup.md §13)

    chore: initialize project structure and agent contract
    feat: implement generic crawler and candidate ranking
    feat: add structured LLM extraction and validation
    feat: process all 10 companies
    test: add edge-case tests
    docs: add Japanese README and technical report
    chore: finalize submission

Run /quality-gate before each commit.
