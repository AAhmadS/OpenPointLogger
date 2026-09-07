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
    "export": {
        "template": "personal-report",
        "formats": ["html", "pdf", "markdown"],
        "author": "",
        "org": "",
        "engine": "",
        "dates": True,
    },
    "appearance": {
        "theme": "system",
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
                for section in ("hotkey", "llm", "export", "appearance"):
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
        return {"topics": topics, "config": self.config, "providers": PROVIDERS,
                "exports": self.list_exports(), "templates": self.list_templates()}

    def list_templates(self):
        try:
            import templates_registry
            return [{k: v for k, v in t.items() if k != "dir"} for t in templates_registry.available()]
        except Exception:
            return []

    # --- exports -------------------------------------------------------------

    def _read_export(self, folder):
        """One export folder as a record, from its manifest when it has one.

        Exports written before manifests existed are still listed: the topic is
        recovered from the folder-name slug so old reports do not vanish from the
        tab, they just group under a slug instead of a topic id.
        """
        files = {}
        for kind, name in (("html", "report.html"), ("markdown", "report.md"),
                           ("pdf", "report.pdf"), ("docx", "report.docx"),
                           ("latex", "report.tex")):
            p = folder / name
            if p.exists():
                files[kind] = str(p)
        if not files:
            return None
        mf = folder / "manifest.json"
        doc = {}
        if mf.exists():
            try:
                doc = json.loads(mf.read_text(encoding="utf-8"))
            except Exception:
                doc = {}
        newest = max((Path(p).stat().st_mtime for p in files.values()), default=0)
        slug = re.sub(r"_\d{8}_\d{6}(?:-\d+)?$", "", folder.name)
        legacy_polished = slug.endswith("_polished")
        if legacy_polished:
            slug = slug[: -len("_polished")]
        return {
            "folder": str(folder),
            "name": folder.name,
            "files": files,
            # kept flat for the toast and older call sites
            "html": files.get("html", ""),
            "md": files.get("markdown", ""),
            "pdf": files.get("pdf", ""),
            "docx": files.get("docx", ""),
            "mtime": newest,
            "size": sum(Path(p).stat().st_size for p in files.values()),
            "topic_id": doc.get("topic_id") or ("slug:" + slug),
            "topic_title": doc.get("topic_title") or slug.replace("-", " ").title(),
            "template": doc.get("template", ""),
            "template_name": doc.get("template_name", ""),
            "polished": bool(doc.get("polished", legacy_polished)),
            "entries": doc.get("entries"),
            "sources": doc.get("sources"),
            "pdf_pages": doc.get("pdf_pages"),
            "warnings": doc.get("warnings", []),
            "has_manifest": bool(doc),
        }

    def list_exports(self, per_topic=12, max_groups=40):
        """Exports grouped by the topic they came from, newest group first.

        The tab used to be a flat list, so a topic exported five times filled the
        sidebar with five near-identical rows. Grouping makes each topic one
        collapsible entry whose most recent report is the one on top.
        """
        groups = {}
        if not EXPORT_DIR.exists():
            return []
        for folder in EXPORT_DIR.iterdir():
            if not folder.is_dir():
                continue
            try:
                rec = self._read_export(folder)
            except Exception:
                rec = None
            if not rec:
                continue
            g = groups.setdefault(rec["topic_id"], {
                "topic_id": rec["topic_id"], "topic_title": rec["topic_title"],
                "exports": [], "latest": 0})
            g["exports"].append(rec)
            if rec["mtime"] > g["latest"]:
                g["latest"] = rec["mtime"]
                g["topic_title"] = rec["topic_title"]

        out = sorted(groups.values(), key=lambda g: g["latest"], reverse=True)[:max_groups]
        for g in out:
            g["exports"].sort(key=lambda e: e["mtime"], reverse=True)
            g["total"] = len(g["exports"])
            g["exports"] = g["exports"][:per_topic]
            g["formats"] = sorted({k for e in g["exports"] for k in e["files"]})
        return out

    def delete_export(self, folder):
        try:
            p = Path(str(folder or "")).resolve()
            base = EXPORT_DIR.resolve()
            # ensure p is inside EXPORT_DIR to avoid deleting arbitrary paths
            if not str(p).startswith(str(base)):
                return {"error": "Invalid export path."}
            if not p.exists() or not p.is_dir():
                return {"error": "Export not found."}
            # safety: the folder must actually look like an export we produced
            if not any((p / n).exists() for n in
                       ("report.html", "report.md", "report.pdf", "report.docx", "manifest.json")):
                return {"error": "Not a valid export folder."}
            shutil.rmtree(p, ignore_errors=False)
            return self.state()
        except Exception as e:
            return {"error": "Could not remove export: %s" % e}

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

    # --- export --------------------------------------------------------------
    #
    # All four artefacts come out of one staged pipeline (pipeline.py). The old
    # hand-rolled HTML/Markdown renderers that used to live here are gone: there
    # were two of them, they disagreed about Markdown, and the polished one
    # emitted literal ** into the report.

    def _export_meta(self, extra=None):
        cfg = dict(self.config.get("export") or {})
        meta = {"author": cfg.get("author", ""), "org": cfg.get("org", "")}
        meta.update(extra or {})
        return meta

    def export_topic(self, tid, options=None):
        """Export one topic. ``options`` may carry template, formats, subtitle,
        summary, and a polished Markdown body from the AI path."""
        import pipeline
        options = dict(options or {})
        t = self.find_topic(tid)
        if not t:
            return {"error": "Topic not found."}
        entries = sorted(t.get("entries", []), key=lambda e: e.get("created") or "")
        if not entries:
            return {"error": "Nothing to export yet - add a few logs first."}
        cfg = dict(self.config.get("export") or {})
        template = options.get("template") or cfg.get("template") or "personal-report"
        formats = options.get("formats") or cfg.get("formats") or ["html", "markdown"]
        refs, cites = self._collect_refs(entries)
        res = pipeline.export(
            t, entries, refs, cites, EXPORT_DIR,
            template_id=template,
            formats=tuple(formats),
            polished_markdown=options.get("polished_markdown"),
            meta=self._export_meta({"subtitle": options.get("subtitle", ""),
                                    "summary": options.get("summary", "")}),
            prefer_engine=(cfg.get("engine") or None))
        if res.get("error") and not res.get("files"):
            return {"error": res["error"]}
        # shape the result the UI toast expects, plus the richer detail
        files = res.get("files", {})
        res.update({"html": files.get("html", ""), "md": files.get("markdown", ""),
                    "pdf": files.get("pdf", ""), "docx": files.get("docx", "")})
        return res

    def export_topic_polished(self, tid, polished_markdown, options=None):
        options = dict(options or {})
        options["polished_markdown"] = polished_markdown
        return self.export_topic(tid, options)

    def export_payload(self, tid):
        """The Markdown the AI polish pass rewrites - same text the deterministic
        export starts from, so the citation check can compare the two."""
        import pipeline
        t = self.find_topic(tid)
        if not t:
            return None
        entries = sorted(t.get("entries", []), key=lambda e: e.get("created") or "")
        if not entries:
            return None
        refs, cites = self._collect_refs(entries)
        return {"markdown": pipeline.compose_markdown(t, entries, cites),
                "refs": len(refs), "entries": len(entries), "title": t.get("title", "")}

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

