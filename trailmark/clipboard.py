"""Clipboard capture for T10/T11 (clipboard-aware source capture, and the
Ctrl+Alt+V auto-detect hotkey that triggers it).

``read()`` is called from two contexts that must never crash: the Win32
hotkey message-loop thread (``point_logger.Controller.on_clipboard_hotkey``)
and the pywebview JS bridge (``point_logger.Api.read_clipboard``, invoked by
the popup's per-row "paste from clipboard" button). An uncaught exception in
either context is worse than a no-op, so every failure mode here degrades to
``{"type": "none", ...}`` rather than raising.
"""

import base64
import ctypes
import io
import re

try:
    from PIL import Image, ImageGrab
except Exception:  # Pillow itself is a hard requirement, but stay defensive.
    Image = None
    ImageGrab = None

CF_UNICODETEXT = 13

if hasattr(ctypes, "windll"):
    # ctypes defaults an undeclared function's return type to a 32-bit
    # c_int, which truncates a 64-bit HANDLE/HGLOBAL on Win64 and makes
    # GlobalLock() fail on a handle that GetClipboardData() actually
    # returned successfully. Declare the real (pointer-sized) signatures
    # once at import time so the handle survives the round trip.
    ctypes.windll.user32.GetClipboardData.restype = ctypes.c_void_p
    ctypes.windll.user32.GetClipboardData.argtypes = [ctypes.c_uint]
    ctypes.windll.kernel32.GlobalLock.restype = ctypes.c_void_p
    ctypes.windll.kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    ctypes.windll.kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]

#: Matches the popup's own screenshot cap (ui.py caps pasted/dropped images at
#: 8*1024*1024 bytes) - a captured clipboard image is downscaled to fit the
#: same ceiling rather than introducing a second, different limit.
MAX_IMAGE_BYTES = 8 * 1024 * 1024

_URL_RE = re.compile(r"^https?://\S+$", re.IGNORECASE)


def _is_single_url(s):
    return bool(_URL_RE.match(s))


def _resample_filter():
    # Pillow >=9.1 moved these onto Image.Resampling; >=10 still keeps the
    # old top-level aliases as of this writing, but don't rely on that.
    resampling = getattr(Image, "Resampling", None)
    if resampling is not None:
        return resampling.LANCZOS
    return getattr(Image, "LANCZOS", 1)


def _encode_image(img):
    """A PIL Image -> a ``data:image/png;base64,...`` URL, downscaled by 3/4
    steps until the encoded size fits under ``MAX_IMAGE_BYTES`` (matching the
    popup's existing screenshot cap) or further downscaling stops helping."""
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA")
    resample = _resample_filter()
    current = img
    while True:
        buf = io.BytesIO()
        current.save(buf, format="PNG", optimize=True)
        raw = buf.getvalue()
        if len(raw) <= MAX_IMAGE_BYTES:
            return "data:image/png;base64," + base64.b64encode(raw).decode("ascii")
        w, h = current.size
        if w <= 64 or h <= 64:
            # can't shrink further - hand back what we have rather than loop
            return "data:image/png;base64," + base64.b64encode(raw).decode("ascii")
        current = current.resize((max(1, w * 3 // 4), max(1, h * 3 // 4)), resample)


def _read_image():
    """A data-URL for a clipboard image, or None if there isn't one (or it
    isn't an image - a list of file paths is deliberately treated as
    "nothing here", since reading arbitrary files off disk is out of scope)."""
    if ImageGrab is None:
        return None
    try:
        grabbed = ImageGrab.grabclipboard()
    except Exception:
        return None
    if grabbed is None or isinstance(grabbed, list):
        return None
    try:
        return _encode_image(grabbed)
    except Exception:
        return None


def _read_text_windows():
    """CF_UNICODETEXT off the Windows clipboard via ctypes, or None."""
    if not hasattr(ctypes, "windll"):
        return None
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    opened = False
    try:
        opened = bool(user32.OpenClipboard(0))
        if not opened:
            return None
        if not user32.IsClipboardFormatAvailable(CF_UNICODETEXT):
            return None
        handle = user32.GetClipboardData(CF_UNICODETEXT)
        if not handle:
            return None
        locked = kernel32.GlobalLock(handle)
        if not locked:
            return None
        try:
            return ctypes.wstring_at(locked)
        finally:
            kernel32.GlobalUnlock(handle)
    except Exception:
        return None
    finally:
        if opened:
            try:
                user32.CloseClipboard()
            except Exception:
                pass


def read():
    """Read whatever is currently on the clipboard.

    Returns ``{"type": "image"|"link"|"text"|"none", "value": ..., "meta": {}}``.
    Image is checked first: a screenshot tool leaves an image on the
    clipboard but may leave stale text from an earlier copy sitting there
    too, and the image is the thing the user just did.
    Never raises.
    """
    try:
        image_url = _read_image()
        if image_url:
            return {"type": "image", "value": image_url, "meta": {}}
    except Exception:
        pass

    try:
        text = _read_text_windows()
    except Exception:
        text = None

    if text:
        text = text.strip()
        if text:
            if _is_single_url(text):
                return {"type": "link", "value": text, "meta": {}}
            return {"type": "text", "value": text, "meta": {}}

    return {"type": "none", "value": None, "meta": {}}
