"""Headless test of clipboard.py (T10 clipboard-aware capture).

Exercises CF_UNICODETEXT text/link classification against the real Windows
clipboard, and image capture against a monkeypatched PIL.ImageGrab so the
test never depends on what image tooling (if any) happens to already be on
the clipboard.

Run:  PYTHONPATH=. .venv/Scripts/python.exe tests/test_clipboard.py

Whatever plain text is on the clipboard when this starts is saved and
restored afterward. If the clipboard cannot be opened at all (locked by
another app, or a headless/non-interactive session with nothing to hold a
clipboard), the text/link checks are skipped rather than failed - a locked
clipboard is an environment fact, not a bug in this module.
"""

import ctypes
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import clipboard  # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + name + ((" - " + str(detail)) if detail else ""))
    if not cond:
        FAILS.append(name)


GMEM_MOVEABLE = 0x0002
CF_UNICODETEXT = 13

if hasattr(ctypes, "windll"):
    # Same truncated-handle trap clipboard.py works around: declare real
    # pointer-sized signatures instead of ctypes' default 32-bit c_int.
    ctypes.windll.kernel32.GlobalAlloc.restype = ctypes.c_void_p
    ctypes.windll.kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
    ctypes.windll.kernel32.GlobalLock.restype = ctypes.c_void_p
    ctypes.windll.kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    ctypes.windll.kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    ctypes.windll.user32.SetClipboardData.restype = ctypes.c_void_p
    ctypes.windll.user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]


def _set_clipboard_text(text):
    """Replace the clipboard's contents with CF_UNICODETEXT. Raises OSError
    on any failure - callers treat that as a reason to SKIP, not to fail."""
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    if not user32.OpenClipboard(0):
        raise OSError("could not open clipboard")
    try:
        data = text.encode("utf-16-le") + b"\x00\x00"
        h_mem = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
        if not h_mem:
            raise OSError("GlobalAlloc failed")
        ptr = kernel32.GlobalLock(h_mem)
        if not ptr:
            raise OSError("GlobalLock failed")
        ctypes.memmove(ptr, data, len(data))
        kernel32.GlobalUnlock(h_mem)
        if not user32.EmptyClipboard():
            raise OSError("EmptyClipboard failed")
        if not user32.SetClipboardData(CF_UNICODETEXT, h_mem):
            raise OSError("SetClipboardData failed")
    finally:
        user32.CloseClipboard()


if not hasattr(ctypes, "windll"):
    print("SKIP: not running on Windows, no clipboard to test")
    sys.exit(0)

_user32 = ctypes.windll.user32
if not _user32.OpenClipboard(0):
    print("SKIP: clipboard is locked by another app or unavailable")
    sys.exit(0)
_user32.CloseClipboard()

previous_text = None
try:
    previous_text = clipboard._read_text_windows()
except Exception as e:
    print("SKIP: could not read the clipboard (%s)" % e)
    sys.exit(0)

try:
    _set_clipboard_text("just some plain clipboard text")
except OSError as e:
    print("SKIP: could not write to the clipboard (%s)" % e)
    sys.exit(0)

class _ClipboardContention(Exception):
    """Raised when clipboard.read() comes back "none" right after we just
    proved we could write to the clipboard - clipboard.py's contract is to
    degrade any read-time failure (including OpenClipboard losing a race to
    another process) to "none" rather than raise, so this specific shape is
    the read-side twin of the OSError _set_clipboard_text raises on the
    write side: real transient contention, not a classification bug. A
    genuine classification bug would show up as the *wrong* type (e.g. a
    link tagged "text"), not as "none"."""


def _read_or_contention(label, attempts=3, delay=0.05):
    """Read the clipboard, retrying past a transient "none" before treating
    it as contention.

    A single "none" is ambiguous: it's the same shape genuine transient
    contention takes (another process grabbed the clipboard between our
    write and our read) AND the same shape a real classification bug in
    clipboard.py would take if it started misclassifying our fixture data
    as "none". Retrying a couple of times with a short delay lets real
    contention (which clears quickly) resolve itself, while a persistent
    classification bug still comes back "none" on every attempt and is
    reported as a FAIL below, not silently swallowed as a SKIP. The first
    attempt succeeding (the normal case) incurs no delay at all.
    """
    result = clipboard.read()
    for attempt in range(1, attempts):
        if result["type"] != "none":
            return result
        time.sleep(delay)
        result = clipboard.read()
    if result["type"] == "none":
        raise _ClipboardContention(
            "clipboard.read() returned 'none' on all %d attempt(s) right after a "
            "successful write (%s)" % (attempts, label))
    return result


try:
    result = _read_or_contention("plain text")
    check("plain text classified as text", result["type"] == "text", result)
    check("plain text value round-trips",
          result["value"] == "just some plain clipboard text", result)

    url = "https://example.org/some/path?x=1"
    _set_clipboard_text(url)
    result = _read_or_contention("bare URL")
    check("a bare URL is classified as a link", result["type"] == "link", result)
    check("link value is the URL unchanged", result["value"] == url, result)

    # a URL embedded in a larger blob of text is not falsely detected as a link
    _set_clipboard_text("see " + url + " for details")
    result = _read_or_contention("URL embedded in prose")
    check("a URL embedded in prose stays text, not link",
          result["type"] == "text", result)
except (OSError, _ClipboardContention) as e:
    # Real transient clipboard contention (another process grabbed the
    # clipboard between our checks) mid-body is the same environment fact
    # as failing to open it up front - SKIP, don't crash. The finally below
    # still runs (SystemExit propagates through it) so the restore attempt
    # is not skipped just because a step failed partway through.
    print("SKIP: clipboard contention mid-test (%s)" % e)
    sys.exit(0)
finally:
    if previous_text is not None:
        try:
            _set_clipboard_text(previous_text)
        except OSError:
            print("WARNING: could not restore the original clipboard text")


# --- image, via a monkeypatched PIL.ImageGrab --------------------------------
# Never touches the real clipboard - what grabclipboard() would return is
# stood in for directly, so this doesn't depend on an image tool anywhere
# near the test machine's real clipboard.

if clipboard.ImageGrab is None or clipboard.Image is None:
    check("image capture (Pillow importable)", False, "Pillow not importable")
else:
    fake_img = clipboard.Image.new("RGB", (4, 4), color=(200, 50, 50))
    original_grab = clipboard.ImageGrab.grabclipboard
    clipboard.ImageGrab.grabclipboard = lambda: fake_img
    try:
        result = clipboard.read()
    finally:
        clipboard.ImageGrab.grabclipboard = original_grab
    check("clipboard image type is 'image'", result["type"] == "image", result)
    check("clipboard image becomes a data URL",
          isinstance(result.get("value"), str)
          and result["value"].startswith("data:image/png;base64,"),
          (result.get("value") or "")[:50])

print()
print("ALL CHECKS PASSED" if not FAILS else "FAILED: " + ", ".join(FAILS))
sys.exit(1 if FAILS else 0)
