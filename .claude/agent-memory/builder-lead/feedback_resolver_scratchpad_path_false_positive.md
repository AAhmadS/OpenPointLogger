---
name: feedback-resolver-scratchpad-path-false-positive
description: resolve_evidence.py flags hex-looking segments of this machine's scratchpad temp path as unresolved commit hashes
metadata:
  type: feedback
---

`resolve_evidence.py`'s commit-hash regex fires on segments of this session's scratchpad temp path
(e.g. `...\claude\D---vscode-OpenPointLogger\0741386f-b3b9-4d24-8c66-81055bf07a59\scratchpad\...`) —
the conversation-id UUID gets split at hyphens and pieces like `0741386f` or `81055bf07a59` read as
short/long hex commit SHAs, producing `UNRESOLVED COMMIT` even though nothing in the claim was a
git reference.

**Why:** this is a tool limitation (the regex can't distinguish a UUID fragment from a hash), not a
fabrication — confirmed by independently verifying the same screenshot/harness files existed on disk
via direct file reads before relaying a worker's report that cited the path.

**How to apply:** when a report must cite a scratchpad path containing the session UUID (screenshot
paths, harness files), either (a) verify the referenced files exist yourself via `Read`/`ls` rather
than trusting the resolver's verdict on that one claim, or (b) label the path explicitly in the report
text as "session scratchpad path, not a commit" before running the resolver, per
`~/.claude/rules/evidence-resolvers.md`'s own guidance for unlabelled hex strings. Do not treat this
specific UNRESOLVED COMMIT shape as a real failure once the underlying file has been checked by hand —
but do not skip that manual check either. See [[project-trailmark-testing]] for this repo's other
scratchpad conventions.
