---
report: product-spec
project: Trailmark (formerly OpenPointLogger)
slice: platform-expansion
workstream: T17 (see .claude/PROJECT_STATE.md)
stage: 0 — product shape
generated: 2026-09-15
generated_by: product-cartographer
status: DRAFT — awaiting owner acceptance (gate G0.4 in .claude/gates/platform-expansion.yaml)
stage_1_contract: NOT WRITTEN — blocked on the open decisions in §9. No openapi.yaml, no schema.dbml.
schema_version: 1
---

# Trailmark — product spec for the platform expansion

## 0. How to read this file

- Everything in **§1–§4** is derived from what the app does today (README.md, TEMPLATES.md,
  `point_store.py`, `llm.py`, `point_logger.py`) and from the owner's stated backlog in
  `.claude/PROJECT_STATE.md`. Nothing there is invented.
- Everything in **§5–§7** is a **RECOMMENDATION**. It is labelled as such, carries alternatives,
  and is not a decision until the owner says so.
- **"not established"** means the material available does not decide it. It is a correct
  output, not a gap to be filled with a plausible default.
- Stage 1 (OpenAPI 3.1 + DBML) is deliberately **not** started. A contract built on an
  unaccepted surface matrix is worse than no contract. §9 lists exactly what unblocks it.
- Operation names in the surface tables come in two kinds:
  - `api.<name>` — a method that exists today on the pywebview bridge in `point_logger.py`.
  - `proposed:<ns>.<name>` — a name reserved for the stage-1 contract. **It resolves to
    nothing yet.** It is written down so every row has a claim to test at stage 1, not as
    evidence that anything exists.

---

## 1. Product statement

Trailmark is a research logger that stays out of the way: a global hotkey opens a small
always-on-top panel over whatever you are reading, you drop a point with its source (link,
string citation, or screenshot), and when the topic closes you export a numbered, cited report
(HTML, PDF, Markdown, DOCX, optionally LaTeX) through a template. Today it is a Windows tray
app, fully local, with no accounts, no cloud, no telemetry, and optional bring-your-own-key AI
assist. The expansion adds accounts, paid plans, sync across devices, mobile capture, a Telegram
capture channel, a Linux build and a website — without breaking the local-only tier.

---

## 2. User archetypes

Derived from features that exist in the code, not from a market study.

| # | Archetype | Evidence in the product today | Appears in V1 surfaces? |
|---|---|---|---|
| U1 | **Solo researcher / grad student** — reads papers and books, needs citations to be right | Scientific mode (`claim`/`note`/`quote` kinds in `point_store.py`), five citation styles and DOI lookup in `citation.py`, the Research Roam template with a LaTeX path | Yes — every desktop and mobile surface |
| U2 | **Knowledge worker writing reports** — reading the web, PDFs, interviews; wants a clean report fast | Personal Report and Protocol templates; the "Business Formal" and "Team Report" cards already named in the design prototype (PROJECT_STATE T9); author/org fields in export config | Yes — every desktop and mobile surface |
| U3 | **The same person, away from the desk** ("mobile-first capturer") — captures on a phone, reviews and exports later on the desktop | The owner's request for Android/iOS and a Telegram bot; the bot token already present in the untracked `.env` (PROJECT_STATE C1). This is U1/U2 in a second context, not a separate market | Yes — mobile app, Telegram bot, web capture inbox |
| U4 | **Small team sharing a topic** | **not established.** The only traces are the "Team Report" template card in the design prototype and the word "Plus" in the owner's plan list. No sharing, roles, or multi-user concept exists in the data model | **No V1 surface.** By the protocol's rule this is either a missing page or a fictional user: it is a *candidate* Plus-tier archetype awaiting the owner's decision (§9, `business-decision-plans`). Do not build a surface for it until then |
| — | Owner / operator (internal) | Nobody today: no backend, no users to support | A role on the website's bucket E (`/admin`), marked *later*. Listed as a role, not an archetype |

Anonymous visitor exists only on the website (bucket A/B) and on the mobile sign-in screen.

---

## 3. Capabilities today, bucketed

First-match-wins per `~/.claude/rules/build-protocol.md` §3, applied to the desktop app as it
is. The desktop is a single-user local tool, so buckets A, B and D largely collapse — that is
the "internal tool" row of the substitution table, and it is why the desktop inventory in §4.1
is written as surfaces, not routes.

| Bucket | Today | After expansion |
|---|---|---|
| A Acquisition | GitHub README, Releases page | Website landing (+ pricing section), download |
| B Identity | none (no accounts) | Sign in (web, desktop Settings, mobile), device pairing, Telegram chat pairing |
| C Core engine | Quick-capture popup; topics (open/closed); entries with sub-topics, kinds and sources; export pipeline; templates; BYO-key polish and summary | Same, plus: sync across devices; mobile capture; web capture inbox; Telegram capture; hosted AI polish quota (Pro, recommended) |
| D Account | Settings (hotkey, AI assist, exports, appearance, science) | Plus: account, plan, billing, devices |
| E System/legal | MIT LICENSE file, tray menu | Terms, privacy, 404/500, admin (later) |

### Data model today (input to stage 1)

`points.json`: `topics[] {id, title, status: open|closed, created, closed, subtopics[], entries[]}`
→ `entries[] {id, subtopic, text, kind: claim|note|quote, created, sources[]}`
→ `sources[] {id, type: link|string|image, value, note, meta?}` (meta = structured citation
fields, normalised by `citation.py`, absent when empty).
`config.json`: sections `hotkey`, `llm`, `export`, `appearance`, `science`. The `llm` section
holds one of five BYO providers (`PROVIDERS` in `point_store.py`: OpenRouter, OpenAI, Mistral,
AvalAI, Google AI Studio — the README lists four).
`attachments/`: screenshot files referenced by image sources.
`exports/<folder>/`: rendered files + `manifest.json` (the export index reads the folder).
State machine: topic `open ⇄ closed` (`close_topic` / `reopen_topic`). Entries and sources
have no state; they are created, edited (`update_entry`, `set_source_meta`, `rename_subtopic`)
and deleted. Every id is a uuid4 hex, which matters for sync: ids are already globally unique.

---

## 4. Surface inventory per platform

This is not a pure web application, so per build-protocol §3 the five web buckets are used for
the website only; desktop and mobile use a surface / screen inventory with the same
access-guard column. Access guards: **anon** (no identity), **local** (the machine's user,
no account required — the entire Free tier), **signed-in** (has an account), **paired-device**
(a device or chat bound to an account by a one-time code), **admin** (owner/operator).

Budget: ~10–12 V1 surfaces per platform. Counts are in §4.7.

### 4.1 Windows desktop — exists

| # | Surface | Guard | Primary goal | Operations behind it | Status |
|---|---|---|---|---|---|
| W1 | Quick-capture popup (global hotkey, always-on-top) | local | Log a point with source without leaving the source | `api.start_topic`, `api.add_entry`, `api.add_source`, `api.save_image`, `api.hide_popup`, `api.show_full` | exists |
| W2 | Full window — Open topics tab | local | Review and edit points, sub-topics, sources, kinds | `api.get_state`, `api.update_topic`, `api.add_subtopic`, `api.rename_subtopic`, `api.delete_subtopic`, `api.update_entry`, `api.delete_entry`, `api.add_source`, `api.set_source_meta`, `api.lookup_doi`, `api.delete_source`, `api.close_topic`, `api.polish_entry` | exists |
| W3 | Full window — Closed topics tab | local | Revisit, reopen, export, draft AI summary | `api.get_state`, `api.reopen_topic`, `api.delete_topic`, `api.draft_summary`, `api.export_topic` | exists |
| W4 | Export dialog (template + formats) | local | Produce the cited report | `api.list_templates`, `api.pdf_engines`, `api.export_topic`, `api.export_topic_polished` | exists |
| W5 | Full window — Exports tab (grouped per topic) | local | Find and open past exports | `api.get_state` (exports index), `api.open_path`, `api.delete_export` | exists (format-leak bug T4 pending) |
| W6 | Settings (hotkey, AI assist, exports, appearance, scientific mode) | local | Configure the app | `api.get_config`, `api.save_hotkey`, `api.save_llm`, `api.test_llm`, `api.save_export`, `api.save_appearance`, `api.save_science`, `api.open_template_dir`, `api.citation_styles` | exists |
| W7 | Tray icon + owner-drawn menu | local | Open / show popup / quit | `api.tray_action`, `api.hide_menu` | exists |
| W8 | Settings → Account (sign in, plan shown, sync on/off) | local → signed-in | Attach this install to an account; turn sync on | `proposed:auth.start`, `proposed:auth.callback`, `proposed:account.get`, `proposed:sync.push`, `proposed:sync.pull` | planned (T18) |
| W9 | Settings → Devices & channels (pairing code for mobile / Telegram; list and revoke devices) | signed-in | Pair a phone or a Telegram chat; revoke | `proposed:devices.create_pairing_code`, `proposed:devices.list`, `proposed:devices.revoke` | planned (T15/D4 for Telegram, T18 for devices) |
| W10 | Sync status indicator (sidebar chip: synced / pending / offline / signed-out) | local | Trust that a phone capture arrived | `proposed:sync.status` (client-side state, no new endpoint) | planned |
| — | Upgrade prompt when a Pro-only action is used while signed out / Free | local | Convert | `proposed:billing.checkout_url` | **later** — depends on `business-decision-plans` |
| — | Category/template management, clipboard capture, ASR mode, Telegram pairing UI | local | (existing backlog D1–D4, T5–T16) | — | out of scope for this spec; tracked in PROJECT_STATE |

Windows V1 count: 10 (7 exist + 3 planned).

### 4.2 Linux desktop — planned port (T23)

Same ten surfaces as §4.1, same guards, same operations. What the port changes is beneath the
surfaces, and each item below is a technical decision that stage 1 does not need but T23 does:

| Concern | Windows today | Linux | Status |
|---|---|---|---|
| Window/webview | pywebview on WebView2 | pywebview GTK (WebKitGTK) or Qt backend | planned |
| Global hotkey (W1) | Win32 `RegisterHotKey` in `hotkey.py` | X11: needs a new listener (e.g. python-xlib / pynput). **Wayland: global hotkeys are not generally available to apps; approach not established** | not established |
| Tray (W7) | owner-drawn Win32 menu in `traymenu.py` | AppIndicator/StatusNotifier, or drop the tray and rely on the hotkey + launcher | not established |
| Single instance | Win32 named event in `single.py` | lock file / D-Bus | planned |
| PDF engine (W4) | headless Edge (ships with Windows) | Chromium/Chrome or WeasyPrint, both already detected in `pdf_render.py`; Edge branch is n/a | planned |
| Data dir | `%APPDATA%` Trailmark folder | XDG data home | planned |
| Packaging | PyInstaller one-file `.exe` | AppImage / .deb / Flatpak — **not established** | not established |

Linux V1 count: 10 (same inventory; no new surfaces).

### 4.3 Android — planned (T21)

Screens by navigation stack. Export does **not** exist on mobile in V1: the export pipeline is
desktop Python (`pipeline.py`, `pdf_render.py`, `docx_writer.py`), and whether it ever runs
server-side is an open decision (§9, D-8).

| # | Screen / stack | Guard | Primary goal | Operations behind it | Status |
|---|---|---|---|---|---|
| M1 | Sign-in / pair (root stack, shown when signed out) | anon → signed-in | Enter the account: magic link, or a pairing code from desktop W9 | `proposed:auth.start`, `proposed:auth.callback`, `proposed:devices.pair` | planned |
| M2 | **Capture** (home tab) — text, link, photo/screenshot; active topic chip; sub-topic chip; kind toggle (claim/note/quote, shown only if scientific mode is on) | signed-in | Log a point in under ten seconds, offline-safe | `proposed:sync.push` (queued locally when offline), `proposed:attachments.upload_url` | planned |
| M3 | **Topics** tab — open / closed list | signed-in | Pick or start the active topic | `proposed:sync.pull`, `proposed:sync.push` (start topic) | planned |
| M4 | **Topic detail** (pushed from M3) — entries grouped by sub-topic, sources, edit text, delete | signed-in | Review what was captured; light editing | `proposed:sync.push` (update/delete ops), `proposed:sync.pull` | planned |
| M5 | **Settings / Account** tab — plan, this device, other devices, theme, sign out | signed-in | Manage the account from the phone | `proposed:account.get`, `proposed:devices.list`, `proposed:devices.revoke`, `proposed:billing.portal_url` | planned |
| M6 | **Share-sheet target** (system share → Capture prefilled with URL / text / image) | signed-in | Capture from the browser or any app with two taps | same as M2 | planned |
| — | Export from phone | signed-in | — | — | **later** — depends on D-8 (server-side export) |
| — | Polish on phone (hosted AI quota) | signed-in (Pro, recommended) | — | `proposed:ai.polish` (async) | **later** — depends on `business-decision-plans` and `business-decision-hosted-provider` |
| — | Structured citation editing (author/year/DOI) | signed-in | — | — | later |
| — | Home-screen widget / quick tile | signed-in | — | — | later |

Android V1 count: 6.

### 4.4 iOS — planned (T22)

Identical inventory to §4.3 (M1–M6), same guards and operations, built from the same codebase
if the recommendation in §7 is accepted. Platform differences that do not add surfaces:

- M6 share target is an iOS Share Extension (a separate process with its own storage
  entitlement; the capture must be queued to an app-group container and pushed on next launch
  if the extension cannot reach the network).
- Payments: an iOS app that sells the Pro plan inside the app is subject to App Store
  in-app-purchase rules. Whether Trailmark sells on the web only (and the app just shows the
  plan) or also through IAP is **not established** (§9, D-9).

iOS V1 count: 6.

### 4.5 Website — planned (T24), five buckets

Access tags follow gate G0.3: **Public**, **Guest-Only** (signed-in users are redirected
away), **Authenticated(user)**, **Authenticated(admin)**.

| # | Route | Bucket | Access | Primary goal | Operations behind it | Primary components | Status |
|---|---|---|---|---|---|---|---|
| S1 | `/` | A | Public | Explain the product, download desktop, show plans (pricing is a section, `/#pricing`, in V1) | none (static); download links to GitHub Releases | hero, feature grid, screenshots, plan cards, download CTA, footer | planned |
| S2 | `/login` | B | Guest-Only | Sign in **or** create the account (one page; passwordless magic link recommended — §9 D-6) | `proposed:auth.start` | email form, "check your inbox" state | planned |
| S3 | `/auth/callback` | B | Public (transient) | Complete the magic link / OAuth return, set session, redirect | `proposed:auth.callback` | spinner, error state | planned |
| S4 | `/pair` | B | Authenticated(user) | Bind a phone or Telegram chat by entering the code shown on desktop W9 (also reachable by deep link from the mobile app) | `proposed:devices.pair` | code entry, confirmation | planned |
| S5 | `/capture` | C | Authenticated(user) | Web capture inbox: add a point (text / link / image) to the active topic from any browser, including phones without the app | `proposed:sync.push`, `proposed:attachments.upload_url` | capture form, topic chip, recent-captures list | planned |
| S6 | `/topics` | C | Authenticated(user) | Read-only list of open and closed topics with their entries expandable inline | `proposed:sync.pull` | topic list, entry list, source pills | planned |
| S7 | `/settings` | D | Authenticated(user) | Profile (email, display name), devices & channels (list / revoke), sign out, delete account | `proposed:account.get`, `proposed:account.update`, `proposed:account.delete`, `proposed:devices.list`, `proposed:devices.revoke` | profile form, device table | planned |
| S8 | `/settings/billing` | D | Authenticated(user) | See plan, upgrade to Pro, manage/cancel through the provider's portal | `proposed:billing.checkout_url`, `proposed:billing.portal_url` (provider webhooks are `proposed:billing.webhook`, async) | plan card, upgrade button, portal link | planned — blocked on T19 (provider account) |
| S9 | `/terms` | E | Public | Terms of service | none | document | planned — **text not established**; needs the owner or counsel |
| S10 | `/privacy` | E | Public | Privacy policy — must describe exactly what leaves the device per tier | none | document | planned — **text not established** |
| S11 | 404 | E | Public | Not found | none | error layout | planned |
| S12 | 500 | E | Public | Server error | none | error layout | planned |
| — | `/pricing` as its own route | A | Public | SEO-able pricing page | none | — | **later** (V1 uses `/#pricing`; owner may overrule at G0.4) |
| — | `/docs` | A | Public | Templates and workflow docs | none | — | **later** — README.md and TEMPLATES.md on GitHub serve this today |
| — | `/topics/[id]` | C | Authenticated(user) | Full topic page on the web | `proposed:sync.pull` | — | later (S6 expands inline) |
| — | `/settings/team` | D | Authenticated(user) | Team sharing | — | — | **later / Plus** — depends on `business-decision-plans`; archetype U4 not established |
| — | `/admin` | E | Authenticated(admin) | Users, plans, quotas, support | `proposed:admin.*` | — | later — nothing to administer until accounts exist |
| — | `/reset-password`, `/signup`, `/verify` | B | Guest-Only | Password-auth surfaces | — | — | **n/a if passwordless auth is chosen** (§9 D-6); otherwise V1 grows to 15 and the owner must accept the overrun |

Website V1 count: 12.

**Primary nav / footer (G0.2 — zero orphans):**

```
header (signed out): / · /#pricing · Download (→ GitHub Releases) · /login
header (signed in):  /capture · /topics · /settings · /settings/billing · sign out
footer (all):        / · /#pricing · /terms · /privacy · GitHub
transient / reached by flow only: /auth/callback (from the email link), /pair (from /settings
  "add a device" and from the mobile app deep link), 404, 500 (error handlers)
```

Every V1 route above is reachable from that tree or is an error/transient page reached by the
flow that owns it. No orphans.

### 4.6 Telegram bot — planned (D4, T15, T16)

Status of the material: a bot token sits in the untracked `.env` (never printed here); **no
Telegram code exists in the repo** (a grep for `telegram` across the Python files returns
nothing). The current plan in PROJECT_STATE is a **desktop-hosted long-polling client, paired
chat only**, which needs no backend and fits the Free tier. Once accounts exist, the same bot
could be hosted server-side and become a capture channel like the mobile app — that fork is
decision D-7 in §9. The inventory below is written for the desktop-hosted V1 and is unchanged
in shape if hosting moves.

| # | Surface (command / message type) | Guard | Primary goal | Operations behind it | Status |
|---|---|---|---|---|---|
| T1 | `/start <code>` — pair this chat using the code from desktop W9 | anon → paired-device | One-time pairing; every other command is refused until paired | `proposed:devices.pair` (desktop-hosted: local pairing record in `config.json`) | planned |
| T2 | Plain text message → point (claim) on the active topic | paired-device | Capture a thought | `api.add_entry` (desktop-hosted) / `proposed:sync.push` (server-hosted) | planned |
| T3 | Message containing a URL → point with a **link** source (text before the URL becomes the point; a URL alone — **not established**, needs D4 design) | paired-device | Capture a source fast | `api.add_entry` with `source_link` | planned |
| T4 | Photo message → point with an **image** source; caption becomes the text | paired-device | Capture a screenshot from the phone | `api.add_entry` with `image_data` / `api.save_image` | planned |
| T5 | `/topic` — list open topics; `/topic <name>` — switch or start | paired-device | Pick where captures land | `api.get_state`, `api.start_topic` | planned |
| T6 | `/status` — active topic, last capture, desktop reachable? | paired-device | Trust the channel | `api.get_state` | planned |
| T7 | `/unpair` | paired-device | Revoke this chat | `proposed:devices.revoke` | planned |
| — | Voice message → ASR → point | paired-device | — | — | **later** — depends on T12–T14 and `business-decision-hosted-provider` |
| — | Group chats / multiple paired users | — | — | — | **n/a in V1** — single paired chat, single user (archetype U4 not established) |

Telegram V1 count: 7. Note for D4: while the desktop hosts the bot, a message sent while the
desktop is off is delivered on the next long-poll after the desktop starts, but only within
Telegram's update-retention window; the exact window is not established here and must be
checked against the Bot API documentation when T15 is built.

### 4.7 Counts against the budget (G0.1)

| Platform | Exists | Planned V1 | V1 total | Later / n/a |
|---|---|---|---|---|
| Windows desktop | 7 | 3 | **10** | 1 later, existing backlog out of scope |
| Linux desktop | 0 | 10 (port) | **10** | — |
| Android | 0 | 6 | **6** | 4 later |
| iOS | 0 | 6 | **6** | 4 later |
| Website | 0 | 12 | **12** | 5 later, 3 n/a-if-passwordless |
| Telegram bot | 0 | 7 | **7** | 1 later, 1 n/a |

Method: hand count of the rows marked `exists` or `planned` in §4.1–§4.6. No script was run.
What was cut to stay inside 12 on the website, so the owner can overrule at G0.4:
`/pricing` (folded into `/#pricing`), `/docs` (GitHub serves it), `/topics/[id]` (S6 expands
inline), `/signup`+`/reset-password`+`/verify` (removed by the passwordless recommendation),
`/admin` and `/settings/team` (nothing to administer or share yet).

---

## 5. Plans

### 5.1 As stated by the owner

Three tiers: **Free**, **Pro at $5**, **Plus "coming soon"**. That is the entire established
fact. **Not established:** the billing period of the $5 (this document *assumes* monthly and
says so wherever it matters), what Pro contains, what Plus contains, any quota, any provider
deal, any user count, any regional pricing, the billing provider (T19).

### 5.2 RECOMMENDED split — awaiting owner decision (`business-decision-plans`)

| Tier | Contains | Why here |
|---|---|---|
| **Free** | Everything the desktop does today, forever local: capture, topics, sub-topics, scientific mode, templates, all export formats, BYO-key AI assist, desktop-hosted Telegram bot. **No account required.** Linux build included | Keeps the README's "No accounts. No cloud." literally true for the people it was written for, and keeps the open-source promise (MIT) meaningful. The BYO-key user costs the owner nothing |
| **Pro — $5 (per month, assumed)** | Account + sync across devices; Android and iOS apps; web capture inbox; **hosted AI polish / summary quota** for people who do not want to bring a key (cap: not established) | Everything in Pro costs the owner money to run (hosting, storage, inference) — the tier boundary sits exactly on the cost boundary, which makes it easy to explain and to defend |
| **Plus — coming soon** | Hosted ASR (auto-transcription mode T12–T14, voice messages on Telegram); team sharing of a topic (archetype U4) | ASR is the most expensive inference the product would run and team sharing is the only feature that needs a multi-user data model — both belong in a tier that can wait until Pro proves demand |

### 5.3 Alternatives the owner may prefer

- **A1 — Sync is the only paid thing.** Pro = accounts + sync + mobile; hosted AI moves to Plus.
  Cheaper to run, simpler to promise; loses the "I don't want to manage API keys" argument for
  Pro.
- **A2 — Mobile apps are free with an account; sync is what you pay for.** Grows the installed
  base faster; but an account with no sync has nothing to show on the phone, so "free mobile"
  is really "free trial of sync".
- **A3 — One-time desktop purchase + subscription for cloud.** Fits a local-first tool and the
  users who distrust subscriptions; conflicts with the MIT source being freely buildable
  unless the purchase buys signed binaries and support rather than the code.
- **A4 — Team sharing in Pro, not Plus.** Only if U4 turns out to be real. Not recommended
  before there is evidence of a team user.

---

## 6. Sync / accounts architecture — three options, one recommendation

Starting point: zero backend. Data is JSON on disk with globally unique ids, screenshots are
files, exports are regenerable artefacts. Whatever is chosen has to (a) leave the Free tier
working with no server at all, (b) survive a phone being offline for a day, and (c) be run by
one Python developer who also ships the desktop app.

| | Option A — managed BaaS (e.g. Supabase: Postgres + auth + storage + row-level security) | Option B — self-hosted modular monolith (FastAPI + Postgres + S3-compatible storage) | Option C — local-first sync (per-device append-only op log, merged on a thin server) |
|---|---|---|---|
| What the owner writes | Schema + RLS policies, a small amount of server code (edge functions or one small FastAPI) for billing webhooks and hosted AI | Everything: auth, sessions, email, storage, backups, billing, AI proxy, ops | The op-log format, merge rules, and a thin server — the server still needs *hosting*, so C is really a **data model**, not a hosting choice |
| Fits one Python dev | Yes — auth, email, storage and backups are somebody else's pager | Only with real ops time budgeted (stage 8 becomes a standing cost) | Yes for the model; hosting still has to be A or B |
| Fits the local-first product | Partly — clients must still keep a local store and queue | Same | Best — the desktop keeps `points.json` as the source of truth and syncs a log |
| Offline mobile capture | Client-side queue required either way | Same | Native to the model |
| Lock-in / exit | Postgres underneath; export is a `pg_dump`; auth users are exportable | None | None |
| Risk | Vendor pricing changes; RLS mistakes are IDOR | Solo dev running production auth and email | Merge rules for edits/deletes must be designed carefully (LWW with tombstones is enough for this data) |

**RECOMMENDATION (`business-decision-sync-backend`): Option A for hosting, with Option C's
data model on top.** In three lines:

1. The cost of Pro is dominated by *operating* accounts, not by writing them; a managed
   Postgres + auth + storage removes the ops burden that would otherwise land on the one
   person who also maintains a Win32 tray app.
2. The data is already shaped for a log: every topic/entry/source has a uuid, entries are
   append-mostly, and edits/deletes are rare — a per-device op log with last-writer-wins and
   tombstones merges cleanly and keeps the desktop's local JSON as the source of truth, so
   the Free tier is untouched.
3. Postgres underneath means the exit to Option B later is a `pg_dump` and a FastAPI, not a
   rewrite.

Sync/async boundary for the operations named in §4 (input to gate G1.4 later):
- `sync.push`, `sync.pull`, `devices.*`, `account.*`, `auth.*` — single DB round trips → **sync**.
- `attachments.upload_url` — issue a signed URL (sync); the upload itself goes client → storage.
- `ai.polish`, `ai.summary` — LLM call → **enqueued**, result polled or pushed.
- `billing.webhook` — external webhook → **enqueued**, idempotent on the provider's event id.
- DOI lookup stays client-side as today (`api.lookup_doi`) — it is an external call and does
  not need to touch the account backend.

What is **not established** and must be decided before stage 1: hosting region / data residency;
whether attachments are synced at all in V1 or only text (a screenshot-heavy user changes the
storage bill); whether exports are synced (recommendation: **no**, they are regenerable); the
retention of a deleted account's data.

---

## 7. Mobile framework — options and a recommendation

Constraints: one Python developer; the web/desktop design system is plain tokenised HTML/CSS
(commit `301e61e`); the mobile V1 is six screens plus a share-sheet target; the mobile app
never renders a report in V1.

| | React Native + Expo | Flutter | Native (Kotlin + Swift) | Python-based (Flet / BeeWare / Kivy) |
|---|---|---|---|---|
| Codebases for Android + iOS | 1 | 1 | 2 | 1 |
| New language for a Python dev | TypeScript | Dart | Two | None |
| Reuse of the tokenised design system | Tokens port as constants; the mental model (flexbox, CSS-like styles) carries over; the website can share the same token file | Tokens must be re-expressed in Dart; no HTML/CSS reuse | Re-expressed twice | Partial |
| Share-sheet target (M6) | Supported via config plugins; iOS Share Extension needs a native module but is well-trodden | Supported via plugins | First-class | Weak / not established |
| Store builds, signing, updates | Expo EAS does the signing and store submission — the single biggest time sink for a solo dev | Manual per platform | Manual per platform | Manual, immature |
| Risk | Native-module edges (share extension) and upgrade churn | Learning Dart; the web design system is not reusable | Cost | App-store polish and OS integration are the product, and this is the weakest at exactly that |

**RECOMMENDATION (`mobile-framework-choice`): React Native with Expo.** One codebase, the
closest language to the existing HTML/CSS design system so tokens are shared rather than
translated, and EAS removes the signing/submission chore that otherwise eats a solo developer's
weeks. Flutter is the credible alternative if the owner would rather learn one strongly-typed
toolchain than TypeScript; native is not recommended at this team size.

**Staging alternative worth a decision (§9, D-10):** ship the website's `/capture` page (S5) as
an installable PWA first. On Android an installed PWA can register as a share target, which
delivers M2 + M6 to Android users with zero mobile code; iOS does not support share targets for
PWAs, so this is a bridge, not a substitute.

---

## 8. One end-to-end flow

Anonymous visitor → signup → install desktop → pair mobile → capture from phone → point
appears on desktop → export.

| Step | Surface | Guard transition | Operation(s) | What the user sees |
|---|---|---|---|---|
| 1 | Website `/` (S1) | anon | none | Landing, "Download for Windows", plans section |
| 2 | Downloads `Trailmark.exe` from GitHub Releases; installs; presses the hotkey; logs a first point (W1) | local | `api.start_topic`, `api.add_entry` | Works with no account — this is the Free tier and the whole first-run experience is unchanged |
| 3 | Desktop Settings → Account (W8) "Sign in / create account" | local → signed-in | `proposed:auth.start` → email → `/auth/callback` (S3) → `proposed:auth.callback` → desktop receives the session (loopback listener or custom URI scheme — decided at stage 1) | Account exists; sync toggle appears; upgrade prompt to Pro if sync is Pro-only (per §5) |
| 4 | Upgrade at `/settings/billing` (S8) | signed-in (Free → Pro) | `proposed:billing.checkout_url` → provider → `proposed:billing.webhook` (async) → plan updated | Plan card shows Pro |
| 5 | Desktop W8 sync on → first push | signed-in | `proposed:sync.push` (initial upload of the local log), `proposed:attachments.upload_url` per screenshot | Sync chip (W10) shows *synced* |
| 6 | Desktop W9 "Add a device" shows a pairing code | signed-in | `proposed:devices.create_pairing_code` | Short code with an expiry |
| 7 | Phone installs the app; M1 enters the code (or `/pair` S4 on the web) | anon → paired-device | `proposed:devices.pair`, then `proposed:sync.pull` | Topics appear on the phone |
| 8 | Phone: reading an article in the browser → share → Trailmark (M6) → Capture (M2) prefilled with the URL; type the point; save | paired-device | local queue → `proposed:sync.push` | Saved instantly; syncs when online |
| 9 | Desktop pulls | signed-in | `proposed:sync.pull` (poll on show / periodic; realtime channel optional at stage 1) | The point is in the open topic on the desktop; W10 briefly shows *pending → synced* |
| 10 | Desktop closes the topic and exports (W3 → W4) | local | `api.close_topic`, `api.export_topic` (or `api.export_topic_polished`, using either a BYO key or — Pro — `proposed:ai.polish` async) | HTML/PDF/Markdown/DOCX with the phone capture cited as `[n]` |

Where the flow is **not established**: step 3's session hand-off into a pywebview desktop app
(loopback HTTP listener vs custom URI scheme); whether step 4 is required before step 5
(depends on `business-decision-plans`); how step 9 is triggered (poll vs realtime).

---

## 9. Open decisions — everything that blocks stage 1

Each line: id · question · **recommended answer** · gate in `.claude/gates/platform-expansion.yaml`.

| id | Question for the owner | Recommended answer (one line) | Gate |
|---|---|---|---|
| D-1 | What is in Free, Pro ($5) and Plus? Is $5 per month? Any quota for hosted AI? | The split in §5.2: Free = today's desktop + BYO keys; Pro = accounts, sync, mobile, web inbox, hosted polish quota; Plus = hosted ASR + team sharing. Period and quota: owner must state | `business-decision-plans` |
| D-2 | Which LLM provider backs hosted polish/summary for non-BYO users, and at what cap? | Reuse the app's shipped default (OpenRouter, `deepseek/deepseek-v4-flash`, the `PROVIDERS` default in `point_store.py`) behind a server-held key; cap not established — owner sets it from the provider's per-token price | `business-decision-hosted-provider` |
| D-3 | Which ASR provider for Plus / auto-transcription? | Not established — no ASR code exists (T12–T14 pending); decide with D3's design, not now | `business-decision-hosted-provider` |
| D-4 | Managed BaaS, self-hosted monolith, or local-first sync? | Supabase (or equivalent managed Postgres + auth + storage) for hosting, per-device op log with LWW + tombstones as the sync model (§6) | `business-decision-sync-backend` |
| D-5 | React Native/Expo, Flutter, or native for Android + iOS? | React Native + Expo (§7); one decision for both apps | `mobile-framework-choice` |
| D-6 | Passwordless (magic link) or password auth? | Passwordless — removes `/signup`, `/reset-password`, `/verify` from the website and keeps V1 at 12 routes | `G0.4` (changes the matrix) |
| D-7 | Telegram bot: keep desktop-hosted (current plan, Free) or move server-side once accounts exist? | Desktop-hosted for V1 (no backend, ships with T15/T16); revisit as a server-hosted Pro channel after sync exists | `G0.4` (changes §4.6 guards) |
| D-8 | Will export ever run server-side (so phones can export)? | Not in V1; export stays desktop-only, which is why the mobile screens have no export | `G0.4` |
| D-9 | Does iOS sell Pro via in-app purchase, or web-only? | Web-only checkout in V1; the iOS app displays the plan and links out where policy allows — confirm against current App Store rules before T22 | `business-decision-plans` |
| D-10 | Ship `/capture` as an installable PWA before native mobile? | Yes as a bridge for Android (share target works); not a substitute for M1–M6 | `mobile-framework-choice` |
| D-11 | Do Free users ever need an account (e.g. for the Telegram bot or Linux build)? | No — Free stays account-free so the README's privacy claim stays true; an account only appears with Pro | `business-decision-plans` |
| D-12 | Accept the surface inventory in §4 (counts in §4.7, cuts listed there)? | Accept as V1; overrule any cut by naming it | `G0.4` |
| D-13 | Design pages for W8–W10, M1–M6, S1–S12, T1–T7 in the Claude Design project | After G0.4, before any implementation, per the owner's design-first rule | `G2.5` |
| D-14 | Terms and privacy text (S9, S10) | Not established — the owner or counsel writes them; the privacy text must enumerate exactly what leaves the device per tier | `G0.4` (content); no separate gate exists |
| D-15 | Billing provider account and keys (T19) | Not established — only the owner can create it; stage 1 can still define `billing.*` against a provider-agnostic shape | no gate id in the file — recommend the lead add one |
| D-16 | Attachments and exports in sync scope | Text + attachments synced, exports not synced (regenerable) | `business-decision-sync-backend` |

**Stage 1 can start when D-1, D-4, D-5, D-6, D-12 are answered.** D-2/D-3 can trail (they
affect one async operation and a quota field). D-7, D-8, D-9, D-10, D-11, D-16 shape the
contract's scope and should be answered in the same sitting. D-13 (G2.5) gates implementation,
not the contract. D-14/D-15 gate go-live, not the contract.

---

## 10. Gate self-assessment for stage 0

Recorded here because, per the dispatch, only this file and the platform-expansion gate file
were to be written; no separate `budget-bootstrap` gate file was created under `.claude/gates/`
(that file does not exist).

| Gate | Status | Evidence |
|---|---|---|
| G0.1 mvp_page_count ≤ 10–12 | measured by hand count | §4.7: Windows 10, Linux 10, Android 6, iOS 6, Website 12, Telegram 7. No script; counted rows |
| G0.2 orphan_routes = 0 | measured by inspection | §4.5 nav/footer tree covers every V1 website route; desktop/mobile/bot surfaces are reachable from their tab bars or commands as listed. Not script-verified |
| G0.3 route_authorization_parity 100% | measured by inspection | Every row in §4.1–§4.6 carries a guard column value; §4.5 uses the Public / Guest-Only / Authenticated(role) vocabulary |
| G0.4 product_breakdown_accepted | **unmeasured — human** | Awaiting the owner. Raised in `.claude/gates/platform-expansion.yaml` |
| G1.1–G1.4 | not started | Blocked on §9 |

---

## 11. Not established — the complete list

Billing period of the $5 · contents of Pro and Plus · hosted AI quota and cap · hosted LLM and
ASR providers · billing provider · sync backend and hosting region · whether attachments and
exports sync · account data retention on deletion · mobile framework · in-app purchase on iOS ·
passwordless vs password auth · desktop session hand-off mechanism · poll vs realtime sync ·
Telegram hosting after accounts exist · Telegram URL-only message mapping · Telegram update
retention window · Linux hotkey approach on Wayland · Linux tray approach · Linux packaging
format · terms and privacy text · whether a team user (U4) exists at all · any user count,
revenue, provider deal, or pricing beyond "$5".
