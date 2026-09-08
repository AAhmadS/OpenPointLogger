import os
import sys
import threading
import traceback
import webbrowser

import webview

from brand import ICON_DATA_URI, asset_path
from hotkey import HotkeyListener
from point_store import Store, data_dir
from ui import MAIN_HTML, POPUP_HTML

import llm
import single
import traymenu

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
            import templates_registry
            d = templates_registry.user_dir()
            d.mkdir(parents=True, exist_ok=True)
            os.startfile(str(d))
            return {"path": str(d)}
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
        self.popup_visible = True
        self.quitting = False
        self.hotkey = None
        self.api = Api(self.store, self)
        self.tray = None

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
                self.popup.on_top = True
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
            self.popup.on_top = True
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
                try:
                    # bring to front and restore if minimized
                    self.full.restore()
                except Exception:
                    pass
                try:
                    self.full.minimize = False
                except Exception:
                    pass
                try:
                    self.full.on_top = True
                    self.full.on_top = False
                except Exception:
                    pass
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
            width=POPUP_W, height=POPUP_H, frameless=True, easy_drag=True,
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
            except Exception:
                pass
            return False

        def on_full_shown():
            self.refresh_full()

        self.popup.events.closing += on_popup_closing
        self.full.events.closing += on_full_closing
        self.full.events.shown += on_full_shown

    def build_tray(self):
        """The notification-area icon, with the menu Trailmark draws itself.

        The actions run on the tray thread, so `quit` gets its own thread -
        it tears that very thread down."""
        item = traymenu.Item
        items = [
            item("Open Trailmark", self.show_full, glyph="window", tone="accent"),
            item("Quick capture", self.show_popup, glyph="capture"),
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

    def run(self):
        self.build_windows()
        self.build_tray()

        def startup():
            try:
                self.apply_hotkey()
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