"""mdlite - a small, dependency-free Markdown renderer for Trailmark exports.

Why this exists: the AI polish path used to emit raw Markdown into the HTML
report, so **bold**, `code`, tables and links leaked through as literal
punctuation. This module is the single place where Markdown becomes HTML, and
it is deliberately small: no third-party parser, no C extension, nothing that
grows a PyInstaller one-file build.

Supported: ATX headings (#..######), fenced code blocks, bullet and ordered
lists, blockquotes, horizontal rules, GFM pipe tables, and the inline set
**bold**, __bold__, *italic*, _italic_, ~~strike~~, `code`, [text](url), bare
URLs, and Trailmark's own [n] citation markers.

Everything is escaped first, so untrusted note text can never inject HTML.
"""

import re

__all__ = ["render", "render_inline", "strip_markdown", "esc"]

_CITE_RE = re.compile(r"\[(\d{1,3})\]")
_LINK_RE = re.compile(r"\[([^\]\n]+)\]\(\s*([^)\s]+)\s*\)")
_CODE_RE = re.compile(r"`([^`\n]+)`")
_BOLD_RE = re.compile(r"(?<!\w)(?:\*\*|__)(?=\S)(.+?)(?<=\S)(?:\*\*|__)(?!\w)", re.S)
_ITAL_RE = re.compile(r"(?<![\w*_])[*_](?=[^\s*_])(.+?)(?<=[^\s*_])[*_](?![\w*_])", re.S)
_STRIKE_RE = re.compile(r"~~(?=\S)(.+?)(?<=\S)~~", re.S)
_BARE_URL_RE = re.compile(r"(?<![\"'=>(])\b(https?://[^\s<>\"')\]]+)")
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_HR_RE = re.compile(r"^\s*(?:-{3,}|\*{3,}|_{3,})\s*$")
_UL_RE = re.compile(r"^(\s*)[-*+]\s+(.*)$")
_OL_RE = re.compile(r"^(\s*)(\d+)[.)]\s+(.*)$")
_QUOTE_RE = re.compile(r"^\s*>\s?(.*)$")
_FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})\s*([A-Za-z0-9_+-]*)\s*$")
_TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)+\|?\s*$")


def esc(s):
    return (str(s if s is not None else "")
            .replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;"))


# --- inline ------------------------------------------------------------------

def _protect(text, store):
    """Stash a rendered fragment behind a sentinel so later passes skip it."""
    store.append(text)
    return "\x00%d\x00" % (len(store) - 1)


def render_inline(s, cite_href="#r%s"):
    """Render one span of Markdown inline syntax to HTML. Input is escaped."""
    parts = []
    out = esc(s)

    # code spans first - nothing inside them is Markdown
    out = _CODE_RE.sub(lambda m: _protect("<code>%s</code>" % m.group(1), parts), out)

    # [text](url) links before bare [n] citations, so link labels survive
    def _link(m):
        label, url = m.group(1), m.group(2)
        if url.lower().startswith(("javascript:", "data:", "vbscript:")):
            return _protect(label, parts)
        return _protect('<a href="%s" rel="noreferrer">%s</a>' % (url, label), parts)
    out = _LINK_RE.sub(_link, out)

    # Trailmark citation markers -> anchors into the References list
    if cite_href:
        out = _CITE_RE.sub(
            lambda m: _protect('<a class="cite" href="%s">[%s]</a>'
                               % (cite_href % m.group(1), m.group(1)), parts),
            out)

    out = _BOLD_RE.sub(lambda m: "<strong>%s</strong>" % m.group(1), out)
    out = _ITAL_RE.sub(lambda m: "<em>%s</em>" % m.group(1), out)
    out = _STRIKE_RE.sub(lambda m: "<del>%s</del>" % m.group(1), out)
    out = _BARE_URL_RE.sub(
        lambda m: _protect('<a href="%s" rel="noreferrer">%s</a>' % (m.group(1), m.group(1)), parts),
        out)

    # restore protected fragments (they can nest one level, so loop)
    for _ in range(3):
        if "\x00" not in out:
            break
        out = re.sub(r"\x00(\d+)\x00", lambda m: parts[int(m.group(1))], out)
    return out


def strip_markdown(s):
    """Plain-text version - used for DOCX runs and for previews."""
    out = str(s if s is not None else "")
    out = _CODE_RE.sub(lambda m: m.group(1), out)
    out = _LINK_RE.sub(lambda m: "%s (%s)" % (m.group(1), m.group(2)), out)
    out = _BOLD_RE.sub(lambda m: m.group(1), out)
    out = _ITAL_RE.sub(lambda m: m.group(1), out)
    out = _STRIKE_RE.sub(lambda m: m.group(1), out)
    out = _HEADING_RE.sub(lambda m: m.group(2), out)
    return out


# --- block -------------------------------------------------------------------

class _Builder:
    def __init__(self):
        self.buf = []
        self.stack = []      # open list tags, innermost last

    def close_lists(self, depth=0):
        while len(self.stack) > depth:
            tag, nested = self.stack.pop()
            self.buf.append("</%s>" % tag)
            if nested:
                # we re-opened the parent <li> to nest inside it; close it now
                self.buf.append("</li>")

    def open_list(self, tag):
        # A nested list belongs INSIDE the preceding <li>, not beside it.
        nested = False
        if self.stack and self.buf and self.buf[-1].endswith("</li>"):
            self.buf[-1] = self.buf[-1][: -len("</li>")]
            nested = True
        self.stack.append((tag, nested))
        self.buf.append("<%s>" % tag)

    def add(self, html):
        self.buf.append(html)

    def html(self):
        self.close_lists(0)
        return "".join(self.buf)


def _split_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def _render_table(rows, cite_href):
    head, body = rows[0], rows[1:]
    th = "".join("<th>%s</th>" % render_inline(c, cite_href) for c in head)
    trs = "".join(
        "<tr>%s</tr>" % "".join("<td>%s</td>" % render_inline(c, cite_href) for c in r)
        for r in body)
    return ('<table class="md-table"><thead><tr>%s</tr></thead>'
            "<tbody>%s</tbody></table>") % (th, trs)


def render(md, cite_href="#r%s", heading_offset=0, section_class="sub"):
    """Render a Markdown document to an HTML fragment.

    ``heading_offset`` shifts every heading level down (1 turns ``#`` into
    ``<h2>``), which is what the report shell wants since it owns the ``<h1>``.
    ``section_class`` wraps top-level headings in ``<section>`` so the report
    stylesheet can space them; pass ``None`` to emit bare headings.
    """
    md = (md or "").replace("\r\n", "\n").replace("\r", "\n")
    lines = md.split("\n")
    b = _Builder()
    i = 0
    para = []
    quote = []
    state = {"section": False}

    def flush_para():
        if para:
            b.close_lists(0)
            b.add("<p>%s</p>" % render_inline("\n".join(para), cite_href).replace("\n", "<br>"))
            del para[:]

    def flush_quote():
        if quote:
            b.close_lists(0)
            b.add("<blockquote>%s</blockquote>"
                  % render_inline("\n".join(quote), cite_href).replace("\n", "<br>"))
            del quote[:]

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        fence = _FENCE_RE.match(line)
        if fence:
            flush_para(); flush_quote(); b.close_lists(0)
            marker, lang = fence.group(1)[0], fence.group(2)
            i += 1
            code = []
            while i < len(lines) and not lines[i].strip().startswith(marker * 3):
                code.append(lines[i])
                i += 1
            i += 1  # consume the closing fence
            cls = ' class="lang-%s"' % esc(lang) if lang else ""
            b.add("<pre><code%s>%s</code></pre>" % (cls, esc("\n".join(code))))
            continue

        # a header row followed by a |---|---| separator is a table
        if "|" in stripped and i + 1 < len(lines) and _TABLE_SEP_RE.match(lines[i + 1]):
            flush_para(); flush_quote(); b.close_lists(0)
            rows = [_split_row(stripped)]
            i += 2
            while i < len(lines) and "|" in lines[i] and lines[i].strip():
                rows.append(_split_row(lines[i]))
                i += 1
            b.add(_render_table(rows, cite_href))
            continue

        if not stripped:
            flush_para(); flush_quote(); b.close_lists(0)
            i += 1
            continue

        if _HR_RE.match(line) and not _UL_RE.match(line):
            flush_para(); flush_quote(); b.close_lists(0)
            b.add("<hr>")
            i += 1
            continue

        h = _HEADING_RE.match(stripped)
        if h:
            flush_para(); flush_quote(); b.close_lists(0)
            level = min(6, len(h.group(1)) + heading_offset)
            text = render_inline(h.group(2).strip(), cite_href)
            if section_class and level <= 2:
                if state["section"]:
                    b.add("</section>")
                b.add('<section class="%s">' % section_class)
                state["section"] = True
            b.add("<h%d>%s</h%d>" % (level, text, level))
            i += 1
            continue

        q = _QUOTE_RE.match(line)
        if q:
            flush_para(); b.close_lists(0)
            quote.append(q.group(1))
            i += 1
            continue
        flush_quote()

        ul = _UL_RE.match(line)
        ol = _OL_RE.match(line)
        if ul or ol:
            flush_para()
            indent = len((ul or ol).group(1).expandtabs(4))
            depth = min(2, indent // 2) + 1
            tag = "ul" if ul else "ol"
            if len(b.stack) > depth:
                b.close_lists(depth)
            if len(b.stack) < depth:
                b.open_list(tag)
            elif b.stack and b.stack[-1][0] != tag:
                b.close_lists(depth - 1)
                b.open_list(tag)
            content = ul.group(2) if ul else ol.group(3)
            b.add("<li>%s</li>" % render_inline(content.strip(), cite_href))
            i += 1
            continue

        b.close_lists(0)
        para.append(line.strip())
        i += 1

    flush_para()
    flush_quote()
    out = b.html()
    if state["section"]:
        out += "</section>"
    return out
