---
report: project-state
project: Trailmark (formerly OpenPointLogger)
generated: 2026-09-15
generated_by: project-cartographer
branch: main
last_updated: 2026-09-22 by main session: owner answered the 20-question decision set; gates resolved, PRODUCT_SPEC amended (§0.1), ASR default moved to OpenRouter, Trailmark.spec un-ignored
schema_version: 1
phase: build
phase_evidence: >
  No CI config anywhere in the tree (only stray .playwright-mcp/*.yml page dumps, not workflow
  files). No committed test-run artifacts. User data files (points.json, config.json,
  attachments/, exports/) are gitignored, confirming this runs against a single developer's own
  local data, not a served product. An untracked .env holds a live Telegram bot token
  (key literally spelled TELEGROM_BOT) and an untracked image.png sits in the repo root —
  both signs of an active, unstaged working session rather than a stabilized release. 5 commits
  sit ahead of origin/main, unpushed. This is pre-PMF single-developer desktop software under
  active feature development: phase build, builder-lead posture, medium risk tolerance.
legend:
  status: "done = merged and independently verified; todo = not yet done"
  importance: "critical | high | medium | low — weight to the product/architecture"
  force: "now (cheap, unblocks others) | scheduled (needs a coordination window) | later"
  human_gate: "none | review (approve before merge) | decision (must choose direction first) | action (only a human can do it)"
---

## big_picture

Trailmark is a Windows tray app (Python 3.12, pywebview/WebView2, PyInstaller) for capturing
research points with cited sources from a global-hotkey mini popup, then exporting them as
formatted, cited reports (HTML/Markdown/PDF/DOCX/LaTeX) via a template system. It has just
finished a design-system pass (commit `301e61e`) bringing the UI onto a committed design
language, and a tray-menu rewrite (commit `69f2e27`) dropping pystray for an owned Win32 menu.
The owner's new backlog is a mix of same-day desktop bugs (duplicate logo, unselectable popup
text, Enter-key mislogging, a format-selection bug that leaks unrequested export files), unbuilt
product surface (category/template management, clipboard-aware source capture, an auto-ASR
logging mode), and a full platform expansion (accounts, paid plans, mobile apps, a Telegram bot,
a website) that does not exist as code, design, or product spec yet. The gap is not "bugs vs.
polish" — it's a single-user local desktop tool that the owner wants to grow into a
multi-platform product with billing and a mobile/web presence, and none of the multi-platform
plumbing (auth, sync backend, hosted API keys, subscriptions) has been designed. The owner's
explicit design-first rule means slices 2-6 below cannot start implementation before a
corresponding page existing in the "Trailmark Design System" project in the separate Claude
Design tool (its URL is the one the owner gave in their request; it is a design-tool project
URL, not a git commit or a path in this repo — omitted here so its UUID is not mistaken for a
commit SHA by anyone scanning this report).

## small_pictures

- **The in-app topbar mark is a leftover from before the design system existed, not a deliberate
  triple-brand.** `ui.py` has three separate logo renders: the OS window icon (`point_logger.py:543`,
  `webview.start(..., icon=...)`), an in-app `<header class="topbar">` with `.tb-mark`+`.tb-title`
  (`ui.py:715-717`), and the sidebar `.brand` block (`ui.py:525-528, 728`). The design system's
  main-window page inside that external Claude Design project (not a file in this git repo) uses a frameless window with the sidebar brand as the only in-content mark — the topbar duplicate was never removed when the frameless design shipped.
- **The popup is undraggable-by-design and that's what broke text selection.** `easy_drag=True`
  at window-creation time (`point_logger.py:466-468`) makes pywebview treat every mousedown as a
  window-drag start, which is why `body{user-select:none}` (`ui.py:240`) isn't even the whole
  story — even with user-select enabled, drag would still eat the mouse-down. Both must change
  together: `easy_drag=False` + a `pywebview-drag-region` class scoped to the header only.
- **The format-leak bug is a listing bug, not a generation bug.** `pipeline.export()` always
  writes `report.html` to disk as the PDF-rendering intermediate whenever `html` or `pdf` is
  requested (`pipeline.py:535-539`), and `point_store._read_export()` lists every `report.*` file
  it finds on disk (`point_store.py:262-268`) rather than trusting the per-export `manifest.json`
  — so a PDF-only export still surfaces an "html" file in the Exports tab. A `manifest.json` is
  already being written per export; `_read_export` just isn't reading it.
- **There is no category concept at all, only a flat template list with a free-text grouping
  field.** `templates_registry.py`'s `purpose` key defaults to `"general"` and is described in its
  own docstring as "used for grouping only" (`templates_registry.py:86`) — it is not rendered
  anywhere as a category, has no create-UI, and there's a single global `export.template` setting
  in config, so "default template per category" has no home to live in yet. The Claude Design
  prototype already names "Business Formal" and "Team Report" as template cards, ahead of any
  backing template folder existing in `templates/` (only `personal-report`, `protocol`,
  `research-roam` exist on disk) — the design is ahead of the data model here, which is unusual
  and worth preserving: build the category/default model to match what's already drawn.
- **The hotkey subsystem is single-listener today; multiplexing needs a second RegisterHotKey
  registration, not a rewrite.** `HotkeyListener` (`hotkey.py`) runs its own Win32 message loop
  per instance with a fixed `_id = 0x4343`. A second instance with a different id is a safe,
  additive way to add Ctrl+Alt+V without touching the existing capture hotkey.
- **Pillow is already a dependency for a reason that isn't used yet.** `requirements.txt` lists
  `Pillow>=10.0`; nothing in `ui.py`/`point_logger.py` currently calls `ImageGrab`, so clipboard
  image capture is additive, not a new dependency.
- **The repo is mid-session, not between sessions.** Untracked `.env` (Telegram bot token, key
  name misspelled `TELEGROM_BOT` — never print the value) and untracked `image.png` (the owner's
  screenshot of the now-obsolete pystray tray menu) sit in the working tree; `.gitignore` does not
  yet exclude `.env`, so the first commit touching this backlog must add it there before anything
  else is staged, or the token risks being committed.
- **5 local commits are unpushed to origin/main** — normal for a solo dev, but means any
  "current state" claim from GitHub/CI would be stale; this report is built from the local tree.

## architecture_snapshot

| id | delta | current → target | status |
|---|---|---|---|
| A1 | Window chrome | 3 rendered logos → 2 (icon + sidebar) | done (43f46c5) |
| A2 | Popup interaction | drag-everywhere → draggable header only, selectable body text | done (43f46c5) |
| A3 | Popup logging keys | Enter logs → Alt+Enter logs, Enter inserts a newline | done (43f46c5) |
| A4 | Export listing | disk-glob of `report.*` → manifest-driven file list | done (43f46c5) |
| A5 | Template model | flat list → category entity, per-category default, create/preview UI, 5 built-ins | done (8d4ce4e) |
| A6 | Source capture | manual paste only → per-row clipboard buttons + Ctrl+Alt+V fills the popup with the detected item | done (b4326df, 489e95a, 3707427) |
| A7 | Logging modality | manual only → opt-in auto-ASR mode (energy VAD + OpenAI-compatible transcription) | done (508af97) |
| A8 | Distribution channel | desktop-only → + Telegram bot bridge (paired chat) | done (416ce2f backend, 772f811 UI) |
| A9 | Monetization | none → Free / Pro $5 / Plus plans | spec + design done (T17, D5); build blocked on .claude/gates/platform-expansion.yaml |
| A10 | Platform surface | Windows desktop only → + Android, iOS, Linux, website, accounts | spec + design done (T17, D5); build blocked on owner decisions |
| A11 | Explicitly deferred | in-app PDF reader, Chrome extension | **not planned** — see `.claude/research/pdf-and-extension.md`; do not schedule |

## workstreams.done

- id: D0.1
  title: "Design system adopted across the UI (light+dark, tokenised CSS, app top bar)"
  importance: high
  commit: 301e61e
  verified: "commit exists in `git log` on `main`; ui.py contains the tokenised CSS and topbar markup this commit introduced"

- id: D0.2
  title: "Owner-drawn Win32 tray menu replaces pystray; app icon shipped with the window"
  importance: medium
  commit: 69f2e27
  verified: "commit exists in `git log` on `main`; `traymenu.py` present, no `pystray` import remains in `point_logger.py`'s import list observed during this survey"

- id: D0.3
  title: "Scientific mode: claims/quotations/notes separated with real citation styles"
  importance: medium
  commit: f111ed2
  verified: "commit exists in `git log` on `main`"

- id: D0.4
  title: "Multi-format export pipeline, templates, grouped exports, Open-app fix"
  importance: high
  commit: f91a645
  verified: "commit exists in `git log` on `main`; `pipeline.py`, `templates_registry.py`, `TEMPLATES.md` present"

- id: T1-T4
  title: "Desktop bug batch: duplicate topbar logo removed, popup text selectable with header drag-region, Alt+Enter logs (Enter = newline), export format leak fixed, .env gitignored"
  importance: high
  commit: 43f46c5
  verified: "PM re-ran tests/test_export.py, test_store.py, test_science.py, test_hotkey.py, test_llm.py after the commit: each exit 0 (uncached, run as scripts); node --check on both extracted ui.py script blocks exit 0; grep confirms easy_drag=False (point_logger.py:468), pywebview-drag-region on popup header (ui.py:264), altKey gate (ui.py:455), no .tb-mark/.tb-title left; git status shows .env no longer untracked"

- id: D1-D4
  title: "Design pages written to the Claude Design project: app/categories-templates.html, app/clipboard-capture.html, app/asr-mode.html, app/telegram-bridge.html"
  importance: high
  commit: n/a (design-tool project, not a repo artifact)
  verified: "PM listed the project's app/ folder after the write and read the first lines of categories-templates.html: all four files present with the @dsCard header convention. Status: designed, awaiting post-hoc owner review (owner's working agreement: build first, review after)."

- id: T17
  title: "Stage-0 product shape for platform expansion: .claude/PRODUCT_SPEC.md (archetypes, per-platform surface inventory, plan split, sync + mobile options, e2e flow, open decisions)"
  importance: critical
  commit: n/a (uncommitted planning artifact under .claude/)
  verified: "PM confirmed .claude/PRODUCT_SPEC.md exists (447 lines, 11 sections); .claude/gates/platform-expansion.yaml parses with PyYAML, 7 gates all status unmeasured, each carrying question: and recommended: lines. Stage 1 (contract) NOT started - blocked on the owner decisions in that gate file."

- id: D5
  title: "Design pages for the platform expansion: platform/account-profile.html, platform/plan-picker.html, platform/mobile-capture-topics.html, platform/website-landing.html"
  importance: high
  commit: n/a (design-tool project)
  verified: "PM listed the project's platform/ folder: four files present. Status: designed, awaiting post-hoc owner review; plan contents in the UI follow the RECOMMENDED split in PRODUCT_SPEC.md s5 and are not an owner decision."

- id: T5-T9
  title: "Template categories: config section + registry category key, bridge CRUD + template_demo, export-dialog category strip / default badge / new-category popover / sandboxed live preview, Settings > Exports category list, built-in Business Formal + Team Report templates"
  importance: high
  commit: 8d4ce4e
  verified: "PM re-ran all five tests/test_*.py after the commit (each exit 0, uncached); node --check on both extracted ui.py script blocks exit 0; viewed scratchpad screenshot shot-preview.png showing category pills, Default badge, Set as default, docked preview pane and no topbar logo. Deferred qa findings (Medium/Low): double-submit guard on category create, unsaved-rename discard, duplicate popover markup, template_demo ignores scientific-mode style, delete_category unknown-id is a silent no-op. Env note: %APPDATA%/Trailmark/templates has older business-formal/team-report user templates (2026-09-07) shadowing the new built-ins on this machine - user data, left in place."

- id: T10-T11
  title: "Clipboard capture: clipboard.py classifier (image/link/text), per-row paste buttons in the popup, Ctrl+Alt+V auto-log hotkey (second HotkeyListener id 0x4344, off by default) with Undo toast, Settings > Hotkeys row"
  importance: medium
  commit: b4326df
  verified: "The builder-lead agent stalled before committing; PM verified and committed its work: all seven tests/test_*.py exit 0 (uncached, run separately, incl. new test_clipboard.py and test_clipboard_hotkey.py); node --check on both extracted ui.py script blocks exit 0; imports ok; PM read the point_logger.py/point_store.py/hotkey.py diff and spot-checked ui.py (clipboard text goes through textContent/value, innerHTML only carries constant icon markup); headless popup screenshot shows the three paste buttons and the pasted-image chip. Not run: qa-lead gate (agent died first) - a code-review pass over b4326df is a cheap follow-up. Open check: headless Edge shows a ~10px right overflow of the popup at 462px that affects pre-existing elements too; confirm against the real window after the rebuild."

- id: T12-T14
  title: "Auto-ASR logging mode: asr.py (sounddevice RawInputStream + energy VAD + WAV utterances, OpenAI-compatible /audio/transcriptions via urllib multipart), asr config section + save_asr/test_asr/list_asr_devices bridge, utterances logged as note entries into the last open topic, topbar state chip + tray label, Settings > Voice logging"
  importance: medium
  commit: 508af97
  verified: "PM re-ran all 8 tests/test_*.py after the commit (each exit 0; test_clipboard printed an environmental SKIP because the clipboard was locked, still exit 0); node --check on both extracted ui.py script blocks exit 0; import ui, point_logger, asr, traymenu ok; viewed asr_logged.png showing the Voice logging card and the 'Logged' topbar chip. New dependency sounddevice>=0.4 in requirements.txt and hiddenimport in the gitignored Trailmark.spec - exe build NOT yet verified (done at the end of the run). qa: 2 High fixed before commit (transcription moved off the audio callback thread; apply_asr start/stop lock). security-lead: SHIP, no Medium+. Deferred Medium/Low: device index 0 treated as default; Test-5-seconds uses last-saved config not the live form; concurrent test capture can open a second stream; tray label may read On when sounddevice is missing; blank endpoint/model reverts to previous value; dead hasattr guard in push_asr_state."

- id: T11b
  title: "Clipboard hotkey review fixes: Store.add_entry returns entry_id (Undo targets the exact entry), Store mutators/readers used from the hotkey and ASR threads take an RLock"
  importance: high
  commit: 489e95a
  verified: "PM re-ran all 8 tests/test_*.py after the commit, each exit 0; grep confirms RLock at point_store.py:220, entry_id at point_store.py:562 and point_logger.py:735; _newest_entry_id removed."

- id: T15-T16
  title: "Telegram bridge backend: telegram_bridge.py (token from config or .env incl. the misspelled TELEGROM_BOT key, dotenv parser, long-polling getUpdates on a daemon thread with backoff, pairing via /start <code>, one paired chat only, text -> note / URL -> link source / photo -> image source, /topic switching, help reply), telegram config section (token masked in state(), token_set flag), Api.save_telegram / telegram_regenerate_code / telegram_unpair / telegram_status, Controller.apply_telegram + push_telegram_state -> JS telegramState()"
  importance: medium
  commit: 416ce2f
  verified: "Committed by the main session after this loop's builder-lead run was cut off by a rate limit; PM confirmed on resume: commit present on main, tests/test_telegram.py exists (332 lines) and exits 0 together with the other 8 test scripts; point_store.state() masks telegram.token (point_store.py:286). The Settings UI for it is slice F (next)."

- id: T10-T11 (contract change) + topbar deadlock fix
  title: "Ctrl+Alt+V now parks the clipboard read on the controller, opens the quick-capture popup and attaches it there as a pending link/string/image chip via Api.take_clipboard_capture() -> JS clipboardCaptured(); it never files an entry directly any more (clipboard.enabled defaults to True; the Undo toast path is gone). Topbar '+' deadlock fixed: popup.on_top set from the JS-bridge thread deadlocked pythonnet's GIL against SetWindowPos; topmost is now asserted through a ctypes _set_topmost(hwnd, bool) on HWNDs cached in the shown events."
  importance: high
  commit: 3707427
  verified: "Committed by the main session; PM confirmed on resume: commit present, tests/test_clipboard_hotkey.py rewritten to the new contract, all 9 tests exit 0, node --check on both ui.py script blocks ok. Design page app/clipboard-capture.html was updated to the attach-not-log contract by the main session. Standing rule recorded below: never set a pywebview Window property from a non-UI thread."

- id: F (Telegram Settings UI)
  title: "Settings > Telegram bridge card (enable switch, status row, pairing code with Copy/Regenerate, bot-token field that never echoes the value, Unpair with confirm) + topbar #tgChip driven by telegramState()"
  importance: medium
  commit: 772f811
  verified: "PM re-ran all 9 tests/test_*.py after the commit (each exit 0, venv python); node --check on both extracted ui.py script blocks exit 0; staged diff scanned for token-shaped literals: 0; viewed shot-telegram-paired.png (card + chip match app/telegram-bridge.html). qa-lead found 1 Critical before commit (transient no_topic/logged pushes were persisted as connection state, hiding Unpair) - fixed and re-verified by builder-lead. Cosmetic leftover: Unpair uses an inline style instead of a .btn.danger-ghost class."

- id: BUILD
  title: "Rebuilt dist/Trailmark.exe from 772f811 (+ committed map 10b46b9), installed to %LOCALAPPDATA%/Programs/Trailmark, relaunched"
  importance: high
  commit: n/a (build artifact; Trailmark.spec itself is now tracked - .gitignore carries a !Trailmark.spec exception as of 2026-09-22)
  verified: "PyInstaller 6.22.2 via .venv python, exit 0, hook-sounddevice.py processed, exe 33,853,231 bytes; both Trailmark processes stopped, file copied, SHA256 of dist and installed exe equal; relaunched 2026-09-22 08:45, still alive after 109 s; HotkeyListener.probe reports Ctrl+Alt+P and Ctrl+Alt+V both HELD by another process (the running app). Not exercised by hand: voice logging and Telegram polling against live services from the packaged exe."

## workstreams.todo

- id: T18
  title: "Backend: accounts + auth service (whichever stack is chosen in T17)"
  importance: high
  force: scheduled
  depends_on: []
  agents: [db-lead, backend-lead]
  skills: []
  human_gate: none
  note: "UNBLOCKED 2026-09-22. Backend = managed BaaS (Supabase-style), owner decision; auth, Postgres and object storage come with it, so the greenfield surface is the schema and the sync op log, not a server. Still needs stage 1 first: openapi.yaml + schema.dbml before any endpoint, per build-protocol.md section 4. Region not established - pick at provisioning."

- id: T19
  title: "Billing integration for Free/Pro $5/Plus tiers"
  importance: high
  force: scheduled
  depends_on: [T18]
  agents: [backend-lead]
  skills: []
  human_gate: action
  status: blocked
  note: "STILL BLOCKED. Price is fixed at $5/month for Pro (owner, 2026-09-22) but tier contents, the Free-account rule and the payment provider are all deferred to pre-ship; no provider account exists. Gates business-decision-plans + billing-provider-account. Do not build."

- id: T20
  title: "Hosted API-key service for users who don't bring their own key"
  importance: medium
  force: scheduled
  depends_on: [T18]
  agents: [ai-engineering-lead, backend-lead]
  skills: []
  human_gate: decision
  status: blocked
  note: "PARTLY RESOLVED. Provider is decided: OpenRouter, deepseek/deepseek-v4-flash for LLM and whisper-1 for ASR (owner, 2026-09-22; already the shipped defaults). The usage cap per tier is deferred to pre-ship, and that is the number the service is built around, so this stays blocked."

- id: T21
  title: "Android app (React Native + Expo, sideloaded APK)"
  importance: medium
  force: scheduled
  depends_on: [T18]
  agents: [frontend-lead]
  skills: []
  human_gate: none
  note: "Framework decided 2026-09-22: React Native + Expo (owner accepted the recommendation). Distribution is a directly-installed APK - the owner has no Play developer account and will publish locally first, so no store listing, no store review, and in-app purchase is not available on this route. Blocked only on the stage-1 contract."

- id: T22
  title: "iOS app"
  importance: medium
  force: held
  status: held
  depends_on: [T18, T21]
  agents: [frontend-lead]
  skills: []
  human_gate: decision
  note: "HELD by owner 2026-09-22 (\"for now linux and ios should be held\"). Parked, not cut. When it resumes it inherits T21's React Native + Expo codebase, but needs an Apple Developer account (none exists) and an answer on the purchase route, both deferred. Do not start."

- id: T23
  title: "Linux desktop build"
  importance: low
  force: held
  status: held
  depends_on: []
  agents: [python-engineer]
  skills: []
  human_gate: none
  note: "HELD by owner 2026-09-22. Technically the cheapest surface left (pywebview has a GTK/Qt backend; it needs a Linux PyInstaller spec and a non-Win32 hotkey path), but out of scope for V1. Do not start."

- id: T24
  title: "Website: landing, auth, and the history/trajectory dashboard"
  importance: medium
  force: scheduled
  depends_on: [T18]
  agents: [frontend-lead]
  skills: []
  human_gate: review
  note: "RESCOPED 2026-09-22. The owner: \"on website, people will only have account and a history and trajectory of their tasks. We will provide them with a dashboard.\" So: buckets A (landing/pricing), B (auth), C-read-only (dashboard: history + trajectory of topics), D (account/billing), E (terms/privacy). NO capture surface on the web - no /capture, no web quick-log, no PWA capture bridge. Capture stays desktop + Android + Telegram. \"Trajectory\" is read as how a topic developed over time (points per topic over time, movement between categories); that reading is an assumption flagged in PRODUCT_SPEC.md section 0.1, not an owner statement."

## challenges

- id: C5
  risk: "pywebview Window property setters (on_top, title, ...) called from a non-UI thread (JS bridge, hotkey, ASR, Telegram threads) deadlock pythonnet's GIL against the UI thread; 3707427 hit this with popup.on_top"
  severity: High
  mitigation: "Rule for every worker touching point_logger.py: from non-UI threads only call Window methods (show/hide/evaluate_js); anything else goes through ctypes on the HWNDs cached in the shown events (_set_topmost). Pass this rule down verbatim in every slice brief."

- id: C1
  risk: "Untracked .env with a live bot token sits in a git working tree that is not yet ignoring it"
  severity: High
  mitigation: "Add .env to .gitignore in the very first commit of the Telegram slice (T15), before staging anything else; never echo or log the token value; verify with git status that .env stays untracked after the change."

- id: C2
  risk: "Template/category work in T5-T9 could be built ahead of or diverging from the Claude Design prototype, which already names specific template cards (Business Formal, Team Report) not yet backed by files on disk"
  severity: Medium
  mitigation: "Treat D1's design output as the source of truth for category names and defaults; build T9's two new templates to match those exact names so the shipped app doesn't contradict the approved design."

- id: C3
  risk: "Platform-expansion slice (T17-T24) has no backend, no chosen mobile framework, and no billing decision — starting implementation before the human decisions in T17/T18/T19/T20 land wastes the largest amount of work in this backlog"
  severity: High
  mitigation: "PARTLY DISCHARGED 2026-09-22. T18, T21 and T24 are released for work once the stage-1 contract exists; T22 and T23 are held by the owner; T19 and T20 stay blocked on the deferred business decisions. The rule survives for those two: do not let a lead schedule billing or hosted-key work until business-decision-plans and billing-provider-account leave unmeasured."

- id: C6
  risk: "api.telegram.org is unreachable from the owner's network - DNS returns the private address 10.10.34.36 and the TCP connect is actively refused (WinError 10061) after 5.21 s, while a control host completed TLS in 0.39 s on the same machine. T15/T16 are committed and unit-tested but have NEVER exchanged a packet with Telegram, and the .env token has therefore never been validated."
  severity: High
  mitigation: "Add proxy support to telegram_bridge.py: every outbound call goes through one UrllibTransport class on stdlib urllib, so a ProxyHandler-built opener fed from a Settings field covers the whole module. Alternative is a system-wide VPN, which needs no code but is outside the app. Owner decision recorded as gate telegram-network-reachability. Until then, no Telegram claim may be reported as working - only as unit-tested."

- id: C4
  risk: "ASR mode introduces a new class of always-listening background behavior with privacy/consent implications the owner hasn't specified"
  severity: Medium
  mitigation: "D3's design pass should make the listening/transcribing state visually unmissable and require an explicit on/off, not a background default; confirm with the owner whether meeting audio (loopback) or only microphone input is in scope before T12."

## human_checkpoints

- step: D1 category/template design review
  why: "New user-facing surface; owner's own design-first rule requires sign-off before implementation begins"
  kind: review

- step: D2 clipboard-capture design review
  why: "New interaction pattern (global hotkey side effects on clipboard) needs owner approval before build"
  kind: review

- step: D3 ASR mode design review
  why: "Introduces background audio processing; needs explicit design and consent-flow approval"
  kind: review

- step: D4 Telegram bridge design review
  why: "New external-facing channel tied to a real bot token"
  kind: review

- step: T15 Telegram token confirmation
  why: "Only the owner can confirm the token in .env is the intended production credential and authorize using it"
  kind: action

- step: T17 platform-expansion product decision
  why: "Business questions (Pro tier contents, hosted-provider choice, sync backend architecture) are commercial calls the repo cannot answer; this is stage-0 build-protocol gate G0.4"
  kind: decision
  status: "ANSWERED 2026-09-22 in part. G0.4 accepted; hosted provider, sync backend, mobile framework, surface matrix and website scope all decided. Tier contents, usage cap, Free-account rule, iOS purchase route and payment provider deferred to pre-ship - those remain open and keep T19/T20 blocked."

- step: D5 platform design direction
  why: "Build-protocol gate G2.5 (design direction accepted) is a named human gate, not delegable"
  kind: review

- step: T19 billing provider setup
  why: "Only a human can create/supply a live payment-provider account and keys"
  kind: action

- step: T20 hosted-provider selection
  why: "Choosing which LLM/ASR provider Trailmark resells, and usage caps per tier, is a cost/business decision"
  kind: decision

- step: T21/T22 mobile framework choice
  why: "React Native vs. Flutter vs. native affects both apps; a one-time architecture decision best made by the owner or escalated once, not decided twice independently"
  kind: decision
  status: "RESOLVED 2026-09-22: React Native + Expo, distributed as a sideloaded APK. iOS held."

- step: Telegram network reachability
  why: "api.telegram.org is intercepted on the owner's network (measured). Whether Trailmark grows a proxy setting or the owner runs a VPN is the owner's call; only they know the network"
  kind: decision

- step: Terms of service and privacy policy
  why: "Agent drafts to standards for Chantex / trailmark.chantex.ir, but publishing legal text binding a real company is the owner's signature, not an agent's"
  kind: review

## agent_skill_matrix

- when: "Desktop bug fixes (T1-T4), no new design needed"
  agent_or_skill: "frontend-lead / backend-lead -> python-engineer, no design skill"

- when: "Any new surface reaching a user (category picker, clipboard affordance, ASR mode, Telegram pairing, accounts/plans, mobile, website)"
  agent_or_skill: "design page written into the \"Trailmark Design System\" Claude Design project (see URL in big_picture; a design-tool project, not a repo commit) via mcp__claude-design__write_files, BEFORE implementation"

- when: "Platform-expansion stage-0/1 work (T17)"
  agent_or_skill: "engagement skill / delivery-orchestrator, producing PRODUCT_SPEC.md + surface inventory + contract, per ~/.claude/rules/build-protocol.md"

- when: "ASR/transcription provider selection or LLM routing for hosted keys (T13, T20)"
  agent_or_skill: "ai-engineering-lead (dispatches ai-model-strategist for the explore/exploit provider comparison)"

- when: "Any Win32-specific work (hotkeys, tray menu, window chrome)"
  agent_or_skill: "python-engineer with ctypes/pywebview familiarity — case-specific, not a generic backend task"

- when: "Verifying any of T1-T4 or T9's shipped templates"
  agent_or_skill: "qa-lead -> test-engineer (tests/ already has test_export.py, test_hotkey.py — extend, don't replace)"

- when: "Anything touching the .env Telegram token or billing keys"
  agent_or_skill: "security-lead review before merge, regardless of posture"

## owner_decisions_2026_09_22

The owner answered the open-decision set. Full record with statuses:
`.claude/gates/platform-expansion.yaml`; spec amendments: `.claude/PRODUCT_SPEC.md` §0.1.
Summary of what changed for planning:

- **V1 targets are desktop + Android + Telegram + website.** iOS (T22) and Linux (T23) are
  HELD — parked by the owner, not cut, not scheduled.
- **Website is not a capture surface.** It is: marketing landing, auth, dashboard showing
  history + trajectory of topics, account/billing, terms, privacy. This removes the web
  capture inbox and the Android-PWA bridge from the plan.
- **Sync = managed BaaS** (Supabase-style) with a local-first op log as the data model.
  Screenshots sync; exports do not. Region: still not established.
- **Mobile = React Native + Expo**, distributed as a directly-installed APK — the owner has
  no Play or Apple developer account and will "publish locally first".
- **Hosted AI = OpenRouter** for both LLM (`deepseek/deepseek-v4-flash`) and ASR
  (`whisper-1`). Applied in code the same day.
- **Deferred to pre-ship, still `unmeasured`:** tier contents, hosted-AI usage cap, whether
  Free ever needs an account, iOS purchase route, payment provider. These keep T19 and T20
  blocked. Only the $5/month price is fixed.
- **Supplied:** domain `trailmark.chantex.ir`, legal name `Chantex`, `.env` token confirmed.
- **Terms + privacy:** agent drafts to standards, owner accepts (new gate).

### New blocker — Telegram unreachable from the owner's network

Measured 2026-09-22 with the owner's authorisation: `api.telegram.org` resolves to
`10.10.34.36`, a private address that refuses the connection; a control host completed TLS in
0.39 s on the same machine. DNS-level interception, not a code fault. **The `.env` token was
never validated — the request never reached Telegram.** T15/T16 are committed and unit-tested
but have never exchanged a packet with Telegram. Gate `telegram-network-reachability`
(status `blocked`) carries the decision: add proxy support to `telegram_bridge.py`, or rely
on a system-wide VPN. Recommended: proxy support — every call goes through one
`UrllibTransport` class on stdlib urllib, so a `ProxyHandler` opener fed from a Settings
field covers the whole module.

## recommended_next

2. Owner review of the design pages written this run (app/categories-templates, clipboard-capture, asr-mode, telegram-bridge; platform/account-profile, plan-picker, mobile-capture-topics, website-landing) - post-hoc per the working agreement
3. Small follow-ups surfaced by qa: category-create double-submit guard, unsaved-rename discard, template_demo ignoring scientific-mode style, ASR device index 0 / Test-5-seconds using saved config, Unpair danger-ghost class; a sweep-sized batch
4. Telegram proxy support in telegram_bridge.py — the one thing standing between a
   finished, tested bridge and a bridge that works for the owner. Blocked on the owner
   choosing proxy-vs-VPN (gate telegram-network-reachability)
5. STAGE 1 — contract-first, now UNBLOCKED for the V1 targets: openapi.yaml (OpenAPI 3.1) +
   schema.dbml covering accounts/auth, the local-first op-log sync, and the dashboard read
   model. Per build-protocol.md §4 this is what lets backend, website and Android proceed as
   concurrent heads instead of a serial chain. Scope it to what the decided gates cover —
   NOT billing, NOT hosted-key issuance
6. T18 (accounts + auth on managed BaaS) and T24 (website: landing, auth, dashboard) after
   stage 1; T21 (Android, RN+Expo, APK distribution) after the contract exists
7. Terms + privacy draft (gate legal-text-terms-privacy) — agent drafts, owner accepts
8. STILL BLOCKED, do not build: T19 (billing) and T20 (hosted keys) pending
   business-decision-plans + billing-provider-account; T22 (iOS) and T23 (Linux) HELD by
   owner decision
