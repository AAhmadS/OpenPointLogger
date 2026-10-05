"""Trailmark application package.

All modules live here; ``point_logger.py`` at the repo root is the only
entry point (dev: ``python point_logger.py``, shipped: PyInstaller one-file
exe built from ``Trailmark.spec``). Imports between modules are absolute
(``from trailmark import ui``) so they resolve identically from source and
from the frozen exe.
"""
