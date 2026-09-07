"""templates_registry - discovery and rendering of Trailmark export templates.

A template is a folder. Trailmark looks for them in two places, user first so a
hand-written template can shadow a built-in one of the same id:

    %APPDATA%\\Trailmark\\templates\\<id>\\     user templates (yours, never shipped)
    <app>\\templates\\<id>\\                    templates that ship with Trailmark

A template folder contains:

    template.json   required - metadata, and which formats it can produce
    template.html   required for html/pdf output - the page shell
    template.tex    optional  - a LaTeX shell, used when a TeX engine is present
    assets/         optional  - fonts/images, inlined as data URIs at render time

Substitution is deliberately dumb: ``{{name}}`` is replaced by a string, and
``{{#name}}...{{/name}}`` keeps its contents only when ``name`` is non-empty.
No loops, no expressions, no sandbox to get wrong. Everything a template needs
is precomputed by the pipeline and handed over as flat strings.
"""

import base64
import json
import mimetypes
import os
import re
import sys
from pathlib import Path

__all__ = ["available", "load", "render_shell", "user_dir", "builtin_dir",
           "TemplateError", "PLACEHOLDERS"]

_SECTION_RE = re.compile(r"\{\{#([a-z0-9_]+)\}\}(.*?)\{\{/\1\}\}", re.S)
_VAR_RE = re.compile(r"\{\{([a-z0-9_]+)\}\}")
_ASSET_RE = re.compile(r"""(?:src|href)\s*=\s*["'](?!https?:|data:|#)([^"']+)["']""")

#: Every value the pipeline guarantees a template can reference.
PLACEHOLDERS = {
    "title": "Report title (escaped)",
    "subtitle": "Sub-title / topic descriptor",
    "kicker": "Small uppercase line above the title",
    "author": "Author name from settings, may be empty",
    "org": "Organisation from settings, may be empty",
    "date": "Long-form generation date",
    "date_iso": "ISO-8601 generation date",
    "period": "Span the points were collected over",
    "body": "The rendered report body as HTML",
    "toc": "Table of contents as a <nav><ol>, empty when under 3 sections",
    "references": "<li> items for the References list, already numbered",
    "figures": "<figure> blocks for attached screenshots",
    "summary": "One-paragraph abstract, may be empty",
    "count_points": "Number of logged points",
    "count_sources": "Number of distinct cited sources",
    "footer": "Footer line",
    "accent": "Accent colour from template.json",
    "app_version": "Trailmark version string",
}


class TemplateError(Exception):
    pass


def builtin_dir():
    base = getattr(sys, "_MEIPASS", None)
    root = Path(base) if base else Path(__file__).resolve().parent
    return root / "templates"


def user_dir():
    base = Path(os.environ.get("APPDATA") or Path.home()) / "Trailmark" / "templates"
    return base


def _read_manifest(folder):
    mf = folder / "template.json"
    if not mf.exists():
        return None
    try:
        data = json.loads(mf.read_text(encoding="utf-8"))
    except Exception as e:
        raise TemplateError("%s: template.json is not valid JSON (%s)" % (folder.name, e))
    data.setdefault("id", folder.name)
    data.setdefault("name", folder.name.replace("-", " ").title())
    data.setdefault("description", "")
    data.setdefault("purpose", "general")
    data.setdefault("accent", "#c97f2d")
    data.setdefault("formats", ["html", "pdf", "markdown", "docx"])
    data.setdefault("page", {"size": "A4", "margin": "18mm"})
    data["dir"] = str(folder)
    data["source"] = "user" if str(folder).startswith(str(user_dir())) else "builtin"
    data["has_html"] = (folder / "template.html").exists()
    data["has_tex"] = (folder / "template.tex").exists()
    return data


def available(include_broken=False):
    """Every template Trailmark can see, user templates shadowing built-ins."""
    found = {}
    for root in (builtin_dir(), user_dir()):
        if not root.exists():
            continue
        for folder in sorted(root.iterdir()):
            if not folder.is_dir() or folder.name.startswith((".", "_")):
                continue
            try:
                m = _read_manifest(folder)
            except TemplateError:
                if include_broken:
                    found[folder.name] = {"id": folder.name, "name": folder.name,
                                          "broken": True, "dir": str(folder)}
                continue
            if m:
                found[m["id"]] = m
    return sorted(found.values(), key=lambda m: (m.get("source") != "builtin", m["id"]))


def load(template_id):
    for m in available():
        if m["id"] == template_id:
            return m
    raise TemplateError("No template named %r. Known: %s"
                        % (template_id, ", ".join(t["id"] for t in available())))


def _inline_assets(html, folder):
    """Turn relative src/href references into data URIs so the HTML is portable.

    A report is a single file the user can mail to someone; a template that
    reaches out to ../assets/logo.png would break the moment it left the folder.
    """
    def sub(m):
        rel = m.group(1)
        p = (folder / rel).resolve()
        try:
            p.relative_to(folder.resolve())
        except ValueError:
            return m.group(0)          # refuses to escape the template folder
        if not p.exists() or p.stat().st_size > 4 * 1024 * 1024:
            return m.group(0)
        mime = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
        b64 = base64.b64encode(p.read_bytes()).decode()
        return m.group(0).replace(rel, "data:%s;base64,%s" % (mime, b64))
    return _ASSET_RE.sub(sub, html)


def _fill(text, values):
    def section(m):
        key, inner = m.group(1), m.group(2)
        return inner if str(values.get(key) or "").strip() else ""
    text = _SECTION_RE.sub(section, text)
    return _VAR_RE.sub(lambda m: str(values.get(m.group(1), "")), text)


def render_shell(manifest, values, flavour="html"):
    """Fill a template's shell with ``values``. ``flavour`` is 'html' or 'tex'."""
    folder = Path(manifest["dir"])
    name = "template.html" if flavour == "html" else "template.tex"
    path = folder / name
    if not path.exists():
        raise TemplateError("Template %r has no %s" % (manifest["id"], name))
    shell = path.read_text(encoding="utf-8")
    out = _fill(shell, values)
    if flavour == "html":
        out = _inline_assets(out, folder)
    return out
