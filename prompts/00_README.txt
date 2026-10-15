Prompt history map (2026-10-15)
================================

Read by workflow: 01 requirements -> 02 research/design -> 03 implementation
-> 05 runtime extraction prompt -> 06 Gemini execution -> 04 independent
review. File numbers group topics; they are not a strict timestamp order.
07 is the available Codex conversation export that supports parts of 04/06.

File  Record type                         What it proves
01    ChatGPT share link + summary        Planning conversation; link is the
                                         primary prompt-and-response record.
02    Decision summary                   Research/design rationale, not a
                                         verbatim conversation export.
03    Claude Code user prompt + summary  All user prompts confirmed by the
                                         user; AI response history is missing.
04    Review template + outcome summary  Review criteria and findings; see 07
                                         for available actual exchanges.
05    Active system prompt               Loaded by src/extract.py at runtime;
                                         this reviewed version governs future
                                         extraction, not the archived runs.
06    Execution summary                  Gemini integration and run evidence;
                                         see 07 for actual Codex exchanges.
07    Redacted Codex transcript export   Available prompts and responses,
                                         grouped by original session.

These record types are deliberately distinct. A decision or action summary
must not be presented as an AI response. The Claude Code/GLM conversation's
responses or shareable link remain unavailable, so the assignment's history
requirement is still partial. Do not invent the missing response text.

The Codex export is a historical record: later corrections in 04/06 do not
rewrite earlier statements in 07. Credentials are redacted; no key, cookie,
or browser profile belongs in this directory.
