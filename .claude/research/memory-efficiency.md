# Trailmark — Memory/Resource Efficiency Research

Scope: idle-RAM reduction for a pywebview (WinForms/WebView2) + pystray tray app that stays
resident all day, plus the memory implications of the incoming multi-format export /
headless-PDF work. Repo inspected: `point_logger.py`, `ui.py`, `.venv/Lib/site-packages/webview`.

Ground truth confirmed by reading the installed pywebview 5.x source
(`webview/platforms/edgechromium.py`, `webview/platforms/winforms.py`, `webview/__init__.py`):

- Each `webview.create_window()` on Windows creates one WinForms `WebView2` control
  (`self.webview = WebView2()`) inside the **same** .NET process/AppDomain — pywebview does not
  spawn a new OS process per window. Two windows = two `CoreWebView2` controls in one host
  process.
- pywebview does **not** set a custom `UserDataFolder` or pass
  `WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS` itself — it only exposes `WEBVIEW2_RUNTIME_PATH`
  (fixed-version runtime override) and `--remote-debugging-port` via `REMOTE_DEBUGGING_PORT`.
  There is no `webview_settings` key for extra browser arguments.
- Because both controls run in the same process with the default (unset) `UserDataFolder`, and
  Microsoft's own docs say a `CoreWebView2Environment` is shared automatically for controls
  created with identical creation properties in the same process, Trailmark's two windows
  **already share one WebView2 browser process** — they do not each spin up an independent
  browser-process tree. What is *not* shared is the renderer process: WebView2/Chromium gives
  each top-level `WebView2` control (site instance) its own renderer process, the same as two
  tabs in Edge. So the real duplication in Trailmark today is **2 renderer processes + 1 GPU
  process + 1 network/utility process on top of 1 shared browser process**, not two full browser
  trees.

---

## 1. Where the RAM actually goes

For a pywebview(WinForms/WebView2)+pystray Python app idling in the tray, the resident set
breaks down roughly like this (component-level; exact numbers vary by Windows build, WebView2
Runtime version, and GPU driver — flagged **unverified** where no benchmark could be found):

| Component | Typical idle contribution | Avoidable? |
|---|---|---|
| Python 3.11 interpreter + stdlib import graph | ~15–30 MB **unverified** (well-known order of magnitude for CPython 3.11 with `threading`, `json`, `ctypes` imported; no single authoritative number found) | Partially — lazy-import heavy modules |
| PyInstaller `--onefile` overhead | One-time extra ~5–15s startup unpack cost to a temp `_MEIxxxx` dir, plus a bootloader stub process; **does not meaningfully add to steady-state idle RAM** once unpacked into the running process — the "overhead" is mostly disk I/O/startup latency, not resident memory | Switch to `--onedir` removes startup unzip cost; doesn't move the needle on idle RSS |
| WebView2 **browser** process (shared, 1 instance since both pywebview windows are in-process) | ~80–150 MB **unverified** (order-of-magnitude consistent with community reports in the search results below; Microsoft does not publish a fixed number because it depends on cache/profile size) | Partially — `MemoryUsageTargetLevel=Low`, trimming disk cache, smaller UDF |
| WebView2 **renderer** process — one per open top-level window/site instance (Trailmark has 2: popup + main) | ~40–100 MB each idle **unverified**, scales with DOM size/JS heap; ui.py's ~53 KB of embedded HTML/CSS/JS is trivial by web standards so should sit at the low end | Yes — see §2 |
| WebView2 **GPU process** (shared) | ~30–60 MB **unverified**; exists because WebView2 uses the GPU by default for compositing | Yes, via `--disable-gpu`, at a rendering-quality/battery cost — Microsoft explicitly advises *against* disabling it except for troubleshooting |
| WebView2 **network/utility/crashpad** helper processes | tens of MB combined **unverified** | Not really controllable from the pywebview layer |
| pystray + Pillow | Pillow itself is a compiled C extension (~a few MB resident once imported); pystray's Win32 backend uses `Shell_NotifyIcon` under the hood already — Pillow is only used to hand it an `Image` object | Yes — swap for a pre-baked `.ico` fed straight to `Shell_NotifyIcon`/pywin32, drop the `Image.open(...).convert("RGBA")` call at `point_logger.py:247` |
| base64 data URIs (logo.png 202 KB, icon-96.png 8.9 KB) embedded in `ui.py` | Each webview window that loads `ui.py`'s HTML pays for decoding the base64 string into memory and Chromium re-decoding it into a bitmap in its own process — duplicated per window (i.e., ~2× the decoded-bitmap cost since main + popup both load) | Yes — see §2 |

**Realistic idle footprint** for the *current* two-window architecture: commonly reported
ballpark for a "one WebView2 window, simple content, GPU on" idle app is **150–250 MB total**
across all its child processes (browser+renderer+GPU+utility) — this is a synthesis of the
Hoppscotch and WebView2Feedback GitHub threads below, not a number Microsoft publishes, so treat
it as **unverified but directionally consistent**. With Trailmark's second always-alive window
(the main 1180×764 window, which the user may never open in a given session), a second renderer
process is being paid for continuously — this is the single largest avoidable cost.

Sources:
- [WebView2 Feedback — process leak, ~30 GB from repeated instances](https://github.com/oraios/serena/issues/1281) (extreme case, multiprocessing anti-pattern, illustrates unbounded growth risk, not steady-state cost)
- [Hoppscotch Desktop — excessive memory from WebView2 processes](https://github.com/hoppscotch/hoppscotch/issues/6340)
- [WebView2Feedback #1424 — processes not shut down when WebView-hosting windows close](https://github.com/MicrosoftEdge/WebView2Feedback/issues/1424)
- [Microsoft Learn — Performance best practices for WebView2 apps](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/performance) (authoritative on mechanism, not on absolute MB numbers)
- [Microsoft Learn — Process model for WebView2 apps](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/process-model)

---

## 2. The single highest-leverage change

Ranked by evidence quality, not just intuition:

### A. Lazy-create the main window, destroy on close — **high leverage, but check reliability**
Currently `build_windows()` creates *both* `self.popup` and `self.full` at startup
(`point_logger.py:378-385`), and `on_full_closing` just calls `self.full.hide()` — the main
window and its renderer process live for the entire session even if the user never opens it
(`point_logger.py:393-400`).

- **What WebView2 actually reclaims on destroy:** destroying a `CoreWebView2Controller`/closing
  a WinForms `WebView2` control tears down that control's renderer process (assuming no other
  control shares the same renderer/site-instance), returning that renderer's RSS (JS heap +
  DOM + compositor buffers) to the OS. The shared browser process, GPU process, and network
  process stay resident because the popup still needs them — so the saving is roughly "one
  renderer process's worth" (order tens of MB, **unverified** exact figure), not the full
  150–250 MB.
- **Does pywebview support destroy+recreate reliably?** pywebview does expose `window.destroy()`
  (already used for both windows in `point_logger.py:368-374` at quit time) and
  `webview.create_window()` can be called again after `webview.start()` has begun, but recreating
  a *destroyed* window from a background thread on the WinForms backend is a known source of
  flakiness in this exact codebase — the recent commit history (`01d2acf "fix crashy
  show_tray_menu (no move from tray thread)"`, `7d1a80a "remove crashy 3rd webview menu"`) shows
  Trailmark has already hit UI-thread/cross-thread crashes with pywebview's WinForms backend.
  Recommendation: don't destroy+recreate the main window on every close; instead keep the
  current hide-on-close behavior (cheap, already stable) and only invest in true destroy/recreate
  if profiling shows the main window's renderer is actually a material chunk of idle RAM in
  practice. This is the item most likely to reintroduce the exact crash class already fixed —
  treat as **medium risk**.

### B. Both windows already share one browser process — nothing to do here
As established above, pywebview's WinForms backend already puts both windows' `WebView2`
controls in one process with (by default) one shared `CoreWebView2Environment`/user-data folder,
because neither window sets a custom `UserDataFolder`. There is no separate "spawn one shared
environment" project to do — it's already the behavior. Verify this holds for Trailmark
specifically with Task Manager (`msedgewebview2.exe` process count, grouped by "Details" tab,
should show one `--type=browser` regardless of whether 1 or 2 pywebview windows are open); this
research could not run that measurement directly (no live Trailmark process was profiled).

### C. WebView2 browser-argument flags
- `WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS` is a standard **OS environment variable** read by the
  WebView2 loader itself (not something pywebview needs to plumb through) — set it via
  `os.environ['WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS'] = "..."` **before** the first
  `webview.create_window()`/`webview.start()` call in `point_logger.py`.
- `--disable-gpu`: Microsoft's own performance doc explicitly says **do not use this except for
  troubleshooting** — GPU compositing is "critical for performance," and disabling it can shift
  cost from GPU-process memory to CPU-bound software rendering, which for a mostly-static
  form/list UI like Trailmark's popup may be an acceptable trade, but Microsoft does not endorse
  it as a memory-savings technique. Treat as **experimental, verify visually** before shipping.
- `--single-process`: **not supported by Chromium/WebView2 in production** — Chromium's
  multi-process security model assumes separate renderer processes; `--single-process` is a
  dev/test-only flag in upstream Chromium and known to be unstable or rejected outright in
  WebView2's hardened build. Do not rely on it. **unverified whether WebView2 silently ignores
  it or crashes** — no direct citation found; treat as unsupported by default.
- `--renderer-process-limit=1`: legitimate Chromium flag; forces same-site/isolated pages
  toward a single renderer. For a 2-window app this could collapse the two renderer processes
  into one, but breaks WebView2's process-isolation crash containment (a JS crash in the popup
  could now take the main window with it). **unverified** whether WebView2 honors this identically
  to full Chrome — no explicit doc citation found, only that it's a general Chromium switch.
- `--js-flags="--max-old-space-size=..."`: caps the V8 heap ceiling, not steady-state usage —
  relevant only if a leak is suspected, not for baseline idle RAM.
- `--memory-pressure-off` vs the default (on): default is "on" (Chromium responds to Windows
  low-memory signals by trimming caches). Turning it off would *increase* memory pressure
  responsiveness loss — this is a flag to leave alone; there is no flag literally named
  `--memory-pressure-off` (confusable with disabling MemoryPressureListener behavior) —
  **unverified**, not confidently recommended.
- `--disable-features=...`: could disable specific Chromium features (e.g.
  `BackForwardCache`, `Vulkan`) but requires per-feature testing; no blanket recommendation.
- **Documented, Microsoft-endorsed API alternative that beats flag-hacking:**
  `CoreWebView2.MemoryUsageTargetLevel = Low` on the main window while it's hidden, restored to
  `Normal` when shown again, and/or `CoreWebView2.TrySuspendAsync()` on the popup while it's not
  visible — both are official WebView2 memory-management APIs described in the performance doc
  (see §2.A sources). pywebview does **not** currently expose `MemoryUsageTargetLevel` or
  `TrySuspendAsync` — using them would require dropping to pythonnet/`clr` and reaching into
  `self.webview.CoreWebView2` directly from `edgechromium.py`'s underlying WinForms control
  (accessible via pywebview's internal `window.gui.pywebview_window` handle or a small patch),
  which is a real but moderate-effort integration, not a one-line env var.

Sources:
- [Microsoft Learn — WebView2 browser flags](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/webview-features-flags)
- [Microsoft Learn — Performance best practices for WebView2 apps](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/performance)
- [Microsoft Q&A — GPU process exited unexpectedly, disable-gpu discussion](https://learn.microsoft.com/en-us/answers/questions/2262467/gpu-process-exited-unexpectedly-exit-code-34-only)

### D. `SetProcessWorkingSetSize` / `EmptyWorkingSet` on minimize/hide — **mostly cosmetic**
Confirmed from Microsoft's own docs discussion and community analysis: these APIs don't free
memory the process no longer needs — they force *currently-resident, possibly still-wanted*
pages out to the pagefile immediately, rather than letting Windows' own working-set trimmer
(which uses actual LRU/usage heuristics) decide. Effect: Task Manager's "Memory" column drops
immediately (looks good in a screenshot), but:
- If the app becomes active again soon, those pages page back in from disk — a real latency
  cost (a stutter on "show window"), trading a cosmetic RAM number for a UX regression.
- It doesn't reduce *commit* — the memory is still reserved/committed, just not resident.
- Windows' own automatic working-set management is generally regarded as smarter than a manual
  force-trim, per the community consensus in the sources reviewed.

**Verdict: do not add this for Trailmark.** It would make Task Manager numbers look better
without reducing real system memory pressure, and pairs badly with a tray app the user expects
to pop open instantly on hotkey — exactly the scenario ([hotkey.py](../../hotkey.py) exists for)
where a page-fault stutter is most noticeable.

Source: [Working Set — Win32 apps, Microsoft Learn](https://learn.microsoft.com/en-us/windows/win32/memory/working-set); community synthesis in [SetProcessWorkingSetSize: you hardly ever need to call this](https://wiert.me/2021/07/07/setprocessworkingsetsize-you-hardly-if-ever-need-to-call-this-from-your-process/) — **treat the specific MB figures as unverified**, but the mechanism (forces pageout, doesn't reduce commit, fights the OS's own heuristics) is corroborated across all sources found.

### E. Python-side changes
- `gc.freeze()`: only helps generational-GC scan time after a large one-time allocation burst
  (e.g., right after loading `points.json` fully into memory) — it does not reduce RSS, it
  reduces future GC pause overhead by excluding frozen objects from collection scans. Low
  relevance to idle RAM; cheap to add, negligible risk, but don't oversell it as a memory win.
- Lazy imports: legitimate, cheap. `llm.py`, any DOCX/PDF export libraries, and Pillow itself
  should be imported inside the functions that use them, not at module top, so the tray-idle
  path never pays for their import cost. Effort: ~1 hour. Saving: a few MB, mostly startup time
  not steady idle RSS.
- Dropping Pillow for tray icon: pystray's own Win32 backend already calls `Shell_NotifyIcon`
  under the hood — Pillow is only a data-format adapter pystray demands as input
  (`pystray.Icon(..., image)` wants a `PIL.Image`). Trailmark currently does
  `Image.open(icon_path).convert("RGBA")` (`point_logger.py:247`) at least once per icon change.
  Fully removing Pillow means either forking pystray (community fork `pycona` exists exactly for
  this — "removes the Pillow dependency for the Windows platform, dramatically reducing the
  executable size" per its own description, **unverified** actual MB figure) or writing a raw
  `win32gui`/`win32api` `Shell_NotifyIcon` tray icon directly against a `.ico`, bypassing pystray
  entirely. Given Trailmark already depends on `pywin32` transitively (webview's WinForms
  backend) this is plausible, but it is a rewrite of the tray subsystem, not a tweak — the RAM
  saved is Pillow's own resident footprint (a few MB) plus whatever PyInstaller-bundled DLLs
  Pillow drags in (its own image codecs, notably `libjpeg`/`zlib`/`libwebp` shared libs bundled
  by `--onefile`), which matters more for *binary size* than *idle RSS*.
- Base64 data URIs → local `file://`/tiny HTTP server: right now `ui.py` embeds `logo.png`
  (202 KB → ~270 KB as base64) and `icon-96.png` (8.9 KB) directly in the HTML string constants
  injected via `webview.create_window(html=...)`. Every window that loads this HTML re-parses
  and re-decodes that base64 blob independently (once per window: popup + main = 2×). Serving
  these as `file://` URLs (pywebview supports a `url=` window created against a local file, or a
  small `http.server`/`waitress` loopback server) lets Chromium's normal disk/HTTP cache dedupe
  the decode across windows and avoids holding an extra ~360 KB (270 KB×~1.33 base64 overhead)
  of string data in the Python process per window. This is a real but small saving (hundreds of
  KB, not MB) — worth doing as part of the template-system work anyway (see §5), not as a
  standalone memory fix.

---

## 3. Alternative runtimes

| Option | Reported idle RAM | Rewrite cost for Trailmark | Verdict |
|---|---|---|---|
| **Stay on pywebview, restructure** | Same WebView2 floor (~150–250 MB across processes, unverified) minus whatever §2 items are applied | Low — hours to days | Best cost/benefit for a solo maintainer; the floor is set by WebView2 itself, not by pywebview |
| **Rust + Tauri v2** | Community-reported **~30–80 MB idle** vs Electron's ~150–400 MB (see sources) — Tauri also uses WebView2 as its Windows renderer, so the *webview* memory floor is the **same WebView2 process family**; Tauri's win over Electron is *not shipping a bundled Chromium/Node* — on Windows, Tauri and a lean pywebview app converge toward similar WebView2-driven floors, because both delegate rendering to the same OS-provided WebView2 Runtime. The commonly-cited "30-40 MB" Tauri numbers are largely **Linux (WebKitGTK) or best-case single-window Windows measurements**; a fair Windows apples-to-apples number for a 2-window Tauri app is **unverified** but should not be assumed dramatically lower than an equally lean pywebview app, since both ride the same WebView2 process tree on Windows. | Full rewrite: UI already exists as HTML/CSS/JS in `ui.py`, so front-end reuse is real, but `point_logger.py`, `point_store.py`, `hotkey.py`, `llm.py` (all Python) would need a Rust rewrite or an IPC boundary. Realistically **1–3 weeks** for a solo maintainer given the app's current size (~53 KB UI, a handful of Python modules) | Worth it only if the maintainer wants the ecosystem improvements (auto-update, code-signing tooling, smaller installer) — the memory case specifically is weaker than the marketing numbers suggest, because Windows Tauri still uses WebView2 |
| **C# / WinUI3 or WPF (.NET Native AOT)** | WPF/WinUI3 hosting WebView2 pays the *same* WebView2 process cost as pywebview for the web content, plus a much smaller host-process footprint than a Python interpreter + PyInstaller bootloader (Native AOT .NET host processes commonly idle in the low tens of MB) — **unverified exact figure**, but directionally the host-process saving (not the WebView2 saving) is the real win | Full rewrite of all Python logic to C#; UI markup could stay mostly HTML/CSS/JS since WPF/WinUI3 also embed WebView2. **2–4 weeks** for a solo maintainer, higher for someone without existing C# fluency | Meaningful if the *Python interpreter + PyInstaller* overhead (not the WebView2 overhead) is judged worth eliminating — but that overhead is smaller than the WebView2 footprint to begin with, so ROI is modest relative to the rewrite cost |
| **Go + Wails** | Wails uses WebView2 on Windows too (same floor argument as Tauri) with a small Go host binary; no authoritative idle-RAM benchmark found for Wails specifically — **unverified** | Full rewrite, comparable effort to Tauri | Same ceiling as Tauri/WinUI3: the webview cost dominates and doesn't change; only the host-process savings differ | 
| **Hybrid: raw Win32/pywin32 UI for the popup, keep webview for the main window** | Eliminates one full WebView2 renderer process (the popup's) permanently, since a native Win32 form (`pywin32`/`ctypes` + GDI or a lightweight `tkinter` popup) has no Chromium involvement at all — savings on the order of the popup's renderer process (tens of MB, unverified exact) plus removing base64/HTML overhead for that surface entirely | **Moderate** — the popup is described as a fixed 462×648 quick-capture form; rewriting a bounded, simple capture form (a few text fields + buttons) in native Win32/`tkinter` is realistic in **1–3 days**, versus rewriting the full main window (which has richer, evolving UI: overview/detail, exports, templates) which would be much harder to keep in native widgets | **This is the most interesting option for Trailmark specifically**, because the prompt itself identifies the popup as "the always-resident part" — it is open (or at least alive) all day, while the main window is opened occasionally. Cutting the always-resident surface's WebView2 dependency removes a permanent renderer process rather than an occasional one. Recommend prototyping this before considering any full-framework rewrite. |

Sources:
- [Rustify — Tauri vs Electron 2026, 30-40MB vs Electron figures](https://rustify.rs/articles/rust-tauri-vs-electron-2026)
- [Digital Applied — Tauri vs Electron vs Deno vs Wails 2026](https://www.digitalapplied.com/blog/desktop-apps-web-stack-tauri-electron-deno-wails-2026)
- [tauri-apps/tauri #5889 — memory benchmark methodology concerns, shared-memory accounting caveat](https://github.com/tauri-apps/tauri/issues/5889)

Overall verdict: **on Windows specifically, every "lightweight framework" (Tauri, Wails,
WinUI3/WPF) still uses WebView2 for rendering**, so none of them escape the ~150-250 MB
multi-process WebView2 floor this research found for the current architecture. Their real,
verifiable advantage over Python+PyInstaller is a smaller *host* process and a smaller
*installer*, not a smaller *browser engine footprint*. Given that, and given Trailmark is a
working, shipping app maintained solo, **a full framework rewrite is not justified by the
memory case alone** — the hybrid native-popup approach captures most of the same benefit
(removing one permanent renderer process) at a fraction of the cost.

---

## 4. The PDF-rendering question

| Approach | RAM (spike/steady) | Disk footprint | PyInstaller bundling | Fit for "occasional, low-RAM app" |
|---|---|---|---|---|
| **Headless Chrome/Playwright on demand** | ~150 MB resident per browser instance + ~30 MB per page reported by industry benchmarks (see source) — this is a **spike**, not idle, since it's launched only for export and torn down after | Chromium download ≈280 MB; a Playwright+Chromium install is commonly cited around ~550 MB unpacked | Painful — PyInstaller `--onefile` does not play well with bundling an entire external Chromium binary; typically needs `--add-data`/`--onedir` plus post-install browser download step (`playwright install chromium`) done outside the frozen exe, which complicates a single-EXE distribution story | Poor fit for a "small installer, low idle RAM" app unless export is rare and the user accepts a large one-time download |
| **Reuse the already-present WebView2 via `PrintToPdfAsync`** | **Zero additional process** — reuses the browser/renderer process already resident for the main window; the print operation runs in-process | Zero extra disk footprint — the runtime is already installed system-wide (Evergreen) or already bundled | No extra bundling — no new binary to ship | **Best fit** for Trailmark: no new dependency, no new process tree, and the app already has a live `CoreWebView2` to call `PrintToPdfAsync`/`PrintToPdfStreamAsync` on. Constraint: pywebview does not expose this API directly — needs a small `clr`/pythonnet call into `self.webview.CoreWebView2.PrintToPdfAsync(...)` reached through pywebview's internal window handle, similar to the `MemoryUsageTargetLevel` integration in §2.C. Also: only one `PrintToPdf` operation may be in flight at a time per `CoreWebView2` (Microsoft docs), fine for a single-user desktop app doing occasional exports. |
| **WeasyPrint (pure Python)** | No browser process at all; pure-Python + Cairo/Pango rendering — Docker images cited at 200–400 MB, but that includes OS-level font/Cairo libraries, not WeasyPrint's own Python-process RSS, which is much smaller (no authoritative bare number found, **unverified**) | No Chromium; adds Cairo/Pango/GDK-Pixbuf native dependencies which do need Windows binary wheels (available via `weasyprint`'s Windows install docs/GTK runtime) | Bundles cleanly into PyInstaller relative to a full browser, but historically WeasyPrint-on-Windows has needed the GTK3 runtime DLLs available on `PATH` — a known packaging friction point, smaller than Playwright's but real | Good fallback: no extra process, modest native-dependency bundling cost, weaker CSS/JS fidelity than a real browser (no JS execution, partial modern-CSS support) |
| **Typst/Tectonic (single small binary)** | Single native binary, no browser, minimal RSS (**unverified** specific MB, but categorically in the tens-of-MB range typical of native Rust/LaTeX-engine CLI tools) | Small single executable, easy to bundle as a PyInstaller `--add-binary` | Cleanest bundling story of all four options | Best fit *if* Trailmark's HTML template system were instead a Typst/markup template system — but the prompt specifies an **HTML template system**, and Typst does not consume HTML/CSS, so adopting it means maintaining templates in two different markup systems (HTML for on-screen preview, Typst for print) — not recommended unless the HTML template requirement is dropped |

**Recommendation: primary = reuse WebView2's `PrintToPdfAsync` on the already-resident main
window; fallback = WeasyPrint** for any export path that must run when no webview window is
open (e.g., a future CLI/background export), or as a lighter-weight path if the pythonnet
`PrintToPdfAsync` integration proves too fragile with pywebview's WinForms backend. Do **not**
bundle Playwright/headless Chrome — it duplicates a browser engine Trailmark already ships via
WebView2, at real cost to installer size and idle-adjacent spike memory, for no fidelity gain
over reusing WebView2 directly.

Sources:
- [PDF4.dev — Playwright vs WeasyPrint PDF generation Python 2026](https://pdf4.dev/blog/playwright-vs-weasyprint)
- [Microsoft Learn — CoreWebView2.PrintToPdfAsync](https://learn.microsoft.com/en-us/dotnet/api/microsoft.web.webview2.core.corewebview2.printtopdfasync)
- [Microsoft Learn — Printing from WebView2 apps](https://learn.microsoft.com/en-us/microsoft-edge/webview2/how-to/print)

---

## 5. Ranked action list for Trailmark

### Do now — cheap, low risk

| # | Action | Est. MB saved | Effort | Risk |
|---|---|---|---|---|
| 1 | Move `import Pillow`/PIL usage and any future DOCX/PDF/LLM library imports inside the functions that use them instead of module top-level in `point_logger.py`/`llm.py` | A few MB resident + faster cold start | 1 hr | Low |
| 2 | Set `os.environ['WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS']` before `webview.start()` with a conservative flag set (start with nothing destructive, e.g. just confirm no flags are silently breaking anything, then trial `--disable-features=...` for unused Chromium features) | Unverified, likely single-digit MB per shared process | 2–3 hrs incl. testing | Medium (flags can subtly break rendering; verify visually) |
| 3 | Serve `logo.png`/`icon-96.png` via `file://` paths instead of inline base64 in `ui.py`'s HTML string constants, letting both windows share one decoded/cached copy | Low hundreds of KB, plus makes the upcoming HTML template system cleaner | 2–4 hrs (touches `ui.py`'s ~53 KB of embedded HTML) | Low |
| 4 | Confirm in Task Manager that both current windows really do share one `msedgewebview2.exe --type=browser` process (validates §2.B before investing further) | 0 (diagnostic only) | 15 min | None |
| 5 | Do **not** add `SetProcessWorkingSetSize`/`EmptyWorkingSet` trimming — actively skip this idea | Avoids a UX regression, not an addition | 0 | N/A — this is a "don't do" item |
| 6 | `gc.freeze()` right after the initial `points.json` load in `point_store.py` | ~0 MB (this is a GC-pause optimization, not a memory saver — include for correctness of understanding, low priority) | 30 min | Low |

### Medium-effort, real leverage

| # | Action | Est. MB saved | Effort | Risk |
|---|---|---|---|---|
| 7 | Reach into pywebview's underlying `CoreWebView2` (via `clr`) to call `MemoryUsageTargetLevel = Low` on the main window when hidden and `TrySuspendAsync()` on whichever window isn't frontmost | Unverified, plausibly tens of MB while the main window sits hidden | 1–2 days (undocumented integration point in pywebview, needs care around the exact crash class already fixed in commits `01d2acf`/`7d1a80a`) | Medium — touches the same cross-thread/WinForms surface that has crashed before |
| 8 | Use WebView2's `PrintToPdfAsync`/`PrintToPdfStreamAsync` for the incoming PDF export feature instead of bundling Playwright/headless Chrome | Avoids adding an entirely new ~550 MB Chromium dependency and its spike memory | 1–2 days (pythonnet call into `CoreWebView2`, same integration pattern as #7) | Medium |
| 9 | Prototype a native Win32/`pywin32` (or `tkinter`) replacement for the always-resident quick-capture popup, keeping WebView2 only for the main window | Removes one permanently-resident renderer process — the single largest concrete, attributable saving identified in this research | 1–3 days for the popup specifically (it's a small, bounded form UI) | Medium — UI must be re-implemented natively; loses shared CSS with the main window's design system |

### Only if you rewrite (not recommended purely for memory)

| # | Action | Est. MB saved | Effort | Risk |
|---|---|---|---|---|
| 10 | Full rewrite to Tauri v2 / WinUI3 / Wails | Host-process savings only (tens of MB) — the WebView2 floor itself does not change on Windows | 1–4 weeks | High — full rewrite of a working app, for a benefit smaller than commonly advertised because Windows builds of these frameworks also ride WebView2 |
| 11 | Bundle WeasyPrint as a second export path (pure-Python PDF fallback) | Avoids any browser-engine dependency for export entirely | 3–5 days (Windows native-dependency packaging for Cairo/Pango/GTK) | Medium — packaging friction on Windows is real and documented |

**Bottom line:** the two changes with the best evidence-to-effort ratio are (a) confirming and
then not disturbing the already-shared WebView2 browser process, and (b) making the
quick-capture popup — the part of Trailmark that is genuinely resident all day — native Win32
instead of WebView2-backed. Everything else (flags, working-set trimming, framework rewrites) is
either low-yield, actively counterproductive, or disproportionate in effort for a solo
maintainer of a working app.
