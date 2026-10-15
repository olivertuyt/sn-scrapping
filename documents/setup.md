# Claude Code + GLM-5.3 Setup Guide (v2: Skills & Plugins)

> Project: 9-hour web scraping + Generative AI extraction assignment
> Primary implementer: Claude Code + GLM-5.3
> Independent reviewer: Codex CLI
> Principle: **quality comes from execution evidence, not from the number of installed skills.**

---

## 0. TL;DR: Skill Decision

| Skill / plugin | Decision | How to use it here |
|---|---|---|
| **Superpowers** (`obra/superpowers`) | **Use selectively** | Keep `systematic-debugging`, `verification-before-completion`, `requesting-code-review`, `receiving-code-review`, lightweight `test-driven-development`. Skip `brainstorming`, `writing-plans`, `subagent-driven-development`, `dispatching-parallel-agents`, `using-git-worktrees`. |
| **Ponytail** (`DietrichGebert/ponytail`) | **Use, `lite` level only** | Anti-overengineering guard during implementation. Never `ultra`. Never allowed to cut validation, evidence checks, or error handling. |
| **Custom project skills** (this guide, Section 8) | **Must have** | `crawl-test`, `extraction-audit`, `quality-gate`, `submission-audit`. These encode the assignment's acceptance criteria. |
| Extra MCP servers (browser, Firecrawl, GitHub, memory, etc.) | **Do not install initially** | Add only for a demonstrated blocker. |

Precedence when instructions conflict:

```text
1. Assignment requirements
2. AGENTS.md / CLAUDE.md (project contract)
3. ACCEPTANCE_CRITERIA.md
4. Custom project skills
5. Superpowers skills
6. Ponytail
```

---

## 1. Why These Choices

### Superpowers: valuable, but its full workflow is too heavy for 9 hours

Superpowers is a skills framework covering TDD, systematic debugging, brainstorming, plan writing/execution, and subagent-driven development with code review. Its debugging methodology requires root-cause investigation before fixes, and its TDD skill enforces red-green-refactor.

Its session-start bootstrap (`using-superpowers`) pushes the agent to check and invoke skills on almost every response. That is useful for long projects, but in a 9-hour assignment it can cause:

- a brainstorming/spec phase you already completed (the research and implementation plan exist)
- re-writing an implementation plan that already exists
- subagent fan-out, extra tokens, and longer waits
- git worktree overhead with no benefit for a single-developer repo

**Keep the skills that directly prevent the most expensive failures:**

| Skill | Failure it prevents |
|---|---|
| `verification-before-completion` | Agent claims "done" without running code. This is the #1 vibe-coding failure. |
| `systematic-debugging` | Random patching of crawler/extraction bugs instead of finding the root cause. |
| `requesting-code-review` / `receiving-code-review` | Accepting or rejecting Codex findings without technical verification. |
| `test-driven-development` (light use) | Untested URL normalization, validation, and conflict logic. |

**Use TDD selectively**: apply strict red-green for deterministic logic (URL normalization, domain policy, ranking, evidence validation, conflict handling). Do **not** force TDD on exploratory crawling of live websites.

### Ponytail: a good guard against overengineering, if constrained

Ponytail makes the agent prefer: no code > existing code > standard library > installed dependency > minimal new code. It explicitly bans unrequested abstractions, scaffolding "for later", and new dependencies for a few lines of code.

This matches the assignment well: the biggest architectural risk is adding LangChain, Scrapy, agents, queues, or databases that do not move any acceptance criterion.

**Risk:** a "minimal code" mindset can collide with the quality requirements of this project. Explicitly protect these from being "simplified away":

- evidence and source URL validation
- null / NOT_FOUND / CONFLICT handling
- establishment-month rule
- retry and timeout handling
- logging of failures
- tests for high-risk logic

Use **`/ponytail lite`**. Do not use `ultra`.

### Custom project skills: the highest-value skills for this project

Generic skills do not know that:

- 10 companies × 4 fields = 40 field decisions must exist
- a month must never be inferred from a year
- Sakata Seed and Tama Home have multiple representative directors
- Sakata's corporate data lives on a different subdomain
- the README must be in Japanese

Project skills encode exactly this, so they are worth more than any marketplace plugin here.

---

## 2. Tooling

### Coding agents

- Claude Code with GLM-5.3 (via Z.AI GLM Coding Plan)
- Codex CLI as independent reviewer

### Python stack

```text
httpx (or requests)
beautifulsoup4
lxml
pydantic
<LLM provider SDK with structured output>
pytest
pytest-cov
ruff
mypy
playwright        # fallback only, add when needed
```

### Do not add initially

LangChain, Scrapy, Firecrawl, n8n, Dify, vector DB, Redis/Celery, Docker/Kubernetes, proxy rotation, many MCP servers.

---

## 3. Install and Configure Claude Code + GLM-5.3

```bash
npm install -g @anthropic-ai/claude-code
claude --version
```

Configure GLM-5.3 using the official Z.AI documentation for Claude Code.

Rules:

1. Store credentials in environment variables, never in the repository.
2. **Verify the actual active model.** Z.AI's default mapping may point Claude Code tiers to a GLM Flash variant; confirm that the session uses the model you intend.
3. Keep provider settings out of committed files unless they contain no secrets.

### Smoke test (do this before starting the 9-hour clock if allowed)

In a throwaway directory:

```text
Create a trivial Python function and one pytest test.
Run the test.
Report the exact command and output.
Then state which skills are currently available to you.
```

Pass conditions:

- the agent edits files
- the agent runs commands
- the agent can list/invoke installed skills

> **GLM-specific caveat:** skills are model-invoked based on their descriptions. Skill auto-triggering was designed around Claude models; with GLM through Claude Code, auto-triggering reliability is not guaranteed. **Invoke critical skills explicitly with `/skill-name`** instead of relying on automatic activation.

---

## 4. Install Skills

### 4.1 Superpowers

Install from the official Claude plugin marketplace:

```text
/plugin install superpowers@claude-plugins-official
```

Or from the Superpowers marketplace:

```text
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace
```

Restart the session and verify the skills are listed.

**Constrain it** by adding this to `CLAUDE.md` (Section 6):

```markdown
## Superpowers usage policy

Requirements, research, and the implementation plan are already complete.

Do NOT run: brainstorming, writing-plans, subagent-driven-development,
dispatching-parallel-agents, using-git-worktrees.

DO use:
- verification-before-completion before claiming any milestone is done
- systematic-debugging for any failing crawl, test, or extraction
- requesting-code-review / receiving-code-review at review checkpoints
- test-driven-development only for deterministic logic
  (URL normalization, domain policy, ranking, validation, conflict handling)
```

If the plugin still pushes heavy workflows, alternative: disable the plugin and copy only the needed `SKILL.md` folders into `.claude/skills/`. Review each file before copying.

### 4.2 Ponytail

```bash
npx skills add https://github.com/DietrichGebert/ponytail --skill ponytail
```

Or install through its Claude Code plugin marketplace as documented in its repository.

Then in session:

```text
/ponytail lite
```

Add to `CLAUDE.md`:

```markdown
## Ponytail usage policy

Use Ponytail at `lite` level only. Never `ultra`.

Ponytail must NEVER remove or simplify:
- evidence / source URL validation
- null, NOT_FOUND, CONFLICT handling
- the rule that establishment month must not be inferred from year
- retries, timeouts, and failure logging
- tests for URL normalization, domain policy, validation, conflict handling
- the Japanese README or report.md requirements
```

### 4.3 Security check before installing any third-party skill

Skills execute as part of your agent session. Before enabling:

- read `SKILL.md` and any `scripts/` or `hooks/`
- check what hooks run at session start
- do not install skills that request credentials or network access you do not understand

---

## 5. Repository Structure

```text
project/
├── .claude/
│   └── skills/
│       ├── crawl-test/SKILL.md
│       ├── extraction-audit/SKILL.md
│       ├── quality-gate/SKILL.md
│       └── submission-audit/SKILL.md
├── prompts/
├── result/
├── src/
├── tests/
├── CLAUDE.md
├── AGENTS.md
├── ACCEPTANCE_CRITERIA.md
├── IMPLEMENTATION_PLAN.md
├── CURRENT_STATUS.md
├── README.md            # Japanese
├── report.md
├── requirements.txt
├── .env.example
└── .gitignore
```

- `CLAUDE.md` is read by Claude Code.
- `AGENTS.md` is read by Codex.
- Keep the hard rules **identical** in both. Simplest option: `CLAUDE.md` contains `@AGENTS.md` plus the Claude-specific skill policies.

> Decide whether `.claude/` belongs in the submission. It shows your AI workflow (a plus for "effective use of Generative AI"), but keep it clean and free of secrets.

### `.gitignore`

```gitignore
.env
.env.*
!.env.example
.venv/
venv/
__pycache__/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/
browser_profiles/
cookies/
traces/
playwright-report/
.claude/settings.local.json
*.tmp
```

If logs are a deliverable, commit only the sanitized `result/run.log.jsonl`.

---

## 6. `AGENTS.md` (shared contract)

```markdown
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
```

## 7. `CLAUDE.md`

```markdown
@AGENTS.md

## Working mode
- Read AGENTS.md, ACCEPTANCE_CRITERIA.md, IMPLEMENTATION_PLAN.md, CURRENT_STATUS.md first.
- One milestone at a time.
- After each milestone: run /quality-gate, then superpowers verification-before-completion,
  then update CURRENT_STATUS.md with commands and evidence.

## Superpowers usage policy
(see Section 4.1)

## Ponytail usage policy
(see Section 4.2)
```

---

## 8. Custom Project Skills

Create each file at `.claude/skills/<name>/SKILL.md`.

### 8.1 `crawl-test`

```markdown
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
```

### 8.2 `extraction-audit`

```markdown
---
name: extraction-audit
description: Audit LLM extraction results for hallucination, missing evidence, and wrong field semantics. Use after any extraction run or change to prompts, schema, or validation.
---

# Extraction Audit

Read result/companies.json and the cached cleaned pages.

For each of the 40 field decisions check:
1. Non-null value has source_url that was actually fetched.
2. Non-null value has evidence that is a substring of the cleaned source text.
3. Value is supported by the evidence (not just present nearby).
4. established_year_month contains a month only if the evidence contains a month.
5. 創業/founded is not used as 設立/established unless the source says so.
6. Multiple representatives (Sakata Seed, Tama Home) are preserved or marked
   MULTIPLE_CANDIDATES/CONFLICT, not silently reduced to one.
7. Multiple head offices (Yukiguni Factory) are handled explicitly.
8. Missing values are null with status NOT_FOUND, never "", "N/A", or guesses.

Output: company | field | value | status | evidence OK | issue.
List every failure with the reason. Never "fix" a value by guessing.
```

### 8.3 `quality-gate`

```markdown
---
name: quality-gate
description: Run deterministic quality checks and validate real outputs. Use before claiming any milestone is complete and before every commit.
---

# Quality Gate

Run and report exact output:

    ruff check .
    mypy src
    pytest -q

Then, if result files exist, verify:
- 10 company records exist
- 40 field decisions exist
- JSON parses; CSV parses with the expected header
- every non-null field has source_url and evidence
- no secrets in tracked files (search for api_key, sk-, Authorization, token)

Return PASS only if every check passed. Otherwise return FAIL with the failing items.
```

### 8.4 `submission-audit`

```markdown
---
name: submission-audit
description: Final audit of the repository against assignment requirements. Use before the final commit.
---

# Submission Audit

Check each item and give evidence:

1. prompts/, result/, src/, README.md, report.md exist with exact names.
2. README.md is written in Japanese and contains setup + run instructions.
3. README setup steps were actually executed successfully.
4. report.md compares multiple approaches by Cost, Speed, Quality/Completeness.
5. report.md explains the final technology selection.
6. report.md Task B section: observed anti-bot measures, attempts, results,
   or clearly marked as not attempted (optional).
7. Conversational AI history exported into prompts/ as TXT (or share links listed).
8. result/ contains CSV or JSON for all 10 companies.
9. No .env, API keys, cookies, or browser profiles tracked by Git.
10. git status is clean; all deliverables committed.

Output a PASS/FAIL table mapped to ACCEPTANCE_CRITERIA.md IDs.
Any item without evidence is FAIL.
```

---

## 9. ACCEPTANCE_CRITERIA.md

```markdown
| ID | Priority | Requirement | Evidence | Status |
|---|---|---|---|---|
| AC-01 | MUST | Start from all 10 supplied homepages | crawl log | TODO |
| AC-02 | MUST | Follow internal/official links | discovered URLs | TODO |
| AC-03 | MUST | Process all 10 companies | result files | TODO |
| AC-04 | MUST | 4 fields per company (40 decisions) | JSON | TODO |
| AC-05 | MUST | Generative AI performs extraction | extractor + prompts | TODO |
| AC-06 | MUST | Missing values explicit | JSON status | TODO |
| AC-07 | MUST | Evidence for non-null fields | JSON | TODO |
| AC-08 | MUST | Source URL for non-null fields | JSON | TODO |
| AC-09 | MUST | Generalizable approach | code + tests | TODO |
| AC-10 | MUST | CSV or JSON in result/ | result/ | TODO |
| AC-11 | MUST | Japanese README | README.md | TODO |
| AC-12 | MUST | Technology comparison | report.md | TODO |
| AC-13 | MUST | Cost evaluated | report.md | TODO |
| AC-14 | MUST | Speed evaluated | report.md | TODO |
| AC-15 | MUST | Quality / Completeness evaluated | report.md | TODO |
| AC-16 | MUST | Conversational AI history (TXT) or share link | prompts/ | TODO |
| AC-17 | MUST | No secrets in Git | audit | TODO |
| AC-18 | MUST | All committed before deadline | git log | TODO |
| AC-19 | OPTIONAL | Task B anti-bot report | report.md | TODO |
```

---

## 10. Prompt History Requirement

The assignment requires conversational AI history (TXT) or share links.

- Export ChatGPT/Claude/Copilot research conversations into `prompts/*.txt` or list share links.
- **Be conservative with Claude Code and Codex sessions:** export or summarize their key prompts into `prompts/` as well, so there is no ambiguity.
- Sanitize: remove API keys, tokens, and personal data before committing.

Suggested files:

```text
prompts/01_requirement_analysis.txt
prompts/02_website_research_and_architecture.txt
prompts/03_claude_code_implementation_sessions.txt
prompts/04_codex_reviews.txt
prompts/05_extraction_system_prompt.txt
```

---

## 11. Codex Reviewer Prompt

```text
Act as an independent senior reviewer. Do not modify code yet.

Read AGENTS.md, ACCEPTANCE_CRITERIA.md, IMPLEMENTATION_PLAN.md,
CURRENT_STATUS.md, src/, tests/, and result/.

Run ruff, mypy, pytest. Inspect actual result files.

Review for:
1. assignment requirement violations
2. crawler/URL/domain bugs
3. hidden site-specific logic
4. LLM hallucination risk and unsupported values
5. missing evidence/source validation
6. wrong establishment-month or representative handling
7. tests that pass without proving the requirement
8. unnecessary complexity
9. secret leakage

Return findings as BLOCKER / HIGH / MEDIUM / LOW with:
file, problem, evidence/reproduction, impact, recommended fix.
No style-only refactors.
```

In Claude Code, process Codex findings with Superpowers `receiving-code-review`: verify each finding technically before fixing; reject findings that are wrong, with reasons.

---

## 12. 9-Hour Workflow with Skills

| Time | Work | Skills invoked |
|---|---|---|
| 00:00–00:30 | Scaffold, contract files, smoke test | `/ponytail lite` |
| 00:30–01:15 | 3-site spike: Nissui, Sakata, Mirait | `/crawl-test` (3 sites) |
| 01:15–03:00 | Generic crawler, ranking, cleaner | TDD for normalization/domain/ranking, `/crawl-test`, `/quality-gate` |
| 03:00–03:15 | **Codex review #1** (crawling/generalization) | `receiving-code-review` |
| 03:15–04:45 | LLM extraction + validation + conflicts | TDD for validation/conflicts, `/quality-gate` |
| 04:45–05:45 | Full 10-company run | `/crawl-test`, `/extraction-audit`, `systematic-debugging` on failures |
| 05:45–06:00 | **Codex review #2** (evidence/hallucination) | `receiving-code-review` |
| 06:00–07:15 | Fixes, tests, clean rerun | `systematic-debugging`, `/quality-gate`, `verification-before-completion` |
| 07:15–08:00 | Japanese README, report.md, prompts/ | `/submission-audit` (draft) |
| 08:00–08:30 | Task B only if Task A passes | none required |
| 08:30–09:00 | Final audit + commit | `/quality-gate`, `/submission-audit`, Codex final review |

Hard checkpoints:

- **03:00** crawler finds corporate pages generically for the 3 spike sites. Otherwise: no new features, fix the core.
- **06:00** 10 companies, 40 decisions, evidence present. Otherwise: skip Task B entirely.
- **08:00** all MUST criteria PASS. Only then start Task B.

---

## 13. Git Checkpoints

```text
chore: initialize project structure and agent contract
feat: implement generic crawler and candidate ranking
feat: add structured LLM extraction and validation
feat: process all 10 companies
test: add edge-case tests
docs: add Japanese README and technical report
chore: finalize submission
```

Run `/quality-gate` before each commit.

---

## 14. Rule of Thumb

When the agent (or any skill) proposes new complexity, ask:

> Which acceptance criterion does this move from FAIL to PASS?

No answer → do not add it.

When the agent says "done", ask:

> Show me the command, the output, and the result file that prove it.

No evidence → not done.
