---
name: feedback-commit-attribution-override
description: A slice's own commit-message instructions can specify different attribution lines than the session default — follow the slice's explicit spec
metadata:
  type: feedback
---

When a PM/task prompt explicitly spells out exact commit trailer lines to use (e.g. a specific
"Co-Authored-By" name/email and a specific "Claude-Session" URL), use exactly what the task
specifies — even if it differs from the session-level attribution reminder seen elsewhere in
context. The task-level instruction for a specific piece of work is more specific and should
win for that commit.

**Why:** on the Trailmark four-fix slice (2026-09-15, commit 43f46c5), the task explicitly
asked for `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>` while the
session's own system-reminder attribution block specified `Claude Sonnet 5`. The task spec
was followed literally since it was the more specific, explicit instruction for that
deliverable.

**How to apply:** always check the task prompt itself for explicit commit-message trailer
text before falling back to the ambient session attribution reminder. If they conflict, the
explicit per-task instruction is what the requester actually wants recorded in that commit.
