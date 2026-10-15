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
