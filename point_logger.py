import os
import sys
import threading
import webbrowser

import pystray
import webview
from PIL import Image

from brand import ICON_DATA_URI, asset_path
from hotkey import HotkeyListener
from point_store import Store
from ui import MAIN_HTML, POPUP_HTML

import llm

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
        return self.store.state()

    def save_llm(self, cfg):
        merged = dict(self.store.config.get("llm") or {})
        merged.update(cfg or {})
        self.store.config["llm"] = merged
        self.store.save_config()
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
        return self.store.start_topic(title)

    def update_topic(self, tid, title):
        return self.store.update_topic(tid, title)

    def close_topic(self, tid):
        return self.store.close_topic(tid)

    def reopen_topic(self, tid):
        return self.store.reopen_topic(tid)

    def delete_topic(self, tid):
        return self.store.delete_topic(tid)

    def add_subtopic(self, tid, name):
        return self.store.add_subtopic(tid, name)

    def rename_subtopic(self, tid, old, new):
        return self.store.rename_subtopic(tid, old, new)

    def delete_subtopic(self, tid, name):
        return self.store.delete_subtopic(tid, name)

    def add_entry(self, tid, subtopic, text, source_link="", source_string="", image_data=None):
        return self.store.add_entry(tid, subtopic, text, source_link, source_string, image_data)

    def update_entry(self, tid, eid, fields):
        return self.store.update_entry(tid, eid, fields)

    def delete_entry(self, tid, eid):
        return self.store.delete_entry(tid, eid)

    def add_source(self, tid, eid, stype, value, note=""):
        return self.store.add_source(tid, eid, stype, value, note)

    def delete_source(self, tid, eid, sid):
        return self.store.delete_source(tid, eid, sid)

    def save_image(self, tid, eid, data_url):
        return self.store.save_image(tid, eid, data_url)

    def export_topic(self, tid):
        return self.store.export_topic(tid)

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


class Controller:
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
        try:
            self.full.show()
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
            "OpenPointLogger · Quick capture", html=POPUP_HTML, js_api=self.api,
            width=POPUP_W, height=POPUP_H, frameless=True, easy_drag=True,
            on_top=True, resizable=False, background_color="#0b0f16")
        self.full = webview.create_window(
            "OpenPointLogger", html=MAIN_HTML, js_api=self.api,
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

        self.popup.events.closing += on_popup_closing
        self.full.events.closing += on_full_closing

    def build_tray(self):
        def open_full(icon, item):
            self.show_full()

        def open_popup(icon, item):
            self.show_popup()

        def hide_all(icon, item):
            self.hide_all()

        def do_quit(icon, item):
            threading.Thread(target=self.quit, daemon=True).start()

        menu = pystray.Menu(
            pystray.MenuItem("Open OpenPointLogger", open_full),
            pystray.MenuItem("Quick capture", open_popup),
            pystray.MenuItem("Hide windows", hide_all),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", do_quit),
        )
        self.tray = pystray.Icon("OpenPointLogger", self._icon_image(), "OpenPointLogger", menu)

    def run(self):
        self.build_windows()
        self.build_tray()

        def startup():
            self.apply_hotkey()
            try:
                self.popup.hide()
                self.popup_visible = False
            except Exception:
                pass
            t = threading.Thread(target=self.tray.run, daemon=True)
            t.start()

        webview.start(func=startup)


def main():
    if os.name != "nt":
        print("OpenPointLogger currently supports Windows only.")
        return
    c = Controller()
    c.run()


if __name__ == "__main__":
    main()