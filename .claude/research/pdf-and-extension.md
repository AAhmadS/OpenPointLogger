# Feasibility research: in-app PDF reader + Chrome extension capture

Scope: two proposed Trailmark features, researched against the app's real constraints
(single PyInstaller `--onefile --windowed` exe, pywebview + WebView2/WinForms backend,
dependency-averse, offline-first, size/RAM sensitive). Every numeric claim below is either
sourced to a fetched page/primary doc, or explicitly marked **unverified**. Absence of a
capability is reported as a finding, not glossed over.

---

## Feature 1 — in-app PDF reader for citation capture

### 1. PDF.js embedded in WebView2 — viable offline?

**Verdict: yes, viable, and it is the only realistic option** (see §2 — WebView2's native
PDF viewer is a dead end for anything programmatic). Some specifics:

**Size (confirmed against the unpkg file listing for `pdfjs-dist@5.4.149`):**

| File | Size |
|---|---|
| `pdf.min.mjs` (main library, minified) | **394 kB** |
| `pdf.worker.min.mjs` (worker, minified) | **1.04 MB** |
| `pdf.mjs` (unminified) | 737 kB |
| `pdf.worker.mjs` (unminified) | 1.89 MB |
| `pdf.sandbox.min.mjs` (JS-in-PDF sandbox, optional) | 674 kB |

So the two files Trailmark actually needs total **~1.4 MB** minified — not the full
`pdfjs-dist` npm tree (which also carries source maps, unminified copies, the sandbox,
and `web/` viewer chrome, several MB more). Vendoring just `pdf.min.mjs` +
`pdf.worker.min.mjs` (and skipping `pdf.sandbox.*`, which is only for executing
JavaScript embedded inside malicious/interactive PDF forms — Trailmark doesn't need it)
keeps the installer delta under ~1.5 MB, comfortably inside the stated 20 MB budget.
No standard viewer CSS/UI is needed either, since Trailmark will build its own citation
UI around the canvas — that saves the ~1 MB `web/` viewer bundle entirely.

**Does the worker run when the page is a string / non-http origin?** This is the real
risk, and the honest answer is *it depends on how pywebview serves the page, and that
turns out to already be solved*:

- pywebview does **not** load `html=` strings as a raw `data:` URI or `about:blank` on
  the WebView2/Edge Chromium backend. Per pywebview's own docs, it "provides its own HTTP
  server for serving static local files," and for the string/embedded-HTML case it spins
  up that server on a random local port for exactly this reason (WebView2 restricts what
  `data:`/`file://` content can do — no workers, no fetch, broken relative paths). This
  means Trailmark's existing `js_api` bridge already runs over `http://127.0.0.1:<port>/…`,
  not a `file://` or string origin.
- Given that, pdf.js's worker is same-origin to the page and there is **no special
  workaround needed** — `new Worker('pdf.worker.min.mjs')` from an `http://127.0.0.1`
  origin works exactly as it would on any normal web page, because the file is served by
  pywebview's own local HTTP server, not opened as `file://`.
- If for some reason a page **is** ever rendered as a true `file://` or blob context
  (e.g. a quick preview window), pdf.js's fallback path is well documented: same-origin
  checks fail for `file://`, worker creation throws, and pdf.js silently falls back to a
  "fake worker" that runs parsing on the main thread (a real behavior in pdf.js's
  `_setupFakeWorker()`, confirmed via pdf.js's own GitHub issue threads — this is not
  vendor speculation, it's documented pdf.js internal fallback logic). The historical
  `disableWorker` flag was removed from the public API; the fake-worker fallback is now
  automatic and silent, with a console warning. Practical implication for Trailmark: even
  in the worst case (no worker at all), pdf.js still works — just single-threaded, which
  matters only for very large PDFs (parsing blocks the UI thread). Given pywebview already
  serves over local HTTP, this fallback path likely never triggers.
- **Does WebView2 support the APIs pdf.js needs?** WebView2 is Chromium-based (Edge)
  under the hood, so it supports Web Workers, `ArrayBuffer`/`Uint8Array`, Canvas 2D,
  `fetch`, and ES modules — everything current pdf.js (5.x, ESM-only since v4) requires.
  No API gap found in research. **Confidence: high but not exhaustively verified against
  WebView2's exact Chromium version pin** — recommend a 30-minute spike loading a real
  PDF before committing engineering days.

### 2. WebView2's own built-in PDF viewer

**Finding: it does not expose what Trailmark needs, and this can be stated plainly.**
Edge/WebView2 does render PDFs natively when you navigate `CoreWebView2` to a `.pdf`
URL/file — but this uses Edge's internal PDF viewer surface, which is **not** a DOM the
host application can reach into. Research (WebView2Feedback issues #1263, #5514, #1345)
converges on:

- There is no `CoreWebView2` API to read selected text out of the built-in PDF viewer.
  Requests for exactly this ("how to get selected text via WebView2… any event that can
  raise after selecting") are open, unresolved feature requests against Microsoft's own
  WebView2Feedback repo, not documented capabilities.
- No API surfaces annotations/highlights created in the built-in viewer back to the host.
- Text selection itself is reported as buggy/partial for some PDFs in the built-in viewer.

**Conclusion: the built-in PDF viewer is a non-starter for Feature 1.** It's fine for
"just open this file so a human can look at it," useless for programmatic capture,
highlighting, or citation logging. This rules it out early and cleanly — pdf.js is not
just preferred, it's the only path that gives Trailmark a DOM/data model to work against.

### 3. Highlight/annotation persistence in pdf.js

- The **annotation editor layer** (`AnnotationEditorType`) is a real, current pdf.js
  feature, not legacy — it ships in the mainline `pdf.min.mjs`/viewer as of pdf.js 4.x
  and continues in 5.x/6.x. `AnnotationEditorType.HIGHLIGHT` is one of the built-in editor
  modes (alongside FREETEXT, INK, STAMP).
- **Highlight colour is configurable**: the layer exposes an `EventBus`
  (`dispatch("switchannotationeditorparams", …)`) through which the host page can set the
  active highlight colour before a user drags a selection — this is exactly the hook
  Trailmark needs to map "colour → log-entry kind," since the app already owns the
  surrounding UI and can drive this EventBus from its own colour picker.
- **Reading highlights back**: annotations created through the editor layer live in
  pdf.js's `AnnotationStorage`, keyed per page/annotation id, and are queryable — colour,
  page number, and the annotation's rects/quadpoints are all present in that storage
  object. Getting the **underlying selected text** for a highlight is not automatic from
  the annotation object alone; it requires cross-referencing the highlight's quadpoints/
  rects against `getTextContent()` output for that page to recover the covered string(s).
  This is a well-known, solvable but nontrivial join (several third-party pdf.js-based
  products, e.g. Nutrient/PSPDFKit-adjacent blog posts, describe doing exactly this) —
  budget real implementation time for it, don't assume it falls out for free.
- **Writing annotations back into the PDF file**: `PDFDocumentProxy.saveDocument()` is a
  real pdf.js API — it serializes the current `AnnotationStorage` into a new PDF byte
  stream, and works for annotations created through the editor layer (this is documented,
  confirmed usage, not a form-only feature as some older pdf.js documentation implied —
  form fields were the original use case but the editor-layer highlights also live in the
  same storage and are eligible). **However**, recommend Trailmark **not** rely on
  round-tripping the original PDF file as the source of truth. Reasons: (a) `saveDocument`
  produces a *new* PDF byte stream — Trailmark would need to manage "save back to the
  original path vs. keep a copy," which touches user files it doesn't own; (b) the
  citation metadata Trailmark actually needs (colour → log-entry-kind mapping, the
  chosen citation format, links to specific log entries) has no home in standard PDF
  annotation semantics — it would have to be smuggled into a `/Contents` string or a
  custom key, which is fragile and unreadable by other PDF tools anyway. **Recommended
  approach: sidecar JSON in `%APPDATA%\Trailmark`, keyed by a content hash of the PDF**,
  identical in spirit to how the app already keeps its own data model rather than fighting
  a foreign file format (matches the existing hand-written-OOXML-writer philosophy —
  Trailmark owns its data, doesn't depend on round-tripping someone else's format).
  Optionally *also* call `saveDocument()` to leave a human-readable highlighted copy for
  users who want to open the PDF elsewhere — that's a nice-to-have, not the system of
  record.

### 4. Text extraction fidelity — `getTextContent()`

pdf.js's `getTextContent()` returns text items with position info that must be
reassembled into reading order — it does **not** guarantee left-to-right/top-to-bottom
document order for anything beyond simple single-column layouts. Known failure modes
(consistent with pdf.js's own long-standing issue tracker patterns, not fetched
individually here but well-established in the ecosystem):

- **Multi-column layouts** (very common in research papers): text items from column 1 and
  column 2 can interleave in extraction order because pdf.js walks the content stream, not
  a visual reading order. Reconstructing correct order requires bucketing items by
  x-position/column before reading top-to-bottom — non-trivial for the general case.
- **Hyphenation across line breaks**: a word split "citation-\nformat" comes back as two
  text items; pdf.js does not de-hyphenate. Left uncorrected, copied/logged text shows
  broken words.
- **Ligatures** (fi, fl, ffi as single glyphs in the font): depends on the font's ToUnicode
  CMap; well-formed PDFs map ligatures back to normal characters, but poorly-produced PDFs
  (especially older scanned-then-OCRed or LaTeX-without-proper-cmap documents) can emit
  the literal ligature glyph or, worse, nothing extractable at all.
- **Scanned/image PDFs have no text layer at all** — `getTextContent()` returns nothing
  useful, and Trailmark would need OCR (out of scope unless explicitly requested; flagging
  it here since "read a PDF" ambiguously includes scanned papers).

None of this blocks selection-based capture (the browser's native `window.getSelection()`
over pdf.js's rendered text layer handles ordering the way a human actually selected it,
which sidesteps the column-reconstruction problem for *user-selected* text specifically —
this is the good news: Trailmark mostly needs "what did the user select," not "give me the
whole document in perfect reading order," which is the easier of the two problems).

### 5. Bibliography / reference parsing

| Option | What it actually requires | Verdict for Trailmark |
|---|---|---|
| **GROBID** | A JVM (Java) service; Docker image, "full" image ~5 GB (bundles Python/TensorFlow/pretrained embeddings for GPU-accelerated deep-learning models), lightweight CRF-only image is much smaller and CPU-only. RAM: **2 GB sufficient for header-only extraction, 3 GB for citations, 4 GB to structure a full document**, 6-8 GB recommended for batch/parallel use (source: GROBID's own docs + Docker readme). | **Disqualified outright.** A JVM + multi-GB Docker image is the opposite of everything Trailmark is built on (single lightweight .exe, no runtime dependencies). Even the "lightweight" CRF-only path still needs a JVM the app doesn't have and can't reasonably bundle. |
| **AnyStyle** | Ruby + `gem install anystyle-cli`. Ships a persistent dictionary (~2 MB) as a Ruby Hash, or GDBM/Redis backends for lower memory. | **Also disqualified.** Requires a Ruby runtime — a second language runtime PyInstaller would have to somehow bundle or shell out to, which the app doesn't have today and which conflicts with "prefer stdlib and vendored-JS." |
| **refextract / science-parse** | Both are Python/JVM tools built around the same class of ML reference-parsing models as GROBID; **not independently verified in this pass** — treat their footprint as unverified but presumptively in the same ballpark as GROBID/AnyStyle (external-runtime-heavy). | **Unverified, deprioritized** — no evidence found that either avoids the runtime weight this app is trying to avoid; not worth spiking ahead of the cheaper options below. |
| **pdf2doi** (Python, pip-installable) | Pure Python; extracts a DOI/arXiv ID from a PDF's *existing* text/metadata using several heuristics (regex over extracted text, PDF metadata fields), **then validates by querying `dx.doi.org` online** (per the project's own README). No JVM, no Ruby — this is the only tool in the list that fits Trailmark's dependency posture. Confirmed limitation from its own docs: "often, especially for old publications, none of the currently implemented methods will work," and it can pick up the wrong DOI if one appears in-text before the real one. | **Viable, cheap, worth vendoring or reimplementing the core regex logic directly** (it's small enough that hand-rolling the DOI-regex-over-text-and-metadata approach in Trailmark's own code, rather than adding a new pip dependency, may fit the "prefer stdlib" instinct better — pdf2doi's DOI-detection regex is public and short). |
| **PDF-embedded metadata (XMP + Document Info dict)** | No extra dependency at all beyond a PDF parser Trailmark likely already needs for rendering/page info. `pikepdf` (or even hand-rolling with the stdlib-adjacent minimal parsing Trailmark's docx-writer philosophy would favor) can read `/Info` dict fields (`/Author`, `/Title`, `/Subject`) and raw XMP XML (`pdf.Root.Metadata.read_bytes()`) if present. In practice: **most research-paper PDFs from publishers (Elsevier, Springer, IEEE, ACM) do embed a DOI in either the Info dict or XMP** — this is usually the highest-fidelity, zero-network source when present, but it is also frequently **absent** in preprints, scanned copies, or author-produced PDFs. | **First thing to try, free, no dependency, but not always populated — must have a fallback.** |
| **Crossref / doi.org content negotiation** | Confirmed as a plain HTTPS GET, no SDK, no API key required for basic lookups. Exact request shape (fetched/confirmed from Crossref's and DOI Foundation's own docs): `curl -L -H "Accept: application/vnd.citationstyles.csl+json" https://doi.org/10.1126/science.169.3946.635` — doi.org redirects (hence `-L`) to the registration agency (Crossref, DataCite, etc.) which returns CSL-JSON: full structured metadata (title, authors, container-title/journal, volume, issue, page, year, publisher) in the same schema reference managers (Zotero) consume. Crossref also exposes the same transform directly: `https://api.crossref.org/works/<doi>/transform` with the same Accept header. **This is the single best source of complete, correctly-formatted citation metadata** — far better than what any local parser can reconstruct from PDF text — but it is unambiguously a network call: **the user must be online**, and Crossref/DataCite coverage, while broad for journal articles, is not universal (preprints, non-DOI'd technical reports, etc. will 404). | **Best data quality, explicitly online-only — must degrade gracefully offline.** |

**Ranking for a dependency-averse, offline-first desktop app:**

1. **PDF-embedded metadata (XMP/Info dict DOI) → if present, resolve via Crossref/doi.org
   when online, else format directly from the embedded fields.** Zero new runtime
   dependency, works offline for basic Author/Title/Year even without a DOI.
2. **pdf2doi-style DOI regex over extracted text** (vendor the ~50-line detection logic,
   don't add the pip package) as a fallback when no embedded DOI exists — still needs
   Crossref to turn a DOI into full structured metadata, so still online-gated for the
   "good" citation, but a bare DOI string is itself useful to show the user even offline.
3. **Crossref/doi.org content negotiation** is the actual metadata engine behind both of
   the above once a DOI is known — no dependency, but it is the one part of this whole
   pipeline that **requires connectivity**; be explicit about that in the UI (e.g. a
   "citation incomplete — reconnect to fetch full details" state) rather than silently
   degrading.
4. **GROBID and AnyStyle are both disqualified** for this app specifically — not because
   they're bad tools (GROBID is in fact the strongest general-purpose reference parser
   that exists), but because both require a runtime (JVM, Ruby) Trailmark has explicitly
   chosen not to carry. If reference *list* parsing (not just the paper's own DOI) becomes
   a hard requirement later, that is the point to reconsider — it would be a deliberate,
   flagged architecture change, not something to sneak in as a "small dependency."

### 6. Recommended architecture — Feature 1

- Vendor `pdf.min.mjs` + `pdf.worker.min.mjs` (~1.4 MB) into the app's existing HTML/JS
  bundle; serve through pywebview's existing local HTTP server (already the delivery
  mechanism for the current UI, so no new serving infrastructure).
- Build a citation-capture page: pdf.js canvas rendering + text layer + the annotation
  editor layer configured to Trailmark's own colour palette, each colour bound (via the
  EventBus) to one of the app's log-entry kinds.
- On highlight creation: read the annotation's rect/quadpoints + colour from
  `AnnotationStorage`, cross-reference against `getTextContent()` for that page to recover
  the highlighted string, and hand the (text, colour→kind, page number) tuple to the
  existing `js_api` bridge exactly the way current UI actions already reach Python.
- Store highlights + notes as sidecar JSON in `%APPDATA%\Trailmark`, keyed by a hash of
  the source PDF (path is not stable enough — content hash is safer against renames/moves).
- Citation metadata: try embedded DOI/XMP first (free, offline); if present, resolve via
  Crossref when online; cache the resolved CSL-JSON alongside the sidecar so it only needs
  fetching once per document.
- **Effort estimate: 8–13 engineer-days.**
  - pdf.js integration + rendering + local-server serving spike: 1–2 days
  - Highlight editor wiring + colour→kind mapping UI: 2–3 days
  - Highlight→text cross-reference (quadpoints ↔ getTextContent join) + sidecar storage: 2–3 days
  - Note capture + selective/automatic logging flow into existing log format: 1–2 days
  - DOI/XMP extraction + Crossref resolution + offline-degradation UI: 2–3 days
- **Specific risks:**
  - Multi-column academic PDFs breaking the highlight-to-text join (mitigate: quadpoint-
    based matching is more robust than raw reading-order text since it's geometric, not
    stream-order — verify this early with a real multi-column paper).
  - pywebview's local-HTTP-server behavior needs to be confirmed for the *specific*
    version pinned in this repo (this was inferred from pywebview's general docs, not
    verified against the app's actual `pywebview` version pin — **first spike task should
    just confirm which origin the PDF page actually loads under**).
  - Large PDFs (100+ pages) parsed without a worker (fallback case) could block the UI
    thread — should be a non-issue if local-HTTP-server origin is confirmed, but worth a
    guard/test with a large file regardless.
  - Crossref coverage gaps (non-DOI'd sources) mean "auto-cite" will sometimes come back
    empty — needs a manual-citation fallback UI regardless of how good the automation is.

---

## Feature 2 — Chrome extension for one-shortcut web citation

### 1. Manifest V3 reality

**Keyboard shortcut (`commands` API):**
- An extension can define many named commands, but **only 4 of them may have a
  `suggested_key` set in the manifest** (confirmed via Chrome's own `chrome.commands`
  reference). Trailmark's single "capture" shortcut fits trivially inside that limit.
- Users can bind additional/different shortcuts manually at
  `chrome://extensions/shortcuts`, bypassing the 4-suggestion cap — but Trailmark cannot
  rely on a specific key combo working out of the box; it should ship one sensible default
  suggested key and tell users where to change it if it conflicts.
- A special sub-restriction exists for **global** commands (ones that fire even when
  Chrome isn't focused): their suggested keys are restricted to `Ctrl+Shift+[0-9]` only.
  Not relevant unless Trailmark wants capture to work while some other window has focus —
  worth deciding explicitly since it changes the shortcut's ergonomics.

**Reading the current selection:** a content script (or `scripting.executeScript` injected
on demand from the command handler) can read `window.getSelection().toString()` in the
page context. Since the shortcut fires via `chrome.commands.onCommand` in the service
worker, the standard pattern is: service worker receives the command → injects/messages a
content script in the active tab → content script returns selection text + `location.href`
back to the service worker.

**Viewport screenshot — `chrome.tabs.captureVisibleTab`:**
- Requires the **`activeTab`** permission (confirmed from Chrome's own reference) — this
  is the *good* case: `activeTab` grants temporary access to the current tab only in
  direct response to a user action (a keyboard shortcut counts) **without** showing an
  install-time "read your browsing data" warning, which is the right trade-off for a
  citation tool a user invokes intentionally per-page.
- Supports PNG or JPEG output; JPEG takes an explicit `quality` (0–100, default 92, mapped
  internally to canvas `toDataURL` `encoderOptions`).
- With `activeTab`, capture works even on otherwise-restricted `chrome://`-scheme pages,
  other extensions' pages, and `data:` URLs — but **only because the user just invoked the
  extension on that exact tab**; it does not work opportunistically in the background.
- **Known real gaps, not fully pinned by this research pass:** Chrome's built-in PDF
  viewer tab (`chrome-extension://mhjfbmdgcfjbbpaeojofohoefgiehjai/...`, the PDF Viewer
  extension) and certain internal pages are historically flaky/blocked for
  `captureVisibleTab` in various Chrome versions — this specific edge case is
  **unverified** in this pass and should be spiked directly (open a PDF in a Chrome tab,
  press the shortcut, see what actually comes back) rather than assumed either way.
- `activeTab` vs `<all_urls>`: `activeTab` is strictly better for this feature — it needs
  no permission screen, satisfies least-privilege, and Trailmark's use case (a per-page,
  user-invoked capture) is exactly the scenario `activeTab` was designed for.
  `<all_urls>`/broad `host_permissions` would only be needed if Trailmark wanted the
  content script running proactively on every page without a prior user gesture, which
  isn't the described feature.

### 2. Reaching a native Windows desktop app

**Option A — Native Messaging.**
- Windows registration: a registry value at
  `HKEY_CURRENT_USER\Software\Google\Chrome\NativeMessagingHosts\<host.name>` (or the
  HKLM equivalent for machine-wide install), whose default value is the **full path to a
  JSON manifest file** (the manifest itself can live anywhere on disk on Windows).
- Manifest shape (illustrative, not to be written into the repo):
  ```json
  {
    "name": "com.trailmark.native_host",
    "description": "Trailmark native messaging host",
    "path": "C:\\Path\\To\\trailmark_host.exe",
    "type": "stdio",
    "allowed_origins": [
      "chrome-extension://<the extension's id>/"
    ]
  }
  ```
- Protocol: length-prefixed JSON over stdin/stdout (a 4-byte native-endian length header,
  then the UTF-8 JSON payload).
- **Size limit is asymmetric and matters here**: messages **from** the native host to
  Chrome are capped at **1 MB**; messages **to** the native host can be up to **4 GB**
  (confirmed from Chrome's own Native Messaging docs). A base64 PNG data URI for a 1080p
  screenshot (~1–4 MB range, see §4) sent host→extension could **exceed the 1 MB cap** —
  this is a real, concrete failure mode for exactly Trailmark's screenshot use case, not a
  theoretical one. (Extension→host is not the constrained direction, so if the screenshot
  flowed the other way it would be fine — but the natural flow here, extension captures
  and *sends to* the host, is extension→host, which is the 4 GB-limited direction, so
  actually the size cap is **not** the blocker for capture-and-send. It **would** matter if
  Trailmark ever wanted the desktop app to push data back through native messaging in the
  other direction, e.g. returning a rendered citation preview — worth remembering if a
  reverse channel gets added later.)
- **The launch model is the real architectural problem for Trailmark, not the size cap.**
  Native Messaging hosts are **launched by Chrome, per connection, as a child process of
  Chrome**, communicating only over that connection's stdio. Chrome does not hand messages
  to an already-running, independent tray application — it starts the registered `.exe`
  fresh each time a `connectNative()`/`sendNativeMessage()` call is made. For a
  **single-instance tray app that is already running**, this means Trailmark's registered
  native-messaging executable can't simply *be* the tray app — it would need to be a thin
  launcher/shim that detects the already-running tray process and hands the message off to
  it (e.g. via a named pipe, local socket, or the same HTTP endpoint discussed in Option B)
  — Native Messaging alone does not solve "deliver this to my existing background process,"
  it solves "launch a short-lived helper process and talk to it over stdio." That
  indirection mostly cancels out Native Messaging's appeal.

**Option B — a localhost HTTP endpoint inside the tray app.**
- MV3 service workers can call `fetch()` freely, including to `http://127.0.0.1:<port>`,
  **provided the extension's `host_permissions` includes that origin** (or the request
  target is covered by `activeTab`/host permissions as applicable) — this is standard,
  documented MV3 `fetch` usage, not a special case.
- **Private/Local Network Access is the real wrinkle, and it recently got stricter.**
  Chrome 142 (shipped **28 October 2025**, i.e. right around now) introduced **Local
  Network Access (LNA)**, which puts a **browser permission prompt** in front of requests
  from public/regular web pages to private-network addresses including `127.0.0.1`. This
  is squarely aimed at *ordinary web pages* silently probing a user's router/localhost
  services. Extensions are a genuinely unsettled/actively-discussed case in Chromium's own
  extension developer forum as of this research (the LNA rollout explicitly distinguishes
  "should extensions be exempt or not" as an open policy question, with a
  `LocalNetworkAccessAllowedForUrls` enterprise policy as one lever) — **this is not fully
  pinned down and should be flagged as a live risk**, not assumed away: a localhost
  endpoint that works today in a personal Chrome install could start requiring a user-
  facing permission grant (or become admin-policy-gated) as LNA enforcement matures. This
  is worth re-checking against the shipping Chrome version at implementation time, not
  just at research time.
- **Security exposure of an open localhost port**: any local process (not just Trailmark's
  own extension) can `POST` to an open `127.0.0.1` port — this is a real local
  attack surface (a malicious local process, or in principle a malicious page if LNA/CORS
  don't block it, could inject fake log entries). Standard, cheap mitigations, all
  implementable without new dependencies:
  - **Bind to `127.0.0.1` only**, never `0.0.0.0` — prevents any exposure beyond the local
    machine.
  - **A shared secret token**, generated once at first run and stored both in the tray
    app's local config and pushed into the extension's storage during a one-time pairing
    step (e.g. the extension's options page displays a "pairing code" the user copies from
    Trailmark, or Trailmark's tray app writes it somewhere the extension's first-run flow
    can read) — every request must include it; reject anything without a match.
  - **Check the `Origin` header** on incoming requests and reject anything that isn't the
    extension's own `chrome-extension://<id>` origin, as defense in depth alongside the
    token.
  - CORS itself is nearly moot here since the *extension's service worker* is the caller
    (not a content script running in page context), so ordinary web-page CORS restrictions
    largely don't apply to the extension→localhost hop the way they would to a plain
    `<script>` on some random website — the LNA permission-prompt layer above is the
    actually-relevant new gate, not classic CORS.

**Recommendation: localhost HTTP, not Native Messaging.**
Reasoning: Native Messaging's launch-per-connection model doesn't compose with "hand data
to an already-running tray app" without adding a second IPC hop anyway (a shim process
talking to the tray app over some local channel) — at which point Trailmark has built a
local RPC mechanism *and* dealt with Native Messaging's registry/manifest packaging
overhead, for no net benefit over just exposing that local RPC mechanism directly as an
HTTP endpoint the extension calls. The localhost-HTTP path also avoids the native-messaging
manifest/registry install step being a separate installer responsibility from the main app
(the tray app already needs to run background code — adding one more `http.server` thread
is cheap; wiring per-connection process spawning + a registry key + a JSON manifest is
comparatively more moving parts for the same result). The LNA uncertainty is real but is a
"verify at implementation time" risk, not a disqualifying one — worst case, Trailmark asks
users to click through one Chrome permission prompt once.

### 3. Distribution

- **Chrome Web Store**: a **one-time $5 USD developer registration fee** (confirmed,
  though note some 2025/2026-dated secondary sources exist rather than Google's own
  pricing page directly — treat the exact figure as **highly likely but not re-verified
  against Google's current billing page in this pass**). Review turnaround **"typically
  1-3 business days"** per secondary sources — Google does not publish a hard SLA, so
  treat this as **approximate, not guaranteed**, especially since Trailmark's extension
  requests `activeTab` + a native/localhost communication pattern, which historically
  draws closer manual review than a trivial extension.
- **Unlisted** listing (Chrome Web Store, visible only via direct link, not searchable) is
  fully workable and still just needs the one-time $5 fee + normal review — this is
  probably the right distribution model for a companion extension to a niche desktop app.
- **Self-hosted `.crx` (no Web Store at all) is effectively dead for regular users.**
  Since ~2020, Chrome hard-blocks installing a downloaded `.crx` outside the Web Store for
  normal (non-managed/enterprise) installs — it throws `CRX_REQUIRED_PROOF_MISSING` and
  disables the extension. The only surviving path is **enterprise policy** (`ExtensionSettings`
  / Group Policy / Chrome Browser Cloud Management), which is not applicable to Trailmark's
  actual users (individual desktop users, not managed corporate fleets). **This rules out
  "just host a .crx on our own site" as a real option** — Web Store (even unlisted) is
  required.
- **Firefox (AMO)**: every add-on, even one never listed on addons.mozilla.org, **must
  still be submitted to Mozilla for signing** — Firefox refuses to run unsigned
  extensions. Automated review/signing "can take up to 24 hours… or longer if selected for
  manual review." Minified/bundled code requires submitting an unminified **source package**
  for review. This is a genuinely separate submission pipeline, not just a repackage.
- **Edge Add-ons**: **not independently verified in this pass** (search did not surface a
  fetched primary source) — treat Edge's requirements as **unverified**, though
  Edge's extension platform is Chromium-based and historically accepts an unmodified
  Chrome MV3 package with its own separate store submission/review (this is the general
  ecosystem norm, but flagging explicitly that it was not confirmed against a primary
  Microsoft doc here).
- **Practical read**: shipping Chrome-only, unlisted, is the cheap path (~$5, days not
  weeks). Firefox/Edge are each a **separate submission + review cycle**, not a checkbox —
  budget them as their own small milestones if genuinely required, not as a rounding error
  on the Chrome build.

### 4. Screenshot size

A precise, sourced number for "a 1080p PNG data URI" was **not found as a single pinned
figure** — this is content-dependent (PNG is lossless and its size varies hugely with
image complexity: a text-heavy page compresses very differently from a photo-heavy one).
What can be stated with confidence:
- Base64 encoding itself adds a fixed, verifiable **~33% overhead** over the underlying
  binary size (every 3 bytes → 4 ASCII characters) — this part is exact, not an estimate.
- A full 1920×1080 PNG screenshot of a typical, moderately complex web page commonly lands
  in the **low-single-digit megabytes** (order of ~1–3 MB is a reasonable planning
  assumption based on general PNG-compression behavior for screen content, but this
  specific range is **not pinned to a fetched source** in this research pass — mark it
  **unverified**, and validate with an actual `captureVisibleTab` PNG capture at
  implementation time rather than trusting this estimate).
- Given the base64 overhead, a data-URI transport for even a modest 1–2 MB PNG becomes
  **1.3–2.7 MB of JSON string** — well under Native Messaging's 4 GB extension→host cap
  (irrelevant either way, since §2 recommends the localhost HTTP path instead) and
  perfectly fine as an HTTP POST body to a localhost server (no meaningful size ceiling
  there).
- **Recommendation regardless of the exact byte count**: capture as **JPEG at a
  moderate quality (e.g. 80-85)**, not PNG. `captureVisibleTab`'s JPEG quality parameter
  is exactly built for this trade-off, screenshots-for-citation-context don't need
  lossless fidelity, and JPEG will reliably be smaller than PNG for photographic/mixed
  web content — this avoids ever needing to think hard about the data-URI size question
  in the first place, rather than relying on downscaling logic that adds code for a
  marginal, content-dependent win.

### 5. Recommended architecture — Feature 2

- Manifest V3 extension: `commands` (one shortcut, default suggested key, documented
  fallback to `chrome://extensions/shortcuts`), `activeTab` permission, a `background`
  service worker, and a minimal content script for `window.getSelection()` (injected via
  `scripting.executeScript` in response to the command, not persistently running on every
  page — keeps the manifest to `activeTab` only, no broad host permissions).
- On shortcut: service worker → `chrome.tabs.captureVisibleTab({format: 'jpeg', quality: 85})`
  + inject content script for selection text + tab URL/title → assemble one payload →
  `POST` to `http://127.0.0.1:<port>/capture` on the tray app, with the shared-secret
  token in a header and the extension's own origin checked server-side.
- Tray app: a lightweight `http.server`/`asyncio` listener (stdlib-only, matches the
  dependency-averse posture) bound to `127.0.0.1`, running alongside the existing
  pywebview/pystray loop, feeding captures into the same logging pipeline the PDF feature
  and the rest of the app already use.
- One-time pairing: on first run of the extension (or first run of the tray app after
  install), generate the shared secret in the tray app and surface it in the extension's
  options page for the user to paste in — a few lines of UI, no external dependency.
- Ship to the Chrome Web Store as an **unlisted** listing ($5 one-time fee); treat
  Firefox/Edge as separate, optional follow-on milestones, not part of this slice.
- **Effort estimate: 5–8 engineer-days.**
  - Extension skeleton (manifest, commands, activeTab capture, selection content script): 1–2 days
  - Tray-app localhost listener + pairing/token flow + Origin check: 2–3 days
  - Integration into existing logging/citation pipeline: 1–2 days
  - Web Store submission + first-review iteration buffer: 1 day (plus unbudgeted wait time
    for Google's review, which is outside engineering control)
- **Specific risks:**
  - **LNA (Local Network Access) enforcement on extensions is genuinely unsettled** as of
    this research (Chrome 142, Oct 2025) — re-verify against the actual shipping Chrome
    version at implementation time; worst case is one extra permission prompt, not a
    blocker, but don't assume today's behavior is Chrome's final answer.
  - `captureVisibleTab` behavior on Chrome's internal PDF-viewer tabs and `chrome://`
    pages is **unverified** in this pass — spike it directly before relying on "capture
    always works."
  - Review turnaround for a Web Store submission is not guaranteed to be fast — don't put
    it on a tight ship-date critical path.
  - A shared-secret pairing UX is one more manual setup step for the user (copy a code
    from the tray app into the extension) — small but real onboarding friction to design
    around, not a pure engineering risk.

---

## Decision table

| Feature | Verdict | Reasoning | Cheapest first slice to prove it |
|---|---|---|---|
| **1 — In-app PDF reader for citation capture** | **RECOMMEND WITH CAVEATS** | Technically sound and fits the size/dependency budget (~1.4 MB for pdf.js core, no new runtime), but two real unknowns are load-bearing: (a) confirm pywebview's actual serving origin for this app's pinned version so the worker genuinely works, and (b) the highlight→text-content join for multi-column PDFs needs to be proven, not assumed. Bibliography auto-parsing is only "recommend" for the cheap tiers (embedded DOI + Crossref); GROBID/AnyStyle are disqualified outright by the dependency posture. | Vendor `pdf.min.mjs`+`pdf.worker.min.mjs`, render one real multi-column research PDF inside the existing pywebview window, confirm the worker actually runs (check DevTools for "fake worker" warnings), and manually select+highlight one passage to confirm quadpoints can be joined back to `getTextContent()` text. If that spike works, the rest is normal feature engineering. |
| **2 — Chrome extension for one-shortcut web citation** | **RECOMMEND WITH CAVEATS** | The mechanics (commands, activeTab, captureVisibleTab, localhost HTTP with a shared secret) are all well-established and cheap — this is a well-worn pattern, not novel territory. The caveat is entirely about two externally-controlled unknowns: Chrome's Local Network Access rollout could add a user-facing prompt to the localhost call, and Web Store review timing is outside engineering control. Neither is a reason to not build it; both are reasons not to promise a specific ship date yet. | Ship a two-file proof: a manifest with just `commands`+`activeTab`, a command handler that captures a JPEG screenshot and POSTs it (with a hardcoded test token) to a throwaway local Python `http.server` script — confirms captureVisibleTab, the shortcut, and the localhost POST all work together on the current Chrome version, before building the real pairing/token/logging integration. |
