import json
import os
import secrets
import sys
import threading
import traceback
import webbrowser
from urllib.parse import urlparse

import webview

from brand import ICON_DATA_URI, asset_path
from hotkey import HotkeyListener
from point_store import Store, data_dir, slugify
from ui import MAIN_HTML, POPUP_HTML

import asr
import clipboard
import llm
import single
import telegram_bridge
import templates_registry
import traymenu

#: Excludes 0/O/1/I - the pairing code is read off a phone screen and typed
#: back, so the characters most often confused with each other are dropped
#: rather than relying on the user to tell them apart.
_PAIRING_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"


def _new_pairing_code():
    return "".join(secrets.choice(_PAIRING_ALPHABET) for _ in range(6))

POPUP_HTML = POPUP_HTML.replace("__ICON__", ICON_DATA_URI)
MAIN_HTML = MAIN_HTML.replace("__ICON__", ICON_DATA_URI)


def system_prefers_light():
    """Whether Windows is set to a light app theme.

    Read straight from the registry rather than through a dependency; any
    failure (missing key on an old build, a locked-down profile) answers
    "dark", which is the app's default and never worse than guessing.
    """
    try:
        import winreg
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        ) as k:
            return bool(winreg.QueryValueEx(k, "AppsUseLightTheme")[0])
    except Exception:
        return False

POPUP_W, POPUP_H = 462, 648
MAIN_W, MAIN_H = 1180, 764

_HWND_TOPMOST, _HWND_NOTOPMOST = -1, -2
_SWP_NOSIZE, _SWP_NOMOVE, _SWP_NOACTIVATE = 0x0001, 0x0002, 0x0010


def _set_topmost(hwnd, topmost):
    """Assert or drop HWND_TOPMOST on a window, from any thread.

    This exists because `window.on_top = True` is not safe off the UI thread.
    pythonnet keeps the GIL while it runs a .NET property setter, the
    setter's SetWindowPos then blocks until the window's own thread services
    it, and right after the UI thread dispatches a js_api call it is itself
    waiting for the GIL - so the "+" button in the topbar wedged the whole
    app. ctypes drops the GIL for the duration of a foreign call, which is
    the one thing that makes the identical SetWindowPos safe here.
    """
    if not hwnd:
        return
    try:
        import ctypes
        ctypes.windll.user32.SetWindowPos(
            int(hwnd), _HWND_TOPMOST if topmost else _HWND_NOTOPMOST, 0, 0, 0, 0,
            _SWP_NOMOVE | _SWP_NOSIZE | _SWP_NOACTIVATE)
    except Exception:
        pass

#: Fixed sample data for the template-preview ("demo") feature. Kept identical,
#: byte-for-byte, to the fixture tests/test_export.py uses for the same purpose
#: - two different call sites rendering the same input is what makes the demo a
#: meaningful preview of a real export rather than its own separate thing.
_DEMO_TOPIC = {"id": "demo", "title": "Rust borrow checker", "status": "closed",
               "created": "2026-08-02T09:15:00", "closed": "2026-09-01T17:40:00"}
_DEMO_ENTRIES = [
    {"id": "d1", "subtopic": "Aliasing", "created": "2026-08-02T09:20:00",
     "text": "Two mutable borrows of the same place are rejected before monomorphisation.",
     "sources": [{"id": "ds1", "type": "link", "value": "https://doc.rust-lang.org/nomicon/",
                  "note": "Rustonomicon"}]},
    {"id": "d2", "subtopic": "Aliasing", "created": "2026-08-04T11:02:00",
     "text": "Reborrowing through &mut *x is what makes method chains work at all.",
     "sources": [{"id": "ds2", "type": "string", "value": "Jung et al., Stacked Borrows, POPL 2020"}]},
    {"id": "d3", "subtopic": "NLL", "created": "2026-08-11T14:33:00",
     "text": "Non-lexical lifetimes ended the drop-at-scope-end rejection class.",
     "sources": [{"id": "ds1", "type": "link", "value": "https://doc.rust-lang.org/nomicon/",
                  "note": "Rustonomicon"}]},
]


class Api:
    def __init__(self, store, controller):
        self.store = store
        self.controller = controller

    def get_state(self):
        return self.store.state()

    def get_config(self):
        return self.store.config

    def save_hotkey(self, cfg):
        mods = (cfg or {}).get("modifiers") or ["ctrl", "alt"]
        key = (cfg or {}).get("key") or "P"
        try:
            if not HotkeyListener.probe(mods, key):
                return {"error": "That combination is already in use by another app."}
        except ValueError as e:
            return {"error": str(e)}
        self.store.config["hotkey"] = {"modifiers": mods, "key": key}
        self.store.save_config()
        self.controller.apply_hotkey(mods, key)
        self.controller.refresh_full()
        return self.store.state()

    def read_clipboard(self):
        """JS-bridge entry point behind the popup's per-row "paste from
        clipboard" button. Never raises - clipboard.read() already can't,
        this is just the seam the frontend calls through."""
        try:
            return clipboard.read()
        except Exception:
            return {"type": "none", "value": None, "meta": {}}

    def take_clipboard_capture(self):
        """JS-bridge entry point behind the popup's clipboardCaptured():
        collects what the Ctrl+Alt+V hotkey read, exactly once."""
        return self.controller.take_clipboard_capture()

    def save_clipboard(self, cfg):
        """Mirrors save_hotkey's validate-then-save shape, not
        _save_section: unlike llm/export/appearance/science this config has
        a side effect (registering a second global hotkey listener) that a
        generic merge-and-save must not silently trigger."""
        cfg = cfg or {}
        enabled = bool(cfg.get("enabled"))
        mods = cfg.get("modifiers") or ["ctrl", "alt"]
        key = cfg.get("key") or "V"
        if enabled:
            # A disabled combo will never be registered, so a clash with
            # another app is not a reason to refuse saving it turned off.
            try:
                if not HotkeyListener.probe(mods, key):
                    return {"error": "That combination is already in use by another app."}
            except ValueError as e:
                return {"error": str(e)}
        self.store.config["clipboard"] = {"enabled": enabled, "modifiers": mods, "key": key}
        self.store.save_config()
        self.controller.apply_clipboard_hotkey(mods, key)
        self.controller.refresh_full()
        return self.store.state()

    def save_asr(self, cfg):
        """Mirrors save_clipboard's shape, not _save_section: enabling this
        starts a background microphone-capture thread, a side effect a generic
        merge-and-save must not silently trigger. The API key is validated for
        shape only (a string) — never logged, never echoed into an error
        message, never truncated-and-shown like a toast snippet."""
        cfg = cfg or {}
        prev = self.store.config.get("asr") or {}
        sensitivity = cfg.get("sensitivity", prev.get("sensitivity", 50))
        try:
            sensitivity = int(sensitivity)
        except (TypeError, ValueError):
            sensitivity = 50
        sensitivity = max(0, min(100, sensitivity))
        merged = {
            "enabled": bool(cfg.get("enabled")),
            "endpoint": (str(cfg.get("endpoint") or prev.get("endpoint") or "")).strip()
                        or "https://api.openai.com/v1",
            "model": (str(cfg.get("model") or prev.get("model") or "")).strip() or "whisper-1",
            "api_key": str(cfg.get("api_key")) if cfg.get("api_key") is not None else str(prev.get("api_key") or ""),
            "language": (str(cfg.get("language") or "")).strip(),
            "device": (str(cfg.get("device") or "")).strip(),
            "sensitivity": sensitivity,
        }
        self.store.config["asr"] = merged
        self.store.save_config()
        self.controller.apply_asr()
        self.controller.refresh_full()
        return self.store.state()

    def test_asr(self, seconds=5):
        cfg = self.store.config.get("asr") or {}
        return asr.test_capture(cfg, seconds=seconds)

    def list_asr_devices(self):
        return asr.list_devices()

    def save_telegram(self, cfg):
        """Mirrors save_asr's shape, not _save_section: enabling this starts
        a background polling thread against the Telegram Bot API, a side
        effect a generic merge-and-save must not silently trigger. The bot
        token is validated for shape only (a string) - never logged, never
        echoed into an error message, never truncated-and-shown like a
        toast snippet. Never returns the raw token: the return value is
        self.store.state(), which already masks it."""
        cfg = cfg or {}
        prev = self.store.config.get("telegram") or {}
        merged = {
            "enabled": bool(cfg.get("enabled")),
            "token": str(cfg.get("token")).strip() if cfg.get("token") is not None else str(prev.get("token") or ""),
            "chat_id": prev.get("chat_id"),
            "username": prev.get("username", ""),
            "pairing_code": prev.get("pairing_code") or _new_pairing_code(),
            "topic_id": cfg.get("topic_id", prev.get("topic_id")),
        }
        self.store.config["telegram"] = merged
        self.store.save_config()
        self.controller.apply_telegram()
        self.controller.refresh_full()
        return self.store.state()

    def telegram_regenerate_code(self):
        cfg = dict(self.store.config.get("telegram") or {})
        cfg["pairing_code"] = _new_pairing_code()
        self.store.config["telegram"] = cfg
        self.store.save_config()
        return self.store.state()

    def telegram_unpair(self):
        cfg = dict(self.store.config.get("telegram") or {})
        cfg["chat_id"] = None
        cfg["username"] = ""
        cfg["pairing_code"] = _new_pairing_code()
        self.store.config["telegram"] = cfg
        self.store.save_config()
        self.controller.apply_telegram()
        self.controller.refresh_full()
        return self.store.state()

    def telegram_status(self):
        cfg = self.store.config.get("telegram") or {}
        _token, source = telegram_bridge.load_token(self.store.config)
        return {
            "state": self.controller.telegram_state,
            "detail": self.controller.telegram_detail,
            "username": cfg.get("username", ""),
            "pairing_code": cfg.get("pairing_code", ""),
            "token_source": source,
        }

    def save_llm(self, cfg):
        return self._save_section("llm", cfg)

    def save_export(self, cfg):
        return self._save_section("export", cfg)

    def save_appearance(self, cfg):
        return self._save_section("appearance", cfg)

    def save_science(self, cfg):
        return self._save_section("science", cfg)

    def _save_section(self, name, cfg):
        merged = dict(self.store.config.get(name) or {})
        merged.update(cfg or {})
        self.store.config[name] = merged
        self.store.save_config()
        self.controller.refresh_full()
        return self.store.state()

    def list_templates(self):
        return {"templates": self.store.list_templates()}

    def open_template_dir(self):
        """Open the folder where the user's own templates live, creating it first."""
        try:
            d = templates_registry.user_dir()
            d.mkdir(parents=True, exist_ok=True)
            os.startfile(str(d))
            return {"path": str(d)}
        except Exception as e:
            return {"error": str(e)}

    def _categories_with_count(self):
        """The saved category list, each entry given a live ``count`` of the
        templates currently resolving to it - computed fresh every call rather
        than stored, since a template's category can change under it (a hand-
        edited template.json) without any category action happening at all."""
        counts = {}
        for t in templates_registry.available():
            cat = t.get("category")
            counts[cat] = counts.get(cat, 0) + 1
        items = self.store.config.get("categories", {}).get("items", [])
        return [dict(c, count=counts.get(c.get("id"), 0)) for c in items]

    def list_categories(self):
        return {**self.store.state(), "categories": self._categories_with_count()}

    def save_category(self, cat):
        """Create or edit a category.

        Edit (an existing ``id``): ``name`` and ``default_template`` are both
        optional and only touched when present; a new ``default_template`` must
        resolve to a real template or the whole call is refused unchanged.

        Create (no matching ``id``): ``name`` and a *resolvable*
        ``default_template`` are both required - unlike edit, there is no
        existing default to fall back on. The new id is ``name`` slugified,
        deduplicated with a ``-2``, ``-3``, ... suffix against any collision:
        two categories sharing a display word (e.g. two teams both wanting
        "Notes") is a normal thing to want, not an error.
        """
        try:
            cat = cat or {}
            known_ids = {t["id"] for t in templates_registry.available()}
            items = self.store.config.setdefault("categories", {}).setdefault("items", [])
            cid = cat.get("id")
            existing = next((c for c in items if c.get("id") == cid), None) if cid else None
            if existing:
                name = str(cat.get("name") or "").strip()
                if name:
                    existing["name"] = name
                new_tpl = cat.get("default_template")
                if new_tpl:
                    if new_tpl not in known_ids:
                        return {"error": "Unknown template: %s" % new_tpl}
                    existing["default_template"] = new_tpl
            else:
                name = str(cat.get("name") or "").strip()
                if not name:
                    return {"error": "Give the category a name first."}
                default_template = cat.get("default_template")
                if not default_template or default_template not in known_ids:
                    return {"error": "Choose a valid default template for the new category."}
                slug = slugify(name)
                existing_ids = {c.get("id") for c in items}
                candidate, n = slug, 2
                while candidate in existing_ids:
                    candidate = "%s-%d" % (slug, n)
                    n += 1
                items.append({"id": candidate, "name": name, "default_template": default_template})
            self.store.save_config()
            self.controller.refresh_full()
            return {**self.store.state(), "categories": self._categories_with_count()}
        except Exception as e:
            return {"error": str(e)}

    def delete_category(self, id):
        """Refuses to delete the last remaining category. A missing id is a
        no-op rather than an error - deleting something already gone leaves
        the world in the state the caller wanted, so there is nothing to
        report as wrong."""
        try:
            items = self.store.config.get("categories", {}).get("items", [])
            if len(items) <= 1:
                return {"error": "Can't delete the last remaining category."}
            items[:] = [c for c in items if c.get("id") != id]
            self.store.save_config()
            self.controller.refresh_full()
            return {**self.store.state(), "categories": self._categories_with_count()}
        except Exception as e:
            return {"error": str(e)}

    def set_category_default(self, cat_id, template_id):
        try:
            items = self.store.config.get("categories", {}).get("items", [])
            cat = next((c for c in items if c.get("id") == cat_id), None)
            if not cat:
                return {"error": "Category not found."}
            if not any(t["id"] == template_id for t in templates_registry.available()):
                return {"error": "Unknown template: %s" % template_id}
            cat["default_template"] = template_id
            self.store.save_config()
            self.controller.refresh_full()
            return {**self.store.state(), "categories": self._categories_with_count()}
        except Exception as e:
            return {"error": str(e)}

    def template_demo(self, template_id):
        """A rendered sample report for one template, for a live preview
        before committing to it as a category default. Uses a fixed fixture
        (module-level ``_DEMO_TOPIC``/``_DEMO_ENTRIES``) so the preview looks
        the same for every template and never touches real data."""
        try:
            import pipeline
            manifest = templates_registry.load(template_id)
            refs, cites = Store._collect_refs(_DEMO_ENTRIES)
            markdown = pipeline.compose_markdown(_DEMO_TOPIC, _DEMO_ENTRIES, cites, refs=refs)
            values = pipeline.build_values(_DEMO_TOPIC, _DEMO_ENTRIES, refs, markdown, manifest, meta={})
            html = templates_registry.render_shell(manifest, values)
            return {"html": html}
        except Exception as e:
            return {"error": str(e)}

    def pdf_engines(self):
        try:
            import pdf_render
            found = pdf_render.available_engines()
            return {"engines": {k: bool(v) for k, v in found.items()}}
        except Exception as e:
            return {"error": str(e)}

    def test_llm(self, cfg):
        return llm.test_connection(cfg or {})

    def polish_entry(self, tid, eid):
        t = self.store.find_topic(tid)
        if not t:
            return {"error": "Topic not found."}
        e = next((x for x in t.get("entries", []) if x["id"] == eid), None)
        if not e:
            return {"error": "Point not found."}
        res = llm.polish_entry(self.store.config.get("llm") or {}, e.get("text", ""))
        if res.get("error"):
            return {"error": res["error"]}
        return {"text": res["content"].strip()}

    def draft_summary(self, tid):
        t = self.store.find_topic(tid)
        if not t:
            return {"error": "Topic not found."}
        entries = sorted(t.get("entries", []), key=lambda e: e.get("created") or "")
        if not entries:
            return {"error": "Nothing to summarize yet."}
        groups = {}
        for e in entries[:60]:
            groups.setdefault(e.get("subtopic") or "General", []).append(e.get("text", ""))
        block = "\n\n".join("[%s]\n- %s" % (k, "\n- ".join(v)) for k, v in groups.items())
        res = llm.draft_summary(self.store.config.get("llm") or {}, t.get("title", ""), block, 60)
        if res.get("error"):
            return {"error": res["error"]}
        return {"text": res["content"].strip()}

    def start_topic(self, title):
        r = self.store.start_topic(title)
        self.controller.refresh_full()
        return r

    def update_topic(self, tid, title):
        r = self.store.update_topic(tid, title)
        self.controller.refresh_full()
        return r

    def close_topic(self, tid):
        r = self.store.close_topic(tid)
        self.controller.refresh_full()
        return r

    def reopen_topic(self, tid):
        r = self.store.reopen_topic(tid)
        self.controller.refresh_full()
        return r

    def delete_topic(self, tid):
        r = self.store.delete_topic(tid)
        self.controller.refresh_full()
        return r

    def add_subtopic(self, tid, name):
        r = self.store.add_subtopic(tid, name)
        self.controller.refresh_full()
        return r

    def rename_subtopic(self, tid, old, new):
        r = self.store.rename_subtopic(tid, old, new)
        self.controller.refresh_full()
        return r

    def delete_subtopic(self, tid, name):
        r = self.store.delete_subtopic(tid, name)
        self.controller.refresh_full()
        return r

    def add_entry(self, tid, subtopic, text, source_link="", source_string="", image_data=None, sources=None, kind="claim"):
        r = self.store.add_entry(tid, subtopic, text, source_link, source_string, image_data, sources, kind)
        self.controller.refresh_full()
        return r

    def update_entry(self, tid, eid, fields):
        r = self.store.update_entry(tid, eid, fields)
        self.controller.refresh_full()
        return r

    def delete_entry(self, tid, eid):
        r = self.store.delete_entry(tid, eid)
        self.controller.refresh_full()
        return r

    def add_source(self, tid, eid, stype, value, note="", meta=None):
        r = self.store.add_source(tid, eid, stype, value, note, meta)
        self.controller.refresh_full()
        return r

    def set_source_meta(self, tid, eid, sid, meta):
        r = self.store.set_source_meta(tid, eid, sid, meta)
        self.controller.refresh_full()
        return r

    def lookup_doi(self, doi):
        """Fill a source's metadata from doi.org. Online, optional, best effort."""
        import citation
        return citation.lookup_doi(doi)

    def citation_styles(self):
        """The styles scientific mode can render, for the settings card."""
        import citation
        return {"styles": [{"id": k, "label": v[0], "hint": v[1]}
                           for k, v in citation.STYLES.items()],
                "fields": list(citation.META_FIELDS)}

    def delete_source(self, tid, eid, sid):
        r = self.store.delete_source(tid, eid, sid)
        self.controller.refresh_full()
        return r

    def save_image(self, tid, eid, data_url):
        r = self.store.save_image(tid, eid, data_url)
        self.controller.refresh_full()
        return r

    def export_topic(self, tid, options=None):
        r = self.store.export_topic(tid, options)
        self.controller.refresh_full()
        return r

    def export_topic_polished(self, tid, options=None):
        """AI writes the prose, code does everything else.

        The model is handed the same Markdown the deterministic export would have
        produced, and its output goes through the pipeline's citation gate before
        it is allowed anywhere near a template. If it fails that gate the pipeline
        silently falls back to the original points and says so in the result.
        """
        cfg = self.store.config.get("llm") or {}
        if not cfg.get("enabled") or not (cfg.get("api_key") or "").strip():
            return {"error": "AI is not configured. Open Settings - AI assist and add your key."}
        payload = self.store.export_payload(tid, options)
        if not payload:
            return {"error": "Nothing to polish yet."}
        res = llm.polish_report(cfg, payload["title"], payload["markdown"],
                                science=self.store._science(options))
        if res.get("error"):
            return {"error": res["error"]}
        polished = (res.get("content") or "").strip()
        if not polished:
            return {"error": "The model returned no content."}
        r = self.store.export_topic_polished(tid, polished, options)
        self.controller.refresh_full()
        return r

    def delete_export(self, folder):
        return self.store.delete_export(folder)

    def open_url(self, url):
        try:
            webbrowser.open(url)
        except Exception:
            pass
        return {}

    def open_path(self, path):
        try:
            os.startfile(path)
        except Exception:
            pass
        return {}

    def hide_popup(self):
        self.controller.hide_popup()
        return {}

    def show_popup(self):
        self.controller.show_popup()
        return {}

    def show_full(self):
        """Bring the main window forward. The popup's "Open app" button calls
        this; it used to call a method that did not exist, so the button silently
        did nothing."""
        self.controller.show_full()
        return {}

    def hide_menu(self):
        return {}

    def tray_action(self, action):
        if action == "open":
            self.controller.show_full()
        elif action == "capture":
            self.controller.show_popup()
        elif action == "hide":
            self.controller.hide_all()
        elif action == "quit":
            self.controller.quit()
        return {}


class Controller:
    _serializable = False

    def __init__(self):
        self.store = Store()
        self.popup = None
        self.full = None
        self.popup_hwnd = 0
        self.full_hwnd = 0
        # What Ctrl+Alt+V last read off the clipboard, until the popup
        # collects it. Written on the hotkey thread, read on the JS-bridge
        # thread, hence the lock.
        self._pending_clip = None
        self._clip_lock = threading.Lock()
        self.popup_visible = True
        self.full_visible = False
        self.quitting = False
        self.hotkey = None
        self.clipboard_hotkey = None
        self.asr_logger = None
        # Guards apply_asr()'s read-modify-write of asr_logger: apply_asr is
        # reachable concurrently from the tray thread (_toggle_voice_logging)
        # and the pywebview JS-bridge thread (Api.save_asr). Without this,
        # two near-simultaneous calls can each stop the same old logger, then
        # each start a new one - the second overwrites self.asr_logger and
        # the first's VoiceLogger is orphaned (nothing left holds a reference
        # to stop it), leaving the microphone open after the user believes
        # voice logging is off.
        self._asr_lock = threading.Lock()
        self.telegram_bridge = None
        self.telegram_state = "off"
        self.telegram_detail = ""
        # Mirrors _asr_lock: apply_telegram is reachable concurrently from
        # the pywebview JS-bridge thread (Api.save_telegram/telegram_unpair)
        # and from startup() - same orphaned-thread risk as apply_asr if
        # unsynchronized.
        self._telegram_lock = threading.Lock()
        self.api = Api(self.store, self)
        self.tray = None
        self.voice_item = None

    def _tray_icon(self, light):
        # The tray lives on the taskbar, not on Trailmark's own surface, so it
        # follows Windows rather than the app's theme: a dark silhouette on a
        # light taskbar, a white one on a dark taskbar. The amber mark is what
        # falls back if those assets are missing.
        p = asset_path("tray-light.ico" if light else "tray-dark.ico")
        return p if p.exists() else asset_path("app.ico")

    def apply_hotkey(self, mods=None, key=None):
        cfg = self.store.config.get("hotkey") or {}
        mods = mods or cfg.get("modifiers") or ["ctrl", "alt"]
        key = key or cfg.get("key") or "P"
        if self.hotkey:
            self.hotkey.stop()
            self.hotkey = None
        try:
            self.hotkey = HotkeyListener(mods, key, self.toggle_popup)
            self.hotkey.start()
        except ValueError:
            self.hotkey = None

    def apply_clipboard_hotkey(self, mods=None, key=None):
        """Mirrors apply_hotkey, but for the independent clipboard-capture
        combo - a second HotkeyListener instance (hotkey_id=0x4344, distinct
        from the capture hotkey's 0x4343) that coexists with it. Registered
        whenever config.clipboard.enabled is set, which is the default."""
        cfg = self.store.config.get("clipboard") or {}
        if self.clipboard_hotkey:
            self.clipboard_hotkey.stop()
            self.clipboard_hotkey = None
        if not cfg.get("enabled"):
            return
        mods = mods or cfg.get("modifiers") or ["ctrl", "alt"]
        key = key or cfg.get("key") or "V"
        try:
            self.clipboard_hotkey = HotkeyListener(mods, key, self.on_clipboard_hotkey,
                                                   hotkey_id=0x4344)
            self.clipboard_hotkey.start()
        except ValueError:
            self.clipboard_hotkey = None

    def apply_asr(self):
        """Mirrors apply_clipboard_hotkey: stop whatever's running, then start
        fresh from current config if enabled. Off by default (config.asr.enabled),
        so the common case is just stopping any previous logger and leaving it
        stopped.

        Serialized on ``self._asr_lock`` - this can be called concurrently
        from the tray thread and from the pywebview JS-bridge thread, and an
        unsynchronized read-modify-write of ``self.asr_logger`` could orphan
        a running capture thread (see the lock's own comment in __init__)."""
        with self._asr_lock:
            cfg = self.store.config.get("asr") or {}
            if self.asr_logger:
                try:
                    self.asr_logger.stop()
                except Exception:
                    traceback.print_exc()
                self.asr_logger = None
            if not cfg.get("enabled"):
                self.push_asr_state("off", "")
                return
            self.asr_logger = asr.VoiceLogger(cfg, self.on_asr_utterance, self.push_asr_state)
            try:
                self.asr_logger.start()
            except Exception:
                traceback.print_exc()
                self.push_asr_state("error", "Could not start voice logging.")

    def on_asr_utterance(self, wav_bytes):
        """Runs on VoiceLogger's own capture thread, not the UI thread — same
        cross-thread discipline as on_clipboard_hotkey/push_asr_state."""
        cfg = self.store.config.get("asr") or {}
        self.push_asr_state("transcribing", "")
        try:
            result = asr.transcribe(cfg, wav_bytes)
        except Exception:
            traceback.print_exc()
            self.push_asr_state("error", "Transcription failed.")
            return
        if result.get("error"):
            self.push_asr_state("error", result["error"])
            return
        self._log_asr_text(result.get("text") or "")

    def _log_asr_text(self, text):
        """Files one transcribed utterance into the last open topic. Split out
        from on_asr_utterance so a test can drive the entry-creation path
        without a real transcription call. Re-verifies the topic is still open
        immediately before writing, exactly like on_clipboard_hotkey does (same
        race: time passes between last_open_topic() and add_entry(), and the UI
        thread could close the topic in between). A "logged" push is not
        terminal - VoiceLogger emits "listening" again on its own once capture
        resumes."""
        text = (text or "").strip()
        if not text:
            self.push_asr_state("listening", "")
            return
        topic = self.store.last_open_topic()
        if topic is None:
            self.push_asr_state("no_topic", "No open topic")
            return
        t = self.store.find_topic(topic["id"])
        if not t or t.get("status") != "open":
            self.push_asr_state("no_topic", "No open topic")
            return
        try:
            r = self.store.add_entry(topic["id"], "", text, kind="note")
        except Exception:
            traceback.print_exc()
            self.push_asr_state("error", "Could not log the transcription.")
            return
        if r.get("error"):
            self.push_asr_state("error", r["error"])
            return
        self.refresh_full()
        detail = text[:120] + ("…" if len(text) > 120 else "")
        self.push_asr_state("logged", detail)

    def push_asr_state(self, state, detail=""):
        """Called from VoiceLogger's capture thread (not the UI thread) as well
        as from the UI thread itself (apply_asr's off-path). detail is
        JSON-encoded rather than string-formatted into the JS so a transcript
        snippet or an error message can never break out of the argument list —
        same discipline as push_telegram_state. Never pass the API key as
        detail, under any state.
        """
        try:
            js = "asrState(%s,%s)" % (json.dumps(state), json.dumps(detail or ""))
        except Exception:
            return
        try:
            if self.full is not None and self.full_visible:
                self.full.evaluate_js(js)
        except Exception:
            pass
        if hasattr(self, "_update_voice_tray_label"):
            try:
                self._update_voice_tray_label(state)
            except Exception:
                pass

    def apply_telegram(self):
        """Mirrors apply_asr: stop whatever's running, then start fresh from
        current config if enabled and a token is actually available (config
        or .env). Idempotent and safe to call repeatedly - the common case
        (disabled, or already running with unchanged config) is just
        stopping any previous bridge and, if enabled, starting a new one.

        Serialized on self._telegram_lock for the same read-modify-write
        race apply_asr's own lock guards against (see its comment in
        __init__) - reachable concurrently from the JS-bridge thread
        (save_telegram/telegram_unpair) and from startup().
        """
        with self._telegram_lock:
            cfg = self.store.config.get("telegram") or {}
            if self.telegram_bridge:
                try:
                    self.telegram_bridge.stop()
                except Exception:
                    traceback.print_exc()
                self.telegram_bridge = None
            if not cfg.get("enabled"):
                self.push_telegram_state("off", "")
                return
            token, _source = telegram_bridge.load_token(self.store.config)
            if not token:
                self.push_telegram_state("error", "No bot token configured.")
                return
            transport = telegram_bridge.UrllibTransport(token)
            bridge = telegram_bridge.TelegramBridge(
                transport, lambda: self.store.config, self._telegram_merge_cfg,
                self.push_telegram_state, self.on_telegram_message,
                get_open_topics=self.store.open_topics)
            try:
                bridge.start()
            except Exception:
                traceback.print_exc()
                self.push_telegram_state("error", "Could not start the Telegram bridge.")
                return
            self.telegram_bridge = bridge
            if cfg.get("chat_id"):
                self.push_telegram_state("paired", cfg.get("username") or "")
            else:
                self.push_telegram_state("waiting", "")

    def _telegram_merge_cfg(self, updates):
        """The save_cfg callback handed to TelegramBridge: merges the given
        fields (chat_id/username on pairing, topic_id on a /topic switch)
        into config["telegram"] and persists. Runs on the bridge's own
        polling thread, not the UI thread - evaluate_js calls downstream
        (via push_telegram_state/refresh_full) follow the same
        try/except-guarded, full_visible-gated discipline as every other
        cross-thread call in this file."""
        cfg = dict(self.store.config.get("telegram") or {})
        cfg.update(updates or {})
        self.store.config["telegram"] = cfg
        self.store.save_config()
        self.refresh_full()
        if "chat_id" in (updates or {}):
            if cfg.get("chat_id"):
                self.push_telegram_state("paired", cfg.get("username") or "")
            else:
                self.push_telegram_state("waiting", "")

    def on_telegram_message(self, kind, payload):
        """The on_message callback wired into TelegramBridge by
        apply_telegram. Runs on the bridge's own polling thread, not the UI
        thread - same cross-thread discipline as on_clipboard_hotkey /
        on_asr_utterance.

        Topic resolution mirrors _log_asr_text: prefer
        config.telegram.topic_id while that topic is still open, else fall
        back to the last open topic; report "no open topic" and log nothing
        if neither resolves. kind ("note"/"link"/"photo") is the message
        shape TelegramBridge classified, not point_store's claim/note/quote
        entry kind - a link keeps the same default entry kind ("claim") the
        T11 clipboard-hotkey link path uses, and only text/photo are filed
        as point_store "note" entries, for consistency with that existing
        capture path.

        Unlike the ASR/clipboard paths, this always returns a reply string -
        TelegramBridge sends it back to the chat as the sender's only
        feedback that anything happened.
        """
        cfg = self.store.config.get("telegram") or {}
        topic = None
        tid = cfg.get("topic_id")
        if tid:
            t = self.store.find_topic(tid)
            if t and t.get("status") == "open":
                topic = t
        if topic is None:
            topic = self.store.last_open_topic()
        if topic is None:
            self.push_telegram_state("no_topic", "No open topic")
            return "No open topic on the desktop — start one first"

        text = payload.get("text", "")
        try:
            if kind == "link":
                r = self.store.add_entry(topic["id"], "", text,
                                         source_link=payload.get("source_link", ""))
            elif kind == "photo":
                r = self.store.add_entry(topic["id"], "", text,
                                         sources=payload.get("sources"), kind="note")
            else:
                r = self.store.add_entry(topic["id"], "", text, kind="note")
        except Exception:
            traceback.print_exc()
            self.push_telegram_state("error", "Could not log the message.")
            return "Could not log that — try again."

        if r.get("error"):
            self.push_telegram_state("error", r["error"])
            return "Could not log that: %s" % r["error"]

        self.refresh_full()
        detail = text[:120] + ("…" if len(text) > 120 else "")
        self.push_telegram_state("logged", detail)
        return "Logged to '%s'" % topic.get("title", "")

    def push_telegram_state(self, state, detail=""):
        """Called from TelegramBridge's polling thread as well as from the
        UI thread itself (apply_telegram's off/error paths) - same
        discipline as push_asr_state: both args are JSON-encoded
        independently so a topic title or error string can never break out
        of the argument list, and the whole call is wrapped in try/except.
        Never pass the bot token as detail, under any state. Also records
        state/detail on the controller so Api.telegram_status can answer
        without a push channel of its own."""
        self.telegram_state = state
        self.telegram_detail = detail or ""
        try:
            js = "telegramState(%s,%s)" % (json.dumps(state), json.dumps(detail or ""))
        except Exception:
            return
        try:
            if self.full is not None and self.full_visible:
                self.full.evaluate_js(js)
        except Exception:
            pass

    def on_clipboard_hotkey(self):
        """Ctrl+Alt+V (by default): read whatever was last copied and hand it
        to the quick-capture popup as a pending source. Nothing is written
        to the store - the hotkey fills the form, the user writes the point
        and logs it. Fires on the Win32 hotkey message-loop thread, same as
        toggle_popup, so the pywebview calls below are direct and guarded.

        The payload is parked on the controller and pulled by the popup
        (Api.take_clipboard_capture) rather than pushed through
        evaluate_js: an image is a multi-megabyte data URL, and a bridge
        return is the path that already carries those for the per-row
        paste buttons."""
        try:
            data = clipboard.read()
        except Exception:
            data = {"type": "none", "value": None, "meta": {}}
        kind = data.get("type") or "none"
        value = data.get("value") if kind != "none" else None
        if kind == "text" and isinstance(value, str):
            value = value[:2000]
        with self._clip_lock:
            self._pending_clip = {"type": kind, "value": value}
        self.show_popup()
        try:
            if self.popup is not None:
                self.popup.evaluate_js("clipboardCaptured()")
        except Exception:
            pass

    def take_clipboard_capture(self):
        """Hand the parked hotkey payload to the popup, once. A second call
        (or a call with nothing parked) answers type "none" so the popup
        can never attach the same capture twice."""
        with self._clip_lock:
            data, self._pending_clip = self._pending_clip, None
        return data or {"type": "none", "value": None}

    def toggle_popup(self):
        if self.popup is None:
            return
        if self.quitting:
            return
        try:
            if self.popup_visible:
                self.popup.hide()
                self.popup_visible = False
            else:
                _set_topmost(self.popup_hwnd, True)
                self.popup.show()
                self.popup_visible = True
                self.popup.evaluate_js("popupShown()")
        except Exception:
            pass

    def hide_popup(self):
        if self.popup is None or not self.popup_visible:
            return
        try:
            self.popup.hide()
            self.popup_visible = False
        except Exception:
            pass

    def show_popup(self):
        if self.popup is None:
            return
        try:
            _set_topmost(self.popup_hwnd, True)
            self.popup.show()
            self.popup_visible = True
            self.popup.evaluate_js("popupShown()")
        except Exception:
            pass

    def show_full(self):
        if self.full is None:
            return
        # pywebview show must run on UI thread — evaluate safely from any thread
        def _do():
            try:
                self.full.show()
                self.full_visible = True
                try:
                    # bring to front and restore if minimized
                    self.full.restore()
                except Exception:
                    pass
                # topmost-then-not is the reliable "bring to front" on Windows
                _set_topmost(self.full_hwnd, True)
                _set_topmost(self.full_hwnd, False)
                try:
                    self.full.evaluate_js("window.focus();")
                except Exception:
                    pass
            except Exception:
                pass
        # webview windows are thread-safe via evaluate, but show must be direct; try both
        try:
            _do()
        except Exception:
            try:
                # fallback: schedule via evaluate_js
                self.full.evaluate_js("setTimeout(()=>window.focus(), 50);")
            except Exception:
                pass

    def refresh_full(self):
        if self.full is None:
            return
        try:
            self.full.evaluate_js("refreshFromBridge()")
        except Exception:
            pass

    def hide_all(self):
        self.hide_popup()
        try:
            if self.full:
                self.full.hide()
                self.full_visible = False
        except Exception:
            pass

    def quit(self):
        self.quitting = True
        try:
            if self.tray:
                self.tray.stop()
        except Exception:
            pass
        if self.hotkey:
            try:
                self.hotkey.stop()
            except Exception:
                pass
        if self.clipboard_hotkey:
            try:
                self.clipboard_hotkey.stop()
            except Exception:
                pass
        if self.asr_logger:
            try:
                self.asr_logger.stop()
            except Exception:
                pass
        if self.telegram_bridge:
            try:
                self.telegram_bridge.stop()
            except Exception:
                pass
        for w in (self.popup, self.full):
            if w is None:
                continue
            try:
                w.destroy()
            except Exception:
                pass
        threading.Timer(1.5, lambda: os._exit(0), ).start()

    def window_bg(self):
        """The colour the native window paints before the page has painted.

        pywebview fixes this at creation time, so it cannot follow a theme
        change later - but it can at least start on the right side. Getting it
        wrong is a dark flash on every launch for a light-theme user.
        """
        pref = ((self.store.config.get("appearance") or {}).get("theme") or "system")
        if pref == "light":
            return "#f6f1e8"
        if pref == "dark":
            return "#0b0f16"
        return "#f6f1e8" if system_prefers_light() else "#0b0f16"

    def build_windows(self):
        bg = self.window_bg()
        self.popup = webview.create_window(
            "Trailmark · Quick capture", html=POPUP_HTML, js_api=self.api,
            width=POPUP_W, height=POPUP_H, frameless=True, easy_drag=False,
            on_top=True, resizable=False, hidden=True, background_color=bg)
        self.popup_visible = False
        self.full = webview.create_window(
            "Trailmark", html=MAIN_HTML, js_api=self.api,
            width=MAIN_W, height=MAIN_H, min_size=(900, 620), background_color=bg)

        def on_popup_closing():
            if self.quitting:
                return True
            self.popup_visible = False
            return False

        def on_full_closing():
            if self.quitting:
                return True
            try:
                self.full.hide()
                self.full_visible = False
            except Exception:
                pass
            return False

        def on_full_shown():
            self.full_hwnd = self._native_hwnd(self.full)
            self.refresh_full()

        def on_popup_shown():
            # Runs on the UI thread, which is the only place reading the
            # form's Handle is free of cross-thread traffic. `hidden=True`
            # windows still fire this once, during creation.
            self.popup_hwnd = self._native_hwnd(self.popup)

        self.popup.events.closing += on_popup_closing
        self.popup.events.shown += on_popup_shown
        self.full.events.closing += on_full_closing
        self.full.events.shown += on_full_shown

    @staticmethod
    def _native_hwnd(window):
        try:
            return int(window.native.Handle.ToInt64())
        except Exception:
            return 0

    def build_tray(self):
        """The notification-area icon, with the menu Trailmark draws itself.

        The actions run on the tray thread, so `quit` gets its own thread -
        it tears that very thread down."""
        item = traymenu.Item
        asr_enabled = bool((self.store.config.get("asr") or {}).get("enabled"))
        # No check-glyph exists in traymenu's _draw_glyph yet (mark/window/
        # capture/hide/power only) — drawing one is real icon-drawing surface,
        # out of scope here, so this row ships glyph=None (n/a with a reason,
        # not a shortcut) until that glyph is added.
        self.voice_item = item(self._voice_label(asr_enabled),
                                self._toggle_voice_logging, glyph=None)
        items = [
            item("Open Trailmark", self.show_full, glyph="window", tone="accent"),
            item("Quick capture", self.show_popup, glyph="capture"),
            self.voice_item,
            item("Hide windows", self.hide_all, glyph="hide"),
            item(kind="sep"),
            item("Quit", lambda: threading.Thread(target=self.quit, daemon=True).start(),
                 glyph="power", tone="danger"),
        ]
        self.tray = traymenu.Tray(
            "Trailmark", items,
            icon_for_theme=self._tray_icon,
            prefers_light=system_prefers_light,
            on_activate=self.show_full)

    @staticmethod
    def _voice_label(enabled):
        return "Voice logging: %s" % ("On" if enabled else "Off")

    def _toggle_voice_logging(self):
        """Tray click handler - runs on the tray's own thread, same as every
        other tray action here. Flips asr.enabled through the same save_asr
        path the Settings UI uses, so config persistence and the apply_asr()
        side effect stay in exactly one place."""
        cfg = dict(self.store.config.get("asr") or {})
        cfg["enabled"] = not cfg.get("enabled")
        self.api.save_asr(cfg)   # save_asr already calls apply_asr() + refresh_full()

    def _update_voice_tray_label(self, state):
        """Called from push_asr_state (main-thread or ASR-capture-thread) on
        every ASR state change, so the tray label tracks reality even when
        the state changed for a reason other than a tray click (an error, or
        the Settings UI toggling it). Ships the minimum bar only: On/Off from
        config. Richer state text ("Listening"/"Transcribing...") is not
        wired in - `state` is accepted but unused for now."""
        if not hasattr(self, "voice_item") or self.voice_item is None:
            return
        try:
            enabled = bool((self.store.config.get("asr") or {}).get("enabled"))
            self.voice_item.label = self._voice_label(enabled)
        except Exception:
            pass

    def run(self):
        self.build_windows()
        self.build_tray()

        def startup():
            try:
                self.apply_hotkey()
            except Exception:
                traceback.print_exc()
            try:
                self.apply_clipboard_hotkey()
            except Exception:
                traceback.print_exc()
            try:
                self.apply_asr()
            except Exception:
                traceback.print_exc()
            try:
                self.apply_telegram()
            except Exception:
                traceback.print_exc()
            try:
                t = threading.Thread(target=self.tray.run, daemon=True)
                t.start()
            except Exception:
                traceback.print_exc()
            # windowed bootloader can leave main hidden on some builds; ensure it's shown
            try:
                self.show_full()
            except Exception:
                traceback.print_exc()

        try:
            # Hand pywebview the icon explicitly. Left to itself it calls
            # ExtractIconW on sys.executable, which is the right file but the
            # wrong guarantee - under a onefile build that is the bootloader,
            # and the window icon is then whatever the shell has cached for it.
            icon = asset_path("app.ico")
            webview.start(func=startup, icon=str(icon) if icon.exists() else None)
        except Exception as e:
            # Fallback: log to file and try again without tray
            try:
                log_path = data_dir() / "trailmark_crash.log"
                log_path.write_text(traceback.format_exc(), encoding="utf-8")
            except Exception:
                pass
            # Try to show main directly without tray
            try:
                self.show_full()
            except Exception:
                pass
            raise


def main():
    if os.name != "nt":
        print("Trailmark currently supports Windows only.")
        return
    try:
        c = Controller()
        if not single.ensure_single_instance(c.show_full):
            return
        c.run()
    except Exception:
        try:
            log_path = data_dir() / "trailmark_crash.log"
            log_path.write_text(traceback.format_exc(), encoding="utf-8")
        except Exception:
            pass
        raise


if __name__ == "__main__":
    main()