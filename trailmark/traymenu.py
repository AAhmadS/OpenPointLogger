r"""The notification-area icon and its menu, drawn by us rather than by Windows.

Windows will not theme a tray menu for you. `TrackPopupMenu` renders whatever
the shell decides - on Windows 11 that is a very tall, very pale list that
looks nothing like the rest of Trailmark, and pystray has no hook to change it
because it hands plain strings to `AppendMenu`.

There is exactly one supported way to draw a menu item yourself: create the
item as `MFT_OWNERDRAW` and answer `WM_MEASUREITEM` and `WM_DRAWITEM`. That
needs a window procedure of our own, and once we have one the tray icon is a
single `Shell_NotifyIconW` call - so this module owns both, and pystray is no
longer a dependency.

What it buys, against app/settings-tray.html in the design system: the raised
surface as the menu background, 12px semibold Segoe UI, the sunken surface as
the hover fill on a rounded rect, a brand row at the top, a hairline
separator, a stroked glyph per item, Quit in the danger colour, and the whole
thing following the Windows light/dark setting. Windows 11 still contributes
the rounded window corner and the drop shadow, which is what we want anyway.

Everything here is plain ctypes against user32/gdi32/shell32.
"""

import ctypes
import ctypes.wintypes as wt
import threading
import traceback

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
try:
    dwmapi = ctypes.windll.dwmapi
except Exception:                      # pre-Vista, or a stripped image
    dwmapi = None
shell32 = ctypes.windll.shell32
kernel32 = ctypes.windll.kernel32

LRESULT = ctypes.c_longlong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_long
ULONG_PTR = ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_ulong

WM_DESTROY = 0x0002
WM_CLOSE = 0x0010
WM_QUIT = 0x0012
WM_MEASUREITEM = 0x002C
WM_DRAWITEM = 0x002B
WM_COMMAND = 0x0111
WM_NULL = 0x0000
WM_USER = 0x0400
WM_TRAY = WM_USER + 1
WM_APP = 0x8000
WM_REBUILD = WM_APP + 2

WM_LBUTTONUP = 0x0202
WM_RBUTTONUP = 0x0205
WM_CONTEXTMENU = 0x007B
NIN_SELECT = WM_USER + 0
NIN_KEYSELECT = WM_USER + 1

NIM_ADD, NIM_MODIFY, NIM_DELETE, NIM_SETVERSION = 0, 1, 2, 4
NIF_MESSAGE, NIF_ICON, NIF_TIP = 0x01, 0x02, 0x04
NOTIFYICON_VERSION_4 = 4

MIIM_STATE, MIIM_ID, MIIM_DATA, MIIM_FTYPE = 0x01, 0x02, 0x20, 0x100
MFT_OWNERDRAW = 0x0100
MFS_DISABLED = 0x0003
MIM_BACKGROUND, MIM_APPLYTOSUBMENUS = 0x02, 0x10

TPM_RETURNCMD, TPM_RIGHTBUTTON, TPM_LEFTALIGN, TPM_BOTTOMALIGN = 0x0100, 0x0002, 0x0000, 0x0020
ODS_SELECTED = 0x0001
IMAGE_ICON = 1
LR_LOADFROMFILE, LR_DEFAULTSIZE = 0x0010, 0x0040
TRANSPARENT = 1
DT_SINGLELINE, DT_VCENTER, DT_LEFT, DT_NOPREFIX = 0x20, 0x04, 0x00, 0x0800
PS_SOLID, PS_GEOMETRIC, PS_ENDCAP_ROUND, PS_JOIN_ROUND = 0, 0x00010000, 0x00000000, 0x00000000
CS_DBLCLKS = 0x0008
WM_TIMER = 0x0113
WM_CANCELMODE = 0x001F
#: Windows 11 only. Both are no-ops on 10, which is why nothing checks a build.
DWMWA_WINDOW_CORNER_PREFERENCE, DWMWCP_ROUND = 33, 2
DWMWA_BORDER_COLOR = 34
MENU_CLASS = "#32768"

WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wt.HWND, ctypes.c_uint, wt.WPARAM, wt.LPARAM)


class WNDCLASSEXW(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint), ("style", ctypes.c_uint),
                ("lpfnWndProc", WNDPROC), ("cbClsExtra", ctypes.c_int),
                ("cbWndExtra", ctypes.c_int), ("hInstance", wt.HINSTANCE),
                ("hIcon", wt.HICON), ("hCursor", wt.HANDLE),
                ("hbrBackground", wt.HBRUSH), ("lpszMenuName", wt.LPCWSTR),
                ("lpszClassName", wt.LPCWSTR), ("hIconSm", wt.HICON)]


class NOTIFYICONDATAW(ctypes.Structure):
    _fields_ = [("cbSize", wt.DWORD), ("hWnd", wt.HWND), ("uID", ctypes.c_uint),
                ("uFlags", ctypes.c_uint), ("uCallbackMessage", ctypes.c_uint),
                ("hIcon", wt.HICON), ("szTip", ctypes.c_wchar * 128),
                ("dwState", wt.DWORD), ("dwStateMask", wt.DWORD),
                ("szInfo", ctypes.c_wchar * 256), ("uVersion", ctypes.c_uint),
                ("szInfoTitle", ctypes.c_wchar * 64), ("dwInfoFlags", wt.DWORD),
                ("guidItem", ctypes.c_byte * 16), ("hBalloonIcon", wt.HICON)]


class MENUITEMINFOW(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint), ("fMask", ctypes.c_uint),
                ("fType", ctypes.c_uint), ("fState", ctypes.c_uint),
                ("wID", ctypes.c_uint), ("hSubMenu", wt.HMENU),
                ("hbmpChecked", wt.HBITMAP), ("hbmpUnchecked", wt.HBITMAP),
                ("dwItemData", ULONG_PTR), ("dwTypeData", wt.LPWSTR),
                ("cch", ctypes.c_uint), ("hbmpItem", wt.HBITMAP)]


class MENUINFO(ctypes.Structure):
    _fields_ = [("cbSize", wt.DWORD), ("fMask", wt.DWORD), ("dwStyle", wt.DWORD),
                ("cyMax", ctypes.c_uint), ("hbrBack", wt.HBRUSH),
                ("dwContextHelpID", wt.DWORD), ("dwMenuData", ULONG_PTR)]


class MEASUREITEMSTRUCT(ctypes.Structure):
    _fields_ = [("CtlType", ctypes.c_uint), ("CtlID", ctypes.c_uint),
                ("itemID", ctypes.c_uint), ("itemWidth", ctypes.c_uint),
                ("itemHeight", ctypes.c_uint), ("itemData", ULONG_PTR)]


class DRAWITEMSTRUCT(ctypes.Structure):
    _fields_ = [("CtlType", ctypes.c_uint), ("CtlID", ctypes.c_uint),
                ("itemID", ctypes.c_uint), ("itemAction", ctypes.c_uint),
                ("itemState", ctypes.c_uint), ("hwndItem", wt.HWND),
                ("hDC", wt.HDC), ("rcItem", wt.RECT), ("itemData", ULONG_PTR)]


def _rgb(hexstr):
    """#rrggbb to a GDI COLORREF, which is 0x00bbggrr."""
    h = hexstr.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return (b << 16) | (g << 8) | r


#: the design system's tokens, for the two themes the menu can be drawn in
DARK = {
    "surface_raised": _rgb("#141b26"), "surface_sunken": _rgb("#1b2330"),
    "content": _rgb("#eef1f6"), "content_secondary": _rgb("#97a2b5"),
    "content_muted": _rgb("#6b7385"), "border": _rgb("#2a3342"),
    "accent": _rgb("#f0a94a"), "danger": _rgb("#ff6b6b"),
}
LIGHT = {
    "surface_raised": _rgb("#fffdf9"), "surface_sunken": _rgb("#f1ebdf"),
    "content": _rgb("#201a12"), "content_secondary": _rgb("#6b6150"),
    "content_muted": _rgb("#8f8571"), "border": _rgb("#e2d9c8"),
    "accent": _rgb("#a15716"), "danger": _rgb("#c23b3b"),
}


# ---------------------------------------------------------------------------
# Signatures. Every one of these is load-bearing on 64-bit: ctypes defaults an
# undeclared argument to c_int, so a HINSTANCE or an HMENU silently overflows
# and the call fails with an OverflowError instead of doing anything useful.
_c_int, _c_uint, _P = ctypes.c_int, ctypes.c_uint, ctypes.POINTER

kernel32.GetModuleHandleW.restype = wt.HMODULE
kernel32.GetModuleHandleW.argtypes = [wt.LPCWSTR]

user32.RegisterClassExW.restype = wt.ATOM
user32.RegisterClassExW.argtypes = [_P(WNDCLASSEXW)]
user32.CreateWindowExW.restype = wt.HWND
user32.CreateWindowExW.argtypes = [wt.DWORD, wt.LPCWSTR, wt.LPCWSTR, wt.DWORD,
                                   _c_int, _c_int, _c_int, _c_int,
                                   wt.HWND, wt.HMENU, wt.HINSTANCE, wt.LPVOID]
user32.DestroyWindow.argtypes = [wt.HWND]
user32.DefWindowProcW.restype = LRESULT
user32.DefWindowProcW.argtypes = [wt.HWND, _c_uint, wt.WPARAM, wt.LPARAM]
user32.PostMessageW.argtypes = [wt.HWND, _c_uint, wt.WPARAM, wt.LPARAM]
user32.GetMessageW.argtypes = [_P(wt.MSG), wt.HWND, _c_uint, _c_uint]
user32.TranslateMessage.argtypes = [_P(wt.MSG)]
user32.DispatchMessageW.argtypes = [_P(wt.MSG)]
user32.RegisterWindowMessageW.restype = _c_uint
user32.RegisterWindowMessageW.argtypes = [wt.LPCWSTR]
user32.SetForegroundWindow.argtypes = [wt.HWND]
user32.GetCursorPos.argtypes = [_P(wt.POINT)]
user32.GetDpiForWindow.restype = _c_uint
user32.GetDpiForWindow.argtypes = [wt.HWND]
user32.LoadImageW.restype = wt.HANDLE
user32.LoadImageW.argtypes = [wt.HINSTANCE, wt.LPCWSTR, _c_uint, _c_int, _c_int, _c_uint]
user32.DestroyIcon.argtypes = [wt.HICON]
user32.FillRect.argtypes = [wt.HDC, _P(wt.RECT), wt.HBRUSH]
user32.DrawTextW.argtypes = [wt.HDC, wt.LPCWSTR, _c_int, _P(wt.RECT), _c_uint]

user32.CreatePopupMenu.restype = wt.HMENU
user32.DestroyMenu.argtypes = [wt.HMENU]
user32.SetMenuInfo.argtypes = [wt.HMENU, _P(MENUINFO)]
user32.InsertMenuItemW.argtypes = [wt.HMENU, _c_uint, wt.BOOL, _P(MENUITEMINFOW)]
user32.TrackPopupMenuEx.restype = _c_int
user32.TrackPopupMenuEx.argtypes = [wt.HMENU, _c_uint, _c_int, _c_int, wt.HWND, wt.LPVOID]

gdi32.CreateSolidBrush.restype = wt.HBRUSH
gdi32.CreateSolidBrush.argtypes = [wt.COLORREF]
gdi32.CreatePen.restype = wt.HANDLE
gdi32.CreatePen.argtypes = [_c_int, _c_int, wt.COLORREF]
gdi32.CreateFontW.restype = wt.HANDLE
gdi32.CreateFontW.argtypes = [_c_int] * 8 + [wt.DWORD] * 5 + [wt.LPCWSTR]
gdi32.SelectObject.restype = wt.HANDLE
gdi32.SelectObject.argtypes = [wt.HDC, wt.HANDLE]
gdi32.DeleteObject.argtypes = [wt.HANDLE]
gdi32.GetStockObject.restype = wt.HANDLE
gdi32.GetStockObject.argtypes = [_c_int]
gdi32.SetTextColor.argtypes = [wt.HDC, wt.COLORREF]
gdi32.SetBkMode.argtypes = [wt.HDC, _c_int]
gdi32.RoundRect.argtypes = [wt.HDC] + [_c_int] * 6
gdi32.MoveToEx.argtypes = [wt.HDC, _c_int, _c_int, wt.LPVOID]
gdi32.LineTo.argtypes = [wt.HDC, _c_int, _c_int]
gdi32.Arc.argtypes = [wt.HDC] + [_c_int] * 8

shell32.Shell_NotifyIconW.argtypes = [wt.DWORD, _P(NOTIFYICONDATAW)]

_ENUMTHREADPROC = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
user32.EnumThreadWindows.argtypes = [wt.DWORD, _ENUMTHREADPROC, wt.LPARAM]
user32.GetClassNameW.argtypes = [wt.HWND, wt.LPWSTR, _c_int]
user32.IsWindowVisible.argtypes = [wt.HWND]
user32.SetTimer.argtypes = [wt.HWND, ULONG_PTR, _c_uint, wt.LPVOID]
user32.KillTimer.argtypes = [wt.HWND, ULONG_PTR]
if dwmapi:
    dwmapi.DwmSetWindowAttribute.argtypes = [wt.HWND, wt.DWORD, wt.LPVOID, wt.DWORD]


class Item:
    """One row of the menu.

    `kind` is "item", "sep" or "header". `glyph` names one of the shapes
    _draw_glyph knows how to stroke; an unknown name simply draws nothing,
    which is a missing icon rather than a crash.
    """

    def __init__(self, label="", action=None, kind="item", glyph=None,
                 tone=None):
        self.label = label
        self.action = action
        self.kind = kind
        self.glyph = glyph
        self.tone = tone            # None, "accent" or "danger"


class Tray:
    """A notification-area icon whose menu Trailmark draws itself."""

    _CLASS = "TrailmarkTrayWnd"
    _ICON_ID = 1
    _FIRST_CMD = 100
    _DRESS_TIMER = 1

    def __init__(self, tooltip, items, icon_for_theme, prefers_light,
                 on_activate=None):
        self.tooltip = tooltip
        self.items = items
        self.icon_for_theme = icon_for_theme    # (light: bool) -> path to .ico
        self.prefers_light = prefers_light
        self.on_activate = on_activate
        self.hwnd = None
        self.hicon = None
        self._added = False
        self._stop = threading.Event()
        self._proc = WNDPROC(self._wndproc)     # kept alive for the window's life
        self._taskbar_created = user32.RegisterWindowMessageW("TaskbarCreated")
        self._pal = LIGHT if prefers_light() else DARK
        self._menu_brush = None
        self._font = None
        self._dpi = 96

    # ---------------------------------------------------------------- setup

    def _register(self):
        wc = WNDCLASSEXW()
        wc.cbSize = ctypes.sizeof(WNDCLASSEXW)
        wc.style = CS_DBLCLKS
        wc.lpfnWndProc = self._proc
        wc.hInstance = kernel32.GetModuleHandleW(None)
        wc.lpszClassName = self._CLASS
        # A class name that is already registered means a previous run of this
        # process left one behind; reusing it is fine and is not an error.
        user32.RegisterClassExW(ctypes.byref(wc))
        self.hwnd = user32.CreateWindowExW(
            0, self._CLASS, self.tooltip, 0, 0, 0, 0, 0,
            None, None, wc.hInstance, None)
        if not self.hwnd:
            raise ctypes.WinError()
        try:
            self._dpi = user32.GetDpiForWindow(self.hwnd) or 96
        except Exception:
            self._dpi = 96

    def _px(self, n):
        return int(round(n * self._dpi / 96.0))

    def _load_icon(self):
        path = self.icon_for_theme(self.prefers_light())
        size = user32.GetSystemMetrics(49) or 16       # SM_CXSMICON
        h = user32.LoadImageW(None, str(path), IMAGE_ICON, size, size,
                              LR_LOADFROMFILE)
        if not h:
            h = user32.LoadImageW(None, str(path), IMAGE_ICON, 0, 0,
                                  LR_LOADFROMFILE | LR_DEFAULTSIZE)
        return h

    def _nid(self, flags):
        nid = NOTIFYICONDATAW()
        nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        nid.hWnd = self.hwnd
        nid.uID = self._ICON_ID
        nid.uFlags = flags
        nid.uCallbackMessage = WM_TRAY
        nid.hIcon = self.hicon
        nid.szTip = self.tooltip[:127]
        return nid

    def _add_icon(self):
        if self.hicon:
            user32.DestroyIcon(self.hicon)
        self.hicon = self._load_icon()
        nid = self._nid(NIF_MESSAGE | NIF_ICON | NIF_TIP)
        if not shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(nid)):
            # The shell can refuse while it is still starting up. Modify is the
            # right retry: if the icon is somehow already there, this adopts it.
            shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(nid))
        nid.uVersion = NOTIFYICON_VERSION_4
        shell32.Shell_NotifyIconW(NIM_SETVERSION, ctypes.byref(nid))
        self._added = True

    def refresh_icon(self):
        """Re-read the theme and swap the icon. Safe from any thread."""
        if self.hwnd:
            user32.PostMessageW(self.hwnd, WM_REBUILD, 0, 0)

    # --------------------------------------------------------------- drawing

    def _make_font(self, weight=600):
        h = -self._px(12)
        return gdi32.CreateFontW(
            h, 0, 0, 0, weight, 0, 0, 0,
            1,        # DEFAULT_CHARSET
            0, 0, 5,  # CLEARTYPE_QUALITY
            0, "Segoe UI Variable Text")

    def _rows(self):
        """The menu rows, with the brand header prepended."""
        return [Item("Trailmark", None, "header", "mark")] + list(self.items)

    def _measure(self, mis):
        row = self._rows()[int(mis.itemData)]
        if row.kind == "sep":
            mis.itemHeight = self._px(9)
            mis.itemWidth = self._px(210)
            return
        mis.itemHeight = self._px(34 if row.kind == "item" else 36)
        mis.itemWidth = self._px(210)

    def _draw(self, dis):
        row = self._rows()[int(dis.itemData)]
        p = self._pal
        hdc = dis.hDC
        r = dis.rcItem
        pad = self._px(6)

        if row.kind == "sep":
            y = (r.top + r.bottom) // 2
            self._line(hdc, r.left + pad + self._px(4), y,
                       r.right - pad - self._px(4), y, p["border"], 1)
            return

        # hover fill: a rounded rect inset from the menu edge, per the design
        if dis.itemState & ODS_SELECTED and row.kind == "item":
            self._round_fill(hdc, r.left + pad, r.top, r.right - pad, r.bottom,
                             self._px(7), p["surface_sunken"])

        gx = r.left + pad + self._px(10)
        gy = (r.top + r.bottom) // 2
        stroke = p["content_secondary"]
        text = p["content"]
        if row.tone == "danger":
            stroke = text = p["danger"]
        elif row.tone == "accent" or row.kind == "header":
            stroke = p["accent"]
        self._draw_glyph(hdc, row.glyph, gx, gy, self._px(13), stroke)

        gdi32.SetBkMode(hdc, TRANSPARENT)
        gdi32.SetTextColor(hdc, text)
        font = self._font_header if row.kind == "header" else self._font
        old = gdi32.SelectObject(hdc, font)
        tr = wt.RECT(gx + self._px(22), r.top, r.right - pad, r.bottom)
        user32.DrawTextW(hdc, row.label, -1, ctypes.byref(tr),
                         DT_SINGLELINE | DT_VCENTER | DT_LEFT | DT_NOPREFIX)
        gdi32.SelectObject(hdc, old)

        if row.kind == "header":
            self._line(hdc, r.left + pad, r.bottom - 1, r.right - pad,
                       r.bottom - 1, p["border"], 1)

    # -- small GDI helpers ---------------------------------------------------

    def _line(self, hdc, x1, y1, x2, y2, colour, width):
        pen = gdi32.CreatePen(PS_SOLID, max(1, self._px(width)), colour)
        old = gdi32.SelectObject(hdc, pen)
        gdi32.MoveToEx(hdc, x1, y1, None)
        gdi32.LineTo(hdc, x2, y2)
        gdi32.SelectObject(hdc, old)
        gdi32.DeleteObject(pen)

    def _round_fill(self, hdc, l, t, r, b, radius, colour):
        brush = gdi32.CreateSolidBrush(colour)
        pen = gdi32.CreatePen(PS_SOLID, 1, colour)
        ob, op = gdi32.SelectObject(hdc, brush), gdi32.SelectObject(hdc, pen)
        gdi32.RoundRect(hdc, l, t, r, b, radius * 2, radius * 2)
        gdi32.SelectObject(hdc, ob)
        gdi32.SelectObject(hdc, op)
        gdi32.DeleteObject(brush)
        gdi32.DeleteObject(pen)

    def _fill(self, hdc, l, t, r, b, colour):
        brush = gdi32.CreateSolidBrush(colour)
        rect = wt.RECT(int(l), int(t), int(r), int(b))
        user32.FillRect(hdc, ctypes.byref(rect), brush)
        gdi32.DeleteObject(brush)

    def _draw_glyph(self, hdc, name, cx, cy, size, colour):
        """Stroke one 20px-grid glyph, scaled to `size` and centred on cx,cy."""
        if not name:
            return
        s = size / 20.0
        w = max(1, int(round(1.75 * s)))

        def X(v):
            return int(round(cx - size / 2 + v * s))

        def Y(v):
            return int(round(cy - size / 2 + v * s))

        pen = gdi32.CreatePen(PS_SOLID, w, colour)
        old = gdi32.SelectObject(hdc, pen)
        hollow = gdi32.GetStockObject(5)                # NULL_BRUSH
        ob = gdi32.SelectObject(hdc, hollow)

        if name == "mark":
            # the Trailmark blaze, filled rather than stroked - at 13px a
            # stroked version of it is mud
            gdi32.SelectObject(hdc, old)
            for x, y, bw, bh in ((0.4, 1.0, 16.4, 3.4), (7.6, 3.2, 1.8, 15.8),
                                 (3.0, 9.4, 4.8, 1.7), (3.0, 13.2, 4.8, 1.7),
                                 (9.4, 16.6, 4.8, 1.7)):
                self._fill(hdc, X(x), Y(y), X(x + bw), Y(y + bh), colour)
            gdi32.SelectObject(hdc, ob)
            gdi32.DeleteObject(pen)
            return
        if name == "window":
            gdi32.RoundRect(hdc, X(2.5), Y(3.5), X(17.5), Y(16.5),
                            int(3 * s), int(3 * s))
            gdi32.MoveToEx(hdc, X(2.5), Y(7.5), None)
            gdi32.LineTo(hdc, X(17.5), Y(7.5))
        elif name == "capture":
            gdi32.RoundRect(hdc, X(2.5), Y(4), X(17.5), Y(16),
                            int(3 * s), int(3 * s))
            gdi32.MoveToEx(hdc, X(6.5), Y(10), None)
            gdi32.LineTo(hdc, X(13.5), Y(10))
            gdi32.MoveToEx(hdc, X(10), Y(6.5), None)
            gdi32.LineTo(hdc, X(10), Y(13.5))
        elif name == "hide":
            gdi32.MoveToEx(hdc, X(4), Y(8), None)
            gdi32.LineTo(hdc, X(10), Y(14))
            gdi32.LineTo(hdc, X(16), Y(8))
        elif name == "power":
            gdi32.Arc(hdc, X(3.5), Y(3.5), X(16.5), Y(16.5),
                      X(6), Y(4.5), X(14), Y(4.5))
            gdi32.MoveToEx(hdc, X(10), Y(3), None)
            gdi32.LineTo(hdc, X(10), Y(10))

        gdi32.SelectObject(hdc, ob)
        gdi32.SelectObject(hdc, old)
        gdi32.DeleteObject(pen)

    # ------------------------------------------------------------ the menu

    def _show_menu(self):
        rows = self._rows()
        hmenu = user32.CreatePopupMenu()
        if not hmenu:
            return
        cmd = 0
        try:
            mi = MENUINFO()
            mi.cbSize = ctypes.sizeof(MENUINFO)
            mi.fMask = MIM_BACKGROUND | MIM_APPLYTOSUBMENUS
            mi.hbrBack = self._menu_brush
            user32.SetMenuInfo(hmenu, ctypes.byref(mi))

            for i, row in enumerate(rows):
                info = MENUITEMINFOW()
                info.cbSize = ctypes.sizeof(MENUITEMINFOW)
                info.fMask = MIIM_FTYPE | MIIM_ID | MIIM_DATA | MIIM_STATE
                info.fType = MFT_OWNERDRAW
                info.fState = 0 if row.kind == "item" else MFS_DISABLED
                info.wID = self._FIRST_CMD + i
                info.dwItemData = i
                user32.InsertMenuItemW(hmenu, i, True, ctypes.byref(info))

            pt = wt.POINT()
            user32.GetCursorPos(ctypes.byref(pt))
            # TrackPopupMenuEx blocks, and the menu's own window does not exist
            # until it does - so a one-shot timer fires just after it appears
            # and rounds the corner and recolours the frame from the outside.
            user32.SetTimer(self.hwnd, self._DRESS_TIMER, 12, None)
            # Without this the menu refuses to close when you click elsewhere -
            # the documented workaround, and it is still required.
            user32.SetForegroundWindow(self.hwnd)
            cmd = user32.TrackPopupMenuEx(
                hmenu, TPM_RETURNCMD | TPM_RIGHTBUTTON | TPM_LEFTALIGN | TPM_BOTTOMALIGN,
                pt.x, pt.y, self.hwnd, None)
            user32.PostMessageW(self.hwnd, WM_NULL, 0, 0)
        finally:
            user32.DestroyMenu(hmenu)

        if cmd:
            row = rows[cmd - self._FIRST_CMD]
            if row.action:
                try:
                    row.action()
                except Exception:
                    traceback.print_exc()

    def _dress_menu_window(self):
        """Round the popup's corner and give it the designed border colour.

        An owner-drawn menu keeps the plain square frame Windows has always
        drawn, which next to the rest of the app looks like a bug. The menu
        window belongs to the shell, not to us, but it is created on our
        thread - so it is findable, and DWM will take instructions about any
        window handle.
        """
        if not dwmapi:
            return
        found = []

        def each(h, _):
            b = ctypes.create_unicode_buffer(32)
            user32.GetClassNameW(h, b, 32)
            if b.value == MENU_CLASS and user32.IsWindowVisible(h):
                found.append(h)
            return False if found else True

        cb = _ENUMTHREADPROC(each)
        user32.EnumThreadWindows(kernel32.GetCurrentThreadId(), cb, 0)
        if not found:
            return
        pref = ctypes.c_int(DWMWCP_ROUND)
        dwmapi.DwmSetWindowAttribute(found[0], DWMWA_WINDOW_CORNER_PREFERENCE,
                                     ctypes.byref(pref), ctypes.sizeof(pref))
        col = wt.COLORREF(self._pal["border"])
        dwmapi.DwmSetWindowAttribute(found[0], DWMWA_BORDER_COLOR,
                                     ctypes.byref(col), ctypes.sizeof(col))

    # -------------------------------------------------------------- plumbing

    def _wndproc(self, hwnd, msg, wparam, lparam):
        try:
            if msg == self._taskbar_created:
                # Explorer restarted and took every tray icon with it.
                self._add_icon()
                return 0
            if msg == WM_TIMER and wparam == self._DRESS_TIMER:
                user32.KillTimer(self.hwnd, self._DRESS_TIMER)
                self._dress_menu_window()
                return 0
            if msg == WM_REBUILD:
                self._pal = LIGHT if self.prefers_light() else DARK
                self._rebuild_gdi()
                self._add_icon()
                return 0
            if msg == WM_MEASUREITEM:
                mis = ctypes.cast(lparam, ctypes.POINTER(MEASUREITEMSTRUCT)).contents
                self._measure(mis)
                return 1
            if msg == WM_DRAWITEM:
                dis = ctypes.cast(lparam, ctypes.POINTER(DRAWITEMSTRUCT)).contents
                self._draw(dis)
                return 1
            if msg == WM_TRAY:
                # With NOTIFYICON_VERSION_4 the event is in the low word of
                # lparam and the anchor point is in wparam.
                ev = lparam & 0xFFFF
                if ev in (WM_RBUTTONUP, WM_CONTEXTMENU):
                    self._show_menu()
                elif ev in (WM_LBUTTONUP, NIN_SELECT, NIN_KEYSELECT):
                    if self.on_activate:
                        try:
                            self.on_activate()
                        except Exception:
                            traceback.print_exc()
                return 0
            if msg == WM_DESTROY:
                user32.PostQuitMessage(0)
                return 0
        except Exception:
            traceback.print_exc()
        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def _rebuild_gdi(self):
        for h in (self._menu_brush, self._font, getattr(self, "_font_header", None)):
            if h:
                gdi32.DeleteObject(h)
        self._menu_brush = gdi32.CreateSolidBrush(self._pal["surface_raised"])
        self._font = self._make_font(600)
        self._font_header = self._make_font(700)

    def run(self):
        """Create the window and pump messages. Blocks; call it on a thread."""
        self._register()
        self._rebuild_gdi()
        self._add_icon()
        msg = wt.MSG()
        while not self._stop.is_set():
            got = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if got in (0, -1):
                break
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
        self._teardown()

    def stop(self):
        self._stop.set()
        if self.hwnd:
            user32.PostMessageW(self.hwnd, WM_CLOSE, 0, 0)
            user32.PostMessageW(self.hwnd, WM_QUIT, 0, 0)

    def _teardown(self):
        try:
            if self._added:
                nid = self._nid(0)
                shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(nid))
                self._added = False
        except Exception:
            pass
        for h in (self._menu_brush, self._font, getattr(self, "_font_header", None)):
            if h:
                gdi32.DeleteObject(h)
        self._menu_brush = self._font = self._font_header = None
        if self.hicon:
            user32.DestroyIcon(self.hicon)
            self.hicon = None
        if self.hwnd:
            user32.DestroyWindow(self.hwnd)
            self.hwnd = None
