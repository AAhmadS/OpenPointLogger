import ctypes
import threading
from ctypes import wintypes

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000
WM_HOTKEY = 0x0312
WM_QUIT = 0x0012

MOD_MAP = {
    "ctrl": MOD_CONTROL,
    "alt": MOD_ALT,
    "shift": MOD_SHIFT,
    "win": MOD_WIN,
    "windows": MOD_WIN,
    "super": MOD_WIN,
    "control": MOD_CONTROL,
}


class HotkeyListener:
    def __init__(self, modifiers, key, on_press):
        self.mods = self._parse_mods(modifiers)
        self.vk = self._parse_key(key)
        self.on_press = on_press
        self._id = 0x4343
        self._thread = None
        self._registered = False

    @staticmethod
    def _parse_mods(modifiers):
        flags = 0
        for m in modifiers or []:
            flags |= MOD_MAP.get(str(m).lower(), 0)
        return flags | MOD_NOREPEAT

    @staticmethod
    def _parse_key(key):
        if key is None:
            raise ValueError("No hotkey key set.")
        key = str(key)
        if len(key) == 1 and key.isalpha():
            return ord(key.upper())
        if len(key) == 1 and key.isdigit():
            return ord(key)
        if len(key) == 1 and key.isprintable():
            return ord(key)
        named = {
            "F1": 0x70, "F2": 0x71, "F3": 0x72, "F4": 0x73,
            "F5": 0x74, "F6": 0x75, "F7": 0x76, "F8": 0x77,
            "F9": 0x78, "F10": 0x79, "F11": 0x7A, "F12": 0x7B,
            "SPACE": 0x20, "ENTER": 0x0D, "RETURN": 0x0D,
            "TAB": 0x09, "BACKSPACE": 0x08, "DELETE": 0x2E,
            "INSERT": 0x2D, "HOME": 0x24, "END": 0x23,
            "PGUP": 0x21, "PAGEDOWN": 0x22, "PRIOR": 0x21, "NEXT": 0x22,
            "UP": 0x26, "DOWN": 0x28, "LEFT": 0x25, "RIGHT": 0x27,
            "MINUS": 0xBD, "EQUALS": 0xBB, "DASH": 0xBD,
            "PERIOD": 0xBE, "COMMA": 0xBC, "SEMICOLON": 0xBA,
            "QUOTE": 0xDE, "SLASH": 0xBF, "BACKSLASH": 0xDC,
            "BACKTICK": 0xC0, "BRACKETLEFT": 0xDB, "BRACKETRIGHT": 0xDD,
            "NUMPAD0": 0x60, "NUMPAD1": 0x61, "NUMPAD2": 0x62, "NUMPAD3": 0x63,
            "NUMPAD4": 0x64, "NUMPAD5": 0x65, "NUMPAD6": 0x66, "NUMPAD7": 0x67,
            "NUMPAD8": 0x68, "NUMPAD9": 0x69,
        }
        upper = key.upper()
        if upper in named:
            return named[upper]
        raise ValueError("Unsupported hotkey key: %s" % key)

    @staticmethod
    def probe(modifiers, key):
        user32 = ctypes.windll.user32
        mods = HotkeyListener._parse_mods(modifiers) | MOD_NOREPEAT
        vk = HotkeyListener._parse_key(key)
        ok = user32.RegisterHotKey(None, 0x5092, mods, vk)
        if ok:
            user32.UnregisterHotKey(None, 0x5092)
        return bool(ok)

    @property
    def label(self):
        names = {MOD_CONTROL: "Ctrl", MOD_ALT: "Alt", MOD_SHIFT: "Shift", MOD_WIN: "Win"}
        parts = [names[f] for f in (MOD_CONTROL, MOD_ALT, MOD_SHIFT, MOD_WIN)
                 if self.mods & f and f != MOD_NOREPEAT]
        return "+".join(parts + [chr(self.vk)]) if parts else chr(self.vk)

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        if not self._thread or not self._thread.is_alive():
            return
        user32 = ctypes.windll.user32
        user32.PostThreadMessageW(wintypes.DWORD(self._thread.ident), WM_QUIT, 0, 0)

    def _loop(self):
        user32 = ctypes.windll.user32
        hwnd = None
        ok = user32.RegisterHotKey(None, self._id, self.mods, self.vk)
        self._registered = bool(ok)
        if not ok:
            return
        msg = wintypes.MSG()
        try:
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                if msg.message == WM_HOTKEY and msg.wParam == self._id:
                    try:
                        self.on_press()
                    except Exception:
                        pass
        finally:
            user32.UnregisterHotKey(None, self._id)
            self._registered = False