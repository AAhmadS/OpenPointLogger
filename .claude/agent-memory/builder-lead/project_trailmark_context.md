---
name: project-trailmark-context
description: What Trailmark is, its phase evidence, and the owner's design-first rule for new surfaces
metadata:
  type: project
---

Trailmark (formerly OpenPointLogger, D:\.vscode\OpenPointLogger) is a Windows tray app
(Python 3.12, pywebview/WebView2, PyInstaller) for capturing cited research points from a
global-hotkey popup and exporting them as formatted reports (HTML/Markdown/PDF/DOCX/LaTeX).
Single-developer, pre-PMF, phase `build` (confirmed via `.claude/PROJECT_STATE.md` as of
2026-09-15: no CI, no committed test-run artifacts, user data gitignored, 5 unpushed commits
ahead of origin/main). An untracked `.env` holds a live Telegram bot token
(`TELEGROM_BOT` — note the typo'd key name, this is the real key spelling in the file, not a
transcription error) — as of 2026-09-15 this is now gitignored (see the four-fix commit
43f46c5).

**Why it matters:** the owner's backlog mixes same-day desktop bug fixes with a stated
"design-first" rule — future slices toward multi-platform expansion (accounts, billing,
mobile, a Telegram bot, a website) cannot start implementation before a design/contract
pass, per `PROJECT_STATE.md`'s own wording.

**How to apply:** treat same-day desktop bug fixes (duplicate UI elements, keybinding
behavior, export file leaks) as normal `build`-phase work needing no gates beyond qa
(+security only when auth/crypto/network/DB is touched). Treat anything touching the
multi-platform backlog as needing a stage-0/1 pass first — flag it up to the PM rather than
implementing directly. See also [[project-trailmark-testing]].
