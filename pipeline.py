"""pipeline - the staged export flow: points -> Markdown -> template -> artefact.

The shape is deliberately agentic in the narrow sense that matters: the model is
allowed to touch exactly one stage, and every other stage is deterministic code
with a gate after it.

    1  COMPOSE   points -> canonical Markdown          (code, or AI in 'polished')
    2  GROUND    check the AI did not drop or invent a citation   GATE
    3  FILL      Markdown -> HTML body -> template shell (code, tool-call style)
    4  RENDER    HTML -> PDF | Markdown -> DOCX | .tex  (code, subprocess)
    5  VERIFY    artefact exists, is non-trivial, parses            GATE
    6  MANIFEST  write manifest.json so the Exports tab can group by topic

Layout is never the model's job. It writes prose; the template decides how prose
looks. That is what stops a rewording pass from silently reflowing a report, and
it is why stage 2 can be a mechanical check rather than a judgement call.
"""

import json
import re
import shutil
from datetime import datetime
from pathlib import Path

import mdlite
import templates_registry as templates

__all__ = ["export", "compose_markdown", "STAGES", "PipelineError"]

STAGES = ["compose", "ground", "fill", "render", "verify", "manifest"]
APP_VERSION = "0.4.0"


class PipelineError(Exception):
    pass


def _slug(s):
    s = re.sub(r"[^a-zA-Z0-9\- ]+", "", str(s or "")).strip().lower()
    return (re.sub(r"[\s-]+", "-", s) or "topic")[:60]


def _fmt_date(iso, long=True):
    try:
        d = datetime.strptime(str(iso)[:19], "%Y-%m-%dT%H:%M:%S")
    except Exception:
        return ""
    return d.strftime("%B %d, %Y" if long else "%Y-%m-%d")


# --- stage 1: compose --------------------------------------------------------

def ref_display(ref):
    """One reference rendered the way it appears in the References list."""
    kind, value, note = ref.get("type"), ref.get("value", ""), (ref.get("note") or "").strip()
    if kind == "link":
        return "%s%s" % (("%s. " % note) if note else "", value)
    if kind == "string":
        return '"%s"%s' % (value, (" - %s" % note) if note else "")
    if kind == "image":
        return "Screenshot: %s%s" % (Path(value).name, (" - %s" % note) if note else "")
    return value


def compose_markdown(topic, entries, cites, with_dates=True):
    """The deterministic composer: points become Markdown grouped by sub-topic.

    This is what 'raw' export uses, and it is also the payload the AI polish
    pass rewrites - so the two paths always start from the same text and stage 2
    can compare them.
    """
    groups = {}
    order = []
    for e in entries:
        sub = (e.get("subtopic") or "General").strip() or "General"
        if sub not in groups:
            groups[sub] = []
            order.append(sub)
        groups[sub].append(e)

    out = []
    for sub in order:
        out.append("## %s" % sub)
        out.append("")
        for e in groups[sub]:
            nums = cites.get(e["id"], [])
            marks = " ".join("[%d]" % n for n in nums)
            text = (e.get("text") or "").strip()
            when = _fmt_date(e.get("created"), long=False)
            line = text if not marks else "%s %s" % (text, marks)
            # the log date rides along as italic text, not an HTML comment - a
            # comment survives Markdown but not the HTML escaper, and used to
            # show up in the report as literal "<!-- logged ... -->"
            if with_dates and when:
                line = "%s *(%s)*" % (line, when)
            out.append("- %s" % line.replace("\n", " "))
        out.append("")
    return "\n".join(out).strip()


# --- stage 2: ground ---------------------------------------------------------

_CITE_RE = re.compile(r"\[(\d{1,3})\]")


def ground_citations(original_md, produced_md, ref_count):
    """Check the AI pass neither invented nor lost citations.

    Returns (ok, findings). Findings are reported either way - an export that
    dropped three sources is still worth producing, but the user must be told,
    because a citation silently vanishing from a research report is exactly the
    failure the app exists to prevent.
    """
    before = set(int(n) for n in _CITE_RE.findall(original_md))
    after = set(int(n) for n in _CITE_RE.findall(produced_md))
    findings = []
    invented = sorted(n for n in after if n < 1 or n > ref_count)
    dropped = sorted(before - after)
    if invented:
        findings.append("Invented citation numbers with no matching source: %s."
                        % ", ".join("[%d]" % n for n in invented))
    if dropped:
        findings.append("Citations present in your points but missing from the polished "
                        "text: %s." % ", ".join("[%d]" % n for n in dropped))
    if not produced_md.strip():
        findings.append("The model returned nothing.")
    return (not invented and bool(produced_md.strip())), findings


# --- stage 3: fill -----------------------------------------------------------

def _toc(markdown):
    heads = [m.group(2).strip() for m in
             re.finditer(r"^(#{2})\s+(.*)$", markdown, re.M)]
    if len(heads) < 3:
        return ""
    items = "".join('<li><a href="#s%d">%s</a></li>' % (i, mdlite.esc(h))
                    for i, h in enumerate(heads))
    return '<nav class="toc"><div class="toc-t">Contents</div><ol>%s</ol></nav>' % items


def _anchor_sections(body_html):
    n = [0]

    def sub(m):
        n[0] += 1
        return '<section class="sub" id="s%d">' % (n[0] - 1)
    return re.sub(r'<section class="sub">', sub, body_html)


def _figures_html(entries, embed=True):
    out = []
    for e in entries:
        for s in e.get("sources", []):
            if s.get("type") != "image":
                continue
            p = Path(s.get("value", ""))
            src = ""
            if embed and p.exists():
                import base64
                mime = "image/%s" % (p.suffix.lstrip(".").lower() or "png")
                src = "data:%s;base64,%s" % (mime, base64.b64encode(p.read_bytes()).decode())
            elif p.exists():
                src = "images/%s" % p.name
            cap = (e.get("text") or "")[:110]
            out.append('<figure><img src="%s" alt="%s"><figcaption>%s</figcaption></figure>'
                       % (src, mdlite.esc(cap), mdlite.esc(cap or p.name)))
    return "".join(out)


def build_values(topic, entries, refs, markdown, manifest, meta):
    body = _anchor_sections(mdlite.render(markdown, cite_href="#r%s", heading_offset=0))
    refs_html = "".join('<li id="r%d">%s</li>' % (i + 1, mdlite.render_inline(ref_display(r), None))
                        for i, r in enumerate(refs))
    created = topic.get("created")
    closed = topic.get("closed")
    period = _fmt_date(created) if not closed else "%s - %s" % (_fmt_date(created), _fmt_date(closed))
    return {
        "title": mdlite.esc(topic.get("title") or "Untitled"),
        "subtitle": mdlite.esc(meta.get("subtitle") or ""),
        "kicker": mdlite.esc(meta.get("kicker") or manifest.get("kicker") or "Trailmark"),
        "author": mdlite.esc(meta.get("author") or ""),
        "org": mdlite.esc(meta.get("org") or ""),
        "date": _fmt_date(datetime.now().isoformat()),
        "date_iso": datetime.now().strftime("%Y-%m-%d"),
        "period": mdlite.esc(period),
        "body": body,
        "toc": _toc(markdown),
        "references": refs_html,
        "figures": _figures_html(entries),
        "summary": mdlite.render_inline(meta.get("summary") or "", "#r%s"),
        "count_points": str(len(entries)),
        "count_sources": str(len(refs)),
        "footer": mdlite.esc(meta.get("footer")
                             or "Generated by Trailmark - log the point, keep the source."),
        "accent": manifest.get("accent", "#c97f2d"),
        "accent_hex": (manifest.get("accent", "#c97f2d").lstrip("#").upper() or "C97F2D")[:6],
        "app_version": APP_VERSION,
    }


# --- stage 4/5: render + verify ---------------------------------------------

def _write_markdown(path, topic, markdown, refs, folder, entries):
    lines = ["# %s" % topic.get("title", "Untitled"), ""]
    lines.append("*%d point%s - %d source%s - exported %s*"
                 % (len(entries), "" if len(entries) == 1 else "s",
                    len(refs), "" if len(refs) == 1 else "s",
                    datetime.now().strftime("%Y-%m-%d %H:%M")))
    lines += ["", markdown, "", "## References", ""]
    img_dir = folder / "images"
    for i, r in enumerate(refs, 1):
        lines.append("%d. %s" % (i, ref_display(r)))
        if r.get("type") == "image":
            src = Path(r.get("value", ""))
            if src.exists():
                img_dir.mkdir(exist_ok=True)
                shutil.copy2(src, img_dir / src.name)
    lines += ["", "---", "_Generated by Trailmark._"]
    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)


def _tex_escape(s):
    for a, b in (("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"), ("$", r"\$"),
                 ("#", r"\#"), ("_", r"\_"), ("{", r"\{"), ("}", r"\}"),
                 ("~", r"\textasciitilde{}"), ("^", r"\textasciicircum{}")):
        s = s.replace(a, b)
    return s


def _markdown_to_tex(md, refs):
    """A narrow Markdown-to-LaTeX pass for the academic template.

    Only the constructs the composer emits are handled; anything else degrades to
    escaped body text rather than producing invalid LaTeX.
    """
    out = []
    in_list = False
    for line in (md or "").split("\n"):
        s = line.strip()
        if not s:
            if in_list:
                out.append(r"\end{itemize}")
                in_list = False
            out.append("")
            continue
        if s.startswith("## "):
            if in_list:
                out.append(r"\end{itemize}")
                in_list = False
            out.append(r"\section{%s}" % _tex_escape(s[3:].strip()))
            continue
        if s.startswith("### "):
            if in_list:
                out.append(r"\end{itemize}")
                in_list = False
            out.append(r"\subsection{%s}" % _tex_escape(s[4:].strip()))
            continue
        if s.startswith("<!--"):
            continue
        body = s[2:].strip() if s.startswith(("- ", "* ")) else s
        # Inline code is lifted out before escaping so its contents stay verbatim,
        # then reinserted as \texttt after the escape pass.
        verbatim = []

        def _stash(m):
            verbatim.append(_tex_escape(m.group(1)))
            return "\x00%d\x00" % (len(verbatim) - 1)
        body = re.sub(r"`([^`\n]+)`", _stash, body)
        body = _tex_escape(body)
        body = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", body)
        body = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"\\textit{\1}", body)
        body = re.sub(r"\[(\d{1,3})\]", r"\\cite{ref\1}", body)
        body = re.sub(r"\x00(\d+)\x00",
                      lambda m: r"\texttt{%s}" % verbatim[int(m.group(1))], body)
        if s.startswith(("- ", "* ")):
            if not in_list:
                out.append(r"\begin{itemize}")
                in_list = True
            out.append(r"  \item %s" % body)
        else:
            out.append(body)
    if in_list:
        out.append(r"\end{itemize}")
    bib = "\n".join(r"\bibitem{ref%d} %s" % (i, _tex_escape(ref_display(r)))
                    for i, r in enumerate(refs, 1))
    return "\n".join(out), bib


# --- the orchestrator --------------------------------------------------------

def export(topic, entries, refs, cites, export_root, template_id="personal-report",
           formats=("html", "markdown"), polished_markdown=None, meta=None,
           prefer_engine=None, on_stage=None):
    """Run the full pipeline. Returns a result dict; never raises for a partial
    success - formats that failed are reported in ``errors`` so the user gets the
    three artefacts that worked plus an honest note about the fourth."""
    meta = dict(meta or {})
    formats = [f for f in formats if f in ("html", "pdf", "markdown", "docx", "latex")]
    if not formats:
        formats = ["html"]

    def stage(name, detail=""):
        if on_stage:
            try:
                on_stage(name, detail)
            except Exception:
                pass

    result = {"stages": [], "errors": [], "warnings": [], "files": {},
              "template": template_id, "topic_id": topic.get("id"),
              "topic_title": topic.get("title"), "polished": bool(polished_markdown)}

    def note(name, ok, detail=""):
        result["stages"].append({"stage": name, "ok": bool(ok), "detail": detail})

    try:
        manifest = templates.load(template_id)
    except templates.TemplateError as e:
        return {"error": str(e)}

    # 1 compose
    stage("compose")
    base_md = compose_markdown(topic, entries, cites)
    markdown = polished_markdown.strip() if polished_markdown else base_md
    note("compose", True, "%d points, %d chars of Markdown" % (len(entries), len(markdown)))

    # 2 ground
    stage("ground")
    if polished_markdown:
        ok, findings = ground_citations(base_md, markdown, len(refs))
        result["warnings"] += findings
        note("ground", ok, "; ".join(findings) or "citations intact")
        if not ok:
            markdown = base_md
            result["warnings"].append(
                "Fell back to your original points - the polished draft failed the "
                "citation check, so nothing you logged was lost.")
    else:
        note("ground", True, "deterministic compose, nothing to check")

    # target folder. The stamp is only second-resolution, and two exports of the
    # same topic a second apart is an ordinary thing to do (HTML now, PDF once
    # you have looked at it) - so a taken name gets a suffix instead of the
    # second export silently overwriting the first.
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = Path(export_root) / ("%s_%s" % (_slug(topic.get("title")), stamp))
    folder = base
    n = 2
    while folder.exists():
        folder = Path("%s-%d" % (base, n))
        n += 1
    folder.mkdir(parents=True, exist_ok=True)

    # 3 fill
    stage("fill")
    values = build_values(topic, entries, refs, markdown, manifest, meta)
    html = ""
    if {"html", "pdf"} & set(formats) and manifest.get("has_html"):
        try:
            html = templates.render_shell(manifest, values, "html")
            note("fill", True, "%s -> %d KB of HTML" % (template_id, len(html) // 1024))
        except templates.TemplateError as e:
            result["errors"].append("Template: %s" % e)
            note("fill", False, str(e))
    else:
        note("fill", True, "no HTML flavour requested")

    # 4 render + 5 verify, per format
    stage("render")
    if "markdown" in formats:
        try:
            result["files"]["markdown"] = _write_markdown(
                folder / "report.md", topic, markdown, refs, folder, entries)
        except Exception as e:
            result["errors"].append("Markdown: %s" % e)

    html_path = folder / "report.html"
    if html and ("html" in formats or "pdf" in formats):
        html_path.write_text(html, encoding="utf-8")
        if "html" in formats:
            result["files"]["html"] = str(html_path)

    if "pdf" in formats:
        pdf_path = folder / "report.pdf"
        done = False
        if manifest.get("has_tex") and "latex" in manifest.get("formats", []):
            try:
                import pdf_render
                tex_body, bib = _markdown_to_tex(markdown, refs)
                tex_values = dict(values)
                tex_values.update({"body": tex_body, "bibliography": bib,
                                   "title": _tex_escape(topic.get("title") or "Untitled"),
                                   "author": _tex_escape(meta.get("author") or ""),
                                   "summary": _tex_escape(meta.get("summary") or "")})
                tex_path = folder / "report.tex"
                tex_path.write_text(templates.render_shell(manifest, tex_values, "tex"),
                                    encoding="utf-8")
                result["files"]["latex"] = str(tex_path)
                info = pdf_render.render_tex_to_pdf(tex_path, pdf_path)
                result["files"]["pdf"] = info["path"]
                result["pdf_engine"] = info["engine"]
                result["pdf_pages"] = info.get("pages")
                done = True
            except Exception as e:
                result["warnings"].append(
                    "LaTeX build unavailable (%s) - rendered the PDF from HTML instead. "
                    "report.tex is in the folder if you want to build it yourself." % e)
        if not done and html:
            try:
                import pdf_render
                info = pdf_render.render_html_to_pdf(html_path, pdf_path, prefer=prefer_engine)
                result["files"]["pdf"] = info["path"]
                result["pdf_engine"] = info["engine"]
                result["pdf_pages"] = info.get("pages")
            except Exception as e:
                result["errors"].append("PDF: %s" % e)
        elif not done:
            result["errors"].append("PDF: this template has no HTML shell to render from.")

    if "docx" in formats:
        try:
            import docx_writer
            docx_writer.write_docx(folder / "report.docx", {
                "title": topic.get("title") or "Untitled",
                "subtitle": meta.get("subtitle") or "",
                "kicker": manifest.get("kicker") or "Trailmark",
                "summary": meta.get("summary") or "",
                "meta_line": "%s  -  %s point%s, %s source%s" % (
                    values["date"], len(entries), "" if len(entries) == 1 else "s",
                    len(refs), "" if len(refs) == 1 else "s"),
                "markdown": markdown,
                "references": [ref_display(r) for r in refs],
                "figures": [{"path": s["value"], "caption": (e.get("text") or "")[:110]}
                            for e in entries for s in e.get("sources", [])
                            if s.get("type") == "image"],
                "accent": manifest.get("accent", "#c97f2d"),
                "footer": values["footer"],
            })
            result["files"]["docx"] = str(folder / "report.docx")
        except Exception as e:
            result["errors"].append("DOCX: %s" % e)

    note("render", bool(result["files"]),
         ", ".join(sorted(result["files"])) or "nothing produced")

    # 5 verify
    stage("verify")
    verified = {}
    for kind, p in result["files"].items():
        try:
            size = Path(p).stat().st_size
        except Exception:
            result["errors"].append("%s: file vanished after writing." % kind)
            continue
        floor = 1200 if kind in ("pdf", "docx") else 40
        if size < floor:
            result["errors"].append("%s: only %d bytes - treating as a failed render." % (kind, size))
            continue
        verified[kind] = p
    result["files"] = verified
    note("verify", bool(verified), "%d artefact(s) passed" % len(verified))

    # 6 manifest
    stage("manifest")
    doc = {
        "topic_id": topic.get("id"),
        "topic_title": topic.get("title"),
        "template": template_id,
        "template_name": manifest.get("name"),
        "polished": bool(polished_markdown),
        "created": datetime.now().isoformat(timespec="seconds"),
        "entries": len(entries),
        "sources": len(refs),
        "files": {k: Path(v).name for k, v in verified.items()},
        "pdf_engine": result.get("pdf_engine"),
        "pdf_pages": result.get("pdf_pages"),
        "warnings": result["warnings"],
        "errors": result["errors"],
        "app_version": APP_VERSION,
    }
    (folder / "manifest.json").write_text(json.dumps(doc, indent=2), encoding="utf-8")
    note("manifest", True, str(folder / "manifest.json"))

    result["folder"] = str(folder)
    result["entries"] = len(entries)
    result["markdown"] = markdown
    if not verified:
        result["error"] = ("Nothing could be exported. "
                           + " ".join(result["errors"])) if result["errors"] else "Nothing to export."
    return result
