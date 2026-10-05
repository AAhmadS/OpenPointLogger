import base64
import sys
from pathlib import Path


def asset_path(name):
    base = getattr(sys, "_MEIPASS", None)
    # This module lives in trailmark/, one level below the project root that
    # holds assets/ in a source checkout.
    root = Path(base) if base else Path(__file__).resolve().parent.parent
    return root / "assets" / name


def _b64(name):
    try:
        return "data:image/png;base64," + base64.b64encode(asset_path(name).read_bytes()).decode()
    except Exception:
        return ""


ICON_DATA_URI = _b64("icon-96.png")
LOGO_DATA_URI = _b64("logo.png")
