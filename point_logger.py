import os
import sys
import threading
import traceback
import webbrowser

import pystray
import webview
from PIL import Image

from brand import ICON_DATA_URI, asset_path
from hotkey import HotkeyListener
from point_store import Store
from ui import MAIN_HTML, POPUP_HTML

import llm
import single

POPUP_HTML = POPUP_HTML.replace("__ICON__", ICON_DATA_URI)
MAIN_HTML = MAIN_HTML.replace("__ICON__", ICON_DATA_URI)

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
        merged = dict(self.store.config.get("llm") or {})
        merged.update(cfg or {})
        self.store.config["llm"] = merged
        self.store.save_config()
        self.controller.refresh_full()
        return self.store.state()

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

    def add_entry(self, tid, subtopic, text, source_link="", source_string="", image_data=None, sources=None):
        r = self.store.add_entry(tid, subtopic, text, source_link, source_string, image_data, sources)
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

    def add_source(self, tid, eid, stype, value, note=""):
        r = self.store.add_source(tid, eid, stype, value, note)
        self.controller.refresh_full()
        return r

    def delete_source(self, tid, eid, sid):
        r = self.store.delete_source(tid, eid, sid)
        self.controller.refresh_full()
        return r

    def save_image(self, tid, eid, data_url):
        r = self.store.save_image(tid, eid, data_url)
        self.controller.refresh_full()
        return r

    def export_topic(self, tid):
        return self.store.export_topic(tid)

    def export_topic_polished(self, tid):
        # Build payload for AI, call polish_report, then render polished HTML
        t = self.store.find_topic(tid)
        if not t:
            return {"error": "Topic not found."}
        cfg = self.store.config.get("llm") or {}
        if not cfg.get("enabled") or not (cfg.get("api_key") or "").strip():
            return {"error": "AI is not configured. Open Settings → AI assist and add your key."}
        entries = sorted(t.get("entries", []), key=lambda e: e.get("created") or "")
        if not entries:
            return {"error": "Nothing to polish yet."}
        refs, cites = self.store._collect_refs(entries)
        # payload: each entry as text + [n] citations
        payload_lines = []
        for e in entries:
            nums = cites.get(e["id"], [])
            cite = " ".join("[%d]" % n for n in nums) if nums else ""
            payload_lines.append("- (%s) %s %s" % (e.get("subtopic") or "General", e.get("text","").strip(), cite))
        payload = "\n".join(payload_lines[:80])
        res = llm.polish_report(cfg, t.get("title",""), payload)
        if res.get("error"):
            return {"error": res["error"]}
        polished = res.get("content","").strip()
        if not polished:
            return {"error": "AI returned no content."}
        return self.store.export_topic_polished(tid, polished)

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

    def _icon_image(self):
        icon_path = asset_path("icon-64.png")
        if icon_path.exists():
            try:
                return Image.open(icon_path).convert("RGBA")
            except Exception:
                pass
        img = Image.new("RGBA", (64, 64), (11, 15, 22, 255))
        return img

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

    def build_windows(self):
        self.popup = webview.create_window(
            "Trailmark · Quick capture", html=POPUP_HTML, js_api=self.api,
            width=POPUP_W, height=POPUP_H, frameless=True, easy_drag=True,
            on_top=True, resizable=False, hidden=True, background_color="#0b0f16")
        self.popup_visible = False
        self.full = webview.create_window(
            "Trailmark", html=MAIN_HTML, js_api=self.api,
            width=MAIN_W, height=MAIN_H, min_size=(900, 620), background_color="#0b0f16")

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
        def open_full(icon, item):
            self.show_full()

        def open_popup(icon, item):
            self.show_popup()

        def hide_all(icon, item):
            self.hide_all()

        def do_quit(icon, item):
            threading.Thread(target=self.quit, daemon=True).start()

        # Keep a native menu as fallback (hidden if chic menu works) — but we will intercept RMB
        menu = pystray.Menu(
            pystray.MenuItem("Open Trailmark", open_full),
            pystray.MenuItem("Quick capture", open_popup),
            pystray.MenuItem("Hide windows", hide_all),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", do_quit),
        )
        self.tray = pystray.Icon("Trailmark", self._icon_image(), "Trailmark", menu)

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
            webview.start(func=startup)
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