import json
import os
import secrets
import sys
import threading
import time
import traceback
import webbrowser
from datetime import datetime
from urllib.parse import urlparse

import webview

from trailmark.brand import ICON_DATA_URI, asset_path
from trailmark.hotkey import HotkeyListener
from trailmark.point_store import Store, data_dir, slugify
from trailmark.ui import MAIN_HTML, POPUP_HTML

import trailmark.asr as asr
import trailmark.speaker as speaker
import trailmark.voicecmd as voicecmd
import trailmark.clipboard as clipboard
import trailmark.llm as llm
import trailmark.single as single
import trailmark.telegram_bridge as telegram_bridge
import trailmark.templates_registry as templates_registry
import trailmark.judge as judge
import trailmark.traymenu as traymenu

def _snip(text, limit=120):
    """One line of a transcript, short enough for a toast or a 396px bar."""
    text = str(text or "").strip()
    return text[:limit] + ("…" if len(text) > limit else "")


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
# The collapsed "mini" quick-capture bar: wide enough for a voice state, the
# draft's counts, the wave and the tail of the draft; short enough to park over
# other work without covering it. 176 is the bar's measured content height at
# 396 px (headless Edge, 2026-09-27) - any less and the page scrolls, pushing
# the header off the top. Restoring goes back to POPUP_W/POPUP_H exactly.
MINI_W, MINI_H = 396, 176
MAIN_W, MAIN_H = 1180, 764

_HWND_TOPMOST, _HWND_NOTOPMOST = -1, -2
_SWP_NOSIZE, _SWP_NOMOVE, _SWP_NOACTIVATE = 0x0001, 0x0002, 0x0010
_SWP_NOZORDER = 0x0004


def _window_scale(hwnd):
    """The window's DPI scale, so a logical size can be turned into physical
    pixels for SetWindowPos.

    pywebview's width/height are logical - it applies the scale itself. Win32
    takes physical pixels. On a 150% display, resizing to a literal 396 would
    hand back a window two-thirds the intended size, so every ctypes resize
    has to do the multiplication pywebview would have done.
    """
    try:
        import ctypes
        dpi = 0
        try:
            dpi = int(ctypes.windll.user32.GetDpiForWindow(int(hwnd)))
        except Exception:
            dpi = 0
        if not dpi:
            # Pre-1607 fallback: the desktop DC's logical pixels per inch.
            dc = ctypes.windll.user32.GetDC(0)
            try:
                dpi = int(ctypes.windll.gdi32.GetDeviceCaps(dc, 88))  # LOGPIXELSX
            finally:
                ctypes.windll.user32.ReleaseDC(0, dc)
        return (dpi or 96) / 96.0
    except Exception:
        return 1.0


def _set_window_size(hwnd, width, height):
    """Resize a window from any thread, in LOGICAL pixels.

    Same reasoning as _set_topmost: window.resize() goes through pythonnet
    and is not safe off the UI thread, and the mini/full toggle is reachable
    from the JS bridge and from the hotkey thread. ctypes drops the GIL, so
    the identical SetWindowPos is safe here.
    """
    if not hwnd:
        return
    try:
        import ctypes
        scale = _window_scale(hwnd)
        ctypes.windll.user32.SetWindowPos(
            int(hwnd), 0, 0, 0, int(round(width * scale)), int(round(height * scale)),
            _SWP_NOMOVE | _SWP_NOZORDER | _SWP_NOACTIVATE)
    except Exception:
        pass


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


class _InOrder:
    """Apply results in capture order, whatever order they finish in.

    Each utterance is transcribed on its own thread, and a short sentence said
    second can come back first. ``deliver(seq, item)`` parks the item and then
    applies every consecutive one from the next expected number, on the
    delivering thread, one at a time.

    A number that never arrives would hold everything after it forever, so
    once ``stall`` seconds pass with later items waiting, the gap is skipped.
    Every caller delivers in a ``finally``, so this only fires for a thread
    that died outright - and a thought applied late is better than a
    microphone that silently stops working.
    """

    def __init__(self, apply, stall=90.0):
        self._apply = apply
        self._stall = stall
        self._lock = threading.Lock()
        self._drain = threading.Lock()
        self._next = 1
        self._waiting = {}
        self._since = None

    def deliver(self, seq, item):
        with self._lock:
            if seq < self._next:
                return
            self._waiting[seq] = item
        self._run()

    def _ready(self):
        with self._lock:
            if self._next in self._waiting:
                self._since = None
                item = self._waiting.pop(self._next)
                self._next += 1
                return item, True
            if not self._waiting:
                self._since = None
                return None, False
            now = time.time()
            if self._since is None:
                self._since = now
            if now - self._since >= self._stall:
                self._next = min(self._waiting)
                self._since = None
                item = self._waiting.pop(self._next)
                self._next += 1
                return item, True
            return None, False

    def _run(self):
        # One drainer at a time: two threads applying at once would put the
        # draft back in whatever order the scheduler felt like.
        while True:
            if not self._drain.acquire(blocking=False):
                return
            try:
                while True:
                    item, ok = self._ready()
                    if not ok:
                        break
                    try:
                        self._apply(item)
                    except Exception:
                        traceback.print_exc()
            finally:
                self._drain.release()
            # Something delivered while this thread was releasing the drain
            # lock would otherwise sit until the next utterance.
            with self._lock:
                if self._next not in self._waiting:
                    return

    def pending(self):
        with self._lock:
            return len(self._waiting)


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

    def get_judge(self):
        """Config plus the questions and thresholds, for the settings card.

        The thresholds travel to the UI because a number that decides whether
        your own words survive an export should be visible to the person whose
        words they are, not buried in a module.
        """
        return {
            "config": self.store.config.get("judge") or {},
            "model": judge.MODEL,
            "thresholds": dict(judge.THRESHOLDS),
        }

    def save_judge(self, cfg):
        """Mirrors save_asr's shape rather than _save_section's: this key is a
        credential, so it is merged explicitly rather than swept in by a
        generic update, and it is never logged, echoed, or put in an error."""
        cfg = cfg or {}
        prev = self.store.config.get("judge") or {}
        merged = {
            "enabled": bool(cfg.get("enabled")),
            "api_key": str(cfg.get("api_key")) if cfg.get("api_key") is not None
                       else str(prev.get("api_key") or ""),
            "model": (str(cfg.get("model") or "")).strip(),
            "base_url": (str(cfg.get("base_url") or "")).strip(),
            "kinds": bool(cfg.get("kinds", prev.get("kinds", True))),
            "notes": bool(cfg.get("notes", prev.get("notes", True))),
        }
        self.store.config["judge"] = merged
        self.store.save_config()
        self.controller.refresh_full()
        return self.store.state()

    def test_judge(self):
        """One real question against the live endpoint, so the card can say
        whether the key works before an export depends on it.

        Deliberately a question with a known answer - if the service is up and
        the key is good, the answer is unambiguous, and anything else is a
        configuration problem rather than a judgement to interpret.
        """
        cfg = self.store.config.get("judge") or {}
        if not judge.available(cfg):
            return {"error": "Not enabled, or no API key."}
        payload = judge.ask(cfg, {"note": "The audit is not finished yet.",
                                  "passage": "The audit has been completed."},
                            {"probe": {"type": "choice",
                                       "instructions": "Does `passage` say what `note` says?",
                                       "criteria": judge.NOTE_CRITERIA}})
        a = (payload.get("answers") or {}).get("probe") or {}
        if not a:
            return {"error": "No answer - check the key and the network."}
        return {"ok": True, "model": payload.get("model", ""),
                "choice": a.get("choice", ""),
                "confidence": round(float(a.get("confidence") or 0), 2)}

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
                        or "https://openrouter.ai/api/v1",
            "model": (str(cfg.get("model") or prev.get("model") or "")).strip() or "whisper-1",
            "api_key": str(cfg.get("api_key")) if cfg.get("api_key") is not None else str(prev.get("api_key") or ""),
            # Persian or English only: "" decides between the two per
            # utterance, "fa" / "en" pins one. Anything else - including a
            # language saved by an older version - falls back to "".
            "language": (lambda l: l if l in asr.ALLOWED_LANGUAGES else "")(
                str(cfg.get("language") or "").strip().lower()),
            # The microphone's NAME, which survives a reboot; an index does not.
            "device": (str(cfg.get("device") or "")).strip(),
            "sensitivity": sensitivity,
        }
        self.store.config["asr"] = merged
        self.store.save_config()
        self.controller.apply_asr()
        self.controller.refresh_full()
        return self.store.state()

    def get_voice(self):
        """Config + live registration state + the grammar, in one call.

        Settings needs all three at once and they are cheap; three separate
        bridge round-trips would only give the panel three chances to render
        a half-built view.
        """
        return {
            "config": self.store.config.get("voice") or {},
            "hotkeys": self.controller.voice_hotkey_report(),
            "grammar": voicecmd.describe_grammar(),
            "draft": self.controller.voice_snapshot(),
            # Whether "session <name>" can be told from a sentence. Without
            # a second opinion it stays text, and Settings says so.
            "second_opinion": bool(judge.available(self.store.config.get("judge") or {})),
        }

    def save_voice(self, cfg):
        """Persist the voice section and re-register the hotkeys.

        Mirrors save_asr's shape rather than _save_section's: changing a key
        has to re-register a Win32 hotkey, and changing always_on changes
        what the microphone already running will do with the next sentence.
        """
        cfg = cfg or {}
        prev = self.store.config.get("voice") or {}
        keys = dict(prev.get("keys") or {})
        incoming = cfg.get("keys")
        if isinstance(incoming, dict):
            for name in ("log", "finish", "session", "tab"):
                if name in incoming:
                    keys[name] = str(incoming[name] or "").strip().upper()[:12]
        mods = cfg.get("modifiers") if isinstance(cfg.get("modifiers"), list) else None
        merged = {
            "always_on": bool(cfg.get("always_on", prev.get("always_on", True))),
            "commands": bool(cfg.get("commands", prev.get("commands", True))),
            "hotkeys": bool(cfg.get("hotkeys", prev.get("hotkeys", True))),
            "modifiers": mods or prev.get("modifiers") or ["ctrl", "alt"],
            "keys": keys,
            "mini": bool(cfg.get("mini", prev.get("mini", False))),
        }
        self.store.config["voice"] = merged
        self.store.save_config()
        self.controller.apply_voice_hotkeys()
        self.controller.refresh_full()
        return self.get_voice()

    def voice_command(self, name, argument=""):
        """Run a command from a button, the same way voice does."""
        return self.controller.run_voice_command(str(name or ""), str(argument or ""),
                                                 via="ui")

    # --- the draft: one point, dictated and typed into the same text -------

    def draft_get(self):
        return self.controller.voice_snapshot()

    def draft_set(self, text, base_rev):
        """The popup's textarea, sent after the user stops typing.

        ``base_rev`` is the revision the text was typed against. Dictation
        that landed in between is merged onto the end rather than overwritten;
        a draft that was logged in between is refused, so the page can put the
        leftover words back instead of resurrecting a filed point.
        """
        try:
            base_rev = int(base_rev)
        except (TypeError, ValueError):
            base_rev = -1
        r = self.controller.draft.set_text(str(text or ""), base_rev)
        if r.get("ok"):
            self.controller.push_voice_state("typed" if not r.get("merged") else "merged", "")
        out = self.controller.voice_snapshot()
        out["result"] = {k: r.get(k) for k in ("ok", "merged", "reason")}
        return out

    def draft_meta(self, fields):
        """Topic, tab and kind for the point being composed."""
        fields = fields or {}
        clean = {}
        if "topic_id" in fields:
            clean["topic_id"] = str(fields.get("topic_id") or "")
        if "subtopic" in fields:
            clean["subtopic"] = str(fields.get("subtopic") or "")
        if "kind" in fields:
            clean["kind"] = str(fields.get("kind") or "")
        self.controller.draft.set_meta(clean)
        self.controller.push_voice_state("edited", "")
        return self.controller.voice_snapshot()

    def draft_add_source(self, stype, value, note=""):
        sid = self.controller.draft.add_source(str(stype or ""), value, str(note or ""),
                                               origin="hand")
        out = self.controller.voice_snapshot()
        if not sid:
            out["error"] = "Already attached, empty, or too many sources."
        else:
            self.controller.push_voice_state("edited", "")
        return out

    def draft_drop_source(self, sid):
        """Removes are by hand only - a misheard spoken delete has no undo."""
        try:
            sid = int(sid)
        except (TypeError, ValueError):
            return self.controller.voice_snapshot()
        self.controller.draft.drop_source(sid)
        self.controller.push_voice_state("edited", "")
        return self.controller.voice_snapshot()

    def draft_clear(self):
        self.controller.draft.clear()
        self.controller.push_voice_state("cleared", "")
        return self.controller.voice_snapshot()

    def draft_log(self, text=None, base_rev=None):
        """The Log button: settle the text the page is showing, then file it.

        The page's latest keystrokes may not have been sent yet, so they come
        along with the press rather than racing a debounce timer.
        """
        if text is not None:
            r = self.draft_set(text, base_rev)
            if not (r.get("result") or {}).get("ok"):
                r["error"] = "The draft changed underneath - check it and log again."
                return r
        r = self.controller.run_voice_command("log", "", via="ui")
        out = self.controller.voice_snapshot()
        out["result"] = {k: r.get(k) for k in ("state", "detail", "topic_id", "entry_id", "sources")}
        if r.get("error"):
            out["error"] = r["error"]
        return out

    # --- held clips --------------------------------------------------------

    def held_list(self):
        return self.controller.held_list()

    def held_use(self, hid):
        try:
            hid = int(hid)
        except (TypeError, ValueError):
            return {"error": "No such clip."}
        r = self.controller.use_held(hid)
        r["held"] = self.controller.held_list()
        return r

    def held_drop(self, hid=None):
        if hid is not None:
            try:
                hid = int(hid)
            except (TypeError, ValueError):
                return {"error": "No such clip."}
        return self.controller.drop_held(hid)

    # --- microphone test and speaker check ---------------------------------

    def mic_test_start(self, device=None, sensitivity=None):
        return self.controller.mic_test_start(device=device, sensitivity=sensitivity)

    def mic_levels(self, last=300):
        return self.controller.mic_levels(last)

    def mic_test_stop(self):
        return self.controller.mic_test_stop()

    def speaker_status(self):
        return self.controller.speaker_status()

    def speaker_download(self):
        return self.controller.speaker_download()

    def speaker_record_start(self):
        return self.controller.enroll_record_start()

    def speaker_record_stop(self):
        return self.controller.enroll_record_stop()

    def speaker_enroll_reset(self):
        return self.controller.enroll_reset()

    def speaker_enroll_finish(self):
        return self.controller.enroll_finish()

    def speaker_check(self):
        return self.controller.speaker_check()

    def speaker_save(self, fields):
        return self.controller.speaker_save(fields)

    def toggle_voice(self, on=None):
        """Turn always-on voice on or off from whichever window asked."""
        try:
            cfg = dict(self.store.config.get("asr") or {})
            cfg["enabled"] = (not cfg.get("enabled")) if on is None else bool(on)
            self.save_asr(cfg)
            out = {"enabled": bool(cfg["enabled"])}
            # Turning it on with no transcription key opens the microphone and
            # then fails on the first thing said, several seconds later and in
            # a different place. Say it now instead - the switch still goes on,
            # because the user asked for it to.
            if cfg["enabled"] and not (cfg.get("api_key") or "").strip():
                out["warn"] = ("Listening, but there is no transcription key yet "
                               "- add one in Settings.")
            return out
        except Exception as e:
            return {"error": str(e)}

    def set_popup_mini(self, mini):
        return self.controller.set_popup_mini(mini)

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
        """Open the folder where the user's own templates live, creating it first.

        Also drops in a starter template and the authoring notes if they are
        not there. An empty folder tells someone nothing about what a template
        is, and the one thing a hand-written template gets wrong - direction -
        is invisible until a Persian report renders sideways. Writing a
        correct example beside their own work is cheaper than documenting it
        somewhere they will not look.
        """
        try:
            d = templates_registry.user_dir()
            d.mkdir(parents=True, exist_ok=True)
            try:
                templates_registry.write_starter(d)
            except Exception:
                pass          # a missing example must never block the folder
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
            import trailmark.pipeline as pipeline
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
            import trailmark.pdf_render as pdf_render
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
        import trailmark.citation as citation
        return citation.lookup_doi(doi)

    def citation_styles(self):
        """The styles scientific mode can render, for the settings card."""
        import trailmark.citation as citation
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
        self.popup_visible = True
        self.full_visible = False
        self.quitting = False
        self.hotkey = None
        self.clipboard_hotkey = None
        # name -> HotkeyListener for the four always-on voice verbs. A dict
        # rather than four attributes because they are registered, stopped
        # and re-registered as a set, and a set is easier to not half-update.
        self.voice_hotkeys = {}
        # The one point being composed - dictated, typed, or both. Its own
        # lock lives inside it; four threads reach it (utterance threads,
        # Win32 hotkey, JS bridge, the tray).
        self.draft = voicecmd.Draft()
        # Commands run one at a time: "log" said while the Log button is being
        # pressed must not file the same draft into two entries.
        self._command_lock = threading.RLock()
        self.voice_state = "off"
        self.voice_detail = ""
        self.voice_heard = ""
        # Clips the speaker check held aside (see _hold).
        self.held = []
        self._held_lock = threading.Lock()
        self._held_seq = 0
        # The speaker model, loaded on first use - 26 MB and ~0.3 s, not
        # worth paying for someone who never turns the check on.
        self._verifier = None
        self._verifier_lock = threading.Lock()
        # Settings' microphone test and voice enrollment: at most one open
        # at a time, and never alongside a second copy of itself.
        self.mic_test = None
        self._mic_test_lock = threading.Lock()
        self._enroll_clips = []
        # Set while a sentence is being recorded for the voiceprint. The live
        # microphone hears it too, and a sentence read aloud for enrollment is
        # not a note - it must not be dictated into the draft.
        self._enrolling = threading.Event()
        self.popup_mini = False
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

    #: Win32 hotkey ids, one per voice verb. 0x4343 is the capture hotkey and
    #: 0x4344 the clipboard one, so these continue the same block - a repeated
    #: id would silently steal the other combo's registration.
    VOICE_HOTKEY_IDS = {"log": 0x4345, "finish": 0x4346,
                        "session": 0x4347, "tab": 0x4348}

    def apply_voice_hotkeys(self):
        """Register (or drop) Ctrl+Alt+S / F / N / T.

        Mirrors apply_clipboard_hotkey, four times. Registration is
        best-effort per key: if another application already holds one of the
        combos, RegisterHotKey fails for that one alone and the other three
        still work, which is better than losing the set to one conflict.
        The ones that failed are reported by voice_hotkey_report() so Settings
        can say which, rather than leaving the user to guess why one verb is
        dead."""
        for listener in self.voice_hotkeys.values():
            try:
                listener.stop()
            except Exception:
                pass
        self.voice_hotkeys = {}
        cfg = self.store.config.get("voice") or {}
        if not cfg.get("hotkeys", True):
            return
        mods = cfg.get("modifiers") or ["ctrl", "alt"]
        keys = cfg.get("keys") or {}
        for name, hid in self.VOICE_HOTKEY_IDS.items():
            key = (keys.get(name) or "").strip()
            if not key:
                continue
            try:
                listener = HotkeyListener(
                    mods, key,
                    (lambda n: (lambda: self.run_voice_command(n, "", via="hotkey")))(name),
                    hotkey_id=hid)
                listener.start()
            except ValueError:
                continue
            self.voice_hotkeys[name] = listener
        self._settle_voice_hotkeys()

    def _settle_voice_hotkeys(self, timeout=0.4):
        """Wait until every listener has actually tried RegisterHotKey.

        HotkeyListener.start() returns as soon as the thread is spawned;
        _registered is set inside that thread, one line into its message
        loop. Reporting straight after start() would therefore say "not
        registered" for a combo that registers a millisecond later - a
        Settings panel that tells the user a working key is dead. A listener
        has decided once it reports registered, or once its thread has
        exited (RegisterHotKey failed and _loop returned).
        """
        deadline = time.time() + timeout
        while time.time() < deadline:
            undecided = [l for l in self.voice_hotkeys.values()
                         if not getattr(l, "_registered", False)
                         and getattr(l, "_thread", None) is not None
                         and l._thread.is_alive()]
            if not undecided:
                return
            time.sleep(0.01)

    def voice_hotkey_report(self):
        """Which voice combos are actually live, for Settings.

        ``registered`` is what RegisterHotKey accepted. A combo held by
        another application reports registered False, which is the only
        honest answer available - Windows does not say who took it."""
        cfg = self.store.config.get("voice") or {}
        mods = cfg.get("modifiers") or ["ctrl", "alt"]
        keys = cfg.get("keys") or {}
        out = []
        for name in self.VOICE_HOTKEY_IDS:
            key = (keys.get(name) or "").strip()
            listener = self.voice_hotkeys.get(name)
            out.append({
                "command": name,
                "key": key,
                "combo": "+".join([m.capitalize() for m in mods] + [key.upper()]) if key else "",
                "registered": bool(listener and getattr(listener, "_registered", False)),
            })
        return out

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
            # A fresh logger counts from 1 again, so it gets a fresh order.
            order = _InOrder(self.apply_heard)
            self.asr_logger = asr.VoiceLogger(
                cfg, lambda wav, seq: self.on_asr_utterance(wav, seq, order),
                self.push_asr_state)
            try:
                self.asr_logger.start()
            except Exception:
                traceback.print_exc()
                self.push_asr_state("error", "Could not start voice logging.")

    def on_asr_utterance(self, wav_bytes, seq=None, order=None):
        """The slow half of one utterance, on the utterance's own thread.

        Several of these run at once - transcription is a network call, and a
        second sentence should not wait for the first one's round trip. What
        they produce is then APPLIED strictly in the order it was said, by
        ``order`` (an _InOrder), because the draft and the commands are
        order-sensitive: "session Rust" followed by a sentence must create the
        topic before the sentence lands, however the two calls raced.

        Always delivers, even on failure - a sequence number that never
        arrives would hold back everything said after it.
        """
        item = {"seq": seq, "wav": wav_bytes}
        try:
            if self._enrolling.is_set():
                item["skip"] = True
            else:
                item.update(self.hear(wav_bytes))
        except Exception:
            traceback.print_exc()
            item["error"] = "Transcription failed."
        if order is not None and seq is not None:
            order.deliver(seq, item)
        else:
            self.apply_heard(item)

    def hear(self, wav_bytes):
        """Speaker check, then transcription - in that order, so a voice that
        is not the owner's is never sent anywhere."""
        gate = self.speaker_gate(wav_bytes)
        if gate.get("hold"):
            return {"held": True, "score": gate.get("score"), "why": gate.get("why") or ""}
        cfg = self.store.config.get("asr") or {}
        self.push_asr_state("transcribing", "")
        result = asr.transcribe(cfg, wav_bytes)
        if result.get("error"):
            return {"error": result["error"]}
        out = {"text": result.get("text") or "", "language": result.get("language") or ""}
        if gate.get("short"):
            out["short"] = True
        if gate.get("score") is not None:
            out["score"] = gate["score"]
        return out

    def apply_heard(self, item):
        """The ordered half: one utterance's result, applied. Runs on whichever
        utterance thread is draining _InOrder, one at a time."""
        if item.get("skip"):
            return
        if item.get("error"):
            self.push_asr_state("error", item["error"])
            return
        if item.get("held"):
            why = item.get("why") or ""
            score = item.get("score")
            self._hold(item.get("wav"), score, "", why or "another voice")
            if why:
                self.push_voice_state("held", "Held aside - the voice check could not run: " + why)
            else:
                self.push_voice_state("held", "Another voice - held aside%s."
                                      % ((" (match %.2f)" % score) if score is not None else ""))
            return
        text = (item.get("text") or "").strip()
        if item.get("short") and text:
            # Too short to check whose voice it was. A certain command is let
            # through - "log" is half a second, and a gate that blocked every
            # command would be switched off within the hour. Anything else
            # this short is held, not dropped.
            p = voicecmd.parse(text)
            if not (p["command"] and p["form"] in voicecmd.CERTAIN_FORMS):
                self._hold(item.get("wav"), None, text, "too short to check the voice")
                self.push_voice_state("held", "Too short to check the voice - held aside.")
                return
        self.on_voice_transcript(text)

    def on_voice_transcript(self, text):
        """One transcript in: a command, or words for the draft.

        Split out from the audio path so the whole decision is testable
        without a microphone - it runs several times a minute, and a wrong
        answer either loses a thought or closes a topic.

        With voice.always_on off this is the older behaviour: every utterance
        becomes its own point immediately.
        """
        text = (text or "").strip()
        cfg = self.store.config.get("voice") or {}
        if not cfg.get("always_on", True):
            self._log_asr_text(text)
            return {"action": "logged-directly"}
        if not text:
            self.push_asr_state("listening", "")
            return {"action": "nothing"}
        decision = {"action": "text", "text": text, "reason": "commands-off"}
        parsed = None
        if cfg.get("commands", True):
            parsed = voicecmd.parse(text)
            verdict = None
            if parsed["command"] and parsed["form"] in voicecmd.OPINION_FORMS:
                self.push_voice_state("deciding", _snip(text))
                verdict = judge.command_intents(self.store.config.get("judge") or {},
                                                [parsed]).get(0)
            decision = voicecmd.decide(parsed, verdict)
        self.voice_heard = text
        if decision["action"] == "command":
            self.run_voice_command(decision["command"], decision["argument"], via="voice")
            return decision
        if not self.draft.append(decision["text"], origin="voice"):
            self.push_voice_state("error", "The draft is full - log it or clear it first.")
            return decision
        detail = _snip(text)
        if parsed and parsed["form"] in voicecmd.OPINION_FORMS and decision["reason"] == "no-opinion":
            # "session Rust" with no second opinion available stays text -
            # say so, or the user waits for a topic that is never coming.
            detail = ('Kept as text - no second opinion to tell a name from a sentence. '
                      'Say "trail %s ..." to make it a command.' % parsed["command"])
        self.push_voice_state("heard", detail)
        return decision

    # --- the commands ------------------------------------------------------

    def run_voice_command(self, name, argument="", via="voice"):
        """Execute one command, whether it was spoken, pressed, or clicked.

        One entry point for all three, so a hotkey, a button and a spoken word
        can never drift apart. Reached from utterance threads, the Win32
        hotkey thread and the JS bridge - so everything it touches is the
        store (locked), the draft (locked), or evaluate_js/ctypes. Never a
        pywebview property; see challenge C5.

        Returns a small dict for tests and the JS bridge. The live windows are
        updated by the state push, not by this return value.
        """
        handler = {
            "save": self._voice_save,
            "log": self._voice_log,
            "finish": self._voice_finish,
            "session": self._voice_session,
            "tab": self._voice_tab,
        }.get(name)
        if handler is None:
            return {"error": "Unknown command: %s" % name}
        with self._command_lock:
            try:
                result = handler(argument)
            except Exception:
                traceback.print_exc()
                result = {"error": "That command failed."}
        if result.get("error"):
            self.push_voice_state("error", result["error"])
        else:
            self.push_voice_state(result.get("state") or "ok", result.get("detail") or "")
        return result

    def _open_topic(self):
        """The newest open topic, re-checked at the moment of use.

        Time passes between hearing a command and acting on it, and the UI
        thread can close the topic in between.
        """
        topic = self.store.last_open_topic()
        if topic is None:
            return None
        t = self.store.find_topic(topic["id"])
        if not t or t.get("status") != "open":
            return None
        return t

    def _target_topic(self, meta=None):
        """Where the draft is going: the topic chosen in the draft if it is
        still open, else the newest open one."""
        meta = meta if meta is not None else self.draft.meta()
        tid = (meta or {}).get("topic_id") or ""
        if tid:
            t = self.store.find_topic(tid)
            if t and t.get("status") == "open":
                return t
        return self._open_topic()

    def _voice_save(self, _argument=""):
        """"save" / Ctrl+Alt+V: attach the clipboard to the draft as a source.

        Nothing is written to the store - the source is filed with the text
        by "log". An image stays a data URL until add_entry writes the file.
        """
        try:
            data = clipboard.read()
        except Exception:
            traceback.print_exc()
            return {"error": "Couldn't read the clipboard."}
        kind = data.get("type") or "none"
        value = data.get("value")
        if kind == "none" or not value:
            return {"error": "Clipboard is empty."}
        if kind == "text" and isinstance(value, str):
            value = value[:2000]
            kind = "string"
        if kind not in ("link", "string", "image"):
            return {"error": "Nothing usable on the clipboard."}
        if not self.draft.add_source(kind, value, origin="voice"):
            return {"state": "duplicate", "detail": "Already attached.", "kind": kind}
        return {"state": "source", "kind": kind,
                "detail": "Image attached." if kind == "image" else _snip(value)}

    def _voice_log(self, _argument=""):
        """"log" / Ctrl+Alt+S / the Log button: file the draft as one point.

        Take first, then write, then put it back if the write failed: the
        drain is atomic with the read, so a sentence that arrives during the
        write is never drained without being filed.
        """
        taken = self.draft.take()
        if not taken["text"] and not taken["sources"]:
            return {"error": "Nothing to log yet."}
        if not taken["text"]:
            self.draft.restore(taken)
            return {"error": "Sources are attached, but the point has no text yet."}
        t = self._target_topic(taken["meta"])
        if t is None:
            self.draft.restore(taken)
            return {"error": "No open topic - say “session” and a name to start one."}
        # The tab belongs to the topic it was chosen under. If the draft fell
        # back to another topic (its own was closed meanwhile), the tab does
        # not follow it there.
        sub = taken["meta"].get("subtopic") or ""
        if t["id"] != taken["meta"].get("topic_id") and sub not in (t.get("subtopics") or []):
            sub = ""
        explicit = taken["meta"].get("kind") or ""
        # Typed points keep the popup's old default; dictated ones are notes
        # until the second opinion says otherwise - each path's behaviour from
        # before the two were one draft.
        kind = explicit or ("note" if taken["origin"] == "voice" else "claim")
        r = self.store.add_entry(t["id"], sub, taken["text"], kind=kind,
                                 sources=taken["sources"])
        if r.get("error"):
            self.draft.restore(taken)
            return {"error": r["error"]}
        self.refresh_full()
        if not explicit and taken["origin"] == "voice":
            self.refine_kind(t["id"], r.get("entry_id"), taken["text"],
                             bool(taken["sources"]))
        return {"state": "logged", "detail": _snip(taken["text"]),
                "topic_id": t["id"], "entry_id": r.get("entry_id"),
                "sources": len(taken["sources"])}

    def refine_kind(self, tid, eid, text, has_source):
        """Ask the judge whether a dictated point is really a note.

        Everything captured by voice or from Telegram is stored as a note,
        because at capture time nobody asked. In scientific mode that is
        load-bearing - a note must carry no citation, a quote must not be
        reworded - so a sentence dictated out of a paper, filed as a note, gets
        neither protection.

        Behind the capture, never in front of it. The entry is already saved
        and already correct by the old rules before this starts; the round trip
        measures 1.4-2.6 s on this machine and a capture that took that long
        would feel broken. If the answer never arrives the entry simply stays a
        note, which is what it would have been anyway.

        Only ever changes ``kind``, and only on an entry this app just created
        with the default. Nothing else about what the user logged is touched.
        """
        cfg = self.store.config.get("judge") or {}
        if not eid or not cfg.get("kinds", True) or not judge.available(cfg):
            return
        def work():
            kinds = judge.capture_kinds(cfg, [(text, has_source)])
            kind = kinds.get(0)
            if not kind:
                return
            r = self.store.update_entry(tid, eid, {"kind": kind})
            if r.get("error"):
                return
            self.refresh_full()
            self.push_voice_state("edited", "Filed as a %s." % kind)
        judge.in_background(work)

    def _voice_finish(self, _argument=""):
        """"finish" / Ctrl+Alt+F: file what is in the draft, then close the topic.

        If the draft cannot be filed, the topic stays open - closing it and
        leaving the words stranded is the loss that makes people stop
        trusting voice.
        """
        t = self._target_topic()
        if t is None:
            return {"error": "No open topic to finish."}
        if self.draft.snapshot()["text"].strip():
            r = self._voice_log()
            if r.get("error"):
                return {"error": "Not finished - the draft could not be filed: " + r["error"]}
        r = self.store.close_topic(t["id"])
        if r.get("error"):
            return {"error": r["error"]}
        self.draft.set_meta({"topic_id": "", "subtopic": ""})
        self.refresh_full()
        return {"state": "finished", "detail": t.get("title") or ""}

    def _voice_session(self, argument=""):
        """"session <name>" / Ctrl+Alt+N: start a new topic, and file into it.

        An unnamed session is still a session: rather than refuse and lose
        whatever gets said next, it takes a dated title the user can rename.
        A draft left over from the previous topic is filed into THAT topic
        first, so words never land under a heading they were not said under.
        With no previous topic, the draft simply carries into the new one.
        """
        title = (argument or "").strip()
        if self.draft.snapshot()["text"].strip() and self._target_topic() is not None:
            r = self._voice_log()
            if r.get("error"):
                return {"error": "No new session - the draft could not be filed: " + r["error"]}
        if not title:
            title = "Session " + datetime.now().strftime("%Y-%m-%d %H:%M")
        r = self.store.start_topic(title)
        if r.get("error"):
            return {"error": r["error"]}
        t = self.store.last_open_topic()
        self.draft.set_meta({"topic_id": (t or {}).get("id") or "", "subtopic": ""})
        self.refresh_full()
        return {"state": "session", "detail": title}

    def _voice_tab(self, argument=""):
        """"tab <name>" / Ctrl+Alt+T: a sub-topic, and file what follows under it.

        An unnamed tab is numbered from the count already there. Naming a tab
        that exists switches to it rather than failing.
        """
        t = self._target_topic()
        if t is None:
            return {"error": "No open topic - say “session” and a name first."}
        name = (argument or "").strip()
        subs = t.get("subtopics") or []
        if not name:
            name = "Tab %d" % (len(subs) + 1)
        existed = name in subs
        if not existed:
            r = self.store.add_subtopic(t["id"], name)
            if r.get("error"):
                return {"error": r["error"]}
        self.draft.set_meta({"topic_id": t["id"], "subtopic": name})
        self.refresh_full()
        return {"state": "tab", "detail": ("Back to " if existed else "") + name}

    # --- held clips (the speaker gate) --------------------------------------

    #: Clips the speaker check held aside, newest last. Kept in memory only -
    #: other people's voices are not written to disk - and capped, because a
    #: busy room would otherwise grow this without end.
    HELD_MAX = 12

    def _hold(self, wav, score, text, reason):
        with self._held_lock:
            self._held_seq += 1
            self.held.append({"id": self._held_seq, "wav": wav or b"",
                              "score": None if score is None else round(float(score), 3),
                              "text": text or "", "reason": reason,
                              "at": datetime.now().strftime("%H:%M:%S"),
                              "seconds": round(max(0, len(wav or b"") - 44) / 32000.0, 1)})
            del self.held[:-self.HELD_MAX]

    def held_list(self):
        with self._held_lock:
            return [{k: v for k, v in h.items() if k != "wav"} for h in self.held]

    def use_held(self, hid):
        """Put a held clip into the draft after all - the owner's call, by hand.

        Transcribed now if it was never sent (a clip held for its voice), and
        always appended as text: a held clip is never run as a command, since
        whoever said it was, by definition, not verified.
        """
        with self._held_lock:
            found = next((h for h in self.held if h["id"] == hid), None)
            if found:
                self.held.remove(found)
        if not found:
            return {"error": "That clip is gone."}
        text = found["text"]
        if not text:
            r = asr.transcribe(self.store.config.get("asr") or {}, found["wav"])
            if r.get("error"):
                with self._held_lock:
                    self.held.append(found)
                return {"error": r["error"]}
            text = (r.get("text") or "").strip()
        if text:
            self.draft.append(text, origin="voice")
        self.push_voice_state("heard", _snip(text) if text else "Nothing in that clip.")
        return {"ok": True, "text": text}

    def drop_held(self, hid=None):
        with self._held_lock:
            if hid is None:
                self.held.clear()
            else:
                self.held[:] = [h for h in self.held if h["id"] != hid]
        return {"ok": True, "held": self.held_list()}

    # --- whose voice is it ---------------------------------------------------

    def models_dir(self):
        return data_dir() / "models"

    def verifier(self):
        """The speaker model, loaded once. None, with the reason, if it cannot be."""
        with self._verifier_lock:
            if self._verifier is not None:
                return self._verifier, ""
            ok, why = speaker.available()
            if not ok:
                return None, why
            if not speaker.model_ready(self.models_dir()):
                return None, "The voice model is not downloaded."
            try:
                self._verifier = speaker.Verifier(speaker.model_path(self.models_dir()))
            except Exception as e:
                traceback.print_exc()
                return None, "The voice model would not load: %s" % e
            return self._verifier, ""

    @staticmethod
    def _threshold(cfg):
        """The saved match threshold. 0.0 is a value, not "unset"."""
        t = (cfg or {}).get("threshold")
        try:
            return float(speaker.DEFAULT_THRESHOLD if t is None or t == "" else t)
        except (TypeError, ValueError):
            return float(speaker.DEFAULT_THRESHOLD)

    def speaker_gate(self, wav_bytes):
        """Is this the owner speaking? Runs before anything leaves the machine.

        ``{}`` means no check is configured - pass. ``{"score": s}`` passed.
        ``{"hold": True, "score": s}`` is someone else, or a check that could
        not run: with the check switched on, a broken model holds clips
        rather than letting every voice in the room through, and the held
        list says why. ``{"short": True}`` is too little speech to tell -
        apply_heard decides what that may still do.
        """
        cfg = self.store.config.get("speaker") or {}
        enrolled = cfg.get("embedding") or []
        if not cfg.get("enabled") or not enrolled:
            return {}
        v, why = self.verifier()
        if v is None:
            return {"hold": True, "score": None, "why": why}
        try:
            pcm, sr = speaker.wav_to_pcm(wav_bytes)
            sensitivity = (self.store.config.get("asr") or {}).get("sensitivity", 50)
            speech = asr.speech_only(pcm, sensitivity=sensitivity, samplerate=sr)
            emb = v.embed(speech, samplerate=sr)
        except Exception:
            traceback.print_exc()
            return {"hold": True, "score": None, "why": "The voice check failed."}
        if emb is None:
            return {"short": True}
        score = speaker.cosine(emb, enrolled)
        threshold = self._threshold(cfg)
        if not speaker.is_owner(score, threshold):
            return {"hold": True, "score": score}
        return {"score": score}

    def speaker_status(self):
        cfg = self.store.config.get("speaker") or {}
        ok, why = speaker.available()
        return {
            "runtime": ok, "runtime_error": why,
            "model": speaker.model_ready(self.models_dir()),
            "model_mb": round(speaker.MODEL_BYTES / 1e6, 1),
            "enabled": bool(cfg.get("enabled")),
            "enrolled": bool(cfg.get("embedding")),
            "threshold": self._threshold(cfg),
            "default_threshold": speaker.DEFAULT_THRESHOLD,
            "clips": int(cfg.get("clips") or 0),
            "seconds": float(cfg.get("seconds") or 0),
            "consistency": float(cfg.get("consistency") or 0),
            "enrolled_at": cfg.get("enrolled_at") or "",
            "recorded": len(self._enroll_clips),
            "held": self.held_list(),
        }

    def speaker_download(self):
        r = speaker.download_model(self.models_dir())
        if r.get("error"):
            return {"error": r["error"]}
        return self.speaker_status()

    # --- the microphone test, and recording for enrollment -------------------

    def mic_test_start(self, device=None, keep_audio=False, max_seconds=30, sensitivity=None):
        """Open the chosen microphone just to watch it.

        While voice is listening, the live logger already has the microphone
        and its own meter - the test shows that instead of opening a second
        stream on the same device, which WASAPI may refuse.
        """
        cfg = self.store.config.get("asr") or {}
        device = (cfg.get("device") or "") if device is None else str(device)
        with self._mic_test_lock:
            if self.mic_test is not None:
                self.mic_test.stop()
                self.mic_test = None
            if not keep_audio and self.asr_logger is not None \
                    and device == (cfg.get("device") or ""):
                return {"ok": True, "shared": True, "note": "Showing the live microphone."}
            if sensitivity is None:
                sensitivity = cfg.get("sensitivity", 50)
            try:
                sensitivity = max(0, min(100, int(sensitivity)))
            except (TypeError, ValueError):
                sensitivity = 50
            m = asr.MicMonitor(device=device, sensitivity=sensitivity,
                               max_seconds=max_seconds, keep_audio=keep_audio)
            r = m.start()
            if r.get("error"):
                return {"error": r["error"]}
            self.mic_test = m
            return {"ok": True, "shared": False, "note": r.get("note") or ""}

    def mic_levels(self, last=300):
        """The newest wave buckets: the test monitor's if one is open, else the
        live logger's, else nothing."""
        with self._mic_test_lock:
            m = self.mic_test
        if m is not None:
            out = m.meter.read(last)
            out["running"] = m.running
            out["source"] = "test"
            if m.error:
                out["error"] = m.error
            return out
        lg = self.asr_logger
        if lg is not None and getattr(lg, "meter", None) is not None:
            out = lg.meter.read(last)
            out["running"] = True
            out["source"] = "live"
            return out
        return {"running": False, "source": "", "lo": [], "hi": [], "rms": [],
                "seq": 0, "bucket_ms": asr.LevelMeter.BUCKET_MS, "threshold": 0}

    def mic_test_stop(self):
        with self._mic_test_lock:
            m, self.mic_test = self.mic_test, None
        if self._enrolling.is_set():
            # An enrollment recording abandoned (the page was left).
            threading.Timer(1.5, self._enrolling.clear).start()
        if m is not None:
            m.stop()
        return {"ok": True}

    def enroll_record_start(self):
        """Start recording one enrollment sentence, with the wave showing."""
        r = self.mic_test_start(keep_audio=True, max_seconds=20)
        if r.get("ok"):
            self._enrolling.set()
        return r

    def enroll_record_stop(self):
        """Stop, keep the speech part of the recording, report how much."""
        with self._mic_test_lock:
            m, self.mic_test = self.mic_test, None
        # The live microphone's VAD closes an utterance ~0.6 s after the
        # speech ends; keep suppressing until that one has been cut.
        threading.Timer(1.5, self._enrolling.clear).start()
        if m is None:
            return {"error": "Nothing was recording."}
        m.stop()
        sensitivity = (self.store.config.get("asr") or {}).get("sensitivity", 50)
        speech = asr.speech_only(m.audio(), sensitivity=sensitivity)
        seconds = len(speech) / 32000.0
        if seconds < speaker.MIN_SPEECH_SECONDS:
            return {"error": "Only %.1f s of speech was heard - read the whole sentence, "
                             "a little louder." % seconds, "seconds": round(seconds, 1)}
        self._enroll_clips.append(speech)
        return {"ok": True, "seconds": round(seconds, 1), "recorded": len(self._enroll_clips)}

    def enroll_reset(self):
        self._enroll_clips = []
        return self.speaker_status()

    def enroll_finish(self):
        """Turn the recorded sentences into the owner's voiceprint and save it.

        Only the averaged embedding is stored - 256 numbers, not the audio.
        The check is switched on here, because enrolling is the owner asking
        for it; it can be switched off again beside the same button.
        """
        v, why = self.verifier()
        if v is None:
            return {"error": why}
        clips, self._enroll_clips = self._enroll_clips, []
        r = speaker.enroll(v, clips)
        if r.get("error"):
            return {"error": "Could not build a voiceprint: %s" % r["error"]}
        cfg = dict(self.store.config.get("speaker") or {})
        cfg.update({"enabled": True, "embedding": r["embedding"], "clips": r["clips"],
                    "seconds": round(r["seconds"], 1),
                    "consistency": round(r["consistency"], 3),
                    "enrolled_at": datetime.now().isoformat(timespec="seconds")})
        cfg.setdefault("threshold", speaker.DEFAULT_THRESHOLD)
        self.store.config["speaker"] = cfg
        self.store.save_config()
        self.push_voice_state(self.voice_state, self.voice_detail)
        return self.speaker_status()

    def speaker_check(self):
        """Record-and-score, for "does it still know me?". Uses the clip just
        recorded with enroll_record_start/stop, without keeping it."""
        v, why = self.verifier()
        if v is None:
            return {"error": why}
        cfg = self.store.config.get("speaker") or {}
        if not cfg.get("embedding"):
            return {"error": "No voice enrolled yet."}
        if not self._enroll_clips:
            return {"error": "Record a sentence first."}
        clip = self._enroll_clips.pop()
        emb = v.embed(clip)
        if emb is None:
            return {"error": "Too short to check."}
        score = speaker.cosine(emb, cfg["embedding"])
        threshold = self._threshold(cfg)
        return {"ok": True, "score": round(score, 3), "threshold": threshold,
                "match": speaker.is_owner(score, threshold)}

    def speaker_save(self, fields):
        """Switch the check on or off, move the threshold, or forget the voice."""
        fields = fields or {}
        cfg = dict(self.store.config.get("speaker") or {})
        if "enabled" in fields:
            cfg["enabled"] = bool(fields["enabled"]) and bool(cfg.get("embedding"))
        if "threshold" in fields:
            try:
                cfg["threshold"] = max(0.0, min(1.0, float(fields["threshold"])))
            except (TypeError, ValueError):
                return {"error": "The threshold must be a number between 0 and 1."}
        if fields.get("forget"):
            cfg.update({"enabled": False, "embedding": [], "clips": 0, "seconds": 0.0,
                        "consistency": 0.0, "enrolled_at": ""})
        self.store.config["speaker"] = cfg
        self.store.save_config()
        self.push_voice_state(self.voice_state, self.voice_detail)
        return self.speaker_status()

    # --- the windows ---------------------------------------------------------

    def voice_snapshot(self):
        """The draft plus everything the voice bar shows, in one payload.

        A window that was hidden missed every push while it was away, so it
        pulls this once on show rather than waiting for the next sentence.
        """
        draft = self.draft.snapshot()
        t = self._target_topic(draft["meta"])
        _asr = self.store.config.get("asr") or {}
        _voice = self.store.config.get("voice") or {}
        _sp = self.store.config.get("speaker") or {}
        return {
            "draft": draft,
            "topic": (t or {}).get("title") or "",
            "topic_id": (t or {}).get("id") or "",
            "subtopic": draft["meta"].get("subtopic") or "",
            "state": self.voice_state,
            "detail": self.voice_detail,
            "heard": self.voice_heard,
            "always_on": bool(_voice.get("always_on", True)),
            "enabled": bool(_asr.get("enabled")),
            # "Configured" decides whether the popup shows the voice strip at
            # all: someone who never set voice up gets a capture form, not a
            # dormant panel.
            "configured": bool((_asr.get("api_key") or "").strip()),
            "listening": bool(self.asr_logger is not None),
            "mini": bool(self.popup_mini),
            "held": len(self.held),
            "speaker_on": bool(_sp.get("enabled") and _sp.get("embedding")),
        }

    def push_voice_state(self, state, detail=""):
        """Tell both windows what just happened, with the draft alongside.

        The draft travels with every push rather than being fetched after
        one: a push followed by a round-trip would let the bar render a draft
        that was already stale. JSON-encoded - a transcript must never be able
        to break out of the argument list.
        """
        self.voice_state = state
        self.voice_detail = detail or ""
        try:
            js = "voiceState(%s)" % json.dumps(self.voice_snapshot())
        except Exception:
            return
        for window, visible in ((self.popup, self.popup_visible),
                                (self.full, self.full_visible)):
            if window is None or not visible:
                continue
            try:
                window.evaluate_js(js)
            except Exception:
                pass

    def set_popup_mini(self, mini):
        """Collapse the quick-capture window to a bar, or restore it.

        The resize goes through ctypes rather than window.resize() for the
        same reason _set_topmost does: this is reachable from the JS bridge
        and from the hotkey thread, and a pywebview property setter off the
        UI thread deadlocks against the GIL (challenge C5).
        """
        mini = bool(mini)
        self.popup_mini = mini
        cfg = self.store.config.setdefault("voice", {})
        cfg["mini"] = mini
        try:
            self.store.save_config()
        except Exception:
            traceback.print_exc()
        if mini:
            _set_window_size(self.popup_hwnd, MINI_W, MINI_H)
        else:
            _set_window_size(self.popup_hwnd, POPUP_W, POPUP_H)
        try:
            if self.popup is not None:
                self.popup.evaluate_js("popupMini(%s)" % ("true" if mini else "false"))
        except Exception:
            pass
        return {"mini": mini}

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
        # In always-on mode the mini bar is the primary surface, and the
        # transport states (listening / transcribing) only ever reach a window
        # through here. Mirror them onto the voice channel so the bar can show
        # what the microphone is DOING, not only what it decided. VoiceLogger
        # emits "listening" once when the stream opens rather than after every
        # utterance, so this does not stamp over "heard" a moment later.
        try:
            if (self.store.config.get("voice") or {}).get("always_on", True):
                self.push_voice_state(state, detail)
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
            if kind != "link" and text.strip():
                self.refine_kind(topic["id"], r.get("entry_id"), text,
                                 bool(payload.get("sources")))
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
        """Ctrl+Alt+V (by default): attach whatever was last copied to the
        draft, and show the popup so the user can see it land.

        One behaviour whether or not voice is on - there is one draft now,
        and a copied link is a source for the point being composed, spoken or
        typed. Fires on the Win32 hotkey message-loop thread: the draft is
        locked and the window calls are show/evaluate_js only (challenge C5).
        """
        self.run_voice_command("save", "", via="hotkey")
        self.show_popup()

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
        try:
            self.mic_test_stop()
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
        return "Always-on voice: %s" % ("On" if enabled else "Off")

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
                self.apply_voice_hotkeys()
            except Exception:
                traceback.print_exc()
            try:
                # Come back collapsed if that is how it was left - an
                # always-on session parked as a bar should stay a bar.
                if (self.store.config.get("voice") or {}).get("mini"):
                    self.set_popup_mini(True)
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
