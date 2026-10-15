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
