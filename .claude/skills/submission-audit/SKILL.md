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
