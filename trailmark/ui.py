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
/* a hotkey another application already holds */
.taken{color:var(--danger);font-weight:650}
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

/* --- Trailmark dialogs: the styled replacement for native prompt()/confirm().
   The browser's own ("This page says…") box cannot be themed, so every naming
   and every destructive question goes through this instead. Same markup in the
   popup and the main window: a scrim plus a raised card built from the design
   tokens above, so light/dark follow the theme for free. One instance at a
   time; Esc / scrim click / Cancel resolves as cancel. */
.tm-back{position:fixed;inset:0;z-index:200;display:flex;align-items:center;
  justify-content:center;padding:18px;background:var(--scrim);animation:fade .16s ease}
.tm-modal{width:min(420px,100%);max-height:calc(100vh - 36px);overflow-y:auto;
  background:var(--surface-raised);border:1px solid var(--border-strong);
  border-radius:var(--r-xl);box-shadow:var(--shadow-3);
  padding:20px 20px 16px;display:flex;flex-direction:column;gap:10px}
.tm-modal h3{margin:0;font-family:var(--font-display);font-size:15px;font-weight:700;
  color:var(--content);word-break:break-word}
.tm-modal p{margin:0;font-size:13px;line-height:1.55;color:var(--content-secondary);
  word-break:break-word}
.tm-modal p b{color:var(--content)}
.tm-actions{display:flex;gap:8px;justify-content:flex-end;margin-top:6px;flex-wrap:wrap}
.tm-actions .btn{min-width:96px}
body.mini .tm-back{padding:10px}
body.mini .tm-modal{padding:14px;gap:8px}

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
#unifiedSec{overflow-y:auto;flex:1}
.card{padding:14px;display:flex;flex-direction:column;gap:9px}
.unified{gap:12px}
#voiceSec{display:flex;flex-direction:column;gap:7px}
.udiv{height:1px;background:var(--border);margin:2px 0}
.big{font-size:17px;font-weight:700}
.trow{display:flex;gap:8px;align-items:center}
.srcbar{display:flex;gap:7px}
.srcbar .grow{flex:1;min-width:0}
.attrow{display:flex;gap:7px;align-items:center;flex-wrap:wrap}
.logrow{display:flex;gap:9px;margin-top:2px}
.logrow .btn.primary{flex:1}
.hint{font-size:11px;color:var(--content-muted);text-align:center;letter-spacing:.03em}
.keys{display:flex;flex-wrap:wrap;gap:5px;justify-content:center;margin-top:6px}
.kkey{font:600 10.5px var(--font-mono);padding:3px 8px;border-radius:var(--r-sm);
  background:var(--surface-sunken);border:1px solid var(--border);
  color:var(--content-muted);white-space:nowrap;
  transition:background .3s,color .3s,border-color .3s}
.kkey b{font-weight:700}
.kkey.flash{background:var(--accent-tint);color:var(--accent);border-color:var(--accent)}
.recent{font-size:11.5px;color:var(--content-secondary);border-top:1px solid var(--border);
  padding-top:8px;margin-top:2px}
.recent b{color:var(--content);font-weight:600}

/* Voice and typing write into ONE draft.

   The draft lives in Python (voicecmd.Draft) because dictation lands there
   from threads this page cannot see. The point box below is a view of it:
   what was said is APPENDED to what was typed (voicecmd.Draft.append via
   _join), and a misheard word is fixed the way a typo is.

   Quick capture is ONE unified card under the top bar: voice bar (state +
   wave), topic (start/select), then the point composer as-is. The old
   Source/Tab/Session/Finish voice buttons are gone on purpose - those verbs
   still work by voice and by global hotkey, but the card has a single action
   row (Log point / Clear / Hide) so there is one place to file, not two.
   Removing a source stays in the full view: at 150px tall a delete target
   sits a few pixels from Log, and a mis-click there has no undo.
   The mini bar is not a second window - it is THIS window resized by ctypes
   (see Controller.set_popup_mini) with a class on <body>. */
.vcard{padding:0;display:flex;flex-direction:column;gap:7px}
.vhead{display:flex;align-items:center;gap:7px;min-width:0}
.vstate{flex:none;display:inline-flex;align-items:center;gap:6px;font-size:11px;font-weight:650;
  padding:3px 9px;border-radius:var(--r-pill);background:var(--surface-sunken);
  color:var(--content-secondary);white-space:nowrap;max-width:62%;overflow:hidden;text-overflow:ellipsis}
.vstate .d{width:6px;height:6px;border-radius:50%;background:var(--content-muted);flex:none}
.vstate.on{color:var(--accent);background:var(--accent-tint)}
.vstate.on .d{background:var(--accent);animation:pulse 1.6s ease-in-out infinite}
.vstate.err{color:var(--danger);background:var(--danger-tint)}
.vstate.err .d{background:var(--danger);animation:none}
.vcounts{display:flex;gap:5px;flex:none}
.vpill{font-size:10.5px;padding:2px 8px;border-radius:var(--r-pill);border:0;
  background:var(--surface-sunken);color:var(--content-secondary);white-space:nowrap;font-family:inherit}
.vpill.hot{background:var(--accent-tint);color:var(--accent);font-weight:650}
button.vpill{cursor:pointer}
.vtopic{flex:1;min-width:0;font-size:11px;color:var(--content-muted);text-align:right;
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
/* The wave: what the microphone is hearing right now, drawn from the same
   10 ms buckets the VAD decides on. Accent where it was loud enough to count
   as speech, muted where it was not - so "why did it not hear me" has an
   answer you can see. */
.vwave{display:block;width:100%;height:34px;border-radius:var(--r-sm);background:var(--surface-sunken)}
.vheard{font-size:12px;line-height:1.35;color:var(--content-secondary);min-height:16px;
  display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.vdraft{display:none}
.vacts{display:none;gap:5px}
.vacts .btn{flex:1;font-size:11px;padding:6px 4px;min-width:0}
.icobtn{flex:none;display:inline-flex;align-items:center;justify-content:center;
  width:24px;height:24px;padding:0;border-radius:var(--r-sm);border:1px solid var(--border);
  background:transparent;color:var(--content-secondary);cursor:pointer}
.icobtn:hover{color:var(--content);border-color:var(--border-strong)}
.icobtn[aria-checked="true"]{color:var(--accent);border-color:var(--accent);
  background:var(--accent-tint)}
.icobtn svg{width:13px;height:13px;stroke:currentColor;fill:none;stroke-width:2;
  stroke-linecap:round;stroke-linejoin:round}
.dhead{display:flex;align-items:baseline;gap:8px}
.dhead label{flex:1}
.dmeta{font-size:10.5px;color:var(--content-muted);white-space:nowrap}
.dmeta b{color:var(--accent);font-weight:650}
#ptText{min-height:92px}
.kinds .k.auto{font-style:italic}

/* Collapsed. The window is 396x176 physical, so everything that is not the
   voice bar is removed from the flow rather than merely scrolled past.
   The unified card stays a single card - mini only hides the topic/point
   blocks and the shortcut hints, keeping voice bar + draft tail + Log. */
body.mini .win{padding:8px;gap:5px;overflow:hidden}
body.mini header{padding:5px 8px;gap:7px}
body.mini header img{height:18px}
body.mini .app{font-size:12px}
body.mini .hk,body.mini #openApp{display:none}
body.mini #noTopic,body.mini #topicSelWrap,body.mini #logPanel,
body.mini #keyHints,body.mini #recent,body.mini .udiv{display:none!important}
body.mini #unifiedSec{overflow:hidden}
body.mini .card.unified{padding:8px 10px;gap:5px}
body.mini .vwave{height:22px}
body.mini .vheard{display:none}
body.mini .vdraft{display:block;font-size:11.5px;line-height:1.3;color:var(--content);
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-height:15px}
body.mini .vacts{display:flex}
/* The 176px bar has no room for a full-height button: at control height the
   Log button alone pushes the card past the window and earns a scrollbar. */
body.mini .vacts .btn{min-height:28px;padding:4px 4px}
body.mini .vtopic{display:none}
</style></head><body>
<div class="win">
  <header class="glass pywebview-drag-region">
    <img src="__ICON__" alt="">
    <div class="tt"><div class="app">Trailmark</div><div class="hk" id="hkLabel"></div></div>
    <button id="openApp" class="chip accent" title="Open the main window">Open app</button>
    <button id="voiceBtn" class="icobtn" type="button" role="switch" aria-checked="false"
            title="Always-on voice"><svg viewBox="0 0 20 20"><path d="M10 3.5a2.5 2.5 0 0 1 2.5 2.5v4a2.5 2.5 0 0 1-5 0V6A2.5 2.5 0 0 1 10 3.5z"/><path d="M5.5 9.5A4.5 4.5 0 0 0 10 14a4.5 4.5 0 0 0 4.5-4.5"/><path d="M10 14v2.5"/></svg></button>
    <button id="miniBtn" class="icobtn" type="button" role="switch" aria-checked="false"
            title="Collapse to the voice bar"><svg viewBox="0 0 20 20"><path d="M4 10h12"/></svg></button>
    <div class="pulse" id="liveDot"></div>
  </header>

  <section id="unifiedSec">
    <div class="card glass fade unified">
      <div id="voiceSec">
        <div class="vhead">
          <span class="vstate" id="vState"><span class="d"></span><span class="tx">Voice off</span></span>
          <span class="vcounts" id="vCounts"></span>
          <span class="vtopic" id="vTopic" dir="auto"></span>
        </div>
        <canvas class="vwave" id="vWave" aria-label="Microphone level"></canvas>
        <div class="vheard" id="vHeard" dir="auto"></div>
        <div class="vdraft" id="vDraft" dir="auto"></div>
        <div class="vacts">
          <button class="btn primary" id="vLog" type="button" title="Same as saying “log”">Log</button>
        </div>
      </div>
      <div class="udiv"></div>
      <div id="noTopic" hidden>
        <div class="big">Start a topic</div>
        <p class="muted" id="ntWhy">No open topic yet. Give this research a name to begin.</p>
        <input id="ntTitle" class="input" dir="auto" placeholder="Topic name — e.g. Rust borrow checker">
        <div class="logrow">
          <button id="ntGo" class="btn primary">Start topic</button>
          <button id="ntCancel" class="btn ghost" hidden>Cancel</button>
        </div>
      </div>
      <div id="topicSelWrap">
        <div class="trow" id="tpRow">
          <select id="tpSel" class="input"></select>
          <button id="tpNew" class="chip">+ New</button>
        </div>
        <div id="subRow">
          <label>Sub-topic</label>
          <div class="chips" id="subChips"></div>
        </div>
      </div>
      <div class="udiv"></div>
      <div id="logPanel">
        <div id="ptKinds" hidden>
          <label>This point is</label>
          <div class="kinds">
            <button class="k auto" data-kind="">Auto</button>
            <button class="k" data-kind="claim">Claim</button>
            <button class="k" data-kind="note">My note</button>
            <button class="k" data-kind="quote">Quotation</button>
          </div>
          <div class="k-hint" id="ptKindHint"></div>
        </div>
        <div class="dhead"><label for="ptText">Point</label><span class="dmeta" id="ptMeta"></span></div>
        <textarea id="ptText" class="input ta" dir="auto" rows="4" placeholder="Type, paste, or just talk — dictation lands here…" spellcheck="false"></textarea>
        <div class="srcbar">
          <input id="ptLink" class="input grow" placeholder="Paste a source link…">
          <button id="ptLinkAdd" class="chip">+ Link</button>
          <button id="ptLinkPaste" class="paste-btn" type="button" aria-label="Paste link from clipboard"><svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="3" width="10" height="3" rx="1"/><path d="M6 4H4.5A1.5 1.5 0 0 0 3 5.5v11A1.5 1.5 0 0 0 4.5 18h11a1.5 1.5 0 0 0 1.5-1.5v-11A1.5 1.5 0 0 0 15.5 4H14"/></svg></button>
        </div>
        <div class="srcbar">
          <input id="ptStr" class="input grow" dir="auto" placeholder="Or a string citation…">
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
          <button id="ptClear" class="btn ghost" title="Empty the draft - text and sources">Clear</button>
          <button id="ptHide" class="btn ghost">Hide</button>
        </div>
        <div class="keys" id="keyHints">
          <span class="kkey" data-k="toggle"><b>Ctrl+Alt+P</b> toggle</span>
          <span class="kkey" data-k="attach"><b>Ctrl+Alt+V</b> attach</span>
          <span class="kkey" data-k="log"><b>Ctrl+Alt+S</b> · Alt+Enter · say “log”</span>
          <span class="kkey" data-k="session"><b>Ctrl+Alt+N</b> · say “session …”</span>
          <span class="kkey" data-k="tab"><b>Ctrl+Alt+T</b> · say “tab …”</span>
          <span class="kkey" data-k="finish"><b>Ctrl+Alt+F</b> · say “finish”</span>
          <span class="kkey" data-k="hide"><b>Esc</b> hide</span>
        </div>
        <div class="recent" id="recent"></div>
      </div>
    </div>
  </section>
</div>
<div id="toasts"></div>
<script>
let state={topics:[]};
const KIND_HINT={
  "":"Dictated points are filed as notes, typed ones as claims - and a dictated one is re-checked when the second opinion is on.",
  claim:"Taken from a source. It carries the citation.",
  note:"Your own thinking. It is kept separate and never given a citation - not even by the AI pass.",
  quote:"Verbatim from the source. Nothing, including the AI pass, may reword it."
};
const sciOn=()=>!!((state.config||{}).science||{}).enabled;
const api=new Proxy({},{get:(_,p)=>{const pv=window.pywebview&&window.pywebview.api;return pv?pv[p]:(()=>Promise.resolve({error:"bridge not ready"}));}});

const $=(s,r=document)=>r.querySelector(s);
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const toast=(m,t="ok")=>{const d=document.createElement("div");d.className="toast "+t;d.textContent=m;
  document.getElementById("toasts").appendChild(d);setTimeout(()=>d.classList.add("out"),2200);setTimeout(()=>d.remove(),2600);};
// --- Trailmark dialogs (styled prompt/confirm) --------------------------------
// Native prompt()/confirm() render as unthemed browser chrome ("This page
// says…"), so every naming / destructive question goes through these instead.
// Same raised-card markup as the main window; text reaches the DOM through
// textContent only, never innerHTML.
let _tmSettle=null;
function tmCloseDialog(result){
  const back=document.querySelector(".tm-back");
  if(back)back.remove();
  if(_tmSettle){const f=_tmSettle;_tmSettle=null;try{f(result);}catch(e){}}
}
function tmConfirm(message,opts){
  opts=opts||{};
  return new Promise(resolve=>{
    tmCloseDialog(undefined);
    _tmSettle=resolve;
    const prevFocus=document.activeElement;
    const back=document.createElement("div");back.className="tm-back";
    const box=document.createElement("div");box.className="tm-modal";
    box.setAttribute("role","alertdialog");box.setAttribute("aria-modal","true");
    const h=document.createElement("h3");h.textContent=opts.title||"Are you sure?";
    const p=document.createElement("p");p.textContent=message;
    const row=document.createElement("div");row.className="tm-actions";
    const cancel=document.createElement("button");cancel.className="btn ghost";
    cancel.type="button";cancel.textContent=opts.cancelText||"Cancel";
    const ok=document.createElement("button");
    ok.className="btn "+(opts.danger?"danger":"primary");
    ok.type="button";ok.textContent=opts.okText||"Confirm";
    row.appendChild(cancel);row.appendChild(ok);
    box.appendChild(h);box.appendChild(p);box.appendChild(row);
    back.appendChild(box);document.body.appendChild(back);
    const done=v=>{if(prevFocus&&prevFocus.focus)try{prevFocus.focus();}catch(e){}tmCloseDialog(v);};
    cancel.addEventListener("click",()=>done(false));
    ok.addEventListener("click",()=>done(true));
    back.addEventListener("mousedown",e=>{if(e.target===back)done(false);});
    back.addEventListener("keydown",e=>{
      if(e.key==="Escape"){e.preventDefault();done(false);}
      if(e.key==="Enter"&&document.activeElement!==ok){e.preventDefault();done(true);}
    });
    setTimeout(()=>{try{ok.focus();}catch(e){}},30);
  });
}
function tmPrompt(title,opts){
  opts=opts||{};
  return new Promise(resolve=>{
    tmCloseDialog(undefined);
    _tmSettle=resolve;
    const prevFocus=document.activeElement;
    const back=document.createElement("div");back.className="tm-back";
    const box=document.createElement("div");box.className="tm-modal";
    box.setAttribute("role","dialog");box.setAttribute("aria-modal","true");
    const h=document.createElement("h3");h.textContent=title;
    box.appendChild(h);
    if(opts.hint){
      const p=document.createElement("p");p.textContent=opts.hint;
      box.appendChild(p);
    }
    const inp=document.createElement("input");
    inp.className="input";inp.dir="auto";inp.spellcheck=false;
    inp.placeholder=opts.placeholder||"";inp.value=opts.value||"";
    inp.setAttribute("aria-label",title);
    box.appendChild(inp);
    const row=document.createElement("div");row.className="tm-actions";
    const cancel=document.createElement("button");cancel.className="btn ghost";
    cancel.type="button";cancel.textContent=opts.cancelText||"Cancel";
    const ok=document.createElement("button");ok.className="btn primary";
    ok.type="button";ok.textContent=opts.okText||"Add";
    row.appendChild(cancel);row.appendChild(ok);
    box.appendChild(row);
    back.appendChild(box);document.body.appendChild(back);
    const done=v=>{if(prevFocus&&prevFocus.focus)try{prevFocus.focus();}catch(e){}tmCloseDialog(v);};
    cancel.addEventListener("click",()=>done(null));
    const commit=()=>done(inp.value);
    ok.addEventListener("click",commit);
    back.addEventListener("mousedown",e=>{if(e.target===back)done(null);});
    inp.addEventListener("keydown",e=>{
      if(e.key==="Enter"){e.preventDefault();commit();}
      else if(e.key==="Escape"){e.preventDefault();done(null);}
      else if(e.key==="Tab"){/* let focus move to the buttons */}
      e.stopPropagation();
    });
    back.addEventListener("keydown",e=>{if(e.key==="Escape"){e.preventDefault();done(null);}});
    setTimeout(()=>{try{inp.focus();inp.select();}catch(e){}},30);
  });
}
const byId=i=>state.topics.find(t=>t.id===i);
const openTopics=()=>state.topics.filter(t=>t.status==="open");
const fmtTime=iso=>{if(!iso)return"";const d=new Date(iso);return d.toLocaleString(undefined,{day:"2-digit",month:"short",hour:"2-digit",minute:"2-digit"});};
// Gamification: flash the shortcut hint that matches the action just used.
// Each .kkey carries data-k="toggle|attach|log|session|tab|finish|hide".
function flashKey(name){
  const el=document.querySelector('#keyHints [data-k="'+name+'"]');
  if(!el)return;
  el.classList.add("flash");
  setTimeout(()=>el.classList.remove("flash"),900);
}

// Everything Python knows about the voice bar AND the draft, as last pushed.
let voice={draft:{rev:0,text:"",origin:"",words:0,sources:[],count_sources:0,
                  meta:{topic_id:"",subtopic:"",kind:""},empty:true},
           state:"off",detail:"",heard:"",topic:"",topic_id:"",subtopic:"",
           always_on:true,enabled:false,configured:false,listening:false,mini:false,
           held:0,speaker_on:false};

// Ctrl+Alt+V and "save" attach the clipboard in Python; this is the toast
// that says so. Its own .cbtoast element rather than toast(): it carries an
// icon for the detected kind and the (untrusted) excerpt as textContent.
const CB_ICONS={
  link:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M8 12a3 3 0 0 0 4.24 0l2-2a3 3 0 0 0-4.24-4.24l-1 1"/><path d="M12 8a3 3 0 0 0-4.24 0l-2 2a3 3 0 0 0 4.24 4.24l1-1"/></svg>',
  image:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="14" height="12" rx="2"/><circle cx="7.5" cy="9" r="1.2"/><path d="M17 13l-4-4-7 7"/></svg>',
  text:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5h12M4 9h12M4 13h8"/></svg>'
};
function cbToast(kind,headline,detailText){
  const d=document.createElement("div");
  d.className="cbtoast fade";
  d.innerHTML=`<div class="row1"><div class="ic">${CB_ICONS[kind]||CB_ICONS.text}</div>
    <div class="txt"><b></b><span></span></div></div>
    <div class="prog"><i></i></div>`;
  d.querySelector(".txt b").textContent=headline;
  d.querySelector(".txt span").textContent=detailText;
  document.getElementById("toasts").appendChild(d);
  const bar=d.querySelector(".prog i");
  requestAnimationFrame(()=>{bar.style.width="0%";});
  setTimeout(()=>{d.classList.add("out");setTimeout(()=>d.remove(),280);},4000);
}

// ---- the draft box ---------------------------------------------------------
// The box sends its whole text back, with the revision it was typed against,
// ~350 ms after the last keystroke. Python merges: a sentence dictated while
// you typed is added after your text rather than overwritten by it. While a
// keystroke is unsent, incoming dictation is NOT painted into the box - it
// comes back with the reply to the send, added to the end of what you typed.
const box=()=>$("#ptText");
let baseRev=0, dirty=false, sending=null, sendTimer=null;

function setBox(text){
  const el=box(); if(el.value===text)return;
  const old=el.value,a=el.selectionStart,b=el.selectionEnd;
  const atEnd=a===b&&a===old.length;
  el.value=text;
  if(document.activeElement===el){
    if(text.startsWith(old)&&!atEnd){el.selectionStart=a;el.selectionEnd=b;}
    else{el.selectionStart=el.selectionEnd=text.length;}
  }
}
function draftIn(d,force){
  if(!d||typeof d!=="object")return;
  // Pushes come from several Python threads and can arrive out of order;
  // a revision never goes backwards.
  if(!force&&typeof d.rev==="number"&&d.rev<(voice.draft.rev||0))return;
  voice.draft=d;
  if(force||(!dirty&&!sending)){setBox(d.text||"");baseRev=d.rev||0;dirty=false;}
  renderAtt();renderDraftMeta();
}
function scheduleSend(){clearTimeout(sendTimer);sendTimer=setTimeout(sendDraft,350);}
function sendDraft(){
  clearTimeout(sendTimer);sendTimer=null;
  if(sending)return sending.then(()=>dirty?sendDraft():null);
  if(!dirty)return Promise.resolve();
  const text=box().value,base=baseRev;
  dirty=false;
  sending=Promise.resolve(api.draft_set(text,base)).then(r=>{
    sending=null;
    if(!r||r.error||!r.draft){dirty=true;return;}
    const d=r.draft,res=r.result||{},now=box().value;
    // The draft is reconciled here, by hand; the rest of the payload is
    // ordinary voice-bar state.
    const rest=Object.assign({},r);delete rest.draft;applyVoice(rest,false);
    if(res.ok){
      voice.draft=d;baseRev=d.rev;
      if(now===text){setBox(d.text);}
      else if(d.text.startsWith(text)){setBox(now+d.text.slice(text.length));}
      else if(now.startsWith(text)){setBox(d.text+now.slice(text.length));}
      dirty=box().value!==d.text;
      if(dirty)scheduleSend();
    }else if(res.reason==="logged"){
      draftIn(d,true);
      toast("That draft was just logged - the box now shows what came after it.","err");
    }else if(res.reason==="too long"){
      dirty=true;toast("The draft is too long to keep.","err");
    }else{
      // Changed underneath by something other than dictation (a failed log
      // put its text back). What is in the box is what you are looking at,
      // so it wins - re-sent against the new revision.
      voice.draft=d;baseRev=d.rev;
      if(d.text.startsWith(text)&&now===text){setBox(d.text);dirty=false;}
      else{dirty=true;scheduleSend();}
    }
    renderAtt();renderDraftMeta();
  }).catch(()=>{sending=null;dirty=true;});
  return sending;
}
box().addEventListener("input",()=>{dirty=true;scheduleSend();renderDraftMeta();});

function renderDraftMeta(){
  const d=voice.draft||{},el=$("#ptMeta");
  const text=box().value,words=text.trim()?text.trim().split(/\\s+/).length:0;
  const bits=[];
  if(words)bits.push(words+(words>1?" words":" word"));
  if(d.origin==="voice")bits.push("<b>dictated</b>");
  else if(d.origin==="hand"&&words)bits.push("edited");
  if(dirty||sending)bits.push("saving…");
  el.innerHTML=bits.join(" · ");
  const md=$("#vDraft");
  if(md){
    const t=(text||"").trim();
    md.textContent=t?(t.length>60?"…"+t.slice(-60):t):(voice.listening?"Talk - say “log” to file it.":"");
  }
}

async function logPoint(){
  flashKey("log");
  await sendDraft();
  if(!box().value.trim()){
    toast((voice.draft.sources||[]).length?"Sources are attached - write or say the point too.":"Write the point first.","err");
    box().focus();return;
  }
  let r;
  try{r=await api.draft_log(null,null);}catch(e){r={error:"Bridge not ready."};}
  if(r&&r.draft)draftIn(r.draft,true);
  if(r)applyVoice(r,false);
  if(!r||r.error){toast((r&&r.error)||"Could not log.","err");return;}
  const res=r.result||{};
  api.get_state().then(s=>{
    if(!s||s.error)return;
    state=s;renderMode();
    const t=byId(res.topic_id);
    if(t&&t.entries.length){
      const e=t.entries.find(x=>x.id===res.entry_id)||t.entries.at(-1);
      $("#recent").innerHTML="<b>Logged</b> · "+fmtTime(e.created)+
        (e.subtopic?" · "+esc(e.subtopic):"")+" · "+esc(t.title)+" · "+t.entries.length+" point(s)";
    }
  });
  toast("Point logged — "+(res.sources||0)+" source(s) attached.");
  box().focus();
}

// ---- where it goes -----------------------------------------------------------
function targetTopicId(){
  const want=voice.topic_id||((voice.draft||{}).meta||{}).topic_id;
  if(want&&byId(want)&&byId(want).status==="open")return want;
  const o=openTopics();return o.length?o[o.length-1].id:null;
}
let creating=false;
function renderMode(){
  const opens=openTopics();
  const no=$("#noTopic");
  if(no)no.hidden=!(creating||!opens.length);
  const tsw=$("#topicSelWrap");
  if(tsw)tsw.hidden=!opens.length;
  const ntC=$("#ntCancel");
  if(ntC)ntC.hidden=!opens.length;
  const ntW=$("#ntWhy");
  if(ntW)ntW.textContent=opens.length?"A new topic - what you log next goes there."
    :"No open topic yet. Name one - or say “session” and a name.";
  const tpR=$("#tpRow"),sbR=$("#subRow");
  if(tpR)tpR.hidden=!opens.length;
  if(sbR)sbR.hidden=!opens.length;
  const pg=$("#ptGo");
  if(pg)pg.disabled=!opens.length;
  const kw=$("#ptKinds");
  const kind=((voice.draft||{}).meta||{}).kind||"";
  if(kw){
    kw.hidden=!sciOn();
    kw.querySelectorAll(".k").forEach(b=>b.classList.toggle("on",b.dataset.kind===kind));
    $("#ptKindHint").textContent=KIND_HINT[kind]||"";
  }
  if(!opens.length)return;
  const tid=targetTopicId();
  const sel=$("#tpSel");
  sel.innerHTML=opens.map(t=>`<option value="${esc(t.id)}">${esc(t.title)}</option>`).join("");
  sel.value=tid;
  renderSubs();
}
function renderSubs(){
  const t=byId(targetTopicId());if(!t)return;
  const cur=((voice.draft||{}).meta||{}).subtopic||"";
  const wrap=$("#subChips");
  const subs=[...(t.subtopics||[])];
  if(cur&&!subs.includes(cur))subs.push(cur);
  const chips=subs.map(s=>`<button class="chip ${cur===s?"active":""}" data-s="${esc(s)}">${esc(s)}</button>`).join("");
  wrap.innerHTML=`<button class="chip ${cur===""?"active":""}" data-s="">General</button>${chips}
    <button class="chip accent" id="subAdd">+ add</button>`;
  wrap.querySelectorAll("button[data-s]").forEach(b=>b.addEventListener("click",()=>{flashKey("tab");setMeta({topic_id:t.id,subtopic:b.dataset.s});}));
  $("#subAdd").addEventListener("click",async()=>{
    flashKey("tab");
    const name=await tmPrompt("New sub-topic",{hint:"Adds to "+t.title+".",placeholder:"Sub-topic name…",okText:"Add sub-topic"});
    if(!name||!name.trim())return;
    api.add_subtopic(t.id,name.trim()).then(r=>{
      if(r.error)return toast(r.error,"err");
      state=r;setMeta({topic_id:t.id,subtopic:name.trim()});
    });
  });
}
async function setMeta(fields){
  let r;try{r=await api.draft_meta(fields);}catch(e){r=null;}
  if(r&&!r.error){applyVoice(r,false);}
  renderMode();
}

function renderAtt(){
  const wrap=$("#attChips");const parts=[];
  // Chips carry the draft's own source id: a "save" can land between this
  // render and the click, and the chip clicked must be the one removed.
  (voice.draft.sources||[]).forEach(s=>{
    if(s.type==="image"){parts.push(`<span class="thumb-chip">
    <span class="thumb"><svg viewBox="0 0 24 24" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="8.5" cy="10" r="1.5"/><path d="M21 16l-5-5-9 9"/></svg></span>
    <span class="thumb-meta"><span class="fn">Image</span></span>
    <button class="xbtn" data-rm="${s.id}" type="button" aria-label="Remove image"><svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M5 5l10 10M15 5L5 15"/></svg></button>
  </span>`);return;}
    const mark=s.type==="link"?"🔗":"“";
    parts.push(`<span class="chip active" data-rm="${s.id}" title="${esc(s.value)}">${mark} ${esc((s.value||"").slice(0,s.type==="link"?22:18))} ×</span>`);
  });
  wrap.innerHTML=parts.join("")||`<span class="muted" style="font-size:11.5px">links, strings or screenshots — all will be cited</span>`;
  wrap.querySelectorAll("[data-rm]").forEach(el=>el.addEventListener("click",async()=>{
    let r;try{r=await api.draft_drop_source(parseInt(el.dataset.rm,10));}catch(e){r=null;}
    if(r&&r.draft)applyVoice(r,false);
  }));
}
async function addSource(type,value,msg){
  let r;try{r=await api.draft_add_source(type,value,"");}catch(e){r={error:"Bridge not ready."};}
  if(r&&r.draft)applyVoice(r,false);
  if(!r||r.error){toast((r&&r.error)||"Could not attach it.","err");return false;}
  if(msg)toast(msg);
  return true;
}

$("#ntGo").addEventListener("click",async()=>{
  flashKey("session");
  const title=$("#ntTitle").value;
  const before=new Set(state.topics.map(t=>t.id));
  const r=await api.start_topic(title);
  if(r.error)return toast(r.error,"err");
  state=r;creating=false;$("#ntTitle").value="";
  const made=r.topics.find(t=>!before.has(t.id));
  if(made)await setMeta({topic_id:made.id,subtopic:""});
  renderMode();box().focus();
});
$("#ntCancel").addEventListener("click",()=>{creating=false;renderMode();});
$("#ntTitle").addEventListener("keydown",e=>{if(e.key==="Enter")$("#ntGo").click();});
$("#tpSel").addEventListener("change",e=>setMeta({topic_id:e.target.value,subtopic:""}));
$("#tpNew").addEventListener("click",()=>{flashKey("session");creating=true;renderMode();$("#ntTitle").focus();});
$("#ptLinkAdd").addEventListener("click",async()=>{
  const v=$("#ptLink").value.trim();if(!v)return;
  try{new URL(v);}catch(e){toast("That doesn't look like a URL.","err");return;}
  if(await addSource("link",v,"Link added.")){flashKey("attach");$("#ptLink").value="";}
});
$("#ptStrAdd").addEventListener("click",async()=>{
  const v=$("#ptStr").value.trim();if(!v)return;
  if(await addSource("string",v,"Citation added.")){flashKey("attach");$("#ptStr").value="";}
});
$("#ptLink").addEventListener("keydown",e=>{if(e.key==="Enter")$("#ptLinkAdd").click();});
$("#ptStr").addEventListener("keydown",e=>{if(e.key==="Enter")$("#ptStrAdd").click();});
$("#ptImgPaste").addEventListener("click",async()=>{
  const d=await api.read_clipboard();
  if(d.type==="image"){addSource("image",d.value,"Image pasted from the clipboard.");flashKey("attach");}
  else toast("Clipboard has no image.","err");
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
  files.forEach(f=>{
    if(f.size>8*1024*1024){toast("Image too large (8 MB max).","err");return;}
    const rd=new FileReader();
    rd.onload=()=>addSource("image",rd.result,"Screenshot attached.");
    rd.readAsDataURL(f);
  });
  e.target.value="";
});
$("#ptKinds").addEventListener("click",e=>{
  const b=e.target.closest("[data-kind]"); if(!b) return;
  setMeta({kind:b.dataset.kind});
});
$("#ptGo").addEventListener("click",logPoint);
$("#ptClear").addEventListener("click",async()=>{
  const d=voice.draft||{};
  if(!box().value.trim()&&!(d.sources||[]).length)return;
  if(!await tmConfirm("The text and its sources are not logged anywhere.",{title:"Empty the draft?",okText:"Empty",danger:true}))return;
  clearTimeout(sendTimer);dirty=false;
  let r;try{r=await api.draft_clear();}catch(e){r=null;}
  if(r&&r.draft){draftIn(r.draft,true);applyVoice(r,false);}
});
box().addEventListener("keydown",e=>{
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
$("#ptHide").addEventListener("click",()=>{flashKey("hide");sendDraft();api.hide_popup();});
document.addEventListener("keydown",e=>{if(e.key==="Escape"){flashKey("hide");sendDraft();api.hide_popup();}});
document.addEventListener("wheel",e=>{if(e.ctrlKey)e.preventDefault();},{passive:false});


// ---- the voice bar -----------------------------------------------------------
const V_LABEL={off:"Voice off",listening:"Listening",speech:"Speaking",
  transcribing:"Transcribing",deciding:"Deciding",heard:"Heard",logged:"Logged",
  source:"Source added",duplicate:"Already added",session:"New session",tab:"Tab",
  finished:"Finished",edited:"Listening",typed:"Listening",merged:"Listening",
  cleared:"Cleared",ok:"Done",no_topic:"No open topic",held:"Held aside"};

// Python calls this on every change. A push is also where a clipboard
// attachment gets its toast - once, as it happens, not again on a refresh.
function voiceState(payload){
  applyVoice(payload,true);
}
window.voiceState=voiceState;
let lastToastRev=-1;
function applyVoice(payload,pushed){
  if(!payload||typeof payload!=="object")return;
  const d=payload.draft;
  const rest=Object.assign({},payload);delete rest.draft;delete rest.result;delete rest.error;
  Object.assign(voice,rest);
  if(d)draftIn(d,false);
  if(pushed&&(voice.state==="source"||voice.state==="duplicate")&&d&&d.rev!==lastToastRev){
    lastToastRev=d.rev;
    flashKey("attach");
    const src=(d.sources||[]).at(-1)||{};
    if(voice.state==="duplicate")cbToast("text","Already attached",voice.detail||"");
    else cbToast(src.type==="image"?"image":src.type==="link"?"link":"text",
                 "Attached to the draft",voice.detail||"");
  }
  if(pushed){
    if(voice.state==="logged")flashKey("log");
    else if(voice.state==="session")flashKey("session");
    else if(voice.state==="tab")flashKey("tab");
    else if(voice.state==="finished")flashKey("finish");
  }
  renderVoice();
  if(pushed&&["session","tab","finished","logged"].includes(voice.state)){
    api.get_state().then(s=>{if(s&&!s.error){state=s;renderMode();}}).catch(()=>{});
  }
}

function popupMini(mini){
  voice.mini=!!mini;
  document.body.classList.toggle("mini",!!mini);
  // Focusing the point box before the bar collapsed can leave the page
  // scrolled; the bar has nothing to scroll to.
  if(mini&&document.scrollingElement)document.scrollingElement.scrollTop=0;
  const b=$("#miniBtn");
  if(b){b.setAttribute("aria-checked",mini?"true":"false");
        b.title=mini?"Back to the full window":"Collapse to the voice bar";}
  renderVoice();
}
window.popupMini=popupMini;

function refreshVoice(){
  api.draft_get().then(p=>{if(p&&!p.error)applyVoice(p,false);}).catch(()=>{});
}

function renderVoice(){
  const sec=$("#voiceSec");
  if(!sec)return;
  const live=!!voice.listening;
  const vb=$("#voiceBtn");
  if(vb){vb.setAttribute("aria-checked",voice.enabled?"true":"false");
         vb.title=voice.enabled?"Always-on voice is on — click to stop listening"
                               :"Always-on voice is off — click to start listening";}
  // Unified card: the voice block is always visible (Voice off included).
  // Only the collapsed mini bar keeps the old gate, so it is never blank.
  if(sec)sec.hidden=false;
  document.body.classList.toggle("mini",!!voice.mini);
  renderDraftMeta();

  const st=$("#vState");
  const err=voice.state==="error";
  st.className="vstate"+(live&&!err?" on":"")+(err?" err":"");
  let label=live?(V_LABEL[voice.state]||"Listening"):"Voice off";
  if(err)label=voice.detail||"Voice error";
  st.querySelector(".tx").textContent=label;
  st.title=label;

  const pills=[];
  const n=(voice.draft||{}).count_sources||0;
  if(n)pills.push('<span class="vpill">'+n+(n>1?" sources":" source")+'</span>');
  if(voice.held)pills.push('<button class="vpill hot" id="vHeld" type="button" title="Clips the voice check held aside - review them in Settings › Voice">'+voice.held+' held</button>');
  if(voice.speaker_on)pills.push('<span class="vpill" title="Only your enrolled voice is transcribed">your voice</span>');
  $("#vCounts").innerHTML=pills.join("");
  const hb=$("#vHeld");if(hb)hb.addEventListener("click",()=>api.show_full());

  $("#vTopic").textContent=(voice.topic||"no open topic")+(voice.subtopic?" › "+voice.subtopic:"");

  // Untrusted text (a transcript, a clipboard excerpt) only ever reaches the
  // DOM through textContent or esc().
  const h=$("#vHeard");
  if(err)h.textContent="";
  else if(voice.detail&&!["listening","transcribing","speech","typed","merged","edited"].includes(voice.state))h.textContent=voice.detail;
  else if(voice.heard)h.textContent="Heard: “"+voice.heard+"”";
  else if(live)h.textContent="Talk - it lands in the box below. Say “log” to file it.";
  else if(voice.enabled)h.textContent="Starting the microphone…";
  else h.textContent="Voice is off. Click the microphone above to start.";
  ensureWave();
}

// ---- the wave ------------------------------------------------------------------
let waveTimer=null, waveBusy=false;
function ensureWave(){
  if(!voice.listening||document.hidden){stopWave();return;}
  if(waveTimer===null)waveTimer=setTimeout(waveTick,0);
}
function stopWave(){clearTimeout(waveTimer);waveTimer=null;drawWave(null);}
function waveTick(){
  waveTimer=null;
  if(!voice.listening||document.hidden){drawWave(null);return;}
  if(waveBusy){waveTimer=setTimeout(waveTick,90);return;}
  waveBusy=true;
  Promise.resolve(api.mic_levels(200)).then(drawWave).catch(()=>{}).finally(()=>{
    waveBusy=false;
    if(voice.listening&&!document.hidden)waveTimer=setTimeout(waveTick,90);
  });
}
document.addEventListener("visibilitychange",ensureWave);
function drawWave(d){
  const c=$("#vWave");if(!c)return;
  const dpr=window.devicePixelRatio||1,w=Math.max(1,c.clientWidth),h=Math.max(1,c.clientHeight);
  if(c.width!==Math.round(w*dpr)||c.height!==Math.round(h*dpr)){c.width=Math.round(w*dpr);c.height=Math.round(h*dpr);}
  const g=c.getContext("2d");g.setTransform(dpr,0,0,dpr,0,0);g.clearRect(0,0,w,h);
  const cs=getComputedStyle(document.documentElement);
  const hot=cs.getPropertyValue("--accent").trim()||"#d9822b";
  const cold=cs.getPropertyValue("--content-muted").trim()||"#888";
  const mid=h/2;
  g.globalAlpha=.35;g.fillStyle=cold;g.fillRect(0,mid-.5,w,1);g.globalAlpha=1;
  if(!d||!d.hi||!d.hi.length)return;
  const N=200,n=d.hi.length,step=w/N,thr=d.threshold||0;
  // Square-root scale: quiet speech is a few percent of full scale, and on a
  // linear axis it would be a flat line you cannot tell from silence.
  const s=v=>Math.sign(v)*Math.sqrt(Math.abs(v));
  for(let i=0;i<n;i++){
    const x=(N-n+i)*step;
    const top=mid-s(d.hi[i])*mid*.95, bot=mid-s(d.lo[i])*mid*.95;
    g.fillStyle=(d.rms[i]>=thr&&thr>0)?hot:cold;
    g.fillRect(x,Math.min(top,bot),Math.max(1,step*.7),Math.max(1,Math.abs(bot-top)));
  }
}

async function vcmd(name){
  if(name==="log"){return logPoint();}
  const map={save:"attach",tab:"tab",session:"session",finish:"finish"};
  if(map[name])flashKey(map[name]);
  await sendDraft();
  let r;
  try{r=await api.voice_command(name,"");}catch(e){r={error:"Bridge not ready."};}
  if(r&&r.error)toast(r.error,"err");
  refreshVoice();
  api.get_state().then(s=>{if(s&&!s.error){state=s;renderMode();}}).catch(()=>{});
}
const _vLog=$("#vLog");
if(_vLog)_vLog.addEventListener("click",()=>vcmd("log"));
$("#voiceBtn").addEventListener("click",async()=>{
  let r;
  try{r=await api.toggle_voice();}catch(e){r={error:"Bridge not ready."};}
  if(r&&r.error){toast(r.error,"err");return;}
  voice.enabled=!!(r&&r.enabled);
  renderVoice();
  if(r&&r.warn)toast(r.warn,"err");
  else if(!voice.enabled)toast("Always-on voice off.");
  refreshVoice();
});
$("#miniBtn").addEventListener("click",()=>{
  const next=!document.body.classList.contains("mini");
  popupMini(next);              // paint first: the ctypes resize is a bridge
  api.set_popup_mini(next);     // round-trip and the bar should not lag it
});

function renderKeyHints(cfg){
  cfg=cfg||{};
  const combo=h=>(h.modifiers||["ctrl","alt"]).map(m=>m[0].toUpperCase()+m.slice(1)).join("+")+"+"+(h.key||"P");
  const cb=cfg.clipboard||{};
  const vc=cfg.voice||{},keys=vc.keys||{},mods=vc.modifiers||["ctrl","alt"];
  const vcombo=k=>mods.map(m=>m[0].toUpperCase()+m.slice(1)).join("+")+"+"+((keys[k]||k[0]||"").toUpperCase());
  const set=(k,html)=>{
    const el=document.querySelector('#keyHints [data-k="'+k+'"]');
    if(el)el.innerHTML=html;
  };
  set("toggle","<b>"+esc(combo(cfg.hotkey||{}))+"</b> toggle");
  if(cb.enabled)set("attach","<b>"+esc(combo({modifiers:cb.modifiers,key:cb.key||"V"}))+"</b> attach");
  if(keys.log||keys.finish||keys.session||keys.tab){
    if(keys.log)set("log","<b>"+esc(vcombo("log"))+"</b> · Alt+Enter · say “log”");
    if(keys.session)set("session","<b>"+esc(vcombo("session"))+"</b> · say “session …”");
    if(keys.tab)set("tab","<b>"+esc(vcombo("tab"))+"</b> · say “tab …”");
    if(keys.finish)set("finish","<b>"+esc(vcombo("finish"))+"</b> · say “finish”");
  }
}
function boot(){
  refreshVoice();
  api.get_state().then(r=>{
    state=r;
    const cfg=r.config||{};
    applyTheme((cfg.appearance||{}).theme||"system");
    const combo=h=>(h.modifiers||["ctrl","alt"]).map(m=>m[0].toUpperCase()+m.slice(1)).join("+")+"+"+(h.key||"P");
    const cb=cfg.clipboard||{};
    $("#hkLabel").textContent=combo(cfg.hotkey||{})+" toggles"+(cb.enabled?" · "+combo({modifiers:cb.modifiers,key:cb.key||"V"})+" attaches the clipboard":"");
    renderKeyHints(cfg);
    $("#liveDot").hidden=r.topics.filter(t=>t.status==="open").length===0;
    renderMode();renderAtt();
    setTimeout(()=>{const el=box();if(el)el.focus();},150);
  });
}
function applyTheme(pref){
  const el=document.documentElement;
  if(pref==="light"||pref==="dark") el.setAttribute("data-theme",pref);
  else el.removeAttribute("data-theme");   // fall back to prefers-color-scheme
}
function popupShown(){
  // A hidden window missed every push while it was away, so it pulls once.
  refreshVoice();
  api.get_state().then(r=>{if(r&&!r.error){state=r;
    applyTheme(((r.config||{}).appearance||{}).theme||"system");renderKeyHints(r.config||{});renderMode();}}).catch(()=>{});
  setTimeout(()=>{const el=box();if(el)el.focus();},120);
}
if(window.pywebview){boot();}else{window.addEventListener("pywebviewready",boot);}

// --- Persian half-space -----------------------------------------------------
// Ctrl+Shift+Space inserts ZWNJ (U+200C). Windows has no key for it, and
// Persian needs it constantly: "\u0645\u06cc \u0634\u0648\u062f" and
// "\u0645\u06cc\u200c\u0634\u0648\u062f" are different words and look
// identical in most editors. Without a key, people type the wrong one - which
// is the single most common defect in Persian text entered on a machine that
// did not expect it.
function zwnjKey(e){
  if(!(e.ctrlKey&&e.shiftKey&&(e.code==="Space"||e.key===" ")))return;
  const el=e.target;
  if(!el||!("selectionStart" in el)||el.selectionStart===null)return;
  e.preventDefault();
  const a=el.selectionStart,b=el.selectionEnd,v=el.value;
  el.value=v.slice(0,a)+"\u200c"+v.slice(b);
  el.selectionStart=el.selectionEnd=a+1;
  el.dispatchEvent(new Event("input",{bubbles:true}));
}
document.addEventListener("keydown",zwnjKey,true);
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
.tb-chip.tg-waiting{color:var(--accent)}
.tb-chip.tg-paired{color:var(--success)}
.tb-chip.tg-error{color:var(--danger)}
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
/* Settings › voice. The command table, the microphone wave, the sentence
   to read for the voiceprint. */
.tbl{width:100%;border-collapse:collapse;font-size:12.5px}
.tbl td{padding:7px 8px;border-bottom:1px solid var(--border);vertical-align:top}
.tbl tr:last-child td{border-bottom:0}
.mwave{display:block;width:100%;height:48px;margin-top:8px;border-radius:var(--r-sm);background:var(--surface-sunken)}
.spk-sent{margin-top:8px;padding:12px 14px;border-radius:var(--r-lg);background:var(--surface-sunken);
  font-size:15px;line-height:1.55;font-weight:550}
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
.modal.wide{width:min(1120px,100%)}
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

.tpls{display:grid;grid-template-columns:repeat(auto-fill,minmax(196px,1fr));gap:12px;
  max-height:340px;overflow-y:auto;
  /* the grid keeps its own scroll so the Formats section and the Export
     button stay visible below it, however many templates are installed */
  padding:2px;margin:0}
.tpl{display:flex;flex-direction:column;gap:0;padding:0;border-radius:var(--r-lg);
  border:1px solid var(--border);background:var(--surface-raised);color:var(--content);
  font-family:inherit;text-align:left;cursor:pointer;transition:.16s;overflow:hidden}
.tpl:hover{border-color:var(--border-strong);transform:translateY(-2px);box-shadow:var(--shadow-2)}
.tpl.on{border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-tint)}
/* the gallery cover: a miniature page in the template's own accent, the way
   Overleaf and Google Docs show a document rather than a list row */
.tpl-cover{position:relative;height:104px;flex:none;overflow:hidden;
  background:var(--surface-sunken);
  background:linear-gradient(160deg,color-mix(in srgb,var(--tpl-accent,var(--accent)) 26%,transparent),transparent 70%),
             var(--surface-sunken);
  border-bottom:1px solid var(--border)}
.tpl-cover::before{content:"";position:absolute;left:14px;right:14px;top:12px;bottom:12px;
  background:var(--surface-raised);border:1px solid var(--border);border-radius:4px;
  box-shadow:var(--shadow-1)}
.tpl-cover::after{content:"";position:absolute;left:22px;right:30px;top:22px;height:52px;
  background:repeating-linear-gradient(to bottom,
    var(--content-muted) 0 2px,transparent 2px 7px);
  opacity:.55;border-radius:2px}
.tpl-cover .tpl-titlebar{position:absolute;left:22px;right:60px;top:14px;height:5px;border-radius:3px;
  background:var(--tpl-accent,var(--accent))}
.tpl-b{flex:1;min-width:0;display:flex;flex-direction:column;gap:4px;padding:10px 12px 11px}
.tpl-dot{display:none}
.tpl-n{font-size:13px;font-weight:650;display:flex;align-items:center;gap:7px;flex-wrap:wrap}
.tpl-d{font-size:11.5px;color:var(--content-muted);line-height:1.45;
  display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;min-height:32px}
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

/* --- settings sub-tabs: one row of pills above the cards -----------------
   Settings used to be a single 12-card scroll: every save rebuilt the whole
   page, wiping focus and scroll. Now only the active panel renders, so a
   save in AI touches AI, not the hotkey form. */
.set-tabs{display:flex;gap:6px;flex-wrap:wrap;margin:0 auto 14px;max-width:780px}
.set-tab{padding:7px 14px;border:1px solid var(--border);border-radius:var(--r-pill);
  background:var(--surface-sunken);color:var(--content-secondary);font-family:inherit;
  font-size:12px;font-weight:650;cursor:pointer;transition:.15s;white-space:nowrap}
.set-tab:hover{color:var(--content);border-color:var(--border-strong)}
.set-tab.on{background:var(--accent-tint);border-color:var(--accent);color:var(--accent)}
/* --- vertical rhythm: stacked rows inside settings cards and the export
   dialog. .card itself is plain block flow, so sibling rows used to touch;
   these two containers are flex columns and every field/button row gets the
   same gap - field-button, button-button and field-field alike. */
.set-panels>.card{display:flex;flex-direction:column;gap:12px}
.set-panels>.card>p,.set-panels>.card>.row{margin:0}
.modal-b{display:flex;flex-direction:column;gap:12px}
.modal-b>.sec-l{margin:0}
.modal-b>.sec-l:not(:first-child){margin-top:8px}
/* --- template panel: pills+grid alongside an optional preview column ----- */
.tpl-panel{display:flex;gap:16px;align-items:flex-start;min-width:0}
.tpl-panel.has-preview{flex-direction:column}
.tpl-main{flex:1;min-width:0;width:100%}
/* sub-headings inside the template column ("Templates in X" / "Also
   available") - deliberately lighter than .sec-l so they read as nested
   under the "Template" section heading, not as a sibling of it */
.tpl-sub-l{font-size:10.5px;font-weight:600;letter-spacing:.03em;text-transform:uppercase;
  color:var(--content-muted);margin:0 0 7px}
.tpl-sub-l.also{margin-top:14px}
.preview-col{flex:0 0 320px;min-width:0;display:flex;flex-direction:column;gap:8px;
  border-left:1px solid var(--border);padding-left:16px;
  position:sticky;top:0}
.tpl-panel.has-preview .preview-col{flex:none;width:100%;border-left:0;padding-left:0;
  border-top:1px solid var(--border);padding-top:14px;position:static}
.preview-h{font-size:11.5px;font-weight:650;color:var(--content-secondary);line-height:1.4}
.preview-frame-wrap{border:1px solid var(--border-strong);border-radius:var(--r-lg);overflow:hidden;
  background:#fff;height:430px;box-shadow:var(--shadow-2)}
.tpl-panel.has-preview .preview-frame-wrap{height:min(620px,calc(100vh - 320px));min-height:420px}
.preview-frame-wrap iframe{width:100%;height:100%;border:0;background:#fff}
.preview-toolbar{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
/* Settings › Templates manager: full-width gallery + large preview below.
   Same card markup as the export dialog, but the preview is the point here,
   so it gets the full card width and a real reading height. */
.tplmgr-preview-wrap{border:1px solid var(--border-strong);border-radius:var(--r-lg);
  overflow:hidden;background:#fff;height:min(640px,calc(100vh - 300px));min-height:440px;
  box-shadow:var(--shadow-2)}
.tplmgr-preview-wrap iframe{width:100%;height:100%;border:0;background:#fff}
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
    <span class="tb-chip" id="voiceChip"></span>
    <span class="tb-chip" id="tgChip"></span>
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
let catNewOpen=false; // Settings -> Templates -> Categories: "+ New category" popover open?
// Settings sub-tabs. One panel renders at a time so a save in one section
// never rebuilds the form being edited in another.
let settingsSub="shortcuts";
const SETTINGS_TABS=[
  ["shortcuts","Shortcuts"],
  ["ai","AI & voice"],
  ["integrations","Integrations"],
  ["science","Science"],
  ["templates","Templates"],
  ["appearance","Appearance"],
];
// Keys that live only in the browser: fetched once via dedicated bridge calls
// (list_categories, list_asr_devices, get_voice, telegram_status,
// speaker_status) and never part of store.state(). Any wholesale `state=r`
// assignment drops them and triggers a refetch cascade - one full rebuild per
// missing key. applyState() merges instead; use it everywhere a bridge call
// returns full state.
const EPHEMERAL_KEYS=["categories","asrDevices","voiceGrammar","voiceHotkeys",
  "voiceOpinion","telegramStatus","speakerInfo"];
function applyState(r){
  if(!r||r.error) return r;
  for(const k of EPHEMERAL_KEYS){
    if(!(k in r)&&state[k]!==undefined) r[k]=state[k];
  }
  state=r;
  return r;
}
// Templates manager preview (Settings › Templates). Sample HTML from
// api.template_demo(), shown full-width below the gallery.
let tplMgrPreview=null, tplMgrHtml=null, tplMgrLoading=false, tplMgrError=null;
// In-flight guards: bindSettings() runs after every render, and without these
// each render would fire a duplicate fetch, each fetch would render, and each
// render would fetch again - the "refreshes so much" storm.
const _fetching={cats:false,asrDevs:false,voice:false,tg:false,spk:false};
// Device poller generation + last select fingerprint. bindSettings() starts
// one chain per render; only the newest chain survives, so re-renders never
// stack up parallel pollers.
let _devPollGen=0, _devPollFp=[];
const api=new Proxy({},{get:(_,p)=>{const pv=window.pywebview&&window.pywebview.api;return pv?pv[p]:(()=>Promise.resolve({error:"bridge not ready"}));}});

const $=(s,r=document)=>r.querySelector(s);
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const toast=(m,t="ok")=>{const d=document.createElement("div");d.className="toast "+t;d.textContent=m;
  document.getElementById("toasts").appendChild(d);setTimeout(()=>d.classList.add("out"),2400);setTimeout(()=>d.remove(),2800);};
// --- Trailmark dialogs (styled prompt/confirm) --------------------------------
// Native prompt()/confirm() render as unthemed browser chrome ("This page
// says…"), so every naming / destructive question goes through these instead.
// Same raised-card markup as the quick-capture popup; text reaches the DOM
// through textContent only, never innerHTML.
let _tmSettle=null;
function tmCloseDialog(result){
  const back=document.querySelector(".tm-back");
  if(back)back.remove();
  if(_tmSettle){const f=_tmSettle;_tmSettle=null;try{f(result);}catch(e){}}
}
function tmConfirm(message,opts){
  opts=opts||{};
  return new Promise(resolve=>{
    tmCloseDialog(undefined);
    _tmSettle=resolve;
    const prevFocus=document.activeElement;
    const back=document.createElement("div");back.className="tm-back";
    const box=document.createElement("div");box.className="tm-modal";
    box.setAttribute("role","alertdialog");box.setAttribute("aria-modal","true");
    const h=document.createElement("h3");h.textContent=opts.title||"Are you sure?";
    const p=document.createElement("p");p.textContent=message;
    const row=document.createElement("div");row.className="tm-actions";
    const cancel=document.createElement("button");cancel.className="btn ghost";
    cancel.type="button";cancel.textContent=opts.cancelText||"Cancel";
    const ok=document.createElement("button");
    ok.className="btn "+(opts.danger?"danger":"primary");
    ok.type="button";ok.textContent=opts.okText||"Confirm";
    row.appendChild(cancel);row.appendChild(ok);
    box.appendChild(h);box.appendChild(p);box.appendChild(row);
    back.appendChild(box);document.body.appendChild(back);
    const done=v=>{if(prevFocus&&prevFocus.focus)try{prevFocus.focus();}catch(e){}tmCloseDialog(v);};
    cancel.addEventListener("click",()=>done(false));
    ok.addEventListener("click",()=>done(true));
    back.addEventListener("mousedown",e=>{if(e.target===back)done(false);});
    back.addEventListener("keydown",e=>{
      if(e.key==="Escape"){e.preventDefault();done(false);}
      if(e.key==="Enter"&&document.activeElement!==ok){e.preventDefault();done(true);}
    });
    setTimeout(()=>{try{ok.focus();}catch(e){}},30);
  });
}
function tmPrompt(title,opts){
  opts=opts||{};
  return new Promise(resolve=>{
    tmCloseDialog(undefined);
    _tmSettle=resolve;
    const prevFocus=document.activeElement;
    const back=document.createElement("div");back.className="tm-back";
    const box=document.createElement("div");box.className="tm-modal";
    box.setAttribute("role","dialog");box.setAttribute("aria-modal","true");
    const h=document.createElement("h3");h.textContent=title;
    box.appendChild(h);
    if(opts.hint){
      const p=document.createElement("p");p.textContent=opts.hint;
      box.appendChild(p);
    }
    const inp=document.createElement("input");
    inp.className="input";inp.dir="auto";inp.spellcheck=false;
    inp.placeholder=opts.placeholder||"";inp.value=opts.value||"";
    inp.setAttribute("aria-label",title);
    box.appendChild(inp);
    const row=document.createElement("div");row.className="tm-actions";
    const cancel=document.createElement("button");cancel.className="btn ghost";
    cancel.type="button";cancel.textContent=opts.cancelText||"Cancel";
    const ok=document.createElement("button");ok.className="btn primary";
    ok.type="button";ok.textContent=opts.okText||"Add";
    row.appendChild(cancel);row.appendChild(ok);
    box.appendChild(row);
    back.appendChild(box);document.body.appendChild(back);
    const done=v=>{if(prevFocus&&prevFocus.focus)try{prevFocus.focus();}catch(e){}tmCloseDialog(v);};
    cancel.addEventListener("click",()=>done(null));
    const commit=()=>done(inp.value);
    ok.addEventListener("click",commit);
    back.addEventListener("mousedown",e=>{if(e.target===back)done(null);});
    inp.addEventListener("keydown",e=>{
      if(e.key==="Enter"){e.preventDefault();commit();}
      else if(e.key==="Escape"){e.preventDefault();done(null);}
      e.stopPropagation();
    });
    back.addEventListener("keydown",e=>{if(e.key==="Escape"){e.preventDefault();done(null);}});
    setTimeout(()=>{try{inp.focus();inp.select();}catch(e){}},30);
  });
}
const byId=i=>state.topics.find(t=>t.id===i);
const escTop=s=>esc(s).replace(/\\n/g,"<br>");

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
  if(tab==="settings"){
    const cur=(SETTINGS_TABS.find(t=>t[0]===settingsSub)||[])[1]||"Settings";
    list.innerHTML=emptyHtml("Settings",cur+" preferences are on the right. Pick a section above the cards to switch.");
    return;
  }
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
      <div class="ti-b"><div class="ti-t" dir="auto">${esc(t.title)}</div><div class="ti-s" dir="auto">${esc(sub)}</div></div>
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
    <div class="row"><input id="ntTitle" class="input grow" dir="auto" placeholder="Topic name — e.g. Rust borrow checker">
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
    if(!await tmConfirm("The folder and its files will be deleted. Your points are not touched.",{title:"Remove this export?",okText:"Remove",danger:true})) return;
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
  else body=`<div class="preview-frame-wrap"><iframe id="mPreviewFrame" title="Template preview" sandbox="allow-same-origin"></iframe></div>`;
  return `<div class="preview-col">
    <div class="preview-h">Preview &mdash; ${esc(title)} &middot; sample data &middot; full width below</div>
    ${body}
    <div class="preview-toolbar">
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
  const accent=tp.accent||"";
  return `<div class="tpl ${on?"on":""}" data-tpl="${esc(tp.id)}" tabindex="0" role="button"${accent?` style="--tpl-accent:${esc(accent)}"`:""}>
      <span class="tpl-cover" aria-hidden="true"><span class="tpl-titlebar"></span></span>
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
      <div class="tpl-panel ${opts.previewTemplate?"has-preview":""}">
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
  // The stages sit at the bottom of a scrolling dialog, below the fold on
  // most window sizes. Without this the Export button's "Exporting..." state
  // is the only thing that changes on screen, and the steps themselves are
  // only found by scrolling down by hand. Bring them into view instead -
  // the dialog body scrolls, the footer with the button stays put.
  try{
    const scroller=el.closest(".modal-b")||el.parentElement;
    if(scroller&&typeof scroller.scrollTo==="function")
      scroller.scrollTo({top:scroller.scrollHeight,behavior:"smooth"});
    else if(el.scrollIntoView) el.scrollIntoView({block:"nearest",behavior:"smooth"});
  }catch(e){}
}

async function openExportDialog(t, closing){
  // Categories/templates need to be fresh before the dialog can pre-select a
  // category (defaultExportOpts reads state.categories/state.templates), so
  // this always re-fetches first. Measured against the real app this is a
  // single local pywebview round-trip - no visible delay before the dialog
  // appears - so there is no debounce/cache here; revisit if that changes.
  try{
    const r=await api.list_categories();
    if(r&&!r.error) applyState(r);
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
      api.list_categories().then(r=>{if(r&&!r.error){applyState(r); renderBody();}}).catch(()=>{});
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
      if(r&&r.error) return toast(r.error,"err");
      applyState(r);
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
      if(r&&r.error) return toast(r.error,"err");
      applyState(r);
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
          if(c&&c.error){clearInterval(tick); go.disabled=false; go.textContent="Export"; return toast(c.error,"err");}
          applyState(c);
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
      applyState(await api.get_state());
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
  // Filter-only chips: clicking narrows the entries below. Adding and deleting
  // live next to the destination dropdown in the composer, where they are used.
  // The whole card is hidden until a first sub-topic exists.
  const subs=(t.subtopics||[]).map(s=>`<button class="chip ${filterSub===s?"active":""}" data-s="${esc(s)}">${esc(s)}</button>`).join("");
  const hasAI=state.config.llm&&state.config.llm.enabled&&(state.config.llm.api_key||"").trim()!=="";
  const acts=t.status==="open"
    ?`<button class="btn primary sm" id="tClose">Close &amp; export</button><button class="btn danger sm" id="tDel">Delete</button>`
    :`<button class="btn primary sm" id="tExp">Export report…</button>${hasAI?`<button class="btn ghost sm" id="tDraft">Draft AI summary</button>`:""}<button class="btn ghost sm" id="tReopen">Reopen</button><button class="btn danger sm" id="tDel">Delete</button>`;
  const composer=t.status==="open"?`<div class="card sub glass composer">
    <div class="row"><select id="cSub" class="input grow" title="File the point under this sub-topic"></select>
      <button class="chip accent" id="cSubAdd" title="Create a new sub-topic">+ add</button>
      <button class="btn danger sm" id="cSubDel" title="Delete the selected sub-topic" hidden>Delete</button>
      <input id="cLink" class="input grow" placeholder="Source link…">
      <button class="chip" id="cLinkAdd">+ Link</button></div>
    ${sciOn()?`<div class="row"><div class="kinds grow" id="cKinds">
      ${["claim","note","quote"].map(k=>`<button class="k ${compKind===k?"on":""}" data-kind="${k}">${KIND_LABEL[k]}</button>`).join("")}
    </div><span class="muted" style="flex:2;min-width:180px;font-size:11px">${esc(KIND_HINT[compKind]||"")}</span></div>`:""}
    <div class="row"><textarea id="cText" class="input ta grow" dir="auto" rows="2" placeholder="Type or paste the point…" spellcheck="false"></textarea>
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
    <div class="e-text" dir="auto" style="white-space:pre-line;margin-bottom:10px">${esc(summaryDraft)}</div>
    <div class="row"><button class="btn ghost sm" id="sumCopy">Copy</button>
      <button class="btn ghost sm" id="sumClose">Dismiss</button></div>
  </div>`:"";
  return `<div class="cards">
    ${summaryBlock}
    <div class="dhead">
      <span class="dot ${t.status}"></span>
      <div class="dh-b"><div class="dh-t" dir="auto">${esc(t.title)}</div>
        <div class="dh-s">${n} point${n===1?"":"s"} · created ${fmt(t.created)}${t.closed?" · closed "+fmt(t.closed):""}</div></div>
      ${pill}
    </div>
    ${(t.subtopics||[]).length?`<div class="card sub glass">
      <div class="row">
        <span class="muted">Filter:</span>
        <div class="chips grow">${subs}</div>
        ${filterSub?`<button class="btn ghost sm" id="subClear">Clear filter</button>`:""}
      </div>
    </div>`:""}
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
    ?`<div class="edit"><textarea id="eeText" class="input ta" dir="auto" rows="2">${esc(e.text)}</textarea>
       <div class="row"><input id="eeSub" class="input grow" dir="auto" placeholder="Sub-topic" value="${esc(e.subtopic||"")}">
       <button class="btn primary sm" id="eeSave">Save</button><button class="btn ghost sm" id="eeCancel">Cancel</button></div></div>`
    :`<div class="e-actions">
        ${state.config.llm&&state.config.llm.enabled?`<button class="btn ghost sm" data-polish="${e.id}">Polish</button>`:""}
        <button class="btn ghost sm" data-edit="${e.id}">Edit</button>
        <button class="btn danger sm" data-del="${e.id}">Delete</button>
       </div>`;
  return `<div class="card sub glass entry fade">
    <div class="e-meta">${when}${sub}${kindBadge}</div>
    <div class="e-text" dir="auto">${escTop(e.text)}</div>
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
    if(!await tmConfirm("All its points are deleted permanently.",{title:"Delete "+t.title+"?",okText:"Delete",danger:true}))return;
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
  const sAdd=$("#subClear");
  if(sAdd)sAdd.addEventListener("click",()=>{filterSub=null;displayLimit=20;render();});
  // Filter chips: one job — narrow the entries below.
  document.querySelectorAll("button[data-s]").forEach(b=>b.addEventListener("click",()=>{
    filterSub=b.dataset.s;displayLimit=20;render();
  }));
  document.querySelectorAll("[data-url]").forEach(el=>el.addEventListener("click",()=>api.open_url(el.dataset.url)));
  document.querySelectorAll("[data-copy]").forEach(el=>el.addEventListener("click",()=>copyText(el.dataset.copy)));
  document.querySelectorAll(".thumb").forEach(el=>el.addEventListener("click",()=>api.open_path(el.dataset.path)));
  document.querySelectorAll("[data-edit]").forEach(b=>b.addEventListener("click",()=>{editEntry=b.dataset.edit;render();}));
  document.querySelectorAll("[data-del]").forEach(b=>b.addEventListener("click",async()=>{
    if(!await tmConfirm("The point and its sources are removed.",{title:"Delete this point?",okText:"Delete",danger:true}))return;
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
  // Sub-topic management lives here, next to the destination it acts on. The
  // delete button only shows when a real sub-topic is selected, so General
  // can never be "deleted". Typed text survives the re-render both actions end in.
  const subDel=$("#cSubDel");
  const syncSubDel=()=>{if(subDel)subDel.hidden=!sub.value;};
  sub.addEventListener("change",syncSubDel);syncSubDel();
  const keepComposer=()=>({text:$("#cText").value,link:$("#cLink").value,str:$("#cStr").value});
  const restoreComposer=k=>{if($("#cText"))$("#cText").value=k.text;
    if($("#cLink"))$("#cLink").value=k.link;if($("#cStr"))$("#cStr").value=k.str;};
  $("#cSubAdd").addEventListener("click",async()=>{
    const keep=keepComposer();
    const name=await tmPrompt("New sub-topic",{hint:"Adds to "+t.title+".",placeholder:"Sub-topic name…",okText:"Add sub-topic"});
    if(!name||!name.trim())return;
    const r=await api.add_subtopic(t.id,name.trim());
    if(r.error)return toast(r.error,"err");
    state=r;render();restoreComposer(keep);
    const sel2=$("#cSub");
    if(sel2&&[...sel2.options].some(o=>o.value===name.trim())){sel2.value=name.trim();sel2.dispatchEvent(new Event("change"));}
    toast("Sub-topic added.");
  });
  if(subDel)subDel.addEventListener("click",async()=>{
    const name=sub.value;if(!name)return;
    if(!await tmConfirm("Points filed under it move back to General.",{title:"Delete sub-topic "+name+"?",okText:"Delete",danger:true}))return;
    const keep=keepComposer();
    const r=await api.delete_subtopic(t.id,name);
    if(r.error)return toast(r.error,"err");
    if(filterSub===name)filterSub=null;
    state=r;render();restoreComposer(keep);
  });
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

async function closeAndExport(){
  const t=byId(sel); if(!t) return;
  if(!await tmConfirm("It will be locked, then exported.",{title:"Close this topic?",okText:"Close & export",danger:false}))return;
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

function settingsTabsBar(){
  return `<div class="set-tabs" role="tablist" aria-label="Settings sections">`+
    SETTINGS_TABS.map(([id,label])=>
      `<button type="button" role="tab" class="set-tab ${settingsSub===id?"on":""}" `+
      `data-settingssub="${id}" aria-selected="${settingsSub===id?"true":"false"}">${label}</button>`
    ).join("")+`</div>`;
}
// Settings › Templates manager gallery. Same template objects the export
// dialog uses, but as a managing surface: every template visible at once with
// its category, formats and a real preview - not a 320px column.
function settingsTplGalleryHtml(){
  const tpls=state.templates||[];
  const cats=state.categories||[];
  const catName=id=>(cats.find(c=>c.id===id)||{}).name||id||"—";
  if(!tpls.length) return `<p class="muted">No templates found. Open the templates folder and drop one in.</p>`;
  return `<div class="tpls" style="max-height:none">`+tpls.map(tp=>{
    const on=tplMgrPreview===tp.id;
    const accent=tp.accent||"";
    return `<div class="tpl ${on?"on":""}" data-tplmgr="${esc(tp.id)}" tabindex="0" role="button" aria-pressed="${on}"${accent?` style="--tpl-accent:${esc(accent)}"`:""}>
      <span class="tpl-cover" aria-hidden="true"><span class="tpl-titlebar"></span></span>
      <span class="tpl-b">
        <span class="tpl-n">${esc(tp.name)}${tp.source==="user"?`<span class="badge">yours</span>`:`<span class="badge">built-in</span>`}</span>
        <span class="tpl-d">${esc(tp.description||"")}</span>
        <span class="muted" style="font-size:11px">${esc(catName(tp.category))} &middot; ${esc((tp.formats||[]).join(", ").toUpperCase()||"—")}</span>
        <span class="tpl-actions">
          <button type="button" class="tpl-preview-btn" data-tplmgr-preview="${esc(tp.id)}">${on?"Hide preview":"Preview"}</button>
          <button type="button" class="tpl-set-default" data-tplmgr-use="${esc(tp.id)}">Use for its category</button>
        </span>
      </span>
    </div>`;
  }).join("")+`</div>`;
}
function settingsTplPreviewHtml(){
  if(!tplMgrPreview) return "";
  const tp=(state.templates||[]).find(x=>x.id===tplMgrPreview);
  const title=tp?tp.name:tplMgrPreview;
  let body;
  if(tplMgrLoading) body=`<div class="preview-empty">Rendering sample report…</div>`;
  else if(tplMgrError) body=`<div class="preview-empty">${esc(tplMgrError)}</div>`;
  else body=`<div class="tplmgr-preview-wrap"><iframe id="tplMgrFrame" title="Template preview" sandbox="allow-same-origin"></iframe></div>`;
  return `<div style="margin-top:14px">
    <div class="preview-h" style="margin-bottom:8px">Preview &mdash; ${esc(title)} &middot; sample data &middot; full width</div>
    ${body}
    <div class="preview-toolbar" style="margin-top:8px">
      <button type="button" class="btn ghost sm" id="tplMgrClose">Close preview</button>
    </div>
  </div>`;
}
// Settings › microphone: one live line under the dropdown. The first paint
// only knows the saved name and the last device list; the poller in
// bindSettings() replaces this with what capture is actually using, in
// place, without rebuilding the form.
function devNoteText(){
  try{
    const devs=state.asrDevices||[];
    const saved=String(((state.config||{}).asr||{}).device||"");
    if(!saved||!devs.length) return "";
    if(!devs.some(d=>String(d.id)===saved))
      return "\u201c"+saved+"\u201d is not connected \u2014 capture uses the system default and switches back when it returns.";
  }catch(e){}
  return "";
}
// Bluetooth hands-free endpoints sleep aggressively and take the capture
// stream down with them. The watcher follows them back automatically, but
// saying so once, next to the dropdown, beats another mysterious silence.
function handsFreeHint(name){
  try{
    if(/hands-?free|headset|\\bhfp\\b/i.test(String(name||"")))
      return "This looks like a Bluetooth hands-free endpoint: those sleep aggressively and vanish mid-session. Trailmark switches back to it automatically when it returns; keeping the headset awake (or using the built-in microphone) drops out less.";
  }catch(e){}
  return "";
}
function settingsHtml(){
  const c=state.config||{};
  const hk=c.hotkey||{};
  const llm=c.llm||{};
  const mods=hk.modifiers||["ctrl","alt"];
  const prov=(state.providers||{});
  const mk=(id,checked,label)=>`<label class="mod"><input type="checkbox" id="${id}" ${checked?"checked":""}> ${label}</label>`;
  const provOpts=Object.keys(prov).map(k=>`<option value="${k}" ${llm.provider===k?"selected":""}>${prov[k].label}</option>`).join("");
  const ex=c.export||{}, app=c.appearance||{}, sci=c.science||{}, cb=c.clipboard||{}, asr=c.asr||{}, tg=c.telegram||{};
  const vc=c.voice||{}, vcKeys=vc.keys||{};
  const jd=c.judge||{}, ji=state.judge_info||{};
  const jdModel=ji.model||"jev", jdTh=ji.thresholds||{};
  const vcMods=(vc.modifiers||["ctrl","alt"]).map(m=>m[0].toUpperCase()+m.slice(1)).join("+");
  const vcRows=(state.voiceGrammar||[]).map(g=>`<tr><td><b>${esc(g.say)}</b></td><td>${esc(g.summary)}</td><td dir="rtl" class="muted">${esc(g.persian||"")}</td></tr>`).join("");
  // "session <name>" is the one form code cannot settle - "session Rust" is a
  // command, "session times were short" is a sentence - so it asks the
  // second opinion first, and a short verb-less name is also accepted by a
  // small local check when no opinion is available. Say so here, not only on
  // the first failed attempt.
  const vcOpinion=state.voiceOpinion?`<p class="muted">&ldquo;Session&rdquo; and &ldquo;tab&rdquo; with a name are told apart from sentences by the second opinion.</p>`
    :`<p class="muted" style="background:var(--surface-sunken);border-radius:var(--r-lg);padding:10px 12px">Short names (up to three words, no verb) work alone; longer ones need the second opinion below. Force any of them with &ldquo;trail&rdquo;: &ldquo;trail session Rust&rdquo;.</p>`;
  const vcHot=(state.voiceHotkeys||[]);
  const vcKeyRow=(id,name,label)=>`<label>${label}<input id="${id}" class="input" maxlength="12" value="${esc(vcKeys[name]||"")}"></label>`;
  const tgStatus=state.telegramStatus||{state:"off",detail:"",username:"",pairing_code:tg.pairing_code||"",token_source:"none"};
  const asrDevs=state.asrDevices||[];
  // Names, not indexes: a name survives a reboot and a USB microphone being
  // plugged in. A saved microphone that is not connected stays listed, marked,
  // rather than silently becoming a different one.
  const asrDevSaved=String(asr.device||"");
  const asrDeviceOpts=`<option value="" ${asrDevSaved===""?"selected":""}>System default</option>`+
    asrDevs.map(d=>`<option value="${esc(d.id)}" ${asrDevSaved===String(d.id)?"selected":""}>${esc(d.name)}${d.default?" (default)":""}</option>`).join("")+
    ((asrDevSaved&&!asrDevs.some(d=>String(d.id)===asrDevSaved))?`<option value="${esc(asrDevSaved)}" selected>${esc(asrDevSaved)} (not connected)</option>`:"");
  const asrLang=String(asr.language||"");
  const asrLangOpts=[["","Persian or English"],["fa","Persian only"],["en","English only"]]
    .map(([v,l])=>`<option value="${v}" ${asrLang===v?"selected":""}>${l}</option>`).join("");
  const speakerBody=speakerHtml(state.speakerInfo);
  const styleOpts=CITE_STYLES.map(x=>`<option value="${x.id}" ${(sci.style||"numeric")===x.id?"selected":""}>${esc(x.label)}</option>`).join("");
  const styleHint=(CITE_STYLES.find(x=>x.id===(sci.style||"numeric"))||{}).hint||"";
  const tpls=state.templates||[];
  const builtinN=tpls.filter(t=>t.source==="builtin").length;
  const tplOpts=tpls.map(t=>`<option value="${esc(t.id)}" ${ex.template===t.id?"selected":""}>${esc(t.name)}${t.source==="user"?" (yours)":""}</option>`).join("");
  const xf=ex.formats||["html","pdf","markdown"];
  const fmtBoxes=[["html","HTML"],["pdf","PDF"],["docx","DOCX"],["markdown","Markdown"]].map(
    ([k,l])=>`<label class="fmt-opt ${xf.includes(k)?"on":""}"><input type="checkbox" data-xfmt="${k}" ${xf.includes(k)?"checked":""}><span><b>${l}</b></span></label>`).join("");
  const hid=name=>settingsSub===name?"":"hidden";
  return settingsTabsBar()+`<div class="cards set-panels">
    <div class="card glass fade" ${hid("shortcuts")}>
      <div class="card-h"><div class="card-t">Global hotkey</div></div>
      <p class="muted">Press this combination anywhere on Windows to show or hide the quick capture popup. It never steals focus until you ask for it.</p>
      <div class="row">
        ${mk("mCtrl",mods.includes("ctrl"),"Ctrl")}${mk("mAlt",mods.includes("alt"),"Alt")}${mk("mShift",mods.includes("shift"),"Shift")}${mk("mWin",mods.includes("win"),"Win")}
        <input id="kKey" class="input kkey" maxlength="1" placeholder="P" value="${esc(hk.key||"P")}">
        <button class="btn primary" id="hkSave">Apply hotkey</button>
      </div>
      <p class="muted" id="hkInfo"></p>
    </div>
    <div class="card glass fade" ${hid("shortcuts")}>
      <div class="card-h"><div class="card-t">Log clipboard</div></div>
      <p class="muted">Opens quick capture with the clipboard attached as a source — detected as image, link or text.</p>
      <div class="row" style="align-items:center;gap:8px">
        <span class="key">Ctrl</span><span class="plus">+</span><span class="key">Alt</span><span class="plus">+</span><span class="key">V</span>
        <button class="sw ${cb.enabled?"on":""}" id="cbSw" type="button" role="switch" aria-checked="${cb.enabled?"true":"false"}" aria-label="Enable clipboard hotkey" style="margin-left:auto"><span class="kn"></span></button>
      </div>
    </div>
    <div class="card glass fade" ${hid("ai")}>
      <div class="card-h"><div class="card-t">AI assist</div></div>
      <p class="muted">Optional, bring-your-own-key: polish points, summaries, and polished exports. Default: <b>OpenRouter</b> + <b>deepseek/deepseek-v4-flash</b>.</p>
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
    <div class="card glass fade" ${hid("ai")}>
      <div class="card-h"><div class="card-t">Always-on voice</div></div>
      <div class="row" style="align-items:flex-start;gap:10px">
        <div style="flex:1;min-width:0">
          <b style="font-size:12.5px;font-weight:650;display:block">Always-on voice</b>
          <p class="muted" style="margin:3px 0 0">The master switch. While on, speech lands as text in the quick-capture box and is filed when you say &ldquo;log&rdquo; or press Log.</p>
        </div>
        <button class="sw ${asr.enabled?"on":""}" id="asrSw" type="button" role="switch" aria-checked="${asr.enabled?"true":"false"}" aria-label="Always-on voice" style="flex:none"><span class="kn"></span></button>
      </div>
      <div class="grid3">
        <label>Endpoint<input id="asrEndpoint" class="input" placeholder="https://openrouter.ai/api/v1" value="${esc(asr.endpoint||"")}"></label>
        <label>Model<input id="asrModel" class="input" placeholder="whisper-1" value="${esc(asr.model||"whisper-1")}"></label>
        <label>Language<select id="asrLang" class="input">${asrLangOpts}</select></label>
      </div>
      <p class="muted">Any OpenAI-compatible /audio/transcriptions endpoint. For Groq: <b>https://api.groq.com/openai/v1</b> with <b>whisper-large-v3-turbo</b>. Transcripts are <b>Persian or English only</b>.</p>
      <div class="row">
        <label class="grow" style="min-width:200px">API key<input id="asrKey" class="input" type="password" placeholder="sk-…" value="${esc(asr.api_key||"")}"></label>
        <button class="btn ghost" id="asrShow">Show</button>
        <button class="btn primary" id="asrSave">Save settings</button>
      </div>
      <div class="row" style="align-items:flex-end">
        <label class="grow" style="min-width:220px">Microphone<select id="asrDevice" class="input" ${micTestOn?"disabled":""}>${asrDeviceOpts}</select></label>
        <button class="btn ghost" id="mtBtn" type="button">${micTestOn?"Stop test":"Test microphone"}</button>
        <button class="btn ghost" id="mtRefresh" type="button" title="Re-check which microphones are connected" ${micTestOn?"disabled":""}>Refresh</button>
        ${(!micTestOn&&micHadRecording)?'<button class="btn ghost" id="mtPlay" type="button" title="Hear what the last test recorded">Play recording</button>':""}
      </div>
      <div class="muted" id="mtDevNote" style="min-height:16px">${esc(devNoteText())}</div>
      <div class="muted" id="hfHint" style="min-height:16px">${handsFreeHint(asrDevSaved)||""}</div>
      <canvas class="mwave" id="mtWave" aria-label="Microphone level"></canvas>
      <div class="muted" id="mtOut" style="min-height:16px">${micTestOn?esc(micNote):esc(asrDevs.length+" microphone"+(asrDevs.length===1?"":"s")+" found. Speakers, loopback and duplicate driver entries are left out.")}</div>
      <label style="display:block">Sensitivity
        <input id="asrSensitivity" type="range" min="0" max="100" value="${asr.sensitivity!=null?asr.sensitivity:50}" style="width:100%;accent-color:var(--accent);margin-top:6px">
      </label>
      <p class="muted" style="margin-top:2px">Bars that light up count as speech. Your voice should light up; the room should not.</p>
      <div class="row"><button class="btn ghost sm" id="asrTest">Transcribe 5 seconds</button><span class="muted" id="asrTestOut"></span></div>
      <div class="row" style="background:var(--accent-tint);border:1px solid var(--accent);border-radius:var(--r-lg);padding:14px 16px;align-items:flex-start">
        <div>
          <b style="display:block;font-size:12.5px;margin-bottom:4px">Voice is strictly opt-in.</b>
          <p class="muted" style="margin:0">Trailmark only listens to your own microphone while this switch is on &mdash; never system audio, other apps, or call/loopback audio. Turning it off immediately stops capture. Nothing is recorded to disk; only the transcribed text lands in your draft.</p>
        </div>
      </div>
    </div>
    <div class="card glass fade" ${hid("ai")}>
      <div class="card-h"><div class="card-t">Only my voice</div></div>
      <p class="muted">For rooms where others talk: each sentence is checked against your voiceprint <b>before</b> anything is transcribed. Other voices are held aside &mdash; the last ${((state.speakerInfo||{}).held_max||3)} stay listed below. The voiceprint is 256 numbers in config.json; no audio is stored.</p>
      ${speakerBody}
    </div>
    <div class="card glass fade" ${hid("shortcuts")}>
      <div class="card-h"><div class="card-t">Commands &amp; hotkeys</div></div>
      <p class="muted">These refine always-on voice above; they do nothing while it is off.</p>
      <div class="row" style="align-items:flex-start;gap:10px">
        <div style="flex:1;min-width:0">
          <b style="font-size:12.5px;font-weight:650;display:block">Compose, don&rsquo;t file each phrase</b>
          <p class="muted" style="margin:3px 0 0">On: speech joins the draft; you decide when it becomes a point. Off: every phrase is filed at once.</p>
        </div>
        <button class="sw ${vc.always_on!==false?"on":""}" id="vcSw" type="button" role="switch" aria-checked="${vc.always_on!==false?"true":"false"}" aria-label="Compose what I say into a draft" style="flex:none"><span class="kn"></span></button>
      </div>
      <div class="row" style="align-items:flex-start;gap:10px">
        <div style="flex:1;min-width:0">
          <b style="font-size:12.5px;font-weight:650;display:block">Listen for spoken commands</b>
          <p class="muted" style="margin:3px 0 0">Say a command <i>on its own</i>: &ldquo;log&rdquo;, &ldquo;save&rdquo;, &ldquo;finish&rdquo;. &ldquo;Session&rdquo; and &ldquo;tab&rdquo; take a name. A command at the end of a sentence stays dictation.</p>
        </div>
        <button class="sw ${vc.commands!==false?"on":""}" id="vcCmdSw" type="button" role="switch" aria-checked="${vc.commands!==false?"true":"false"}" aria-label="Listen for spoken commands" style="flex:none"><span class="kn"></span></button>
      </div>
      <table class="tbl"><tbody>${vcRows||'<tr><td class="muted">No commands loaded.</td></tr>'}</tbody></table>
      ${vcOpinion}
      <div class="row" style="align-items:flex-start;gap:10px">
        <div style="flex:1;min-width:0">
          <b style="font-size:12.5px;font-weight:650;display:block">Global hotkeys (${esc(vcMods)}+&hellip;)</b>
          <p class="muted" style="margin:3px 0 0">The same commands as global hotkeys.</p>
        </div>
        <button class="sw ${vc.hotkeys!==false?"on":""}" id="vcHkSw" type="button" role="switch" aria-checked="${vc.hotkeys!==false?"true":"false"}" aria-label="Enable voice hotkeys" style="flex:none"><span class="kn"></span></button>
      </div>
      <div class="grid3">
        ${vcKeyRow("vcKeyLog","log","Log")}
        ${vcKeyRow("vcKeyFinish","finish","Finish")}
        ${vcKeyRow("vcKeySession","session","New session")}
        ${vcKeyRow("vcKeyTab","tab","New tab")}
      </div>
      <div id="vcHkStatus" class="muted" style="margin-top:8px">${vcHot.length?vcHot.map(h=>esc(h.combo)+" &rarr; "+esc(h.command)+(h.registered?"":" <b class='taken'>(taken)</b>")).join(" &middot; "):"Not registered yet."}</div>
      <div class="row"><button class="btn primary" id="vcSave">Save settings</button></div>
      <div class="row" style="background:var(--surface-sunken);border-radius:var(--r-lg);padding:12px 14px;align-items:flex-start">
        <p class="muted" style="margin:0">Removing words or a source is done by hand, in the quick-capture box &mdash; never by voice. A misheard delete has no undo.</p>
      </div>
    </div>
    <div class="card glass fade" ${hid("ai")}>
      <div class="card-h"><div class="card-t">Second opinion</div></div>
      <p class="muted">Two judgements, not calculations: whether the polished draft kept your notes, and what a captured line is. They go to <b>TypeSafe System One</b> (bring your own key); with it off, a substring test and file-as-note apply.</p>
      <div class="row" style="align-items:flex-start;gap:10px">
        <div style="flex:1;min-width:0">
          <b style="font-size:12.5px;font-weight:650;display:block">Use a second opinion</b>
          <p class="muted" style="margin:3px 0 0">Nothing is sent unless this is on. What travels is one note and the one paragraph of the draft nearest it &mdash; never the whole report.</p>
        </div>
        <button class="sw ${jd.enabled?"on":""}" id="jdSw" type="button" role="switch" aria-checked="${jd.enabled?"true":"false"}" aria-label="Use a second opinion" style="flex:none"><span class="kn"></span></button>
      </div>
      <div class="grid3">
        <label>Model<input id="jdModel" class="input" placeholder="${esc(jdModel)}" value="${esc(jd.model||"")}"></label>
        <label>Endpoint<input id="jdBase" class="input" placeholder="auto" value="${esc(jd.base_url||"")}"></label>
        <label>API key<input id="jdKey" class="input" type="password" placeholder="ts-…" value="${esc(jd.api_key||"")}"></label>
      </div>
      <div class="row" style="align-items:flex-start;gap:10px">
        <div style="flex:1;min-width:0">
          <b style="font-size:12.5px;font-weight:650;display:block">Check the polished draft against your notes</b>
          <p class="muted" style="margin:3px 0 0">Asks, per note, whether the polished draft still says what you said &mdash; overturning only at ${esc(jdTh.note_preserved_overturn)} confidence or better.</p>
        </div>
        <button class="sw ${jd.notes!==false?"on":""}" id="jdNotesSw" type="button" role="switch" aria-checked="${jd.notes!==false?"true":"false"}" aria-label="Check notes against the polished draft" style="flex:none"><span class="kn"></span></button>
      </div>
      <div class="row" style="align-items:flex-start;gap:10px">
        <div style="flex:1;min-width:0">
          <b style="font-size:12.5px;font-weight:650;display:block">Work out what a captured line is</b>
          <p class="muted" style="margin:3px 0 0">Decides whether a captured line is a claim, note or quotation &mdash; changing it only at ${esc(jdTh.capture_kind_min)} confidence or better.</p>
        </div>
        <button class="sw ${jd.kinds!==false?"on":""}" id="jdKindsSw" type="button" role="switch" aria-checked="${jd.kinds!==false?"true":"false"}" aria-label="Work out what a captured line is" style="flex:none"><span class="kn"></span></button>
      </div>
      <div class="row"><button class="btn ghost sm" id="jdTest">Test connection</button><span class="muted" id="jdTestOut"></span><button class="btn primary" id="jdSave">Save settings</button></div>
      <div class="row" style="background:var(--surface-sunken);border-radius:var(--r-lg);padding:12px 14px;align-items:flex-start">
        <p class="muted" style="margin:0">It never rewrites text and never blocks an export.</p>
      </div>
    </div>
    <div class="card glass fade" ${hid("integrations")}>
      <div class="card-h"><div class="card-t">Telegram bridge</div></div>
      <p class="muted">Take points from Telegram through a private bot pairing.</p>
      <div class="row" style="align-items:center;gap:8px">
        <div style="flex:1;min-width:0">
          <b style="font-size:12.5px;font-weight:650;display:block">Accept points from Telegram</b>
        </div>
        <button class="sw ${tg.enabled?"on":""}" id="tgSw" type="button" role="switch" aria-checked="${tg.enabled?"true":"false"}" aria-label="Enable Telegram bridge" style="flex:none"><span class="kn"></span></button>
      </div>
      <div style="padding:12px;border-radius:var(--r-md);background:var(--surface-sunken);">
        <div style="font-size:12.5px;font-weight:600;margin-bottom:6px">Status: <span id="tgStatusRow">${tgStatus.state==="off"?"Off":tgStatus.state==="waiting"?"Waiting for pairing":tgStatus.state==="paired"?"Paired with @"+esc(tgStatus.username||tg.username||""):tgStatus.state==="error"?"Error: "+esc(tgStatus.detail||""):"Unknown"}</span></div>
      </div>
      <div style="padding:14px;border:1px solid var(--border);border-radius:var(--r-md);background:var(--surface-sunken);">
        <div style="font-size:11.5px;font-weight:600;letter-spacing:.03em;text-transform:uppercase;color:var(--content-muted);margin-bottom:8px">Pairing code</div>
        <div id="tgPairCode" style="font-size:18px;font-family:var(--font-mono);font-weight:700;letter-spacing:2px;text-align:center;padding:10px;background:var(--surface);border-radius:var(--r-sm);margin-bottom:10px;word-break:break-all">${esc(tg.pairing_code||"")}</div>
        <div style="display:flex;gap:8px;justify-content:center">
          <button class="btn ghost sm" id="tgCopyCode">Copy</button>
          <button class="btn ghost sm" id="tgRegenCode">Regenerate</button>
        </div>
        <div style="font-size:11px;color:var(--content-secondary);margin-top:10px;text-align:center;line-height:1.5">Open the Trailmark bot and send <b>/start ${esc(tg.pairing_code||"")}</b></div>
      </div>
      <div>
        <label style="display:flex;flex-direction:column;gap:6px">Bot token<input id="tgToken" class="input" type="password" placeholder="${tg.token_set||tgStatus.token_source==="env"?"Paste a new token to replace":"Paste a bot token from @BotFather"}"></label>
        ${tg.token_set||tgStatus.token_source==="env"?`<div class="muted" style="margin-top:2px">•••• token set (from ${tgStatus.token_source==="env"?"env":"config"})</div>`:""}
        <div class="muted" style="margin-top:8px">From .env or pasted here; never leaves this machine.</div>
      </div>
      <div class="row">
        <button class="btn primary" id="tgSave">Save</button>
        ${tgStatus.state==="paired"?'<button class="btn ghost" id="tgUnpair" style="background:var(--danger-tint);color:var(--danger);border-color:var(--danger)">Unpair</button>':""}
      </div>
    </div>
    <div class="card glass fade" ${hid("appearance")}>
      <div class="card-h"><div class="card-t">Appearance</div></div>
      <p class="muted">Trailmark follows your Windows light/dark setting by default. Override it here if you want one or the other regardless.</p>
      <div class="segmented" id="themeSeg">
        ${["system","light","dark"].map(k=>`<button class="seg ${(app.theme||"system")===k?"active":""}" data-theme="${k}">${k[0].toUpperCase()+k.slice(1)}</button>`).join("")}
      </div>
    </div>
    <div class="card glass fade" ${hid("science")}>
      <div class="card-h"><div class="card-t">Scientific mode</div></div>
      <p class="muted">On: reports keep apart <b>claims</b> (from a source), <b>quotations</b> (verbatim) and your <b>notes</b> (never cited). The AI pass is held to the same rules.</p>
      <div class="row"><label class="mod" style="flex-direction:row"><input type="checkbox" id="sciOn" ${sci.enabled?"checked":""}> Enable scientific mode</label></div>
      <div class="grid3">
        <label>Citation style<select id="sciStyle" class="input">${styleOpts}</select></label>
        <label class="mod" style="flex-direction:row;align-self:end;padding-bottom:8px"><input type="checkbox" id="sciSep" ${sci.separate_notes!==false?"checked":""}> Notes in their own section</label>
        <label class="mod" style="flex-direction:row;align-self:end;padding-bottom:8px"><input type="checkbox" id="sciReq" ${sci.require_source_for_claims?"checked":""}> A claim must have a source</label>
      </div>
      <p class="muted" id="sciHint">${esc(styleHint)}</p>
      <div class="row"><button class="btn primary" id="sciSave">Save scientific mode</button></div>
      <p class="muted">Styles are approximations, not CSL &mdash; blank fields stay blank. For submission, export Markdown and run Pandoc with a <b>.csl</b> file.</p>
    </div>
    <div class="card glass fade" ${hid("templates")}>
      <div class="card-h"><div class="card-t">Templates</div><span class="badge count">${tpls.length}</span></div>
      <p class="muted">Built-ins and your own, previewed against sample data. Yours appear here without a restart.</p>
      ${settingsTplGalleryHtml()}
      ${settingsTplPreviewHtml()}
    </div>
    <div class="card glass fade" ${hid("templates")}>
      <div class="card-h"><div class="card-t">Exports</div></div>
      <p class="muted">Defaults for the export dialog. Whatever you pick in the dialog itself wins for that one export.</p>
      <div class="grid3">
        <label>Default template<select id="xTpl" class="input">${tplOpts}</select></label>
        <label>Your name <span class="muted" style="font-weight:400">(appears on reports)</span><input id="xAuthor" class="input" value="${esc(ex.author||"")}" placeholder="optional"></label>
        <label>Organisation<input id="xOrg" class="input" value="${esc(ex.org||"")}" placeholder="optional"></label>
      </div>
      <div class="row">
        <div class="fmts grow">${fmtBoxes}</div>
      </div>
      <div class="row">
        <button class="btn primary" id="xSave">Save export defaults</button>
        <button class="btn ghost" id="xFolder">Open my templates folder</button>
        <span class="muted" id="xEngines">Checking PDF engines…</span>
      </div>
      <p class="muted">A template is a folder with <b>template.json</b> + <b>template.html</b> using <b>{{title}}</b>, <b>{{body}}</b>, <b>{{references}}</b>. Full field list: <b>TEMPLATES.md</b>.</p>
      ${categoriesHtml()}
    </div>
    <div class="card glass fade" ${hid("appearance")}>
      <div class="card-h"><div class="card-t">Data &amp; privacy</div></div>
      <p class="muted">Everything is stored locally next to the app: <b>points.json</b> for your topics, <b>attachments/</b> for screenshots, <b>exports/</b> for closed reports. No cloud, no telemetry. The AI assist feature only sends a point’s text to the provider you chose, and only when you click <b>Polish</b> or <b>Export</b>.</p>
    </div>
  </div>`;
}

// ---- Settings › voice: the microphone test and "only my voice" ------------
// Three sentences with different sounds in them. Read them in the language you
// dictate in - mixing Persian and English is fine, and is what the check will
// hear afterwards anyway.
const SPK_SENTENCES=[
  "I am writing down what I found today, so that I can check every source again later.",
  "The quick brown fox jumps over the lazy dog, and then it runs all the way back home.",
  "امروز چند منبع تازه پیدا کردم و می‌خواهم نکته‌های مهمش را یادداشت کنم."
];
let micTestOn=false, micRec=null, micTimer=null, spkRedo=false, micNote="", spkNote="", micHadRecording=false;

function speakerHtml(sp){
  if(!sp)return `<p class="muted">Loading…</p>`;
  const held=(sp.held||[]);
  const heldHtml=held.length?`
      <div style="margin-top:14px"><b style="font-size:12.5px;font-weight:650">Held aside</b>
      <span class="muted"> &middot; newest last &middot; kept in memory until Trailmark closes</span></div>
      <table class="tbl" style="margin-top:6px"><tbody>${held.map(h=>`<tr>
        <td>${esc(h.at)}</td><td>${esc(h.seconds)} s</td>
        <td>${esc(h.reason)}${h.score!=null?" &middot; match "+esc(h.score):""}${h.text?`<div dir="auto">&ldquo;${esc(h.text)}&rdquo;</div>`:""}</td>
        <td style="white-space:nowrap;text-align:right"><button class="btn ghost sm" data-held-use="${h.id}">Use it</button>
        <button class="btn ghost sm" data-held-drop="${h.id}">Drop</button></td></tr>`).join("")}</tbody></table>
      <div class="row"><button class="btn ghost sm" id="heldDropAll">Drop all</button></div>`:"";
  if(!sp.runtime)return `<p class="muted"><b>The voice check cannot run in this build:</b> ${esc(sp.runtime_error)}</p>`+heldHtml;
  if(!sp.model)return `
      <div class="row"><button class="btn primary" id="spkDl">Download the voice model (${esc(sp.model_mb)} MB)</button>
      <span class="muted" id="spkOut">${esc(spkNote)}</span></div>
      <p class="muted">WeSpeaker ResNet34, from the sherpa-onnx releases on GitHub. It is checked against a fixed SHA-256 before it is used, and saved next to your data.</p>`+heldHtml;
  const rec=micRec==="enroll"||micRec==="check";
  if(!sp.enrolled||spkRedo){
    const n=sp.recorded||0;
    const body=n<3?`
      <div class="muted" style="margin-top:4px">Sentence ${n+1} of 3 &mdash; press Record, read it at your normal distance and volume, then press Stop.</div>
      <div class="spk-sent" dir="auto">${esc(SPK_SENTENCES[n])}</div>`
      :`<div class="spk-sent">Three sentences recorded.</div>`;
    return body+`
      <canvas class="mwave" id="spkWave" aria-label="Microphone level"></canvas>
      <div class="row">
        ${n<3?`<button class="btn ${rec?"danger":"primary"}" id="spkRec">${rec?"Stop":"Record"}</button>`
             :`<button class="btn primary" id="spkSave">Save my voice</button>`}
        ${n?`<button class="btn ghost" id="spkReset">Start over</button>`:""}
        ${spkRedo?`<button class="btn ghost" id="spkCancel">Cancel</button>`:""}
        <span class="muted" id="spkOut">${esc(spkNote)}</span>
      </div>`+heldHtml;
  }
  const th=Number(sp.threshold||sp.default_threshold||0.55);
  return `
      <div class="row" style="align-items:flex-start;gap:10px;margin-top:6px">
        <div style="flex:1;min-width:0">
          <b style="font-size:12.5px;font-weight:650;display:block">Only transcribe my voice</b>
          <p class="muted" style="margin:3px 0 0">Enrolled ${esc((sp.enrolled_at||"").replace("T"," "))} from ${esc(sp.clips)} sentences (${esc(sp.seconds)} s of speech) &middot; the sentences matched each other at ${esc(sp.consistency)}.</p>
        </div>
        <button class="sw ${sp.enabled?"on":""}" id="spkSw" type="button" role="switch" aria-checked="${sp.enabled?"true":"false"}" aria-label="Only transcribe my voice" style="flex:none"><span class="kn"></span></button>
      </div>
      <label style="display:block;margin-top:10px">Match needed: <b id="spkThOut">${th.toFixed(2)}</b>
        <input id="spkTh" type="range" min="30" max="90" step="1" value="${Math.round(th*100)}" style="width:100%;accent-color:var(--accent);margin-top:6px">
      </label>
      <p class="muted">Yours should score well above the line; if a colleague comes close, raise it. Anything under a second cannot be checked, so it <b>is</b> sent to be transcribed &mdash; but only used if it is a command.</p>
      <canvas class="mwave" id="spkWave" aria-label="Microphone level"></canvas>
      <div class="row">
        <button class="btn ${rec?"danger":"ghost"}" id="spkChk">${rec?"Stop and score":"Record a check"}</button>
        <span class="muted" id="spkOut">${esc(spkNote)}</span>
      </div>
      <div class="row">
        <button class="btn ghost sm" id="spkRedoBtn">Re-record my voice</button>
        <button class="btn ghost sm" id="spkForget">Forget my voice</button>
      </div>`+heldHtml;
}

// The wave in Settings. One loop for both canvases: the plain test and the
// enrollment recording read the same monitor.
function drawWaveOn(c,d){
  if(!c)return;
  const dpr=window.devicePixelRatio||1,w=Math.max(1,c.clientWidth),h=Math.max(1,c.clientHeight);
  if(c.width!==Math.round(w*dpr)||c.height!==Math.round(h*dpr)){c.width=Math.round(w*dpr);c.height=Math.round(h*dpr);}
  const g=c.getContext("2d");g.setTransform(dpr,0,0,dpr,0,0);g.clearRect(0,0,w,h);
  const cs=getComputedStyle(document.documentElement);
  const hot=cs.getPropertyValue("--accent").trim()||"#d9822b";
  const cold=cs.getPropertyValue("--content-muted").trim()||"#888";
  const mid=h/2;
  g.globalAlpha=.35;g.fillStyle=cold;g.fillRect(0,mid-.5,w,1);g.globalAlpha=1;
  if(!d||!d.hi||!d.hi.length)return;
  const N=300,n=d.hi.length,step=w/N,thr=d.threshold||0;
  const s=v=>Math.sign(v)*Math.sqrt(Math.abs(v));
  for(let i=0;i<n;i++){
    const x=(N-n+i)*step;
    const top=mid-s(d.hi[i])*mid*.95, bot=mid-s(d.lo[i])*mid*.95;
    g.fillStyle=(d.rms[i]>=thr&&thr>0)?hot:cold;
    g.fillRect(x,Math.min(top,bot),Math.max(1,step*.7),Math.max(1,Math.abs(bot-top)));
  }
}
function micLoop(){
  clearTimeout(micTimer);micTimer=null;
  if(tab!=="settings"){if(micTestOn||micRec)stopMic();return;}
  if(!micTestOn&&!micRec)return;
  Promise.resolve(api.mic_levels(300)).then(d=>{
    drawWaveOn($("#mtWave"),d);drawWaveOn($("#spkWave"),d);
    if(d&&d.error){const o=$("#mtOut");if(o)o.textContent=d.error;}
    // The monitor stops itself after 30 s so a forgotten test does not hold
    // the microphone; the button follows it.
    if(d&&d.source==="test"&&d.running===false&&micTestOn&&!micRec){micTestOn=false;renderMain();return;}
    if(d&&d.source===""&&micTestOn){micTestOn=false;renderMain();return;}
  }).catch(()=>{}).finally(()=>{if(micTestOn||micRec)micTimer=setTimeout(micLoop,80);});
}
function stopMic(){
  micTestOn=false;micRec=null;clearTimeout(micTimer);micTimer=null;
  Promise.resolve(api.mic_test_stop()).catch(()=>{});
}
async function refreshSpeaker(){
  try{const r=await api.speaker_status();if(r&&!r.error)state.speakerInfo=r;}catch(e){}
  // Only the AI panel shows the voiceprint. Rebuilding any other panel would
  // wipe its form for a card the user cannot even see - and rebuilding while
  // typing wipes the keystrokes. Typing guard lives in refreshFromBridge;
  // here the panel guard is enough (callers already avoid typing contexts).
  if(tab==="settings"&&settingsSub==="ai"&&!isTypingInSettings())renderMain();
}
function isTypingInSettings(){
  const ae=document.activeElement;
  return !!(ae&&tab==="settings"&&
    (ae.tagName==="INPUT"||ae.tagName==="TEXTAREA"||ae.tagName==="SELECT"));
}

// The device watcher pushes "switched" whenever capture moves microphones
// on its own (unplug fall-back, replug return, system-default flip). It
// renders amber with the message, and the same message lands on the live
// line under Settings' microphone row when that panel is open - so the move
// is visible where the microphone is chosen, not just as a chip flash.
function devNoteFromSwitch(detail){
  if(tab!=="settings"||settingsSub!=="ai")return;
  const el=$("#mtDevNote");
  if(el&&detail)el.textContent=detail;
}
function asrState(state,detail){
  if(state==="switched")devNoteFromSwitch(detail);
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
  }else if(state==="switched"){
    chip.classList.add("transcribing");
    chip.innerHTML='<span class="ring"></span><span class="tx"></span>';
    chip.querySelector(".tx").textContent=detail||"Microphone changed";
  }else{
    chip.classList.remove("show");
    chip.innerHTML="";
  }
}
window.asrState=asrState;

// Always-on voice. The full window is not the capture surface - quick capture
// is - so this is a status chip: what is waiting in the draft, and whether
// the voice check has held anything aside.
let mainVoice={draft:{words:0,count_sources:0},always_on:true,listening:false,
               state:"off",detail:"",topic:"",held:0};
let _lastHeldRefresh=0;
function voiceState(payload){
  if(payload&&typeof payload==="object"&&!payload.error)
    mainVoice=Object.assign(mainVoice,payload);
  const sp=state.speakerInfo;
  // Held-count changes used to rebuild the whole settings page on every push
  // (several per utterance while voice is on). Now: AI panel only, not while
  // typing, at most once per 2 s - the chip below already shows the count.
  if(tab==="settings"&&settingsSub==="ai"&&sp&&(sp.held||[]).length!==(mainVoice.held||0)){
    const now=Date.now();
    if(now-_lastHeldRefresh>2000&&!isTypingInSettings()){_lastHeldRefresh=now;refreshSpeaker();}
  }
  const chip=$("#voiceChip");
  if(!chip)return;
  chip.classList.remove("show","listening","logged","error");
  const live=!!(mainVoice.always_on&&mainVoice.listening);
  if(!live){chip.innerHTML="";return;}
  const d=mainVoice.draft||{},words=d.words||0,cs=d.count_sources||0,held=mainVoice.held||0;
  chip.classList.add("show");
  chip.classList.add(mainVoice.state==="error"?"error":(words||cs)?"logged":"listening");
  chip.innerHTML='<span class="tx"></span>';
  let txt;
  if(mainVoice.state==="error")txt=mainVoice.detail||"Voice error";
  else if(words||cs)txt="In the draft: "+words+(words===1?" word":" words")+
    (cs?(" · "+cs+(cs===1?" source":" sources")):"");
  else txt="Voice ready";
  if(held&&mainVoice.state!=="error")txt+=" · "+held+" held";
  chip.querySelector(".tx").textContent=txt;
  const sw=$("#vcSw");
  if(sw){sw.classList.toggle("on",!!mainVoice.always_on);
         sw.setAttribute("aria-checked",mainVoice.always_on?"true":"false");}
}
window.voiceState=voiceState;

function telegramState(st,detail){
  const chip=$("#tgChip");
  if(chip){
    chip.classList.remove("show","tg-waiting","tg-paired","tg-error");
    if(st==="waiting"||st==="paired"||st==="error"){
      chip.classList.add("show");
      if(st==="waiting"){chip.classList.add("tg-waiting");chip.innerHTML='<span class="tx"></span>';chip.querySelector(".tx").textContent="Telegram: waiting for pairing";}
      else if(st==="paired"){chip.classList.add("tg-paired");chip.innerHTML='<span class="tx"></span>';chip.querySelector(".tx").textContent="Telegram: paired"+(detail?(" · "+detail):"");}
      else if(st==="error"){chip.classList.add("tg-error");chip.innerHTML='<span class="tx"></span>';chip.querySelector(".tx").textContent="Telegram: "+(detail||"error");}
    }else{
      chip.innerHTML="";
    }
  }
  const row=$("#tgStatusRow");
  if(row){
    let label;
    if(st==="off")label="Off"; else if(st==="waiting")label="Waiting for pairing";
    else if(st==="paired")label="Paired with @"+(detail||"");
    else if(st==="error")label="Error: "+(detail||"");
    else label=null;
    if(label!==null) row.textContent=label;
  }
  if(st==="off"||st==="waiting"||st==="paired"||st==="error"){
    state.telegramStatus=Object.assign({},state.telegramStatus||{},{state:st,detail:detail});
  }
}
window.telegramState=telegramState;

function bindSettings(){
  // Sub-tab bar. Always present, so this binding is unconditional - everything
  // below it guards on its own panel's elements existing.
  document.querySelectorAll("[data-settingssub]").forEach(b=>b.addEventListener("click",()=>{
    if(settingsSub===b.dataset.settingssub) return;
    settingsSub=b.dataset.settingssub;
    const main=$("#main");
    if(main) main.scrollTop=0;
    renderMain();
  }));
  // Lazy, guarded fetches: only the active panel's data is fetched, once, and
  // each completion merges (applyState) and re-renders at most once. The old
  // code fetched all five on every render and replaced state wholesale, which
  // wiped the other four - five rebuilds per settings open, per save.
  const needCats=settingsSub==="templates"&&!state.categories;
  if(needCats&&!_fetching.cats){
    _fetching.cats=true;
    api.list_categories().then(r=>{
      _fetching.cats=false;
      if(r&&!r.error){applyState(r);if(tab==="settings"&&settingsSub==="templates")renderMain();}
    }).catch(()=>{_fetching.cats=false;});
  }
  const hkInfo=$("#hkInfo");
  if(hkInfo){
    api.get_config().then(c=>{
      const el=$("#hkInfo"); if(!el) return;
      const hk=(c||{}).hotkey||{};
      el.textContent="Current: "+(hk.modifiers||[]).map(m=>m[0].toUpperCase()+m.slice(1)).join("+")+"+"+(hk.key||"P");
    }).catch(()=>{});
  }
  const hkSave=$("#hkSave");
  if(hkSave) hkSave.addEventListener("click",async()=>{
    const mods=[];["ctrl","alt","shift","win"].forEach(m=>{const cb=$("#m"+m[0].toUpperCase()+m.slice(1));if(cb&&cb.checked)mods.push(m);});
    const keyEl=$("#kKey"); const key=(keyEl?keyEl.value:"").trim();
    if(!mods.length){toast("Pick at least one modifier.","err");return;}
    if(!key){toast("Enter a key letter.","err");return;}
    const r=await api.save_hotkey({modifiers:mods,key:key.toUpperCase()});
    if(r&&r.error)return toast(r.error,"err");
    applyState(r);
    if(hkInfo) hkInfo.textContent="Current: "+mods.map(m=>m[0].toUpperCase()+m.slice(1)).join("+")+"+"+key.toUpperCase();
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
    applyState(r);
    toast("Clipboard hotkey "+(next?"enabled.":"disabled."));
  });
  const show=$("#lShow");
  if(show) show.addEventListener("click",()=>{const k=$("#lKey");if(!k)return;k.type=k.type==="password"?"text":"password";show.textContent=k.type==="password"?"Show":"Hide";});
  const lSave=$("#lSave");
  if(lSave) lSave.addEventListener("click",async()=>{
    const cfg={
      llm:{
        enabled:$("#lEnabled")?$("#lEnabled").checked:false,
        provider:$("#lProvider")?$("#lProvider").value:"",
        model:$("#lModel")?$("#lModel").value:"",
        base_url:$("#lBase")?$("#lBase").value:"",
        api_key:$("#lKey")?$("#lKey").value:"",
      }
    };
    const r=await api.save_llm(cfg.llm);
    if(r&&r.error)return toast(r.error,"err");
    applyState(r);toast("AI settings saved.");
  });
  const lTest=$("#lTest");
  if(lTest) lTest.addEventListener("click",async()=>{
    const out=$("#lTestOut");if(out)out.textContent="Testing…";
    const cfg={
      enabled:true,
      provider:$("#lProvider")?$("#lProvider").value:"",
      model:$("#lModel")?$("#lModel").value:"",
      base_url:$("#lBase")?$("#lBase").value:"",
      api_key:$("#lKey")?$("#lKey").value:"",
    };
    const r=await api.test_llm(cfg);
    if(r&&r.ok){if(out)out.textContent="OK — "+(r.reply||"connected");}
    else{if(out)out.textContent="";toast((r&&r.error)||"Connection failed.","err");}
  });
  const lProv=$("#lProvider");
  if(lProv) lProv.addEventListener("change",()=>{
    const k=lProv.value;
    const p=(state.providers||{})[k];
    const mEl=$("#lModel");
    if(p&&mEl){if(!mEl.value||p.model)mEl.value=p.model||"";}
  });

  // --- voice logging (ASR): microphone list only matters on the AI panel ---
  if(settingsSub==="ai"&&!state.asrDevices&&!_fetching.asrDevs){
    _fetching.asrDevs=true;
    api.list_asr_devices().then(r=>{
      _fetching.asrDevs=false;
      state.asrDevices=Array.isArray(r)?r:[];
      if(tab==="settings"&&settingsSub==="ai")renderMain();
    }).catch(()=>{_fetching.asrDevs=false;state.asrDevices=[];});
  }

  // --- always-on voice ---
  // The grammar and the live hotkey report are not part of get_state(): one
  // is a constant this window has no business hard-coding, the other is only
  // true after the listener threads have actually registered.
  if((settingsSub==="ai"||settingsSub==="shortcuts")&&!state.voiceGrammar&&!_fetching.voice){
    _fetching.voice=true;
    api.get_voice().then(v=>{
      _fetching.voice=false;
      if(!v||v.error){state.voiceGrammar=[];return;}
      state.voiceGrammar=v.grammar||[];state.voiceHotkeys=v.hotkeys||[];
      state.voiceOpinion=!!v.second_opinion;
      voiceState(v.draft||{});
      if(tab==="settings"&&(settingsSub==="ai"||settingsSub==="shortcuts"))renderMain();
    }).catch(()=>{_fetching.voice=false;state.voiceGrammar=[];});
  }

  if(settingsSub==="ai"&&state.speakerInfo===undefined&&!_fetching.spk){
    _fetching.spk=true; state.speakerInfo=null;
    refreshSpeaker().finally(()=>{_fetching.spk=false;});
  }
  if(micTestOn||micRec)micLoop();
  // Live microphone presence, without rebuilding the form. A handsfree that
  // sleeps appears and disappears from PortAudio while this page sits open;
  // the dropdown would otherwise offer a mic that is gone, and hide one that
  // came back, until something else re-rendered. This chain only touches the
  // <select> options and the two muted lines below it - never renderMain, so
  // typing and focus survive - and it ends itself the moment the AI panel is
  // left or the row is gone.
  if(settingsSub==="ai"){const myGen=++_devPollGen;devPoll(myGen);}

// Paint the microphone row in place: dropdown options, live note, hint.
// Shared by the background poller and the manual Refresh button, so both
// show the same truth. Never renderMain - typing and focus survive.
function paintMicRow(list,st){
  const sel=$("#asrDevice");
  if(sel&&Array.isArray(list)){
    // Element-wise compare, deliberately separator-free: joining ids needs
    // no separator at all, and a stray control character here once blanked
    // the whole window, so this stays plain on purpose.
    const fp=list.map(d=>String(d.id));
    const same=fp.length===_devPollFp.length&&fp.every((v,i)=>v===_devPollFp[i]);
    if(!same){
      _devPollFp=fp;
      state.asrDevices=list;
      const cur=sel.value;
      const saved=String(((state.config||{}).asr||{}).device||"");
      sel.innerHTML=`<option value="">System default</option>`+
        list.map(d=>`<option value="${esc(d.id)}">${esc(d.name)}${d.default?" (default)":""}</option>`).join("")+
        ((saved&&!list.some(d=>String(d.id)===saved))?`<option value="${esc(saved)}" selected>${esc(saved)} (not connected)</option>`:"");
      if([...sel.options].some(o=>o.value===cur))sel.value=cur;
      else if([...sel.options].some(o=>o.value===saved))sel.value=saved;
    }
  }
  if(st&&!st.error){
    const note=$("#mtDevNote");
    if(note){
      if(st.missing)note.textContent="\u201c"+(st.wanted||"")+"\u201d is not connected \u2014 capture uses the system default and switches back when it returns.";
      else if(st.fell_back&&st.active)note.textContent="Listening on \u201c"+st.active+"\u201d until \u201c"+(st.fallback_from||st.wanted)+"\u201d returns.";
      else if(st.wanted&&st.active)note.textContent="Listening on \u201c"+st.active+"\u201d.";
      else if(st.default)note.textContent="Listening on the system default (\u201c"+st.default+"\u201d).";
      else note.textContent="";
    }
    const hint=$("#hfHint");
    if(hint)hint.textContent=handsFreeHint(st.active||st.wanted||st.default)||handsFreeHint(String(((state.config||{}).asr||{}).device||""));
  }
}
function refreshMicList(){
  let st=null;
  return Promise.resolve(api.asr_device_status()).then(s=>{st=s||{};return api.list_asr_devices();}).then(devs=>{
    if(tab!=="settings"||settingsSub!=="ai"||!$("#asrDevice"))return null;
    paintMicRow(Array.isArray(devs)?devs:[],st);
    return Array.isArray(devs)?devs:[];
  });
}
function devPoll(gen){
  if(gen!==_devPollGen||tab!=="settings"||settingsSub!=="ai"||!$("#asrDevice"))return;
  if(isTypingInSettings()&&document.activeElement&&document.activeElement.id==="asrDevice")return;
  refreshMicList().catch(()=>{}).finally(()=>{
    setTimeout(()=>{try{devPoll(gen);}catch(e){}},5000);
  });
}

  // --- Telegram bridge: only the Integrations panel needs it ---
  if(settingsSub==="integrations"&&!state.telegramStatus&&!_fetching.tg){
    _fetching.tg=true;
    api.telegram_status().then(r=>{
      _fetching.tg=false;
      state.telegramStatus=r;
      if(tab==="settings"&&settingsSub==="integrations")renderMain();
    }).catch(()=>{_fetching.tg=false;});
  }
  function asrCfgFromForm(){
    const devEl=$("#asrDevice");
    const devVal=devEl?devEl.value:"";
    const val=id=>{const el=$(id);return el?el.value:"";};
    return{
      endpoint:val("#asrEndpoint"),
      model:val("#asrModel")||"whisper-1",
      api_key:val("#asrKey"),
      language:$("#asrLang")?$("#asrLang").value:"",
      device:devVal,
      sensitivity:Number(($("#asrSensitivity")||{}).value)||0,
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
    applyState(r);
    toast("Voice logging "+(next?"enabled.":"disabled."));
  });
  const asrShow=$("#asrShow");
  if(asrShow) asrShow.addEventListener("click",()=>{const k=$("#asrKey");if(!k)return;k.type=k.type==="password"?"text":"password";asrShow.textContent=k.type==="password"?"Show":"Hide";});
  const asrSaveBtn=$("#asrSave");
  if(asrSaveBtn) asrSaveBtn.addEventListener("click",async()=>{
    const cfg=asrCfgFromForm();cfg.enabled=asrSw?asrSw.classList.contains("on"):false;
    const r=await api.save_asr(cfg);
    if(r&&r.error)return toast(r.error,"err");
    applyState(r);toast("Voice logging settings saved.");
  });
  // --- always-on voice ---
  function vcCfgFromForm(){
    return {
      always_on:$("#vcSw")?$("#vcSw").classList.contains("on"):true,
      commands:$("#vcCmdSw")?$("#vcCmdSw").classList.contains("on"):true,
      hotkeys:$("#vcHkSw")?$("#vcHkSw").classList.contains("on"):true,
      keys:{
        log:($("#vcKeyLog")||{}).value||"S",
        finish:($("#vcKeyFinish")||{}).value||"F",
        session:($("#vcKeySession")||{}).value||"N",
        tab:($("#vcKeyTab")||{}).value||"T",
      },
    };
  }
  async function vcApply(cfg){
    let r;
    try{r=await api.save_voice(cfg);}catch(e){r={error:"Bridge not ready."};}
    if(r&&r.error)return toast(r.error,"err");
    // save_voice answers with the live registration report, so a key that is
    // held by another app says so here instead of failing silently later.
    state.voiceHotkeys=r.hotkeys||[];
    state.voiceGrammar=r.grammar||state.voiceGrammar;
    const el=$("#vcHkStatus");
    if(el){
      el.innerHTML=(r.hotkeys||[]).map(h=>esc(h.combo)+" &rarr; "+esc(h.command)+
        (h.registered?"":" <b class='taken'>(taken)</b>")).join(" &middot; ")
        ||"Not registered.";
    }
    const taken=(r.hotkeys||[]).filter(h=>!h.registered);
    if(taken.length)toast(taken.length+" hotkey(s) are held by another app.","err");
    return r;
  }
  ["vcSw","vcCmdSw","vcHkSw"].forEach(id=>{
    const sw=$("#"+id);
    if(!sw)return;
    sw.addEventListener("click",async()=>{
      const next=!sw.classList.contains("on");
      sw.classList.toggle("on",next);sw.setAttribute("aria-checked",next?"true":"false");
      const r=await vcApply(vcCfgFromForm());
      if(!r||r.error){sw.classList.toggle("on",!next);
                      sw.setAttribute("aria-checked",!next?"true":"false");}
    });
  });
  const vcSaveBtn=$("#vcSave");
  if(vcSaveBtn) vcSaveBtn.addEventListener("click",async()=>{
    const r=await vcApply(vcCfgFromForm());
    if(r&&!r.error)toast("Voice settings saved.");
  });

  function jdCfgFromForm(){
    return {enabled:$("#jdSw")?$("#jdSw").classList.contains("on"):false,
            model:$("#jdModel")?$("#jdModel").value.trim():"",
            base_url:$("#jdBase")?$("#jdBase").value.trim():"",
            api_key:$("#jdKey")?$("#jdKey").value:"",
            notes:$("#jdNotesSw")?$("#jdNotesSw").classList.contains("on"):true,
            kinds:$("#jdKindsSw")?$("#jdKindsSw").classList.contains("on"):true};
  }
  ["jdSw","jdNotesSw","jdKindsSw"].forEach(id=>{
    const sw=$("#"+id);
    if(!sw)return;
    sw.addEventListener("click",async()=>{
      const next=!sw.classList.contains("on");
      sw.classList.toggle("on",next);sw.setAttribute("aria-checked",next?"true":"false");
      const r=await api.save_judge(jdCfgFromForm());
      if(!r||r.error){sw.classList.toggle("on",!next);
                      sw.setAttribute("aria-checked",!next?"true":"false");}
      else applyState(r);
    });
  });
  const jdSaveBtn=$("#jdSave");
  if(jdSaveBtn) jdSaveBtn.addEventListener("click",async()=>{
    const r=await api.save_judge(jdCfgFromForm());
    if(r&&r.error)toast(r.error,"err");
    else{applyState(r);toast("Second-opinion settings saved.");}
  });
  const jdTestBtn=$("#jdTest");
  if(jdTestBtn) jdTestBtn.addEventListener("click",async()=>{
    const out=$("#jdTestOut");if(out)out.textContent="Asking…";
    await api.save_judge(jdCfgFromForm());
    let r;
    try{r=await api.test_judge();}catch(e){r={error:"Bridge not ready."};}
    if(r&&r.error){if(out)out.textContent="";toast(r.error,"err");return;}
    // The probe asks whether "the audit has been completed" says what "the
    // audit is not finished yet" says. Anything but `altered` means the
    // service answered but not sensibly, and that is worth seeing.
    if(out)out.textContent=r.model+" · "+r.choice+" @ "+r.confidence+
      (r.choice==="altered"?" ✓":" (unexpected)");
  });

  const asrTestBtn=$("#asrTest");
  if(asrTestBtn) asrTestBtn.addEventListener("click",async()=>{
    const out=$("#asrTestOut");if(out)out.textContent="Testing…";
    const r=await api.test_asr(5);
    if(r&&r.error){if(out)out.textContent="";toast(r.error,"err");}
    else if(out)out.textContent=(r&&r.text)?r.text:"(no speech detected)";
  });

  // --- the microphone test ---
  async function startMicTest(){
    const devEl=$("#asrDevice"),dev=devEl?devEl.value:"";
    const o=$("#mtOut");if(o)o.textContent="Opening the microphone…";
    let r;
    try{r=await api.mic_test_start(dev,Number(($("#asrSensitivity")||{}).value||50));}
    catch(e){r={error:"Bridge not ready."};}
    if(!r||r.error){micTestOn=false;micNote="";renderMain();
      const o2=$("#mtOut");if(o2)o2.textContent=(r&&r.error)||"Could not open the microphone.";return;}
    micRec=null;micTestOn=true;micHadRecording=!r.shared;
    const saved=String(((state.config||{}).asr||{}).device||"");
    micNote=r.shared?"Voice is on, so this is the live microphone at the saved sensitivity."
      :(r.note||"Speak - up to 10 seconds are recorded, then press Play to hear it.")+
       (dev!==saved?" Press Save settings to use this microphone.":"");
    renderMain();micLoop();
  }
  const mtBtn=$("#mtBtn");
  if(mtBtn) mtBtn.addEventListener("click",()=>{
    if(micTestOn){stopMic();micNote="";renderMain();return;}
    startMicTest();
  });
  // Manual re-check: deterministic answer to "I just plugged my headset in".
  // Same painter as the background poller, plus a toast with the count.
  const mtRefresh=$("#mtRefresh");
  if(mtRefresh) mtRefresh.addEventListener("click",async()=>{
    mtRefresh.disabled=true;
    try{
      const list=await refreshMicList();
      if(list)toast(list.length+(list.length===1?" microphone":" microphones")+" found.");
    }catch(e){toast("Could not re-check microphones.","err");}
    mtRefresh.disabled=false;
  });
  // Sensitivity applies live to the running test - no restart, no lost wave.
  const sensEl=$("#asrSensitivity");
  if(sensEl){
    let sensTimer=null;
    const pushSens=()=>{if(!(micTestOn||micRec))return;
      try{Promise.resolve(api.mic_test_sensitivity(Number(sensEl.value)||0)).catch(()=>{});}catch(e){}};
    sensEl.addEventListener("input",()=>{clearTimeout(sensTimer);sensTimer=setTimeout(pushSens,150);});
    sensEl.addEventListener("change",()=>{clearTimeout(sensTimer);pushSens();});
  }
  // The dropdown is disabled while a test runs; this restart is only a
  // safety net for anything that changes it programmatically meanwhile.
  const devSel=$("#asrDevice");
  if(devSel) devSel.addEventListener("change",()=>{if(micTestOn)startMicTest();});
  const mtPlay=$("#mtPlay");
  if(mtPlay) mtPlay.addEventListener("click",async()=>{
    mtPlay.disabled=true;
    let r;try{r=await api.mic_test_play();}catch(e){r={error:"Bridge not ready."};}
    if(!r||r.error){mtPlay.disabled=false;toast((r&&r.error)||"Could not play it.","err");return;}
    setTimeout(()=>{const b=$("#mtPlay");if(b)b.disabled=false;},
      Math.max(500,Number(r.seconds||0)*1000+300));
  });

  // --- only my voice ---
  const spkDl=$("#spkDl");
  if(spkDl) spkDl.addEventListener("click",async()=>{
    spkDl.disabled=true;
    const o=$("#spkOut");if(o)o.textContent="Downloading…";
    let r;try{r=await api.speaker_download();}catch(e){r={error:"Bridge not ready."};}
    if(!r||r.error){spkDl.disabled=false;spkNote=(r&&r.error)||"Download failed.";
      const o2=$("#spkOut");if(o2)o2.textContent=spkNote;return;}
    spkNote="";state.speakerInfo=r;renderMain();toast("Voice model downloaded and verified.");
  });
  const spkRec=$("#spkRec");
  if(spkRec) spkRec.addEventListener("click",async()=>{
    if(micRec==="enroll"){
      micRec=null;clearTimeout(micTimer);
      let r;try{r=await api.speaker_record_stop();}catch(e){r={error:"Bridge not ready."};}
      spkNote=(r&&r.error)?r.error:("Kept "+r.seconds+" s of speech.");
      if(r&&r.error)toast(r.error,"err");
      await refreshSpeaker();return;
    }
    micTestOn=false;
    let r;try{r=await api.speaker_record_start();}catch(e){r={error:"Bridge not ready."};}
    if(!r||r.error){toast((r&&r.error)||"Could not open the microphone.","err");return;}
    micRec="enroll";spkNote="Recording - read the sentence, then press Stop.";renderMain();micLoop();
  });
  const spkSave=$("#spkSave");
  if(spkSave) spkSave.addEventListener("click",async()=>{
    spkSave.disabled=true;
    let r;try{r=await api.speaker_enroll_finish();}catch(e){r={error:"Bridge not ready."};}
    if(!r||r.error){spkSave.disabled=false;toast((r&&r.error)||"Could not save the voiceprint.","err");
      spkNote=(r&&r.error)||"";await refreshSpeaker();return;}
    spkRedo=false;spkNote="Saved. From now on only your voice is transcribed.";
    state.speakerInfo=r;renderMain();toast("Voiceprint saved - the check is on.");
  });
  const spkReset=$("#spkReset");
  if(spkReset) spkReset.addEventListener("click",async()=>{
    if(micRec)stopMic();spkNote="";
    try{const r=await api.speaker_enroll_reset();if(r&&!r.error)state.speakerInfo=r;}catch(e){}
    renderMain();
  });
  const spkCancel=$("#spkCancel");
  if(spkCancel) spkCancel.addEventListener("click",async()=>{
    if(micRec)stopMic();spkRedo=false;spkNote="";
    try{const r=await api.speaker_enroll_reset();if(r&&!r.error)state.speakerInfo=r;}catch(e){}
    renderMain();
  });
  const spkRedoBtn=$("#spkRedoBtn");
  if(spkRedoBtn) spkRedoBtn.addEventListener("click",async()=>{
    spkRedo=true;spkNote="The old voiceprint stays in use until you save the new one.";
    try{const r=await api.speaker_enroll_reset();if(r&&!r.error)state.speakerInfo=r;}catch(e){}
    renderMain();
  });
  const spkForget=$("#spkForget");
  if(spkForget) spkForget.addEventListener("click",async()=>{
    if(!await tmConfirm("The check turns off, and every voice is transcribed again.",{title:"Forget your voiceprint?",okText:"Forget",danger:true}))return;
    let r;try{r=await api.speaker_save({forget:true});}catch(e){r={error:"Bridge not ready."};}
    if(!r||r.error)return toast((r&&r.error)||"Could not forget it.","err");
    spkNote="";state.speakerInfo=r;renderMain();toast("Voiceprint forgotten.");
  });
  const spkSw=$("#spkSw");
  if(spkSw) spkSw.addEventListener("click",async()=>{
    const next=!spkSw.classList.contains("on");
    let r;try{r=await api.speaker_save({enabled:next});}catch(e){r={error:"Bridge not ready."};}
    if(!r||r.error)return toast((r&&r.error)||"Could not change it.","err");
    state.speakerInfo=r;renderMain();
    toast(next?"Only your voice is transcribed.":"Every voice is transcribed again.");
  });
  const spkTh=$("#spkTh");
  if(spkTh){
    spkTh.addEventListener("input",()=>{const o=$("#spkThOut");if(o)o.textContent=(spkTh.value/100).toFixed(2);});
    spkTh.addEventListener("change",async()=>{
      let r;try{r=await api.speaker_save({threshold:Number(spkTh.value)/100});}catch(e){r={error:"Bridge not ready."};}
      if(!r||r.error)return toast((r&&r.error)||"Could not save it.","err");
      state.speakerInfo=r;
    });
  }
  const spkChk=$("#spkChk");
  if(spkChk) spkChk.addEventListener("click",async()=>{
    if(micRec==="check"){
      micRec=null;clearTimeout(micTimer);
      let r1;try{r1=await api.speaker_record_stop();}catch(e){r1={error:"Bridge not ready."};}
      if(!r1||r1.error){spkNote=(r1&&r1.error)||"Nothing recorded.";await refreshSpeaker();return;}
      let r;try{r=await api.speaker_check();}catch(e){r={error:"Bridge not ready."};}
      spkNote=(!r||r.error)?((r&&r.error)||"Could not score it.")
        :("Match "+r.score.toFixed(2)+" against a line of "+Number(r.threshold).toFixed(2)+" - "+
          (r.match?"let through.":"this would be held aside."));
      await refreshSpeaker();return;
    }
    micTestOn=false;
    let r;try{r=await api.speaker_record_start();}catch(e){r={error:"Bridge not ready."};}
    if(!r||r.error){toast((r&&r.error)||"Could not open the microphone.","err");return;}
    micRec="check";spkNote="Recording - say a sentence or two, then press Stop.";renderMain();micLoop();
  });
  document.querySelectorAll("[data-held-use]").forEach(b=>b.addEventListener("click",async()=>{
    b.disabled=true;
    let r;try{r=await api.held_use(Number(b.dataset.heldUse));}catch(e){r={error:"Bridge not ready."};}
    if(!r||r.error){b.disabled=false;toast((r&&r.error)||"Could not use it.","err");return;}
    toast(r.text?"Added to the draft.":"Nothing was said in that clip.");
    await refreshSpeaker();
  }));
  document.querySelectorAll("[data-held-drop]").forEach(b=>b.addEventListener("click",async()=>{
    try{await api.held_drop(Number(b.dataset.heldDrop));}catch(e){}
    await refreshSpeaker();
  }));
  const heldDropAll=$("#heldDropAll");
  if(heldDropAll) heldDropAll.addEventListener("click",async()=>{
    try{await api.held_drop(null);}catch(e){}
    await refreshSpeaker();
  });

  // --- Telegram bridge ---
  const tgSw=$("#tgSw");
  if(tgSw) tgSw.addEventListener("click",async()=>{
    const next=!tgSw.classList.contains("on");
    tgSw.classList.toggle("on",next);tgSw.setAttribute("aria-checked",next?"true":"false");
    const r=await api.save_telegram({enabled:next});
    if(r&&r.error){
      toast(r.error,"err");
      tgSw.classList.toggle("on",!next);tgSw.setAttribute("aria-checked",!next?"true":"false");
      return;
    }
    applyState(r);
    toast("Telegram bridge "+(next?"enabled.":"disabled."));
  });
  const tgSaveBtn=$("#tgSave");
  if(tgSaveBtn) tgSaveBtn.addEventListener("click",async()=>{
    const sw=$("#tgSw");
    const cfg={enabled:sw?sw.classList.contains("on"):false};
    const tokenEl=$("#tgToken");
    const tokenVal=tokenEl?tokenEl.value.trim():"";
    if(tokenVal!=="") cfg.token=tokenVal;
    const r=await api.save_telegram(cfg);
    if(r&&r.error)return toast(r.error,"err");
    applyState(r);if(tokenEl)tokenEl.value="";renderMain();toast("Telegram settings saved.");
  });
  const tgCopyCodeBtn=$("#tgCopyCode");
  if(tgCopyCodeBtn) tgCopyCodeBtn.addEventListener("click",()=>{
    const codeEl=$("#tgPairCode");
    const code=(codeEl?codeEl.textContent:"").trim();
    if(!code){toast("No pairing code available.","err");return;}
    copyText(code);
  });
  const tgRegenCodeBtn=$("#tgRegenCode");
  if(tgRegenCodeBtn) tgRegenCodeBtn.addEventListener("click",async()=>{
    const r=await api.telegram_regenerate_code();
    if(r&&r.error)return toast(r.error,"err");
    applyState(r);renderMain();toast("New pairing code generated.");
  });
  const tgUnpairBtn=$("#tgUnpair");
  if(tgUnpairBtn) tgUnpairBtn.addEventListener("click",async()=>{
    if(!await tmConfirm("You will need a new pairing code to reconnect.",{title:"Unpair this Telegram account?",okText:"Unpair",danger:true}))return;
    const r=await api.telegram_unpair();
    if(r&&r.error)return toast(r.error,"err");
    applyState(r);renderMain();toast("Telegram account unpaired.");
  });

  // --- scientific mode ---
  const sciStyle=$("#sciStyle");
  if(sciStyle){
    sciStyle.addEventListener("change",()=>{
      const x=CITE_STYLES.find(y=>y.id===sciStyle.value);
      const h=$("#sciHint");if(h)h.textContent=x?x.hint:"";
    });
    const sciSave=$("#sciSave");
    if(sciSave) sciSave.addEventListener("click",async()=>{
      const onEl=$("#sciOn"),sepEl=$("#sciSep"),reqEl=$("#sciReq");
      const r=await api.save_science({
        enabled:onEl?onEl.checked:false,
        style:sciStyle.value,
        separate_notes:sepEl?sepEl.checked:true,
        require_source_for_claims:reqEl?reqEl.checked:false,
      });
      if(r&&r.error)return toast(r.error,"err");
      applyState(r);renderMain();
      toast(onEl&&onEl.checked?"Scientific mode on.":"Scientific mode off.");
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
    if(r&&!r.error) applyState(r);
  });

  // --- export defaults (Templates panel) ---
  const xf=$("#xTpl");
  if(xf){
    document.querySelectorAll("[data-xfmt]").forEach(cb=>cb.addEventListener("change",()=>{
      const box=cb.closest(".fmt-opt");if(box)box.classList.toggle("on",cb.checked);
    }));
    const xSave=$("#xSave");
    if(xSave) xSave.addEventListener("click",async()=>{
      const formats=[...document.querySelectorAll("[data-xfmt]")].filter(c=>c.checked).map(c=>c.dataset.xfmt);
      if(!formats.length) return toast("Pick at least one default format.","err");
      const tplEl=$("#xTpl"),auEl=$("#xAuthor"),orgEl=$("#xOrg");
      const r=await api.save_export({template:tplEl?tplEl.value:"",formats,
        author:auEl?auEl.value:"",org:orgEl?orgEl.value:""});
      if(r&&r.error)return toast(r.error,"err");
      applyState(r); toast("Export defaults saved.");
    });
    const xFolder=$("#xFolder");
    if(xFolder) xFolder.addEventListener("click",async()=>{
      const r=await api.open_template_dir();
      if(r&&r.error)return toast(r.error,"err");
      toast("Opened "+((r&&r.path)||"templates folder"));
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

  // --- templates manager: gallery preview + use-for-category ---
  bindTplManager();
}

function bindTplManager(){
  document.querySelectorAll("[data-tplmgr-preview]").forEach(b=>b.addEventListener("click",async e=>{
    e.stopPropagation();
    const id=b.dataset.tplmgrPreview;
    if(tplMgrPreview===id){tplMgrPreview=null;tplMgrHtml=null;tplMgrError=null;renderMain();return;}
    tplMgrPreview=id;tplMgrHtml=null;tplMgrError=null;tplMgrLoading=true;renderMain();
    paintTplMgrFrame();
    let r;
    try{r=await api.template_demo(id);}catch(err){r={error:"Bridge not ready."};}
    if(tplMgrPreview!==id) return;
    tplMgrLoading=false;
    if(r&&r.error)tplMgrError=r.error; else tplMgrHtml=(r&&r.html)||"";
    if(tab==="settings"&&settingsSub==="templates")renderMain();
    paintTplMgrFrame();
  }));
  document.querySelectorAll('[data-tplmgr]').forEach(card=>card.addEventListener("click",e=>{
    if(e.target.closest("[data-tplmgr-preview],[data-tplmgr-use]"))return;
    const id=card.dataset.tplmgr;
    const btn=card.querySelector('[data-tplmgr-preview]');
    if(btn)btn.click();
  }));
  document.querySelectorAll("[data-tplmgr-use]").forEach(b=>b.addEventListener("click",async e=>{
    e.stopPropagation();
    const tplId=b.dataset.tplmgrUse;
    const tp=(state.templates||[]).find(x=>x.id===tplId);
    if(!tp){toast("Template not found.","err");return;}
    const catId=tp.category||((state.categories||[])[0]||{}).id;
    if(!catId){toast("No category to attach it to.","err");return;}
    const r=await api.set_category_default(catId,tplId);
    if(r&&r.error)return toast(r.error,"err");
    applyState(r);renderMain();toast("Default template updated.");
  }));
  const closeBtn=$("#tplMgrClose");
  if(closeBtn)closeBtn.addEventListener("click",()=>{
    tplMgrPreview=null;tplMgrHtml=null;tplMgrError=null;renderMain();
  });
  paintTplMgrFrame();
}
function paintTplMgrFrame(){
  const f=$("#tplMgrFrame");
  if(f&&tplMgrHtml) f.srcdoc=tplMgrHtml;
}

function bindCategories(){
  const mgr=$(".cat-mgr");
  if(!mgr) return;

  mgr.querySelectorAll(".cat-row").forEach(row=>{
    const id=row.dataset.catRow;
    const defEl=row.querySelector(".cat-def-tpl");
    if(defEl) defEl.addEventListener("change",async e=>{
      const r=await api.set_category_default(id, e.target.value);
      if(r&&r.error) return toast(r.error,"err");
      applyState(r); renderMain(); toast("Default template updated.");
    });
    const renBtn=row.querySelector(".cat-rename");
    if(renBtn) renBtn.addEventListener("click",async()=>{
      const name=(row.querySelector(".cat-name").value||"").trim();
      if(!name) return toast("Name the category first.","err");
      const r=await api.save_category({id, name});
      if(r&&r.error) return toast(r.error,"err");
      applyState(r); renderMain(); toast("Category renamed.");
    });
    const delBtn=row.querySelector(".cat-delete");
    if(delBtn) delBtn.addEventListener("click",async()=>{
      if(!await tmConfirm("Its templates keep working, but stop suggesting a default here.",{title:"Delete this category?",okText:"Delete",danger:true})) return;
      const r=await api.delete_category(id);
      if(r&&r.error) return toast(r.error,"err");
      applyState(r); renderMain(); toast("Category deleted.");
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
    const nameEl=mgr.querySelector("#sCatName"),defEl=mgr.querySelector("#sCatDefTpl");
    const name=((nameEl&&nameEl.value)||"").trim();
    const defTpl=defEl?defEl.value:"";
    if(!name) return toast("Name the category first.","err");
    if(!defTpl) return toast("Pick a default template.","err");
    const r=await api.save_category({name, default_template:defTpl});
    if(r&&r.error) return toast(r.error,"err");
    applyState(r); catNewOpen=false; renderMain();
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
  if(r&&!r.error)applyState(r);
  render();
});

function refreshFromBridge(){
  api.get_state().then(r=>{
    if(!r||r.error)return;
    // Background pushes (voice log, telegram message, the save we just did
    // ourselves via refresh_full) must never wipe a settings form mid-edit.
    // While typing, merge state silently and refresh only chrome (topbar +
    // sidebar); the form re-renders on the next save or panel switch.
    if(tab==="settings"&&isTypingInSettings()){applyState(r);renderTopbar();renderSide();return;}
    const main=$("#main");
    const st=main?main.scrollTop:0;
    const ae=document.activeElement, aid=ae&&ae.id?ae.id:null;
    applyState(r);render();
    try{
      const m2=$("#main");if(m2&&typeof st==="number")m2.scrollTop=st;
      if(aid){const el=document.getElementById(aid);if(el&&el.focus)el.focus({preventScroll:true});}
    }catch(e){}
  }).catch(()=>{});
}

async function init(){
  applyState(await api.get_state());
  applyTheme(((state.config||{}).appearance||{}).theme||"system");
  // the list of citation styles lives in citation.py; the UI asks for it rather
  // than keeping a second copy that can drift
  try{const cs=await api.citation_styles(); if(cs&&cs.styles&&cs.styles.length)CITE_STYLES=cs.styles;}catch(e){}
  render();
}
if(window.pywebview){init();}else{window.addEventListener("pywebviewready",init);}

// --- Persian half-space -----------------------------------------------------
// Ctrl+Shift+Space inserts ZWNJ (U+200C). Windows has no key for it, and
// Persian needs it constantly: "\u0645\u06cc \u0634\u0648\u062f" and
// "\u0645\u06cc\u200c\u0634\u0648\u062f" are different words and look
// identical in most editors. Without a key, people type the wrong one - which
// is the single most common defect in Persian text entered on a machine that
// did not expect it.
function zwnjKey(e){
  if(!(e.ctrlKey&&e.shiftKey&&(e.code==="Space"||e.key===" ")))return;
  const el=e.target;
  if(!el||!("selectionStart" in el)||el.selectionStart===null)return;
  e.preventDefault();
  const a=el.selectionStart,b=el.selectionEnd,v=el.value;
  el.value=v.slice(0,a)+"\u200c"+v.slice(b);
  el.selectionStart=el.selectionEnd=a+1;
  el.dispatchEvent(new Event("input",{bubbles:true}));
}
document.addEventListener("keydown",zwnjKey,true);
</script></body></html>
"""

POPUP_HTML = POPUP_HTML.replace("__BASE_CSS__", BASE_CSS)
MAIN_HTML = MAIN_HTML.replace("__BASE_CSS__", BASE_CSS)
