"""Headless tests for voicecmd.py - the spoken command grammar and buffer.

No audio, no network, no store. Every case here is a string that a speech
model could plausibly hand back, and the question is always the same one:
instruction, or comment?

The bias under test is asymmetric. A missed command costs a repeat; a false
command closes a topic or logs half a thought. So the false-positive cases
below (section 2) are the ones that matter most, and they are deliberately
the sentences a person would actually say while using Trailmark.
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

import voicecmd  # noqa: E402

FAILS = []


def check(label, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + label + (" - %s" % (detail,) if detail else ""))
    if not ok:
        FAILS.append(label)


def cmd(text):
    return voicecmd.match(text)["command"]


def arg(text):
    return voicecmd.match(text)["argument"]


# ---------------------------------------------------------------------------
# 1. The five commands, said cleanly
# ---------------------------------------------------------------------------
print("\n-- clean commands --")

for spoken, want in [
    ("Trail-Save", "save"),
    ("Trail-Log", "log"),
    ("Trail-Finish", "finish"),
    ("Trail-Session", "session"),
    ("Trail-Tab", "tab"),
]:
    check("%r -> %s" % (spoken, want), cmd(spoken) == want, cmd(spoken))

# The hyphen is how it is written; the space is how ASR returns it.
for spoken, want in [("trail save", "save"), ("trail log", "log"),
                     ("trail finish", "finish"), ("trail session", "session"),
                     ("trail tab", "tab")]:
    check("%r -> %s" % (spoken, want), cmd(spoken) == want, cmd(spoken))

# Case and trailing punctuation are the transcriber's, not the speaker's.
check("'TRAIL LOG.' -> log", cmd("TRAIL LOG.") == "log", cmd("TRAIL LOG."))
check("'Trail, save!' -> save", cmd("Trail, save!") == "save", cmd("Trail, save!"))


# ---------------------------------------------------------------------------
# 2. FALSE POSITIVES - the cases that cost real work
# ---------------------------------------------------------------------------
print("\n-- must NOT fire --")

for spoken in [
    "the trail logs are in the folder",
    "trail log the sources for this one",          # log takes no argument
    "I need to finish the trail before dark",
    "we should save the trail data somewhere",
    "this is the trail marking system",
    "trailing whitespace broke the parser",
    "her session on the trail was long",
    "open a new tab in the browser",               # no wake word
    "save this",                                   # no wake word
    "finish",                                      # no wake word
    "log",                                         # no wake word
    "session",                                     # no wake word
    "",                                            # silence
    "   ",
    "trail",                                       # wake word with no verb
    "trail something else entirely",               # wake word, unknown verb
]:
    check("%r stays a comment" % spoken, cmd(spoken) is None, cmd(spoken))


# ---------------------------------------------------------------------------
# 3. ASR mangling - what the model really returns
# ---------------------------------------------------------------------------
print("\n-- mangled but intended --")

for spoken, want in [
    ("trials save", "save"),        # plural wake word
    ("trial save", "save"),         # the classic trail/trial transposition
    ("trail safe", "save"),         # save/safe
    ("trail lock", "log"),          # log/lock
    ("trail logged", "log"),
    ("trail finished", "finish"),
    ("trail finnish", "finish"),
    ("trail sessions", "session"),
    ("trail tap", "tab"),           # tab/tap
    ("traillog", "log"),            # the space was dropped entirely
    ("trailsave", "save"),
    ("trailfinish", "finish"),
]:
    got = cmd(spoken)
    check("%r -> %s" % (spoken, want), got == want, got)

# Filler around a bare command is ignored.
for spoken, want in [("ok trail log", "log"), ("trail log please", "log"),
                     ("hey trail finish", "finish"), ("so, trail save, now", "save"),
                     ("alright trail log then", "log")]:
    got = cmd(spoken)
    check("%r -> %s" % (spoken, want), got == want, got)


# ---------------------------------------------------------------------------
# 4. Arguments - the two commands that name something
# ---------------------------------------------------------------------------
print("\n-- arguments --")

check("session argument kept verbatim",
      arg("Trail-Session Rust borrow checker") == "Rust borrow checker",
      arg("Trail-Session Rust borrow checker"))
check("session keeps capitals",
      arg("trail session Postgres Migration") == "Postgres Migration",
      arg("trail session Postgres Migration"))
check("tab argument",
      arg("Trail-Tab open questions") == "open questions",
      arg("Trail-Tab open questions"))
check("no argument is empty, not None",
      arg("trail session") == "", repr(arg("trail session")))

# A hyphen inside the ARGUMENT must survive - normalisation splits hyphens,
# so this is the case that catches a naive token-count slice.
check("hyphenated argument word survives",
      arg("trail tab borrow-checker") == "borrow-checker",
      arg("trail tab borrow-checker"))
check("hyphenated argument among others",
      arg("Trail-Session lock-free queues in Rust") == "lock-free queues in Rust",
      arg("Trail-Session lock-free queues in Rust"))

# Leading filler must not eat the first word of the argument.
check("leading filler does not shift the argument",
      arg("ok trail session Rust borrow checker") == "Rust borrow checker",
      arg("ok trail session Rust borrow checker"))
# Trailing filler must not be taken as the argument.
check("trailing filler dropped from the argument",
      arg("trail session Rust please") == "Rust",
      arg("trail session Rust please"))
check("trailing sentence punctuation dropped",
      arg("Trail-Tab open questions.") == "open questions",
      arg("Trail-Tab open questions."))
# A joined wake+verb still finds its argument.
check("joined command keeps its argument",
      arg("trailsession Rust borrow checker") == "Rust borrow checker",
      arg("trailsession Rust borrow checker"))

# A no-argument command with trailing words is a SENTENCE, not a command with
# an ignored argument. This is the rule that keeps "trail log the sources"
# from silently logging.
check("'trail save the link' is not a command",
      cmd("trail save the link") is None, cmd("trail save the link"))


# ---------------------------------------------------------------------------
# 5. Persian - the wake word and verbs in Persian script, and Persian arguments
# ---------------------------------------------------------------------------
print("\n-- persian --")

check("persian wake + persian verb (تریل لاگ)",
      cmd("تریل لاگ") == "log",
      cmd("تریل لاگ"))
check("persian wake + latin verb (تریل log)",
      cmd("تریل log") == "log",
      cmd("تریل log"))
check("latin wake + persian verb (trail سیو)",
      cmd("trail سیو") == "save",
      cmd("trail سیو"))
# Arabic yeh vs Farsi yeh: the same word, two code points, one must fold.
check("arabic-yeh spelling of the wake word folds",
      cmd("تريل لاگ") == "log",
      cmd("تريل لاگ"))
# A Persian argument must come back intact, RTL text and all.
persian_arg = "بررسی بازار"  # بررسی بازار
check("persian argument preserved",
      arg("trail session " + persian_arg) == persian_arg,
      arg("trail session " + persian_arg))
# Persian comma as trailing punctuation.
check("persian comma stripped from the argument",
      arg("trail tab " + persian_arg + "،") == persian_arg,
      arg("trail tab " + persian_arg + "،"))
# Persian digits fold to ASCII so a numbered tab is usable.
check("persian digits fold in normalise",
      voicecmd.normalise("۲۳") == ["23"],
      voicecmd.normalise("۲۳"))
# A Persian sentence that happens to be a comment must stay a comment.
check("persian sentence stays a comment",
      cmd("این یک نکته است") is None,
      cmd("این یک نکته است"))


# ---------------------------------------------------------------------------
# 6. The grammar description used by Settings
# ---------------------------------------------------------------------------
print("\n-- describe_grammar --")

g = voicecmd.describe_grammar()
check("describes all five commands", len(g) == 5, len(g))
check("every row has say/summary",
      all(r.get("say") and r.get("summary") for r in g), g)
check("session and tab are the two that take an argument",
      sorted(r["command"] for r in g if r["argument"]) == ["session", "tab"],
      [r["command"] for r in g if r["argument"]])


# ---------------------------------------------------------------------------
# 7. VoiceBuffer
# ---------------------------------------------------------------------------
print("\n-- buffer --")

b = voicecmd.VoiceBuffer()
check("starts empty", b.is_empty())
check("blank comment rejected", b.add_comment("   ") is False)
check("comment accepted", b.add_comment("first thought") is True)
b.add_comment("second thought")
b.add_source("link", "https://example.org/a")
check("duplicate link rejected", b.add_source("link", "https://example.org/a") is False)
check("distinct link accepted", b.add_source("link", "https://example.org/b") is True)
check("bad source type rejected", b.add_source("video", "x") is False)
check("empty source value rejected", b.add_source("link", "  ") is False)

snap = b.snapshot()
check("snapshot counts comments", snap["count_comments"] == 2, snap["count_comments"])
check("snapshot counts sources", snap["count_sources"] == 2, snap["count_sources"])
check("snapshot joins text", snap["text"] == "first thought second thought", snap["text"])
check("snapshot not empty", snap["empty"] is False)
check("snapshot does not drain", b.is_empty() is False)

# Two images that differ must both survive - deduplication is for links and
# strings only, because two screenshots are two pieces of evidence.
b.add_source("image", "data:image/png;base64,AAAA")
check("identical image is NOT deduplicated",
      b.add_source("image", "data:image/png;base64,AAAA") is True)

took = b.take()
check("take returns the contents", took["count_comments"] == 2, took["count_comments"])
check("take drains", b.is_empty() is True)
check("take twice is empty the second time", b.take()["empty"] is True)

# Mutating what snapshot() handed back must not reach inside the buffer.
b2 = voicecmd.VoiceBuffer()
b2.add_comment("keep me")
s2 = b2.snapshot()
s2["comments"].append("injected")
s2["sources"].append({"type": "link", "value": "nope"})
check("snapshot lists are copies", b2.snapshot()["count_comments"] == 1,
      b2.snapshot()["count_comments"])

# The cap keeps a forgotten session from growing without bound.
b3 = voicecmd.VoiceBuffer()
for i in range(voicecmd.VoiceBuffer.MAX_COMMENTS + 25):
    b3.add_comment("c%d" % i)
snap3 = b3.snapshot()
check("comments capped at MAX_COMMENTS",
      snap3["count_comments"] == voicecmd.VoiceBuffer.MAX_COMMENTS,
      snap3["count_comments"])
check("the cap drops OLDEST, keeps newest",
      snap3["comments"][-1] == "c%d" % (voicecmd.VoiceBuffer.MAX_COMMENTS + 24),
      snap3["comments"][-1])

# Three real threads write while one reads: the buffer is touched from the
# audio thread, the Win32 hotkey thread and the JS-bridge thread.
b4 = voicecmd.VoiceBuffer()
errors = []


def _hammer(n):
    try:
        for i in range(200):
            b4.add_comment("t%d-%d" % (n, i))
            b4.add_source("link", "https://example.org/%d-%d" % (n, i))
            b4.snapshot()
    except Exception as e:          # pragma: no cover - a failure is the point
        errors.append(repr(e))


threads = [threading.Thread(target=_hammer, args=(n,)) for n in range(3)]
for t in threads:
    t.start()
for t in threads:
    t.join()
check("concurrent writers raise nothing", not errors, errors)
final = b4.snapshot()
check("concurrent writes land within the caps",
      final["count_comments"] == voicecmd.VoiceBuffer.MAX_COMMENTS
      and final["count_sources"] == voicecmd.VoiceBuffer.MAX_SOURCES,
      (final["count_comments"], final["count_sources"]))


print()
print("ALL CHECKS PASSED" if not FAILS else "FAILED: " + ", ".join(FAILS))
sys.exit(1 if FAILS else 0)
