import base64
import json
import os
import re
import shutil
import sys
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path

APP_NAME = "Trailmark"
FMT = "%Y-%m-%dT%H:%M:%S"

DEFAULT_CONFIG = {
    "hotkey": {"modifiers": ["ctrl", "alt"], "key": "P"},
    "llm": {
        "enabled": False,
        "provider": "openrouter",
        "model": "deepseek/deepseek-v4-flash",
        "api_key": "",
        "base_url": "",
    },
}

PROVIDERS = {
    "openrouter": {"label": "OpenRouter", "base_url": "https://openrouter.ai/api/v1", "model": "deepseek/deepseek-v4-flash"},
    "openai": {"label": "OpenAI", "base_url": "https://api.openai.com/v1", "model": "gpt-4o-mini"},
    "mistralai": {"label": "Mistral AI", "base_url": "https://api.mistral.ai/v1", "model": "mistral-small-latest"},
    "avalai": {"label": "AvalAI", "base_url": "https://api.avalai.ir/v1", "model": "gpt-4o-mini"},
    "google": {"label": "Google AI Studio", "base_url": "https://generativelanguage.googleapis.com/v1beta", "model": "gemini-2.0-flash"},
}


def data_dir():
    if getattr(sys, "frozen", False):
        base = Path(os.environ.get("APPDATA") or Path.home()) / "Trailmark"
    else:
        base = Path(__file__).resolve().parent
    return base


BASE_DIR = data_dir()
DATA_FILE = BASE_DIR / "points.json"
CONFIG_FILE = BASE_DIR / "config.json"
ATTACH_DIR = BASE_DIR / "attachments"
EXPORT_DIR = BASE_DIR / "exports"

LEGACY_DIR = None
if os.environ.get("LOCALAPPDATA"):
    LEGACY_DIR = Path(os.environ["LOCALAPPDATA"]) / "Programs" / "OpenPointLogger"


def _migrate_legacy_data():
    if not getattr(sys, "frozen", False):
        return
    if not LEGACY_DIR or not LEGACY_DIR.exists():
        return
    legacy_data = LEGACY_DIR / "points.json"
    if not legacy_data.exists() or DATA_FILE.exists():
        return
    try:
        ATTACH_DIR.mkdir(parents=True, exist_ok=True)
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        for sub, dst in (("attachments", ATTACH_DIR), ("exports", EXPORT_DIR)):
            src = LEGACY_DIR / sub
            if src.exists():
                for f in src.rglob("*"):
                    if f.is_file():
                        rel = f.relative_to(src)
                        out = dst / rel
                        out.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(f, out)
        cfg = LEGACY_DIR / "config.json"
        if cfg.exists():
            shutil.copy2(cfg, CONFIG_FILE)
        data = json.loads(legacy_data.read_text(encoding="utf-8"))
        old_att = str((LEGACY_DIR / "attachments").resolve())
        new_att = str(ATTACH_DIR.resolve())
        for t in data.get("topics", []):
            for e in t.get("entries", []):
                for s in e.get("sources", []):
                    v = s.get("value", "")
                    if s.get("type") == "image" and v.startswith(old_att):
                        s["value"] = new_att + v[len(old_att):]
        DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def now_iso():
    return datetime.now().strftime(FMT)


def parse_time(v):
    if isinstance(v, datetime):
        return v
    if not isinstance(v, str):
        return None
    try:
        return datetime.strptime(v, FMT)
    except ValueError:
        return None


def new_topic(title):
    return {
        "id": uuid.uuid4().hex,
        "title": title,
        "status": "open",
        "created": now_iso(),
        "closed": None,
        "subtopics": [],
        "entries": [],
    }


def new_entry(subtopic, text):
    return {
        "id": uuid.uuid4().hex,
        "subtopic": subtopic or "",
        "text": text,
        "created": now_iso(),
        "sources": [],
    }


def esc(s):
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;"))


def slugify(title):
    s = re.sub(r"[^\w\-]+", "-", title.lower()).strip("-")
    return s[:48] or "topic"


class Store:
    _serializable = False

    def __init__(self):
        _migrate_legacy_data()
        self._lock = threading.Lock()
        self._topics = self._load()
        self.config = self._load_config()

    def _load(self):
        if DATA_FILE.exists():
            try:
                data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
                return data.get("topics", [])
            except Exception:
                return []
        return []

    def _save(self):
        with self._lock:
            DATA_FILE.parent.mkdir(exist_ok=True)
            tmp = DATA_FILE.with_suffix(".json.tmp")
            data = json.dumps({"topics": self._topics}, ensure_ascii=False, indent=2)
            for attempt in range(2):
                try:
                    tmp.write_text(data, encoding="utf-8")
                    tmp.replace(DATA_FILE)
                    return
                except PermissionError:
                    if attempt == 1:
                        raise
                    time.sleep(0.15)

    def _load_config(self):
        cfg = json.loads(json.dumps(DEFAULT_CONFIG))
        if CONFIG_FILE.exists():
            try:
                saved = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
                for section in ("hotkey", "llm"):
                    if section in saved and isinstance(saved[section], dict):
                        cfg[section].update(saved[section])
            except Exception:
                pass
        return cfg

    def save_config(self):
        with self._lock:
            CONFIG_FILE.parent.mkdir(exist_ok=True)
            CONFIG_FILE.write_text(json.dumps(self.config, ensure_ascii=False, indent=2),
                                   encoding="utf-8")

    def state(self):
        topics = sorted(self._topics, key=lambda t: t.get("closed") or t.get("created") or "", reverse=True)
        return {"topics": topics, "config": self.config, "providers": PROVIDERS, "exports": self.list_exports()}

    def list_exports(self):
        out = []
        if not EXPORT_DIR.exists():
            return out
        for folder in sorted(EXPORT_DIR.iterdir(), reverse=True):
            if not folder.is_dir():
                continue
            html = folder / "report.html"
            md = folder / "report.md"
            if not html.exists():
                continue
            try:
                stat = html.stat()
                out.append({"folder": str(folder), "html": str(html), "md": str(md) if md.exists() else "",
                            "name": folder.name, "mtime": stat.st_mtime, "size": stat.st_size})
            except Exception:
                pass
        return out[:20]

    def find_topic(self, tid):
        for t in self._topics:
            if t["id"] == tid:
                return t
        return None

    def open_topics(self):
        return [t for t in self._topics if t.get("status") == "open"]

    def last_open_topic(self):
        opens = self.open_topics()
        if not opens:
            return None
        opens.sort(key=lambda t: t.get("created") or "", reverse=True)
        return opens[0]

    def start_topic(self, title):
        title = str(title or "").strip()
        if not title:
            return {"error": "Give the topic a name first."}
        t = new_topic(title)
        self._topics.append(t)
        self._save()
        return self.state()

    def update_topic(self, tid, title):
        t = self.find_topic(tid)
        if not t:
            return {"error": "Topic not found."}
        title = str(title or "").strip()
        if not title:
            return {"error": "Topic title cannot be empty."}
        t["title"] = title
        self._save()
        return self.state()

    def close_topic(self, tid):
        t = self.find_topic(tid)
        if not t:
            return {"error": "Topic not found."}
        if t.get("status") == "closed":
            return {"error": "Topic is already closed."}
        t["status"] = "closed"
        t["closed"] = now_iso()
        self._save()
        return self.state()

    def reopen_topic(self, tid):
        t = self.find_topic(tid)
        if not t:
            return {"error": "Topic not found."}
        t["status"] = "open"
        t["closed"] = None
        self._save()
        return self.state()

    def delete_topic(self, tid):
        t = self.find_topic(tid)
        if not t:
            return {"error": "Topic not found."}
        self._topics.remove(t)
        drop = ATTACH_DIR / tid
        if drop.exists():
            shutil.rmtree(drop, ignore_errors=True)
        self._save()
        return self.state()

    def add_subtopic(self, tid, name):
        t = self.find_topic(tid)
        if not t:
            return {"error": "Topic not found."}
        name = str(name or "").strip()
        if not name:
            return {"error": "Sub-topic name cannot be empty."}
        if name not in t["subtopics"]:
            t["subtopics"].append(name)
            self._save()
        return self.state()

    def rename_subtopic(self, tid, old, new):
        t = self.find_topic(tid)
        if not t:
            return {"error": "Topic not found."}
        new = str(new or "").strip()
        if not new:
            return {"error": "Sub-topic name cannot be empty."}
        if old in t["subtopics"]:
            t["subtopics"] = [new if s == old else s for s in t["subtopics"]]
        for e in t["entries"]:
            if e.get("subtopic") == old:
                e["subtopic"] = new
        self._save()
        return self.state()

    def delete_subtopic(self, tid, name):
        t = self.find_topic(tid)
        if not t:
            return {"error": "Topic not found."}
        if name in t["subtopics"]:
            t["subtopics"].remove(name)
        for e in t["entries"]:
            if e.get("subtopic") == name:
                e["subtopic"] = ""
        self._save()
        return self.state()

    def add_entry(self, tid, subtopic, text, source_link="", source_string="", image_data=None, sources=None):
        t = self.find_topic(tid)
        if not t:
            return {"error": "Topic not found."}
        text = str(text or "").strip()
        if not text:
            return {"error": "Write the point before logging it."}
        e = new_entry(subtopic, text)
        # legacy single fields (kept for backward compat + tests)
        if source_link:
            links = source_link if isinstance(source_link, list) else [source_link]
            for v in links:
                v = str(v).strip()
                if v:
                    e["sources"].append({"id": uuid.uuid4().hex, "type": "link",
                                         "value": v, "note": "", "added": now_iso()})
        if source_string:
            strs = source_string if isinstance(source_string, list) else [source_string]
            for v in strs:
                v = str(v).strip()
                if v:
                    e["sources"].append({"id": uuid.uuid4().hex, "type": "string",
                                         "value": v, "note": "", "added": now_iso()})
        if image_data:
            imgs = image_data if isinstance(image_data, list) else [image_data]
            for data_url in imgs:
                if not data_url:
                    continue
                path = self._save_image(tid, e["id"], data_url)
                if path:
                    e["sources"].append({"id": uuid.uuid4().hex, "type": "image",
                                         "value": str(path), "note": "", "added": now_iso()})
        # new unified sources array (preferred for multi-citation UI)
        if sources and isinstance(sources, list):
            for s in sources:
                stype = (s.get("type") or "").strip()
                value = str(s.get("value") or "").strip()
                if not value or stype not in ("link", "string", "image"):
                    continue
                if stype == "image" and value.startswith("data:"):
                    path = self._save_image(tid, e["id"], value)
                    if path:
                        value = str(path)
                    else:
                        continue
                e["sources"].append({"id": uuid.uuid4().hex, "type": stype,
                                     "value": value, "note": str(s.get("note") or "").strip(), "added": now_iso()})
        if e["subtopic"] and e["subtopic"] not in t["subtopics"]:
            t["subtopics"].append(e["subtopic"])
        t["entries"].append(e)
        self._save()
        return self.state()

    def update_entry(self, tid, eid, fields):
        t = self.find_topic(tid)
        if not t:
            return {"error": "Topic not found."}
        e = self._find_entry(t, eid)
        if not e:
            return {"error": "Entry not found."}
        if "text" in fields:
            e["text"] = str(fields.get("text") or "").strip()
        if "subtopic" in fields:
            e["subtopic"] = str(fields.get("subtopic") or "").strip()
            if e["subtopic"] and e["subtopic"] not in t["subtopics"]:
                t["subtopics"].append(e["subtopic"])
        self._save()
        return self.state()

    def delete_entry(self, tid, eid):
        t = self.find_topic(tid)
        if not t:
            return {"error": "Topic not found."}
        e = self._find_entry(t, eid)
        if not e:
            return {"error": "Entry not found."}
        for s in e.get("sources", []):
            if s.get("type") == "image":
                p = Path(s["value"])
                if p.is_absolute() and p.exists():
                    p.unlink(missing_ok=True)
        t["entries"].remove(e)
        self._save()
        return self.state()

    def add_source(self, tid, eid, stype, value, note=""):
        t = self.find_topic(tid)
        if not t:
            return {"error": "Topic not found."}
        e = self._find_entry(t, eid)
        if not e:
            return {"error": "Entry not found."}
        value = str(value or "").strip()
        if not value:
            return {"error": "Source cannot be empty."}
        e["sources"].append({"id": uuid.uuid4().hex, "type": stype,
                             "value": value, "note": str(note or "").strip(), "added": now_iso()})
        self._save()
        return self.state()

    def delete_source(self, tid, eid, sid):
        t = self.find_topic(tid)
        if not t:
            return {"error": "Topic not found."}
        e = self._find_entry(t, eid)
        if not e:
            return {"error": "Entry not found."}
        src = next((s for s in e.get("sources", []) if s.get("id") == sid), None)
        if not src:
            return {"error": "Source not found."}
        if src.get("type") == "image":
            p = Path(src["value"])
            if p.is_absolute() and p.exists():
                p.unlink(missing_ok=True)
        e["sources"].remove(src)
        self._save()
        return self.state()

    def save_image(self, tid, eid, data_url):
        t = self.find_topic(tid)
        if not t:
            return {"error": "Topic not found."}
        e = self._find_entry(t, eid)
        if not e:
            return {"error": "Entry not found."}
        path = self._save_image(tid, eid, data_url)
        if not path:
            return {"error": "Could not save the image."}
        e["sources"].append({"id": uuid.uuid4().hex, "type": "image",
                             "value": str(path), "note": "", "added": now_iso()})
        self._save()
        return self.state()

    @staticmethod
    def _save_image(tid, eid, data_url):
        try:
            header, b64 = data_url.split(",", 1)
            ext = "png"
            m = re.search(r"image/(\w+)", header)
            if m and m.group(1) in ("png", "jpeg", "jpg", "gif", "webp", "bmp"):
                ext = "jpg" if m.group(1) == "jpeg" else m.group(1)
            folder = ATTACH_DIR / tid / eid
            folder.mkdir(parents=True, exist_ok=True)
            path = folder / ("%s.%s" % (uuid.uuid4().hex[:12], ext))
            path.write_bytes(base64.b64decode(b64))
            return path
        except Exception:
            return None

    @staticmethod
    def _find_entry(t, eid):
        for e in t.get("entries", []):
            if e["id"] == eid:
                return e
        return None

    def export_topic(self, tid):
        t = self.find_topic(tid)
        if not t:
            return {"error": "Topic not found."}
        entries = sorted(t.get("entries", []), key=lambda e: e.get("created") or "")
        if not entries:
            return {"error": "Nothing to export yet — add a few logs first."}
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder = EXPORT_DIR / ("%s_%s" % (slugify(t["title"]), stamp))
        folder.mkdir(parents=True, exist_ok=True)
        html_path = folder / "report.html"
        md_path = folder / "report.md"
        refs, cites = self._collect_refs(entries)
        html_path.write_text(self._render_html(t, entries, refs, cites), encoding="utf-8")
        md_path.write_text(self._render_md(t, entries, refs, folder), encoding="utf-8")
        return {"html": str(html_path), "md": str(md_path), "entries": len(entries), "folder": str(folder)}

    def export_topic_polished(self, tid, polished_markdown):
        """Render a polished AI version without touching raw data. Returns same shape as export_topic."""
        t = self.find_topic(tid)
        if not t:
            return {"error": "Topic not found."}
        entries = sorted(t.get("entries", []), key=lambda e: e.get("created") or "")
        if not entries:
            return {"error": "Nothing to export yet — add a few logs first."}
        refs, cites = self._collect_refs(entries)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder = EXPORT_DIR / ("%s_polished_%s" % (slugify(t["title"]), stamp))
        folder.mkdir(parents=True, exist_ok=True)
        html_path = folder / "report.html"
        md_path = folder / "report.md"
        html_path.write_text(self._render_polished_html(t, entries, refs, cites, polished_markdown), encoding="utf-8")
        md_path.write_text(self._render_polished_md(t, refs, polished_markdown, folder, entries), encoding="utf-8")
        return {"html": str(html_path), "md": str(md_path), "entries": len(entries), "folder": str(folder), "polished": True}

    def _render_polished_html(self, t, entries, refs, cites, polished_md):
        # Convert markdown ## headers / paragraphs to HTML, keep [n] as links to #rN
        import re as _re
        def md_inline(s):
            s = esc(s)
            s = _re.sub(r'\[(\d+)\]', lambda m: '<a class="cite" href="#r%s">[%s]</a>' % (m.group(1), m.group(1)), s)
            s = s.replace("\n", "<br>")
            return s
        lines = polished_md.split("\n")
        body = ""
        in_list = False
        for line in lines:
            ls = line.strip()
            if ls.startswith("## "):
                if in_list:
                    body += "</ul>"
                    in_list = False
                body += '<section class="sub"><h2>%s</h2>' % esc(ls[3:].strip())
            elif ls.startswith("- ") or ls.startswith("* "):
                if not in_list:
                    body += '<ul class="polished-list">'
                    in_list = True
                body += '<li>%s</li>' % md_inline(ls[2:].strip())
            elif ls == "":
                if in_list:
                    body += "</ul>"
                    in_list = False
                body += ""
            else:
                if in_list:
                    body += "</ul>"
                    in_list = False
                if ls.startswith("# "):
                    body += '<h2>%s</h2>' % esc(ls[2:].strip())
                else:
                    body += '<p>%s</p>' % md_inline(line)
        if in_list:
            body += "</ul>"
        # close open sections
        body = body.replace("</ul><section", "</ul></section><section")
        # Ensure sections closed (simple count)
        open_secs = body.count("<section")
        close_secs = body.count("</section>")
        if open_secs > close_secs:
            body += "</section>" * (open_secs - close_secs)

        # append image figures at end (so screenshots are not lost)
        figures = ""
        for e in entries:
            for s in e.get("sources", []):
                if s.get("type") == "image":
                    p = Path(s["value"])
                    try:
                        b64 = base64.b64encode(p.read_bytes()).decode()
                        src = "data:image/%s;base64,%s" % (p.suffix.lstrip("."), b64)
                    except Exception:
                        src = ""
                    figures += '<figure><img src="%s" alt="screenshot"><figcaption>%s — %s</figcaption></figure>' % (src, esc(e.get("text","")[:60]), esc(p.name))
        if figures:
            body += '<section class="sub"><h2>Figures</h2>%s</section>' % figures

        ref_html = "".join(
            '<li id="r%d">%s</li>' % (i + 1, self._ref_text(r, Path(r.get("value", "")) if r.get("type") == "image" else None))
            for i, r in enumerate(refs))
        closed = parse_time(t.get("closed"))
        when_c = closed.strftime("%B %d, %Y · %H:%M") if closed else ""
        html = self._render_html(t, entries, refs, cites)  # reuse shell
        # replace body section with polished body
        # Instead of re-rendering shell, build fresh shell using polished body
        shell = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>__TITLE__ — Polished</title>
<style>
:root{--ink:#1a2230;--mut:#5c6675;--acc:#c97f2d;--acc-soft:#f3e4d2;--line:#e4e2dd;--bg:#fbfaf7}
*{box-sizing:border-box}body{margin:0;font-family:Georgia,'Times New Roman',serif;color:var(--ink);background:var(--bg)}
.page{max-width:820px;margin:0 auto;padding:52px 44px}
header{border-bottom:3px solid var(--acc);padding-bottom:22px;margin-bottom:30px}
.kicker{font-family:'Segoe UI',sans-serif;letter-spacing:.18em;text-transform:uppercase;font-size:11px;color:var(--acc);font-weight:600}
h1{margin:6px 0 4px;font-size:34px;line-height:1.15}
.sub{font-family:'Segoe UI',sans-serif;color:var(--mut);font-size:13px}
section.sub{margin:0 0 26px}
section.sub h2{font-family:'Segoe UI',sans-serif;font-size:15px;letter-spacing:.06em;text-transform:uppercase;color:#b3742a;margin:0 0 8px;padding-bottom:6px;border-bottom:1px solid var(--line)}
.entry{margin:0 0 18px}
.meta{font-family:'Segoe UI',sans-serif;font-size:11px;color:#a09a8e;letter-spacing:.03em}
.meta .cite, a.cite{color:var(--acc);font-weight:700;font-size:12px;text-decoration:none;border-bottom:1px solid rgba(201,127,45,.35)}
a.cite:hover{background:var(--acc-soft)}
.entry p, .page p{margin:5px 0 8px;font-size:15.5px;line-height:1.65;white-space:pre-line}
.polished-list{margin:6px 0 10px;padding-left:22px;font-size:15px;line-height:1.6}
h2.refs{font-family:'Segoe UI',sans-serif;font-size:16px;margin:38px 0 10px;padding-top:16px;border-top:3px solid var(--acc)}
ol.refs{font-family:'Segoe UI',sans-serif;font-size:12.5px;line-height:1.7;color:#333;padding-left:22px}
ol.refs a{color:var(--acc);word-break:break-all}
footer{margin-top:40px;font-family:'Segoe UI',sans-serif;font-size:11px;color:#b3ada1;text-align:center}
.badge{display:inline-flex;align-items:center;gap:6px;padding:4px 10px;border-radius:999px;font-family:'Segoe UI',sans-serif;font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;background:rgba(79,216,200,.14);color:#0e8a7a;border:1px solid rgba(79,216,200,.32);margin-top:8px}
figure{margin:10px 0}figure img{max-width:100%;border-radius:10px;border:1px solid var(--line);box-shadow:0 6px 18px rgba(0,0,0,.08)}
figcaption{font-family:'Segoe UI',sans-serif;font-size:11.5px;color:var(--mut);margin-top:6px}
</style></head><body><div class="page">
<header><div class="kicker">Trailmark · Research Notes — Polished via AI</div>
<h1>__TITLE__</h1>
<div class="sub">__WHEN__ &nbsp;·&nbsp; __COUNT__</div>
<span class="badge">✦ Polished — facts unchanged, prose arranged</span>
</header>
__BODY__
<h2 class="refs">References</h2>
<ol class="refs">__REFS__</ol>
<footer>Generated by Trailmark · Log the point. Keep the source. · Polished via AI (optional)</footer>
</div></body></html>"""
        shell = (shell.replace("__TITLE__", esc(t["title"]))
                 .replace("__WHEN__", when_c)
                 .replace("__COUNT__", "%d logged point%s &nbsp;·&nbsp; %d source%s cited" % (
                     len(entries), "" if len(entries) == 1 else "s",
                     len(refs), "" if len(refs) == 1 else "s"))
                 .replace("__BODY__", body)
                 .replace("__REFS__", ref_html))
        return shell

    def _render_polished_md(self, t, refs, polished_md, folder, entries):
        lines = ["# %s (Polished)" % t["title"], ""]
        lines.append(polished_md)
        lines.append("")
        lines.append("## References")
        lines.append("")
        for i, r in enumerate(refs):
            if r.get("type") == "link":
                lines.append("%d. %s" % (i + 1, r["value"]))
            elif r.get("type") == "string":
                lines.append("%d. \"%s\"" % (i + 1, r["value"]))
            elif r.get("type") == "image":
                lines.append("%d. Screenshot: %s" % (i + 1, Path(r["value"]).name))
                src = Path(r["value"])
                if src.is_absolute() and src.exists():
                    img_dir = folder / "images"
                    img_dir.mkdir(exist_ok=True)
                    shutil.copy2(src, img_dir / src.name)
        lines.append("")
        lines.append("---")
        lines.append("_Polished via AI — facts unchanged. Generated by Trailmark._")
        return "\n".join(lines)

    @staticmethod
    def _collect_refs(entries):
        refs = []
        cites = {}
        for e in entries:
            nums = []
            for s in e.get("sources", []):
                key = (s.get("type"), s.get("value"))
                if key not in cites:
                    cites[key] = len(refs) + 1
                    refs.append(s)
                nums.append(cites[key])
            cites[e["id"]] = nums
        return refs, cites

    def _render_html(self, t, entries, refs, cites):
        def img_data(path):
            try:
                return "data:%s;base64,%s" % ("image/" + path.suffix.lstrip("."), base64.b64encode(path.read_bytes()).decode())
            except Exception:
                return ""

        groups = {}
        for e in entries:
            groups.setdefault(e.get("subtopic") or "General", []).append(e)

        body = ""
        for subtopic in sorted(groups.keys()):
            body += '<section class="sub"><h2>%s</h2>' % esc(subtopic)
            for e in groups[subtopic]:
                when = parse_time(e.get("created"))
                when_s = when.strftime("%B %d, %Y · %H:%M") if when else ""
                nums = cites.get(e["id"], [])
                cite = (" ".join('<sup class="cite"><a href="#r%d">[%d]</a></sup>' % (n, n) for n in nums)) if nums else ""
                body += '<article class="entry"><div class="meta">%s %s</div><p>%s</p>' % (
                    esc(when_s), cite, esc(e.get("text")).replace("\n", "<br>"))
                for s in e.get("sources", []):
                    if s.get("type") == "link":
                        body += '<div class="src src-link">Link: <a href="%s" target="_blank" rel="noopener">%s</a></div>' % (esc(s["value"]), esc(s["value"]))
                    elif s.get("type") == "string":
                        body += '<div class="src src-str">Source: &ldquo;%s&rdquo;</div>' % esc(s["value"])
                    elif s.get("type") == "image":
                        body += '<figure><img src="%s" alt="screenshot"><figcaption>%s</figcaption></figure>' % (img_data(Path(s["value"])), esc(s.get("note") or "Screenshot"))
                body += "</article>"
            body += "</section>"

        ref_html = "".join(
            '<li id="r%d">%s</li>' % (i + 1, self._ref_text(r, Path(r.get("value", "")) if r.get("type") == "image" else None))
            for i, r in enumerate(refs))

        closed = parse_time(t.get("closed"))
        when_c = closed.strftime("%B %d, %Y · %H:%M") if closed else ""
        html = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>__TITLE__</title>
<style>
:root{--ink:#1a2230;--mut:#5c6675;--acc:#c97f2d;--acc-soft:#f3e4d2;--line:#e4e2dd;--bg:#fbfaf7}
*{box-sizing:border-box}body{margin:0;font-family:Georgia,'Times New Roman',serif;color:var(--ink);background:var(--bg)}
.page{max-width:820px;margin:0 auto;padding:52px 44px}
header{border-bottom:3px solid var(--acc);padding-bottom:22px;margin-bottom:30px}
.kicker{font-family:'Segoe UI',sans-serif;letter-spacing:.18em;text-transform:uppercase;font-size:11px;color:var(--acc);font-weight:600}
h1{margin:6px 0 4px;font-size:34px;line-height:1.15}
.sub{font-family:'Segoe UI',sans-serif;color:var(--mut);font-size:13px}
.stats{margin-top:10px;font-family:'Segoe UI',sans-serif;font-size:12.5px;color:var(--mut)}
.stats b{color:var(--ink)}
section.sub{margin:0 0 26px}
section.sub h2{font-family:'Segoe UI',sans-serif;font-size:15px;letter-spacing:.06em;text-transform:uppercase;color:#b3742a;margin:0 0 8px;padding-bottom:6px;border-bottom:1px solid var(--line)}
.entry{margin:0 0 18px}
.meta{font-family:'Segoe UI',sans-serif;font-size:11px;color:#a09a8e;letter-spacing:.03em}
.meta .cite{color:var(--acc);font-weight:700;font-size:12px}
.meta .cite a{color:inherit;text-decoration:none;border-bottom:1px solid rgba(201,127,45,.35)}
.meta .cite a:hover{background:var(--acc-soft)}
.entry p{margin:5px 0 8px;font-size:15.5px;line-height:1.65;white-space:pre-line}
.src{font-family:'Segoe UI',sans-serif;font-size:12.5px;margin:3px 0}
.src-link a{color:var(--acc);text-decoration:none;word-break:break-all}
.src-link a:hover{text-decoration:underline}
.src-str{color:var(--mut);font-style:italic}
figure{margin:10px 0}
figure img{max-width:100%;border-radius:10px;border:1px solid var(--line);box-shadow:0 6px 18px rgba(0,0,0,.08)}
figcaption{font-family:'Segoe UI',sans-serif;font-size:11.5px;color:var(--mut);margin-top:6px}
h2.refs{font-family:'Segoe UI',sans-serif;font-size:16px;margin:38px 0 10px;padding-top:16px;border-top:3px solid var(--acc)}
ol.refs{font-family:'Segoe UI',sans-serif;font-size:12.5px;line-height:1.7;color:#333;padding-left:22px}
ol.refs a{color:var(--acc);word-break:break-all}
ol.refs .imgref{color:var(--mut);font-style:italic}
footer{margin-top:40px;font-family:'Segoe UI',sans-serif;font-size:11px;color:#b3ada1;text-align:center}
</style></head><body><div class="page">
<header><div class="kicker">Trailmark · Research Notes</div>
<h1>__TITLE__</h1>
<div class="sub">__WHEN__ &nbsp;·&nbsp; __COUNT__</div>
</header>
__BODY__
<h2 class="refs">References</h2>
<ol class="refs">__REFS__</ol>
<footer>Generated by Trailmark · Log the point. Keep the source.</footer>
</div></body></html>"""
        html = (html.replace("__TITLE__", esc(t["title"]))
                .replace("__WHEN__", when_c)
                .replace("__COUNT__", "%d logged point%s &nbsp;·&nbsp; %d source%s cited" % (
                    len(entries), "" if len(entries) == 1 else "s",
                    len(refs), "" if len(refs) == 1 else "s"))
                .replace("__BODY__", body)
                .replace("__REFS__", ref_html))
        return html

    def _ref_text(self, r, image_path=None):
        if r.get("type") == "link":
            return '<a href="%s">%s</a>' % (esc(r["value"]), esc(r["value"]))
        if r.get("type") == "string":
            return "&ldquo;%s&rdquo;" % esc(r["value"])
        if r.get("type") == "image":
            return '<span class="imgref">Screenshot: %s</span>' % esc(image_path.name if image_path else "")
        return ""

    def _render_md(self, t, entries, refs, folder):
        lines = ["# %s" % t["title"], ""]
        when_c = parse_time(t.get("closed"))
        lines.append("_%s · %d points · %d sources cited_" % (
            when_c.strftime("%Y-%m-%d") if when_c else "", len(entries), len(refs)))
        lines.append("")
        groups = {}
        for e in entries:
            groups.setdefault(e.get("subtopic") or "General", []).append(e)
        ref_nums = {}
        for i, r in enumerate(refs):
            ref_nums[(r.get("type"), r.get("value"))] = i + 1
        for subtopic in sorted(groups.keys()):
            lines.append("## %s" % subtopic)
            lines.append("")
            for e in groups[subtopic]:
                when = parse_time(e.get("created"))
                stamp = when.strftime("%Y-%m-%d %H:%M") if when else ""
                nums = [ref_nums[(s.get("type"), s.get("value"))] for s in e.get("sources", [])
                        if (s.get("type"), s.get("value")) in ref_nums]
                cite = " [%s]" % ", ".join("[%d]" % n for n in nums) if nums else ""
                lines.append("- **%s** %s%s" % (stamp, e.get("text", ""), cite))
                for s in e.get("sources", []):
                    if s.get("type") == "link":
                        lines.append("  - Link: %s" % s["value"])
                    elif s.get("type") == "string":
                        lines.append("  - Source: \"%s\"" % s["value"])
                    elif s.get("type") == "image":
                        src = Path(s["value"])
                        rel = "images/%s" % src.name if src.is_absolute() else s["value"]
                        if src.is_absolute() and src.exists():
                            img_dir = folder / "images"
                            img_dir.mkdir(exist_ok=True)
                            shutil.copy2(src, img_dir / src.name)
                        lines.append("  - Screenshot: %s" % rel)
                lines.append("")
        lines.append("## References")
        lines.append("")
        for i, r in enumerate(refs):
            if r.get("type") == "link":
                lines.append("%d. %s" % (i + 1, r["value"]))
            elif r.get("type") == "string":
                lines.append("%d. \"%s\"" % (i + 1, r["value"]))
            elif r.get("type") == "image":
                lines.append("%d. Screenshot: %s" % (i + 1, Path(r["value"]).name))
        lines.append("")
        lines.append("---")
        lines.append("_Generated by Trailmark — Log the point. Keep the source._")
        return "\n".join(lines)