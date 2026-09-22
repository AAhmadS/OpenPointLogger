---
name: project-trailmark-testing
description: How Trailmark's test suite is structured and run — plain scripts, not pytest
metadata:
  type: project
---

Trailmark (D:\.vscode\OpenPointLogger) has no pytest/unittest runner. Each `tests/test_*.py`
is a standalone script invoked as `PYTHONPATH=. python tests/test_<name>.py` (use
`.venv/Scripts/python.exe` on this Windows box to get the right interpreter). Each script
prints PASS/FAIL lines via its own `check()` helper, appends failures to a local `FAILS`
list, and exits non-zero only if `FAILS` is non-empty at the end — a clean run prints
`ALL CHECKS PASSED` and exits 0. Known suites as of 2026-09-15: `test_export.py`,
`test_store.py`, `test_science.py`, `test_hotkey.py`, `test_llm.py`. `test_export.py`
exercises every template x every export format combination and is the slowest of the five
(builds real PDFs via `pdf_render`).

**Why:** the repo has no CI (confirmed in `.claude/PROJECT_STATE.md` phase evidence) — these
scripts are the only automated verification that exists, and they must be run individually
with real exit codes captured (never piped through `tail`/`head`, which masks the exit code).

**How to apply:** when asked to verify a Trailmark change, run each relevant `tests/test_*.py`
separately and paste the literal tail + exit code, matching the existing script's own
check-style if adding new assertions (see [[feedback-match-existing-test-style]] pattern:
read a test file's existing checks before adding new ones, don't introduce a different
pattern/framework).

Also: on this Windows box, writing temp files to `/` (bash root) fails with "Permission
denied" — always redirect command output/temp files to the scratchpad directory instead.
