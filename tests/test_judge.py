"""The second opinion, offline.

Not one check here touches the network. Every call to Jev is stubbed, because
the question this file answers is not "is the model good" - that is measured in
evals/judge_eval.py against labelled cases - but "does Trailmark still work
when the model is absent, slow, wrong, or unsure", which is the condition it
will be in most of the time.

The load-bearing test is section 3: with the judge off, `ground_science` must
produce byte-identical findings to the version that existed before judge.py.
Everything else in this feature is an improvement; that one is a promise.
"""

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import trailmark.judge as judge
import trailmark.pipeline as pipeline
import trailmark.point_store as point_store
import point_logger as point_logger
import trailmark.ui as ui

FAILS = []


def check(label, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + label + (" - %s" % (detail,) if detail else ""))
    if not ok:
        FAILS.append(label)


OFF = {"enabled": False, "api_key": ""}
KEYLESS = {"enabled": True, "api_key": ""}
ON = {"enabled": True, "api_key": "ts-not-a-real-key", "notes": True, "kinds": True}


# ---------------------------------------------------------------------------
print("-- 1. it stays shut unless it is opened --")
# ---------------------------------------------------------------------------

check("off is unavailable", judge.available(OFF) is False)
check("enabled without a key is unavailable", judge.available(KEYLESS) is False)
check("enabled with a key is available", judge.available(ON) is True)
check("None config is unavailable", judge.available(None) is False)

calls = []
real_urlopen = judge.urllib.request.urlopen


def no_network(*a, **kw):
    calls.append(a)
    raise judge.urllib.error.URLError("the suite does not have a network")


judge.urllib.request.urlopen = no_network
try:
    check("ask() with no key makes no request", judge.ask(OFF, "s", {"q": {}}) == {}
          and not calls, len(calls))
    calls.clear()
    check("ask() with no questions makes no request",
          judge.ask(ON, "s", {}) == {} and not calls, len(calls))
    calls.clear()
    # And when it does reach the network and the network refuses, it is still {}.
    out = judge.ask(ON, "s", {"q": {"type": "choice", "instructions": "i",
                                    "criteria": {"a": "a", "b": "b"}}})
    check("a dead network returns the empty verdict, not an exception",
          out == {} and len(calls) == 1, "%r calls=%d" % (out, len(calls)))
finally:
    judge.urllib.request.urlopen = real_urlopen


# ---------------------------------------------------------------------------
print()
print("-- 2. retrieval, which is code and not judgement --")
# ---------------------------------------------------------------------------

DRAFT = """## Findings

Cargo workspaces let several crates share one lockfile and one target directory.

It is worth remembering that Rust's borrow checker does not function as a
proof assistant, whatever the type system suggests.

Pricing was revised in the second quarter to emphasise annual billing.
"""

p = judge.best_passage("The borrow checker is not a proof assistant.", DRAFT)
check("best_passage finds the paragraph that restates the note",
      "proof assistant" in p and "lockfile" not in p, p[:60].replace("\n", " "))
check("best_passage on an empty draft says nothing",
      judge.best_passage("anything at all", "") == "")
check("best_passage on an empty note says nothing",
      judge.best_passage("", DRAFT) == "")
check("best_passage on a note that shares no words says nothing",
      judge.best_passage("zzzz qqqq", DRAFT) == "",
      judge.best_passage("zzzz qqqq", DRAFT)[:40])

# The confidence gate, which is the whole routing mechanism.
A_HIGH = {"q": {"type": "choice", "choice": "preserved", "confidence": 0.93,
                "probabilities": {}}}
A_LOW = {"q": {"type": "choice", "choice": "preserved", "confidence": 0.31,
               "probabilities": {}}}
check("a confident answer passes the gate",
      judge._choice(A_HIGH, "q", 0.8) == ("preserved", 0.93))
check("an unconfident answer is no answer", judge._choice(A_LOW, "q", 0.8) is None)
check("a missing answer is no answer", judge._choice({}, "q", 0.5) is None)
check("a malformed answer is no answer",
      judge._choice({"q": {"type": "noul", "noul": 0.9}}, "q", 0.5) is None)
check("a non-numeric confidence is no answer",
      judge._choice({"q": {"type": "choice", "choice": "x", "confidence": "high"}},
                    "q", 0.5) is None)


# ---------------------------------------------------------------------------
print()
print("-- 3. with the judge off, nothing changed --")
# ---------------------------------------------------------------------------

SCI = {"enabled": True, "separate_notes": True}
NOTE_TEXT = "The borrow checker is not a proof assistant."
ENTRIES = [
    {"id": "e1", "kind": "note", "text": NOTE_TEXT},
    {"id": "e2", "kind": "quote", "text": "No amount of static analysis substitutes for a specification."},
]

GOOD = """## Findings

No amount of static analysis substitutes for a specification. [1]

## %s

%s
""" % (pipeline.NOTES_HEADING, NOTE_TEXT)

# The note was reworded - allowed - so the substring test fires. This is the
# false positive the whole feature exists to remove.
REWORDED = GOOD.replace(NOTE_TEXT,
                        "It is worth remembering that Rust's borrow checker does "
                        "not function as a proof assistant.")

ok, f = pipeline.ground_science(GOOD, ENTRIES, SCI)
check("an untouched draft passes with the judge absent", ok and not f, f)

ok_off, f_off = pipeline.ground_science(REWORDED, ENTRIES, SCI)
check("a reworded note still fails with the judge absent", not ok_off and f_off, f_off)
check("and the finding names the note", "missing" in (f_off[0] if f_off else ""), f_off)

ok_none, f_none = pipeline.ground_science(REWORDED, ENTRIES, SCI, judge_cfg=None)
check("judge_cfg=None behaves exactly like no judge_cfg at all",
      (ok_none, f_none) == (ok_off, f_off), "%r vs %r" % (f_none, f_off))

ok_disabled, f_disabled = pipeline.ground_science(REWORDED, ENTRIES, SCI, judge_cfg=OFF)
check("a disabled judge behaves exactly like no judge",
      (ok_disabled, f_disabled) == (ok_off, f_off), f_disabled)

# A quotation is still mechanical, and must stay that way even when the judge
# is on - a model has no business deciding whether a verbatim quote is verbatim.
REWORDED_QUOTE = GOOD.replace("No amount of static analysis substitutes for a specification.",
                              "Static analysis is no substitute for a specification.")
stub_calls = []


def stub_ask(cfg, state, questions, timeout=None):
    stub_calls.append({"state": state, "questions": questions})
    answers = {}
    for qid in questions:
        answers[qid] = STUB_ANSWER(qid, state)
    return {"model": "jev-stub", "answers": answers}


STUB_ANSWER = lambda qid, state: {"type": "choice", "choice": "preserved",
                                  "confidence": 0.99, "probabilities": {}}
real_ask = judge.ask
judge.ask = stub_ask
try:
    ok_q, f_q = pipeline.ground_science(REWORDED_QUOTE, ENTRIES, SCI, judge_cfg=ON)
    check("a reworded quotation still fails, judge or no judge",
          not ok_q and any("quotation" in x for x in f_q), f_q)
finally:
    judge.ask = real_ask


# ---------------------------------------------------------------------------
print()
print("-- 4. what the judge is allowed to change --")
# ---------------------------------------------------------------------------

judge.ask = stub_ask
try:
    # (a) Confident "preserved" removes the false positive.
    stub_calls.clear()
    STUB_ANSWER = lambda qid, state: {"type": "choice", "choice": "preserved",
                                      "confidence": 0.93, "probabilities": {}}
    ok_a, f_a = pipeline.ground_science(REWORDED, ENTRIES, SCI, judge_cfg=ON)
    check("a confident 'preserved' rescues an allowed rewording", ok_a and not f_a, f_a)
    check("and it asked exactly once, with every note in the one request",
          len(stub_calls) == 1 and len(stub_calls[0]["questions"]) == 1,
          "%d call(s)" % len(stub_calls))
    sent = json.dumps(stub_calls[0]["state"], ensure_ascii=False)
    check("the whole draft was not sent - only the nearest passage",
          "Pricing was revised" not in sent and "borrow checker" in sent,
          "%d chars of state" % len(sent))

    # (b) An unconfident "preserved" must NOT overturn: relaxing a protection
    #     needs the high bar, and below it the substring test wins.
    STUB_ANSWER = lambda qid, state: {"type": "choice", "choice": "preserved",
                                      "confidence": 0.62, "probabilities": {}}
    ok_b, f_b = pipeline.ground_science(REWORDED, ENTRIES, SCI, judge_cfg=ON)
    check("an unconfident 'preserved' does not overturn the strict check",
          not ok_b and f_b, f_b)

    # (c) "altered" raises a finding the substring test could never raise: the
    #     note survives verbatim, but the draft reversed it.
    INVERTED = GOOD.replace(NOTE_TEXT, NOTE_TEXT + " It is one, in effect.")
    STUB_ANSWER = lambda qid, state: {"type": "choice", "choice": "altered",
                                      "confidence": 0.55, "probabilities": {}}
    ok_c, f_c = pipeline.ground_science(INVERTED, ENTRIES, SCI, judge_cfg=ON)
    check("'altered' catches what a substring test cannot",
          not ok_c and any("changed" in x for x in f_c), f_c)
    check("the finding quotes the note so a person can find it",
          any(NOTE_TEXT[:20] in x for x in f_c), f_c)

    # (d) Below the flag threshold, an 'altered' verdict is not acted on.
    STUB_ANSWER = lambda qid, state: {"type": "choice", "choice": "altered",
                                      "confidence": 0.20, "probabilities": {}}
    ok_d, f_d = pipeline.ground_science(INVERTED, ENTRIES, SCI, judge_cfg=ON)
    check("an unconfident 'altered' is ignored", ok_d and not f_d, f_d)

    # (e) A judge that throws must not break an export.
    def boom(*a, **kw):
        raise RuntimeError("upstream is on fire")
    judge.ask = boom
    ok_e, f_e = pipeline.ground_science(REWORDED, ENTRIES, SCI, judge_cfg=ON)
    check("an exploding judge falls back to the strict check",
          (ok_e, f_e) == (ok_off, f_off), f_e)

    # (f) The per-question switch is honoured.
    judge.ask = stub_ask
    STUB_ANSWER = lambda qid, state: {"type": "choice", "choice": "preserved",
                                      "confidence": 0.99, "probabilities": {}}
    ok_f, f_f = pipeline.ground_science(REWORDED, ENTRIES, SCI,
                                        judge_cfg=dict(ON, notes=False))
    check("notes=False means the note question is never asked",
          (ok_f, f_f) == (ok_off, f_off), f_f)
finally:
    judge.ask = real_ask


# ---------------------------------------------------------------------------
print()
print("-- 5. capture kinds --")
# ---------------------------------------------------------------------------

judge.ask = stub_ask
try:
    STUB_ANSWER = lambda qid, state: {"type": "choice", "choice": "quote",
                                      "confidence": 0.97, "probabilities": {}}
    out = judge.capture_kinds(ON, [("Reading from the abstract: we demonstrate x.", True)])
    check("a confident kind comes back", out == {0: "quote"}, out)

    STUB_ANSWER = lambda qid, state: {"type": "choice", "choice": "quote",
                                      "confidence": 0.71, "probabilities": {}}
    check("an unconfident kind does not",
          judge.capture_kinds(ON, [("x y z", False)]) == {},
          judge.capture_kinds(ON, [("x y z", False)]))

    # "note" is already what the app does, so returning it would be a no-op
    # write. Nothing is changed unless the answer disagrees with the default.
    STUB_ANSWER = lambda qid, state: {"type": "choice", "choice": "note",
                                      "confidence": 1.0, "probabilities": {}}
    check("a verdict of 'note' changes nothing",
          judge.capture_kinds(ON, [("I think so.", False)]) == {})

    stub_calls.clear()
    STUB_ANSWER = lambda qid, state: {"type": "choice", "choice": "claim",
                                      "confidence": 0.95, "probabilities": {}}
    many = judge.capture_kinds(ON, [("a b c", False), ("d e f", True), ("g h i", False)])
    check("three captures cost one request, not three",
          len(stub_calls) == 1 and len(many) == 3, "%d call(s)" % len(stub_calls))
    check("whether a source is attached travels with the text",
          stub_calls[0]["state"]["captures"][1]["a_source_is_attached"] is True,
          json.dumps(stub_calls[0]["state"]["captures"][1], ensure_ascii=False))
finally:
    judge.ask = real_ask

check("capture_kinds with the judge off asks nothing",
      judge.capture_kinds(OFF, [("a", False)]) == {})
check("KIND_FALLBACK is what the app already did", judge.KIND_FALLBACK == "note")


# ---------------------------------------------------------------------------
print()
print("-- 6. config, and the key --")
# ---------------------------------------------------------------------------

check("there is a judge section in the defaults", "judge" in point_store.DEFAULT_CONFIG)
d = point_store.DEFAULT_CONFIG["judge"]
check("it is off by default", d["enabled"] is False)
check("it ships no key", d["api_key"] == "")
check("both questions default on once it is enabled",
      d["kinds"] is True and d["notes"] is True)
check("the model is left empty so judge.MODEL stays the single source",
      d["model"] == "")
check("the model judge.py pins is a version, not a moving alias",
      judge.MODEL[0].isalpha() and any(ch.isdigit() for ch in judge.MODEL), judge.MODEL)

info = point_store._judge_info()
check("state() carries the pinned model", info["model"] == judge.MODEL, info["model"])
check("state() carries the thresholds", info["thresholds"] == judge.THRESHOLDS)
check("a threshold that relaxes a protection is stricter than one that adds one",
      judge.THRESHOLDS["note_preserved_overturn"] > judge.THRESHOLDS["note_flag_min"],
      judge.THRESHOLDS)

SECRET = "ts-secret-value-that-must-never-be-echoed"
api = point_logger.Api.__new__(point_logger.Api)


class _FakeStore:
    def __init__(self):
        self.config = {"judge": dict(point_store.DEFAULT_CONFIG["judge"])}
        self.saved = 0

    def save_config(self):
        self.saved += 1

    def state(self):
        return {"config": dict(self.config), "judge_info": point_store._judge_info()}


class _FakeController:
    def refresh_full(self):
        pass


api.store = _FakeStore()
api.controller = _FakeController()
st = api.save_judge({"enabled": True, "api_key": SECRET, "kinds": False})
check("save_judge persists", api.store.saved == 1)
check("save_judge keeps the switches it was given",
      api.store.config["judge"]["kinds"] is False
      and api.store.config["judge"]["notes"] is True,
      api.store.config["judge"])
check("save_judge without a key keeps the stored one",
      (api.save_judge({"enabled": True}) is not None)
      and api.store.config["judge"]["api_key"] == SECRET)

probe = api.get_judge()
check("get_judge reports the pinned model and thresholds",
      probe["model"] == judge.MODEL and probe["thresholds"] == judge.THRESHOLDS)

# The key is allowed to be in config (same as llm/asr - the settings field has
# to render it). What must never happen is it turning up in an error string, a
# toast, or a log line, so nothing on the error paths may carry it.
err = api.test_judge.__doc__ or ""
api.store.config["judge"] = {"enabled": True, "api_key": ""}
r = api.test_judge()
check("test_judge with no key says so without quoting anything",
      "error" in r and SECRET not in json.dumps(r), r)
JUDGE_SRC = pathlib.Path(__file__).resolve().parent.parent / "trailmark" / "judge.py"
check("judge.py never logs or prints",
      "print(" not in JUDGE_SRC.read_text(encoding="utf-8")
      and "logging" not in JUDGE_SRC.read_text(encoding="utf-8"))
src = JUDGE_SRC.read_text(encoding="utf-8")
key_lines = [ln.strip() for ln in src.splitlines() if "api_key" in ln]
# Two uses, and each has to be one of exactly two safe shapes: a bool() test
# that discards the value, or the Authorization header. Anything else - a
# format string, a return, an f-string - is the key going somewhere new.
safe = [ln for ln in key_lines
        if ln.startswith("return bool(") or ln.startswith('"Authorization"')]
check("the key is only ever tested for truth or put in an Authorization header",
      len(key_lines) == 2 and len(safe) == 2, key_lines)


# ---------------------------------------------------------------------------
print()
print("-- 7. python/js contract --")
# ---------------------------------------------------------------------------

for meth in ("get_judge", "save_judge", "test_judge"):
    check("Api.%s exists" % meth, callable(getattr(point_logger.Api, meth, None)))

for eid in ("jdSw", "jdNotesSw", "jdKindsSw", "jdModel", "jdBase", "jdKey",
            "jdSave", "jdTest", "jdTestOut"):
    check("settings markup has #%s" % eid, ('id="%s"' % eid) in ui.MAIN_HTML)

import re as _re  # noqa: E402
called = set(_re.findall(r"api\.([a-z_]+)\(", ui.POPUP_HTML + ui.MAIN_HTML))
missing = sorted(m for m in called if not hasattr(point_logger.Api, m))
check("no window calls a bridge method Api lacks", not missing, missing)

check("the card is reachable from Settings and names the feature",
      ui.MAIN_HTML.count(">Second opinion</div>") == 1,
      ui.MAIN_HTML.count(">Second opinion</div>"))
check("the capture path refines kinds behind the save, not in front of it",
      "self.refine_kind(" in (JUDGE_SRC.parent.parent / "point_logger.py").read_text(encoding="utf-8")
      and "judge.in_background" in (JUDGE_SRC.parent.parent / "point_logger.py").read_text(encoding="utf-8"))

# The eval that produced the thresholds has to still be here and still be
# runnable, or the numbers above are folklore.
check("the labelled cases are committed",
      pathlib.Path("evals/judge_cases.json").exists())
check("the eval runner is committed", pathlib.Path("evals/judge_eval.py").exists())
if pathlib.Path("evals/judge_cases.json").exists():
    cases = json.loads(pathlib.Path("evals/judge_cases.json").read_text(encoding="utf-8"))
    n_notes = len(cases.get("notes") or [])
    n_kinds = len(cases.get("kinds") or [])
    check("there are enough labelled cases to mean anything",
          n_notes >= 20 and n_kinds >= 10, "notes=%d kinds=%d" % (n_notes, n_kinds))
    fa = [c for c in (cases.get("notes") or []) + (cases.get("kinds") or [])
          if c.get("lang") == "fa"]
    check("the band includes Persian, which the rules require before trusting it",
          len(fa) >= 5, "%d persian cases" % len(fa))


print()
print("ALL CHECKS PASSED" if not FAILS else "FAILED: " + ", ".join(FAILS))
sys.exit(1 if FAILS else 0)
