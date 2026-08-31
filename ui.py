BASE_CSS = """
:root{
  --bg1:#0b0f16; --bg2:#141b26;
  --glass:rgba(255,255,255,.06);
  --glass-hi:rgba(255,255,255,.10);
  --stroke:rgba(255,255,255,.14);
  --stroke-hi:rgba(255,255,255,.26);
  --text:#eef1f6; --muted:#94a0b2;
  --accent:#f0a94a; --accent-dim:#c97f2d; --accent-deep:#9a5f1f;
  --teal:#4fd8c8; --danger:#ff6b6b; --ok:#7bd88f;
  --radius:18px;
}
*{box-sizing:border-box}
[hidden]{display:none !important}
html,body{height:100%;margin:0}
body{
  font-family:"Segoe UI Variable","Segoe UI",system-ui,-apple-system,sans-serif;
  color:var(--text);
  background:
    radial-gradient(900px 620px at 90% -10%, rgba(240,169,74,.20), transparent 60%),
    radial-gradient(800px 600px at -8% 110%, rgba(79,216,200,.16), transparent 58%),
    radial-gradient(600px 460px at 55% 50%, rgba(240,169,74,.06), transparent 60%),
    linear-gradient(158deg,var(--bg1),var(--bg2));
  overflow:hidden;
  -webkit-font-smoothing:antialiased;
}
.glass{
  background:var(--glass);
  backdrop-filter:blur(22px) saturate(150%);
  -webkit-backdrop-filter:blur(22px) saturate(150%);
  border:1px solid var(--stroke);
  border-radius:var(--radius);
  box-shadow:0 12px 38px rgba(0,0,0,.4), inset 0 1px 0 rgba(255,255,255,.08);
}
::-webkit-scrollbar{width:9px;height:9px}
::-webkit-scrollbar-thumb{background:rgba(255,255,255,.14);border-radius:9px}
::-webkit-scrollbar-track{background:transparent}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:7px;border:0;border-radius:12px;
  padding:10px 15px;font-family:inherit;font-size:13.5px;font-weight:600;cursor:pointer;transition:.16s;
  color:var(--text);background:rgba(255,255,255,.08);box-shadow:inset 0 1px 0 rgba(255,255,255,.09)}
.btn:hover{background:rgba(255,255,255,.14);transform:translateY(-1px)}
.btn:active{transform:translateY(0)}
.btn.primary{background:linear-gradient(180deg,rgba(240,169,74,.9),rgba(201,127,45,.95));
  box-shadow:0 6px 18px rgba(201,127,45,.32), inset 0 1px 0 rgba(255,255,255,.28);color:#201407}
.btn.primary:hover{filter:brightness(1.07)}
.btn.ghost{background:transparent;border:1px solid var(--stroke)}
.btn.danger{background:rgba(255,107,107,.15);border:1px solid rgba(255,107,107,.38)}
.btn.danger:hover{background:rgba(255,107,107,.26)}
.btn.sm{padding:6px 11px;font-size:12.5px;border-radius:10px}
.btn.full{width:100%}
.input{width:100%;background:rgba(255,255,255,.055);border:1px solid var(--stroke);border-radius:11px;
  padding:10px 12px;color:var(--text);font-family:inherit;font-size:13.5px;outline:none;transition:.15s;color-scheme:dark}
.input:focus{border-color:var(--stroke-hi);box-shadow:0 0 0 3px rgba(240,169,74,.18)}
.ta{resize:vertical;line-height:1.5}
label{display:flex;flex-direction:column;gap:5px;font-size:11.5px;font-weight:600;color:var(--muted);letter-spacing:.02em}
label .input{font-weight:400}
.chip{padding:6px 11px;border:1px solid var(--stroke);border-radius:11px;background:rgba(255,255,255,.04);
  color:var(--muted);font-family:inherit;font-size:12.5px;font-weight:600;cursor:pointer;transition:.15s;white-space:nowrap}
.chip:hover{color:var(--text)}
.chip.active{background:rgba(240,169,74,.16);color:var(--text);border-color:rgba(240,169,74,.45)}
.chip.accent{background:rgba(240,169,74,.12);border-color:rgba(240,169,74,.35);color:#ffd9a8}
.chips{display:flex;gap:6px;flex-wrap:wrap;align-items:center}
.muted{color:var(--muted);font-size:12.5px;line-height:1.5}
#toasts{position:fixed;bottom:18px;left:50%;transform:translateX(-50%);display:flex;flex-direction:column;
  gap:8px;z-index:80;align-items:center;pointer-events:none}
.toast{padding:9px 15px;border-radius:12px;background:rgba(18,24,33,.8);border:1px solid var(--stroke-hi);
  backdrop-filter:blur(16px);color:var(--text);font-size:12.5px;box-shadow:0 8px 26px rgba(0,0,0,.45);
  transition:.3s;max-width:340px}
.toast.err{border-color:rgba(255,107,107,.5);color:#ffd9d9}
.toast.out{opacity:0;transform:translateY(8px)}
.fade{animation:fade .2s ease}
@keyframes fade{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
"""

POPUP_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Trailmark · Quick capture</title><style>
__BASE_CSS__
body{user-select:none}
.win{display:flex;flex-direction:column;height:100vh;padding:12px;gap:10px}
header{display:flex;align-items:center;gap:9px;padding:9px 12px}
header img{width:30px;height:30px;border-radius:9px;object-fit:cover;border:1px solid rgba(255,255,255,.2);
  box-shadow:0 4px 14px rgba(0,0,0,.35)}
.tt{min-width:0;flex:1}
.app{font-weight:650;font-size:13.5px;letter-spacing:.2px}
.hk{font-size:10.5px;color:var(--muted)}
.pulse{flex:none;width:9px;height:9px;border-radius:50%;background:var(--accent);
  box-shadow:0 0 0 5px rgba(240,169,74,.12);animation:pulse 2s ease-in-out infinite}
@keyframes pulse{0%,100%{opacity:1;box-shadow:0 0 0 5px rgba(240,169,74,.12)}50%{opacity:.6;box-shadow:0 0 0 9px rgba(240,169,74,0)}}
section{overflow-y:auto;flex:1}
.card{padding:14px;display:flex;flex-direction:column;gap:9px}
.big{font-size:17px;font-weight:700}
.trow{display:flex;gap:8px;align-items:center}
.srcbar{display:flex;gap:7px}
.attrow{display:flex;gap:7px;align-items:center;flex-wrap:wrap}
.logrow{display:flex;gap:9px;margin-top:2px}
.logrow .btn.primary{flex:1}
.hint{font-size:10.5px;color:var(--muted);text-align:center;letter-spacing:.03em}
.recent{font-size:11.5px;color:var(--muted);border-top:1px solid var(--stroke);padding-top:8px;margin-top:2px}
.recent b{color:var(--text);font-weight:600}
</style></head><body>
<div class="win">
  <header class="glass">
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
      <label>Point</label>
      <textarea id="ptText" class="input ta" rows="3" placeholder="Type or paste the point…" spellcheck="false"></textarea>
      <div class="srcbar">
        <input id="ptLink" class="input grow" placeholder="Paste a source link…">
        <button id="ptLinkAdd" class="chip">+ Link</button>
      </div>
      <div class="srcbar">
        <input id="ptStr" class="input grow" placeholder="Or a string citation…">
        <button id="ptStrAdd" class="chip">+ String</button>
      </div>
      <div class="attrow">
        <label class="chip">+ Screenshot<input id="ptShot" type="file" accept="image/*" hidden></label>
        <div id="attChips" class="chips"></div>
      </div>
      <div class="logrow">
        <button id="ptGo" class="btn primary">Log point</button>
        <button id="ptHide" class="btn ghost">Hide</button>
      </div>
      <div class="hint">Enter logs · Esc hides · hotkey toggles · Open app to review</div>
      <div class="recent" id="recent"></div>
    </div>
  </section>
</div>
<div id="toasts"></div>
<script>
let state={topics:[]};
let topicId=null, subTopic="";
let pLink="", pString="", pImage=null;
let lastTopicId=null;
const api=new Proxy({},{get:(_,p)=>{const pv=window.pywebview&&window.pywebview.api;return pv?pv[p]:(()=>Promise.resolve({error:"bridge not ready"}));}});

const $=(s,r=document)=>r.querySelector(s);
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const toast=(m,t="ok")=>{const d=document.createElement("div");d.className="toast "+t;d.textContent=m;
  document.getElementById("toasts").appendChild(d);setTimeout(()=>d.classList.add("out"),2200);setTimeout(()=>d.remove(),2600);};
const byId=i=>state.topics.find(t=>t.id===i);
const openTopics=()=>state.topics.filter(t=>t.status==="open");
const fmtTime=iso=>{if(!iso)return"";const d=new Date(iso);return d.toLocaleString(undefined,{day:"2-digit",month:"short",hour:"2-digit",minute:"2-digit"});};

function renderMode(){
  const opens=openTopics();
  const no=$("#noTopic"), log=$("#logPanel");
  if(!opens.length){
    no.hidden=false;log.hidden=true;return;
  }
  no.hidden=true;log.hidden=false;
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
  const r=await api.add_entry(topicId,subTopic,text,pLink,pString,pImage);
  if(r.error){toast(r.error,"err");return;}
  state=r;lastTopicId=topicId;
  $("#ptText").value="";$("#ptLink").value="";$("#ptStr").value="";pLink="";pString="";pImage=null;
  renderAtt();
  $("#recent").innerHTML="<b>Logged</b> · "+fmtTime(r.topics.find(t=>t.id===topicId).entries.at(-1).created)+
    (subTopic?" · "+esc(subTopic):"");
  toast("Point logged.");
  $("#ptText").focus();
}

function renderAtt(){
  const wrap=$("#attChips");const parts=[];
  if(pLink)parts.push(`<span class="chip active">link</span>`);
  if(pString)parts.push(`<span class="chip active">string</span>`);
  if(pImage)parts.push(`<span class="chip active">shot</span>`);
  wrap.innerHTML=parts.join("")||`<span class="muted" style="font-size:11.5px">sources for this point appear here</span>`;
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
$("#ptLinkAdd").addEventListener("click",()=>{const v=$("#ptLink").value.trim();if(!v)return;pLink=v;$("#ptLink").value="";renderAtt();toast("Link added.");});
$("#ptStrAdd").addEventListener("click",()=>{const v=$("#ptStr").value.trim();if(!v)return;pString=v;$("#ptStr").value="";renderAtt();toast("Citation added.");});
$("#ptLink").addEventListener("keydown",e=>{if(e.key==="Enter")$("#ptLinkAdd").click();});
$("#ptStr").addEventListener("keydown",e=>{if(e.key==="Enter")$("#ptStrAdd").click();});
$("#ptShot").addEventListener("change",e=>{
  const f=e.target.files[0];if(!f)return;
  const rd=new FileReader();
  rd.onload=()=>{pImage=rd.result;renderAtt();toast("Screenshot attached.");};
  rd.readAsDataURL(f);e.target.value="";
});
$("#ptGo").addEventListener("click",logPoint);
$("#ptText").addEventListener("keydown",e=>{
  if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();logPoint();}
});
$("#openApp").addEventListener("click",()=>api.show_full());
$("#ptHide").addEventListener("click",()=>api.hide_popup());
document.addEventListener("keydown",e=>{if(e.key==="Escape")api.hide_popup();});
document.addEventListener("wheel",e=>{if(e.ctrlKey)e.preventDefault();},{passive:false});

function boot(){
  api.get_state().then(r=>{
    state=r;
    const cfg=r.config||{};
    const mods=cfg.hotkey&&cfg.hotkey.modifiers||["ctrl","alt"];
    const key=cfg.hotkey&&cfg.hotkey.key||"P";
    $("#hkLabel").textContent=mods.map(m=>m[0].toUpperCase()+m.slice(1)).join("+")+"+"+key+" toggles";
    $("#liveDot").hidden=r.topics.filter(t=>t.status==="open").length===0;
    renderMode();
    setTimeout(()=>{const el=$("#ptText");if(el)el.focus();},150);
  });
}
function popupShown(){
  api.get_state().then(r=>{if(r&&!r.error){state=r;renderMode();}}).catch(()=>{});
  setTimeout(()=>{const el=$("#ptText");if(el)el.focus();},120);
}
if(window.pywebview){boot();}else{window.addEventListener("pywebviewready",boot);}
</script></body></html>
"""

MAIN_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Trailmark</title><style>
__BASE_CSS__
.app{display:grid;grid-template-columns:292px 1fr;gap:16px;height:100vh;padding:16px}
aside{display:flex;flex-direction:column;overflow:hidden}
.brand{display:flex;align-items:center;gap:10px;padding:16px 16px 8px}
.brand img{width:34px;height:34px;border-radius:10px;object-fit:cover;border:1px solid rgba(255,255,255,.22);
  box-shadow:0 4px 14px rgba(0,0,0,.4)}
.brand .bn{font-weight:700;font-size:14.5px;letter-spacing:.2px}
.brand .bt{font-size:10.5px;color:var(--muted)}
.segmented{display:flex;gap:4px;margin:10px 14px 6px;padding:4px;background:rgba(255,255,255,.05);
  border:1px solid var(--stroke);border-radius:13px}
.seg{flex:1;padding:8px 0;border:0;border-radius:10px;background:transparent;color:var(--muted);
  font-family:inherit;font-size:12.5px;font-weight:600;cursor:pointer;transition:.18s}
.seg:hover{color:var(--text)}
.seg.active{background:rgba(255,255,255,.14);color:var(--text);box-shadow:0 2px 10px rgba(0,0,0,.25), inset 0 1px 0 rgba(255,255,255,.12)}
.list{flex:1;overflow-y:auto;padding:8px;margin:2px 8px 8px}
.ti{display:flex;align-items:center;gap:10px;padding:11px 12px;border-radius:13px;cursor:pointer;
  border:1px solid transparent;transition:.16s}
.ti:hover{background:rgba(255,255,255,.06)}
.ti.sel{background:var(--glass-hi);border-color:var(--stroke-hi);box-shadow:0 4px 16px rgba(0,0,0,.28)}
.dot{flex:none;width:10px;height:10px;border-radius:50%;box-shadow:0 0 0 4px rgba(255,255,255,.05)}
.dot.open{background:var(--accent)}
.dot.closed{background:#5b6577}
.ti-b{min-width:0;flex:1}
.ti-t{font-size:13px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ti-s{font-size:11.5px;color:var(--muted);margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.empty{color:var(--muted);font-size:12.5px;text-align:center;padding:24px 10px}
.side-actions{padding:8px 14px 14px;display:flex;flex-direction:column;gap:8px}
main{overflow-y:auto;padding:22px}
.cards{display:flex;flex-direction:column;gap:15px;max-width:780px;margin:0 auto;padding-top:6px}
.card{padding:19px}
.card-h{display:flex;align-items:center;gap:9px;margin-bottom:6px}
.card-t{font-size:15.5px;font-weight:650}
.hero{border-color:rgba(240,169,74,.34);box-shadow:0 12px 38px rgba(0,0,0,.4), 0 0 0 1px rgba(240,169,74,.13), inset 0 1px 0 rgba(255,255,255,.1)}
.hero .orb{width:52px;height:52px;border-radius:50%;margin:0 auto 12px;
  background:radial-gradient(circle at 35% 30%, rgba(240,169,74,.95), rgba(154,95,31,.9));
  box-shadow:0 0 0 10px rgba(240,169,74,.08), 0 0 24px rgba(240,169,74,.32), inset 0 -6px 14px rgba(0,0,0,.25);
  animation:breathe 3s ease-in-out infinite}
@keyframes breathe{0%,100%{box-shadow:0 0 0 10px rgba(240,169,74,.08), 0 0 24px rgba(240,169,74,.32)}50%{box-shadow:0 0 0 16px rgba(240,169,74,.04), 0 0 40px rgba(240,169,74,.46)}}
.dhead{display:flex;align-items:center;gap:14px;margin-bottom:16px}
.dh-b{min-width:0;flex:1}
.dh-t{font-size:20px;font-weight:700;word-break:break-word}
.dh-s{color:var(--muted);font-size:12.5px;margin-top:3px}
.pill{display:inline-flex;align-items:center;gap:6px;padding:4px 10px;border-radius:999px;font-size:11px;
  font-weight:700;letter-spacing:.05em;text-transform:uppercase}
.pill.open{background:rgba(240,169,74,.15);color:#ffd9a8;border:1px solid rgba(240,169,74,.4)}
.pill.closed{background:rgba(91,101,119,.18);color:#b9c2d0;border:1px solid rgba(91,101,119,.4)}
.sub{padding:17px}
.composer{display:flex;flex-direction:column;gap:9px}
.entries{display:flex;flex-direction:column;gap:11px}
.entry{padding:15px}
.e-meta{display:flex;align-items:center;gap:8px;flex-wrap:wrap;font-size:11.5px;color:var(--muted);margin-bottom:7px}
.tag{font-size:10.5px;font-weight:700;letter-spacing:.05em;padding:2px 8px;border-radius:999px;
  background:rgba(79,216,200,.13);color:#8fe9dd;border:1px solid rgba(79,216,200,.3)}
.e-text{font-size:14px;line-height:1.6;white-space:pre-line;word-break:break-word}
.sources{display:flex;flex-direction:column;gap:6px;margin-top:11px;border-top:1px solid rgba(255,255,255,.07);padding-top:10px}
.src{display:flex;align-items:center;gap:8px;font-size:12.5px}
.src-link{display:inline-flex;align-items:center;gap:6px;max-width:100%;overflow:hidden;text-overflow:ellipsis;
  white-space:nowrap;padding:5px 10px;border-radius:9px;background:rgba(240,169,74,.1);
  border:1px solid rgba(240,169,74,.28);color:#ffd9a8;cursor:pointer}
.src-link:hover{background:rgba(240,169,74,.18)}
.src-str{display:inline-flex;align-items:center;gap:6px;font-style:italic;color:var(--muted);padding:5px 10px;
  border-radius:9px;background:rgba(255,255,255,.04);border:1px solid var(--stroke);cursor:pointer;max-width:100%}
.src-str span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.thumb{width:64px;height:64px;object-fit:cover;border-radius:9px;border:1px solid var(--stroke-hi);cursor:pointer}
.e-actions{display:flex;gap:7px;margin-top:10px;flex-wrap:wrap}
.edit{width:100%;display:flex;flex-direction:column;gap:9px}
.export-ok{display:flex;flex-direction:column;gap:9px;align-items:flex-start}
.path{font-family:Consolas,monospace;font-size:11.5px;color:var(--teal);background:rgba(255,255,255,.04);
  border:1px solid var(--stroke);border-radius:8px;padding:7px 10px;word-break:break-all;max-width:100%}
.set-card{display:flex;flex-direction:column;gap:11px}
.row{display:flex;gap:9px;align-items:flex-end;flex-wrap:wrap}
.grow{flex:1;min-width:0}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.grid3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px}
.mod{display:inline-flex;gap:6px;align-items:center}
.mod input{width:15px;height:15px;accent-color:var(--accent)}
.kkey{width:90px;text-align:center;text-transform:uppercase;letter-spacing:.1em}
.dim{color:var(--muted)}
.spacer{flex:1}
</style></head><body>
<div class="app">
  <aside class="glass">
    <div class="brand">
      <img src="__ICON__" alt="">
      <div><div class="bn">Trailmark</div><div class="bt">Log the point. Keep the source.</div></div>
    </div>
    <div class="segmented" id="seg">
      <button class="seg active" data-tab="open">Open</button>
      <button class="seg" data-tab="closed">Closed</button>
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
let state={topics:[],config:{},providers:{}};
let tab="open", sel=null, editEntry=null, filterSub=null, summaryDraft=null;
const api=new Proxy({},{get:(_,p)=>{const pv=window.pywebview&&window.pywebview.api;return pv?pv[p]:(()=>Promise.resolve({error:"bridge not ready"}));}});

const $=(s,r=document)=>r.querySelector(s);
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const toast=(m,t="ok")=>{const d=document.createElement("div");d.className="toast "+t;d.textContent=m;
  document.getElementById("toasts").appendChild(d);setTimeout(()=>d.classList.add("out"),2400);setTimeout(()=>d.remove(),2800);};
const byId=i=>state.topics.find(t=>t.id===i);
const escTop=s=>esc(s).replace(/\\n/g,"<br>");
function fmt(iso){if(!iso)return"—";const d=new Date(iso);return d.toLocaleString(undefined,{day:"2-digit",month:"short",year:"numeric",hour:"2-digit",minute:"2-digit"});}
function fmtT(iso){if(!iso)return"";const d=new Date(iso);return d.toLocaleTimeString(undefined,{hour:"2-digit",minute:"2-digit"});}
function copyText(t){navigator.clipboard&&navigator.clipboard.writeText(t).then(()=>toast("Copied."),()=>legacyCopy(t)).catch(()=>legacyCopy(t));}
function legacyCopy(t){const ta=document.createElement("textarea");ta.value=t;document.body.appendChild(ta);ta.select();
  try{document.execCommand("copy");toast("Copied.");}catch(e){toast("Copy failed.","err");}ta.remove();}

function render(){
  document.querySelectorAll("#seg .seg").forEach(b=>b.classList.toggle("active",b.dataset.tab===tab));
  if(sel&&!byId(sel))sel=null;
  renderSide();
  renderMain();
}

function renderSide(){
  const list=$("#sideList");
  if(tab==="settings"){list.innerHTML=`<div class="empty">AI assist, hotkey &amp; storage preferences.</div>`;return;}
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
  }).join("")||`<div class="empty">${open?"No open topics. Start one below.":"No closed topics yet."}</div>`;
  list.querySelectorAll(".ti").forEach(el=>el.addEventListener("click",()=>{sel=el.dataset.id;editEntry=null;filterSub=null;render();}));
}

function renderMain(){
  const main=$("#main");
  if(tab==="settings"){main.innerHTML=settingsHtml();bindSettings();return;}
  const t=sel?byId(sel):null;
  if(!t){main.innerHTML=newViewHtml();bindNew();return;}
  main.innerHTML=detailHtml(t);bindDetail(t);
}

function newViewHtml(){
  return `<div class="cards"><div class="card glass fade hero"><div class="orb"></div>
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

function detailHtml(t){
  const n=t.entries.length;
  const pill=t.status==="open"?`<span class="pill open">Open</span>`:`<span class="pill closed">Closed</span>`;
  const subs=(t.subtopics||[]).map(s=>`<button class="chip ${filterSub===s?"active":""}" data-s="${esc(s)}">${esc(s)}<span style="opacity:.5">×</span></button>`).join("");
  const subRow=subs||`<span class="muted">No sub-topics yet.</span>`;
  const acts=t.status==="open"
    ?`<button class="btn primary sm" id="tClose">Close &amp; export</button><button class="btn danger sm" id="tDel">Delete</button>`
    :`<button class="btn primary sm" id="tExp">Export report</button>${state.config.llm&&state.config.llm.enabled?`<button class="btn ghost sm" id="tDraft">Draft AI summary</button>`:""}<button class="btn ghost sm" id="tReopen">Reopen</button><button class="btn danger sm" id="tDel">Delete</button>`;
  const composer=t.status==="open"?`<div class="card sub glass composer">
    <div class="row"><select id="cSub" class="input grow"></select>
      <input id="cLink" class="input grow" placeholder="Source link…">
      <button class="chip" id="cLinkAdd">+ Link</button></div>
    <div class="row"><textarea id="cText" class="input ta grow" rows="2" placeholder="Type or paste the point…" spellcheck="false"></textarea>
      <button class="btn primary" id="cGo">Log point</button></div>
    <div class="row"><input id="cStr" class="input grow" placeholder="String citation…">
      <button class="chip" id="cStrAdd">+ String</button>
      <label class="chip">+ Screenshot<input id="cShot" type="file" accept="image/*" hidden></label>
      <div id="cAtt" class="chips"></div></div>
  </div>`:"";
  const entries=t.entries.slice().sort((a,b)=>a.created<b.created?1:-1);
  const shown=filterSub?entries.filter(e=>(e.subtopic||"")===filterSub):entries;
  const list=shown.map(e=>entryHtml(t,e)).join("")||`<div class="empty">No points logged yet.</div>`;
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
    <div class="card sub glass">
      <div class="row"><div class="muted grow">Closing the topic locks it and exports a clean, cited report (HTML + Markdown).</div>${acts}</div>
    </div>
  </div>`;
}

function entryHtml(t,e){
  const when=fmt(e.created);
  const sub=e.subtopic?`<span class="tag">${esc(e.subtopic)}</span>`:"";
  const srcs=e.sources.map((s,i)=>{
    if(s.type==="link")return `<span class="src-link" data-url="${esc(s.value)}" title="${esc(s.value)}"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M10 13a5 5 0 0 0 7.5.5l3-3a5 5 0 0 0-7-7l-1.7 1.7"/><path d="M14 11a5 5 0 0 0-7.5-.5l-3 3a5 5 0 0 0 7 7l1.7-1.7"/></svg>${esc(s.value)}</span>`;
    if(s.type==="string")return `<span class="src-str" data-copy="${esc(s.value)}" title="Click to copy"><span>“${esc(s.value)}”</span></span>`;
    if(s.type==="image")return `<img class="thumb" data-path="${esc(s.value)}" src="${imgSrc(s.value)}" title="Screenshot">`;
    return "";
  }).join("")||`<span class="muted" style="font-size:11.5px">no source</span>`;
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
    <div class="e-meta">${when}${sub}</div>
    <div class="e-text">${escTop(e.text)}</div>
    <div class="sources">${srcs}</div>
    ${actions}
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
  if(sAdd)sAdd.addEventListener("click",()=>{filterSub=null;render();});
  document.querySelectorAll("button[data-s]").forEach(b=>b.addEventListener("click",async()=>{
    const s=b.dataset.s;
    if(b.querySelector("span")){
      if(!confirm("Delete sub-topic "+s+"?"))return;
      const r=await api.delete_subtopic(t.id,s);
      if(r.error)return toast(r.error,"err");
      state=r;render();return;
    }
    filterSub=s;render();
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
}

let compLink="",compString="",compImage=null;
function bindComposer(t){
  const sub=$("#cSub");
  sub.innerHTML=[`<option value="">General</option>`].concat((t.subtopics||[]).map(s=>`<option value="${esc(s)}">${esc(s)}</option>`)).join("");
  $("#cLinkAdd").addEventListener("click",()=>{
    const v=$("#cLink").value.trim();if(!v)return;
    compLink=v;$("#cLink").value="";renderAtt();toast("Link added.");
  });
  $("#cStrAdd").addEventListener("click",()=>{
    const v=$("#cStr").value.trim();if(!v)return;
    compString=v;$("#cStr").value="";renderAtt();toast("Citation added.");
  });
  $("#cLink").addEventListener("keydown",e=>{if(e.key==="Enter")$("#cLinkAdd").click();});
  $("#cStr").addEventListener("keydown",e=>{if(e.key==="Enter")$("#cStrAdd").click();});
  $("#cShot").addEventListener("change",e=>{
    const f=e.target.files[0];if(!f)return;
    const rd=new FileReader();
    rd.onload=()=>{compImage=rd.result;renderAtt();toast("Screenshot attached.");};
    rd.readAsDataURL(f);e.target.value="";
  });
  $("#cGo").addEventListener("click",logComposer);
  $("#cText").addEventListener("keydown",e=>{if(e.key==="Enter"&&!e.ctrlKey&&!e.metaKey){e.preventDefault();logComposer();}});
}
function renderAtt(){
  const wrap=$("#cAtt");
  if(!wrap)return;
  const parts=[];
  if(compLink)parts.push(`<span class="chip active">link</span>`);
  if(compString)parts.push(`<span class="chip active">string</span>`);
  if(compImage)parts.push(`<span class="chip active">shot</span>`);
  wrap.innerHTML=parts.join("")||`<span class="muted" style="font-size:11.5px">pending sources</span>`;
}
async function logComposer(){
  const t=byId(sel);if(!t)return;
  const text=$("#cText").value;
  if(!text.trim()){toast("Write the point first.","err");return;}
  const r=await api.add_entry(t.id,$("#cSub").value,text,compLink,compString,compImage);
  if(r.error)return toast(r.error,"err");
  state=r;compLink="";compString="";compImage=null;
  $("#cText").value="";renderAtt();render();toast("Point logged.");
}

async function closeAndExport(){
  if(!confirm("Close this topic? It will be locked and exported as a cited report."))return;
  const r=await api.close_topic(sel);
  if(r.error)return toast(r.error,"err");
  state=r;
  const ex=await api.export_topic(sel);
  if(ex.error)return toast(ex.error,"err");
  tab="closed";render();
  showExportToast(ex);
}
async function doExport(){
  const ex=await api.export_topic(sel);
  if(ex.error)return toast(ex.error,"err");
  showExportToast(ex);
}
function showExportToast(ex){
  const t=document.createElement("div");t.className="toast";
  t.innerHTML=`<b>Exported ${ex.entries} point(s)</b><br><a href="#" id="exOpenHtml" style="color:#f0a94a">Open HTML report</a> &nbsp;·&nbsp; <a href="#" id="exOpenMd" style="color:#7bd88f">Open Markdown</a> &nbsp;·&nbsp; <a href="#" id="exFolder" style="color:#4fd8c8">Show folder</a>`;
  document.getElementById("toasts").appendChild(t);
  setTimeout(()=>t.classList.add("out"),9000);setTimeout(()=>t.remove(),9400);
  t.querySelector("#exOpenHtml").addEventListener("click",()=>api.open_path(ex.html));
  t.querySelector("#exOpenMd").addEventListener("click",()=>api.open_path(ex.md));
  t.querySelector("#exFolder").addEventListener("click",()=>api.open_path(ex.folder));
}

function settingsHtml(){
  const c=state.config||{};
  const hk=c.hotkey||{};
  const llm=c.llm||{};
  const mods=hk.modifiers||["ctrl","alt"];
  const prov=(state.providers||{});
  const mk=(id,checked,label)=>`<label class="mod"><input type="checkbox" id="${id}" ${checked?"checked":""}> ${label}</label>`;
  const provOpts=Object.keys(prov).map(k=>`<option value="${k}" ${llm.provider===k?"selected":""}>${prov[k].label}</option>`).join("");
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
      <div class="card-h"><div class="card-t">AI assist</div></div>
      <p class="muted">Optional and bring-your-own-key. Polish a logged point or draft a summary on export. Works with any OpenAI-compatible provider. Default: <b>OpenRouter</b> + <b>deepseek/deepseek-v4-flash</b>.</p>
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
      <div class="card-h"><div class="card-t">Data &amp; privacy</div></div>
      <p class="muted">Everything is stored locally next to the app: <b>points.json</b> for your topics, <b>attachments/</b> for screenshots, <b>exports/</b> for closed reports. No cloud, no telemetry. The AI assist feature only sends a point’s text to the provider you chose, and only when you click <b>Polish</b> or <b>Export</b>.</p>
    </div>
  </div>`;
}

function bindSettings(){
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
}

document.getElementById("seg").addEventListener("click",e=>{
  const b=e.target.closest(".seg");if(!b)return;
  tab=b.dataset.tab;sel=null;editEntry=null;filterSub=null;render();
});
document.getElementById("newBtn").addEventListener("click",()=>{tab="open";sel=null;render();});
document.getElementById("popupBtn").addEventListener("click",()=>api.show_popup());

function refreshFromBridge(){
  api.get_state().then(r=>{if(r&&!r.error){state=r;render();}}).catch(()=>{});
}

async function init(){
  state=await api.get_state();
  render();
}
if(window.pywebview){init();}else{window.addEventListener("pywebviewready",init);}
</script></body></html>
"""

POPUP_HTML = POPUP_HTML.replace("__BASE_CSS__", BASE_CSS)
MAIN_HTML = MAIN_HTML.replace("__BASE_CSS__", BASE_CSS)