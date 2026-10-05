"""Headless tests for persian.py - direction, digits, calendar, orthography.

Every check here is mechanical, which is the whole point of the module: these
are the Persian defects a reader without Persian can find by counting code
points. Nothing in this file claims a sentence reads well.

Two of them matter more than the rest, because they are invisible:

  * a missing ZWNJ makes a different word and looks identical in a terminal,
  * Arabic yeh/kaf render almost the same as Persian yeh/kaf.

So the fixed Persian vocabulary the app ships is counted, not eyeballed.
"""

import datetime
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import trailmark.persian as persian

FAILS = []


def check(label, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + label + (" - %s" % (detail,) if detail else ""))
    if not ok:
        FAILS.append(label)


FA = "این یک متن فارسی است"
EN = "This is an English document with a reasonable amount of text in it"


# ---------------------------------------------------------------------------
# 1. Direction
# ---------------------------------------------------------------------------
print("\n-- direction --")

check("persian text is rtl", persian.direction(FA + FA) == "rtl", persian.direction(FA + FA))
check("english text is ltr", persian.direction(EN) == "ltr", persian.direction(EN))

# Digits and punctuation are neutral under bidi and must not decide a layout.
check("digits alone do not decide", persian.direction("1234567890 ... 42") == "ltr",
      persian.direction("1234567890 ... 42"))
check("punctuation alone does not decide", persian.direction("--- ... !!! ???") == "ltr")

# A short string must not flip a document.
check("two persian letters under the floor stay ltr",
      persian.direction("سلام") == "ltr",
      persian.direction("سلام"))
check("empty is ltr", persian.direction("") == "ltr")
check("None is ltr", persian.direction(None) == "ltr")

# "Major" means major. An English report quoting Persian stays English; a
# Persian report citing English sources stays Persian.
check("english with a persian quotation stays ltr",
      persian.direction(EN + " " + FA) == "ltr",
      persian.analyse(EN + " " + FA))
check("persian with an english citation stays rtl",
      persian.direction(FA + FA + FA + " (Jung et al. 2018)") == "rtl",
      persian.analyse(FA + FA + FA + " (Jung et al. 2018)"))

a = persian.analyse(FA + FA)
check("analyse reports lang fa", a["lang"] == "fa", a)
check("analyse carries the counts that decided it", a["rtl"] > 0 and a["ltr"] == 0, a)
check("analyse ratio is between 0 and 1", 0.0 <= a["ratio"] <= 1.0, a)
check("english analyse reports lang en", persian.analyse(EN)["lang"] == "en")

# Hebrew is right-to-left too, and must not be mislabelled as Persian.
HE = "שלום עולם זה טקסט"
check("hebrew is rtl", persian.direction(HE) == "rtl", persian.direction(HE))


# ---------------------------------------------------------------------------
# 2. Digits
# ---------------------------------------------------------------------------
print("\n-- digits --")

check("ascii to persian digits",
      persian.to_persian_digits("2026") == "۲۰۲۶",
      persian.to_persian_digits("2026"))
check("persian digits back to ascii",
      persian.to_latin_digits("۲۰۲۶") == "2026",
      persian.to_latin_digits("۲۰۲۶"))
# Arabic-Indic (U+0660..) differ from Persian (U+06F0..) in four of ten and
# both must fold back to ASCII for parsing.
check("arabic-indic digits also fold back",
      persian.to_latin_digits("٠١٤٦") == "0146",
      persian.to_latin_digits("٠١٤٦"))
check("round-trip is identity",
      persian.to_latin_digits(persian.to_persian_digits("9876543210")) == "9876543210")
check("non-digits are untouched",
      persian.to_persian_digits("v1.2-beta") == "v۱.۲-beta",
      persian.to_persian_digits("v1.2-beta"))
check("persian and arabic-indic digit sets really differ",
      persian.PERSIAN_DIGITS[4] != persian.ARABIC_INDIC_DIGITS[4],
      (persian.PERSIAN_DIGITS[4], persian.ARABIC_INDIC_DIGITS[4]))


# ---------------------------------------------------------------------------
# 3. Orthography
# ---------------------------------------------------------------------------
print("\n-- orthography --")

# Arabic yeh U+064A and kaf U+0643 vs Persian yeh U+06CC and keheh U+06A9.
arabic_spelling = "تريل"       # تريل, Arabic yeh
persian_spelling = "تریل"      # تریل, Persian yeh
check("arabic yeh is folded to persian yeh",
      persian.fix_orthography(arabic_spelling) == persian_spelling)
check("arabic kaf is folded to keheh",
      persian.fix_orthography("كتاب") == "کتاب")
check("already-persian text is unchanged",
      persian.fix_orthography(persian_spelling) == persian_spelling)
check("latin text is unchanged", persian.fix_orthography(EN) == EN)


# ---------------------------------------------------------------------------
# 4. The fixed vocabulary the app ships - counted, not eyeballed
# ---------------------------------------------------------------------------
print("\n-- shipped persian strings --")

shipped = list(persian.MONTHS_FA) + list(persian.WEEKDAYS_FA) + \
    list(persian.LABELS["fa"].values())

bad_yeh = [w for w in shipped if "ي" in w or "ى" in w]
check("no Arabic yeh in any shipped string", not bad_yeh, bad_yeh)
bad_kaf = [w for w in shipped if "ك" in w]
check("no Arabic kaf in any shipped string", not bad_kaf, bad_kaf)

check("twelve months", len(persian.MONTHS_FA) == 12, len(persian.MONTHS_FA))
check("seven weekdays", len(persian.WEEKDAYS_FA) == 7, len(persian.WEEKDAYS_FA))
check("months are distinct", len(set(persian.MONTHS_FA)) == 12)
check("no month carries a stray half-space",
      not [m for m in persian.MONTHS_FA if persian.ZWNJ in m],
      [m for m in persian.MONTHS_FA if persian.ZWNJ in m])

# The three weekdays that MUST carry a ZWNJ: یک‌شنبه, سه‌شنبه, پنج‌شنبه.
# Written without it they are two words and the wrong ones.
zwnj_days = [d for d in persian.WEEKDAYS_FA if persian.ZWNJ in d]
check("exactly three weekdays carry a half-space", len(zwnj_days) == 3, zwnj_days)
check("yek-shanbe has its half-space",
      persian.WEEKDAYS_FA[1] == "یک‌شنبه",
      persian.WEEKDAYS_FA[1])

# نکته‌ها and یادداشت‌ها are plurals in ها and need the half-space.
for key in ("points", "notes"):
    v = persian.LABELS["fa"][key]
    check("label %r carries its half-space" % key, persian.ZWNJ in v, v)

check("no shipped persian string uses a latin comma",
      not [w for w in shipped if "," in w], [w for w in shipped if "," in w])
check("en and fa label sets have the same keys",
      set(persian.LABELS["en"]) == set(persian.LABELS["fa"]),
      set(persian.LABELS["en"]) ^ set(persian.LABELS["fa"]))
check("labels() falls back to english for an unknown language",
      persian.labels("de") == persian.LABELS["en"])


# ---------------------------------------------------------------------------
# 5. The Jalali calendar
# ---------------------------------------------------------------------------
print("\n-- calendar --")

# Anchors that can be checked against any Persian calendar.
for gy, gm, gd, want in [
    (2026, 3, 21, (1405, 1, 1)),    # Nowruz 1405
    (2026, 9, 25, (1405, 7, 3)),
    (2025, 3, 21, (1404, 1, 1)),    # Nowruz 1404
    (2024, 3, 20, (1403, 1, 1)),    # Nowruz 1403 fell on the 20th
    (2000, 1, 1, (1378, 10, 11)),
    (1979, 2, 11, (1357, 11, 22)),  # 22 Bahman 1357
    (2021, 12, 31, (1400, 10, 10)),
]:
    got = persian.gregorian_to_jalali(gy, gm, gd)
    check("%04d-%02d-%02d -> %s" % (gy, gm, gd, want), got == want, got)

# Round-trip every day over 12 years, including leap years both sides.
bad = []
d = datetime.date(2018, 1, 1)
end = datetime.date(2030, 1, 1)
n = 0
while d < end:
    jy, jm, jd = persian.gregorian_to_jalali(d.year, d.month, d.day)
    back = persian.jalali_to_gregorian(jy, jm, jd)
    if back != (d.year, d.month, d.day):
        bad.append((d.isoformat(), (jy, jm, jd), back))
        if len(bad) > 4:
            break
    n += 1
    d += datetime.timedelta(days=1)
check("round-trips every day 2018-2030 (%d days)" % n, not bad, bad[:3])

# Month lengths: 1-6 are 31 days, 7-11 are 30, Esfand is 29 or 30.
lengths = {}
d = datetime.date(2019, 1, 1)
while d < datetime.date(2029, 1, 1):
    jy, jm, jd = persian.gregorian_to_jalali(d.year, d.month, d.day)
    lengths[(jy, jm)] = max(lengths.get((jy, jm), 0), jd)
    d += datetime.timedelta(days=1)
full = {k: v for k, v in lengths.items() if 1390 < k[0] < 1410}
bad_len = [k for k, v in full.items()
           if (k[1] <= 6 and v != 31) or (7 <= k[1] <= 11 and v != 30)
           or (k[1] == 12 and v not in (29, 30))]
# The first and last partial years are excluded by construction below.
years = sorted({k[0] for k in full})
bad_len = [k for k in bad_len if years[0] < k[0] < years[-1]]
check("every month has the right length", not bad_len, bad_len[:5])

# A leap Esfand has 30 days, and the 33-year rule must agree with the count.
esfand = {y: full.get((y, 12)) for y in years[1:-1]}
mismatch = [(y, v, persian.is_jalali_leap(y)) for y, v in esfand.items()
            if v is not None and ((v == 30) != persian.is_jalali_leap(y))]
check("is_jalali_leap agrees with the measured length of Esfand",
      not mismatch, mismatch)

print("   Esfand lengths measured: %s" % sorted(esfand.items()))


# ---------------------------------------------------------------------------
# 6. format_date
# ---------------------------------------------------------------------------
print("\n-- format_date --")

d = datetime.date(2026, 9, 25)
fa = persian.format_date(d, "fa")
check("persian date uses the jalali year",
      persian.to_latin_digits(fa).endswith("1405"), fa)
check("persian date uses persian digits",
      not any(c.isdigit() and c in "0123456789" for c in fa), fa)
check("persian date names the month",
      persian.MONTHS_FA[6] in fa, fa)
check("short persian date is jalali y/m/d",
      persian.to_latin_digits(persian.format_date(d, "fa", long=False)) == "1405/07/03",
      persian.format_date(d, "fa", long=False))
check("english date is gregorian",
      "2026" in persian.format_date(d, "en"), persian.format_date(d, "en"))
check("an unknown language falls back to gregorian",
      "2026" in persian.format_date(d, "de"), persian.format_date(d, "de"))
print("   fa: %s   en: %s" % (fa, persian.format_date(d, "en")))


# ---------------------------------------------------------------------------
# 7. lint - mechanical only
# ---------------------------------------------------------------------------
print("\n-- lint --")

codes = lambda t: sorted(x["code"] for x in persian.lint(t))  # noqa: E731

check("english text is never linted as persian", persian.lint(EN) == [], persian.lint(EN))
check("clean persian has no findings",
      persian.lint("این متن درست "
                   "است") == [], "")

# می شود without the half-space.
t = "این کار می شود و "\
    "تمام است"
check("missing half-space is found", "zwnj" in codes(t), codes(t))
# The same sentence written correctly must be clean.
t_ok = t.replace("می ش", "می‌ش")
check("the corrected sentence is clean", "zwnj" not in codes(t_ok), codes(t_ok))

# Arabic letters inside Persian.
t = "این تريل است "\
    "و متن دارد"
check("arabic yeh is found", "arabic_letters" in codes(t), codes(t))

# Mixed digit systems.
t = "سال ۱۴۰۵ و 2026 است "\
    "و متن دارد"
check("mixed digits are found", "mixed_digits" in codes(t), codes(t))

# Latin punctuation in Persian prose.
t = "این متن, درست است "\
    "و کامل است"
check("latin comma is found", "punctuation" in codes(t), codes(t))

# می‌باشد - the classic bureaucratic verb.
t = "این درست می‌باشد "\
    "و کامل است"
check("mibashad is found", "mibashad" in codes(t), codes(t))

# lint never mutates and never raises on odd input.
for odd in (None, "", "   ", "‌", "1234", EN):
    try:
        persian.lint(odd)
        ok = True
    except Exception as e:
        ok = False
        detail = e
    check("lint survives %r" % (odd,), ok, "" if ok else detail)

check("every finding carries code/message/count",
      all(set(x) == {"code", "message", "count"} for x in persian.lint(t)),
      persian.lint(t))


print()
print("ALL CHECKS PASSED" if not FAILS else "FAILED: " + ", ".join(FAILS))
sys.exit(1 if FAILS else 0)
