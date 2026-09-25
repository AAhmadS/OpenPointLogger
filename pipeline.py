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

import citation
import mdlite
import judge
import persian
import templates_registry as templates

__all__ = ["export", "compose_markdown", "STAGES", "PipelineError",
           "NOTES_HEADING", "NOTE_PREFIX", "ground_science", "ordered_refs"]

#: Scientific mode keeps your own thinking out of the sourced argument. It has
#: to be a real heading rather than a styling choice, because the grounding gate
#: needs somewhere it can point at and say "no citation may appear below this".
NOTES_HEADING = "Notes and commentary"
NOTE_PREFIX = "*Note.*"

STAGES = ["compose", "ground", "fill", "render", "verify", "manifest"]
APP_VERSION = "0.4.0"


class PipelineError(Exception):
    pass


def _slug(s):
    s = re.sub(r"[^a-zA-Z0-9\- ]+", "", str(s or "")).strip().lower()
    return (re.sub(r"[\s-]+", "-", s) or "topic")[:60]


def _fmt_date(iso, lang="en", long=True):
    """A stored timestamp as a human date, in the document's own calendar.

    ``lang="fa"`` means Solar Hijri with Persian digits. ISO-8601 output is
    left Gregorian everywhere it appears, because it is the machine-readable
    form and something downstream will parse it.
    """
    try:
        d = datetime.strptime(str(iso)[:19], "%Y-%m-%dT%H:%M:%S")
    except Exception:
        return ""
    if lang == "fa":
        return persian.format_date(d, "fa", long=long)
    return d.strftime("%B %d, %Y" if long else "%Y-%m-%d")


def _num(value, lang="en"):
    """A number the document generated, in the document's own digits.

    Only ever applied to counts this code produced. Digits inside text the
    user wrote are left alone - converting those would quietly corrupt a DOI,
    an ISBN, a URL or a year inside a verbatim quotation.
    """
    return persian.to_persian_digits(str(value)) if lang == "fa" else str(value)


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


def _meta_index(refs):
    """number -> that reference's structured metadata (or None)."""
    return {i + 1: (r.get("meta") or None) for i, r in enumerate(refs or [])}


def markers_for(nums, meta_for, style):
    """The in-text citation strings for one entry, in the configured style."""
    return [citation.inline_marker(n, meta_for.get(n), style) for n in nums]


def ordered_refs(refs, style="numeric"):
    """(number, ref) pairs in the order the reference list should print them.

    The number is always the order of first use, because that is what the
    in-text markers and the #rN anchors point at. Only the *order of the rows*
    changes for the alphabetical styles - which is the actual difference between
    an IEEE list and an APA one.
    """
    pairs = list(enumerate(refs or [], 1))
    if style in citation.ALPHABETICAL:
        pairs.sort(key=lambda pr: citation.sort_key(pr[1].get("meta"), ref_display(pr[1])))
    return pairs


def reference_text(ref, style="numeric"):
    """One reference row: formatted from metadata when there is any, and left
    exactly as the user typed it when there is not."""
    return citation.format_reference(ref.get("meta"), style, fallback=ref_display(ref))


def compose_markdown(topic, entries, cites, with_dates=True, refs=None, science=None):
    """The deterministic composer: points become Markdown grouped by sub-topic.

    This is what 'raw' export uses, and it is also the payload the AI polish
    pass rewrites - so the two paths always start from the same text and stage 2
    can compare them.
    """
    sci = dict(science or {})
    on = bool(sci.get("enabled"))
    style = sci.get("style") or "numeric"
    separate = bool(sci.get("separate_notes", True))
    meta_for = _meta_index(refs) if on else {}

    groups = {}
    order = []
    for e in entries:
        sub = (e.get("subtopic") or "General").strip() or "General"
        if sub not in groups:
            groups[sub] = []
            order.append(sub)
        groups[sub].append(e)

    def dated(line, e):
        # the log date rides along as italic text, not an HTML comment - a
        # comment survives Markdown but not the HTML escaper, and used to
        # show up in the report as literal "<!-- logged ... -->"
        when = _fmt_date(e.get("created"), long=False)
        return "%s *(%s)*" % (line, when) if (with_dates and when) else line

    out = []
    for sub in order:
        out.append("## %s" % sub)
        out.append("")
        notes = []
        for e in groups[sub]:
            nums = cites.get(e["id"], [])
            kind = (e.get("kind") if on else "claim") or "claim"
            if kind not in ("claim", "note", "quote"):
                kind = "claim"
            text = (e.get("text") or "").strip().replace("\n", " ")
            if on and kind == "note":
                # a note is yours: it never carries a citation, in either layout
                line = dated(text, e)
                if separate:
                    notes.append("- %s" % line)
                else:
                    out.append("- %s %s" % (NOTE_PREFIX, line))
                continue
            marks = " ".join(markers_for(nums, meta_for, style) if on
                             else ["[%d]" % n for n in nums])
            body = text if not marks else "%s %s" % (text, marks)
            if on and kind == "quote":
                out.append("> %s" % dated(body, e))
                out.append("")
            else:
                out.append("- %s" % dated(body, e))
        if notes:
            out.append("")
            out.append("### %s" % NOTES_HEADING)
            out.append("")
            out += notes
        out.append("")
    return "\n".join(out).strip()


# --- stage 2: ground ---------------------------------------------------------

_CITE_RE = re.compile(r"\[(\d{1,3})\]")


def ground_citations(original_md, produced_md, ref_count, expected_markers=None):
    """Check the AI pass neither invented nor lost citations.

    Returns (ok, findings). Findings are reported either way - an export that
    dropped three sources is still worth producing, but the user must be told,
    because a citation silently vanishing from a research report is exactly the
    failure the app exists to prevent.
    """
    after = set(int(n) for n in _CITE_RE.findall(produced_md))
    findings = []
    invented = sorted(n for n in after if n < 1 or n > ref_count)
    # In an author-date style the markers are not numbers, so the check is on the
    # literal marker strings the composer emitted rather than on [n].
    if expected_markers is None:
        before = set(int(n) for n in _CITE_RE.findall(original_md))
        missing = ["[%d]" % n for n in sorted(before - after)]
    else:
        missing = sorted({m for m in expected_markers if m not in produced_md})
    if invented:
        findings.append("Invented citation numbers with no matching source: %s."
                        % ", ".join("[%d]" % n for n in invented))
    if missing:
        findings.append("Citations present in your points but missing from the polished "
                        "text: %s." % ", ".join(missing))
    if not produced_md.strip():
        findings.append("The model returned nothing.")
    return (not invented and bool(produced_md.strip())), findings


_AUTHOR_DATE_RE = re.compile(r"\([A-Z][^()]{0,70}?\b(?:1[6-9]|20)\d{2}[a-z]?\)")


def _norm(s):
    return re.sub(r"\s+", " ", str(s or "")).strip().lower()


def _judge_notes(judge_cfg, notes, produced_md):
    """Ask the judge what happened to each note. {} whenever it cannot say."""
    try:
        if not (judge_cfg or {}).get("notes", True):
            return {}
        if not judge.available(judge_cfg):
            return {}
        return judge.note_verdicts(judge_cfg, [e.get("text") or "" for e in notes],
                                   produced_md)
    except Exception:
        return {}


def ground_science(produced_md, entries, sci, judge_cfg=None):
    """Scientific-mode gate: the model may reword, but not reclassify.

    Three things it must not do:

      * turn one of your notes into a sourced claim, by attaching a citation
        to it or by dropping the notes block it lived in;
      * lose a note entirely, which would quietly delete your own thinking;
      * reword a quotation, which stops being a quotation the moment it is
        reworded.

    Two of those are mechanical and stay mechanical. A citation marker either
    appears under the notes heading or it does not; a quotation either survives
    character for character or it is no longer a quotation. Code decides both
    exactly, and a model could only add a way to be wrong about them.

    The third is not mechanical and never was. The model is ALLOWED to reword a
    note - that is what polishing is - so "is the note still there" cannot be a
    substring test. The test that shipped took the first 60 characters and
    looked for them, which fails in both directions: an allowed rewording reads
    as tampering and throws away the whole polished draft, while a note whose
    opening survives and whose meaning was inverted sails through.

    So when a judge is configured, that one question goes to it, per note, all
    in a single request. When it is not configured, or it cannot answer, or it
    is not confident, the substring test is what decides - exactly as before.
    See judge.py for the questions and the measured thresholds.

    Returns (ok, findings). ok=False sends the export back to your own text.
    """
    findings = []
    if not sci.get("enabled"):
        return True, findings
    separate = bool(sci.get("separate_notes", True))
    notes = [e for e in entries if (e.get("kind") or "claim") == "note"]
    quotes = [e for e in entries if (e.get("kind") or "claim") == "quote"]
    hay = _norm(produced_md)

    if notes:
        if separate:
            # everything under a notes heading, up to the next heading, must be
            # citation-free
            blocks = re.split(r"^#{1,4}[ \t]+", produced_md, flags=re.M)
            found = False
            for b in blocks:
                if not b.lower().startswith(NOTES_HEADING.lower()):
                    continue
                found = True
                if _CITE_RE.search(b) or _AUTHOR_DATE_RE.search(b):
                    findings.append("A citation was attached to your own notes - "
                                    "notes are your thinking, not a sourced claim.")
                    break
            if not found:
                findings.append("The '%s' section disappeared from the polished draft."
                                % NOTES_HEADING)
        else:
            for line in produced_md.split("\n"):
                if NOTE_PREFIX in line and (_CITE_RE.search(line)
                                            or _AUTHOR_DATE_RE.search(line)):
                    findings.append("A citation was attached to a line marked as your "
                                    "own note.")
                    break
        # Per note, not per corpus: a verdict that names which note is the
        # only kind the judge below can act on, and the only kind worth
        # showing a person.
        suspect = set()
        for i, e in enumerate(notes):
            head = _norm(e.get("text"))[:60]
            if head and head not in hay:
                suspect.add(i)

        verdicts = _judge_notes(judge_cfg, notes, produced_md)
        for i, e in enumerate(notes):
            got = verdicts.get(i)
            snip = (e.get("text") or "")[:48]
            if got:
                verdict, conf = got
                if verdict == "preserved":
                    # Only an answer this confident may RELAX a protection the
                    # user already had. Below the bar the substring test keeps
                    # its finding, which is the conservative side.
                    if conf >= judge.THRESHOLDS["note_preserved_overturn"]:
                        suspect.discard(i)
                    continue
                suspect.discard(i)   # replaced by something more specific
                if verdict == "altered":
                    findings.append("A note of yours was changed in the polished "
                                    "draft: %s..." % snip)
                else:
                    findings.append("A note of yours is missing from the polished "
                                    "draft: %s..." % snip)
        for i in sorted(suspect):
            findings.append("A note of yours is missing from the polished draft: "
                            "%s..." % ((notes[i].get("text") or "")[:48]))

    for e in quotes:
        body = _norm(e.get("text")).strip('"').strip()
        if body and body not in hay:
            findings.append("A quotation was reworded: %s..." % (e.get("text") or "")[:48])
            break

    return not findings, findings


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


#: The one sentence this application writes onto every page. The Persian is
#: fixed vocabulary, not a translation call, and its half-spaces are counted
#: in tests/test_persian_export.py rather than trusted to look right.
_FOOTER = {
    "en": "Generated by Trailmark - log the point, keep the source.",
    # ساخته‌شده با Trailmark - نکته را ثبت کنید، منبع را نگه دارید.
    "fa": "ساخته‌شده با "
          "Trailmark. نکته را ثبت "
          "کنید، منبع را "
          "نگه دارید.",
}


def build_values(topic, entries, refs, markdown, manifest, meta, style="numeric"):
    body = _anchor_sections(mdlite.render(markdown, cite_href="#r%s", heading_offset=0))
    # value="n" keeps the printed number equal to the citation number even when
    # the rows are sorted by author, which is what an APA list actually wants.
    refs_html = "".join('<li id="r%d" value="%d">%s</li>'
                        % (n, n, mdlite.render_inline(reference_text(r, style), None))
                        for n, r in ordered_refs(refs, style))
    created = topic.get("created")
    closed = topic.get("closed")

    # Which way the page runs is decided by what was written, not by a setting
    # nobody will find. The title and the points decide it; the reference list
    # deliberately does not, because a Persian report citing English sources
    # would otherwise flip to left-to-right at exactly the length where it
    # stops being fixable by hand.
    script = persian.analyse((topic.get("title") or "") + "\n" + markdown)
    lang, page_dir = script["lang"], script["dir"]
    lbl = persian.labels(lang)

    now = datetime.now()
    if closed:
        period = "%s - %s" % (_fmt_date(created, lang), _fmt_date(closed, lang))
    else:
        period = _fmt_date(created, lang)
    return {
        "lang": lang,
        "dir": page_dir,
        "rtl_css": persian.stylesheet(page_dir),
        "l_references": mdlite.esc(lbl["references"]),
        "l_sources": mdlite.esc(lbl["sources"]),
        "l_contents": mdlite.esc(lbl["contents"]),
        "l_abstract": mdlite.esc(lbl["abstract"]),
        "l_figures": mdlite.esc(lbl["figures"]),
        "l_points": mdlite.esc(lbl["points"]),
        "l_period": mdlite.esc(lbl["period"]),
        "l_author": mdlite.esc(lbl["author"]),
        "l_date": mdlite.esc(lbl["date"]),
        "title": mdlite.esc(topic.get("title") or "Untitled"),
        "subtitle": mdlite.esc(meta.get("subtitle") or ""),
        "kicker": mdlite.esc(meta.get("kicker") or manifest.get("kicker") or "Trailmark"),
        "author": mdlite.esc(meta.get("author") or ""),
        "org": mdlite.esc(meta.get("org") or ""),
        # The long date follows the document: a Persian report dated in the
        # Gregorian calendar with Latin digits reads as a translation of an
        # English one. date_iso stays Gregorian ISO-8601 on purpose - it is
        # the machine-readable copy and something will parse it.
        "date": persian.format_date(now, lang),
        "date_iso": now.strftime("%Y-%m-%d"),
        "date_gregorian": _fmt_date(now.isoformat(), "en"),
        "period": mdlite.esc(period),
        "body": body,
        "toc": _toc(markdown),
        "references": refs_html,
        "figures": _figures_html(entries),
        "summary": mdlite.render_inline(meta.get("summary") or "", "#r%s"),
        "count_points": _num(len(entries), lang),
        "count_sources": _num(len(refs), lang),
        "footer": mdlite.esc(meta.get("footer") or _FOOTER.get(lang, _FOOTER["en"])),
        "accent": manifest.get("accent", "#c97f2d"),
        "accent_hex": (manifest.get("accent", "#c97f2d").lstrip("#").upper() or "C97F2D")[:6],
        "app_version": APP_VERSION,
    }


# --- stage 4/5: render + verify ---------------------------------------------

def _write_markdown(path, topic, markdown, refs, folder, entries, style="numeric"):
    lines = ["# %s" % topic.get("title", "Untitled"), ""]
    lines.append("*%d point%s - %d source%s - exported %s*"
                 % (len(entries), "" if len(entries) == 1 else "s",
                    len(refs), "" if len(refs) == 1 else "s",
                    datetime.now().strftime("%Y-%m-%d %H:%M")))
    lines += ["", markdown, "", "## References", ""]
    img_dir = folder / "images"
    for i, r in ordered_refs(refs, style):
        lines.append("%d. %s" % (i, reference_text(r, style)))
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


def _markdown_to_tex(md, refs, style="numeric"):
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
    bib = "\n".join(r"\bibitem{ref%d} %s" % (i, _tex_escape(reference_text(r, style)))
                    for i, r in ordered_refs(refs, style))
    return "\n".join(out), bib


# --- the orchestrator --------------------------------------------------------

def export(topic, entries, refs, cites, export_root, template_id="personal-report",
           formats=("html", "markdown"), polished_markdown=None, meta=None,
           prefer_engine=None, on_stage=None, science=None, judge_cfg=None):
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
    sci = dict(science or {})
    style = (sci.get("style") or "numeric") if sci.get("enabled") else "numeric"
    result["science"] = bool(sci.get("enabled"))
    result["citation_style"] = style
    stage("compose")
    base_md = compose_markdown(topic, entries, cites, refs=refs, science=sci)
    markdown = polished_markdown.strip() if polished_markdown else base_md
    note("compose", True, "%d points, %d chars of Markdown%s"
         % (len(entries), len(markdown),
            ", %s style" % citation.STYLES.get(style, (style,))[0] if sci.get("enabled") else ""))

    # 2 ground
    stage("ground")
    if polished_markdown:
        meta_for = _meta_index(refs) if sci.get("enabled") else {}
        expected = None
        if sci.get("enabled") and style not in ("numeric", "ieee", "vancouver"):
            expected = sorted({m for nums in cites.values() if isinstance(nums, list)
                               for m in markers_for(nums, meta_for, style)})
        ok, findings = ground_citations(base_md, markdown, len(refs), expected)
        sci_ok, sci_findings = ground_science(markdown, entries, sci, judge_cfg)
        findings = findings + sci_findings
        ok = ok and sci_ok
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
    values = build_values(topic, entries, refs, markdown, manifest, meta, style)
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
                folder / "report.md", topic, markdown, refs, folder, entries, style)
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
                tex_body, bib = _markdown_to_tex(markdown, refs, style)
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

    # report.html only ever existed as the source pdf_render renders from; once
    # the PDF is out the door, don't leave it behind unless it was requested.
    if "html" not in formats and "pdf" in result["files"] and html_path.exists():
        html_path.unlink()

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
                "references": [reference_text(r, style) for _n, r in ordered_refs(refs, style)],
                "figures": [{"path": s["value"], "caption": (e.get("text") or "")[:110]}
                            for e in entries for s in e.get("sources", [])
                            if s.get("type") == "image"],
                "accent": manifest.get("accent", "#c97f2d"),
                "footer": values["footer"],
                # The .docx inherits the direction the HTML already settled
                # on, rather than re-deriving it, so the two artefacts of one
                # export can never disagree about which way the report runs.
                "dir": values["dir"],
                "l_figures": values["l_figures"],
                "l_references": values["l_references"],
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
        "science": bool(sci.get("enabled")),
        "citation_style": style,
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
