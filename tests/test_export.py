"""Headless test of the export pipeline: templates, Markdown, DOCX, PDF.

Run:  $env:PYTHONPATH="."; python tests\test_export.py
It writes into a temp folder and prints a pass/fail line per check. Nothing here
touches your real %APPDATA% data.
"""

import json
import shutil
import sys
import tempfile
import unittest.mock
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import mdlite            # noqa: E402
import pipeline          # noqa: E402
import templates_registry as templates   # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + name + ((" - " + str(detail)) if detail else ""))
    if not cond:
        FAILS.append(name)


TOPIC = {
    "id": "t1",
    "title": "Borrow checker ergonomics",
    "status": "closed",
    "created": "2026-08-02T09:15:00",
    "closed": "2026-09-01T17:40:00",
    "subtopics": ["Aliasing", "NLL"],
}

ENTRIES = [
    {"id": "e1", "subtopic": "Aliasing", "created": "2026-08-02T09:20:00",
     "text": "Two **mutable** borrows of the same place are rejected before monomorphisation.",
     "sources": [{"id": "s1", "type": "link", "value": "https://doc.rust-lang.org/nomicon/",
                  "note": "Rustonomicon"}]},
    {"id": "e2", "subtopic": "Aliasing", "created": "2026-08-04T11:02:00",
     "text": "Reborrowing through `&mut *x` is what makes method chains work at all.",
     "sources": [{"id": "s2", "type": "string", "value": "Jung et al., Stacked Borrows, POPL 2020"}]},
    {"id": "e3", "subtopic": "NLL", "created": "2026-08-11T14:33:00",
     "text": "Non-lexical lifetimes ended the *drop-at-scope-end* rejection class.",
     "sources": [{"id": "s3", "type": "link", "value": "https://rust-lang.github.io/rfcs/2094-nll.html"},
                 {"id": "s1", "type": "link", "value": "https://doc.rust-lang.org/nomicon/",
                  "note": "Rustonomicon"}]},
    {"id": "e4", "subtopic": "NLL", "created": "2026-08-19T08:05:00",
     "text": "Polonius is still not on by default; check before citing it as shipped.",
     "sources": []},
]


def collect_refs(entries):
    refs, cites = [], {}
    for e in entries:
        nums = []
        for s in e.get("sources", []):
            key = (s.get("type"), s.get("value"))
            if key not in cites:
                cites[key] = len(refs) + 1
                refs.append(s)
            nums.append(cites[key])
        cites[e["id"]] = nums
    return refs, cites


def main():
    tmp = Path(tempfile.mkdtemp(prefix="trailmark-test-"))
    try:
        print("\n== templates ==")
        found = templates.available()
        ids = [t["id"] for t in found]
        print("  discovered:", ", ".join(ids) or "(none)")
        check("at least the three shipped templates exist",
              {"research-roam", "personal-report", "protocol"} <= set(ids), ids)

        print("\n== markdown ==")
        html = mdlite.render("## H\n\nA **bold** and `code` and [link](https://x.test) [1].\n\n"
                             "- one\n- two\n  - nested\n\n| a | b |\n| --- | --- |\n| 1 | 2 |\n")
        check("no literal ** survives", "**" not in html)
        check("no literal backtick survives", "`" not in html)
        check("bold became <strong>", "<strong>bold</strong>" in html)
        check("citation became an anchor", '<a class="cite" href="#r1">[1]</a>' in html)
        check("table rendered", "<table" in html and "<th>a</th>" in html)
        check("nested list is inside its li", "two<ul>" in html)
        check("html injection is escaped",
              "&lt;script&gt;" in mdlite.render("<script>alert(1)</script>"))

        refs, cites = collect_refs(ENTRIES)
        check("refs deduplicated", len(refs) == 3, "%d refs" % len(refs))

        print("\n== compose + ground ==")
        md = pipeline.compose_markdown(TOPIC, ENTRIES, cites)
        check("every sub-topic became a heading", "## Aliasing" in md and "## NLL" in md)
        ok, findings = pipeline.ground_citations(md, md, len(refs))
        check("identical text grounds clean", ok and not findings, findings)
        ok2, f2 = pipeline.ground_citations(md, md + "\nInvented [9].", len(refs))
        check("invented citation is caught", not ok2 and f2, f2)
        _, f3 = pipeline.ground_citations(md, "no citations here", len(refs))
        check("dropped citations are reported", any("missing" in x for x in f3), f3)

        print("\n== full export, every template x every format ==")
        for tid in ids:
            res = pipeline.export(
                TOPIC, ENTRIES, refs, cites, tmp / tid, template_id=tid,
                formats=("html", "markdown", "docx", "pdf"),
                meta={"author": "A. Researcher", "org": "Trailmark",
                      "summary": "A **short** abstract with a citation [1]."})
            got = sorted(res.get("files", {}))
            print("\n  --- %s -> %s" % (tid, ", ".join(got) or "NOTHING"))
            for w in res.get("warnings", []):
                print("      warn:", w)
            for e in res.get("errors", []):
                print("      err :", e)
            check("%s: html produced" % tid, "html" in got)
            check("%s: markdown produced" % tid, "markdown" in got)
            check("%s: docx produced" % tid, "docx" in got)
            check("%s: pdf produced" % tid, "pdf" in got, res.get("errors"))
            if "pdf" in got:
                print("      pdf: %s, %s page(s), %d KB"
                      % (res.get("pdf_engine"), res.get("pdf_pages"),
                         Path(res["files"]["pdf"]).stat().st_size // 1024))
                check("%s: pdf has >=1 page" % tid, (res.get("pdf_pages") or 0) >= 1)
            if "html" in got:
                out = Path(res["files"]["html"]).read_text(encoding="utf-8")
                check("%s: no unfilled placeholder" % tid, "{{" not in out,
                      [l for l in out.splitlines() if "{{" in l][:2])
                check("%s: markdown did not leak into html" % tid,
                      "**mutable**" not in out)
            if "docx" in got:
                with zipfile.ZipFile(res["files"]["docx"]) as z:
                    names = z.namelist()
                    doc = z.read("word/document.xml").decode("utf-8")
                check("%s: docx has the required parts" % tid,
                      {"[Content_Types].xml", "word/document.xml", "word/styles.xml",
                       "word/numbering.xml", "word/_rels/document.xml.rels"} <= set(names))
                check("%s: docx bold became a run property" % tid, "<w:b/>" in doc)
                check("%s: markdown did not leak into docx" % tid, "**mutable**" not in doc)
            mf = Path(res["folder"]) / "manifest.json"
            check("%s: manifest written with topic_id" % tid,
                  mf.exists() and '"topic_id": "t1"' in mf.read_text(encoding="utf-8"))

        print("\n== polished path falls back safely ==")
        res = pipeline.export(TOPIC, ENTRIES, refs, cites, tmp / "polished",
                              template_id="personal-report", formats=("markdown",),
                              polished_markdown="## Rewritten\n\nClaim with a bogus source [42].")
        check("bad polish falls back to raw points",
              any("Fell back" in w for w in res.get("warnings", [])), res.get("warnings"))
        body = Path(res["files"]["markdown"]).read_text(encoding="utf-8")
        check("fallback kept the real content", "Polonius" in body)

        print("\n== pdf-only export doesn't leak report.html ==")
        res = pipeline.export(TOPIC, ENTRIES, refs, cites, tmp / "pdf-only",
                              template_id="personal-report", formats=("pdf",),
                              meta={"author": "A. Researcher", "org": "Trailmark",
                                    "summary": "A **short** abstract with a citation [1]."})
        check("pdf-only: pdf produced", "pdf" in res.get("files", {}), res.get("errors"))
        out_dir = Path(res["folder"])
        leaked = [p.name for p in out_dir.glob("*.html")]
        check("pdf-only: no report.html left behind", not leaked, leaked)
        mf = out_dir / "manifest.json"
        mf_files = (json.loads(mf.read_text(encoding="utf-8")).get("files", {})
                    if mf.exists() else {})
        check("pdf-only: manifest files lists only pdf",
              mf_files == {"pdf": "report.pdf"}, mf_files)

        print("\n== pdf-only export with pdf rendering failure preserves report.html ==")
        with unittest.mock.patch("pdf_render.render_tex_to_pdf", side_effect=RuntimeError("LaTeX unavailable")), \
             unittest.mock.patch("pdf_render.render_html_to_pdf", side_effect=RuntimeError("PDF engine unavailable")):
            res = pipeline.export(TOPIC, ENTRIES, refs, cites, tmp / "pdf-fail",
                                  template_id="personal-report", formats=("pdf",),
                                  meta={"author": "A. Researcher", "org": "Trailmark",
                                        "summary": "A **short** abstract with a citation [1]."})
        check("pdf-fail: pdf NOT in result files (failed)", "pdf" not in res.get("files", {}))
        check("pdf-fail: error logged", any("PDF:" in e for e in res.get("errors", [])), res.get("errors"))
        out_dir = Path(res["folder"])
        html_files = [p.name for p in out_dir.glob("*.html")]
        check("pdf-fail: report.html preserved when pdf fails", "report.html" in html_files, html_files)

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("\n" + ("ALL CHECKS PASSED" if not FAILS
                  else "%d FAILED: %s" % (len(FAILS), ", ".join(FAILS))))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
