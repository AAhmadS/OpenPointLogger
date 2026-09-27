"""Headless test of point_logger's clipboard-hotkey controller path.

Exercises Controller.on_clipboard_hotkey() and Api.save_clipboard() against a
temp-dir Store, a monkeypatched clipboard.read(), and a monkeypatched
HotkeyListener.probe - no real Win32 hotkey registration or webview window is
ever touched. A bare point_logger.Controller() degrades harmlessly here:
self.popup and self.full both default to None, and every pywebview call in
show_popup short-circuits cleanly on None.

The contract under test: the hotkey never writes to the store. It attaches
what was copied to the ONE draft - the same draft voice dictates into and the
popup box edits - as a source, and opens the popup so the user sees it land.
The point is filed by "log", with its text.

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
controller.refresh_full = lambda: None
pushes = []
_push = controller.push_voice_state
controller.push_voice_state = lambda st, d="": (pushes.append((st, d)), _push(st, d))[1]


def _all_entries():
    return [e for t in store.state()["topics"] for e in (t.get("entries") or [])]


def _sources():
    return controller.draft.snapshot()["sources"]


# --- 1. text: attached as a string source, popup opened, nothing logged ----------

r = store.start_topic("T")
tid = r["topics"][0]["id"]

shows.clear()
clipboard.read = lambda: {"type": "text", "value": "x" * 2500, "meta": {}}
controller.on_clipboard_hotkey()
check("text: no entry was written to the store", _all_entries() == [], _all_entries())
check("text: the popup was shown", shows == [True], shows)
src = _sources()
check("text: attached to the draft as a string source",
      len(src) == 1 and src[0]["type"] == "string", src)
check("text: trimmed to exactly 2000 chars", len(src[0]["value"]) == 2000, len(src[0]["value"]))
check("text: the push says a source landed", pushes[-1][0] == "source", pushes[-1])
controller.on_clipboard_hotkey()
check("text: pressing again on the same clipboard does not attach it twice",
      len(_sources()) == 1 and pushes[-1][0] == "duplicate", (_sources(), pushes[-1]))

# --- 2. link -------------------------------------------------------------------

clipboard.read = lambda: {"type": "link", "value": "https://example.org/path", "meta": {}}
controller.on_clipboard_hotkey()
src = _sources()
check("link: attached as a link", src[-1]["type"] == "link" and src[-1]["value"] == "https://example.org/path", src)
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
src = _sources()
check("image: attached as an image", src[-1]["type"] == "image", src[-1])
check("image: the window payload does not carry the image data", src[-1]["value"] == "", src[-1])
taken = controller.draft.take()
check("image: the data URL is there for filing",
      [x["value"] for x in taken["sources"] if x["type"] == "image"] == [data_url])
controller.draft.restore(taken)

# --- 4. empty clipboard: popup still opens, nothing attached ----------------------

n = len(_sources())
shows.clear()
clipboard.read = lambda: {"type": "none", "value": None, "meta": {}}
controller.on_clipboard_hotkey()
check("empty: the popup was shown anyway", shows == [True], shows)
check("empty: nothing attached", len(_sources()) == n, _sources())
check("empty: the push says why", pushes[-1] == ("error", "Clipboard is empty."), pushes[-1])

# --- 4b. no open topic is not the hotkey's problem: it still attaches -------------

store.close_topic(tid)
shows.clear()
clipboard.read = lambda: {"type": "text", "value": "hello", "meta": {}}
controller.on_clipboard_hotkey()
check("no-open-topic: popup shown, source attached",
      shows == [True] and _sources()[-1]["value"] == "hello", _sources()[-1])
check("no-open-topic: nothing was created", _all_entries() == [], _all_entries())

# --- 4c. clipboard.read raising degrades to an error, never propagates -----------


def _boom():
    raise RuntimeError("clipboard locked")


n = len(_sources())
clipboard.read = _boom
shows.clear()
controller.on_clipboard_hotkey()
check("read() raising: hotkey survives and shows the popup", shows == [True], shows)
check("read() raising: nothing attached, the error is pushed",
      len(_sources()) == n and pushes[-1][0] == "error", pushes[-1])

# --- 4d. the attached sources are filed with the point, by "log" -----------------

store.start_topic("U")
controller.draft.append("the text the sources belong to", origin="hand")
r = controller.run_voice_command("log", "", via="hotkey")
ents = _all_entries()
check("log: one point carrying every attached source",
      len(ents) == 1 and len(ents[0]["sources"]) == n, (r, [len(e["sources"]) for e in ents]))
check("log: the image was written to a file, not left as a data URL",
      all(not str(x.get("value", "")).startswith("data:") for x in ents[0]["sources"]),
      [x.get("type") for x in ents[0]["sources"]])

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
