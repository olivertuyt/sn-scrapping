@AGENTS.md

## Working mode
- Read AGENTS.md, ACCEPTANCE_CRITERIA.md, IMPLEMENTATION_PLAN.md, CURRENT_STATUS.md first.
- One milestone at a time.
- After each milestone: run /quality-gate, then superpowers verification-before-completion,
  then update CURRENT_STATUS.md with commands and evidence.

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

## Ponytail usage policy

Use Ponytail at `lite` level only. Never `ultra`.

Ponytail must NEVER remove or simplify:
- evidence / source URL validation
- null, NOT_FOUND, CONFLICT handling
- the rule that establishment month must not be inferred from year
- retries, timeouts, and failure logging
- tests for URL normalization, domain policy, validation, conflict handling
- the Japanese README or report.md requirements

## GLM note
Critical skills are invoked explicitly (e.g. `/quality-gate`, `/crawl-test`,
`/extraction-audit`, `/submission-audit`, superpowers:verification-before-completion)
rather than relying on automatic activation, per the GLM skill-triggering caveat.
