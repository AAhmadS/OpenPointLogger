"""Persian document mechanics: direction, digits, calendar, orthography.

Nothing in here writes Persian *prose*. Everything is mechanical - things a
non-native reader can verify by counting code points - and that boundary is
deliberate. Generated Persian that reads as translated is the failure this
module is built to avoid contributing to, so it only handles the parts that
have one correct answer: which direction the page runs, which digits a date
uses, which calendar that date is in, and whether a half-space is missing.

The two mechanical defects that break Persian silently:

**ZWNJ (U+200C, نیم‌فاصله).** ``می شود`` and ``می‌شود`` are different words and
the difference is invisible in most terminals and editors. Every fixed Persian
string in this module carries its half-spaces, and ``tests/test_persian.py``
counts them rather than trusting them to look right.

**Arabic yeh and kaf.** ``ي`` (U+064A) and ``ك`` (U+0643) are Arabic; Persian
is ``ی`` (U+06CC) and ``ک`` (U+06A9). They render almost identically and sort,
search and hyphenate differently.

Both are detected here and neither is silently repaired in text the user
typed. ``fix_orthography`` exists and is called on strings *this application*
produces; a point someone wrote is theirs.
"""

import re
import unicodedata

__all__ = [
    "ZWNJ", "PERSIAN_DIGITS", "DECIMAL_SEP", "THOUSANDS_SEP",
    "script_counts", "direction", "is_persian_major", "analyse",
    "to_persian_digits", "to_latin_digits", "fix_orthography",
    "MONTHS_FA", "WEEKDAYS_FA", "gregorian_to_jalali", "jalali_to_gregorian",
    "format_date", "is_jalali_leap", "lint", "LABELS", "labels", "stylesheet",
    "FONT_SANS_FA", "FONT_SERIF_FA",
]

ZWNJ = "‌"

#: Persian (extended Arabic-Indic) digits. Note these are NOT the Arabic-Indic
#: digits U+0660-U+0669 used in Arabic proper - four of the ten differ.
PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
ARABIC_INDIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"

DECIMAL_SEP = "٫"       # ٫ - not the Latin full stop
THOUSANDS_SEP = "٬"     # ٬ - not the Latin comma

_FA_DIGIT_MAP = {ord(c): PERSIAN_DIGITS[i] for i, c in enumerate("0123456789")}
_LATIN_DIGIT_MAP = {}
for _i, _c in enumerate(PERSIAN_DIGITS):
    _LATIN_DIGIT_MAP[ord(_c)] = "0123456789"[_i]
for _i, _c in enumerate(ARABIC_INDIC_DIGITS):
    _LATIN_DIGIT_MAP[ord(_c)] = "0123456789"[_i]

#: Arabic letters that must be their Persian equivalents in Persian text.
_ORTHOGRAPHY = {
    "ي": "ی",   # ARABIC YEH        -> FARSI YEH
    "ى": "ی",   # ALEF MAKSURA      -> FARSI YEH
    "ك": "ک",   # ARABIC KAF        -> KEHEH
    "ۀ": "ه‌ی",   # heh with yeh above -> heh + ZWNJ + yeh
}
_ORTH_MAP = {ord(k): v for k, v in _ORTHOGRAPHY.items()}


# ---------------------------------------------------------------------------
# Direction
# ---------------------------------------------------------------------------

def script_counts(text):
    """Count the letters that actually carry a direction.

    Digits, punctuation and spaces are neutral under the bidi algorithm and
    deciding a page's direction from them is how a page of English prose with
    a Persian title ends up right-to-left. Only strong characters are counted.
    """
    rtl = ltr = 0
    for ch in text or "":
        bidi = unicodedata.bidirectional(ch)
        if bidi in ("R", "AL"):
            rtl += 1
        elif bidi == "L":
            ltr += 1
    return {"rtl": rtl, "ltr": ltr}


def direction(text, minimum=8):
    """``"rtl"`` when the major text is right-to-left, else ``"ltr"``.

    "Major" is taken literally - more strong RTL letters than strong LTR ones.
    A Persian report quoting English sources stays Persian; an English report
    with a Persian quotation in it stays English, and the quotation gets its
    own direction from ``dir="auto"`` at the element level rather than
    flipping the document.

    ``minimum`` guards the degenerate case: a title of "OK" or an empty draft
    should not decide a layout. Under it, the answer is ``"ltr"``, because
    left-to-right is what every template was designed in and a wrong guess
    there costs nothing.
    """
    c = script_counts(text)
    if c["rtl"] + c["ltr"] < minimum:
        return "ltr"
    return "rtl" if c["rtl"] > c["ltr"] else "ltr"


def is_persian_major(text, minimum=8):
    return direction(text, minimum) == "rtl"


def analyse(text):
    """Direction, language tag and the counts that produced them.

    The counts travel with the verdict so a caller - or a gate file - can say
    *why* a document came out right-to-left instead of asserting it.
    """
    c = script_counts(text)
    d = direction(text)
    return {
        "dir": d,
        "lang": "fa" if d == "rtl" else "en",
        "rtl": c["rtl"],
        "ltr": c["ltr"],
        "ratio": (c["rtl"] / (c["rtl"] + c["ltr"])) if (c["rtl"] + c["ltr"]) else 0.0,
    }


# ---------------------------------------------------------------------------
# Digits
# ---------------------------------------------------------------------------

def to_persian_digits(text):
    """ASCII digits to Persian ones.

    Applied to chrome this application generates - dates, counts, page
    numbers - and never to text the user wrote, where it would silently
    corrupt a DOI, a URL, an ISBN or a year inside a verbatim quotation.
    """
    return str(text or "").translate(_FA_DIGIT_MAP)


def to_latin_digits(text):
    """Persian or Arabic-Indic digits back to ASCII, for parsing and sorting."""
    return str(text or "").translate(_LATIN_DIGIT_MAP)


def fix_orthography(text):
    """Arabic yeh/kaf/alef-maksura to their Persian forms.

    Safe on strings this application owns. Not applied to user text: a point
    someone typed may legitimately quote Arabic, and rewriting a quotation is
    exactly the kind of silent "improvement" that makes an export untrustable.
    """
    return str(text or "").translate(_ORTH_MAP)


# ---------------------------------------------------------------------------
# The Jalali (Solar Hijri) calendar
# ---------------------------------------------------------------------------

#: Month names. All single words - no half-spaces to get wrong.
MONTHS_FA = ["فروردین",      # فروردین
             "اردیبهشت",  # اردیبهشت
             "خرداد",                  # خرداد
             "تیر",                              # تیر
             "مرداد",                  # مرداد
             "شهریور",            # شهریور
             "مهر",                              # مهر
             "آبان",                        # آبان
             "آذر",                              # آذر
             "دی",                                    # دی
             "بهمن",                        # بهمن
             "اسفند"]                  # اسفند

#: Weekday names, Saturday first. Four of the seven carry a mandatory ZWNJ -
#: یک‌شنبه, سه‌شنبه, پنج‌شنبه - and the test counts them.
WEEKDAYS_FA = ["شنبه",                                    # شنبه
               "یک‌شنبه",                  # یک‌شنبه
               "دوشنبه",                        # دوشنبه
               "سه‌شنبه",                  # سه‌شنبه
               "چهارشنبه",            # چهارشنبه
               "پنج‌شنبه",            # پنج‌شنبه
               "جمعه"]                                    # جمعه

_G_DAYS_BEFORE_MONTH = (0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334)


def is_jalali_leap(jy):
    """The 33-year cycle rule.

    Astronomically the Solar Hijri year begins at the vernal equinox in Tehran
    and leap years cannot be derived from arithmetic alone. This is the
    conventional 33-year approximation that every civil implementation uses;
    it agrees with the Iranian civil calendar over the range this application
    will ever format - the last few decades and the next few.
    """
    return (jy % 33) in (1, 5, 9, 13, 17, 22, 26, 30)


def gregorian_to_jalali(gy, gm, gd):
    """(year, month, day) Gregorian to (year, month, day) Jalali."""
    if gy > 1600:
        jy = 979
        gy -= 1600
    else:
        jy = 0
        gy -= 621
    gy2 = gy + 1 if gm > 2 else gy
    days = (365 * gy + (gy2 + 3) // 4 - (gy2 + 99) // 100 + (gy2 + 399) // 400
            - 80 + gd + _G_DAYS_BEFORE_MONTH[gm - 1])
    jy += 33 * (days // 12053)
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm = 1 + days // 31
        jd = 1 + days % 31
    else:
        jm = 7 + (days - 186) // 30
        jd = 1 + (days - 186) % 30
    return jy, jm, jd


def jalali_to_gregorian(jy, jm, jd):
    """The inverse, so the conversion can be round-tripped in a test.

    A calendar routine that is only ever exercised in one direction is a
    calendar routine nobody has checked.
    """
    if jy > 979:
        gy = 1600
        jy -= 979
    else:
        gy = 621
    days = (365 * jy + (jy // 33) * 8 + ((jy % 33) + 3) // 4 + 78 + jd
            + ((jm - 1) * 31 if jm < 7 else ((jm - 7) * 30 + 186)))
    gy += 400 * (days // 146097)
    days %= 146097
    if days > 36524:
        days -= 1
        gy += 100 * (days // 36524)
        days %= 36524
        if days >= 365:
            days += 1
    gy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        gy += (days - 1) // 365
        days = (days - 1) % 365
    gd = days + 1
    leap = (gy % 4 == 0 and gy % 100 != 0) or (gy % 400 == 0)
    months = (0, 31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    gm = 0
    for gm in range(1, 13):
        if gd <= months[gm]:
            break
        gd -= months[gm]
    return gy, gm, gd


def format_date(dt, lang="en", long=True):
    """A date in the calendar and digits the document's language expects.

    A Persian report dated in the Gregorian calendar with Latin digits reads
    as a translation of an English document, which is precisely the impression
    the whole of this module exists to avoid. So ``lang="fa"`` means Solar
    Hijri, Persian month name, Persian digits - the form every Persian
    business and academic document uses.
    """
    if lang != "fa":
        return dt.strftime("%d %B %Y") if long else dt.strftime("%Y-%m-%d")
    jy, jm, jd = gregorian_to_jalali(dt.year, dt.month, dt.day)
    if long:
        return "%s %s %s" % (to_persian_digits(str(jd)), MONTHS_FA[jm - 1],
                             to_persian_digits(str(jy)))
    return to_persian_digits("%04d/%02d/%02d" % (jy, jm, jd))


# ---------------------------------------------------------------------------
# The mechanical lint
# ---------------------------------------------------------------------------

#: Signals that are string-level and near-decisive. Each one is a defect a
#: reader without Persian can find by searching, which is the only kind this
#: module is willing to claim. Nothing here judges whether a sentence is good.
_MISSING_ZWNJ = re.compile(
    "(?:"
    "\\u0645\\u06cc \\u0634|\\u0645\\u06cc \\u06a9|\\u0645\\u06cc \\u0631|"   # می شود/کند/رود
    "\\u0646\\u0645\\u06cc \\u0634|\\u0646\\u0645\\u06cc \\u06a9|"            # نمی شود/کند
    "[\\u0600-\\u06ff] \\u0647\\u0627[\\u06cc\\u0654\\s\\u060c.]|"            # ... ها
    "[\\u0600-\\u06ff] \\u062a\\u0631\\u06cc\\u0646"                          # ... ترین
    ")")

_BUREAUCRATIC = (
    ("mibashad", "می‌باشد",
     "می‌باشد reads as bureaucratic Persian; "
     "است is the natural verb."),
    ("gardid", "گردید",
     "گردید is dry officialese; شد is the natural past."),
    ("namud", "نمود",
     "نمود for 'did' is officialese; کرد is natural."),
    ("mored_qarar", "مورد",
     "مورد ... قرار گرفت is a "
     "calqued passive; one simple verb usually replaces it."),
    ("lazem_be_zekr", "لازم به ذکر",
     "'It should be noted that' translated; Persian starts at the content."),
)


def lint(text):
    """Mechanical defects in a Persian string. Never a judgement of style.

    Returns a list of ``{code, message, count}``. An empty list means no
    *detectable* defect - not that the Persian is good. Saying "I cannot tell
    whether this reads naturally" is the correct output for everything this
    function deliberately does not attempt.
    """
    text = str(text or "")
    if not is_persian_major(text, minimum=4):
        return []
    out = []

    n = len(_MISSING_ZWNJ.findall(text))
    if n:
        out.append({"code": "zwnj", "count": n,
                    "message": "%d place(s) look like a missing half-space "
                               "(نیم‌فاصله) - "
                               "e.g. می شود instead of "
                               "می‌شود." % n})

    arabic = sum(text.count(ch) for ch in ("ي", "ك", "ى"))
    if arabic:
        out.append({"code": "arabic_letters", "count": arabic,
                    "message": "%d Arabic ي/ك where Persian "
                               "ی/ک is expected." % arabic})

    latin = len(re.findall(r"[0-9]", text))
    persian = sum(text.count(ch) for ch in PERSIAN_DIGITS)
    if latin and persian:
        out.append({"code": "mixed_digits", "count": latin + persian,
                    "message": "Latin and Persian digits appear in the same text; "
                               "pick one and hold it for the whole document."})

    for ch, name in ((",", "،"), (";", "؛"), ("?", "؟")):
        c = text.count(ch)
        if c:
            out.append({"code": "punctuation", "count": c,
                        "message": "%d Latin '%s' where Persian '%s' is expected."
                                   % (c, ch, name)})

    # The em dash has no place in Persian punctuation - a colon or a new
    # sentence carries the same break. It arrives by way of English drafts.
    dashes = text.count(chr(0x2014)) + text.count(chr(0x2013))
    if dashes:
        out.append({"code": "em_dash", "count": dashes,
                    "message": "%d en/em dash(es); Persian uses a colon or a new "
                               "sentence instead." % dashes})

    for code, needle, message in _BUREAUCRATIC:
        c = text.count(needle)
        if c:
            out.append({"code": code, "count": c, "message": message})
    return out


# ---------------------------------------------------------------------------
# Fixed document vocabulary
# ---------------------------------------------------------------------------

#: The handful of words a report's chrome needs, per language. These are the
#: only Persian words this application puts on a page that the user did not
#: write, which is why they are a closed list rather than a translation call.
LABELS = {
    "en": {
        "references": "References",
        "sources": "Sources",
        "contents": "Contents",
        "abstract": "Abstract",
        "figures": "Figures",
        "points": "Points",
        "period": "Period",
        "author": "Author",
        "date": "Date",
        "notes": "Notes and commentary",
    },
    "fa": {
        "references": "منابع",              # منابع
        "sources": "منابع",                 # منابع
        "contents": "فهرست",                # فهرست
        "abstract": "چکیده",                # چکیده
        "figures": "تصویرها",     # تصویرها
        "points": "نکته‌ها",      # نکته‌ها
        "period": "بازهٔ زمانی",
        "author": "نویسنده",      # نویسنده
        "date": "تاریخ",                    # تاریخ
        "notes": "یادداشت‌ها "
                 "و تفسیر",            # یادداشت‌ها و تفسیر
    },
}


def labels(lang):
    return dict(LABELS.get(lang) or LABELS["en"])


# ---------------------------------------------------------------------------
# Typesetting
# ---------------------------------------------------------------------------

#: Font stacks, best-first, landing somewhere that actually exists.
#:
#: Vazirmatn, Sahel and the IRANSans family are what a Persian document should
#: be set in, and none of them is on a stock Windows machine. So the chain ends
#: at **Tahoma**, which is - and has complete, correctly-shaped Persian
#: coverage. Letting it fall through to the generic ``sans-serif`` keyword
#: instead would land on a Latin face and render Persian through a fallback
#: chain nobody designed, which is how Persian ends up looking broken in
#: documents that are otherwise fine.
FONT_SANS_FA = ('"Vazirmatn","Vazir","IRANSansX","IRANSans","Sahel","Shabnam",'
                '"Segoe UI",Tahoma,"Noto Sans Arabic",sans-serif')
FONT_SERIF_FA = ('"Noto Naskh Arabic","Vazirmatn","IRANSansX","Sahel",'
                 '"Segoe UI",Tahoma,serif')


def stylesheet(direction_):
    """The Persian typesetting block, or an empty string for a left-to-right
    document.

    Empty is the important half: an English export must be byte-identical to
    what it was before any of this existed, and the cheapest way to guarantee
    that is to add literally nothing to it.

    Everything below is a documented convention rather than a preference:

    * **Leading.** Persian needs more of it than Latin at the same size -
      the script has deeper descenders and its diacritics sit above the line.
      1.6 is comfortable for English and cramped for Persian.
    * **No italic.** Persian has no italic tradition and no italic cuts, so a
      browser synthesises an oblique by shearing the glyphs. It reads as a
      rendering fault, not as emphasis. Weight carries emphasis instead.
    * **Persian digits in ordered lists**, because those numbers are the
      document's own voice.
    * **Latin digits in citations.** A bracketed [12] in the body has to match
      [12] in the reference list, and the reference itself is usually an
      English title with a Latin year. Translating half of that pairing is
      how a reader loses the thread.
    * **Isolation for Latin runs.** A URL, a DOI or a product name inside
      Persian prose is a left-to-right island. ``unicode-bidi:isolate`` stops
      the bidi algorithm from dragging the surrounding punctuation into it -
      the reason a trailing full stop so often jumps to the wrong end of a
      link in Persian documents.
    """
    if direction_ != "rtl":
        return ""
    return """
/* --- Persian typesetting (injected because the major text is right-to-left)
   See persian.stylesheet() for why each of these is here. ------------------ */
html[dir="rtl"]{
  --fa-sans:%s;
  --fa-serif:%s;
  --sans:var(--fa-sans); --serif:var(--fa-serif); --ui:var(--fa-sans);
}
html[dir="rtl"] body{font-family:var(--fa-sans);line-height:1.85;letter-spacing:0}
html[dir="rtl"] h1,html[dir="rtl"] h2,html[dir="rtl"] h3,
html[dir="rtl"] h4,html[dir="rtl"] h5{font-family:var(--fa-sans);line-height:1.5}
/* Persian has no italic cuts; the browser would shear the glyphs. */
html[dir="rtl"] i,html[dir="rtl"] em,html[dir="rtl"] cite,
html[dir="rtl"] h3,html[dir="rtl"] .abstract{font-style:normal}
html[dir="rtl"] em,html[dir="rtl"] i{font-weight:700}
/* The document's own numbering speaks Persian. */
html[dir="rtl"] ol:not(.refs):not(.toc-list){list-style-type:persian}
/* Citations stay Latin so [12] in the body matches [12] in the list. */
html[dir="rtl"] a.cite,html[dir="rtl"] ol.refs{font-variant-numeric:lining-nums}
html[dir="rtl"] ol.refs li{text-align:start}
/* Left-to-right islands: URLs, code, identifiers. */
html[dir="rtl"] code,html[dir="rtl"] pre,html[dir="rtl"] kbd,html[dir="rtl"] samp,
html[dir="rtl"] .mono{direction:ltr;unicode-bidi:isolate;text-align:start}
html[dir="rtl"] a[href^="http"],html[dir="rtl"] a[href^="mailto"]{unicode-bidi:isolate}
html[dir="rtl"] time,html[dir="rtl"] .doi,html[dir="rtl"] .url{unicode-bidi:isolate}
/* Tables and figures inherit the page direction; captions follow the text. */
html[dir="rtl"] table{direction:rtl}
html[dir="rtl"] th,html[dir="rtl"] td{text-align:start}
html[dir="rtl"] figcaption{text-align:start}
/* Persian text justifies badly without kashida, which CSS cannot do, so it
   is set ragged-end rather than justified with stretched word spaces. */
html[dir="rtl"] p,html[dir="rtl"] li,html[dir="rtl"] blockquote{text-align:start}
""" % (FONT_SANS_FA, FONT_SERIF_FA)
