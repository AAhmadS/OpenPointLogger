"""Headless test of point_logger's clipboard-hotkey controller path.

Exercises Controller.on_clipboard_hotkey() / take_clipboard_capture() and
Api.save_clipboard() against a temp-dir Store, a monkeypatched
clipboard.read(), and a monkeypatched HotkeyListener.probe - no real Win32
hotkey registration or webview window is ever touched. A bare
point_logger.Controller() degrades harmlessly here: self.popup and self.full
both default to None, and every pywebview call in show_popup is already
wrapped in try/except and short-circuits cleanly on None - so this never
needs a real webview window, and this file never builds one.

The contract under test: the hotkey never writes to the store. It parks
what it read, opens the popup, and the popup collects the payload exactly
once through the bridge.

Run:  PYTHONPATH=. .venv/Scripts/python.exe tests/test_clipboard_hotkey.py
"""

import base64
import pathlib
import sys
import tempfile

import point_store as ps

# Patch point_store's module globals to a temp dir BEFORE constructing
# anything - point_logger imports Store from point_store but only
# constructs it lazily inside Controller.__init__ (self.store = Store()),
# so patch-then-import-then-construct is safe.
tmp = pathlib.Path(tempfile.mkdtemp(prefix="opl_test_"))
ps.BASE_DIR = tmp
ps.DATA_FILE = tmp / "points.json"
ps.CONFIG_FILE = tmp / "config.json"
ps.ATTACH_DIR = tmp / "attachments"
ps.EXPORT_DIR = tmp / "exports"

import point_logger  # noqa: E402
import clipboard  # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + name + ((" - " + str(detail)) if detail else ""))
    if not cond:
        FAILS.append(name)


controller = point_logger.Controller()
store = controller.store
api = point_logger.Api(store, controller)

shows = []
controller.show_popup = lambda: shows.append(True)


def _all_entries():
    return [e for t in store.state()["topics"] for e in (t.get("entries") or [])]


# --- 1. text: parked, popup opened, nothing logged, collected once ---------------

r = store.start_topic("T")
tid = r["topics"][0]["id"]

shows.clear()
clipboard.read = lambda: {"type": "text", "value": "x" * 2500, "meta": {}}
controller.on_clipboard_hotkey()
check("text: no entry was written to the store", _all_entries() == [], _all_entries())
check("text: the popup was shown", shows == [True], shows)
got = api.take_clipboard_capture()
check("text: capture collected with type 'text'", got.get("type") == "text", got)
check("text: trimmed to exactly 2000 chars", len(got.get("value") or "") == 2000,
      len(got.get("value") or ""))
again = api.take_clipboard_capture()
check("text: a second collect answers 'none' (never attached twice)",
      again.get("type") == "none", again)

# --- 2. link -------------------------------------------------------------------

shows.clear()
clipboard.read = lambda: {"type": "link", "value": "https://example.org/path", "meta": {}}
controller.on_clipboard_hotkey()
got = api.take_clipboard_capture()
check("link: capture is the URL, typed 'link'",
      got == {"type": "link", "value": "https://example.org/path"}, got)
check("link: still nothing in the store", _all_entries() == [], _all_entries())

# --- 3. image ------------------------------------------------------------------

png = base64.b64encode(
    bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
        "0000000d49444154789c6360000002000100ffff03000006000557bfabd4000000"
        "0049454e44ae426082"
    )
).decode()
data_url = "data:image/png;base64," + png

shows.clear()
clipboard.read = lambda: {"type": "image", "value": data_url, "meta": {}}
controller.on_clipboard_hotkey()
got = api.take_clipboard_capture()
check("image: capture is the data URL, typed 'image'",
      got == {"type": "image", "value": data_url}, got)

# --- 4. empty clipboard: popup still opens, capture says 'none' -------------------

shows.clear()
clipboard.read = lambda: {"type": "none", "value": None, "meta": {}}
controller.on_clipboard_hotkey()
check("empty: the popup was shown anyway", shows == [True], shows)
got = api.take_clipboard_capture()
check("empty: capture answers 'none' with no value",
      got.get("type") == "none" and got.get("value") is None, got)

# --- 4b. no open topic is not the hotkey's problem: it still parks the capture ----

store.close_topic(tid)
shows.clear()
clipboard.read = lambda: {"type": "text", "value": "hello", "meta": {}}
controller.on_clipboard_hotkey()
check("no-open-topic: popup shown, capture parked",
      shows == [True] and api.take_clipboard_capture() == {"type": "text", "value": "hello"})
check("no-open-topic: nothing was created", _all_entries() == [], _all_entries())

# --- 4c. clipboard.read raising degrades to 'none', never propagates -------------


def _boom():
    raise RuntimeError("clipboard locked")


clipboard.read = _boom
shows.clear()
controller.on_clipboard_hotkey()
check("read() raising: hotkey survives and parks 'none'",
      shows == [True] and api.take_clipboard_capture().get("type") == "none")

# --- 5. save_clipboard probes before registering when enabling; combo taken ------

_original_probe = point_logger.HotkeyListener.probe
point_logger.HotkeyListener.probe = staticmethod(lambda mods, key: False)

before_cfg = dict(store.config.get("clipboard") or {})
result = api.save_clipboard({"enabled": True, "modifiers": ["ctrl", "shift"], "key": "V"})
check("save_clipboard(enabled, clashing): returns an error", bool(result.get("error")), result)
check("save_clipboard(enabled, clashing): config left unwritten",
      store.config.get("clipboard") == before_cfg,
      store.config.get("clipboard"))

# --- 6. save_clipboard skips the probe entirely when disabling, same clashing combo --

result = api.save_clipboard({"enabled": False, "modifiers": ["ctrl", "alt"], "key": "V"})
check("save_clipboard(disabled, same combo): no error", "error" not in result, result)
check("save_clipboard(disabled, same combo): config written despite probe() == False",
      store.config.get("clipboard") == {"enabled": False, "modifiers": ["ctrl", "alt"], "key": "V"},
      store.config.get("clipboard"))

point_logger.HotkeyListener.probe = _original_probe

print()
print("ALL CHECKS PASSED" if not FAILS else "FAILED: " + ", ".join(FAILS))
sys.exit(1 if FAILS else 0)
