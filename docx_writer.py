"""docx_writer - Markdown to .docx with nothing but the standard library.

A .docx is a zip of XML parts. python-docx would be the obvious dependency, but
it pulls lxml, which pulls a compiled extension, which adds several megabytes to
a PyInstaller one-file build for an app whose whole pitch is that it stays out of
the way. Writing the four parts we actually need by hand costs about 300 lines
and zero megabytes.

What is supported: headings 1-4, body paragraphs with bold / italic /
strikethrough / inline-code runs, hyperlinks, bullet and numbered lists,
blockquotes, tables with a header row, horizontal rules, images, and a
References list. That is the whole vocabulary a Trailmark report uses.
"""

import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape as _xesc

import mdlite

__all__ = ["write_docx", "DocxError"]

NS = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
      'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
      'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
      'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"')

EMU_PER_PX = 9525
MAX_IMG_WIDTH_EMU = 5486400          # 6 inches, the usable width of an A4 page


class DocxError(Exception):
    pass


def _x(s):
    return _xesc(str(s if s is not None else ""))


# --- inline runs -------------------------------------------------------------

_TOKEN_RE = re.compile(
    r"(?P<code>`[^`\n]+`)"
    r"|(?P<link>\[[^\]\n]+\]\(\s*[^)\s]+\s*\))"
    r"|(?P<bold>(?:\*\*|__)(?=\S).+?(?<=\S)(?:\*\*|__))"
    r"|(?P<strike>~~(?=\S).+?(?<=\S)~~)"
    r"|(?P<ital>(?<![\w*_])[*_](?=[^\s*_]).+?(?<=[^\s*_])[*_](?![\w*_]))",
    re.S)


def _run(text, bold=False, ital=False, strike=False, code=False, style=None):
    props = []
    if style:
        props.append('<w:rStyle w:val="%s"/>' % style)
    if code:
        props.append('<w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/>')
    if bold:
        props.append("<w:b/>")
    if ital:
        props.append("<w:i/>")
    if strike:
        props.append("<w:strike/>")
    rpr = "<w:rPr>%s</w:rPr>" % "".join(props) if props else ""
    # xml:space=preserve keeps the spaces between adjacent runs
    return '<w:r>%s<w:t xml:space="preserve">%s</w:t></w:r>' % (rpr, _x(text))


class _Rels:
    """Accumulates document relationships (hyperlinks and images)."""

    def __init__(self):
        self.items = []          # (rid, type, target, mode)
        self.media = {}          # zip path -> bytes

    def hyperlink(self, url):
        rid = "rId%d" % (len(self.items) + 100)
        self.items.append((rid, "hyperlink", url, "External"))
        return rid

    def image(self, path):
        p = Path(path)
        if not p.exists():
            return None
        name = "media/img%d%s" % (len(self.media) + 1, p.suffix.lower() or ".png")
        self.media[name] = p.read_bytes()
        rid = "rId%d" % (len(self.items) + 100)
        self.items.append((rid, "image", name, None))
        return rid

    def xml(self):
        rows = "".join(
            '<Relationship Id="%s" Type="http://schemas.openxmlformats.org/'
            'officeDocument/2006/relationships/%s" Target="%s"%s/>'
            % (rid, kind, _x(target), ' TargetMode="External"' if mode else "")
            for rid, kind, target, mode in self.items)
        base = ('<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/'
                'officeDocument/2006/relationships/styles" Target="styles.xml"/>'
                '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/'
                'officeDocument/2006/relationships/numbering" Target="numbering.xml"/>')
        return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/'
                '2006/relationships">%s%s</Relationships>' % (base, rows))


def _runs(text, rels):
    """Split one line of Markdown into Word runs, resolving links to rels."""
    out = []
    pos = 0
    for m in _TOKEN_RE.finditer(text):
        if m.start() > pos:
            out.append(_run(text[pos:m.start()]))
        kind = m.lastgroup
        raw = m.group()
        if kind == "code":
            out.append(_run(raw[1:-1], code=True))
        elif kind == "bold":
            out.append(_run(raw[2:-2], bold=True))
        elif kind == "strike":
            out.append(_run(raw[2:-2], strike=True))
        elif kind == "ital":
            out.append(_run(raw[1:-1], ital=True))
        elif kind == "link":
            label, url = re.match(r"\[([^\]]+)\]\(\s*([^)\s]+)\s*\)", raw).groups()
            rid = rels.hyperlink(url)
            out.append('<w:hyperlink r:id="%s">%s</w:hyperlink>'
                       % (rid, _run(label, style="Hyperlink")))
        pos = m.end()
    if pos < len(text):
        out.append(_run(text[pos:]))
    return "".join(out) or _run("")


def _para(runs_xml, style=None, numid=None, level=0, spacing=None):
    props = []
    if style:
        props.append('<w:pStyle w:val="%s"/>' % style)
    if numid:
        props.append('<w:numPr><w:ilvl w:val="%d"/><w:numId w:val="%d"/></w:numPr>'
                     % (level, numid))
    if spacing:
        props.append(spacing)
    ppr = "<w:pPr>%s</w:pPr>" % "".join(props) if props else ""
    return "<w:p>%s%s</w:p>" % (ppr, runs_xml)


def _image_para(rid, w_px, h_px, alt="image"):
    w = min(int(w_px) * EMU_PER_PX, MAX_IMG_WIDTH_EMU)
    scale = w / float(int(w_px) * EMU_PER_PX) if w_px else 1.0
    h = int(int(h_px) * EMU_PER_PX * scale)
    return (
        '<w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:drawing>'
        '<wp:inline distT="0" distB="0" distL="0" distR="0">'
        '<wp:extent cx="%d" cy="%d"/><wp:docPr id="%d" name="%s"/>'
        '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/'
        'drawingml/2006/picture"><pic:pic>'
        '<pic:nvPicPr><pic:cNvPr id="%d" name="%s"/><pic:cNvPicPr/></pic:nvPicPr>'
        '<pic:blipFill><a:blip r:embed="%s"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
        '<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="%d" cy="%d"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
        '</pic:pic></a:graphicData></a:graphic></wp:inline>'
        "</w:drawing></w:r></w:p>"
        % (w, h, abs(hash(rid)) % 90000 + 1000, _x(alt),
           abs(hash(rid)) % 90000 + 1000, _x(alt), rid, w, h))


def _png_size(data):
    """Width/height of a PNG or JPEG without pulling in Pillow."""
    try:
        if data[:8] == b"\x89PNG\r\n\x1a\n":
            return (int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big"))
        if data[:2] == b"\xff\xd8":
            i = 2
            while i < len(data) - 9:
                if data[i] != 0xFF:
                    i += 1
                    continue
                marker = data[i + 1]
                if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                    return (int.from_bytes(data[i + 7:i + 9], "big"),
                            int.from_bytes(data[i + 5:i + 7], "big"))
                i += 2 + int.from_bytes(data[i + 2:i + 4], "big")
    except Exception:
        pass
    return (800, 500)


# --- block conversion --------------------------------------------------------

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_UL_RE = re.compile(r"^(\s*)[-*+]\s+(.*)$")
_OL_RE = re.compile(r"^(\s*)(\d+)[.)]\s+(.*)$")
_QUOTE_RE = re.compile(r"^\s*>\s?(.*)$")
_HR_RE = re.compile(r"^\s*(?:-{3,}|\*{3,}|_{3,})\s*$")
_FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
_TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)+\|?\s*$")


def _table(rows, rels):
    def cell(text, header):
        shd = '<w:shd w:val="clear" w:fill="F2F0EB"/>' if header else ""
        return ('<w:tc><w:tcPr><w:tcBorders>'
                '<w:top w:val="single" w:sz="4" w:color="D8D4CC"/>'
                '<w:bottom w:val="single" w:sz="4" w:color="D8D4CC"/>'
                '<w:left w:val="nil"/><w:right w:val="nil"/></w:tcBorders>%s</w:tcPr>%s</w:tc>'
                % (shd, _para(_runs(("**%s**" % text) if header else text, rels),
                              style="TableCell")))
    trs = []
    for n, row in enumerate(rows):
        trs.append("<w:tr>%s</w:tr>" % "".join(cell(c, n == 0) for c in row))
    return ('<w:tbl><w:tblPr><w:tblW w:w="5000" w:type="pct"/>'
            '<w:tblLayout w:type="fixed"/></w:tblPr>%s</w:tbl><w:p/>' % "".join(trs))


def _split_row(line):
    line = line.strip().strip("|")
    return [c.strip() for c in line.split("|")]


def _markdown_body(md, rels, heading_offset=0):
    lines = (md or "").replace("\r\n", "\n").split("\n")
    out = []
    para = []
    i = 0

    def flush():
        if para:
            out.append(_para(_runs(" ".join(para), rels), style="Body"))
            del para[:]

    while i < len(lines):
        line = lines[i]
        s = line.strip()

        if _FENCE_RE.match(line):
            flush()
            marker = s[0]
            i += 1
            code = []
            while i < len(lines) and not lines[i].strip().startswith(marker * 3):
                code.append(lines[i])
                i += 1
            i += 1
            for c in code:
                out.append(_para(_run(c, code=True), style="Code"))
            continue

        if "|" in s and i + 1 < len(lines) and _TABLE_SEP_RE.match(lines[i + 1]):
            flush()
            rows = [_split_row(s)]
            i += 2
            while i < len(lines) and "|" in lines[i] and lines[i].strip():
                rows.append(_split_row(lines[i]))
                i += 1
            out.append(_table(rows, rels))
            continue

        if not s:
            flush()
            i += 1
            continue

        if _HR_RE.match(line) and not _UL_RE.match(line):
            flush()
            out.append('<w:p><w:pPr><w:pBdr><w:bottom w:val="single" w:sz="6" '
                       'w:color="D8D4CC"/></w:pBdr></w:pPr></w:p>')
            i += 1
            continue

        h = _HEADING_RE.match(s)
        if h:
            flush()
            level = min(4, len(h.group(1)) + heading_offset)
            out.append(_para(_runs(h.group(2).strip(), rels), style="Heading%d" % level))
            i += 1
            continue

        q = _QUOTE_RE.match(line)
        if q:
            flush()
            out.append(_para(_runs(q.group(1), rels), style="Quote"))
            i += 1
            continue

        ul, ol = _UL_RE.match(line), _OL_RE.match(line)
        if ul or ol:
            flush()
            indent = len((ul or ol).group(1).expandtabs(4))
            level = min(2, indent // 2)
            text = ul.group(2) if ul else ol.group(3)
            out.append(_para(_runs(text.strip(), rels), style="ListParagraph",
                             numid=1 if ul else 2, level=level))
            i += 1
            continue

        para.append(s)
        i += 1

    flush()
    return "".join(out)


# --- parts -------------------------------------------------------------------

def _styles_xml(accent="C97F2D", serif="Georgia", sans="Segoe UI"):
    def st(sid, name, size, color, bold, spacing, font, extra=""):
        return (
            '<w:style w:type="paragraph" w:styleId="%s"><w:name w:val="%s"/>'
            "<w:pPr>%s%s</w:pPr>"
            '<w:rPr><w:rFonts w:ascii="%s" w:hAnsi="%s"/><w:sz w:val="%d"/>'
            '<w:color w:val="%s"/>%s</w:rPr></w:style>'
            % (sid, name, spacing, extra, font, font, size, color,
               "<w:b/>" if bold else ""))
    sp = lambda b, a: '<w:spacing w:before="%d" w:after="%d" w:line="276" w:lineRule="auto"/>' % (b, a)
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            "<w:styles %s>" % NS
            + '<w:docDefaults><w:rPrDefault><w:rPr>'
              '<w:rFonts w:ascii="%s" w:hAnsi="%s"/><w:sz w:val="22"/>'
              '<w:color w:val="1A2230"/></w:rPr></w:rPrDefault></w:docDefaults>' % (serif, serif)
            + st("Title", "Title", 56, "1A2230", True, sp(0, 120), serif)
            + st("Subtitle", "Subtitle", 22, "5C6675", False, sp(0, 360), sans)
            + st("Kicker", "Kicker", 17, accent, True, sp(0, 60), sans,
                 extra='<w:spacing w:val="36"/>')
            + st("Heading1", "heading 1", 32, "1A2230", True, sp(360, 140), serif)
            + st("Heading2", "heading 2", 26, accent, True, sp(320, 120), sans)
            + st("Heading3", "heading 3", 23, "1A2230", True, sp(260, 100), sans)
            + st("Heading4", "heading 4", 22, "5C6675", True, sp(220, 80), sans)
            + st("Body", "Body Text", 22, "1A2230", False, sp(0, 160), serif)
            + st("TableCell", "Table Cell", 19, "1A2230", False, sp(40, 40), sans)
            + st("ListParagraph", "List Paragraph", 22, "1A2230", False, sp(0, 60), serif)
            + st("Code", "Code", 19, "34405A", False, sp(0, 0), "Consolas")
            + st("Quote", "Quote", 22, "5C6675", False, sp(120, 160), serif,
                 extra='<w:ind w:left="480"/><w:pBdr><w:left w:val="single" w:sz="12" '
                       'w:space="10" w:color="%s"/></w:pBdr>' % accent)
            + st("Caption", "caption", 18, "8A8578", False, sp(40, 200), sans)
            + st("Reference", "Reference", 19, "333333", False, sp(0, 60), sans)
            + '<w:style w:type="character" w:styleId="Hyperlink"><w:name w:val="Hyperlink"/>'
              '<w:rPr><w:color w:val="%s"/><w:u w:val="single"/></w:rPr></w:style>' % accent
            + "</w:styles>")


def _numbering_xml(accent="C97F2D"):
    def lvl(i, fmt, text, indent):
        return ('<w:lvl w:ilvl="%d"><w:start w:val="1"/><w:numFmt w:val="%s"/>'
                '<w:lvlText w:val="%s"/><w:lvlJc w:val="left"/>'
                '<w:pPr><w:ind w:left="%d" w:hanging="360"/></w:pPr></w:lvl>'
                % (i, fmt, text, indent))
    bullets = "".join(lvl(i, "bullet", ch, 420 + i * 360)
                      for i, ch in enumerate(("•", "◦", "▪")))
    numbers = "".join(lvl(i, f, t, 420 + i * 360) for i, (f, t) in
                      enumerate((("decimal", "%1."), ("lowerLetter", "%2."),
                                 ("lowerRoman", "%3."))))
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            "<w:numbering %s>"
            '<w:abstractNum w:abstractNumId="1">%s</w:abstractNum>'
            '<w:abstractNum w:abstractNumId="2">%s</w:abstractNum>'
            '<w:num w:numId="1"><w:abstractNumId w:val="1"/></w:num>'
            '<w:num w:numId="2"><w:abstractNumId w:val="2"/></w:num>'
            "</w:numbering>" % (NS, bullets, numbers))


CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Default Extension="png" ContentType="image/png"/>'
    '<Default Extension="jpg" ContentType="image/jpeg"/>'
    '<Default Extension="jpeg" ContentType="image/jpeg"/>'
    '<Default Extension="gif" ContentType="image/gif"/>'
    '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-'
    'officedocument.wordprocessingml.document.main+xml"/>'
    '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-'
    'officedocument.wordprocessingml.styles+xml"/>'
    '<Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-'
    'officedocument.wordprocessingml.numbering+xml"/>'
    "</Types>")

ROOT_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rIdDoc" Type="http://schemas.openxmlformats.org/officeDocument/'
    '2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')

SECT_PR = ('<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
           '<w:pgMar w:top="1418" w:right="1418" w:bottom="1418" w:left="1418" '
           'w:header="708" w:footer="708" w:gutter="0"/></w:sectPr>')


def write_docx(path, doc):
    """Write ``doc`` (the pipeline's document dict) to a .docx at ``path``.

    ``doc`` keys used: title, subtitle, kicker, summary, markdown, references
    (list of display strings), figures (list of {path, caption}), accent,
    meta_line.
    """
    rels = _Rels()
    accent = (doc.get("accent") or "#c97f2d").lstrip("#").upper()[:6] or "C97F2D"
    body = []

    if doc.get("kicker"):
        body.append(_para(_run(doc["kicker"].upper()), style="Kicker"))
    body.append(_para(_run(doc.get("title") or "Untitled"), style="Title"))
    if doc.get("subtitle"):
        body.append(_para(_run(doc["subtitle"]), style="Subtitle"))
    if doc.get("meta_line"):
        body.append(_para(_run(doc["meta_line"]), style="Subtitle"))
    if doc.get("summary"):
        body.append(_para(_runs(doc["summary"], rels), style="Quote"))

    body.append(_markdown_body(doc.get("markdown") or "", rels))

    figures = doc.get("figures") or []
    if figures:
        body.append(_para(_run("Figures"), style="Heading2"))
        for fig in figures:
            rid = rels.image(fig.get("path", ""))
            if not rid:
                continue
            data = rels.media[rels.items[-1][2]]
            w, h = _png_size(data)
            body.append(_image_para(rid, w, h, fig.get("caption", "figure")))
            if fig.get("caption"):
                body.append(_para(_run(fig["caption"]), style="Caption"))

    refs = doc.get("references") or []
    if refs:
        body.append(_para(_run("References"), style="Heading2"))
        for n, r in enumerate(refs, 1):
            body.append(_para(_runs("%d. %s" % (n, r), rels), style="Reference"))

    if doc.get("footer"):
        body.append(_para(_run(doc["footer"]), style="Caption"))

    document = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                "<w:document %s><w:body>%s%s</w:body></w:document>"
                % (NS, "".join(body), SECT_PR))

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).timetuple()[:6]
    try:
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
            def put(name, data):
                info = zipfile.ZipInfo(name, date_time=stamp)
                info.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(info, data)
            put("[Content_Types].xml", CONTENT_TYPES)
            put("_rels/.rels", ROOT_RELS)
            put("word/document.xml", document)
            put("word/styles.xml", _styles_xml(accent=accent))
            put("word/numbering.xml", _numbering_xml(accent=accent))
            put("word/_rels/document.xml.rels", rels.xml())
            for name, data in rels.media.items():
                put("word/" + name, data)
    except Exception as e:
        raise DocxError("Could not write %s: %s" % (path.name, e))
    return str(path)
