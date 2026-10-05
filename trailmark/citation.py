"""citation - structured source metadata, and reference strings in real styles.

Trailmark used to treat a source as a string: a URL, or whatever you typed. That
is enough to number sources [1][2] and no more. Scientific mode needs the parts
separately - who, when, what, where - because every citation style arranges the
same parts differently, and no amount of string munging recovers a structure
that was never captured.

So a source may now carry a `meta` dict. Every field is optional and an absent
field is never invented: a reference with only a title and a URL renders as a
title and a URL, not as a plausible-looking full citation. That rule is the
whole design. A missing author is a fact about your source, and the report
should show it as one.

What this is not: a CSL processor. Real CSL is a 2000-style XML-driven
specification, and shipping citeproc-py plus a styles repository would cost more
than the rest of the app put together. These five styles are hand-written
approximations of their most common forms - good enough for a working document,
and honest about it. If you need submission-grade output, export the Markdown
and run it through Pandoc with a real .csl file.

Reference: https://www.crossref.org/documentation/retrieve-metadata/content-negotiation/
gives CSL-JSON for a DOI, which maps onto `meta` almost field for field - the
field names here are deliberately CSL-JSON's, so that path stays open.
"""

import re
import urllib.parse

__all__ = ["STYLES", "normalise_meta", "format_reference", "inline_marker",
           "sort_key", "meta_from_csl", "is_empty"]

#: id -> (label, one-line description). The id is what lands in config.
STYLES = {
    "numeric": ("Numbered", "[1] in the text, sources numbered in order of first use."),
    "apa": ("APA 7", "(Smith, 2020) in the text, reference list alphabetical."),
    "ieee": ("IEEE", "[1] in the text, reference list in citation order."),
    "chicago": ("Chicago author-date", "(Smith 2020) in the text, list alphabetical."),
    "vancouver": ("Vancouver", "(1) in the text, numbered in order of first use."),
}

#: styles whose reference list is sorted by author rather than by first use
ALPHABETICAL = ("apa", "chicago")

META_FIELDS = ("type", "authors", "year", "title", "container", "publisher",
               "edition", "volume", "issue", "pages", "doi", "url", "accessed",
               "isbn", "issn", "note")


#: fields that describe the source rather than *being* it. A record holding only
#: these is still empty: normalise_meta guesses a type for everything it touches,
#: and a guessed type must not make an empty record look filled in.
_DERIVED = ("type",)


def is_empty(meta):
    """True when there is nothing here worth formatting."""
    if not meta:
        return True
    return not any(str(meta.get(f) or "").strip() if f != "authors"
                   else bool(meta.get(f))
                   for f in META_FIELDS if f not in _DERIVED)


def normalise_meta(meta):
    """Coerce whatever the UI or an importer produced into the stored shape.

    Unknown keys are dropped rather than kept, so a template can rely on the
    field list. Authors accept either a list or a single semicolon/'and'
    separated string, because both are what people actually paste.
    """
    meta = dict(meta or {})
    out = {}
    for f in META_FIELDS:
        v = meta.get(f)
        if f == "authors":
            out[f] = _authors(v)
        elif v is None:
            out[f] = ""
        else:
            out[f] = str(v).strip()
    if out["year"]:
        m = re.search(r"\d{4}", out["year"])
        out["year"] = m.group(0) if m else out["year"]
    if out["doi"]:
        out["doi"] = re.sub(r"^\s*(?:https?://(?:dx\.)?doi\.org/|doi:)\s*", "",
                            out["doi"], flags=re.I).strip()
    if not out["type"]:
        out["type"] = _guess_type(out)
    return out


def _authors(v):
    if not v:
        return []
    if isinstance(v, str):
        parts = re.split(r"\s*;\s*|\s+and\s+|\s*&\s*", v)
    else:
        parts = list(v)
    names = []
    for p in parts:
        if isinstance(p, dict):
            fam = str(p.get("family") or "").strip()
            giv = str(p.get("given") or "").strip()
            if fam or giv:
                names.append({"family": fam, "given": giv})
            continue
        p = str(p or "").strip().strip(",")
        if not p:
            continue
        names.append(_split_name(p))
    return names


def _split_name(s):
    """Split a written name into family/given without being clever about it.

    "Smith, Jane Q." and "Jane Q. Smith" both work. Anything else is kept whole
    as the family name, which formats as-is - better than mangling an
    organisation or a name whose shape this code does not know.
    """
    if "," in s:
        fam, _, giv = s.partition(",")
        return {"family": fam.strip(), "given": giv.strip()}
    bits = s.split()
    if len(bits) >= 2:
        return {"family": bits[-1], "given": " ".join(bits[:-1])}
    return {"family": s, "given": ""}


def _guess_type(meta):
    if meta.get("doi") or meta.get("container"):
        return "article"
    if meta.get("isbn") or meta.get("publisher"):
        return "book"
    if meta.get("url"):
        return "web"
    return "misc"


def meta_from_csl(doc):
    """Map a CSL-JSON document (what doi.org content negotiation returns).

    Kept deliberately small: the fields Trailmark renders, and nothing else.
    Anything absent stays absent.
    """
    doc = doc or {}
    issued = (doc.get("issued") or {}).get("date-parts") or [[]]
    year = ""
    try:
        year = str(issued[0][0]) if issued and issued[0] else ""
    except Exception:
        year = ""
    page = doc.get("page") or ""
    container = doc.get("container-title") or ""
    if isinstance(container, list):
        container = container[0] if container else ""
    return normalise_meta({
        "type": {"journal-article": "article", "book": "book",
                 "chapter": "chapter", "posted-content": "preprint",
                 "webpage": "web"}.get(doc.get("type", ""), doc.get("type", "")),
        "authors": [{"family": a.get("family", ""), "given": a.get("given", "")}
                    for a in (doc.get("author") or [])],
        "year": year,
        "title": doc.get("title") if isinstance(doc.get("title"), str)
                 else (doc.get("title") or [""])[0],
        "container": container,
        "publisher": doc.get("publisher") or "",
        "volume": doc.get("volume") or "",
        "issue": doc.get("issue") or "",
        "pages": page,
        "doi": doc.get("DOI") or "",
        "url": doc.get("URL") or "",
        "issn": (doc.get("ISSN") or [""])[0] if isinstance(doc.get("ISSN"), list)
                else (doc.get("ISSN") or ""),
    })


# --- name rendering ----------------------------------------------------------

def _initials(given):
    return " ".join("%s." % w[0].upper() for w in re.split(r"[\s.\-]+", given) if w)


def _name_apa(a):
    fam, giv = a.get("family", ""), a.get("given", "")
    return "%s, %s" % (fam, _initials(giv)) if fam and giv else (fam or giv)


def _name_ieee(a):
    fam, giv = a.get("family", ""), a.get("given", "")
    return "%s %s" % (_initials(giv), fam) if fam and giv else (fam or giv)


def _name_vancouver(a):
    fam, giv = a.get("family", ""), a.get("given", "")
    ini = "".join(w[0].upper() for w in re.split(r"[\s.\-]+", giv) if w)
    return ("%s %s" % (fam, ini)).strip()


def _join(names, sep=", ", last=" and ", amp=False):
    names = [n for n in names if n]
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    tail = " & " if amp else last
    return sep.join(names[:-1]) + tail + names[-1]


def _authors_str(meta, style):
    people = meta.get("authors") or []
    if not people:
        return ""
    if style == "apa":
        shown = [_name_apa(a) for a in people[:20]]
        return _join(shown, ", ", ", & " if len(shown) > 2 else " & ", amp=len(shown) == 2)
    if style == "chicago":
        first = people[0]
        head = "%s, %s" % (first.get("family", ""), first.get("given", ""))
        rest = ["%s %s" % (a.get("given", ""), a.get("family", "")).strip()
                for a in people[1:]]
        return _join([head.strip().strip(",")] + rest, ", ", ", and ")
    if style == "vancouver":
        shown = [_name_vancouver(a) for a in people[:6]]
        return ", ".join(shown) + (", et al" if len(people) > 6 else "")
    # ieee + numeric
    shown = [_name_ieee(a) for a in people[:6]]
    return _join(shown, ", ", ", and ") + (", et al." if len(people) > 6 else "")


# --- reference rendering -----------------------------------------------------

def _bits(*parts):
    """Join the parts that exist, with a full stop, without inventing any."""
    out = [str(p).strip().rstrip(".") for p in parts if p and str(p).strip()]
    return ". ".join(out) + "." if out else ""


def format_reference(meta, style="numeric", fallback=""):
    """One reference-list entry as plain text.

    `fallback` is used when there is no structured metadata at all - that is
    the ordinary case for a pasted link or a typed citation string, and it is
    returned unchanged rather than dressed up as something it is not.
    """
    meta = normalise_meta(meta)
    if is_empty(meta):
        return fallback or ""
    a = _authors_str(meta, style)
    t = meta.get("title") or fallback or ""
    y, c = meta.get("year"), meta.get("container")
    pub, vol, iss, pg = (meta.get("publisher"), meta.get("volume"),
                         meta.get("issue"), meta.get("pages"))
    loc = meta.get("doi") and "https://doi.org/%s" % meta["doi"] or meta.get("url") or ""

    if style == "apa":
        where = c
        if c and vol:
            where = "%s, %s" % (c, vol) + ("(%s)" % iss if iss else "")
            if pg:
                where += ", %s" % pg
        head = _bits(a, "(%s)" % y if y else "", t, where, pub if not c else "")
        return (head + (" " + loc if loc else "")).strip()

    if style == "ieee":
        # the title carries its own comma inside the quotes, so it is joined to
        # what follows with a space rather than another comma
        tail = ", ".join(x for x in [
            "*%s*" % c if c else "",
            "vol. %s" % vol if vol else "",
            "no. %s" % iss if iss else "",
            "pp. %s" % pg if pg else "",
            y or "",
        ] if x)
        title = '"%s,"' % t.rstrip(".") if t else ""
        head = ", ".join(x for x in [a, title] if x)
        base = " ".join(x for x in [head, tail] if x) if title else \
            ", ".join(x for x in [head, tail] if x)
        return (base.rstrip(",").rstrip(".") + "." + (" " + loc if loc else "")).strip()

    if style == "chicago":
        head = _bits(a, y, '"%s"' % t.rstrip(".") if t else "",
                     "*%s*" % c if c else "", pub, pg)
        return (head + (" " + loc if loc else "")).strip()

    if style == "vancouver":
        head = _bits(a, t, c, y)
        extra = ""
        if vol:
            extra = ";%s" % vol + ("(%s)" % iss if iss else "") + (":%s" % pg if pg else "")
        return (head.rstrip(".") + extra + "." + (" " + loc if loc else "")).strip()

    # numeric: a readable neutral form
    head = _bits(a, "(%s)" % y if y else "", t, c, pub, pg)
    return (head + (" " + loc if loc else "")).strip()


def inline_marker(n, meta, style="numeric"):
    """The in-text citation for reference number `n`.

    Author-date styles fall back to the number when there is no author or no
    year to print - a marker that says "(n.d.)" about a source that simply was
    not described is noise, and [3] at least points somewhere real.
    """
    meta = normalise_meta(meta)
    people = meta.get("authors") or []
    year = meta.get("year")
    if style in ("apa", "chicago") and people and year:
        fam = people[0].get("family") or people[0].get("given")
        if len(people) == 1:
            who = fam
        elif len(people) == 2:
            second = people[1].get("family") or people[1].get("given")
            who = "%s %s %s" % (fam, "&" if style == "apa" else "and", second)
        else:
            who = "%s et al." % fam
        return "(%s, %s)" % (who, year) if style == "apa" else "(%s %s)" % (who, year)
    if style == "vancouver":
        return "(%d)" % n
    return "[%d]" % n


def sort_key(meta, fallback=""):
    """Alphabetical ordering for the styles that want it."""
    meta = normalise_meta(meta)
    people = meta.get("authors") or []
    if people:
        return (0, (people[0].get("family") or people[0].get("given") or "").lower(),
                meta.get("year") or "")
    title = (meta.get("title") or fallback or "").lower()
    return (1, title, meta.get("year") or "")


def lookup_doi(doi, timeout=12):
    """Fetch CSL-JSON for a DOI from doi.org content negotiation.

    Online-only and deliberately unclever: no cache, no retry, no third-party
    client. If there is no network, or the DOI is wrong, you get an error string
    and the fields you typed by hand are left exactly as they were - the one
    thing this must never do is overwrite real metadata with a guess.

    https://www.crossref.org/documentation/retrieve-metadata/content-negotiation/
    """
    import json
    import urllib.error
    import urllib.request

    doi = re.sub(r"^\s*(?:https?://(?:dx\.)?doi\.org/|doi:)\s*", "", str(doi or ""),
                 flags=re.I).strip()
    if not doi or "/" not in doi:
        return {"error": "That does not look like a DOI (they look like 10.1000/abc123)."}
    req = urllib.request.Request(
        "https://doi.org/" + urllib.parse.quote(doi, safe="/:"),
        headers={"Accept": "application/vnd.citationstyles.csl+json",
                 "User-Agent": "Trailmark (local research logger)"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            doc = json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"error": "No record for that DOI."}
        return {"error": "The DOI service answered %s." % e.code}
    except Exception as e:
        return {"error": "Could not reach doi.org (%s)." % e.__class__.__name__}
    meta = meta_from_csl(doc)
    if is_empty(meta):
        return {"error": "The record came back empty."}
    return {"meta": meta}
