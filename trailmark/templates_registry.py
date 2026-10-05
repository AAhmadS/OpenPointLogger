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
           "TemplateError", "PLACEHOLDERS", "write_starter"]

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
    "accent_hex": "The same colour as six bare hex digits, for LaTeX",
    "app_version": "Trailmark version string",

    # --- direction and language -------------------------------------------
    # Decided from the report's own text, not from a setting. A template that
    # wants to work in both directions needs only the first three: put lang
    # and dir on <html>, and rtl_css last inside <style>. Everything else
    # follows from CSS logical properties, which resolve to the same physical
    # sides in a left-to-right document - so adding them costs an English
    # template nothing.
    "lang": "BCP-47 language tag for <html lang>: 'fa' or 'en'",
    "dir": "'rtl' when the major text is right-to-left, else 'ltr'",
    "rtl_css": "Persian typesetting block; EMPTY for a left-to-right document",
    "date_gregorian": "The generation date in the Gregorian calendar, always",

    # --- chrome the template would otherwise hard-code in English ----------
    "l_references": "Label: References",
    "l_sources": "Label: Sources",
    "l_contents": "Label: Contents",
    "l_abstract": "Label: Abstract",
    "l_figures": "Label: Figures",
    "l_points": "Label: Points",
    "l_period": "Label: Period",
    "l_author": "Label: Author",
    "l_date": "Label: Date",
}


#: A template that predates the categories feature (or simply doesn't set one)
#: falls back to this map, keyed by its declared ``purpose``. Anything not
#: listed here - including the default purpose "general" - lands in "personal",
#: which is the safest bucket to over-populate.
_CATEGORY_FALLBACK = {
    "academic": "research",
    "procedure": "research",
    "personal": "personal",
    "business": "business",
    "team": "team",
}


class TemplateError(Exception):
    pass


def builtin_dir():
    base = getattr(sys, "_MEIPASS", None)
    # This module lives in trailmark/, one level below the project root that
    # holds templates/ in a source checkout.
    root = Path(base) if base else Path(__file__).resolve().parent.parent
    return root / "templates"


def user_dir():
    base = Path(os.environ.get("APPDATA") or Path.home()) / "Trailmark" / "templates"
    return base


# ---------------------------------------------------------------------------
# The starter template
# ---------------------------------------------------------------------------

#: A template that works in BOTH directions, written out beside the user's own
#: templates so making a new one starts from something correct rather than
#: from a copy of a built-in that happens to be English.
#:
#: Direction is three lines of a template's work and no more:
#:   1. lang and dir on <html>
#:   2. {{rtl_css}} as the last thing inside <style>
#:   3. CSS logical properties instead of left/right
#: Everything else the pipeline does for it.
_STARTER_HTML = """<!doctype html>
<html lang="{{lang}}" dir="{{dir}}"><head><meta charset="utf-8">
<title>{{title}}</title>
<style>
/* Starter - a deliberately plain template that is correct in both
   directions. Copy the folder, rename it, and change what you like.

   The three things that make it bidirectional are marked BIDI below. Keep
   them and your template works in Persian; drop them and it does not. */
@page{size:A4;margin:18mm}
:root{
  --ink:#1a1a1a; --mut:#5f6570; --rule:#e2e4e8; --accent:{{accent}};
  --sans:"Segoe UI",system-ui,-apple-system,sans-serif;
  --mono:Consolas,"Cascadia Mono",monospace;
}
*{box-sizing:border-box}
html{-webkit-print-color-adjust:exact;print-color-adjust:exact}
body{margin:0;background:#fff;color:var(--ink);font-family:var(--sans);
  font-size:14px;line-height:1.65}
.wrap{max-width:900px;margin:0 auto;padding:36px 28px 56px}

header{border-bottom:2px solid var(--accent);padding-bottom:14px;margin-bottom:26px}
.kicker{font-size:10px;letter-spacing:.14em;text-transform:uppercase;
  color:var(--accent);font-weight:700}
h1{font-size:27px;line-height:1.25;margin:6px 0 4px}
.sub{color:var(--mut);font-size:14px}
.meta{margin-top:10px;font-size:12px;color:var(--mut);
  display:flex;gap:16px;flex-wrap:wrap}

h2{font-size:18px;margin:26px 0 8px;padding-bottom:5px;border-bottom:1px solid var(--rule)}
h3{font-size:15px;margin:18px 0 6px}
p{margin:0 0 11px}

/* BIDI 1: logical, not physical. padding-inline-start resolves to
   padding-left in a left-to-right document and padding-right in a
   right-to-left one, so one declaration is correct in both. */
ul,ol{margin:8px 0 14px;padding-inline-start:22px}
blockquote{margin:12px 0;padding:9px 14px;background:#f7f8f9;
  border-inline-start:3px solid var(--rule);color:var(--mut)}
.summary{background:#f7f8f9;border-inline-start:3px solid var(--accent);
  padding:12px 16px;margin:0 0 22px}

code{font-family:var(--mono);font-size:12.5px;background:#f2f3f5;padding:1px 4px;
  border-radius:3px}
pre{font-family:var(--mono);font-size:12px;background:#f7f8f9;
  border:1px solid var(--rule);border-radius:5px;padding:11px 13px;overflow-x:auto}

table{border-collapse:collapse;width:100%;margin:12px 0;font-size:13px}
/* BIDI 2: start/end, not left/right. */
th,td{border:1px solid var(--rule);padding:6px 9px;text-align:start;
  vertical-align:top}
th{background:#f7f8f9;font-weight:650}

a.cite{color:var(--accent);text-decoration:none;font-weight:600}
figure{margin:16px 0}
figure img{max-width:100%;border:1px solid var(--rule);border-radius:5px;display:block}
figcaption{font-size:12px;color:var(--mut);margin-top:5px}

ol.refs{padding-inline-start:0;list-style:none;counter-reset:ref;font-size:13px}
ol.refs li{counter-increment:ref;position:relative;
  padding-inline-start:2.2em;margin:0 0 5px}
ol.refs li::before{content:"[" counter(ref) "]";position:absolute;
  inset-inline-start:0;color:var(--accent);font-weight:700}

footer{margin-top:34px;padding-top:12px;border-top:1px solid var(--rule);
  font-size:11.5px;color:var(--mut)}

/* BIDI 3: the Persian typesetting block. EMPTY unless the report's own text
   is mostly right-to-left - an English report is byte-identical without it.
   It must be LAST inside <style> so it wins on source order. */
{{rtl_css}}
</style></head><body>
<div class="wrap">
  <header>
    <div class="kicker">{{kicker}}</div>
    <h1>{{title}}</h1>
    {{#subtitle}}<div class="sub">{{subtitle}}</div>{{/subtitle}}
    <div class="meta">
      <span>{{l_date}}: {{date}}</span>
      <span>{{l_period}}: {{period}}</span>
      {{#author}}<span>{{l_author}}: {{author}}</span>{{/author}}
      <span>{{count_points}} / {{count_sources}}</span>
    </div>
  </header>

  {{#summary}}<div class="summary"><b>{{l_abstract}}</b><br>{{summary}}</div>{{/summary}}
  {{#toc}}<nav><b>{{l_contents}}</b>{{toc}}</nav>{{/toc}}

  {{body}}

  {{#figures}}<h2>{{l_figures}}</h2>{{figures}}{{/figures}}
  {{#references}}<h2>{{l_references}}</h2><ol class="refs">{{references}}</ol>{{/references}}

  <footer>{{footer}} &middot; {{app_version}} &middot; {{date_iso}}</footer>
</div>
</body></html>
"""

_STARTER_JSON = """{
  "id": "starter",
  "name": "Starter",
  "purpose": "general",
  "category": "personal",
  "description": "A plain template that is correct in both directions. Copy the folder, rename it, and edit.",
  "kicker": "Report",
  "accent": "#7a5cff",
  "formats": ["html", "pdf", "markdown", "docx"],
  "page": { "size": "A4", "margin": "18mm" }
}
"""


def _starter_readme():
    """Written next to the starter so the placeholder list is never guessed."""
    rows = "\n".join("| `{{%s}}` | %s |" % (k, v) for k, v in sorted(PLACEHOLDERS.items()))
    return """# Writing a Trailmark template

A template is a folder with `template.json` and `template.html`. Drop it in
this directory and Trailmark finds it - no restart, no registration. A folder
whose `id` matches a built-in shadows that built-in.

Start by copying `starter/`.

## Placeholders

`{{name}}` is replaced. `{{#name}}...{{/name}}` keeps its contents only when
that value is non-empty, which is how you hide an Abstract heading on a report
that has no abstract.

| Placeholder | What it is |
|---|---|
%s

## Right-to-left, and Persian

Trailmark decides direction from the report's own text - if the major text is
Persian (or any right-to-left script) the whole document becomes right-to-left.
There is no setting; there is nothing for the reader to get wrong.

Three things make a template work in both directions:

1. **`<html lang="{{lang}}" dir="{{dir}}">`** - the base direction.

2. **`{{rtl_css}}` as the last thing inside `<style>`.** For an English report
   this is the empty string and your template renders exactly as it would have
   without it. For a Persian one it supplies the font stack, the looser
   leading Persian needs, Persian numerals on ordered lists, and bidi
   isolation for URLs and code. Being last matters: it wins on source order.

3. **CSS logical properties instead of physical ones.** Use
   `padding-inline-start` rather than `padding-left`, `border-inline-start`
   rather than `border-left`, `text-align:start` rather than `text-align:left`,
   and `inset-inline-start` rather than `left` on positioned elements. In a
   left-to-right document each of these is *defined* to resolve to the
   physical property you would have written, so this costs an English template
   nothing and is the entire reason a Persian one works.

What Trailmark handles for you when the report is Persian:

- the Solar Hijri calendar and Persian digits in `{{date}}`, `{{period}}` and
  the counts - while `{{date_iso}}` stays Gregorian ISO-8601 because something
  will parse it, and `{{date_gregorian}}` is there if you want both;
- the chrome labels (`{{l_references}}`, `{{l_abstract}}`, ...) in Persian;
- no synthetic italics, because Persian has no italic cuts and a browser
  would shear the glyphs into something that reads as a rendering fault.

What it deliberately does **not** do: touch the text you wrote. Digits inside
a point stay as typed, because converting them would corrupt a DOI, a URL or a
year inside a quotation.

## Testing one

Settings -> Templates shows a live preview of every template against a fixed
sample report, so you can see a change without exporting anything.
""" % rows


def write_starter(dest=None, force=False):
    """Write the starter template and the authoring notes into ``dest``.

    Called whenever the templates folder is opened, so it is never an empty
    directory with no hint of what belongs in it. Existing files are left
    alone unless ``force`` - someone may have edited the starter into their
    own template, and silently overwriting that would be unforgivable.

    Returns the paths actually written.
    """
    root = Path(dest) if dest else user_dir()
    folder = root / "starter"
    folder.mkdir(parents=True, exist_ok=True)
    written = []
    for path, text in ((folder / "template.html", _STARTER_HTML),
                       (folder / "template.json", _STARTER_JSON),
                       (root / "README.md", _starter_readme())):
        if path.exists() and not force:
            continue
        path.write_text(text, encoding="utf-8")
        written.append(str(path))
    return written


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
    if not (isinstance(data.get("category"), str) and data["category"]):
        data["category"] = _CATEGORY_FALLBACK.get(data.get("purpose"), "personal")
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
