"""Headless tests for voicecmd.py - the spoken commands and the one draft.

No audio, no network, no store. Two halves:

1. parse/decide. Every case is a string a speech model could plausibly hand
   back, and the question is always: instruction, or words to keep? The bias
   is asymmetric - a missed command costs a repeat, a false one closes a topic
   or files half a thought - so the false-positive cases (section 2) matter
   most, and they are sentences a person would actually say.

2. Draft. Dictation and typing write into the same text from different
   threads. The merge rules are what keep a sentence said while you were
   typing from being erased by your keystroke.
"""

import pathlib
import sys
import threading

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

# Persian labels below are printed as-is; a cp1252 console would otherwise
# abort the run with UnicodeEncodeError before the Persian cases are reached.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import trailmark.voicecmd as voicecmd

FAILS = []


def check(label, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + label + (" - %s" % (detail,) if detail else ""))
    if not ok:
        FAILS.append(label)


def parsed(text):
    p = voicecmd.parse(text)
    return p["command"], p["form"], p["argument"]


# ---------------------------------------------------------------------------
# 1. Plain words, said on their own - no wake word
# ---------------------------------------------------------------------------
print("\n-- plain commands --")

for spoken, want in [
    ("log", "log"), ("Log.", "log"), ("save", "save"), ("Save!", "save"),
    ("finish", "finish"), ("finished", "finish"),
    ("session", "session"), ("tab", "tab"),
    # fillers around the word are still the word
    ("log it", "log"), ("um log", "log"), ("okay save", "save"), ("save this", "save"),
]:
    c, form, _ = parsed(spoken)
    check("%r -> %s (bare)" % (spoken, want), c == want and form == "bare", (c, form))

print("\n-- Persian --")
for spoken, want in [
    ("\u0644\u0627\u06af", "log"),                       # لاگ
    ("\u0644\u0627\u06af \u06a9\u0646", "log"),          # لاگ کن
    ("\u0627\u06cc\u0646\u0648 \u0644\u0627\u06af \u06a9\u0646", "log"),   # اینو لاگ کن
    ("\u0633\u06cc\u0648", "save"),                      # سیو
    ("\u0641\u06cc\u0646\u06cc\u0634", "finish"),        # فینیش
]:
    c, form, _ = parsed(spoken)
    check("%s -> %s (bare)" % (spoken, want), c == want and form == "bare", (c, form))

# The wake word still works, and is how a named session is forced without a
# second opinion.
print("\n-- wake word --")
for spoken, want, want_arg in [
    ("Trail-Log", "log", ""), ("trail log", "log", ""), ("traillog", "log", ""),
    ("trial log", "log", ""), ("trail lock", "log", ""),
    ("Trail-Save", "save", ""), ("trail finish", "finish", ""),
    ("Trail-Session Rust", "session", "Rust"),
    ("trail session Postgres migration", "session", "Postgres migration"),
    ("trail tab intro", "tab", "intro"),
    ("\u062a\u0631\u06cc\u0644 \u0644\u0627\u06af", "log", ""),   # تریل لاگ
]:
    c, form, a = parsed(spoken)
    check("%r -> %s %r (wake)" % (spoken, want, want_arg),
          c == want and form == "wake" and a == want_arg, (c, form, a))


# ---------------------------------------------------------------------------
# 2. Sentences that mention a command are words, not commands
# ---------------------------------------------------------------------------
print("\n-- no accidental commands --")

for sentence in [
    "the trail logs are in the folder",
    "trail log the sources for this one",
    "I want to finish the trail tomorrow",
    "log the sources",
    "save the file to disk",
    "finish the chapter first",
    # A command at the END of a sentence was measured and could not be told
    # from a list ending in the same word, so it is dictation. Say it alone.
    "that is the idea, log",
    "log log",
    "",
    "   ",
]:
    c, form, _ = parsed(sentence)
    check("%r is not a command" % sentence, c is None, (c, form))


# ---------------------------------------------------------------------------
# 3. session/tab + words: code cannot tell, so it asks - and without an answer
#    it keeps the words
# ---------------------------------------------------------------------------
print("\n-- the argument form --")

for spoken, want, want_arg in [
    ("session Rust borrow checker", "session", "Rust borrow checker"),
    ("tab open questions", "tab", "open questions"),
    ("session times were short today", "session", "times were short today"),
    ("tab completion is broken", "tab", "completion is broken"),
    ("\u0633\u0634\u0646 \u0628\u0631\u0631\u0633\u06cc \u0645\u0646\u0627\u0628\u0639", "session",
     "\u0628\u0631\u0631\u0633\u06cc \u0645\u0646\u0627\u0628\u0639"),     # سشن بررسی منابع
]:
    c, form, a = parsed(spoken)
    check("%r is a candidate, not a verdict" % spoken,
          c == want and form == "argument" and a == want_arg, (c, form, a))
    check("%r is in OPINION_FORMS" % spoken, form in voicecmd.OPINION_FORMS)

p = voicecmd.parse("session Rust")
d = voicecmd.decide(p, fallback=False)
check("no second opinion and no fallback -> the words are kept as text",
      d["action"] == "text" and d["text"] == "session Rust" and d["reason"] == "no-opinion", d)
d = voicecmd.decide(p)
check("no second opinion, short name -> the local fallback files it",
      d["action"] == "command" and d["command"] == "session" and d["argument"] == "Rust"
      and d["reason"] == "local-fallback", d)
d = voicecmd.decide(voicecmd.parse("session times were short today"))
check("no second opinion, a sentence stays text",
      d["action"] == "text" and d["reason"] == "no-opinion", d)
d = voicecmd.decide(voicecmd.parse("tab open questions"))
check("no second opinion, two-word name -> local fallback",
      d["action"] == "command" and d["argument"] == "open questions"
      and d["reason"] == "local-fallback", d)
d = voicecmd.decide(voicecmd.parse("session is tricky"))
check("a two-word rest with a verb stays text",
      d["action"] == "text" and d["reason"] == "no-opinion", d)
check("the fallback only covers three words",
      voicecmd.local_fallback(voicecmd.parse("session interview with the design team")) is None)
check("Jev still wins when it answers",
      voicecmd.decide(voicecmd.parse("tab open questions"), "text")["action"] == "text"
      and voicecmd.decide(voicecmd.parse("session times were short today"), "command")["action"] == "command")
d = voicecmd.decide(p, "text")
check("second opinion says sentence -> text", d["action"] == "text", d)
d = voicecmd.decide(p, "command")
check("second opinion says name -> command with the name",
      d["action"] == "command" and d["command"] == "session" and d["argument"] == "Rust", d)
d = voicecmd.decide(voicecmd.parse("log"), "text")
check("a certain form ignores a verdict it never asked for",
      d["action"] == "command" and d["command"] == "log", d)
d = voicecmd.decide(voicecmd.parse("the trail logs are in the folder"), "command")
check("a verdict cannot turn a non-candidate into a command", d["action"] == "text", d)
check("the certain forms are wake and bare", set(voicecmd.CERTAIN_FORMS) == {"wake", "bare"})


# ---------------------------------------------------------------------------
# 4. The grammar table Settings shows
# ---------------------------------------------------------------------------
print("\n-- grammar --")

g = voicecmd.describe_grammar()
check("five commands", [r["command"] for r in g] == ["log", "save", "finish", "session", "tab"],
      [r["command"] for r in g])
check("no row asks for the old Trail- prefix", not [r for r in g if "Trail" in r["say"]],
      [r["say"] for r in g])
check("session and tab take a name", [r["command"] for r in g if r["argument"]] == ["session", "tab"])
check("every row has a Persian form", all(r["persian"] for r in g))
check("no command removes anything",
      not [r for r in g if any(w in r["summary"].lower() for w in ("remove", "delete", "drop"))])


# ---------------------------------------------------------------------------
# 5. The draft
# ---------------------------------------------------------------------------
print("\n-- draft: appending --")

dr = voicecmd.Draft()
check("starts empty", dr.is_empty() and dr.snapshot()["rev"] == 0)
check("blank text is refused", dr.append("   ") is False and dr.is_empty())
dr.append("first sentence")
dr.append("second sentence")
s = dr.snapshot()
check("dictation joins with one space", s["text"] == "first sentence second sentence", s["text"])
check("origin is voice", s["origin"] == "voice", s["origin"])
check("words counted", s["words"] == 4, s["words"])

print("\n-- draft: typing and dictation at once --")

# The window read rev r, the user edited, and a sentence arrived before the
# edit was sent. The edit must not erase the sentence.
r0 = dr.snapshot()["rev"]
dr.append("said while typing")
res = dr.set_text("First sentence, corrected. Second sentence", r0)
check("a stale edit merges instead of failing", res["ok"] and res["merged"], res)
check("the edit wins AND the new sentence survives, after it",
      res["text"] == "First sentence, corrected. Second sentence said while typing", res["text"])
check("an edited draft is the hand's", res["origin"] == "hand", res["origin"])

# Up to date: a plain set.
res = dr.set_text("replaced entirely", res["rev"])
check("a current edit is a plain set", res["ok"] and not res["merged"] and res["text"] == "replaced entirely", res)

# Setting over a set the window never saw is refused - both are edits of the
# same text and neither can be merged onto the other.
r1 = dr.snapshot()["rev"]
dr.set_text("someone else's edit", r1)
res = dr.set_text("my edit", r1)
check("an edit over an unseen edit is refused as stale", not res["ok"] and res["reason"] == "stale", res)
check("and the refusal carries what to show", res["text"] == "someone else's edit", res["text"])
check("a rev from the future is stale", dr.set_text("x", 10 ** 6)["reason"] == "stale")

print("\n-- draft: logged while you typed --")

dr = voicecmd.Draft()
dr.append("the point being dictated")
r0 = dr.snapshot()["rev"]
taken = dr.take()
check("take returns the text", taken["text"] == "the point being dictated", taken)
check("take empties the draft", dr.is_empty())
# The window had typed onto the end of what was just filed.
res = dr.set_text("the point being dictated and a new thought", r0)
check("text typed onto the END of a filed draft is kept", res["ok"] and res["text"] == "and a new thought", res)
# An edit in the MIDDLE of filed text cannot be kept - it was already filed.
dr2 = voicecmd.Draft()
dr2.append("alpha beta")
r0 = dr2.snapshot()["rev"]
dr2.take()
res = dr2.set_text("alpha GAMMA beta", r0)
check("an edit inside filed text is refused as logged", not res["ok"] and res["reason"] == "logged", res)
check("and nothing is resurrected", dr2.is_empty())

print("\n-- draft: take and restore --")

dr = voicecmd.Draft()
dr.append("keep me")
dr.add_source("link", "https://example.org/a")
dr.set_meta({"topic_id": "t1", "subtopic": "intro", "kind": "quote"})
taken = dr.take()
check("take carries sources with their values", taken["sources"][0]["value"] == "https://example.org/a", taken)
check("take carries where it goes", taken["meta"] == {"topic_id": "t1", "subtopic": "intro", "kind": "quote"}, taken["meta"])
check("after take, the destination stays and the kind resets",
      dr.meta() == {"topic_id": "t1", "subtopic": "intro", "kind": ""}, dr.meta())
dr.append("arrived during the failed write")
dr.restore(taken)
s = dr.snapshot()
check("restore puts the text back, BEFORE what arrived meanwhile",
      s["text"] == "keep me arrived during the failed write", s["text"])
check("restore puts the sources back", s["count_sources"] == 1 and s["sources"][0]["value"] == "https://example.org/a", s["sources"])
check("restore puts the kind back", s["meta"]["kind"] == "quote", s["meta"])
check("an edit over a restore is stale, not merged",
      dr.set_text("x", taken["rev"])["reason"] == "stale")

print("\n-- draft: sources --")

dr = voicecmd.Draft()
a = dr.add_source("link", "https://example.org/x")
check("a source gets an id", a > 0, a)
check("the same link twice is not cited twice", dr.add_source("link", "https://example.org/x") == 0)
i1 = dr.add_source("image", "data:image/png;base64,AAAA")
i2 = dr.add_source("image", "data:image/png;base64,AAAA")
check("images are never deduplicated", i1 and i2 and i1 != i2, (i1, i2))
check("an unknown type is refused", dr.add_source("file", "C:/x") == 0)
check("an empty value is refused", dr.add_source("link", "  ") == 0)
s = dr.snapshot()
check("the snapshot never carries image data",
      all(x["value"] == "" for x in s["sources"] if x["type"] == "image"), s["sources"])
check("take does carry the image data",
      [x["value"] for x in voicecmd.Draft.take(dr)["sources"] if x["type"] == "image"][0].startswith("data:"))
dr = voicecmd.Draft()
a = dr.add_source("link", "https://example.org/1")
b = dr.add_source("link", "https://example.org/2")
dr.drop_source(a)
check("drop by id removes that one", [x["id"] for x in dr.snapshot()["sources"]] == [b])
check("a stale id is a no-op, not a crash", dr.drop_source(a)["ok"] is False)

print("\n-- draft: meta --")

dr = voicecmd.Draft()
dr.set_meta({"kind": "gossip", "topic_id": "t", "evil": "x"})
check("an unknown kind is refused", dr.meta()["kind"] == "", dr.meta())
check("an unknown key is ignored", "evil" not in dr.meta(), dr.meta())
check("a known key is kept", dr.meta()["topic_id"] == "t")

print("\n-- draft: limits --")

dr = voicecmd.Draft()
check("an append past MAX_CHARS is refused, not trimmed",
      dr.append("x" * (voicecmd.Draft.MAX_CHARS + 1)) is False and dr.is_empty())
check("a set past MAX_CHARS is refused",
      dr.set_text("x" * (voicecmd.Draft.MAX_CHARS + 1), 0)["reason"] == "too long")
for i in range(voicecmd.Draft.MAX_SOURCES + 5):
    dr.add_source("link", "https://example.org/%d" % i)
check("sources capped", dr.snapshot()["count_sources"] == voicecmd.Draft.MAX_SOURCES)

# Four real threads: utterance threads, the hotkey thread and the JS bridge
# all reach the draft.
print("\n-- draft: threads --")

dr = voicecmd.Draft()
errors = []


def _hammer(n):
    try:
        for i in range(150):
            dr.append("t%d-%d" % (n, i))
            dr.add_source("link", "https://example.org/%d-%d" % (n, i))
            s = dr.snapshot()
            dr.set_text(s["text"] + " edit", s["rev"])
            if i % 50 == 49:
                dr.restore(dr.take())
    except Exception as e:          # pragma: no cover - a failure is the point
        errors.append(repr(e))


threads = [threading.Thread(target=_hammer, args=(n,)) for n in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join()
check("concurrent writers raise nothing", not errors, errors[:3])
s = dr.snapshot()
check("every dictated piece survived the concurrent edits",
      all(("t%d-149" % n) in s["text"] for n in range(4)), s["words"])
check("revisions only go up", s["rev"] > 0)


print()
print("ALL CHECKS PASSED" if not FAILS else "FAILED: " + ", ".join(FAILS))
sys.exit(1 if FAILS else 0)
