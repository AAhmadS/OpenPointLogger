"""Headless test of scientific mode: citation styles, and the two gates.

Run:  $env:PYTHONPATH="."; python tests\test_science.py

The point of scientific mode is a distinction the rest of the app does not make:
a sourced claim, a verbatim quotation, and your own note are three different
things, and an AI rewording pass must not be able to turn one into another. So
most of what is checked here is what the gate REJECTS.
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import citation         # noqa: E402
import pipeline         # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + name + ((" - " + str(detail)) if detail else ""))
    if not cond:
        FAILS.append(name)


SMITH = {"authors": "Smith, Jane Q.", "year": "2020",
         "title": "Ownership without tears", "container": "Journal of Systems",
         "volume": "12", "issue": "3", "pages": "44-61", "doi": "10.1000/abc"}
ANON = {"title": "A page with no author", "url": "https://example.org/x"}

TOPIC = {"id": "t1", "title": "Borrowing", "created": "2026-08-02T09:15:00",
         "closed": None, "subtopics": ["Aliasing"]}

ENTRIES = [
    {"id": "e1", "subtopic": "Aliasing", "kind": "claim",
     "created": "2026-08-02T09:20:00",
     "text": "Two mutable borrows of the same place are rejected.",
     "sources": [{"id": "s1", "type": "link", "value": "https://doi.org/10.1000/abc",
                  "note": "", "meta": citation.normalise_meta(SMITH)}]},
    {"id": "e2", "subtopic": "Aliasing", "kind": "quote",
     "created": "2026-08-03T09:20:00",
     "text": "The borrow checker is not a proof assistant.",
     "sources": [{"id": "s2", "type": "string", "value": "p. 51",
                  "note": "", "meta": citation.normalise_meta(SMITH)}]},
    {"id": "e3", "subtopic": "Aliasing", "kind": "note",
     "created": "2026-08-04T09:20:00",
     "text": "My own hunch is that this is really about aliasing, not mutation.",
     "sources": []},
]
REFS = [ENTRIES[0]["sources"][0], ENTRIES[1]["sources"][0]]
CITES = {"e1": [1], "e2": [2], "e3": []}
SCI = {"enabled": True, "style": "apa", "separate_notes": True}


# --- reference formatting ----------------------------------------------------

print("citation styles")
apa = citation.format_reference(SMITH, "apa")
check("APA has author, year, journal", "Smith, J. Q." in apa and "(2020)" in apa
      and "Journal of Systems" in apa, apa)
ieee = citation.format_reference(SMITH, "ieee")
check("IEEE initials lead the name", ieee.startswith("J. Q. Smith"), ieee)
van = citation.format_reference(SMITH, "vancouver")
check("Vancouver has no dot initials", "Smith JQ" in van, van)

# The rule the whole module exists for.
thin = citation.format_reference(ANON, "apa")
check("a source with no author invents none",
      "n.d." not in thin and "Anonymous" not in thin and "A page with no author" in thin, thin)
check("no metadata at all falls back to the typed string",
      citation.format_reference({}, "apa", fallback="whatever I typed") == "whatever I typed")

check("APA marker is author-date", citation.inline_marker(1, SMITH, "apa") == "(Smith, 2020)")
check("marker falls back to the number when undescribed",
      citation.inline_marker(3, ANON, "apa") == "[3]")


# --- composition -------------------------------------------------------------

print("composition")
md = pipeline.compose_markdown(TOPIC, ENTRIES, CITES, refs=REFS, science=SCI)
check("claim carries the author-date marker", "(Smith, 2020)" in md, md[:80])
check("quote is a blockquote", "> The borrow checker is not a proof assistant." in md)
check("notes get their own heading", ("### " + pipeline.NOTES_HEADING) in md)
note_block = md.split(pipeline.NOTES_HEADING, 1)[1]
check("nothing in the notes block is cited",
      "[" not in note_block and "(Smith" not in note_block, note_block.strip()[:90])

plain = pipeline.compose_markdown(TOPIC, ENTRIES, CITES, refs=REFS,
                                  science={"enabled": False})
check("mode off keeps the old numeric shape", "[1]" in plain
      and pipeline.NOTES_HEADING not in plain and "> The borrow" not in plain)

pairs = pipeline.ordered_refs(REFS, "apa")
check("numbers survive alphabetical sorting", sorted(n for n, _ in pairs) == [1, 2])


# --- the gates ---------------------------------------------------------------

print("gates")
ok, f = pipeline.ground_science(md, ENTRIES, SCI)
check("an unchanged draft passes", ok, f)

bad = md.replace("My own hunch", "My own hunch (Smith, 2020)")
ok, f = pipeline.ground_science(bad, ENTRIES, SCI)
check("a citation attached to a note is rejected", not ok, f)

bad = md.replace("### " + pipeline.NOTES_HEADING, "### Discussion")
ok, f = pipeline.ground_science(bad, ENTRIES, SCI)
check("removing the notes heading is rejected", not ok, f)

bad = md.replace("The borrow checker is not a proof assistant.",
                 "The borrow checker isn't a proof assistant.")
ok, f = pipeline.ground_science(bad, ENTRIES, SCI)
check("a reworded quotation is rejected", not ok, f)

bad = "\n".join(l for l in md.split("\n") if "My own hunch" not in l)
ok, f = pipeline.ground_science(bad, ENTRIES, SCI)
check("a deleted note is rejected", not ok, f)

reworded = md.replace("Two mutable borrows of the same place are rejected.",
                      "Two mutable borrows of one place are rejected outright.")
ok, f = pipeline.ground_science(reworded, ENTRIES, SCI)
check("rewording an ordinary claim is allowed", ok, f)

# the author-date path through the citation gate: there is no [n] to count
markers = ["(Smith, 2020)"]
ok, f = pipeline.ground_citations(md, md.replace("(Smith, 2020)", "as Smith notes"),
                                  len(REFS), markers)
check("a dropped author-date marker is caught", not ok or f, f)


# --- end to end --------------------------------------------------------------

print("export")
out = Path(tempfile.mkdtemp(prefix="tm_sci_"))
res = pipeline.export(TOPIC, ENTRIES, REFS, CITES, out,
                      template_id="personal-report",
                      formats=("html", "markdown"), science=SCI)
check("export produced files", bool(res.get("files")), res.get("errors"))
html = Path(res["files"]["html"]).read_text(encoding="utf-8") if res.get("files", {}).get("html") else ""
check("HTML reference list is formatted, not raw", "Journal of Systems" in html)
check("HTML keeps the anchor numbering", 'id="r1"' in html)
check("manifest records the style", res.get("citation_style") == "apa")

# a polished draft that breaks the rules must fall back to the user's own text
res2 = pipeline.export(TOPIC, ENTRIES, REFS, CITES, out,
                       template_id="personal-report", formats=("markdown",),
                       polished_markdown=md.replace(
                           "The borrow checker is not a proof assistant.",
                           "The borrow checker isn't one."),
                       science=SCI)
check("a reworded quote sends the export back to your own text",
      any("quotation was reworded" in w for w in res2.get("warnings", [])),
      res2.get("warnings"))

print()
print("FAILED: " + ", ".join(FAILS) if FAILS else "all scientific-mode checks passed")
sys.exit(1 if FAILS else 0)
