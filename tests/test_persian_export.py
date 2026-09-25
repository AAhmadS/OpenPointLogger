"""The Persian half of the export path, end to end through all five templates.

Two questions, and the second one is the one that bites:

  1. Does a Persian report come out right-to-left, in the Solar Hijri
     calendar, with Persian digits and Persian chrome?
  2. Does an ENGLISH report come out exactly as it did before any of this
     existed?

Question 2 is why the CSS conversion used logical properties rather than a
pile of [dir="rtl"] overrides: `padding-inline-start` is DEFINED to resolve to
`padding-left` in a left-to-right context, so the English output is unchanged
by construction. This file checks the construction held.
"""

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import persian          # noqa: E402
import pipeline         # noqa: E402
import templates_registry as templates  # noqa: E402

FAILS = []


def check(label, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + label + (" - %s" % (detail,) if detail else ""))
    if not ok:
        FAILS.append(label)


# A Persian research topic. The points are ordinary Persian sentences with
# their half-spaces in place, one English citation, and one URL - the mix a
# real Persian report has.
FA_TOPIC = {
    "id": "fa1",
    "title": "بررسی بازار "
             "خدمات ابری",
    "status": "closed",
    "created": "2026-03-21T09:00:00",
    "closed": "2026-09-25T18:00:00",
    "subtopics": [],
    "entries": [],
}
FA_ENTRIES = [
    {"id": "e1", "subtopic": "", "kind": "claim",
     "text": "سهم بازار در "
             "دو سال گذشته "
             "دو‌برابر شده "
             "است و رشد ادامه "
             "دارد.",
     "created": "2026-04-02T10:00:00",
     "sources": [{"id": "s1", "type": "link",
                  "value": "https://example.org/market-report",
                  "note": "", "added": "2026-04-02T10:00:00"}]},
    {"id": "e2", "subtopic": "", "kind": "note",
     "text": "به نظر می‌رسد "
             "رقابت در بخش "
             "میانی بیشتر "
             "است.",
     "created": "2026-05-10T11:00:00", "sources": []},
    {"id": "e3", "subtopic": "", "kind": "claim",
     "text": "هزینهٔ جابه‌"
             "جایی داده "
             "مهم‌ترین مانع "
             "است.",
     "created": "2026-06-01T09:30:00",
     "sources": [{"id": "s2", "type": "string",
                  "value": "Armbrust et al., A View of Cloud Computing (2010)",
                  "note": "", "added": "2026-06-01T09:30:00"}]},
]

EN_TOPIC = {"id": "en1", "title": "Cloud services market", "status": "closed",
            "created": "2026-03-21T09:00:00", "closed": "2026-09-25T18:00:00",
            "subtopics": [], "entries": []}
EN_ENTRIES = [
    {"id": "e1", "subtopic": "", "kind": "claim",
     "text": "Market share has doubled over the last two years and growth continues.",
     "created": "2026-04-02T10:00:00",
     "sources": [{"id": "s1", "type": "link", "value": "https://example.org/market-report",
                  "note": "", "added": "2026-04-02T10:00:00"}]},
    {"id": "e2", "subtopic": "", "kind": "note",
     "text": "Competition looks heaviest in the mid market.",
     "created": "2026-05-10T11:00:00", "sources": []},
]


def render(topic, entries, template_id):
    refs, cites = _collect(entries)
    md = pipeline.compose_markdown(topic, entries, cites, refs=refs)
    manifest = templates.load(template_id)
    values = pipeline.build_values(topic, entries, refs, md, manifest, meta={})
    return values, templates.render_shell(manifest, values)


def _collect(entries):
    import point_store
    return point_store.Store._collect_refs(entries)


ALL = [t["id"] for t in templates.available() if t.get("has_html")]


# ---------------------------------------------------------------------------
# 1. The direction verdict
# ---------------------------------------------------------------------------
print("\n-- direction --")

fa_values, _ = render(FA_TOPIC, FA_ENTRIES, "personal-report")
en_values, _ = render(EN_TOPIC, EN_ENTRIES, "personal-report")

check("persian report is rtl", fa_values["dir"] == "rtl", fa_values["dir"])
check("persian report is lang fa", fa_values["lang"] == "fa", fa_values["lang"])
check("english report is ltr", en_values["dir"] == "ltr", en_values["dir"])
check("english report is lang en", en_values["lang"] == "en", en_values["lang"])
check("english report gets NO injected css", en_values["rtl_css"] == "",
      len(en_values["rtl_css"]))
check("persian report gets the typesetting block",
      len(fa_values["rtl_css"]) > 500, len(fa_values["rtl_css"]))

# An English report with one Persian quotation in it must stay English.
mixed = dict(EN_TOPIC)
mixed_entries = EN_ENTRIES + [dict(FA_ENTRIES[1], id="e9")]
mv, _ = render(mixed, mixed_entries, "personal-report")
check("one persian point does not flip an english report", mv["dir"] == "ltr", mv["dir"])


# ---------------------------------------------------------------------------
# 2. Dates, digits and chrome
# ---------------------------------------------------------------------------
print("\n-- dates and digits --")

check("persian date is jalali",
      persian.to_latin_digits(fa_values["date"]).split()[-1].startswith("14"),
      fa_values["date"])
check("persian date uses persian digits",
      not re.search(r"[0-9]", fa_values["date"]), fa_values["date"])
check("persian period is jalali",
      not re.search(r"[0-9]", fa_values["period"]), fa_values["period"])
check("date_iso stays gregorian ISO even in a persian report",
      re.match(r"^\d{4}-\d{2}-\d{2}$", fa_values["date_iso"]), fa_values["date_iso"])
check("date_gregorian is available alongside",
      "2026" in fa_values["date_gregorian"], fa_values["date_gregorian"])
check("persian counts use persian digits",
      not re.search(r"[0-9]", fa_values["count_points"]), fa_values["count_points"])
check("english counts stay latin", en_values["count_points"] == "2",
      en_values["count_points"])
check("english date is gregorian", "2026" in en_values["date"], en_values["date"])
print("   fa date: %s  period: %s  points: %s"
      % (fa_values["date"], fa_values["period"], fa_values["count_points"]))

check("persian labels are persian",
      fa_values["l_references"] == persian.LABELS["fa"]["references"],
      fa_values["l_references"])
check("english labels are english",
      en_values["l_references"] == "References", en_values["l_references"])
check("persian footer is persian",
      fa_values["footer"] != en_values["footer"], fa_values["footer"])


# ---------------------------------------------------------------------------
# 3. Nothing this app ships in Persian has a mechanical defect
# ---------------------------------------------------------------------------
print("\n-- shipped persian is clean --")

for name in ("footer", "l_references", "l_sources", "l_contents", "l_abstract",
             "l_figures", "l_points", "l_period", "l_author", "l_date"):
    v = fa_values[name]
    findings = persian.lint(v)
    check("lint clean: %s" % name, not findings,
          [f["code"] for f in findings] if findings else "")

# The user's OWN text must come through untouched - same digits, same
# half-spaces, same letters. Rewriting it would be the one unforgivable bug.
for e in FA_ENTRIES:
    check("point text survives verbatim", e["text"] in fa_values["body"]
          or e["text"].replace("&", "&amp;") in fa_values["body"],
          e["text"][:40])
zwnj_in = sum(e["text"].count(persian.ZWNJ) for e in FA_ENTRIES)
zwnj_out = fa_values["body"].count(persian.ZWNJ)
check("every half-space in the user's text survived the pipeline",
      zwnj_out >= zwnj_in, (zwnj_in, zwnj_out))
check("the url in a persian point is not digit-converted",
      "https://example.org/market-report" in
      (fa_values["references"] + fa_values["body"]), "")
check("an english citation inside a persian report keeps its latin year",
      "2010" in fa_values["references"], fa_values["references"][:120])


# ---------------------------------------------------------------------------
# 4. Every template renders both ways
# ---------------------------------------------------------------------------
print("\n-- all five templates --")

check("five html templates found", len(ALL) == 5, ALL)

for tid in ALL:
    fv, fa_html = render(FA_TOPIC, FA_ENTRIES, tid)
    ev, en_html = render(EN_TOPIC, EN_ENTRIES, tid)

    check("%s: persian html declares dir=rtl" % tid,
          'dir="rtl"' in fa_html, fa_html[:200])
    check("%s: persian html declares lang=fa" % tid,
          'lang="fa"' in fa_html, "")
    check("%s: english html declares dir=ltr" % tid,
          'dir="ltr"' in en_html and 'lang="en"' in en_html, "")
    check("%s: persian html carries the font stack" % tid,
          "Vazirmatn" in fa_html and "Tahoma" in fa_html, "")
    check("%s: english html carries NO persian css" % tid,
          "Vazirmatn" not in en_html and "--fa-sans" not in en_html, "")
    check("%s: no placeholder left unfilled" % tid,
          "{{" not in fa_html and "{{" not in en_html,
          re.findall(r"\{\{[a-z_]+\}\}", fa_html + en_html)[:4])
    check("%s: persian labels reached the page" % tid,
          persian.LABELS["fa"]["references"] in fa_html
          or persian.LABELS["fa"]["sources"] in fa_html
          or persian.LABELS["fa"]["abstract"] in fa_html, "")
    check("%s: english labels reached the page" % tid,
          "References" in en_html or "Sources" in en_html, "")


# ---------------------------------------------------------------------------
# 5. The CSS conversion: nothing physical left to fail silently
# ---------------------------------------------------------------------------
print("\n-- logical css --")

PHYSICAL = re.compile(r"(?:padding|margin|border)-(?:left|right)\s*:"
                      r"|text-align\s*:\s*(?:left|right)\b"
                      r"|position\s*:\s*absolute\s*;\s*(?:left|right)\s*:")

for tid in ALL:
    m = templates.load(tid)
    css = (pathlib.Path(m["dir"]) / "template.html").read_text(encoding="utf-8")
    found = PHYSICAL.findall(css)
    check("%s: no physical left/right property" % tid, not found, found[:4])
    check("%s: opens an rtl_css slot" % tid, "{{rtl_css}}" in css, "")
    check("%s: html tag is direction-aware" % tid,
          '<html lang="{{lang}}" dir="{{dir}}">' in css, "")

# The Persian block must scope every rule, or it would restyle English too.
css = persian.stylesheet("rtl")
rules = [ln for ln in css.splitlines()
         if ln.strip() and not ln.strip().startswith(("/*", "*", "--", "}"))
         and "{" in ln]
unscoped = [ln for ln in rules if 'html[dir="rtl"]' not in ln]
check("every injected rule is scoped to [dir=rtl]", not unscoped, unscoped[:3])
check("the block sets a persian font stack", "--fa-sans" in css)
check("the block neutralises synthetic italics", "font-style:normal" in css)
check("the block gives ordered lists persian numerals",
      "list-style-type:persian" in css)
check("but NOT the reference list, whose numbers pair with the body",
      "ol:not(.refs)" in css)
check("latin islands are isolated from the bidi run",
      "unicode-bidi:isolate" in css)


# ---------------------------------------------------------------------------
# 6. PLACEHOLDERS documents what a template author can actually use
# ---------------------------------------------------------------------------
print("\n-- placeholder contract --")

declared = set(templates.PLACEHOLDERS)
supplied = set(fa_values)
missing = sorted(declared - supplied)
check("every documented placeholder is supplied", not missing, missing)
undocumented = sorted(supplied - declared)
check("every supplied value is documented", not undocumented, undocumented)
for k in ("lang", "dir", "rtl_css", "l_references", "date_gregorian"):
    check("PLACEHOLDERS documents %r" % k, k in declared)


# ---------------------------------------------------------------------------
# 7. The .docx, which Word will not read a dir attribute out of
# ---------------------------------------------------------------------------
print()
print("-- docx --")

import tempfile          # noqa: E402
import xml.etree.ElementTree as ET  # noqa: E402
import zipfile           # noqa: E402

import docx_writer       # noqa: E402

DOC_FA = {
    "title": FA_TOPIC["title"], "kicker": "", "subtitle": "", "summary": "",
    "meta_line": fa_values["date"],
    "markdown": "## " + persian.LABELS["fa"]["abstract"] + chr(10) * 2
                + FA_ENTRIES[0]["text"] + chr(10) * 2 + "- " + FA_ENTRIES[1]["text"],
    "references": ["Armbrust et al., A View of Cloud Computing (2010)"],
    "figures": [], "accent": "#0f766e", "footer": fa_values["footer"],
    "dir": "rtl", "l_figures": fa_values["l_figures"],
    "l_references": fa_values["l_references"],
}
DOC_EN = dict(DOC_FA, title="Cloud services market",
              markdown="## Findings" + chr(10) * 2 + "Share doubled." + chr(10) * 2 + "- one",
              meta_line=en_values["date"], footer=en_values["footer"],
              dir="ltr", l_figures="Figures", l_references="References")

tmp = pathlib.Path(tempfile.mkdtemp(prefix="opl_docx_"))
parts = {}
for name, d in (("fa", DOC_FA), ("en", DOC_EN)):
    p = tmp / ("report_%s.docx" % name)
    docx_writer.write_docx(p, d)
    z = zipfile.ZipFile(p)
    parts[name] = {"body": z.read("word/document.xml").decode("utf-8"),
                   "styles": z.read("word/styles.xml").decode("utf-8"),
                   "size": p.stat().st_size, "names": z.namelist()}

fa_body, en_body = parts["fa"]["body"], parts["en"]["body"]

# Both files must still be well-formed OOXML - a stray attribute here is a
# file Word refuses to open at all, which is worse than one that opens wrong.
for name in ("fa", "en"):
    ok = True
    try:
        ET.fromstring(parts[name]["body"])
        ET.fromstring(parts[name]["styles"])
    except Exception as e:
        ok = False
        err = e
    check("%s docx: document.xml and styles.xml are well-formed" % name, ok,
          "" if ok else err)
    check("%s docx: has the six required parts" % name,
          len(parts[name]["names"]) == 6, parts[name]["names"])

# All three places Word looks. Getting two of the three is a document that
# looks almost right.
n_paras = fa_body.count("<w:p>") + fa_body.count("<w:p ")
check("persian docx: every paragraph is bidi",
      fa_body.count("<w:bidi/>") >= n_paras, (fa_body.count("<w:bidi/>"), n_paras))
check("persian docx: runs are marked rtl", fa_body.count("<w:rtl/>") > 0,
      fa_body.count("<w:rtl/>"))
check("persian docx: the section is bidi",
      "<w:bidi/></w:sectPr>" in fa_body, "")
check("persian docx: the complex-script font is set",
      'w:cs="%s"' % docx_writer.CS_FONT in parts["fa"]["styles"], "")
check("persian docx: no synthetic italics", fa_body.count("<w:i/>") == 0,
      fa_body.count("<w:i/>"))
check("persian docx: persian labels used",
      persian.LABELS["fa"]["references"] in fa_body, "")
check("persian docx: the point text is verbatim",
      FA_ENTRIES[0]["text"] in fa_body, "")

# And the English file is untouched by any of it.
check("english docx: no bidi anywhere", "<w:bidi/>" not in en_body, "")
check("english docx: no rtl runs", "<w:rtl/>" not in en_body, "")
check("english docx: no complex-script font",
      'w:cs="%s"' % docx_writer.CS_FONT not in parts["en"]["styles"], "")
check("english docx: english labels used", "References" in en_body, "")
print("   fa %d bytes, %d bidi, %d rtl runs   en %d bytes"
      % (parts["fa"]["size"], fa_body.count("<w:bidi/>"),
         fa_body.count("<w:rtl/>"), parts["en"]["size"]))

# The legacy constant must still be the left-to-right section, because
# something outside this repo may import it.
check("SECT_PR is still the ltr section",
      docx_writer.SECT_PR == docx_writer.sect_pr(False)
      and "<w:bidi/>" not in docx_writer.SECT_PR, docx_writer.SECT_PR[-60:])


# ---------------------------------------------------------------------------
# 8. The starter template - template CREATION, not just template editing
# ---------------------------------------------------------------------------
# A user writing their first template copies this one. If it is wrong about
# direction, every template descended from it is wrong about direction, and
# the defect is invisible until someone writes a Persian report.
print("%s-- starter template --" % chr(10))

import tempfile         # noqa: E402

with tempfile.TemporaryDirectory() as tmp:
    root = pathlib.Path(tmp)
    written = templates.write_starter(root)
    check("write_starter writes three files", len(written) == 3,
          ", ".join(pathlib.Path(w).name for w in written))
    check("a second call overwrites nothing",
          templates.write_starter(root) == [], "user edits survive")

    folder = root / "starter"
    manifest = templates._read_manifest(folder)
    check("the starter manifest parses", bool(manifest and manifest.get("id")),
          (manifest or {}).get("id", ""))

    shell = (folder / "template.html").read_text(encoding="utf-8")

    # The three bidi requirements, checked as strings rather than trusted.
    check("starter: html carries lang and dir",
          'lang="{{lang}}" dir="{{dir}}"' in shell, "")
    check("starter: rtl_css is inside style, and last",
          shell.index("{{rtl_css}}") < shell.index("</style>")
          and shell[shell.index("{{rtl_css}}") + 11:shell.index("</style>")].strip() == "",
          "")
    phys = re.findall(r"(?<![-\w])(?:padding|margin|border)-(?:left|right)\s*:"
                      r"|text-align\s*:\s*(?:left|right)", shell)
    check("starter: no physical left/right CSS", not phys, ", ".join(phys))

    # It renders, both ways, through the real pipeline.
    for lang_id, topic, entries in (("fa", FA_TOPIC, FA_ENTRIES),
                                    ("en", EN_TOPIC, EN_ENTRIES)):
        refs, cites = _collect(entries)
        md = pipeline.compose_markdown(topic, entries, cites, refs=refs)
        values = pipeline.build_values(topic, entries, refs, md, manifest, meta={})
        html = templates.render_shell(manifest, values)
        want_dir = "rtl" if lang_id == "fa" else "ltr"
        check("starter renders %s as %s" % (lang_id, want_dir),
              ('dir="%s"' % want_dir) in html, "")
        check("starter %s: no unfilled placeholder" % lang_id,
              "{{" not in html, html[html.find("{{"):][:40] if "{{" in html else "")
        check("starter %s: labels are localised" % lang_id,
              persian.LABELS[lang_id]["references"] in html
              or not values.get("references"), "")
        if lang_id == "en":
            check("starter en: injects no rtl css",
                  "direction:rtl" not in html and persian.FONT_SANS_FA not in html, "")

    readme = (root / "README.md").read_text(encoding="utf-8")
    missing = [k for k in templates.PLACEHOLDERS if ("{{%s}}" % k) not in readme]
    check("README documents every placeholder", not missing, ", ".join(missing))
    check("README explains the direction rules",
          "logical" in readme and "{{rtl_css}}" in readme, "")


print()
print("ALL CHECKS PASSED" if not FAILS else "FAILED: " + ", ".join(FAILS))
sys.exit(1 if FAILS else 0)
