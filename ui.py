BASE_CSS = """
/* Trailmark design tokens.

   Dark is the brand default - the app launches into it and the amber blaze
   reads correctly against near-black. Light is a designed warm-parchment
   theme, not an inversion, because a research tool is used in daylight at
   least as often as at night.

   The accent changes weight per surface: #f0a94a on parchment only reaches
   3.63:1, which fails AA for text, so light uses a deeper #a15716 from the
   same hue family (4.80:1 as text, 5.12:1 as a fill).

   Three states, per the theme contract: bare :root is dark; the media query
   flips to light when Windows says so; [data-theme] overrides either way, so
   the Settings toggle wins in both directions.
*/
:root{
  --ink-950:#0b0f16; --ink-900:#0e131c; --ink-850:#141b26; --ink-800:#1b2330;
  --ink-050:#eef1f6; --fog-400:#97a2b5; --fog-600:#6b7385;
  --paper-000:#fffdf9; --paper-050:#f6f1e8; --paper-100:#efe8da; --paper-200:#f1ebdf;
  --char-900:#201a12; --char-600:#6b6150; --char-400:#8f8571;
  --blaze-300:#ffbb66; --blaze-500:#f0a94a; --blaze-700:#a15716; --blaze-900:#7d420c;
  --moss-300:#8ce0c8; --moss-400:#6fcbb0; --moss-600:#2f7d64; --moss-700:#256051;
  --danger-300:#ff8f8f; --danger-400:#ff6b6b; --danger-600:#d94848; --danger-700:#c23b3b;

  --surface:var(--ink-950); --surface-2:var(--ink-900);
  --surface-raised:var(--ink-850); --surface-sunken:var(--ink-800);
  --content:var(--ink-050); --content-secondary:var(--fog-400); --content-muted:var(--fog-600);
  --border:rgba(255,255,255,.12); --border-strong:rgba(255,255,255,.24);
  --accent:var(--blaze-500); --accent-hover:var(--blaze-300);
  --accent-content:#1c1206; --accent-tint:rgba(240,169,74,.16);
  --secondary:var(--moss-400); --secondary-tint:rgba(111,203,176,.16); --success:var(--moss-400);
  --danger:var(--danger-400); --danger-hover:var(--danger-300); --danger-tint:rgba(255,107,107,.15);
  --focus-ring:var(--blaze-500); --scrim:rgba(5,7,11,.55);

  --shadow-1:0 1px 2px rgba(0,0,0,.4);
  --shadow-2:0 8px 24px rgba(0,0,0,.32), inset 0 1px 0 rgba(255,255,255,.06);
  --shadow-3:0 16px 48px rgba(0,0,0,.48), inset 0 1px 0 rgba(255,255,255,.08);

  --dur-fast:100ms; --dur-mid:180ms; --dur-slow:260ms;
  --ease-standard:cubic-bezier(.2,.8,.2,1); --ease-entrance:cubic-bezier(.16,1,.3,1);
  --font-ui:"Segoe UI Variable Text","Segoe UI",system-ui,-apple-system,sans-serif;
  --font-display:"Segoe UI Variable Display","Segoe UI Semibold","Segoe UI",system-ui,sans-serif;
  --font-mono:"Cascadia Code","Cascadia Mono",ui-monospace,Consolas,monospace;

  /* the scales, straight from the design system - components size themselves
     from these rather than from ad-hoc pixel values */
  --sp-1:4px; --sp-2:8px; --sp-3:12px; --sp-4:16px; --sp-5:20px;
  --sp-6:24px; --sp-7:32px; --sp-8:40px; --sp-9:56px;
  --r-sm:8px; --r-md:12px; --r-lg:16px; --r-xl:20px; --r-pill:999px;
  --control-h:36px; --tap-target:44px;

  /* the one translucent surface each window is allowed - see .glass below */
  --glass:rgba(255,255,255,.06);
  color-scheme:dark;
}
@media (prefers-color-scheme:light){
  :root:not([data-theme="dark"]){
    --surface:var(--paper-050); --surface-2:var(--paper-100);
    --surface-raised:var(--paper-000); --surface-sunken:var(--paper-200);
    --content:var(--char-900); --content-secondary:var(--char-600); --content-muted:var(--char-400);
    --border:rgba(32,26,18,.12); --border-strong:rgba(32,26,18,.30);
    --accent:var(--blaze-700); --accent-hover:var(--blaze-900);
    --accent-content:#fff8ef; --accent-tint:rgba(161,87,22,.12);
    --secondary:var(--moss-700); --secondary-tint:rgba(37,96,81,.12); --success:var(--moss-700);
    --danger:var(--danger-700); --danger-hover:#9c2e2e; --danger-tint:rgba(194,59,59,.12);
    --focus-ring:var(--blaze-700); --scrim:rgba(32,26,18,.35);
    --shadow-1:0 1px 2px rgba(32,26,18,.08);
    --shadow-2:0 8px 24px rgba(32,26,18,.10), inset 0 1px 0 rgba(255,255,255,.6);
    --shadow-3:0 20px 48px rgba(32,26,18,.16), inset 0 1px 0 rgba(255,255,255,.7);
    --glass:rgba(255,253,249,.62);
    color-scheme:light;
  }
}
:root[data-theme="light"]{
  --surface:var(--paper-050); --surface-2:var(--paper-100);
  --surface-raised:var(--paper-000); --surface-sunken:var(--paper-200);
  --content:var(--char-900); --content-secondary:var(--char-600); --content-muted:var(--char-400);
  --border:rgba(32,26,18,.12); --border-strong:rgba(32,26,18,.30);
  --accent:var(--blaze-700); --accent-hover:var(--blaze-900);
  --accent-content:#fff8ef; --accent-tint:rgba(161,87,22,.12);
  --secondary:var(--moss-700); --secondary-tint:rgba(37,96,81,.12); --success:var(--moss-700);
  --danger:var(--danger-700); --danger-hover:#9c2e2e; --danger-tint:rgba(194,59,59,.12);
  --focus-ring:var(--blaze-700); --scrim:rgba(32,26,18,.35);
  --shadow-1:0 1px 2px rgba(32,26,18,.08);
  --shadow-2:0 8px 24px rgba(32,26,18,.10), inset 0 1px 0 rgba(255,255,255,.6);
  --shadow-3:0 20px 48px rgba(32,26,18,.16), inset 0 1px 0 rgba(255,255,255,.7);
  --glass:rgba(255,253,249,.62);
  color-scheme:light;
}
:root[data-theme="dark"]{
  --surface:var(--ink-950); --surface-2:var(--ink-900);
  --surface-raised:var(--ink-850); --surface-sunken:var(--ink-800);
  --content:var(--ink-050); --content-secondary:var(--fog-400); --content-muted:var(--fog-600);
  --border:rgba(255,255,255,.12); --border-strong:rgba(255,255,255,.24);
  --accent:var(--blaze-500); --accent-hover:var(--blaze-300);
  --accent-content:#1c1206; --accent-tint:rgba(240,169,74,.16);
  --secondary:var(--moss-400); --secondary-tint:rgba(111,203,176,.16); --success:var(--moss-400);
  --danger:var(--danger-400); --danger-hover:var(--danger-300); --danger-tint:rgba(255,107,107,.15);
  --focus-ring:var(--blaze-500); --scrim:rgba(5,7,11,.55);
  --shadow-1:0 1px 2px rgba(0,0,0,.4);
  --shadow-2:0 8px 24px rgba(0,0,0,.32), inset 0 1px 0 rgba(255,255,255,.06);
  --shadow-3:0 16px 48px rgba(0,0,0,.48), inset 0 1px 0 rgba(255,255,255,.08);
  --glass:rgba(255,255,255,.06);
  color-scheme:dark;
}
*{box-sizing:border-box}
[hidden]{display:none !important}
html,body{height:100%;margin:0}
body{
  font-family:var(--font-ui);
  color:var(--content);
  /* Flat, as app/main-window.html paints it. Depth in this design comes from
     the raised card surfaces and the one blurred panel, not from an ambient
     gradient - and a flat colour cannot be reset to transparent by a later
     background shorthand, which is how the window ended up see-through once. */
  background-color:var(--surface);
  overflow:hidden;
  -webkit-font-smoothing:antialiased;
}
/* Glass is rationed, not removed: one blurred layer at a time, 12px ceiling.
   backdrop-filter is a real per-frame compositing cost in WebView2, and in
   light mode shadow and opacity already read as depth, so the blur is dropped
   there entirely. */
.glass{
  background:var(--surface-raised);
  border:1px solid var(--border);
  border-radius:var(--r-lg);
  box-shadow:var(--shadow-1);
}
/* the single blurred surface per window: the sidebar in the main window, the
   header strip in the popup. Never a scrolling container, never a card. */
aside.glass, header.glass{
  background:var(--glass);
  backdrop-filter:blur(12px) saturate(120%);
  -webkit-backdrop-filter:blur(12px) saturate(120%);
  border:1px solid var(--border);
  box-shadow:var(--shadow-2);
}
:root[data-theme="light"] aside.glass,
:root[data-theme="light"] header.glass{backdrop-filter:none;-webkit-backdrop-filter:none}
@media (prefers-color-scheme:light){
  :root:not([data-theme="dark"]) aside.glass,
  :root:not([data-theme="dark"]) header.glass{backdrop-filter:none;-webkit-backdrop-filter:none}
}
::-webkit-scrollbar{width:9px;height:9px}
::-webkit-scrollbar-thumb{background:var(--border-strong);border-radius:var(--r-sm)}
::-webkit-scrollbar-track{background:transparent}
:focus-visible{outline:2px solid var(--focus-ring);outline-offset:2px}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:7px;border:0;
  border-radius:var(--r-md);padding:10px 16px;font-family:inherit;font-size:13.5px;
  font-weight:600;cursor:pointer;min-height:var(--control-h);
  transition:transform var(--dur-fast) var(--ease-standard),
             background var(--dur-fast) var(--ease-standard),
             border-color var(--dur-fast) var(--ease-standard);
  color:var(--content);background:var(--surface-sunken)}
.btn:hover{transform:translateY(-1px)}
.btn:active{transform:translateY(0)}
.btn.primary{background:var(--accent);color:var(--accent-content);box-shadow:var(--shadow-1)}
.btn.primary:hover{background:var(--accent-hover)}
.btn.ghost{background:transparent;border:1px solid var(--border)}
.btn.ghost:hover{border-color:var(--border-strong)}
.btn.danger{background:var(--danger-tint);color:var(--danger);border:1px solid transparent}
.btn.danger:hover{background:var(--danger);color:var(--accent-content)}
.btn.sm{padding:6px 12px;font-size:12.5px;border-radius:var(--r-sm);min-height:0}
.btn.full{width:100%}
.input,select.input{width:100%;background:var(--surface-sunken);border:1px solid var(--border);
  border-radius:var(--r-md);padding:10px 12px;color:var(--content);font-family:inherit;
  font-size:13.5px;outline:none;
  transition:border-color var(--dur-fast),box-shadow var(--dur-fast)}
.input:focus{border-color:var(--focus-ring);box-shadow:0 0 0 3px var(--accent-tint)}
.ta{resize:vertical;line-height:1.5}
label{display:flex;flex-direction:column;gap:6px;font-size:11px;font-weight:600;
  color:var(--content-muted);letter-spacing:.03em;text-transform:uppercase}
label .input{font-weight:400;text-transform:none;letter-spacing:normal}
label .muted{text-transform:none;letter-spacing:normal;font-weight:400}
.grid2>label,.grid3>label{height:100%;justify-content:flex-end}
label.mod,label.chip,label.fmt-opt,label.tpl{text-transform:none;letter-spacing:normal;
  font-size:13px;font-weight:600;color:var(--content)}
label.mod .muted{font-weight:400}
.chip{padding:6px 12px;border:1px solid var(--border);border-radius:var(--r-md);
  background:transparent;color:var(--content-secondary);font-family:inherit;font-size:12.5px;
  font-weight:600;cursor:pointer;transition:.14s;white-space:nowrap}
.chip:hover{color:var(--content);border-color:var(--border-strong)}
.chip.active{background:var(--accent-tint);color:var(--content);border-color:var(--accent)}
.chip.accent{background:var(--accent-tint);border-color:var(--accent);color:var(--accent)}
.chip.add{background:transparent;border-color:var(--accent);color:var(--accent);border-style:dashed}
.chips{display:flex;gap:6px;flex-wrap:wrap;align-items:center}
.muted{color:var(--content-secondary);font-size:12.5px;line-height:1.5}
#toasts{position:fixed;bottom:18px;left:50%;transform:translateX(-50%);display:flex;flex-direction:column;
  gap:8px;z-index:80;align-items:center;pointer-events:none}
.toast{display:flex;flex-direction:column;padding:10px 16px;border-radius:var(--r-md);
  background:var(--surface-raised);border:1px solid var(--border-strong);
  color:var(--content);font-size:12.5px;box-shadow:var(--shadow-3);
  transition:var(--dur-slow) var(--ease-standard);max-width:340px;pointer-events:auto}
.toast .muted{color:var(--content-secondary)}
.toast.wide{max-width:520px}
.toast .t-links{margin-top:6px;display:flex;flex-wrap:wrap;gap:2px;align-items:center}
.toast .t-links a{color:var(--accent);text-decoration:none;font-weight:600}
.toast .t-links a:hover{text-decoration:underline}
.toast .t-warn{margin-top:7px;padding-top:7px;border-top:1px solid var(--border);
  color:var(--accent);font-size:11.5px;line-height:1.45}
.toast.err{border-color:var(--danger);color:var(--danger)}
.toast.out{opacity:0;transform:translateY(8px)}
.fade{animation:fade .2s var(--ease-entrance)}
@keyframes fade{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
/* --- scientific mode: a point is a claim, a note, or a quotation --------- */
.kinds{display:flex;gap:3px;background:var(--surface-sunken);border:1px solid var(--border);
  border-radius:var(--r-md);padding:3px;min-width:250px}
.kinds .k{flex:1;border:0;background:transparent;color:var(--content-secondary);font:inherit;
  font-size:11.5px;font-weight:600;padding:7px 8px;border-radius:9px;cursor:pointer;
  white-space:nowrap;transition:background .14s,color .14s}
.kinds .k:hover{color:var(--content)}
.kinds .k.on{background:var(--surface-raised);color:var(--content);box-shadow:var(--shadow-1)}
.k-hint{font-size:11px;color:var(--content-muted);margin-top:6px;text-transform:none;
  letter-spacing:0;font-weight:400}
.badge.kind{font-weight:700;letter-spacing:.04em;text-transform:uppercase;font-size:9.5px}
.src-descs{display:flex;flex-wrap:wrap;gap:6px;margin-top:7px}
.src-desc{border:0;background:var(--surface-sunken);color:var(--content-secondary);font:inherit;
  font-size:11px;padding:4px 10px;border-radius:var(--r-pill);cursor:pointer;
  transition:background .14s,color .14s}
.src-desc:hover{background:var(--accent-tint);color:var(--accent)}
.src-desc.has{color:var(--accent)}
.meta-form{margin-top:10px;padding:var(--sp-3);border:1px solid var(--border);
  border-radius:var(--r-md);background:var(--surface-sunken)}
.meta-form .mf-t{font-weight:600;font-size:12.5px;margin-bottom:2px}
.meta-form .mf-s{font-size:11px;color:var(--content-secondary);margin-bottom:10px;line-height:1.5}
.meta-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px}
.meta-grid label{display:flex;flex-direction:column;gap:3px;font-size:10.5px;
  color:var(--content-muted)}
.meta-grid .input{font-size:12px;padding:6px 8px}
.meta-form .row{margin-top:10px}

/* --- clipboard capture: popup paste buttons, thumb chip, rich toast, hotkey switch (T10/T11) --- */
.paste-btn{flex:none;width:28px;height:28px;border:0;background:transparent;color:var(--content-secondary);
  border-radius:var(--r-sm);display:flex;align-items:center;justify-content:center;cursor:pointer}
.paste-btn:hover{color:var(--accent);background:var(--accent-tint)}
.paste-btn svg{width:15px;height:15px}
.thumb-chip{flex:1;display:flex;align-items:center;gap:8px;min-width:0;background:var(--surface-2);
  border:1px solid var(--border);border-radius:var(--r-sm);padding:5px 8px}
/* scoped to .thumb-chip so this doesn't collide with the unrelated bare .thumb
   (a 64x64 <img> thumbnail) already used elsewhere in the app's own style block */
.thumb-chip .thumb{flex:none;width:32px;height:32px;border-radius:var(--r-sm);
  background:linear-gradient(135deg, var(--accent-tint), var(--secondary-tint));
  border:1px solid var(--border);display:flex;align-items:center;justify-content:center}
.thumb-chip .thumb svg{width:15px;height:15px;stroke:var(--accent)}
.thumb-chip .thumb-meta{min-width:0;flex:1}
.thumb-chip .thumb-meta .fn{font:600 12px var(--font-ui);color:var(--content);white-space:nowrap;
  overflow:hidden;text-overflow:ellipsis}
.thumb-chip .thumb-meta .fs{font:11px var(--font-ui);color:var(--content-muted)}
.xbtn{flex:none;width:20px;height:20px;border:0;background:var(--surface-2);color:var(--content-muted);
  border-radius:50%;display:flex;align-items:center;justify-content:center;cursor:pointer}
.xbtn:hover{color:var(--danger);background:var(--danger-tint)}
.xbtn svg{width:10px;height:10px}

/* the rich "logged from clipboard" toast - deliberately NOT .toast (see report) */
.cbtoast{width:320px;max-width:calc(100vw - 32px);background:var(--surface-raised);
  border:1px solid var(--border-strong);border-radius:var(--r-md);box-shadow:var(--shadow-3);
  padding:13px 14px 0;overflow:hidden;pointer-events:auto;transition:var(--dur-slow) var(--ease-standard)}
.cbtoast.out{opacity:0;transform:translateY(8px)}
.cbtoast .row1{display:flex;align-items:flex-start;gap:10px}
.cbtoast .ic{flex:none;width:26px;height:26px;border-radius:7px;background:var(--accent-tint);
  display:flex;align-items:center;justify-content:center;margin-top:1px}
.cbtoast .ic svg{width:14px;height:14px;stroke:var(--accent)}
.cbtoast .txt{flex:1;min-width:0}
.cbtoast .txt b{display:block;font:700 13px var(--font-display);color:var(--content)}
.cbtoast .txt span{display:block;font:11.5px var(--font-ui);color:var(--content-secondary);margin-top:2px}
.cbtoast .undo{flex:none;border:0;background:transparent;color:var(--accent);font:700 12px var(--font-ui);
  cursor:pointer;padding:2px 0}
.cbtoast .prog{height:2px;background:var(--border);margin-top:12px;position:relative}
.cbtoast .prog i{position:absolute;left:0;top:0;bottom:0;background:var(--accent);width:100%;
  display:block;transition:width 4s linear}

/* Settings -> Hotkeys: static key chips + on/off pill switch for the clipboard hotkey */
.key{background:var(--surface-sunken);border:1px solid var(--border);border-radius:var(--r-sm);
  padding:8px 12px;font:700 12px var(--font-mono)}
.plus{color:var(--content-muted);font:12px var(--font-ui)}
.sw{width:36px;height:21px;border-radius:999px;background:var(--surface-sunken);border:1px solid var(--border);
  position:relative;flex:none;cursor:pointer;padding:0;transition:background .14s var(--ease-standard)}
.sw.on{background:var(--accent);border-color:var(--accent)}
.sw .kn{position:absolute;top:2px;left:2px;width:15px;height:15px;border-radius:50%;
  background:var(--surface-raised);transition:transform .14s var(--ease-standard)}
.sw.on .kn{transform:translateX(15px);background:var(--accent-content)}

"""

POPUP_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Trailmark · Quick capture</title><style>
__BASE_CSS__
header,button,label{user-select:none}
.win{display:flex;flex-direction:column;height:100vh;padding:12px;gap:10px}
header{display:flex;align-items:center;gap:9px;padding:9px 12px}
header img{width:auto;height:26px;object-fit:contain}
.tt{min-width:0;flex:1}
.app{font-weight:650;font-size:13.5px;letter-spacing:.2px}
.hk{font-size:10.5px;color:var(--content-secondary)}
.pulse{flex:none;width:7px;height:7px;border-radius:50%;background:var(--accent);
  box-shadow:0 0 0 3px var(--accent-tint);animation:pulse 2s ease-in-out infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.45}}
section{overflow-y:auto;flex:1}
.card{padding:14px;display:flex;flex-direction:column;gap:9px}
.big{font-size:17px;font-weight:700}
.trow{display:flex;gap:8px;align-items:center}
.srcbar{display:flex;gap:7px}
.attrow{display:flex;gap:7px;align-items:center;flex-wrap:wrap}
.logrow{display:flex;gap:9px;margin-top:2px}
.logrow .btn.primary{flex:1}
.hint{font-size:11px;color:var(--content-muted);text-align:center;letter-spacing:.03em}
.recent{font-size:11.5px;color:var(--content-secondary);border-top:1px solid var(--border);
  padding-top:8px;margin-top:2px}
.recent b{color:var(--content);font-weight:600}
</style></head><body>
<div class="win">
  <header class="glass pywebview-drag-region">
    <img src="__ICON__" alt="">
    <div class="tt"><div class="app">Trailmark</div><div class="hk" id="hkLabel"></div></div>
    <button id="openApp" class="chip accent" title="Open the main window">Open app</button>
    <div class="pulse" id="liveDot"></div>
  </header>

  <section id="noTopic" hidden>
    <div class="card glass fade">
      <div class="big">Start a topic</div>
      <p class="muted">No open topic yet. Give this research a name to begin.</p>
      <input id="ntTitle" class="input" placeholder="Topic name — e.g. Rust borrow checker">
      <button id="ntGo" class="btn primary full">Start topic</button>
    </div>
  </section>

  <section id="logPanel" hidden>
    <div class="card glass fade">
      <div class="trow">
        <select id="tpSel" class="input"></select>
        <button id="tpNew" class="chip">+ New</button>
      </div>
      <label>Sub-topic</label>
      <div class="chips" id="subChips"></div>
      <div id="ptKinds" hidden>
        <label>This point is</label>
        <div class="kinds">
          <button class="k on" data-kind="claim">Claim</button>
          <button class="k" data-kind="note">My note</button>
          <button class="k" data-kind="quote">Quotation</button>
        </div>
        <div class="k-hint" id="ptKindHint"></div>
      </div>
      <label>Point</label>
      <textarea id="ptText" class="input ta" rows="3" placeholder="Type or paste the point…" spellcheck="false"></textarea>
      <div class="srcbar">
        <input id="ptLink" class="input grow" placeholder="Paste a source link…">
        <button id="ptLinkAdd" class="chip">+ Link</button>
        <button id="ptLinkPaste" class="paste-btn" type="button" aria-label="Paste link from clipboard"><svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="3" width="10" height="3" rx="1"/><path d="M6 4H4.5A1.5 1.5 0 0 0 3 5.5v11A1.5 1.5 0 0 0 4.5 18h11a1.5 1.5 0 0 0 1.5-1.5v-11A1.5 1.5 0 0 0 15.5 4H14"/></svg></button>
      </div>
      <div class="srcbar">
        <input id="ptStr" class="input grow" placeholder="Or a string citation…">
        <button id="ptStrAdd" class="chip">+ String</button>
        <button id="ptStrPaste" class="paste-btn" type="button" aria-label="Paste text from clipboard"><svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="3" width="10" height="3" rx="1"/><path d="M6 4H4.5A1.5 1.5 0 0 0 3 5.5v11A1.5 1.5 0 0 0 4.5 18h11a1.5 1.5 0 0 0 1.5-1.5v-11A1.5 1.5 0 0 0 15.5 4H14"/></svg></button>
      </div>
      <div class="attrow">
        <label class="chip">+ Screenshot<input id="ptShot" type="file" accept="image/*" hidden></label>
        <button id="ptImgPaste" class="paste-btn" type="button" aria-label="Paste image from clipboard"><svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="3" width="10" height="3" rx="1"/><path d="M6 4H4.5A1.5 1.5 0 0 0 3 5.5v11A1.5 1.5 0 0 0 4.5 18h11a1.5 1.5 0 0 0 1.5-1.5v-11A1.5 1.5 0 0 0 15.5 4H14"/></svg></button>
        <div id="attChips" class="chips"></div>
      </div>
      <div class="logrow">
        <button id="ptGo" class="btn primary">Log point</button>
        <button id="ptHide" class="btn ghost">Hide</button>
      </div>
      <div class="hint">Alt+Enter logs · Esc hides · hotkey toggles · Open app to review</div>
      <div class="recent" id="recent"></div>
    </div>
  </section>
</div>
<div id="toasts"></div>
<script>
let state={topics:[]};
let topicId=null, subTopic="";
let pLinks=[], pStrings=[], pImages=[];
let pKind="claim";
const KIND_HINT={
  claim:"Taken from a source. It carries the citation.",
  note:"Your own thinking. It is kept separate and never given a citation - not even by the AI pass.",
  quote:"Verbatim from the source. Nothing, including the AI pass, may reword it."
};
const sciOn=()=>!!((state.config||{}).science||{}).enabled;
let lastTopicId=null;
const api=new Proxy({},{get:(_,p)=>{const pv=window.pywebview&&window.pywebview.api;return pv?pv[p]:(()=>Promise.resolve({error:"bridge not ready"}));}});

const $=(s,r=document)=>r.querySelector(s);
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const toast=(m,t="ok")=>{const d=document.createElement("div");d.className="toast "+t;d.textContent=m;
  document.getElementById("toasts").appendChild(d);setTimeout(()=>d.classList.add("out"),2200);setTimeout(()=>d.remove(),2600);};
const byId=i=>state.topics.find(t=>t.id===i);
const openTopics=()=>state.topics.filter(t=>t.status==="open");
const fmtTime=iso=>{if(!iso)return"";const d=new Date(iso);return d.toLocaleString(undefined,{day:"2-digit",month:"short",hour:"2-digit",minute:"2-digit"});};

// Called from Python via evaluate_js("clipboardToast(...)") when the Ctrl+Alt+V
// hotkey auto-detects and logs a clipboard source. Deliberately its own .cbtoast
// element, not the plain toast() above - see report for why. `tid` is a 4th
// argument beyond the original 3-arg contract; see the handback in the report.
const CB_ICONS={
  link:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M8 12a3 3 0 0 0 4.24 0l2-2a3 3 0 0 0-4.24-4.24l-1 1"/><path d="M12 8a3 3 0 0 0-4.24 0l-2 2a3 3 0 0 0 4.24 4.24l1-1"/></svg>',
  image:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="14" height="12" rx="2"/><circle cx="7.5" cy="9" r="1.2"/><path d="M17 13l-4-4-7 7"/></svg>',
  text:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5h12M4 9h12M4 13h8"/></svg>'
};
function clipboardToast(kind,detailText,entryId,tid){
  const d=document.createElement("div");
  d.className="cbtoast fade";
  const headline=kind==="error"?"Couldn't log from clipboard":"Logged from clipboard";
  d.innerHTML=`<div class="row1"><div class="ic">${CB_ICONS[kind]||CB_ICONS.text}</div>
    <div class="txt"><b>${headline}</b><span></span></div>
    ${entryId==null?"":'<button class="undo" type="button">Undo</button>'}</div>
    <div class="prog"><i></i></div>`;
  d.querySelector(".txt span").textContent=detailText; // untrusted, pre-formatted - textContent only
  document.getElementById("toasts").appendChild(d);
  const bar=d.querySelector(".prog i");
  requestAnimationFrame(()=>{bar.style.width="0%";});
  function dismiss(){d.classList.add("out");setTimeout(()=>d.remove(),280);}
  const timer=setTimeout(dismiss,4000);
  const undoBtn=d.querySelector(".undo");
  if(undoBtn) undoBtn.addEventListener("click",async()=>{
    clearTimeout(timer);
    const r=await api.delete_entry(tid,entryId);
    if(r&&r.error){toast(r.error,"err");return;}
    state=r;renderMode();
    dismiss();
  });
}

function renderMode(){
  const opens=openTopics();
  const no=$("#noTopic"), log=$("#logPanel");
  if(!opens.length){
    no.hidden=false;log.hidden=true;return;
  }
  no.hidden=true;log.hidden=false;
  const kw=$("#ptKinds");
  if(kw){
    kw.hidden=!sciOn();
    kw.querySelectorAll(".k").forEach(b=>b.classList.toggle("on",b.dataset.kind===pKind));
    $("#ptKindHint").textContent=KIND_HINT[pKind]||"";
  }
  if(!topicId||!byId(topicId))topicId=lastTopicId&&byId(lastTopicId)?lastTopicId:opens[0].id;
  const sel=$("#tpSel");
  sel.innerHTML=opens.map(t=>`<option value="${t.id}">${esc(t.title)}</option>`).join("");
  sel.value=topicId;
  renderSubs();
}

function renderSubs(){
  const t=byId(topicId);if(!t)return;
  const wrap=$("#subChips");
  const subs=[...(t.subtopics||[])];
  const chips=subs.map(s=>`<button class="chip ${subTopic===s?"active":""}" data-s="${esc(s)}">${esc(s)}</button>`).join("");
  wrap.innerHTML=`<button class="chip ${subTopic===""?"active":""}" data-s="">General</button>${chips}
    <button class="chip accent" id="subAdd">+ add</button>`;
  wrap.querySelectorAll("button[data-s]").forEach(b=>b.addEventListener("click",()=>{subTopic=b.dataset.s;renderSubs();}));
  $("#subAdd").addEventListener("click",()=>{
    const name=prompt("New sub-topic name:");
    if(!name||!name.trim())return;
    addSub(name);
  });
}

function addSub(name){
  api.add_subtopic(topicId,name).then(r=>{if(r.error)return toast(r.error,"err");state=r;renderSubs();});
}

async function logPoint(){
  const text=$("#ptText").value;
  if(!text.trim()){toast("Write the point first.","err");$("#ptText").focus();return;}
  const sources=[];
  pLinks.forEach(v=>sources.push({type:"link",value:v}));
  pStrings.forEach(v=>sources.push({type:"string",value:v}));
  pImages.forEach(v=>sources.push({type:"image",value:v.value}));
  const r=await api.add_entry(topicId,subTopic,text,"","",null,sources,pKind);
  if(r.error){toast(r.error,"err");return;}
  state=r;lastTopicId=topicId;
  $("#ptText").value="";$("#ptLink").value="";$("#ptStr").value="";pLinks=[];pStrings=[];pImages=[];
  renderAtt();
  const t=state.topics.find(t=>t.id===topicId);
  $("#recent").innerHTML="<b>Logged</b> · "+fmtTime(t.entries.at(-1).created)+
    (subTopic?" · "+esc(subTopic):"")+" · "+(t.entries.length)+" point(s) total";
  toast("Point logged — "+sources.length+" source(s) attached.");
  $("#ptText").focus();
}

function renderAtt(){
  const wrap=$("#attChips");const parts=[];
  pLinks.forEach((v,i)=>parts.push(`<span class="chip active" data-rm="link-${i}" title="${esc(v)}">🔗 ${esc(v.slice(0,22))} ×</span>`));
  pStrings.forEach((v,i)=>parts.push(`<span class="chip active" data-rm="str-${i}" title="${esc(v)}">“ ${esc(v.slice(0,18))} ×</span>`));
  // Clipboard-pasted images have no File object, so there's no real filename or
  // size to show - the label instead reflects which control produced the image
  // (paste vs. file-picker), tracked via img.source.
  pImages.forEach((img,i)=>{const label=img.source==="paste"?"Pasted image":"Screenshot";parts.push(`<span class="thumb-chip">
    <span class="thumb"><svg viewBox="0 0 24 24" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="8.5" cy="10" r="1.5"/><path d="M21 16l-5-5-9 9"/></svg></span>
    <span class="thumb-meta"><span class="fn">${label}</span></span>
    <button class="xbtn" data-rm="img-${i}" type="button" aria-label="Remove image"><svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M5 5l10 10M15 5L5 15"/></svg></button>
  </span>`);});
  wrap.innerHTML=parts.join("")||`<span class="muted" style="font-size:11.5px">add links, strings or screenshots — all will be cited</span>`;
  wrap.querySelectorAll("[data-rm]").forEach(el=>el.addEventListener("click",()=>{
    const k=el.dataset.rm;
    if(k.startsWith("link-")) pLinks.splice(parseInt(k.split("-")[1]),1);
    if(k.startsWith("str-")) pStrings.splice(parseInt(k.split("-")[1]),1);
    if(k.startsWith("img-")) pImages.splice(parseInt(k.split("-")[1]),1);
    renderAtt();
  }));
}

$("#ntGo").addEventListener("click",async()=>{
  const title=$("#ntTitle").value;
  const r=await api.start_topic(title);
  if(r.error)return toast(r.error,"err");
  state=r;topicId=r.topics.find(t=>t.status==="open").id;lastTopicId=topicId;
  renderMode();$("#ptText").focus();
});
$("#ntTitle").addEventListener("keydown",e=>{if(e.key==="Enter")$("#ntGo").click();});
$("#tpSel").addEventListener("change",e=>{topicId=e.target.value;lastTopicId=topicId;subTopic="";renderSubs();});
$("#tpNew").addEventListener("click",()=>{topicId=null;$("#noTopic").hidden=false;$("#logPanel").hidden=true;$("#ntTitle").value="";$("#ntTitle").focus();});
$("#ptLinkAdd").addEventListener("click",()=>{
  const v=$("#ptLink").value.trim();if(!v)return;
  try{new URL(v);}catch(e){toast("That doesn't look like a URL.","err");return;}
  pLinks.push(v);$("#ptLink").value="";renderAtt();toast("Link added ("+pLinks.length+").");
});
$("#ptStrAdd").addEventListener("click",()=>{
  const v=$("#ptStr").value.trim();if(!v)return;
  pStrings.push(v);$("#ptStr").value="";renderAtt();toast("Citation added ("+pStrings.length+").");
});
$("#ptLink").addEventListener("keydown",e=>{if(e.key==="Enter")$("#ptLinkAdd").click();});
$("#ptStr").addEventListener("keydown",e=>{if(e.key==="Enter")$("#ptStrAdd").click();});
$("#ptImgPaste").addEventListener("click",async()=>{
  const d=await api.read_clipboard();
  if(d.type==="image"){pImages.push({value:d.value,source:"paste"});renderAtt();toast("Image pasted from clipboard.");}
  else{toast("Clipboard has no image.","err");}
});
$("#ptLinkPaste").addEventListener("click",async()=>{
  const d=await api.read_clipboard();
  if(d.type==="link"){$("#ptLink").value=d.value;}
  else if(d.type==="text"){toast("Clipboard text is not a URL.","err");}
  else if(d.type==="image"){toast("Clipboard has an image, not a link.","err");}
  else{toast("Clipboard is empty.","err");}
});
$("#ptStrPaste").addEventListener("click",async()=>{
  const d=await api.read_clipboard();
  if(d.type==="text"||d.type==="link"){$("#ptStr").value=d.value;}
  else if(d.type==="image"){toast("Clipboard has an image, not text.","err");}
  else{toast("Clipboard is empty.","err");}
});
$("#ptShot").addEventListener("change",e=>{
  const files=[...e.target.files]; if(!files.length) return;
  let pending=files.length;
  files.forEach(f=>{
    if(f.size>8*1024*1024){toast("Image too large (8 MB max).","err"); pending--; if(!pending) renderAtt(); return;}
    const rd=new FileReader();
    rd.onload=()=>{pImages.push({value:rd.result,source:"file"}); renderAtt(); toast("Screenshot attached ("+pImages.length+").");};
    rd.readAsDataURL(f);
  });
  e.target.value="";
});
const ptKinds=$("#ptKinds");
if(ptKinds) ptKinds.addEventListener("click",e=>{
  const b=e.target.closest("[data-kind]"); if(!b) return;
  pKind=b.dataset.kind; renderMode();
});
$("#ptGo").addEventListener("click",logPoint);
$("#ptText").addEventListener("keydown",e=>{
  if(e.altKey && e.key==="Enter"){e.preventDefault();logPoint();}
});
$("#openApp").addEventListener("click",async()=>{
  $("#openApp").textContent="Opening…";
  try{
    const r=await api.show_full();
    if(r && r.error) toast(r.error,"err");
  }catch(e){ /* bridge not ready, try fallback */ }
  setTimeout(()=>$("#openApp").textContent="Open app",900);
});
$("#ptHide").addEventListener("click",()=>api.hide_popup());
document.addEventListener("keydown",e=>{if(e.key==="Escape")api.hide_popup();});
document.addEventListener("wheel",e=>{if(e.ctrlKey)e.preventDefault();},{passive:false});

function boot(){
  api.get_state().then(r=>{
    state=r;
    const cfg=r.config||{};
    applyTheme((cfg.appearance||{}).theme||"system");
    const mods=cfg.hotkey&&cfg.hotkey.modifiers||["ctrl","alt"];
    const key=cfg.hotkey&&cfg.hotkey.key||"P";
    $("#hkLabel").textContent=mods.map(m=>m[0].toUpperCase()+m.slice(1)).join("+")+"+"+key+" toggles";
    $("#liveDot").hidden=r.topics.filter(t=>t.status==="open").length===0;
    renderMode();
    setTimeout(()=>{const el=$("#ptText");if(el)el.focus();},150);
  });
}
function applyTheme(pref){
  const el=document.documentElement;
  if(pref==="light"||pref==="dark") el.setAttribute("data-theme",pref);
  else el.removeAttribute("data-theme");   // fall back to prefers-color-scheme
}
function popupShown(){
  api.get_state().then(r=>{if(r&&!r.error){state=r;
    applyTheme(((r.config||{}).appearance||{}).theme||"system");renderMode();}}).catch(()=>{});
  setTimeout(()=>{const el=$("#ptText");if(el)el.focus();},120);
}
if(window.pywebview){boot();}else{window.addEventListener("pywebviewready",boot);}
</script></body></html>
"""

MAIN_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Trailmark</title><style>
__BASE_CSS__
.app{display:grid;grid-template-columns:292px 1fr;grid-template-rows:auto 1fr;
  gap:16px;height:100vh;padding:0 16px 16px}
/* The app's own header strip. The OS title bar is deliberately kept: pywebview's
   WinForms backend implements frameless as FormBorderStyle=None with no hit-test
   WndProc, so a custom-drawn title bar would cost the window its resize borders
   and Windows snap. This strip is the designed top bar living under real chrome. */
.topbar{grid-column:1/-1;display:flex;align-items:center;gap:10px;height:44px;
  padding:0 4px;-webkit-user-select:none;user-select:none}
.tb-ctx{font-size:12px;color:var(--content-secondary);white-space:nowrap;overflow:hidden;
  text-overflow:ellipsis;min-width:0;flex:1}
.tb-ctx::before{content:"—";margin-right:8px;opacity:.5}
.tb-ctx:empty::before{content:none}
.tb-act{flex:none;display:flex;align-items:center;gap:4px}
.tb-chip{display:none;align-items:center;gap:7px;padding:5px 11px;border-radius:var(--r-pill);
  font:700 11px var(--font-ui);background:var(--surface-sunken);border:1px solid var(--border);
  max-width:220px;flex:none;white-space:nowrap}
.tb-chip.show{display:flex}
.tb-chip .tx{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.tb-chip.listening{color:var(--secondary)}
.tb-chip .dot3{width:7px;height:7px;border-radius:50%;background:var(--secondary);flex:none;
  animation:asrPulse 1.6s ease-in-out infinite}
@keyframes asrPulse{0%,100%{box-shadow:0 0 0 0 var(--secondary-tint)}50%{box-shadow:0 0 0 5px rgba(0,0,0,0)}}
.tb-chip.transcribing{color:var(--accent)}
.tb-chip .ring{width:11px;height:11px;border-radius:50%;border:2px solid var(--border-strong);
  border-top-color:var(--accent);flex:none;animation:asrSpin .8s linear infinite}
@keyframes asrSpin{to{transform:rotate(360deg)}}
.tb-chip.logged{color:var(--success)}
.tb-chip.error{color:var(--danger)}
.tb-chip .check{width:14px;height:14px;flex:none;stroke:var(--success)}
.tb-btn{width:32px;height:32px;display:grid;place-items:center;border:0;border-radius:9px;
  background:transparent;color:var(--content-secondary);cursor:pointer;
  transition:var(--dur-fast) var(--ease-standard)}
.tb-btn:hover{background:var(--surface-sunken);color:var(--content)}
.tb-btn svg{width:15px;height:15px;fill:none;stroke:currentColor;stroke-width:1.8;
  stroke-linecap:round;stroke-linejoin:round}
.tb-btn.on{color:var(--accent);background:var(--accent-tint)}
aside{display:flex;flex-direction:column;overflow:hidden}
.brand{display:flex;align-items:center;gap:10px;padding:16px 16px 8px}
.brand img{width:auto;height:30px;object-fit:contain}
.brand .bn{font-weight:700;font-size:14.5px;letter-spacing:.2px}
.brand .bt{font-size:10.5px;color:var(--content-secondary)}
.segmented{display:inline-flex;gap:3px;padding:3px;background:var(--surface-sunken);
  border:1px solid var(--border);border-radius:var(--r-md);align-self:flex-start}
aside>.segmented{display:flex;margin:10px 14px 6px;align-self:stretch}
aside>.segmented .seg{flex:1;padding:7px 0}
.seg{flex:none;padding:7px 14px;border:0;border-radius:9px;background:transparent;
  color:var(--content-secondary);font-family:inherit;font-size:11.5px;font-weight:600;
  cursor:pointer;transition:.18s}
.seg:hover{color:var(--content)}
.seg.active{background:var(--surface-raised);color:var(--content);box-shadow:var(--shadow-1)}
.list{flex:1;overflow-y:auto;padding:8px;margin:2px 8px 8px}
.ti{display:flex;align-items:center;gap:12px;padding:12px 14px;border-radius:var(--r-md);
  cursor:pointer;border:1px solid transparent;transition:background .12s}
.ti:hover{background:var(--surface-sunken)}
.ti.sel{background:var(--accent-tint)}
.dot{flex:none;width:7px;height:7px;border-radius:50%}
.dot.open{background:var(--accent)}
.dot.closed{background:var(--content-muted)}
.ti-b{min-width:0;flex:1}
.ti-t{font-size:13.5px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ti-s{font-size:12px;color:var(--content-muted);margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.empty{display:flex;flex-direction:column;align-items:center;gap:10px;padding:40px 20px;
  text-align:center;color:var(--content-muted);font-size:12.5px}
.empty svg{width:28px;height:28px;fill:none;stroke:var(--content-muted);stroke-width:1.75;
  stroke-linecap:round;stroke-linejoin:round;opacity:.6}
.empty b{color:var(--content);font-size:14px}
.empty span{font-size:12.5px;max-width:280px;line-height:1.5}
.side-actions{padding:8px 14px 14px;display:flex;flex-direction:column;gap:8px}
main{overflow-y:auto;padding:22px}
.cards{display:flex;flex-direction:column;gap:15px;max-width:780px;margin:0 auto;padding-top:6px}
.card{padding:18px}
.card-h{display:flex;align-items:center;gap:9px;margin-bottom:6px}
.card-t{font-size:15.5px;font-weight:650}
/* The "start a topic" card. It used to carry a breathing amber orb, which was
   a second blaze on a screen that already has a primary button, and an
   animation with nothing behind it - both ruled out by the design system. */
.hero{border-color:var(--accent)}
.hero .mark{width:32px;height:32px;margin:0 auto 4px;display:block;fill:var(--accent)}
.dhead{display:flex;align-items:center;gap:14px;margin-bottom:16px}
.dh-b{min-width:0;flex:1}
.dh-t{font-size:20px;font-weight:700;word-break:break-word}
.dh-s{color:var(--content-secondary);font-size:12.5px;margin-top:3px}
.pill{display:inline-flex;align-items:center;gap:6px;padding:4px 10px;border-radius:999px;font-size:11px;
  font-weight:700;letter-spacing:.05em;text-transform:uppercase}
.pill.open{background:var(--accent-tint);color:var(--accent)}
.pill.closed{background:var(--surface-sunken);color:var(--content-muted)}
.sub{padding:17px}
.composer{display:flex;flex-direction:column;gap:9px}
.entries{display:flex;flex-direction:column;gap:11px}
.entry{padding:15px}
.e-meta{display:flex;align-items:center;gap:8px;flex-wrap:wrap;font-size:11.5px;color:var(--content-secondary);margin-bottom:7px}
.tag{font-size:10.5px;font-weight:700;letter-spacing:.03em;padding:3px 9px;
  border-radius:var(--r-pill);background:var(--secondary-tint);color:var(--secondary)}
.e-text{font-size:14px;line-height:1.6;white-space:pre-line;word-break:break-word}
.sources{display:flex;flex-direction:column;gap:6px;margin-top:11px;
  border-top:1px solid var(--border);padding-top:10px}
.src{display:flex;align-items:center;gap:8px;font-size:12.5px}
.src-link{display:inline-flex;align-items:center;gap:6px;max-width:100%;overflow:hidden;
  text-overflow:ellipsis;white-space:nowrap;padding:6px 10px;border-radius:var(--r-sm);
  background:var(--surface-sunken);color:var(--content-secondary);cursor:pointer;
  font-family:var(--font-mono);font-size:12px;transition:color .14s,background .14s}
.src-link:hover{color:var(--accent);background:var(--accent-tint)}
.src-str{display:inline-flex;align-items:center;gap:6px;font-style:italic;
  color:var(--content-secondary);padding:6px 10px;border-radius:var(--r-sm);
  background:var(--surface-sunken);cursor:pointer;max-width:100%}
.src-str span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.thumb{width:64px;height:64px;object-fit:cover;border-radius:var(--r-sm);
  border:1px solid var(--border);cursor:pointer}
.e-actions{display:flex;gap:7px;margin-top:10px;flex-wrap:wrap}
.edit{width:100%;display:flex;flex-direction:column;gap:9px}
.export-ok{display:flex;flex-direction:column;gap:9px;align-items:flex-start}
.path{font-family:var(--font-mono);font-size:12px;color:var(--content-secondary);
  background:var(--surface-sunken);border-radius:var(--r-sm);padding:6px 10px;
  word-break:break-all;max-width:100%}
.set-card{display:flex;flex-direction:column;gap:11px}
.row{display:flex;gap:9px;align-items:flex-end;flex-wrap:wrap}
.grow{flex:1;min-width:0}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.grid3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px}
.mod{display:inline-flex;gap:6px;align-items:center}
.mod input{width:15px;height:15px;accent-color:var(--accent)}
.kkey{width:90px;text-align:center;text-transform:uppercase;letter-spacing:.1em}
.dim{color:var(--content-secondary)}
.spacer{flex:1}

/* --- badges ------------------------------------------------------------- */
.badge{display:inline-flex;align-items:center;gap:5px;padding:3px 9px;border-radius:var(--r-pill);
  font-size:10.5px;font-weight:700;letter-spacing:.03em;background:var(--surface-sunken);
  color:var(--content-muted);white-space:nowrap}
.badge.tealish{background:var(--secondary-tint);color:var(--secondary)}
.badge.count{background:var(--accent-tint);color:var(--accent);font-variant-numeric:tabular-nums}

/* --- exports: collapsible group per topic ------------------------------- */
.ex-grp{padding:0;overflow:hidden}
.ex-head{display:flex;align-items:center;gap:11px;width:100%;padding:15px 18px;border:0;
  background:transparent;color:var(--content);font-family:inherit;text-align:left;cursor:pointer;
  transition:.16s}
.ex-head:hover{background:var(--surface-sunken)}
.ex-head .caret{flex:none;color:var(--content-secondary);transition:transform .18s ease}
.ex-grp.open .ex-head .caret{transform:rotate(90deg);color:var(--accent)}
.ex-head-b{flex:1;min-width:0}
.ex-head-t{font-size:14.5px;font-weight:650;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ex-head-s{font-size:11.5px;color:var(--content-secondary);margin-top:3px;white-space:nowrap;overflow:hidden;
  text-overflow:ellipsis}
.ex-body{display:none;padding:0 18px 8px;border-top:1px solid var(--border)}
.ex-grp.open .ex-body{display:block;animation:fade .18s ease}
.ex-row{display:flex;gap:14px;align-items:flex-start;padding:13px 0;
  border-bottom:1px solid var(--border)}
.ex-row:last-child{border-bottom:0}
.ex-when{flex:none;width:152px;font-size:11.5px;color:var(--content-secondary);line-height:1.5;
  font-variant-numeric:tabular-nums}
.ex-size{display:block;opacity:.7;font-size:10.5px;margin-top:1px}
.ex-mid{flex:1;min-width:0}
.ex-act{flex:none;display:flex;gap:6px;align-items:center}
.chip.fmt{font-variant-numeric:tabular-nums;letter-spacing:.04em;font-size:11.5px;padding:5px 10px}
.chip.fmt:hover{background:var(--accent-tint);border-color:var(--accent);color:var(--accent)}
.ex-warn{margin-top:8px;font-size:11.5px;line-height:1.45;color:var(--accent);
  border-left:2px solid var(--accent);padding-left:9px}

/* --- modal + export dialog ---------------------------------------------- */
.modal-back{position:fixed;inset:0;z-index:120;display:flex;align-items:center;justify-content:center;
  padding:26px;background:var(--scrim);animation:fade .16s ease}
.modal{width:min(620px,100%);max-height:calc(100vh - 52px);display:flex;flex-direction:column;
  padding:0;border-radius:var(--r-xl);box-shadow:var(--shadow-3);transition:width var(--dur-mid) var(--ease-standard)}
.modal.wide{width:min(860px,100%)}
.modal-h{display:flex;align-items:flex-start;gap:14px;padding:20px 24px 14px;
  border-bottom:1px solid var(--border)}
.modal-h .card-t{word-break:break-word}
.modal-b{flex:1;overflow-y:auto;padding:16px 24px}
.modal-f{display:flex;align-items:center;gap:14px;padding:16px 24px;border-top:1px solid var(--border)}
.modal-f .muted{flex:1;font-size:11.5px}
.sec-l{font-size:11px;font-weight:600;letter-spacing:.03em;text-transform:uppercase;
  color:var(--content-muted);margin:4px 0 9px}
.modal-b label:not(.fmt-opt):not(.mod){display:flex;flex-direction:column;gap:6px;
  font-size:11px}
.modal-b label .cap{display:block}
/* the checkbox row's title and its explanation are two spans inside one span;
   without this they run together on a single line */
.modal-b label.mod>span{display:flex;flex-direction:column;gap:3px;min-width:0}
.modal-b label.mod>span .muted{font-size:11.5px;line-height:1.45;font-weight:400}
.modal-b label.mod input[type=checkbox]{width:15px;height:15px;accent-color:var(--accent);
  margin-top:2px;flex:none}
.sec-l:not(:first-child){margin-top:20px}

.tpls{display:flex;flex-direction:column;gap:7px;max-height:250px;overflow-y:auto;
  /* with five or six templates installed the Formats section fell below the
     fold and the Export button looked like the whole dialog - the list gets
     its own scroll so both halves of the decision stay visible */
  padding-right:4px;margin-right:-4px}
.tpl{display:flex;align-items:flex-start;gap:11px;padding:11px 13px;border-radius:var(--r-md);
  border:1px solid var(--border);background:var(--surface-sunken);color:var(--content);
  font-family:inherit;text-align:left;cursor:pointer;transition:.15s}
.tpl:hover{border-color:var(--border-strong)}
.tpl.on{border-color:var(--accent);background:var(--accent-tint);
  box-shadow:0 0 0 3px var(--accent-tint)}
.tpl-dot{flex:none;width:10px;height:10px;border-radius:3px;margin-top:4px}
.tpl-b{flex:1;min-width:0;display:flex;flex-direction:column;gap:3px}
.tpl-n{font-size:13.5px;font-weight:650;display:flex;align-items:center;gap:7px;flex-wrap:wrap}
.tpl-d{font-size:11.5px;color:var(--content-muted);line-height:1.45}
.badge.accentish{background:var(--accent-tint);color:var(--accent)}

/* --- categories: pill strip above the template grid --------------------- */
.cat-strip{display:flex;flex-wrap:wrap;gap:7px;margin-bottom:11px}
.cat-pill{display:inline-flex;align-items:center;gap:6px;padding:6px 13px;border-radius:var(--r-pill);
  border:1px solid var(--border);background:var(--surface-sunken);color:var(--content-secondary);
  font-family:inherit;font-size:12px;font-weight:600;cursor:pointer;transition:.15s;white-space:nowrap}
.cat-pill:hover{border-color:var(--border-strong);color:var(--content)}
.cat-pill.on{border-color:var(--accent);background:var(--accent-tint);color:var(--accent)}
.cat-pill .badge{padding:1px 7px;font-size:9.5px}
.cat-pill.new{border-style:dashed;color:var(--content-muted)}
.cat-pill.new:hover{color:var(--accent);border-color:var(--accent)}

.cat-popover{display:flex;flex-direction:column;gap:9px;padding:13px;margin-bottom:11px;
  border:1px solid var(--border);border-radius:var(--r-md);background:var(--surface-sunken)}
.cat-popover .row2{display:flex;gap:9px}
.cat-popover .row2>*{flex:1;min-width:0}

/* --- categories manager: Settings -> Exports -------------------------- */
.cat-mgr{margin-top:18px;padding-top:16px;border-top:1px solid var(--border)}
.cat-list{display:flex;flex-direction:column}
.cat-row{display:flex;gap:9px;align-items:center;padding:10px 0;
  border-bottom:1px solid var(--border);flex-wrap:wrap}
.cat-row:last-child{border-bottom:0}
.cat-row .cat-name{flex:1;min-width:120px}
.cat-row .cat-def-tpl{flex:1;min-width:150px}

/* --- template actions (default badge / set-as-default / preview) -------- */
.tpl-actions{display:flex;gap:11px;align-items:center;margin-top:2px}
.tpl-set-default,.tpl-preview-btn{background:none;border:0;padding:0;font-family:inherit;
  font-size:11px;font-weight:650;cursor:pointer;color:var(--accent);text-decoration:underline;
  text-underline-offset:2px}
.tpl-set-default:hover,.tpl-preview-btn:hover{color:var(--accent-hover)}

/* --- template panel: pills+grid alongside an optional preview column ----- */
.tpl-panel{display:flex;gap:16px;align-items:flex-start;min-width:0}
.tpl-main{flex:1;min-width:0}
/* sub-headings inside the template column ("Templates in X" / "Also
   available") - deliberately lighter than .sec-l so they read as nested
   under the "Template" section heading, not as a sibling of it */
.tpl-sub-l{font-size:10.5px;font-weight:600;letter-spacing:.03em;text-transform:uppercase;
  color:var(--content-muted);margin:0 0 7px}
.tpl-sub-l.also{margin-top:14px}
.preview-col{flex:0 0 268px;min-width:0;display:flex;flex-direction:column;gap:8px;
  border-left:1px solid var(--border);padding-left:16px}
.preview-h{font-size:11.5px;font-weight:650;color:var(--content-secondary);line-height:1.4}
.preview-frame-wrap{border:1px solid var(--border);border-radius:var(--r-md);overflow:hidden;
  background:var(--surface-raised);height:280px}
.preview-frame-wrap iframe{width:100%;height:100%;border:0}
.preview-empty{font-size:11.5px;color:var(--content-muted);padding:14px;text-align:center}

.fmts{display:grid;grid-template-columns:1fr 1fr;gap:7px}
.fmt-opt{display:flex;align-items:flex-start;gap:9px;padding:10px 12px;border-radius:var(--r-md);
  border:1px solid var(--border);background:var(--surface-sunken);cursor:pointer;transition:.15s;
  flex-direction:row;font-size:13px;font-weight:400;color:var(--content);letter-spacing:0;
  text-transform:none}
.fmt-opt:hover{border-color:var(--border-strong)}
.fmt-opt.on{border-color:var(--accent);background:var(--accent-tint)}
.fmt-opt input{width:15px;height:15px;accent-color:var(--accent);margin-top:1px;flex:none}
.fmt-opt span{display:flex;flex-direction:column;gap:2px;min-width:0}
.fmt-opt b{font-size:13px;font-weight:650}
.fmt-opt .muted{font-size:11px;line-height:1.4}

.stages{display:flex;align-items:flex-start;gap:0;margin-top:18px;padding-top:16px;
  border-top:1px solid var(--border)}
.stg{display:flex;flex-direction:column;align-items:center;gap:8px;flex:1;position:relative}
.stg .dot2{width:26px;height:26px;border-radius:50%;background:var(--surface-sunken);
  border:2px solid var(--border);display:flex;align-items:center;justify-content:center;
  font:700 11px var(--font-mono);color:var(--content-muted);z-index:1;transition:.2s}
.stg.done .dot2{background:var(--secondary);border-color:var(--secondary);color:var(--surface)}
.stg.active .dot2{background:var(--accent);border-color:var(--accent);color:var(--accent-content)}
.stg span{font:600 11px var(--font-ui);color:var(--content-muted);text-align:center;
  line-height:1.35;padding:0 3px}
.stg.active span,.stg.done span{color:var(--content)}
.stg:not(:last-child)::after{content:'';position:absolute;top:13px;left:50%;width:100%;height:2px;
  background:var(--border);z-index:0}
.stg.done:not(:last-child)::after{background:var(--secondary)}
</style></head><body>
<div class="app">
  <header class="topbar">
    <span class="tb-ctx" id="tbCtx"></span>
    <span class="tb-chip" id="asrChip"></span>
    <span class="tb-act">
      <button class="tb-btn" id="tbTheme" title="Switch theme"><svg viewBox="0 0 24 24">
        <circle cx="12" cy="12" r="4.2"/><path d="M12 2.6v2.2M12 19.2v2.2M4.2 12H2M22 12h-2.2
        M6.5 6.5 5 5M19 19l-1.5-1.5M17.5 6.5 19 5M5 19l1.5-1.5"/></svg></button>
      <button class="tb-btn" id="tbCapture" title="Quick capture"><svg viewBox="0 0 24 24">
        <rect x="3.2" y="5" width="17.6" height="14" rx="3"/><path d="M8 12h8M12 8v8"/></svg></button>
    </span>
  </header>
  <aside class="glass">
    <div class="brand">
      <img src="__ICON__" alt="">
      <div><div class="bn">Trailmark</div><div class="bt">Log the point. Keep the source.</div></div>
    </div>
    <div class="segmented" id="seg">
      <button class="seg active" data-tab="open">Open</button>
      <button class="seg" data-tab="closed">Closed</button>
      <button class="seg" data-tab="exports">Exports</button>
      <button class="seg" data-tab="settings">Settings</button>
    </div>
    <div class="list" id="sideList"></div>
    <div class="side-actions">
      <button class="btn primary full" id="newBtn"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"><path d="M12 5v14M5 12h14"/></svg> New topic</button>
      <button class="btn ghost full" id="popupBtn">Open quick capture</button>
    </div>
  </aside>
  <main id="main"></main>
</div>
<div id="toasts"></div>
<script>
let state={topics:[],config:{},providers:{},exports:[],templates:[]};
let tab="open", sel=null, editEntry=null, filterSub=null, summaryDraft=null;
let displayLimit=20;
// Exports are grouped by topic. openGroups holds the topic ids whose group is
// expanded; the newest group opens by default so the last thing you exported is
// the first thing you see.
let openGroups=null;
let exportDialog=null;
let catNewOpen=false; // Settings -> Exports -> Categories: "+ New category" popover open?
const api=new Proxy({},{get:(_,p)=>{const pv=window.pywebview&&window.pywebview.api;return pv?pv[p]:(()=>Promise.resolve({error:"bridge not ready"}));}});

const $=(s,r=document)=>r.querySelector(s);
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const toast=(m,t="ok")=>{const d=document.createElement("div");d.className="toast "+t;d.textContent=m;
  document.getElementById("toasts").appendChild(d);setTimeout(()=>d.classList.add("out"),2400);setTimeout(()=>d.remove(),2800);};
const byId=i=>state.topics.find(t=>t.id===i);
const escTop=s=>esc(s).replace(/\\n/g,"<br>");

// Called from Python via evaluate_js("clipboardToast(...)") when the Ctrl+Alt+V
// hotkey auto-detects and logs a clipboard source. Deliberately its own .cbtoast
// element, not the plain toast() above - see report for why. `tid` is a 4th
// argument beyond the original 3-arg contract; see the handback in the report.
const CB_ICONS={
  link:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M8 12a3 3 0 0 0 4.24 0l2-2a3 3 0 0 0-4.24-4.24l-1 1"/><path d="M12 8a3 3 0 0 0-4.24 0l-2 2a3 3 0 0 0 4.24 4.24l1-1"/></svg>',
  image:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="14" height="12" rx="2"/><circle cx="7.5" cy="9" r="1.2"/><path d="M17 13l-4-4-7 7"/></svg>',
  text:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5h12M4 9h12M4 13h8"/></svg>'
};
function clipboardToast(kind,detailText,entryId,tid){
  const d=document.createElement("div");
  d.className="cbtoast fade";
  const headline=kind==="error"?"Couldn't log from clipboard":"Logged from clipboard";
  d.innerHTML=`<div class="row1"><div class="ic">${CB_ICONS[kind]||CB_ICONS.text}</div>
    <div class="txt"><b>${headline}</b><span></span></div>
    ${entryId==null?"":'<button class="undo" type="button">Undo</button>'}</div>
    <div class="prog"><i></i></div>`;
  d.querySelector(".txt span").textContent=detailText; // untrusted, pre-formatted - textContent only
  document.getElementById("toasts").appendChild(d);
  const bar=d.querySelector(".prog i");
  requestAnimationFrame(()=>{bar.style.width="0%";});
  function dismiss(){d.classList.add("out");setTimeout(()=>d.remove(),280);}
  const timer=setTimeout(dismiss,4000);
  const undoBtn=d.querySelector(".undo");
  if(undoBtn) undoBtn.addEventListener("click",async()=>{
    clearTimeout(timer);
    const r=await api.delete_entry(tid,entryId);
    if(r&&r.error){toast(r.error,"err");return;}
    state=r;render();
    dismiss();
  });
}
function fmt(iso){if(!iso)return"—";const d=new Date(iso);return d.toLocaleString(undefined,{day:"2-digit",month:"short",year:"numeric",hour:"2-digit",minute:"2-digit"});}
function fmtT(iso){if(!iso)return"";const d=new Date(iso);return d.toLocaleTimeString(undefined,{hour:"2-digit",minute:"2-digit"});}
function copyText(t){navigator.clipboard&&navigator.clipboard.writeText(t).then(()=>toast("Copied."),()=>legacyCopy(t)).catch(()=>legacyCopy(t));}
function legacyCopy(t){const ta=document.createElement("textarea");ta.value=t;document.body.appendChild(ta);ta.select();
  try{document.execCommand("copy");toast("Copied.");}catch(e){toast("Copy failed.","err");}ta.remove();}

function render(){
  renderTopbar();
  document.querySelectorAll("#seg .seg").forEach(b=>b.classList.toggle("active",b.dataset.tab===tab));
  if(sel&&!byId(sel))sel=null;
  renderSide();
  renderMain();
}

function renderTopbar(){
  const t=byId(sel);
  const label=t?t.title:(tab==="exports"?"Exports":tab==="settings"?"Settings":"");
  $("#tbCtx").textContent=label||"";
  const pref=((state.config||{}).appearance||{}).theme||"system";
  $("#tbTheme").classList.toggle("on",pref!=="system");
  $("#tbTheme").title=pref==="system"?"Following your Windows theme - click for light"
    :pref==="light"?"Light - click for dark":"Dark - click to follow Windows";
}

function renderSide(){
  const list=$("#sideList");
  if(tab==="settings"){list.innerHTML=emptyHtml("Settings","AI assist, hotkey and storage preferences are on the right.");return;}
  if(tab==="exports"){
    const groups=(state.exports||[]);
    if(!groups.length){list.innerHTML=emptyHtml("No exports yet","Close a topic, and the cited report lands here.");return;}
    list.innerHTML=groups.map(g=>{
      const d=new Date(g.latest*1000).toLocaleString(undefined,{day:"2-digit",month:"short",hour:"2-digit",minute:"2-digit"});
      const n=g.total||g.exports.length;
      return `<div class="ti ${sel===("grp:"+g.topic_id)?"sel":""}" data-grp="${esc(g.topic_id)}">
        <span class="dot open" style="background:var(--secondary)"></span>
        <div class="ti-b"><div class="ti-t">${esc(g.topic_title)}</div>
        <div class="ti-s">${n} export${n===1?"":"s"} · latest ${esc(d)}</div></div></div>`;
    }).join("");
    list.querySelectorAll(".ti[data-grp]").forEach(el=>el.addEventListener("click",()=>{
      const id=el.dataset.grp;
      sel="grp:"+id;
      groupSet().add(id);
      render();
      const card=document.getElementById("g_"+cssId(id));
      if(card) card.scrollIntoView({behavior:"smooth",block:"start"});
    }));
    return;
  }
  const open=tab==="open";
  const items=state.topics.filter(t=>t.status==="open"===open);
  items.sort((a,b)=>(a.status==="open"?(a.created<b.created?1:-1):(a.closed<b.closed?1:-1)));
  list.innerHTML=items.map(t=>{
    const n=t.entries.length;
    const sub=t.status==="open"
      ?(n+" point"+(n===1?"":"s")+" · started "+fmtT(t.created))
      :(n+" point"+(n===1?"":"s")+" · closed "+fmtT(t.closed));
    return `<div class="ti ${sel===t.id?"sel":""}" data-id="${t.id}">
      <span class="dot ${t.status}"></span>
      <div class="ti-b"><div class="ti-t">${esc(t.title)}</div><div class="ti-s">${esc(sub)}</div></div>
    </div>`;
  }).join("")||(open?emptyHtml("No open topics","Start one with the button below, or hit the capture hotkey.")
                    :emptyHtml("No closed topics yet","A topic moves here when you close and export it."));
  list.querySelectorAll(".ti").forEach(el=>el.addEventListener("click",()=>{sel=el.dataset.id;editEntry=null;filterSub=null;displayLimit=20;render();}));
  list.querySelectorAll(".ti[data-exp]").forEach(el=>el.addEventListener("click",()=>{ sel=el.dataset.exp; displayLimit=20; render(); }));
}

const KIND_HINT={
  claim:"Taken from a source. It carries the citation.",
  note:"Your own thinking. Kept in its own section and never given a citation - not even by the AI pass.",
  quote:"Verbatim from the source. Nothing, including the AI pass, may reword it."
};
const KIND_LABEL={claim:"Claim",note:"My note",quote:"Quotation"};
let CITE_STYLES=[{id:"numeric",label:"Numbered",hint:""}];
const META_LABEL=[["authors","Authors"],["year","Year"],["title","Title"],
  ["container","Journal / book / site"],["publisher","Publisher"],["volume","Volume"],
  ["issue","Issue"],["pages","Pages"],["doi","DOI"],["url","URL"]];
let editSource=null;
const sciOn=()=>!!((state.config||{}).science||{}).enabled;

function renderMain(){
  const main=$("#main");
  if(tab==="settings"){main.innerHTML=settingsHtml();bindSettings();return;}
  if(tab==="exports"){
    main.innerHTML=exportsOverviewHtml();
    bindExports(main);
    return;
  }
  const t=sel?byId(sel):null;
  if(!t){main.innerHTML=newViewHtml();bindNew();return;}
  main.innerHTML=detailHtml(t);bindDetail(t);
}

// The mark, for empty states and the new-topic card. One definition.
const MARK_SVG=`<svg class="mark" viewBox="0 0 1349 1568" aria-hidden="true">
  <rect x="0" y="0" width="1347" height="279" rx="46"/><rect x="597" y="180" width="147" height="1388" rx="46"/>
  <rect x="206" y="679" width="392" height="138" rx="46"/><rect x="206" y="984" width="392" height="139" rx="46"/>
  <rect x="744" y="1259" width="395" height="140" rx="46"/></svg>`;
const EMPTY_SVG=`<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 8h13M11 8v11M7 13h4M7 16h4"/></svg>`;

// components.html section 08: a mark, a bold line, and a hint.
function emptyHtml(title,hint){
  return `<div class="empty">${EMPTY_SVG}<b>${title}</b>${hint?`<span>${hint}</span>`:""}</div>`;
}

function newViewHtml(){
  return `<div class="cards"><div class="card glass fade hero">${MARK_SVG}
    <div class="card-h"><div class="card-t">New research topic</div></div>
    <p class="muted">Give the topic a name, then start logging points. Each point can carry a source — a link, a string citation, or a screenshot.</p>
    <div class="row"><input id="ntTitle" class="input grow" placeholder="Topic name — e.g. Rust borrow checker">
      <button class="btn primary" id="ntGo">Start topic</button></div>
  </div></div>`;
}

function bindNew(){
  $("#ntGo").addEventListener("click",async()=>{
    const r=await api.start_topic($("#ntTitle").value);
    if(r.error)return toast(r.error,"err");
    state=r;sel=r.topics.find(t=>t.status==="open").id;render();toast("Topic started.");
  });
  $("#ntTitle").addEventListener("keydown",e=>{if(e.key==="Enter")$("#ntGo").click();});
}

/* --- Exports: one collapsible group per topic ---------------------------- */

const cssId=s=>String(s).replace(/[^a-zA-Z0-9_-]/g,"_");
const FORMAT_LABEL={html:"HTML",pdf:"PDF",docx:"DOCX",markdown:"MD",latex:"TeX"};

function groupSet(){
  // First render: open the newest group only. A topic exported ten times should
  // not push every other topic off the screen.
  if(openGroups===null){
    openGroups=new Set();
    const first=(state.exports||[])[0];
    if(first) openGroups.add(first.topic_id);
  }
  return openGroups;
}

function exportRowHtml(e){
  const d=new Date(e.mtime*1000).toLocaleString(undefined,
    {day:"2-digit",month:"short",year:"numeric",hour:"2-digit",minute:"2-digit"});
  const chips=Object.keys(e.files||{}).sort().map(k=>
    `<button class="chip fmt" data-open="${esc(e.files[k])}" title="Open the ${FORMAT_LABEL[k]||k} file">${FORMAT_LABEL[k]||k}</button>`).join("");
  const badges=[
    e.polished?`<span class="badge tealish">&#10022; Polished</span>`:"",
    e.template_name?`<span class="badge">${esc(e.template_name)}</span>`:"",
    e.pdf_pages?`<span class="badge">${e.pdf_pages} page${e.pdf_pages===1?"":"s"}</span>`:"",
  ].filter(Boolean).join("");
  const warn=(e.warnings||[]).length
    ? `<div class="ex-warn">&#9888; ${esc(e.warnings.join(" "))}</div>` : "";
  return `<div class="ex-row">
    <div class="ex-when">${esc(d)}<span class="ex-size">${Math.round(e.size/1024)} KB</span></div>
    <div class="ex-mid">
      <div class="chips">${chips||`<span class="muted">no files</span>`}</div>
      ${badges?`<div class="chips" style="margin-top:6px">${badges}</div>`:""}
      ${warn}
    </div>
    <div class="ex-act">
      <button class="btn ghost sm" data-open-f="${esc(e.folder)}">Folder</button>
      <button class="btn danger sm" data-remove="${esc(e.folder)}">Remove</button>
    </div>
  </div>`;
}

function exportsOverviewHtml(){
  const groups=(state.exports||[]);
  if(!groups.length) return `<div class="cards"><div class="card glass fade">
    <div class="card-t">No exports yet</div>
    <p class="muted">Export a topic and its reports collect here &mdash; one group per topic, newest first.
    Removing an export deletes only that export folder; your points are untouched.</p></div></div>`;
  const open=groupSet();
  const cards=groups.map(g=>{
    const isOpen=open.has(g.topic_id);
    const d=new Date(g.latest*1000).toLocaleString(undefined,
      {day:"2-digit",month:"short",year:"numeric",hour:"2-digit",minute:"2-digit"});
    const n=g.total||g.exports.length;
    const formats=(g.formats||[]).map(k=>FORMAT_LABEL[k]||k).join(" · ");
    const hidden=n>g.exports.length
      ? `<div class="muted" style="padding:8px 2px 0">Showing the ${g.exports.length} most recent of ${n}.</div>` : "";
    return `<div class="card glass fade ex-grp ${isOpen?"open":""}" id="g_${cssId(g.topic_id)}">
      <button class="ex-head" data-toggle="${esc(g.topic_id)}" aria-expanded="${isOpen}">
        <svg class="caret" width="14" height="14" viewBox="0 0 24 24" fill="none"
             stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round">
          <path d="M9 6l6 6-6 6"/></svg>
        <div class="ex-head-b">
          <div class="ex-head-t">${esc(g.topic_title)}</div>
          <div class="ex-head-s">${n} export${n===1?"":"s"} · latest ${esc(d)}${formats?" · "+esc(formats):""}</div>
        </div>
        <span class="badge count">${n}</span>
      </button>
      <div class="ex-body">${g.exports.map(exportRowHtml).join("")}${hidden}</div>
    </div>`;
  }).join("");
  return `<div class="cards">
    <div class="card glass fade">
      <div class="card-t">Exports</div>
      <p class="muted">Every report you have generated, grouped by the topic it came from.
      The topic you exported most recently sits at the top, and inside each group the newest
      report is first. Click a format chip to open that file.</p>
    </div>${cards}</div>`;
}

function bindExports(root){
  root.querySelectorAll("[data-toggle]").forEach(b=>b.addEventListener("click",()=>{
    const id=b.dataset.toggle, set=groupSet();
    if(set.has(id)) set.delete(id); else set.add(id);
    sel=set.has(id)?("grp:"+id):null;
    render();
  }));
  root.querySelectorAll("[data-open]").forEach(b=>b.addEventListener("click",e=>{
    e.stopPropagation(); api.open_path(b.dataset.open);}));
  root.querySelectorAll("[data-open-f]").forEach(b=>b.addEventListener("click",e=>{
    e.stopPropagation(); api.open_path(b.dataset.openF);}));
  root.querySelectorAll("[data-remove]").forEach(b=>b.addEventListener("click",async e=>{
    e.stopPropagation();
    if(!confirm("Remove this export? The folder and its files will be deleted. Your points are not touched.")) return;
    const r=await api.delete_export(b.dataset.remove);
    if(r.error) return toast(r.error,"err");
    state=r; render(); toast("Export removed.");
  }));
}

/* --- Export dialog: pick a template and the formats you want ------------- */

/* Which category the dialog should open on, in priority order:
   1) the category of the topic's own last-used template (state.exports groups
      are already sorted newest-export-first per topic - see point_store.py
      list_exports - so exports[0].template is a real, load-bearing signal,
      not a guess);
   2) the category of the global default template (config.export.template);
   3) the first category there is.
   Exported as its own function (rather than folded into defaultExportOpts)
   so the pre-selection rule can be read, and tested against fixtures, on
   its own. */
function defaultExportCategory(t){
  const cats=state.categories||[];
  if(!cats.length) return null;
  const tplById=id=>(state.templates||[]).find(tp=>tp.id===id);
  const grp=(state.exports||[]).find(g=>g.topic_id===t.id);
  const lastTplId=grp&&grp.exports&&grp.exports[0]&&grp.exports[0].template;
  let tpl=lastTplId&&tplById(lastTplId);
  if(tpl&&cats.some(c=>c.id===tpl.category)) return tpl.category;
  const cfgTplId=((state.config||{}).export||{}).template;
  tpl=cfgTplId&&tplById(cfgTplId);
  if(tpl&&cats.some(c=>c.id===tpl.category)) return tpl.category;
  return cats[0].id;
}

function defaultExportOpts(t){
  const cfg=(state.config&&state.config.export)||{};
  const cats=state.categories||[];
  const catId=defaultExportCategory(t);
  const cat=cats.find(c=>c.id===catId);
  return {
    template: (cat&&cat.default_template)||cfg.template||"personal-report",
    category: catId,
    formats: (cfg.formats||["html","pdf","markdown"]).slice(),
    polish: false,
    subtitle: "",
    previewTemplate: null,
    previewHtml: null,
    previewError: null,
    previewLoading: false,
    newCatOpen: false,
  };
}

/* --- category pill strip + "+ New category" popover ---------------------- */

function catStripHtml(opts){
  const cats=state.categories||[];
  const pills=cats.map(c=>`<button type="button" class="cat-pill ${c.id===opts.category?"on":""}" data-cat="${esc(c.id)}">
    ${esc(c.name)}<span class="badge count">${c.count||0}</span></button>`).join("");
  return `<div class="cat-strip">${pills}
    <button type="button" class="cat-pill new" data-cat-new>+ New category</button></div>`
    + (opts.newCatOpen ? catPopoverHtml() : "");
}

function catPopoverHtml(){
  const allTpls=state.templates||[];
  const tplOpts=allTpls.map(tp=>`<option value="${esc(tp.id)}">${esc(tp.name)}</option>`).join("");
  return `<div class="cat-popover">
    <div class="sec-l" style="margin:0">New category</div>
    <div class="row2">
      <label><span class="cap">Name</span><input id="catName" class="input" placeholder="e.g. Client work"></label>
      <label><span class="cap">Default template</span><select id="catDefTpl" class="input">${tplOpts}</select></label>
    </div>
    <div class="row" style="margin-top:2px">
      <button type="button" class="btn primary sm" id="catCreate">Create</button>
      <button type="button" class="btn ghost sm" id="catCancel">Cancel</button>
    </div>
  </div>`;
}

/* --- preview column: a sandboxed iframe rendering template_demo() -------- */

function previewColHtml(opts){
  if(!opts.previewTemplate) return "";
  const tp=(state.templates||[]).find(x=>x.id===opts.previewTemplate);
  const title=tp?tp.name:opts.previewTemplate;
  let body;
  if(opts.previewLoading) body=`<div class="preview-empty">Rendering sample…</div>`;
  else if(opts.previewError) body=`<div class="preview-empty">${esc(opts.previewError)}</div>`;
  else body=`<div class="preview-frame-wrap"><iframe id="mPreviewFrame" sandbox></iframe></div>`;
  return `<div class="preview-col">
    <div class="preview-h">Preview &mdash; ${esc(title)} &middot; sample data</div>
    ${body}
    <div class="row" style="margin-top:2px">
      <button type="button" class="btn primary sm" id="mUseTpl" ${opts.previewLoading?"disabled":""}>Use this template</button>
      <button type="button" class="btn ghost sm" id="mClosePreview">Close</button>
    </div>
  </div>`;
}

/* Builds the CONTENT of the modal (header + body + footer) - not the
   modal-back/modal wrapper, which openExportDialog creates once and keeps
   stable across re-renders so switching a category or opening the preview
   column doesn't tear down and recreate the whole dialog. */
/* One template card's markup - shared by both grids in the Template section
   (the category's own grid and "Also available") so they can never diverge.
   isDefault is passed in rather than recomputed from tp.category, because a
   category's default_template is an assignment (set_category_default just
   writes cat.default_template - it never touches the template's own static
   .category field), not a fact derivable from the template alone. */
function tplCardHtml(tp, opts, defId){
  const on=opts.template===tp.id;
  const isDefault=tp.id===defId;
  return `<div class="tpl ${on?"on":""}" data-tpl="${esc(tp.id)}" tabindex="0" role="button">
      <span class="tpl-dot" style="background:${esc(tp.accent||"")||"var(--accent)"}"></span>
      <span class="tpl-b">
        <span class="tpl-n">${esc(tp.name)}${isDefault?`<span class="badge accentish">Default</span>`:""}${tp.source==="user"?`<span class="badge">yours</span>`:""}</span>
        <span class="tpl-d">${esc(tp.description||"")}</span>
        <span class="tpl-actions">
          ${isDefault?"":`<button type="button" class="tpl-set-default" data-set-default="${esc(tp.id)}">Set as default</button>`}
          <button type="button" class="tpl-preview-btn" data-preview="${esc(tp.id)}">Preview</button>
        </span>
      </span>
    </div>`;
}

function exportDialogHtml(t, opts, closing){
  const tpls=(state.templates||[]);
  const hasAI=state.config.llm&&state.config.llm.enabled&&(state.config.llm.api_key||"").trim()!=="";
  const cats=state.categories||[];
  const cat=cats.find(c=>c.id===opts.category)||cats[0];
  const defId=cat&&cat.default_template;
  let tplPanelBody;
  if(cat){
    // "Templates in <cat>" is every template whose OWN category matches,
    // union'd with whichever template is currently the category's default -
    // without that union, a brand-new category (or one whose default was set
    // to a template from a different category) would show its own default
    // nowhere at all, which was the bug: the grid, and the category, looked
    // permanently empty. "Also available" is everything left over, and is
    // exactly how an empty category gets its first real member: every card
    // in it still offers "Set as default".
    const inCatIds=new Set(tpls.filter(tp=>tp.category===cat.id).map(tp=>tp.id));
    if(defId) inCatIds.add(defId);
    const inCat=tpls.filter(tp=>inCatIds.has(tp.id))
                     .sort((a,b)=>(a.id===defId?0:1)-(b.id===defId?0:1));
    const others=tpls.filter(tp=>!inCatIds.has(tp.id));
    const primaryHtml=inCat.map(tp=>tplCardHtml(tp,opts,defId)).join("")
      ||`<p class="muted">No templates in this category yet.</p>`;
    const alsoHtml=others.length
      ? `<div class="tpl-sub-l also">Also available</div>
         <div class="tpls">${others.map(tp=>tplCardHtml(tp,opts,defId)).join("")}</div>`
      : "";
    tplPanelBody=`<div class="tpl-sub-l">Templates in ${esc(cat.name)}</div>
      <div class="tpls">${primaryHtml}</div>
      ${alsoHtml}`;
  }else{
    // No category exists at all (the backend refuses to let the last one be
    // deleted, so this is only reachable before list_categories() has ever
    // resolved) - fall back to the old unfiltered flat list.
    tplPanelBody=tpls.length
      ? `<div class="tpls">${tpls.map(tp=>tplCardHtml(tp,opts,null)).join("")}</div>`
      : `<p class="muted">No templates found. Settings &rarr; Exports has the folder to put them in.</p>`;
  }
  const fmt=(k,label,note)=>`<label class="fmt-opt ${opts.formats.includes(k)?"on":""}">
    <input type="checkbox" data-fmt="${k}" ${opts.formats.includes(k)?"checked":""}>
    <span><b>${label}</b><span class="muted">${note}</span></span></label>`;
  return `<div class="modal-h">
      <div><div class="card-t">${closing?"Close &amp; export":"Export"} &mdash; ${esc(t.title)}</div>
      <p class="muted" style="margin:4px 0 0">${t.entries.length} point${t.entries.length===1?"":"s"} will be written into the template you pick.</p></div>
      <button class="btn ghost sm" id="mX">Cancel</button>
    </div>
    <div class="modal-b">
      <div class="sec-l">Category</div>
      ${catStripHtml(opts)}
      <div class="sec-l">Template</div>
      <div class="tpl-panel">
        <div class="tpl-main">${tplPanelBody}</div>
        ${previewColHtml(opts)}
      </div>
      <div class="sec-l">Formats</div>
      <div class="fmts">
        ${fmt("html","HTML","one self-contained file")}
        ${fmt("pdf","PDF","rendered from the template")}
        ${fmt("docx","DOCX","opens in Word")}
        ${fmt("markdown","Markdown","plain text, portable")}
      </div>
      <div class="sec-l">Options</div>
      <label class="mod" style="flex-direction:row;align-items:flex-start;gap:9px">
        <input type="checkbox" id="mPolish" ${opts.polish?"checked":""} ${hasAI?"":"disabled"}>
        <span><b>&#10022; Let AI arrange the prose</b>
        <span class="muted">${hasAI
          ? "The model rewrites wording only. Every citation is checked against your sources afterwards; if any is invented or dropped, your original points are used instead."
          : "Turn on AI assist in Settings to enable this."}</span></span></label>
      <label style="margin-top:10px"><span class="cap">Sub-title <span class="muted">(optional)</span></span>
        <input id="mSub" class="input" placeholder="A line under the title" value="${esc(opts.subtitle||"")}"></label>
      <div id="mStages" class="stages" hidden></div>
    </div>
    <div class="modal-f">
      <span class="muted" id="mHint">Reports land in your exports folder and appear in the Exports tab.</span>
      <button class="btn primary" id="mGo">Export</button>
    </div>`;
}

const STAGE_LABEL={compose:"Compose",ground:"Check citations",fill:"Fill template",
                   render:"Render",verify:"Verify",manifest:"Record"};

function renderStages(active, done){
  const el=document.getElementById("mStages");
  if(!el) return;
  el.hidden=false;
  el.innerHTML=Object.keys(STAGE_LABEL).map((k,i)=>{
    const cls=done.includes(k)?"done":(k===active?"active":"");
    return `<div class="stg ${cls}"><div class="dot2">${i+1}</div><span>${STAGE_LABEL[k]}</span></div>`;
  }).join("");
}

async function openExportDialog(t, closing){
  // Categories/templates need to be fresh before the dialog can pre-select a
  // category (defaultExportOpts reads state.categories/state.templates), so
  // this always re-fetches first. Measured against the real app this is a
  // single local pywebview round-trip - no visible delay before the dialog
  // appears - so there is no debounce/cache here; revisit if that changes.
  try{
    const r=await api.list_categories();
    if(r&&!r.error) state=r;
  }catch(e){ /* fall through on whatever state we already have */ }

  exportDialog=defaultExportOpts(t);
  const host=document.createElement("div");
  host.innerHTML=`<div class="modal-back" id="mBack"><div class="modal glass" id="mModal"></div></div>`;
  const back=host.firstElementChild;
  const modalEl=back.querySelector("#mModal");
  document.body.appendChild(back);
  const close=()=>{back.remove(); exportDialog=null;};
  back.addEventListener("mousedown",e=>{if(e.target===back)close();});

  function renderBody(){
    // Various bridge calls elsewhere (get_state(), init(), refreshFromBridge())
    // replace `state` wholesale with a payload that has no `categories` key -
    // only list_categories() populates it - so if one of those runs while this
    // dialog is still open (e.g. after #mGo's own state=await api.get_state()
    // on the very last export) the strip would go blank on the next re-render.
    // Same self-healing guard as bindSettings() uses for the same reason.
    if(!state.categories||!state.categories.length){
      api.list_categories().then(r=>{if(r&&!r.error){state=r; renderBody();}}).catch(()=>{});
    }
    modalEl.classList.toggle("wide", !!exportDialog.previewTemplate);
    modalEl.innerHTML=exportDialogHtml(t, exportDialog, closing);
    // r.html from api.template_demo is a complete standalone document, so it
    // is handed to the iframe as a srcdoc PROPERTY assignment here - never
    // string-concatenated into the template above and never innerHTML'd.
    const frame=modalEl.querySelector("#mPreviewFrame");
    if(frame&&exportDialog.previewHtml) frame.srcdoc=exportDialog.previewHtml;
    bindBody();
  }

  function bindBody(){
    modalEl.querySelector("#mX").addEventListener("click",close);

    modalEl.querySelectorAll("[data-tpl]").forEach(b=>{
      const pick=()=>{
        exportDialog.template=b.dataset.tpl;
        modalEl.querySelectorAll("[data-tpl]").forEach(x=>x.classList.toggle("on",x===b));
      };
      b.addEventListener("click",pick);
      // .tpl is a div (it now hosts nested "Set as default"/"Preview" buttons,
      // and a <button> cannot nest a <button>), so Enter/Space activation -
      // free on a real button - is wired by hand here for keyboard/AT users.
      b.addEventListener("keydown",e=>{
        if(e.key==="Enter"||e.key===" "){ e.preventDefault(); pick(); }
      });
    });

    modalEl.querySelectorAll("[data-fmt]").forEach(cb=>cb.addEventListener("change",()=>{
      const k=cb.dataset.fmt;
      const i=exportDialog.formats.indexOf(k);
      if(cb.checked&&i<0) exportDialog.formats.push(k);
      if(!cb.checked&&i>=0) exportDialog.formats.splice(i,1);
      cb.closest(".fmt-opt").classList.toggle("on",cb.checked);
    }));

    // Subtitle/polish are synced into exportDialog as they change (not only
    // at #mGo time) because a category switch, a "set default" or opening a
    // preview all rebuild this innerHTML - without this, whatever the user
    // had typed or ticked would be silently discarded on the next re-render.
    const subEl=modalEl.querySelector("#mSub");
    if(subEl) subEl.addEventListener("input",()=>{exportDialog.subtitle=subEl.value;});
    const polishEl=modalEl.querySelector("#mPolish");
    if(polishEl) polishEl.addEventListener("change",()=>{exportDialog.polish=polishEl.checked;});

    // --- category pills -----------------------------------------------
    modalEl.querySelectorAll("[data-cat]").forEach(b=>b.addEventListener("click",()=>{
      const cat=(state.categories||[]).find(c=>c.id===b.dataset.cat);
      if(!cat) return;
      exportDialog.category=cat.id;
      exportDialog.template=cat.default_template;
      exportDialog.previewTemplate=null; exportDialog.previewHtml=null; exportDialog.previewError=null;
      exportDialog.newCatOpen=false;
      renderBody();
    }));
    const newCatBtn=modalEl.querySelector("[data-cat-new]");
    if(newCatBtn) newCatBtn.addEventListener("click",()=>{
      exportDialog.newCatOpen=!exportDialog.newCatOpen;
      renderBody();
    });
    const catCancel=modalEl.querySelector("#catCancel");
    if(catCancel) catCancel.addEventListener("click",()=>{
      exportDialog.newCatOpen=false;
      renderBody();
    });
    const catCreate=modalEl.querySelector("#catCreate");
    if(catCreate) catCreate.addEventListener("click",async()=>{
      const name=(modalEl.querySelector("#catName").value||"").trim();
      const defTpl=modalEl.querySelector("#catDefTpl").value;
      if(!name) return toast("Name the category first.","err");
      if(!defTpl) return toast("Pick a default template.","err");
      const beforeIds=new Set((state.categories||[]).map(c=>c.id));
      const r=await api.save_category({name, default_template:defTpl});
      if(r.error) return toast(r.error,"err");
      state=r;
      const created=(state.categories||[]).find(c=>!beforeIds.has(c.id));
      exportDialog.category=created?created.id:((state.categories||[])[0]||{}).id;
      exportDialog.template=created?created.default_template:exportDialog.template;
      exportDialog.newCatOpen=false;
      renderBody();
      toast("Category created.");
    });

    // --- set-as-default / preview, per template card -------------------
    modalEl.querySelectorAll("[data-set-default]").forEach(b=>b.addEventListener("click",async e=>{
      e.stopPropagation();
      const tplId=b.dataset.setDefault;
      if(!exportDialog.category) return;
      const r=await api.set_category_default(exportDialog.category, tplId);
      if(r.error) return toast(r.error,"err");
      state=r;
      renderBody();
      toast("Default template updated.");
    }));
    modalEl.querySelectorAll("[data-preview]").forEach(b=>b.addEventListener("click",async e=>{
      e.stopPropagation();
      const tplId=b.dataset.preview;
      exportDialog.previewTemplate=tplId;
      exportDialog.previewHtml=null; exportDialog.previewError=null; exportDialog.previewLoading=true;
      renderBody();
      const r=await api.template_demo(tplId);
      if(exportDialog.previewTemplate!==tplId) return; // user moved on meanwhile
      exportDialog.previewLoading=false;
      if(r.error){ exportDialog.previewError=r.error; }
      else{ exportDialog.previewHtml=r.html; }
      renderBody();
    }));
    const useTpl=modalEl.querySelector("#mUseTpl");
    if(useTpl) useTpl.addEventListener("click",()=>{
      exportDialog.template=exportDialog.previewTemplate;
      exportDialog.previewTemplate=null; exportDialog.previewHtml=null; exportDialog.previewError=null;
      renderBody();
    });
    const closePreview=modalEl.querySelector("#mClosePreview");
    if(closePreview) closePreview.addEventListener("click",()=>{
      exportDialog.previewTemplate=null; exportDialog.previewHtml=null; exportDialog.previewError=null;
      renderBody();
    });

    modalEl.querySelector("#mGo").addEventListener("click",async()=>{
      const go=modalEl.querySelector("#mGo"), hint=modalEl.querySelector("#mHint");
      exportDialog.polish=modalEl.querySelector("#mPolish").checked;
      exportDialog.subtitle=modalEl.querySelector("#mSub").value;
      if(!exportDialog.formats.length) return toast("Pick at least one format.","err");
      go.disabled=true; go.textContent="Exporting…";
      hint.textContent=exportDialog.polish
        ? "Asking the model for the prose, then rendering."
        : "Rendering. The PDF step starts a short-lived browser process.";

      // The stages are shown optimistically: the pipeline runs synchronously in
      // Python, so there is no progress channel back. Nothing here claims a stage
      // succeeded -- the result decides that.
      const order=Object.keys(STAGE_LABEL);
      let i=0; const done=[];
      renderStages(order[0],done);
      const tick=setInterval(()=>{
        if(i<order.length-1){done.push(order[i]); i++; renderStages(order[i],done);}
      },700);

      // category is UI-only (it drives the grid filter/pre-selection above);
      // export_topic/export_topic_polished only ever take template/formats/subtitle.
      const opts={template:exportDialog.template,formats:exportDialog.formats,
                  subtitle:exportDialog.subtitle};
      let r;
      try{
        if(closing){
          const c=await api.close_topic(t.id);
          if(c.error){clearInterval(tick); go.disabled=false; go.textContent="Export"; return toast(c.error,"err");}
          state=c;
        }
        r=exportDialog.polish ? await api.export_topic_polished(t.id,opts)
                              : await api.export_topic(t.id,opts);
      }finally{ clearInterval(tick); }

      if(r&&r.error&&!(r.files&&Object.keys(r.files).length)){
        go.disabled=false; go.textContent="Export";
        return toast(r.error,"err");
      }
      renderStages(null, order);
      const wasPolish=exportDialog.polish;
      state=await api.get_state();
      openGroups=groupSet(); if(r.topic_id) openGroups.add(r.topic_id);
      if(closing) tab="closed";
      close(); render();
      showExportToast(r, wasPolish);
    });
  }

  renderBody();
}

function detailHtml(t){
  const n=t.entries.length;
  const pill=t.status==="open"?`<span class="pill open">Open</span>`:`<span class="pill closed">Closed</span>`;
  const subs=(t.subtopics||[]).map(s=>`<button class="chip ${filterSub===s?"active":""}" data-s="${esc(s)}">${esc(s)}<span style="opacity:.5">×</span></button>`).join("");
  const subRow=subs||`<span class="muted">No sub-topics yet.</span>`;
  const hasAI=state.config.llm&&state.config.llm.enabled&&(state.config.llm.api_key||"").trim()!=="";
  const acts=t.status==="open"
    ?`<button class="btn primary sm" id="tClose">Close &amp; export</button><button class="btn danger sm" id="tDel">Delete</button>`
    :`<button class="btn primary sm" id="tExp">Export report…</button>${hasAI?`<button class="btn ghost sm" id="tDraft">Draft AI summary</button>`:""}<button class="btn ghost sm" id="tReopen">Reopen</button><button class="btn danger sm" id="tDel">Delete</button>`;
  const composer=t.status==="open"?`<div class="card sub glass composer">
    <div class="row"><select id="cSub" class="input grow"></select>
      <input id="cLink" class="input grow" placeholder="Source link…">
      <button class="chip" id="cLinkAdd">+ Link</button></div>
    ${sciOn()?`<div class="row"><div class="kinds grow" id="cKinds">
      ${["claim","note","quote"].map(k=>`<button class="k ${compKind===k?"on":""}" data-kind="${k}">${KIND_LABEL[k]}</button>`).join("")}
    </div><span class="muted" style="flex:2;min-width:180px;font-size:11px">${esc(KIND_HINT[compKind]||"")}</span></div>`:""}
    <div class="row"><textarea id="cText" class="input ta grow" rows="2" placeholder="Type or paste the point…" spellcheck="false"></textarea>
      <button class="btn primary" id="cGo">Log point</button></div>
    <div class="row"><input id="cStr" class="input grow" placeholder="String citation…">
      <button class="chip" id="cStrAdd">+ String</button>
      <label class="chip">+ Screenshot<input id="cShot" type="file" accept="image/*" hidden></label>
      <div id="cAtt" class="chips"></div></div>
  </div>`:"";
  const entries=t.entries.slice().sort((a,b)=>a.created<b.created?1:-1);
  const shown=filterSub?entries.filter(e=>(e.subtopic||"")===filterSub):entries;
  const displayShown=shown.slice(0,displayLimit);
  const list=displayShown.map(e=>entryHtml(t,e)).join("")||emptyHtml("No points logged yet","Type one above, or press the capture hotkey from anywhere.");
  const moreBtn=shown.length>displayLimit?`<button class="btn ghost full" id="showMore">Show ${shown.length-displayLimit} more</button>`:"";
  const summaryBlock=summaryDraft?`<div class="card sub glass">
    <div class="card-h"><div class="card-t">AI summary</div></div>
    <div class="e-text" style="white-space:pre-line;margin-bottom:10px">${esc(summaryDraft)}</div>
    <div class="row"><button class="btn ghost sm" id="sumCopy">Copy</button>
      <button class="btn ghost sm" id="sumClose">Dismiss</button></div>
  </div>`:"";
  return `<div class="cards">
    ${summaryBlock}
    <div class="dhead">
      <span class="dot ${t.status}"></span>
      <div class="dh-b"><div class="dh-t">${esc(t.title)}</div>
        <div class="dh-s">${n} point${n===1?"":"s"} · created ${fmt(t.created)}${t.closed?" · closed "+fmt(t.closed):""}</div></div>
      ${pill}
    </div>
    <div class="card sub glass">
      <div class="row">
        <div class="chips grow">${subRow}<button class="chip accent" id="subAdd">+ add</button></div>
        ${filterSub?`<button class="btn ghost sm" id="subClear">Clear filter</button>`:""}
      </div>
    </div>
    ${composer}
    <div class="entries">${list}</div>
    ${moreBtn}
    <div class="card sub glass">
      <div class="row"><div class="muted grow">Closing the topic locks it, then opens the export dialog &mdash; pick a template and the formats you want.</div>${acts}</div>
    </div>
  </div>`;
}

function entryHtml(t,e){
  const when=fmt(e.created);
  const kind=e.kind||"claim";
  const kindBadge=(sciOn()&&kind!=="claim")
    ?`<span class="badge kind ${kind==="note"?"":"tealish"}">${KIND_LABEL[kind]}</span>`:"";
  const sub=e.subtopic?`<span class="tag">${esc(e.subtopic)}</span>`:"";
  const described=s=>!!(s.meta&&Object.keys(s.meta).some(k=>k!=="type"&&s.meta[k]&&String(s.meta[k]).length));
  const srcs=e.sources.map((s,i)=>{
    if(s.type==="link")return `<span class="src-link" data-url="${esc(s.value)}" title="${esc(s.value)}"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M10 13a5 5 0 0 0 7.5.5l3-3a5 5 0 0 0-7-7l-1.7 1.7"/><path d="M14 11a5 5 0 0 0-7.5-.5l-3 3a5 5 0 0 0 7 7l1.7-1.7"/></svg>${esc(s.value)}</span>`;
    if(s.type==="string")return `<span class="src-str" data-copy="${esc(s.value)}" title="Click to copy"><span>“${esc(s.value)}”</span></span>`;
    if(s.type==="image")return `<img class="thumb" data-path="${esc(s.value)}" src="${imgSrc(s.value)}" title="Screenshot">`;
    return "";
  }).join("")||`<span class="muted" style="font-size:11.5px">no source</span>`;
  // In scientific mode a source can be described properly - author, year, journal -
  // so the reference list can be a reference list rather than a row of bare URLs.
  const descBtns=sciOn()?e.sources.map(s=>
    `<button class="src-desc ${described(s)?"has":""}" data-desc="${esc(e.id)}|${esc(s.id)}"
      title="${described(s)?"Edit this source's details":"Describe this source"}">${described(s)?"&#10003; described":"describe"}</button>`).join(""):"";
  const mf=(editSource&&editSource.split("|")[0]===e.id)
    ? metaFormHtml(e,(e.sources||[]).find(x=>x.id===editSource.split("|")[1])) : "";
  const actions=editEntry===e.id
    ?`<div class="edit"><textarea id="eeText" class="input ta" rows="2">${esc(e.text)}</textarea>
       <div class="row"><input id="eeSub" class="input grow" placeholder="Sub-topic" value="${esc(e.subtopic||"")}">
       <button class="btn primary sm" id="eeSave">Save</button><button class="btn ghost sm" id="eeCancel">Cancel</button></div></div>`
    :`<div class="e-actions">
        ${state.config.llm&&state.config.llm.enabled?`<button class="btn ghost sm" data-polish="${e.id}">Polish</button>`:""}
        <button class="btn ghost sm" data-edit="${e.id}">Edit</button>
        <button class="btn danger sm" data-del="${e.id}">Delete</button>
       </div>`;
  return `<div class="card sub glass entry fade">
    <div class="e-meta">${when}${sub}${kindBadge}</div>
    <div class="e-text">${escTop(e.text)}</div>
    <div class="sources">${srcs}</div>
    ${descBtns?`<div class="src-descs">${descBtns}</div>`:""}
    ${mf}
    ${actions}
  </div>`;
}

function metaFormHtml(e,s){
  if(!s) return "";
  const m=s.meta||{};
  const val=k=>{
    if(k!=="authors") return esc(m[k]||"");
    return esc((m.authors||[]).map(a=>[a.family,a.given].filter(Boolean).join(", ")).join("; "));
  };
  const fields=META_LABEL.map(([k,l])=>
    `<label>${l}<input class="input" data-mf="${k}" value="${val(k)}" ${k==="authors"?`placeholder="Smith, Jane; Doe, John"`:""}></label>`).join("");
  return `<div class="meta-form">
    <div class="mf-t">Describe this source</div>
    <div class="mf-s">Fill in what you know and leave the rest blank &mdash; a blank field stays
      blank in the reference rather than being guessed at. With a DOI, Trailmark can fetch the
      rest for you.</div>
    <div class="meta-grid">${fields}</div>
    <div class="row">
      <button class="btn ghost sm" id="mfDoi">Fetch from DOI</button>
      <span class="muted grow" id="mfOut"></span>
      <button class="btn primary sm" id="mfSave">Save details</button>
      <button class="btn ghost sm" id="mfClear">Clear</button>
      <button class="btn ghost sm" id="mfCancel">Cancel</button>
    </div>
  </div>`;
}

function imgSrc(path){
  try{return "file:///"+(path.replace(/\\\\/g,"/"));}catch(e){return "";}
}

function bindDetail(t){
  $("#tDel").addEventListener("click",async()=>{
    if(!confirm("Delete this topic and all its points permanently?"))return;
    const r=await api.delete_topic(t.id);
    if(r.error)return toast(r.error,"err");
    state=r;sel=null;render();toast("Topic deleted.");
  });
  if(t.status==="open"){
    $("#tClose").addEventListener("click",closeAndExport);
    bindComposer(t);
  }else{
    $("#tExp").addEventListener("click",doExport);
    $("#tReopen").addEventListener("click",async()=>{
      const r=await api.reopen_topic(t.id);
      if(r.error)return toast(r.error,"err");
      state=r;render();toast("Topic reopened.");
    });
    const tDraft=$("#tDraft");
    if(tDraft)tDraft.addEventListener("click",async()=>{
      tDraft.disabled=true;tDraft.textContent="Drafting…";
      const r=await api.draft_summary(t.id);
      if(r.error){toast(r.error,"err");tDraft.disabled=false;tDraft.textContent="Draft AI summary";return;}
      summaryDraft=r.text;render();toast("Summary drafted.");
    });
    const sumCopy=$("#sumCopy");
    if(sumCopy)sumCopy.addEventListener("click",()=>copyText(summaryDraft));
    const sumClose=$("#sumClose");
    if(sumClose)sumClose.addEventListener("click",()=>{summaryDraft=null;render();});
  }
  const subAdd=$("#subAdd");
  if(subAdd)subAdd.addEventListener("click",async()=>{
    const name=prompt("New sub-topic name:");
    if(!name||!name.trim())return;
    const r=await api.add_subtopic(t.id,name);
    if(r.error)return toast(r.error,"err");
    state=r;render();
  });
  const sAdd=$("#subClear");
  if(sAdd)sAdd.addEventListener("click",()=>{filterSub=null;displayLimit=20;render();});
  document.querySelectorAll("button[data-s]").forEach(b=>b.addEventListener("click",async()=>{
    const s=b.dataset.s;
    if(b.querySelector("span")){
      if(!confirm("Delete sub-topic "+s+"?"))return;
      const r=await api.delete_subtopic(t.id,s);
      if(r.error)return toast(r.error,"err");
      state=r;render();return;
    }
    filterSub=s;displayLimit=20;render();
  }));
  document.querySelectorAll("[data-url]").forEach(el=>el.addEventListener("click",()=>api.open_url(el.dataset.url)));
  document.querySelectorAll("[data-copy]").forEach(el=>el.addEventListener("click",()=>copyText(el.dataset.copy)));
  document.querySelectorAll(".thumb").forEach(el=>el.addEventListener("click",()=>api.open_path(el.dataset.path)));
  document.querySelectorAll("[data-edit]").forEach(b=>b.addEventListener("click",()=>{editEntry=b.dataset.edit;render();}));
  document.querySelectorAll("[data-del]").forEach(b=>b.addEventListener("click",async()=>{
    if(!confirm("Delete this point?"))return;
    const r=await api.delete_entry(t.id,b.dataset.del);
    if(r.error)return toast(r.error,"err");
    state=r;render();toast("Point deleted.");
  }));
  document.querySelectorAll("[data-polish]").forEach(b=>b.addEventListener("click",async()=>{
    b.disabled=true;b.textContent="Polishing…";
    const r=await api.polish_entry(t.id,b.dataset.polish);
    if(r.error)toast(r.error,"err");
    else{toast("Polished. Review the text and save if it reads well.");editEntry=b.dataset.polish;render();}
  }));
  const eeSave=$("#eeSave");
  if(eeSave)eeSave.addEventListener("click",async()=>{
    const r=await api.update_entry(t.id,editEntry,{text:$("#eeText").value,subtopic:$("#eeSub").value});
    if(r.error)return toast(r.error,"err");
    state=r;editEntry=null;render();toast("Point updated.");
  });
  const eeCancel=$("#eeCancel");
  if(eeCancel)eeCancel.addEventListener("click",()=>{editEntry=null;render();});
  document.querySelectorAll("[data-desc]").forEach(b=>b.addEventListener("click",()=>{
    editSource=(editSource===b.dataset.desc)?null:b.dataset.desc; render();
  }));
  bindMetaForm(t);
  const showMore=$("#showMore");
  if(showMore)showMore.addEventListener("click",()=>{displayLimit+=20;render();});
}

function bindMetaForm(t){
  const save=$("#mfSave");
  if(!save||!editSource) return;
  const [eid,sid]=editSource.split("|");
  const read=()=>{
    const out={};
    document.querySelectorAll("[data-mf]").forEach(i=>{out[i.dataset.mf]=i.value.trim();});
    return out;
  };
  const write=m=>{
    document.querySelectorAll("[data-mf]").forEach(i=>{
      const k=i.dataset.mf;
      if(k==="authors") i.value=(m.authors||[]).map(a=>[a.family,a.given].filter(Boolean).join(", ")).join("; ");
      else i.value=m[k]||"";
    });
  };
  $("#mfDoi").addEventListener("click",async()=>{
    const out=$("#mfOut"); const doi=(read().doi||"").trim();
    if(!doi) return toast("Put the DOI in the DOI field first.","err");
    out.textContent="Looking it up…";
    const r=await api.lookup_doi(doi);
    if(r.error){out.textContent="";return toast(r.error,"err");}
    write(r.meta); out.textContent="Filled in from doi.org — check it before saving.";
  });
  save.addEventListener("click",async()=>{
    const r=await api.set_source_meta(t.id,eid,sid,read());
    if(r.error)return toast(r.error,"err");
    state=r;editSource=null;render();toast("Source described.");
  });
  $("#mfClear").addEventListener("click",async()=>{
    const r=await api.set_source_meta(t.id,eid,sid,{});
    if(r.error)return toast(r.error,"err");
    state=r;editSource=null;render();toast("Details cleared.");
  });
  $("#mfCancel").addEventListener("click",()=>{editSource=null;render();});
}

let compLinks=[],compStrings=[],compImages=[],compKind="claim";
function bindComposer(t){
  const ck=$("#cKinds");
  if(ck) ck.addEventListener("click",e=>{
    const b=e.target.closest("[data-kind]"); if(!b) return;
    compKind=b.dataset.kind; render();
  });
  const sub=$("#cSub");
  sub.innerHTML=[`<option value="">General</option>`].concat((t.subtopics||[]).map(s=>`<option value="${esc(s)}">${esc(s)}</option>`)).join("");
  $("#cLinkAdd").addEventListener("click",()=>{
    const v=$("#cLink").value.trim();if(!v)return;
    try{new URL(v);}catch(e){toast("Not a valid URL.","err");return;}
    compLinks.push(v);$("#cLink").value="";renderAtt();toast("Link added ("+compLinks.length+").");
  });
  $("#cStrAdd").addEventListener("click",()=>{
    const v=$("#cStr").value.trim();if(!v)return;
    compStrings.push(v);$("#cStr").value="";renderAtt();toast("Citation added ("+compStrings.length+").");
  });
  $("#cLink").addEventListener("keydown",e=>{if(e.key==="Enter")$("#cLinkAdd").click();});
  $("#cStr").addEventListener("keydown",e=>{if(e.key==="Enter")$("#cStrAdd").click();});
  $("#cShot").addEventListener("change",e=>{
    const files=[...e.target.files]; if(!files.length) return;
    files.forEach(f=>{
      if(f.size>8*1024*1024){toast("Image too large (8 MB).","err");return;}
      const rd=new FileReader();
      rd.onload=()=>{compImages.push(rd.result);renderAtt();toast("Screenshot ("+compImages.length+").");};
      rd.readAsDataURL(f);
    });
    e.target.value="";
  });
  $("#cGo").addEventListener("click",logComposer);
  $("#cText").addEventListener("keydown",e=>{if(e.key==="Enter"&&!e.ctrlKey&&!e.metaKey){e.preventDefault();logComposer();}});
}
function renderAtt(){
  const wrap=$("#cAtt");
  if(!wrap)return;
  const parts=[];
  compLinks.forEach((v,i)=>parts.push(`<span class="chip active" data-rm="link-${i}" title="${esc(v)}">🔗 ${esc(v.slice(0,22))} ×</span>`));
  compStrings.forEach((v,i)=>parts.push(`<span class="chip active" data-rm="str-${i}" title="${esc(v)}">“ ${esc(v.slice(0,18))} ×</span>`));
  compImages.forEach((_,i)=>parts.push(`<span class="chip active" data-rm="img-${i}">🖼 shot ${i+1} ×</span>`));
  wrap.innerHTML=parts.join("")||`<span class="muted" style="font-size:11.5px">add links, strings or screenshots — all cited</span>`;
  wrap.querySelectorAll("[data-rm]").forEach(el=>el.addEventListener("click",()=>{
    const k=el.dataset.rm;
    if(k.startsWith("link-")) compLinks.splice(parseInt(k.split("-")[1]),1);
    if(k.startsWith("str-")) compStrings.splice(parseInt(k.split("-")[1]),1);
    if(k.startsWith("img-")) compImages.splice(parseInt(k.split("-")[1]),1);
    renderAtt();
  }));
}
async function logComposer(){
  const t=byId(sel);if(!t)return;
  const text=$("#cText").value;
  if(!text.trim()){toast("Write the point first.","err");return;}
  const sources=[];
  compLinks.forEach(v=>sources.push({type:"link",value:v}));
  compStrings.forEach(v=>sources.push({type:"string",value:v}));
  compImages.forEach(v=>sources.push({type:"image",value:v}));
  if(sciOn()&&compKind!=="note"&&!sources.length
     &&((state.config||{}).science||{}).require_source_for_claims){
    toast("Scientific mode: a claim needs a source. Log it as a note instead if it is your own.","err");
    return;
  }
  const r=await api.add_entry(t.id,$("#cSub").value,text,"","",null,sources,compKind);
  if(r.error)return toast(r.error,"err");
  state=r;compLinks=[];compStrings=[];compImages=[];
  $("#cText").value="";renderAtt();render();toast("Point logged — "+sources.length+" source(s).");
}

function closeAndExport(){
  const t=byId(sel); if(!t) return;
  if(!confirm("Close this topic? It will be locked, then exported."))return;
  openExportDialog(t, true);
}
function doExport(){
  const t=byId(sel); if(!t) return;
  openExportDialog(t, false);
}

function showExportToast(ex, isPolished=false){
  const t=document.createElement("div");t.className="toast wide";
  const files=ex.files||{};
  const links=Object.keys(files).sort().map(k=>
    `<a href="#" data-p="${esc(files[k])}">${FORMAT_LABEL[k]||k}</a>`).join(" &nbsp;·&nbsp; ");
  const label=isPolished?"Polished and exported":"Exported";
  const problems=[].concat(ex.warnings||[],ex.errors||[]);
  t.innerHTML=`<b>${label} ${ex.entries} point${ex.entries===1?"":"s"}</b>`
    +`<div class="t-links">${links} &nbsp;·&nbsp; <a href="#" data-p="${esc(ex.folder)}">Folder</a></div>`
    +(problems.length?`<div class="t-warn">${esc(problems.join(" "))}</div>`:"");
  document.getElementById("toasts").appendChild(t);
  const life=problems.length?16000:10000;
  setTimeout(()=>t.classList.add("out"),life);setTimeout(()=>t.remove(),life+400);
  t.querySelectorAll("[data-p]").forEach(a=>a.addEventListener("click",e=>{
    e.preventDefault(); api.open_path(a.dataset.p);}));
}

/* --- Settings -> Exports -> Categories: list + inline management -------- */

function catNewFormHtml(){
  const allTpls=state.templates||[];
  const tplOpts=allTpls.map(tp=>`<option value="${esc(tp.id)}">${esc(tp.name)}</option>`).join("");
  return `<div class="cat-popover">
    <div class="sec-l" style="margin:0">New category</div>
    <div class="row2">
      <label><span class="cap">Name</span><input id="sCatName" class="input" placeholder="e.g. Client work"></label>
      <label><span class="cap">Default template</span><select id="sCatDefTpl" class="input">${tplOpts}</select></label>
    </div>
    <div class="row" style="margin-top:2px">
      <button type="button" class="btn primary sm" id="sCatCreate">Create</button>
      <button type="button" class="btn ghost sm" id="sCatCancel">Cancel</button>
    </div>
  </div>`;
}

function categoriesHtml(){
  const cats=state.categories||[];
  const tpls=state.templates||[];
  const tplOpts=selId=>tpls.map(tp=>`<option value="${esc(tp.id)}" ${tp.id===selId?"selected":""}>${esc(tp.name)}</option>`).join("");
  const rows=cats.map(c=>{
    const n=c.count||0;
    return `<div class="cat-row" data-cat-row="${esc(c.id)}">
      <input class="input cat-name" value="${esc(c.name)}">
      <select class="input cat-def-tpl">${tplOpts(c.default_template)}</select>
      <span class="badge count">${n} template${n===1?"":"s"}</span>
      <button type="button" class="btn ghost sm cat-rename">Rename</button>
      <button type="button" class="btn danger sm cat-delete" ${cats.length<=1?"disabled":""}
        title="${cats.length<=1?"At least one category is required.":"Delete this category"}">Delete</button>
    </div>`;
  }).join("");
  return `<div class="cat-mgr">
    <div class="sec-l" style="margin-top:0">Categories</div>
    <p class="muted">Group your templates so the export dialog can suggest the right default for each kind of report.</p>
    <div class="cat-list">${rows || `<p class="muted">No categories yet.</p>`}</div>
    <div class="row" style="margin-top:10px">
      <button type="button" class="btn ghost sm" id="catNewBtn">+ New category</button>
    </div>
    ${catNewOpen ? catNewFormHtml() : ""}
  </div>`;
}

function settingsHtml(){
  const c=state.config||{};
  const hk=c.hotkey||{};
  const llm=c.llm||{};
  const mods=hk.modifiers||["ctrl","alt"];
  const prov=(state.providers||{});
  const mk=(id,checked,label)=>`<label class="mod"><input type="checkbox" id="${id}" ${checked?"checked":""}> ${label}</label>`;
  const provOpts=Object.keys(prov).map(k=>`<option value="${k}" ${llm.provider===k?"selected":""}>${prov[k].label}</option>`).join("");
  const ex=c.export||{}, app=c.appearance||{}, sci=c.science||{}, cb=c.clipboard||{}, asr=c.asr||{};
  const asrDevs=state.asrDevices||[];
  const asrDeviceOpts=asrDevs.length?asrDevs.map(d=>`<option value="${esc(d.id)}" ${String(asr.device)===String(d.id)?"selected":""}>${esc(d.name)}</option>`).join(""):`<option value="">Default</option>`;
  const styleOpts=CITE_STYLES.map(x=>`<option value="${x.id}" ${(sci.style||"numeric")===x.id?"selected":""}>${esc(x.label)}</option>`).join("");
  const styleHint=(CITE_STYLES.find(x=>x.id===(sci.style||"numeric"))||{}).hint||"";
  const tpls=state.templates||[];
  const builtinN=tpls.filter(t=>t.source==="builtin").length;
  const tplOpts=tpls.map(t=>`<option value="${esc(t.id)}" ${ex.template===t.id?"selected":""}>${esc(t.name)}${t.source==="user"?" (yours)":""}</option>`).join("");
  const xf=ex.formats||["html","pdf","markdown"];
  const fmtBoxes=[["html","HTML"],["pdf","PDF"],["docx","DOCX"],["markdown","Markdown"]].map(
    ([k,l])=>`<label class="fmt-opt ${xf.includes(k)?"on":""}"><input type="checkbox" data-xfmt="${k}" ${xf.includes(k)?"checked":""}><span><b>${l}</b></span></label>`).join("");
  return `<div class="cards">
    <div class="card glass fade">
      <div class="card-h"><div class="card-t">Global hotkey</div></div>
      <p class="muted">Press this combination anywhere on Windows to show or hide the quick capture popup. It never steals focus until you ask for it.</p>
      <div class="row">
        ${mk("mCtrl",mods.includes("ctrl"),"Ctrl")}${mk("mAlt",mods.includes("alt"),"Alt")}${mk("mShift",mods.includes("shift"),"Shift")}${mk("mWin",mods.includes("win"),"Win")}
        <input id="kKey" class="input kkey" maxlength="1" placeholder="P" value="${esc(hk.key||"P")}">
        <button class="btn primary" id="hkSave">Apply hotkey</button>
      </div>
      <p class="muted" id="hkInfo"></p>
    </div>
    <div class="card glass fade">
      <div class="card-h"><div class="card-t">Log clipboard</div></div>
      <p class="muted">Detects image, link or text and logs it to the current topic.</p>
      <div class="row" style="align-items:center;gap:8px">
        <span class="key">Ctrl</span><span class="plus">+</span><span class="key">Alt</span><span class="plus">+</span><span class="key">V</span>
        <button class="sw ${cb.enabled?"on":""}" id="cbSw" type="button" role="switch" aria-checked="${cb.enabled?"true":"false"}" aria-label="Enable clipboard hotkey" style="margin-left:auto"><span class="kn"></span></button>
      </div>
    </div>
    <div class="card glass fade">
      <div class="card-h"><div class="card-t">AI assist</div></div>
      <p class="muted">Optional and bring-your-own-key. Polish a point, summon a summary, or generate a polished report on export. Supports <b>OpenAI</b>, <b>OpenRouter</b>, <b>Mistral AI</b>, <b>Google AI Studio (Gemini)</b>, and <b>AvalAI</b>. Default: <b>OpenRouter</b> + <b>deepseek/deepseek-v4-flash</b>.</p>
      <div class="row"><label class="mod" style="flex-direction:row"><input type="checkbox" id="lEnabled" ${llm.enabled?"checked":""}> Enable AI assist</label></div>
      <div class="grid3">
        <label>Provider<select id="lProvider" class="input">${provOpts}</select></label>
        <label>Model<input id="lModel" class="input" value="${esc(llm.model||"")}"></label>
        <label>Base URL<input id="lBase" class="input" placeholder="auto" value="${esc(llm.base_url||"")}"></label>
      </div>
      <div class="row">
        <label class="grow" style="min-width:200px">API key<input id="lKey" class="input" type="password" placeholder="sk-…" value="${esc(llm.api_key||"")}"></label>
        <button class="btn ghost" id="lShow">Show</button>
        <button class="btn primary" id="lSave">Save settings</button>
      </div>
      <div class="row"><button class="btn ghost sm" id="lTest">Test connection</button><span class="muted" id="lTestOut"></span></div>
    </div>
    <div class="card glass fade">
      <div class="card-h"><div class="card-t">Voice logging</div></div>
      <div class="row" style="align-items:flex-start;gap:10px">
        <div style="flex:1;min-width:0">
          <b style="font-size:12.5px;font-weight:650;display:block">Auto-log speech as notes</b>
          <p class="muted" style="margin:3px 0 0">Listens on your microphone only while this is on. Nothing is stored until a phrase is transcribed.</p>
        </div>
        <button class="sw ${asr.enabled?"on":""}" id="asrSw" type="button" role="switch" aria-checked="${asr.enabled?"true":"false"}" aria-label="Enable auto-log speech as notes" style="flex:none"><span class="kn"></span></button>
      </div>
      <div class="grid3" style="margin-top:12px">
        <label>Endpoint<input id="asrEndpoint" class="input" placeholder="https://api.openai.com/v1" value="${esc(asr.endpoint||"")}"></label>
        <label>Model<input id="asrModel" class="input" placeholder="whisper-1" value="${esc(asr.model||"whisper-1")}"></label>
        <label>Microphone<select id="asrDevice" class="input">${asrDeviceOpts}</select></label>
      </div>
      <p class="muted">Any OpenAI-compatible /audio/transcriptions endpoint &mdash; OpenAI, Groq&hellip; For Groq, use <b>https://api.groq.com/openai/v1</b> with model <b>whisper-large-v3-turbo</b>.</p>
      <div class="row">
        <label class="grow" style="min-width:200px">API key<input id="asrKey" class="input" type="password" placeholder="sk-…" value="${esc(asr.api_key||"")}"></label>
        <button class="btn ghost" id="asrShow">Show</button>
        <button class="btn primary" id="asrSave">Save settings</button>
      </div>
      <label style="display:block;margin-top:12px">Sensitivity
        <input id="asrSensitivity" type="range" min="0" max="100" value="${asr.sensitivity!=null?asr.sensitivity:50}" style="width:100%;accent-color:var(--accent);margin-top:6px">
      </label>
      <div class="row"><button class="btn ghost sm" id="asrTest">Test 5 seconds</button><span class="muted" id="asrTestOut"></span></div>
      <div class="row" style="background:var(--accent-tint);border:1px solid var(--accent);border-radius:var(--r-lg);padding:14px 16px;margin-top:12px;align-items:flex-start">
        <div>
          <b style="display:block;font-size:12.5px;margin-bottom:4px">Voice logging is strictly opt-in.</b>
          <p class="muted" style="margin:0">Trailmark only listens to your own microphone while this switch is on &mdash; never system audio, other apps, or call/loopback audio. Turning it off immediately stops capture. Nothing is recorded to disk; only the transcribed text becomes a logged point.</p>
        </div>
      </div>
    </div>
    <div class="card glass fade">
      <div class="card-h"><div class="card-t">Appearance</div></div>
      <p class="muted">Trailmark follows your Windows light/dark setting by default. Override it here if you want one or the other regardless.</p>
      <div class="segmented" id="themeSeg">
        ${["system","light","dark"].map(k=>`<button class="seg ${(app.theme||"system")===k?"active":""}" data-theme="${k}">${k[0].toUpperCase()+k.slice(1)}</button>`).join("")}
      </div>
    </div>
    <div class="card glass fade">
      <div class="card-h"><div class="card-t">Scientific mode</div></div>
      <p class="muted">Off, a point is a point. On, Trailmark keeps three things apart in every
      report: a <b>claim</b> you took from a source, a <b>quotation</b> reproduced word for word,
      and a <b>note</b> of your own. Notes get their own section and are never given a citation;
      quotations are never reworded. The AI polish pass is held to the same rules mechanically
      &mdash; a draft that attaches a citation to your note, drops a note, or rewrites a quotation
      is rejected and your own text is exported instead.</p>
      <div class="row"><label class="mod" style="flex-direction:row"><input type="checkbox" id="sciOn" ${sci.enabled?"checked":""}> Enable scientific mode</label></div>
      <div class="grid3">
        <label>Citation style<select id="sciStyle" class="input">${styleOpts}</select></label>
        <label class="mod" style="flex-direction:row;align-self:end;padding-bottom:8px"><input type="checkbox" id="sciSep" ${sci.separate_notes!==false?"checked":""}> Notes in their own section</label>
        <label class="mod" style="flex-direction:row;align-self:end;padding-bottom:8px"><input type="checkbox" id="sciReq" ${sci.require_source_for_claims?"checked":""}> A claim must have a source</label>
      </div>
      <p class="muted" id="sciHint">${esc(styleHint)}</p>
      <div class="row"><button class="btn primary" id="sciSave">Save scientific mode</button></div>
      <p class="muted">These styles are careful approximations, not a CSL processor &mdash; good
      enough for a working document and honest about it. A source is described from the fields you
      fill in on it, and a field you leave blank stays blank: Trailmark will print a reference with
      no author rather than invent one. For submission-grade output, export the Markdown and run it
      through Pandoc with a real <b>.csl</b> file.</p>
    </div>
    <div class="card glass fade">
      <div class="card-h"><div class="card-t">Exports</div></div>
      <p class="muted">Defaults for the export dialog. Whatever you pick in the dialog itself wins for that one export.</p>
      <div class="grid3">
        <label>Default template<select id="xTpl" class="input">${tplOpts}</select></label>
        <label>Your name <span class="muted" style="font-weight:400">(appears on reports)</span><input id="xAuthor" class="input" value="${esc(ex.author||"")}" placeholder="optional"></label>
        <label>Organisation<input id="xOrg" class="input" value="${esc(ex.org||"")}" placeholder="optional"></label>
      </div>
      <div class="row" style="margin-top:10px">
        <div class="fmts grow">${fmtBoxes}</div>
      </div>
      <div class="row" style="margin-top:12px">
        <button class="btn primary" id="xSave">Save export defaults</button>
        <button class="btn ghost" id="xFolder">Open my templates folder</button>
        <span class="muted" id="xEngines">Checking PDF engines…</span>
      </div>
      <p class="muted" style="margin-top:10px">Trailmark ships ${builtinN} template${builtinN===1?"":"s"} and picks up any you add yourself.
      A template is a folder with a <b>template.json</b> and a <b>template.html</b>; the HTML uses
      <b>{{title}}</b>, <b>{{body}}</b>, <b>{{references}}</b> and friends, which Trailmark fills in.
      Drop your folder next to the built-ins and it shows up in the dialog. The full field list and a
      prompt you can hand to an AI assistant to write one for you are in <b>TEMPLATES.md</b> in the app folder.</p>
      ${categoriesHtml()}
    </div>
    <div class="card glass fade">
      <div class="card-h"><div class="card-t">Data &amp; privacy</div></div>
      <p class="muted">Everything is stored locally next to the app: <b>points.json</b> for your topics, <b>attachments/</b> for screenshots, <b>exports/</b> for closed reports. No cloud, no telemetry. The AI assist feature only sends a point’s text to the provider you chose, and only when you click <b>Polish</b> or <b>Export</b>.</p>
    </div>
  </div>`;
}

function asrState(state,detail){
  const chip=$("#asrChip");
  if(!chip)return;
  chip.classList.remove("show","listening","transcribing","logged","error");
  if(state==="off"||state==="no_topic"){
    chip.innerHTML="";
    return;
  }
  chip.classList.add("show");
  if(state==="listening"){
    chip.classList.add("listening");
    chip.innerHTML='<span class="dot3"></span><span class="tx"></span>';
    chip.querySelector(".tx").textContent="Listening";
  }else if(state==="transcribing"){
    chip.classList.add("transcribing");
    chip.innerHTML='<span class="ring"></span><span class="tx"></span>';
    chip.querySelector(".tx").textContent="Transcribing…";
  }else if(state==="logged"){
    chip.classList.add("logged");
    chip.innerHTML='<svg class="check" viewBox="0 0 20 20" fill="none" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 10l4 4 8-9"/></svg><span class="tx"></span>';
    chip.querySelector(".tx").textContent=detail?('Logged · "'+detail+'"'):"Logged";
  }else if(state==="error"){
    chip.classList.add("error");
    chip.innerHTML='<span class="tx"></span>';
    chip.querySelector(".tx").textContent=detail||"Voice logging error";
  }else{
    chip.classList.remove("show");
    chip.innerHTML="";
  }
}
window.asrState=asrState;

function bindSettings(){
  // state.categories is only populated by list_categories() - get_state() never
  // touches it, so on a fresh app load (Settings opened before any export dialog)
  // the Categories list below would render empty forever without this.
  if(!state.categories){
    api.list_categories().then(r=>{if(r&&!r.error){state=r;render();}}).catch(()=>{});
  }
  const hkInfo=$("#hkInfo");
  api.get_config().then(c=>{
    const hk=c.hotkey||{};
    hkInfo.textContent="Current: "+(hk.modifiers||[]).map(m=>m[0].toUpperCase()+m.slice(1)).join("+")+"+"+(hk.key||"P");
  });
  $("#hkSave").addEventListener("click",async()=>{
    const mods=[];["ctrl","alt","shift","win"].forEach(m=>{if($("#m"+m[0].toUpperCase()+m.slice(1)).checked)mods.push(m);});
    const key=$("#kKey").value.trim();
    if(!mods.length){toast("Pick at least one modifier.","err");return;}
    if(!key){toast("Enter a key letter.","err");return;}
    const r=await api.save_hotkey({modifiers:mods,key:key.toUpperCase()});
    if(r.error)return toast(r.error,"err");
    hkInfo.textContent="Current: "+mods.map(m=>m[0].toUpperCase()+m.slice(1)).join("+")+"+"+key.toUpperCase();
    toast("Hotkey updated.");
  });
  const cbSw=$("#cbSw");
  if(cbSw) cbSw.addEventListener("click",async()=>{
    const next=!cbSw.classList.contains("on");
    cbSw.classList.toggle("on",next);cbSw.setAttribute("aria-checked",next?"true":"false");
    const r=await api.save_clipboard({enabled:next,modifiers:["ctrl","alt"],key:"V"});
    if(r&&r.error){
      toast(r.error,"err");
      cbSw.classList.toggle("on",!next);cbSw.setAttribute("aria-checked",!next?"true":"false");
      return;
    }
    state=r;
    toast("Clipboard hotkey "+(next?"enabled.":"disabled."));
  });
  const show=$("#lShow");
  show.addEventListener("click",()=>{const k=$("#lKey");k.type=k.type==="password"?"text":"password";show.textContent=k.type==="password"?"Show":"Hide";});
  $("#lSave").addEventListener("click",async()=>{
    const cfg={
      llm:{
        enabled:$("#lEnabled").checked,
        provider:$("#lProvider").value,
        model:$("#lModel").value,
        base_url:$("#lBase").value,
        api_key:$("#lKey").value,
      }
    };
    const r=await api.save_llm(cfg.llm);
    if(r.error)return toast(r.error,"err");
    state=r;toast("AI settings saved.");
  });
  $("#lTest").addEventListener("click",async()=>{
    const out=$("#lTestOut");out.textContent="Testing…";
    const cfg={
      enabled:true,
      provider:$("#lProvider").value,
      model:$("#lModel").value,
      base_url:$("#lBase").value,
      api_key:$("#lKey").value,
    };
    const r=await api.test_llm(cfg);
    if(r.ok)out.textContent="OK — "+(r.reply||"connected");
    else{out.textContent="";toast(r.error||"Connection failed.","err");}
  });
  $("#lProvider").addEventListener("change",()=>{
    const k=$("#lProvider").value;
    const p=(state.providers||{})[k];
    if(p){if(!$("#lModel").value||p.model)$("#lModel").value=p.model||"";}
  });

  // --- voice logging (ASR) ---
  if(!state.asrDevices){
    api.list_asr_devices().then(r=>{state.asrDevices=Array.isArray(r)?r:[];render();}).catch(()=>{state.asrDevices=[];});
  }
  function asrCfgFromForm(){
    const devEl=$("#asrDevice");
    const devVal=devEl?devEl.value:"";
    return{
      endpoint:$("#asrEndpoint").value,
      model:$("#asrModel").value,
      api_key:$("#asrKey").value,
      language:"",
      device:devVal!==""?Number(devVal):"",
      sensitivity:Number($("#asrSensitivity").value)||0,
    };
  }
  const asrSw=$("#asrSw");
  if(asrSw) asrSw.addEventListener("click",async()=>{
    const next=!asrSw.classList.contains("on");
    asrSw.classList.toggle("on",next);asrSw.setAttribute("aria-checked",next?"true":"false");
    const cfg=asrCfgFromForm();cfg.enabled=next;
    const r=await api.save_asr(cfg);
    if(r&&r.error){
      toast(r.error,"err");
      asrSw.classList.toggle("on",!next);asrSw.setAttribute("aria-checked",!next?"true":"false");
      return;
    }
    state=r;
    toast("Voice logging "+(next?"enabled.":"disabled."));
  });
  const asrShow=$("#asrShow");
  if(asrShow) asrShow.addEventListener("click",()=>{const k=$("#asrKey");k.type=k.type==="password"?"text":"password";asrShow.textContent=k.type==="password"?"Show":"Hide";});
  const asrSaveBtn=$("#asrSave");
  if(asrSaveBtn) asrSaveBtn.addEventListener("click",async()=>{
    const cfg=asrCfgFromForm();cfg.enabled=asrSw?asrSw.classList.contains("on"):false;
    const r=await api.save_asr(cfg);
    if(r&&r.error)return toast(r.error,"err");
    state=r;toast("Voice logging settings saved.");
  });
  const asrTestBtn=$("#asrTest");
  if(asrTestBtn) asrTestBtn.addEventListener("click",async()=>{
    const out=$("#asrTestOut");out.textContent="Testing…";
    const r=await api.test_asr(5);
    if(r&&r.error){out.textContent="";toast(r.error,"err");}
    else out.textContent=(r&&r.text)?r.text:"(no speech detected)";
  });

  // --- scientific mode ---
  const sciStyle=$("#sciStyle");
  if(sciStyle){
    sciStyle.addEventListener("change",()=>{
      const x=CITE_STYLES.find(y=>y.id===sciStyle.value);
      $("#sciHint").textContent=x?x.hint:"";
    });
    $("#sciSave").addEventListener("click",async()=>{
      const r=await api.save_science({
        enabled:$("#sciOn").checked,
        style:sciStyle.value,
        separate_notes:$("#sciSep").checked,
        require_source_for_claims:$("#sciReq").checked,
      });
      if(r.error)return toast(r.error,"err");
      state=r;render();
      toast($("#sciOn").checked?"Scientific mode on.":"Scientific mode off.");
    });
  }

  // --- appearance ---
  const seg=$("#themeSeg");
  if(seg) seg.addEventListener("click",async e=>{
    const b=e.target.closest("[data-theme]"); if(!b) return;
    const theme=b.dataset.theme;
    applyTheme(theme);
    seg.querySelectorAll(".seg").forEach(x=>x.classList.toggle("active",x===b));
    const r=await api.save_appearance({theme});
    if(r&&!r.error) state=r;
  });

  // --- export defaults ---
  const xf=$("#xTpl");
  if(xf){
    document.querySelectorAll("[data-xfmt]").forEach(cb=>cb.addEventListener("change",()=>{
      cb.closest(".fmt-opt").classList.toggle("on",cb.checked);
    }));
    $("#xSave").addEventListener("click",async()=>{
      const formats=[...document.querySelectorAll("[data-xfmt]")].filter(c=>c.checked).map(c=>c.dataset.xfmt);
      if(!formats.length) return toast("Pick at least one default format.","err");
      const r=await api.save_export({template:$("#xTpl").value,formats,
        author:$("#xAuthor").value,org:$("#xOrg").value});
      if(r.error)return toast(r.error,"err");
      state=r; toast("Export defaults saved.");
    });
    $("#xFolder").addEventListener("click",async()=>{
      const r=await api.open_template_dir();
      if(r.error)return toast(r.error,"err");
      toast("Opened "+r.path);
    });
    api.pdf_engines().then(r=>{
      const out=$("#xEngines"); if(!out) return;
      const found=Object.keys((r&&r.engines)||{}).filter(k=>r.engines[k]);
      out.textContent=found.length
        ? "PDF via "+found[0]+(found.length>1?" (also: "+found.slice(1).join(", ")+")":"")
        : "No PDF engine found — install Edge or Chrome.";
    }).catch(()=>{});
  }

  // --- categories ---
  bindCategories();
}

function bindCategories(){
  const mgr=$(".cat-mgr");
  if(!mgr) return;

  mgr.querySelectorAll(".cat-row").forEach(row=>{
    const id=row.dataset.catRow;
    row.querySelector(".cat-def-tpl").addEventListener("change",async e=>{
      const r=await api.set_category_default(id, e.target.value);
      if(r.error) return toast(r.error,"err");
      state=r; renderMain(); toast("Default template updated.");
    });
    row.querySelector(".cat-rename").addEventListener("click",async()=>{
      const name=(row.querySelector(".cat-name").value||"").trim();
      if(!name) return toast("Name the category first.","err");
      const r=await api.save_category({id, name});
      if(r.error) return toast(r.error,"err");
      state=r; renderMain(); toast("Category renamed.");
    });
    row.querySelector(".cat-delete").addEventListener("click",async()=>{
      if(!confirm("Delete this category? Its templates keep working, but stop suggesting a default here.")) return;
      const r=await api.delete_category(id);
      if(r.error) return toast(r.error,"err");
      state=r; renderMain(); toast("Category deleted.");
    });
  });

  const newBtn=mgr.querySelector("#catNewBtn");
  if(newBtn) newBtn.addEventListener("click",()=>{
    catNewOpen=!catNewOpen;
    renderMain();
  });
  const cancelBtn=mgr.querySelector("#sCatCancel");
  if(cancelBtn) cancelBtn.addEventListener("click",()=>{
    catNewOpen=false;
    renderMain();
  });
  const createBtn=mgr.querySelector("#sCatCreate");
  if(createBtn) createBtn.addEventListener("click",async()=>{
    const name=(mgr.querySelector("#sCatName").value||"").trim();
    const defTpl=mgr.querySelector("#sCatDefTpl").value;
    if(!name) return toast("Name the category first.","err");
    if(!defTpl) return toast("Pick a default template.","err");
    const r=await api.save_category({name, default_template:defTpl});
    if(r.error) return toast(r.error,"err");
    state=r; catNewOpen=false; renderMain();
    toast("Category created.");
  });
}

/* --- theme -------------------------------------------------------------- */

function applyTheme(pref){
  const el=document.documentElement;
  if(pref==="light"||pref==="dark") el.setAttribute("data-theme",pref);
  else el.removeAttribute("data-theme");   // fall back to prefers-color-scheme
}

document.getElementById("seg").addEventListener("click",e=>{
  const b=e.target.closest(".seg");if(!b)return;
  tab=b.dataset.tab;sel=null;editEntry=null;filterSub=null;displayLimit=20;render();
});
document.getElementById("newBtn").addEventListener("click",()=>{tab="open";sel=null;displayLimit=20;render();});
document.getElementById("popupBtn").addEventListener("click",()=>api.show_popup());
document.getElementById("tbCapture").addEventListener("click",()=>api.show_popup());
// system -> light -> dark -> system. Three states, because "follow Windows" is a
// real preference and not the same as whichever theme it happens to resolve to.
document.getElementById("tbTheme").addEventListener("click",async()=>{
  const order={system:"light",light:"dark",dark:"system"};
  const next=order[((state.config||{}).appearance||{}).theme||"system"];
  applyTheme(next);
  const r=await api.save_appearance({theme:next});
  if(r&&!r.error)state=r;
  render();
  if(tab==="settings"){renderMain();}
});

function refreshFromBridge(){
  api.get_state().then(r=>{if(r&&!r.error){state=r;render();}}).catch(()=>{});
}

async function init(){
  state=await api.get_state();
  applyTheme(((state.config||{}).appearance||{}).theme||"system");
  // the list of citation styles lives in citation.py; the UI asks for it rather
  // than keeping a second copy that can drift
  try{const cs=await api.citation_styles(); if(cs&&cs.styles&&cs.styles.length)CITE_STYLES=cs.styles;}catch(e){}
  render();
}
if(window.pywebview){init();}else{window.addEventListener("pywebviewready",init);}
</script></body></html>
"""

POPUP_HTML = POPUP_HTML.replace("__BASE_CSS__", BASE_CSS)
MAIN_HTML = MAIN_HTML.replace("__BASE_CSS__", BASE_CSS)