"""Headless test of point_logger's T11 clipboard-hotkey controller path.

Exercises Controller.on_clipboard_hotkey() and Api.save_clipboard() against a
temp-dir Store, a monkeypatched clipboard.read(), and a monkeypatched
HotkeyListener.probe - no real Win32 hotkey registration or webview window is
ever touched. A bare point_logger.Controller() degrades harmlessly here:
self.popup and self.full both default to None, and every pywebview call in
_deliver_clipboard_toast / show_popup is already wrapped in try/except and
short-circuits cleanly on None - so this never needs a real webview window,
and this file never builds one.

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

toasts = []


def _toast_spy(kind, detail, entry_id, topic_id=None):
    toasts.append((kind, detail, entry_id, topic_id))


controller._deliver_clipboard_toast = _toast_spy


def _entries_for(tid):
    for t in store.state()["topics"]:
        if t["id"] == tid:
            return t.get("entries") or []
    return []


# --- 1. no open topic --------------------------------------------------------

toasts.clear()
clipboard.read = lambda: {"type": "text", "value": "hello", "meta": {}}
controller.on_clipboard_hotkey()
check("no-open-topic: nothing was created", store.state()["topics"] == [], store.state()["topics"])
check("no-open-topic: toast fired with kind 'error'",
      bool(toasts) and toasts[-1][0] == "error", toasts)

# --- 2. link routing ----------------------------------------------------------

r = store.start_topic("T")
tid = r["topics"][0]["id"]

toasts.clear()
clipboard.read = lambda: {"type": "link", "value": "https://example.org/path", "meta": {}}
controller.on_clipboard_hotkey()
entries = _entries_for(tid)
check("link: an entry was created", len(entries) == 1, entries)
if entries:
    sources = entries[-1].get("sources") or []
    check("link: sources holds a type=='link' entry with the URL",
          any(s.get("type") == "link" and s.get("value") == "https://example.org/path"
              for s in sources),
          sources)

# --- 3. text routing + 2000-char trim -----------------------------------------

toasts.clear()
clipboard.read = lambda: {"type": "text", "value": "x" * 2500, "meta": {}}
controller.on_clipboard_hotkey()
entries = _entries_for(tid)
check("text: a second entry was created", len(entries) == 2, entries)
if len(entries) == 2:
    check("text: trimmed to exactly 2000 chars", len(entries[-1]["text"]) == 2000,
          len(entries[-1]["text"]))

# --- 3b. Finding 1 regression: toast must carry the entry add_entry() itself
# just created, not entries[-1] of a state snapshot read later - a concurrent
# write (e.g. from the JS-bridge thread) landing between the hotkey's
# add_entry() call and any later read of "entries[-1]" must not change which
# id the toast/Undo uses. Uses its own topic so it doesn't perturb the entry
# counts the later checks (image routing, etc.) rely on for topic "T". "T" is
# closed first so last_open_topic() unambiguously routes here instead of "T"
# - both topics tie on "created" to the second, and last_open_topic()'s
# stable sort keeps ties in original list order (T first), so with "T" still
# open the hotkey would keep landing in "T" instead of this scratch topic.

store.close_topic(tid)
r = store.start_topic("Race-for-undo topic")
race_undo_tid = next(t["id"] for t in r["topics"] if t["title"] == "Race-for-undo topic")

toasts.clear()
clipboard.read = lambda: {"type": "text", "value": "first entry, from the hotkey", "meta": {}}
controller.on_clipboard_hotkey()
entries_after_first = _entries_for(race_undo_tid)
first_entry_id = entries_after_first[-1]["id"]
toast_entry_id = toasts[-1][2]
check("concurrent-write guard: toast id matches the entry the hotkey just created",
      toast_entry_id == first_entry_id, (toast_entry_id, first_entry_id))

# Simulate a concurrent JS-bridge write landing in the same topic right after
# the hotkey's own add_entry() returned, without going through the hotkey path.
store.add_entry(race_undo_tid, "", "second entry, logged concurrently")
entries_after_second = _entries_for(race_undo_tid)
second_entry_id = entries_after_second[-1]["id"]
check("concurrent-write guard: sanity - the concurrent write really added a new last entry",
      second_entry_id != first_entry_id, (second_entry_id, first_entry_id))
check("concurrent-write guard: toast id still matches entry 1, not the later-arriving entry 2",
      toast_entry_id == first_entry_id and toast_entry_id != second_entry_id,
      (toast_entry_id, first_entry_id, second_entry_id))

# Close this scratch topic and reopen "T" so it is again the sole open topic
# for the remaining checks, which rely on "T" already holding exactly 2
# entries (from checks 2 and 3 above).
store.close_topic(race_undo_tid)
store.reopen_topic(tid)

# --- 4. image routing ----------------------------------------------------------

png = base64.b64encode(
    bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
        "0000000d49444154789c6360000002000100ffff03000006000557bfabd4000000"
        "0049454e44ae426082"
    )
).decode()

toasts.clear()
clipboard.read = lambda: {"type": "image", "value": "data:image/png;base64," + png, "meta": {}}
controller.on_clipboard_hotkey()
entries = _entries_for(tid)
check("image: a third entry was created", len(entries) == 3, entries)
if len(entries) == 3:
    sources = entries[-1].get("sources") or []
    check("image: sources holds a type=='image' entry", any(s.get("type") == "image" for s in sources),
          sources)

# --- Finding 2: TOCTOU guard - topic closes between last_open_topic() and add_entry() --
#
# Injection mechanism: monkeypatch store.find_topic (an *instance* attribute,
# shadowing the bound method) so that its very first call for this topic -
# which, after the fix, is on_clipboard_hotkey's post-last_open_topic()
# re-check, the only place in this path that calls find_topic at all - closes
# the topic for real via the real close_topic() before delegating to the
# original find_topic(). close_topic() itself calls self.find_topic() once
# internally; by the time that inner call happens the wrapper's guard flag is
# already set, so it falls straight through to the unpatched implementation
# instead of recursing. Net effect: the re-check's find_topic() lookup inside
# on_clipboard_hotkey observes the topic already closed, exactly as if a real
# close had arrived on the UI thread between last_open_topic() and the write.
#
# "T" is closed first so last_open_topic() unambiguously returns the race
# topic - topics created within the same second tie on "created" and
# last_open_topic()'s stable sort would otherwise keep returning "T".
store.close_topic(tid)
r = store.start_topic("Race topic")
race_tid = next(t["id"] for t in r["topics"] if t["title"] == "Race topic")

_original_find_topic = store.find_topic
_closed = {"done": False}


def _find_topic_that_closes_once(tid_):
    if not _closed["done"] and tid_ == race_tid:
        _closed["done"] = True
        store.close_topic(tid_)
    return _original_find_topic(tid_)


store.find_topic = _find_topic_that_closes_once

toasts.clear()
before_count = len(_entries_for(race_tid))
clipboard.read = lambda: {"type": "text", "value": "raced", "meta": {}}
controller.on_clipboard_hotkey()
after_count = len(_entries_for(race_tid))

store.find_topic = _original_find_topic  # restore immediately, before any other check needs it

check("race guard: no entry was written to the topic closed mid-call",
      after_count == before_count, (before_count, after_count))
check("race guard: toast fired with kind 'error'",
      bool(toasts) and toasts[-1][0] == "error", toasts)
check("race guard: injection sanity - the topic really did end up closed",
      store.find_topic(race_tid)["status"] == "closed")

# --- 5. save_clipboard probes before registering when enabling; combo taken ------

api = point_logger.Api(store, controller)

_original_probe = point_logger.HotkeyListener.probe
point_logger.HotkeyListener.probe = staticmethod(lambda mods, key: False)

result = api.save_clipboard({"enabled": True, "modifiers": ["ctrl", "alt"], "key": "V"})
check("save_clipboard(enabled, clashing): returns an error", bool(result.get("error")), result)
check("save_clipboard(enabled, clashing): config left unwritten",
      store.config.get("clipboard") != {"enabled": True, "modifiers": ["ctrl", "alt"], "key": "V"},
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
