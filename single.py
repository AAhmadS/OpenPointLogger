import ctypes
import threading

EVENT_NAME = "Local\\Trailmark_ShowMain"
_handle = None


def ensure_single_instance(show_cb):
    """Return True if this process should run as the main instance.

    If another Trailmark instance is already running, it is signalled to
    show its main window (via show_cb) and this process returns False so
    the caller exits immediately.
    """
    global _handle
    k32 = ctypes.windll.kernel32
    existing = k32.OpenEventW(0x001F0003, False, EVENT_NAME)
    if existing:
        k32.SetEvent(existing)
        k32.CloseHandle(existing)
        return False
    _handle = k32.CreateEventW(None, False, False, EVENT_NAME)
    if not _handle:
        return True

    def waiter():
        while True:
            rc = k32.WaitForSingleObject(_handle, 300)
            if rc == 0:
                try:
                    show_cb()
                except Exception:
                    pass

    threading.Thread(target=waiter, daemon=True).start()
    return True