"""pdf_render - HTML (or LaTeX) to PDF, preferring engines already on the machine.

The design constraint is that Trailmark sits in the tray all day, so nothing here
may be resident and nothing may inflate the installer. That rules out bundling
Chromium via Playwright (a ~150MB download) and rules out shipping a TeX
distribution. Instead every engine is discovered at export time and launched as a
short-lived subprocess:

    1. Microsoft Edge  - present on every supported Windows build, 0 bytes to ship
    2. Google Chrome   - if the user has it
    3. WeasyPrint      - only if the user installed it themselves
    4. Typst / Tectonic / pdflatex - the LaTeX path, for the academic template

Every path ends at the same gate: the PDF must exist, be non-trivial in size, and
parse as a PDF with at least one page. A renderer that writes a blank file and
reports success is worse than one that fails loudly.
"""

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

__all__ = ["render_html_to_pdf", "render_tex_to_pdf", "available_engines",
           "page_count", "PdfError"]

CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0
MIN_PDF_BYTES = 1200


class PdfError(Exception):
    pass


# --- engine discovery --------------------------------------------------------

def _first_existing(*paths):
    for p in paths:
        if p and Path(p).exists():
            return str(p)
    return None


def _edge():
    pf = os.environ.get("ProgramFiles(x86)") or r"C:\Program Files (x86)"
    pf64 = os.environ.get("ProgramFiles") or r"C:\Program Files"
    return _first_existing(
        Path(pf) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
        Path(pf64) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
    ) or shutil.which("msedge")


def _chrome():
    pf = os.environ.get("ProgramFiles") or r"C:\Program Files"
    pfx = os.environ.get("ProgramFiles(x86)") or r"C:\Program Files (x86)"
    la = os.environ.get("LOCALAPPDATA") or ""
    return _first_existing(
        Path(pf) / "Google" / "Chrome" / "Application" / "chrome.exe",
        Path(pfx) / "Google" / "Chrome" / "Application" / "chrome.exe",
        Path(la) / "Google" / "Chrome" / "Application" / "chrome.exe",
    ) or shutil.which("chrome")


def available_engines():
    """What this machine can actually render with, for the Settings panel."""
    return {
        "edge": _edge(),
        "chrome": _chrome(),
        "weasyprint": shutil.which("weasyprint"),
        "typst": shutil.which("typst"),
        "tectonic": shutil.which("tectonic"),
        "xelatex": shutil.which("xelatex"),
        "pdflatex": shutil.which("pdflatex"),
    }


# --- verification ------------------------------------------------------------

def page_count(pdf_path):
    """Best-effort page count without a PDF library.

    Reads the page-tree /Count when it is present and uncompressed, otherwise
    falls back to counting /Type /Page objects. This is a sanity gate, not a
    parser: it answers "did anything render" and nothing more. Returns None when
    the file uses object streams we cannot read, which is not a failure.
    """
    try:
        data = Path(pdf_path).read_bytes()
    except Exception:
        return None
    if not data.startswith(b"%PDF"):
        return None
    for blob in (data,) + tuple(_inflated_streams(data)):
        counts = [int(m.group(1)) for m in
                  re.finditer(rb"/Type\s*/Pages\b[^>]{0,400}?/Count\s+(\d+)", blob)]
        if counts:
            return max(counts)
        pages = len(re.findall(rb"/Type\s*/Page[^s]", blob))
        if pages:
            return pages
    return None


def _inflated_streams(data, limit=64):
    """Decompress the FlateDecode streams so a modern PDF is still countable.

    LaTeX engines pack the page tree into compressed object streams, so the
    plain byte scan finds nothing. zlib is in the standard library, so paying a
    few milliseconds here turns "pages: unknown" into a real gate.
    """
    import zlib
    out = []
    for m in re.finditer(rb"stream\r?\n", data):
        if len(out) >= limit:
            break
        start = m.end()
        end = data.find(b"endstream", start)
        if end < 0:
            continue
        try:
            out.append(zlib.decompress(data[start:end]))
        except Exception:
            continue
    return out


def _verify(pdf_path, engine):
    p = Path(pdf_path)
    if not p.exists():
        raise PdfError("%s produced no file." % engine)
    size = p.stat().st_size
    if size < MIN_PDF_BYTES:
        p.unlink(missing_ok=True)
        raise PdfError("%s produced a %d-byte file - the page rendered empty." % (engine, size))
    if not p.read_bytes()[:5].startswith(b"%PDF"):
        p.unlink(missing_ok=True)
        raise PdfError("%s produced something that is not a PDF." % engine)
    return {"path": str(p), "bytes": size, "pages": page_count(p), "engine": engine}


def _run(cmd, timeout=120, cwd=None):
    try:
        return subprocess.run(cmd, capture_output=True, timeout=timeout, cwd=cwd,
                              creationflags=CREATE_NO_WINDOW)
    except subprocess.TimeoutExpired:
        raise PdfError("Rendering timed out after %ds." % timeout)
    except FileNotFoundError:
        raise PdfError("Renderer not found: %s" % cmd[0])


# --- HTML -> PDF -------------------------------------------------------------

def _chromium_pdf(binary, html_path, pdf_path, engine_name, timeout=120):
    """Print a local HTML file with headless Chromium.

    ``--print-to-pdf`` is used over CDP because it needs no client library, and
    the file is loaded by URL rather than by piping HTML in, so relative asset
    paths still resolve. Page geometry lives in the template's ``@page`` rule;
    ``--no-pdf-header-footer`` stops Chromium stamping its own margins on top.
    """
    url = Path(html_path).resolve().as_uri()
    profile = tempfile.mkdtemp(prefix="trailmark-pdf-")
    cmd = [
        binary,
        "--headless=new",
        "--disable-gpu",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-extensions",
        "--disable-background-networking",
        "--disable-sync",
        "--no-pdf-header-footer",
        "--run-all-compositor-stages-before-draw",
        "--virtual-time-budget=8000",
        "--user-data-dir=%s" % profile,
        "--print-to-pdf=%s" % str(Path(pdf_path).resolve()),
        url,
    ]
    try:
        proc = _run(cmd, timeout=timeout)
        if not Path(pdf_path).exists():
            tail = (proc.stderr or b"").decode("utf-8", "replace")[-400:]
            raise PdfError("%s did not write a PDF. %s" % (engine_name, tail.strip()))
        return _verify(pdf_path, engine_name)
    finally:
        shutil.rmtree(profile, ignore_errors=True)


def render_html_to_pdf(html_path, pdf_path, prefer=None, timeout=120):
    """Render an HTML file to PDF, trying each available engine in turn.

    Returns a dict with path/bytes/pages/engine. Raises PdfError with every
    engine's failure listed if none succeeds - the caller shows that to the user
    rather than silently producing nothing.
    """
    engines = available_engines()
    order = []
    if prefer and engines.get(prefer):
        order.append(prefer)
    for name in ("edge", "chrome", "weasyprint"):
        if name not in order and engines.get(name):
            order.append(name)
    if not order:
        raise PdfError(
            "No PDF engine found. Microsoft Edge ships with Windows and is used "
            "automatically; if it has been removed, install Chrome or run "
            "'pip install weasyprint'.")

    failures = []
    for name in order:
        try:
            if name in ("edge", "chrome"):
                return _chromium_pdf(engines[name], html_path, pdf_path, name, timeout)
            if name == "weasyprint":
                proc = _run([engines[name], str(html_path), str(pdf_path)], timeout=timeout)
                if proc.returncode != 0:
                    raise PdfError((proc.stderr or b"").decode("utf-8", "replace")[-300:])
                return _verify(pdf_path, name)
        except PdfError as e:
            failures.append("%s: %s" % (name, e))
    raise PdfError("PDF rendering failed. " + " | ".join(failures))


# --- LaTeX -> PDF ------------------------------------------------------------

def render_tex_to_pdf(tex_path, pdf_path, timeout=180):
    """Build a .tex to PDF with whichever TeX engine is installed.

    Typst is tried first because it is a single ~15MB binary with no package
    database, then Tectonic (self-installing packages), then a classic
    xelatex/pdflatex if the user has a TeX distribution. When none is present the
    caller falls back to the HTML path - the .tex file is still written, so the
    user can build it elsewhere.
    """
    engines = available_engines()
    tex_path = Path(tex_path).resolve()
    out_dir = Path(pdf_path).resolve().parent
    failures = []

    if engines.get("typst") and tex_path.suffix == ".typ":
        try:
            proc = _run([engines["typst"], "compile", str(tex_path), str(pdf_path)], timeout)
            if proc.returncode == 0:
                return _verify(pdf_path, "typst")
            failures.append("typst: " + (proc.stderr or b"").decode("utf-8", "replace")[-300:])
        except PdfError as e:
            failures.append("typst: %s" % e)

    for name, cmd in (("tectonic", ["--outdir", str(out_dir), str(tex_path)]),
                      ("xelatex", ["-interaction=nonstopmode", "-halt-on-error",
                                   "-output-directory", str(out_dir), str(tex_path)]),
                      ("pdflatex", ["-interaction=nonstopmode", "-halt-on-error",
                                    "-output-directory", str(out_dir), str(tex_path)])):
        if not engines.get(name):
            continue
        try:
            # LaTeX needs two passes to resolve references; tectonic handles it itself
            passes = 1 if name == "tectonic" else 2
            for _ in range(passes):
                proc = _run([engines[name]] + cmd, timeout, cwd=str(tex_path.parent))
            produced = out_dir / (tex_path.stem + ".pdf")
            if produced.exists():
                if str(produced) != str(Path(pdf_path).resolve()):
                    shutil.move(str(produced), str(pdf_path))
                return _verify(pdf_path, name)
            failures.append("%s: %s" % (name, (proc.stdout or b"").decode("utf-8", "replace")[-300:]))
        except PdfError as e:
            failures.append("%s: %s" % (name, e))

    raise PdfError("No LaTeX engine available (%s)."
                   % ("; ".join(failures) if failures else "install typst or tectonic"))
