"""Headless tests for always-on voice: utterance -> speaker check -> transcript
-> command or draft -> store.

Drives the Controller against a real Store rooted in a temp directory. No
microphone, no transcription call, no speaker model, no windows: transcription
and the Jev second opinion are replaced with fakes that record their calls,
the verifier with one that tells voices apart by loudness, and the pywebview
surfaces are absent, which push_voice_state must tolerate.

The contract being pinned is the owner's:

    dictation and typing   -> ONE draft; neither overwrites the other
    log / save / finish    -> said on their own, no wake word
    session NAME, tab NAME -> a second opinion decides; without one, text
    another voice          -> held aside, not transcribed, recoverable
    removes                -> by hand only
"""

import json
import pathlib
import struct
import sys
import tempfile
import threading
import time
import wave
import io

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

FAILS = []


def check(label, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + label + (" - %s" % (detail,) if detail else ""))
    if not ok:
        FAILS.append(label)


# Temp data dir before point_logger reads the store's module-level paths.
import trailmark.point_store as ps # noqa: E402

tmp = pathlib.Path(tempfile.mkdtemp(prefix="opl_voice_"))
ps.BASE_DIR = tmp
ps.DATA_FILE = tmp / "points.json"
ps.CONFIG_FILE = tmp / "config.json"
ps.ATTACH_DIR = tmp / "attachments"
ps.EXPORT_DIR = tmp / "exports"

import point_logger as point_logger
import trailmark.clipboard as clipboard
import trailmark.voicecmd as voicecmd

c = point_logger.Controller()
api = point_logger.Api(c.store, c)

# Every push, so the UI contract is testable too.
pushes = []
_orig_push = c.push_voice_state


def _record(state, detail=""):
    pushes.append((state, detail))
    return _orig_push(state, detail)


c.push_voice_state = _record
c.refresh_full = lambda: None
# Never the real data folder's model: a missing model is a case under test.
c.models_dir = lambda: tmp / "models"

# A controllable clipboard: "save" must never touch the real one.
CLIP = {"type": "none", "value": None, "meta": {}}
clipboard.read = lambda: dict(CLIP)

# The second opinion. None = unconfigured (the real function, no key).
_real_intents = point_logger.judge.command_intents
VERDICT = {"v": None, "calls": []}


def _intents(cfg, candidates):
    VERDICT["calls"].append([dict(p) for p in candidates])
    if VERDICT["v"] is None:
        return _real_intents(cfg, candidates)
    return {0: VERDICT["v"]}


point_logger.judge.command_intents = _intents

# Transcription: a WAV maps to the words "said" in it. Every call is counted,
# because "another voice is never sent anywhere" is a claim about calls.
SAID = {}
SENT = []


def _transcribe(cfg, wav_bytes):
    SENT.append(wav_bytes)
    if wav_bytes not in SAID:
        return {"error": "unmapped clip"}
    return {"text": SAID[wav_bytes], "language": "en"}


point_logger.asr.transcribe = _transcribe


def entries_of(tid):
    return (c.store.find_topic(tid) or {}).get("entries", [])


def open_topic():
    return c._open_topic()


def draft():
    return c.draft.snapshot()


def say(text):
    return c.on_voice_transcript(text)


# ---------------------------------------------------------------------------
# 1. No topic: commands report, dictation is still kept
# ---------------------------------------------------------------------------
print("\n-- no open topic --")

check("no topic to start with", open_topic() is None)
r = c.run_voice_command("log")
check("log on an empty draft errors", r.get("error") == "Nothing to log yet.", r)
say("an early thought about lifetimes")
check("dictation lands in the draft with no topic",
      draft()["text"] == "an early thought about lifetimes", draft()["text"])
r = c.run_voice_command("log")
check("log with no topic errors and says how to start one",
      "session" in (r.get("error") or ""), r)
check("the refused draft is put back, not lost",
      draft()["text"] == "an early thought about lifetimes", draft()["text"])
check("tab with no topic errors", bool(c.run_voice_command("tab", "intro").get("error")))
check("finish with no topic errors", bool(c.run_voice_command("finish").get("error")))
check("no topic was invented", open_topic() is None)


# ---------------------------------------------------------------------------
# 2. A session, said with the wake word, carries the draft into it
# ---------------------------------------------------------------------------
print("\n-- session --")

d = say("Trail-Session Rust borrow checker")
check("the wake form is a command without asking anyone",
      d["action"] == "command" and not VERDICT["calls"], (d, VERDICT["calls"]))
t = open_topic()
check("topic took the spoken title", t and t["title"] == "Rust borrow checker", (t or {}).get("title"))
tid = t["id"]
check("the draft now files into it", draft()["meta"]["topic_id"] == tid, draft()["meta"])
check("the early thought carried over, unfiled",
      draft()["text"] == "an early thought about lifetimes" and not entries_of(tid))
check("a push named the session", pushes[-1] == ("session", "Rust borrow checker"), pushes[-1])


# ---------------------------------------------------------------------------
# 3. Talking appends; nothing is filed until "log"
# ---------------------------------------------------------------------------
print("\n-- talking --")

say("the borrow checker rejects this because the lifetime is too short")
check("dictation appends to the same draft",
      draft()["text"] == "an early thought about lifetimes the borrow checker rejects "
                         "this because the lifetime is too short", draft()["text"])
check("NOTHING was filed", not entries_of(tid))
check("a push reported it was heard", pushes[-1][0] == "heard", pushes[-1])
check("the bar shows what was heard last", c.voice_heard.startswith("the borrow"), c.voice_heard)
n = len(pushes)
say("")
say("   ")
check("blank transcripts add nothing", draft()["words"] == 16, draft()["words"])
check("and push no 'heard'", not [p for p in pushes[n:] if p[0] == "heard"], pushes[n:])


# ---------------------------------------------------------------------------
# 4. "save" attaches the clipboard to the draft
# ---------------------------------------------------------------------------
print("\n-- save --")

CLIP.update({"type": "link", "value": "https://doc.rust-lang.org/nomicon/"})
say("save")
s = draft()
check("the link is attached as a source", s["count_sources"] == 1
      and s["sources"][0]["value"] == "https://doc.rust-lang.org/nomicon/", s["sources"])
check("attached by voice", s["sources"][0].get("origin") == "voice", s["sources"][0])
check("nothing filed", not entries_of(tid))
say("Save.")
check("the same clipboard twice is not cited twice", draft()["count_sources"] == 1)
check("a duplicate is reported, not silent", pushes[-1][0] == "duplicate", pushes[-1])
CLIP.update({"type": "text", "value": "Jung, Ralf et al. RustBelt (2018)"})
c.run_voice_command("save", "", via="hotkey")
s = draft()
check("clipboard text becomes a string source",
      s["count_sources"] == 2 and s["sources"][1]["type"] == "string", s["sources"])
CLIP.update({"type": "none", "value": None})
r = c.run_voice_command("save")
check("an empty clipboard errors", r.get("error") == "Clipboard is empty.", r)
check("and adds no blank source", draft()["count_sources"] == 2)
# Persian command word, same effect.
CLIP.update({"type": "link", "value": "https://example.org/fa"})
say("سیو")                                  # سیو
check("the Persian word for save attaches too", draft()["count_sources"] == 3, draft()["count_sources"])


# ---------------------------------------------------------------------------
# 5. "log" files text AND sources as one point
# ---------------------------------------------------------------------------
print("\n-- log --")

say("log")
ents = entries_of(tid)
check("exactly one entry", len(ents) == 1, len(ents))
e = ents[0]
check("the entry is the whole draft",
      e["text"].startswith("an early thought") and e["text"].endswith("too short"), e["text"])
check("with all three sources", len(e["sources"]) == 3, e["sources"])
check("a dictated point is a note", e["kind"] == "note", e["kind"])
check("the draft is empty after filing", c.draft.is_empty(), draft())
check("but still points at the topic", draft()["meta"]["topic_id"] == tid, draft()["meta"])
check("a push says it was logged", pushes[-1][0] == "logged", pushes[-1])
r = c.run_voice_command("log")
check("log on an empty draft errors", bool(r.get("error")) and len(entries_of(tid)) == 1, r)
CLIP.update({"type": "link", "value": "https://example.org/orphan"})
say("save")
r = c.run_voice_command("log")
check("sources with no text are refused", "no text" in (r.get("error") or ""), r)
check("and the source is kept", draft()["count_sources"] == 1, draft())
api.draft_clear()


# ---------------------------------------------------------------------------
# 6. Tabs
# ---------------------------------------------------------------------------
print("\n-- tab --")

say("trail tab intro")
check("the wake form adds a tab", "intro" in open_topic()["subtopics"], open_topic()["subtopics"])
check("and the draft files under it", draft()["meta"]["subtopic"] == "intro", draft()["meta"])
say("the intro needs a diagram")
say("log")
check("the point landed under the tab", entries_of(tid)[-1]["subtopic"] == "intro",
      entries_of(tid)[-1].get("subtopic"))
say("tab")
subs = open_topic()["subtopics"]
check("an unnamed tab is numbered", subs[-1] == "Tab 2", subs)
say("tab")
check("a second unnamed tab does not collide", open_topic()["subtopics"][-1] == "Tab 3",
      open_topic()["subtopics"])
r = c.run_voice_command("tab", "intro")
check("naming a tab that exists switches back to it",
      r.get("detail") == "Back to intro" and open_topic()["subtopics"].count("intro") == 1, r)


# ---------------------------------------------------------------------------
# 7. "session/tab + words": a second opinion, or text
# ---------------------------------------------------------------------------
print("\n-- the second opinion --")

VERDICT["v"] = None
VERDICT["calls"].clear()
n = len(pushes)
d = say("tab open questions")
check("unconfigured: the question was still asked", len(VERDICT["calls"]) == 1, VERDICT["calls"])
check("the bar said it was deciding", ("deciding", "tab open questions") in pushes[n:], pushes[n:])
check("unconfigured: kept as text", d["action"] == "text" and d["reason"] == "no-opinion", d)
check("the words are in the draft", draft()["text"] == "tab open questions", draft()["text"])
check("no tab was made", "open questions" not in open_topic()["subtopics"])
check("the push says why, and how to force it",
      pushes[-1][0] == "heard" and 'trail tab' in pushes[-1][1], pushes[-1])
api.draft_clear()

VERDICT["v"] = "command"
VERDICT["calls"].clear()
d = say("tab open questions")
check("the candidate sent is the parsed command",
      VERDICT["calls"] and VERDICT["calls"][0][0]["command"] == "tab"
      and VERDICT["calls"][0][0]["argument"] == "open questions", VERDICT["calls"])
check("'a name' -> the tab is made", "open questions" in open_topic()["subtopics"], d)
check("nothing went into the draft", c.draft.is_empty(), draft())

VERDICT["v"] = "text"
d = say("tab completion is broken")
check("'a sentence' -> text", d["action"] == "text" and draft()["text"] == "tab completion is broken", d)
check("no tab 'completion is broken'", "completion is broken" not in open_topic()["subtopics"])
VERDICT["calls"].clear()
say("log")
check("a certain command never asks", not VERDICT["calls"], VERDICT["calls"])
check("filed under the tab the second opinion made",
      entries_of(tid)[-1]["subtopic"] == "open questions", entries_of(tid)[-1].get("subtopic"))
VERDICT["v"] = None


# ---------------------------------------------------------------------------
# 8. A new session files the leftover draft into the OLD topic first
# ---------------------------------------------------------------------------
print("\n-- session hand-off --")

before = len(entries_of(tid))
say("one last thought about lifetimes")
say("trail session Postgres migration")
old = entries_of(tid)
check("the leftover landed in the OLD topic",
      len(old) == before + 1 and old[-1]["text"] == "one last thought about lifetimes",
      [x["text"] for x in old[before:]])
new_t = open_topic()
check("the new topic is the open one", new_t["title"] == "Postgres migration", new_t["title"])
check("it starts empty", not new_t["entries"])
check("the draft points at it, with no tab", draft()["meta"] == {"topic_id": new_t["id"], "subtopic": "", "kind": ""},
      draft()["meta"])
new_tid = new_t["id"]
say("session")
unnamed = open_topic()
check("an unnamed session gets a dated title", unnamed["title"].startswith("Session 20"), unnamed["title"])
c.store.close_topic(unnamed["id"])


# ---------------------------------------------------------------------------
# 9. finish files what is pending, then closes - or stays open
# ---------------------------------------------------------------------------
print("\n-- finish --")

c.draft.set_meta({"topic_id": new_tid, "subtopic": ""})
say("indexes rebuilt in about four minutes")
r = c.run_voice_command("finish")
t = c.store.find_topic(new_tid)
check("finish succeeds", not r.get("error"), r)
check("the topic is closed", t["status"] == "closed", t["status"])
check("the pending sentence was filed first",
      len(t["entries"]) == 1 and "four minutes" in t["entries"][0]["text"], t["entries"])
check("the draft forgets the closed topic", draft()["meta"]["topic_id"] == "", draft()["meta"])
check("context falls back to the previous open topic", open_topic()["id"] == tid, open_topic()["title"])

say("trail session Voice parity")
vid = open_topic()["id"]
say("this must not be lost")
_real_add = c.store.add_entry
c.store.add_entry = lambda *a, **k: {"error": "disk full"}
r = c.run_voice_command("finish")
c.store.add_entry = _real_add
check("a failed filing refuses to finish", (r.get("error") or "").startswith("Not finished"), r)
check("the topic stays open", c.store.find_topic(vid)["status"] == "open")
check("the words are still in the draft", draft()["text"] == "this must not be lost", draft()["text"])
api.draft_clear()


# ---------------------------------------------------------------------------
# 10. Spoken, pressed and clicked reach the same code
# ---------------------------------------------------------------------------
print("\n-- spoken == pressed == clicked --")

say("first")
say("Trail-Log")
check("spoken wake-form log filed", len(entries_of(vid)) == 1, len(entries_of(vid)))
say("second")
c.run_voice_command("log", "", via="hotkey")
check("pressed log filed", len(entries_of(vid)) == 2, len(entries_of(vid)))
say("third")
api.voice_command("log")
check("clicked log filed", len(entries_of(vid)) == 3, len(entries_of(vid)))
say("fourth")
say("لاگ کن")                  # لاگ کن
check("Persian log filed", len(entries_of(vid)) == 4, len(entries_of(vid)))


# ---------------------------------------------------------------------------
# 11. A sentence that mentions a command does not run it
# ---------------------------------------------------------------------------
print("\n-- no accidental commands --")

before = len(entries_of(vid))
subs_before = list(open_topic()["subtopics"])
for sentence in ["the trail logs are in the folder",
                 "trail log the sources for this one",
                 "I want to finish the trail tomorrow",
                 "that is the idea, log",
                 "save the file to disk"]:
    say(sentence)
check("none of them filed anything", len(entries_of(vid)) == before)
check("none of them added a tab", open_topic()["subtopics"] == subs_before)
check("the topic is still open", open_topic()["id"] == vid)
check("all five are in the draft, in order",
      draft()["text"].startswith("the trail logs") and draft()["text"].endswith("to disk"), draft()["text"])
api.draft_clear()


# ---------------------------------------------------------------------------
# 12. The switches
# ---------------------------------------------------------------------------
print("\n-- always_on off, commands off --")

c.store.config["voice"]["always_on"] = False
before = len(entries_of(vid))
say("dictated straight in")
check("always_on off: every utterance is filed at once", len(entries_of(vid)) == before + 1)
check("and the draft is untouched", c.draft.is_empty())
say("log")
check("a command word is just text in that mode", entries_of(vid)[-1]["text"] == "log")
c.store.config["voice"]["always_on"] = True

c.store.config["voice"]["commands"] = False
say("log")
check("commands off: the word goes into the draft", draft()["text"] == "log", draft()["text"])
c.store.config["voice"]["commands"] = True
api.draft_clear()


# ---------------------------------------------------------------------------
# 13. Typing and dictation into the same draft, through the bridge
# ---------------------------------------------------------------------------
print("\n-- hand and voice together --")

say("dictated first")
seen = api.draft_get()["draft"]
say("dictated while the user typed")         # arrives before the edit is sent
out = api.draft_set("Dictated first, fixed by hand.", seen["rev"])
check("the edit merged rather than overwrote",
      out["result"]["ok"] is True and out["result"]["merged"] is True, out["result"])
check("both survive, edit first",
      out["draft"]["text"] == "Dictated first, fixed by hand. dictated while the user typed",
      out["draft"]["text"])
check("the push says merged", pushes[-1][0] == "merged", pushes[-1])
out = api.draft_log(None, None)
check("the Log button files it", out["result"]["state"] == "logged" and not out.get("error"), out.get("result"))
check("a draft the hand touched files as a claim", entries_of(vid)[-1]["kind"] == "claim",
      entries_of(vid)[-1]["kind"])

# Logged while the page still showed the text, then more typed onto its end.
say("filed from under the typist")
seen = api.draft_get()["draft"]
c.run_voice_command("log", "", via="hotkey")
out = api.draft_set("filed from under the typist and then more", seen["rev"])
check("text typed onto a filed draft keeps only the new part",
      out["result"]["ok"] and out["draft"]["text"] == "and then more", out["draft"]["text"])
api.draft_clear()

# The page sends its last keystrokes with the press.
seen = api.draft_get()["draft"]
out = api.draft_log("typed and logged in one go", seen["rev"])
check("draft_log settles unsent text, then files it",
      entries_of(vid)[-1]["text"] == "typed and logged in one go" and out["result"]["state"] == "logged",
      entries_of(vid)[-1]["text"])
check("a typed-only point is a claim", entries_of(vid)[-1]["kind"] == "claim")
say("stale edit target")
seen = api.draft_get()["draft"]
api.draft_set("someone else's edit", seen["rev"])
out = api.draft_log("my edit", seen["rev"])
check("a stale press is refused with a reason, nothing filed",
      out.get("error") and entries_of(vid)[-1]["text"] == "typed and logged in one go", out.get("error"))
api.draft_clear()

# Kind and destination chosen in the popup.
api.draft_meta({"kind": "quote"})
api.draft_set("A quoted sentence.", api.draft_get()["draft"]["rev"])
api.draft_log()
check("an explicit kind is kept", entries_of(vid)[-1]["kind"] == "quote", entries_of(vid)[-1]["kind"])
api.draft_meta({"topic_id": tid, "subtopic": "intro"})
say("back in the first topic")
say("log")
check("the draft files into the topic chosen, not the newest",
      entries_of(tid)[-1]["text"] == "back in the first topic"
      and entries_of(tid)[-1]["subtopic"] == "intro", entries_of(tid)[-1])
c.store.close_topic(tid)
say("its topic was closed meanwhile")
say("log")
check("a closed target falls back to the newest open topic, without its tab",
      entries_of(vid)[-1]["text"] == "its topic was closed meanwhile"
      and entries_of(vid)[-1]["subtopic"] == "", entries_of(vid)[-1])
c.draft.set_meta({"topic_id": vid, "subtopic": ""})


# ---------------------------------------------------------------------------
# 14. Removes are by hand
# ---------------------------------------------------------------------------
print("\n-- hand removes --")

CLIP.update({"type": "link", "value": "https://example.org/keep"})
say("save")
CLIP.update({"type": "link", "value": "https://example.org/drop"})
say("save")
drop_id = [x for x in draft()["sources"] if x["value"].endswith("/drop")][0]["id"]
api.draft_drop_source(drop_id)
check("a source is removed by hand", [x["value"] for x in draft()["sources"]] == ["https://example.org/keep"],
      draft()["sources"])
check("a bad id is a no-op", api.draft_drop_source("nope")["draft"]["count_sources"] == 1)
check("no spoken command removes anything",
      not [r for r in voicecmd.describe_grammar()
           if any(w in r["summary"].lower() for w in ("remove", "delete", "drop"))])
check("the grammar has no delete verb",
      not [k for k in voicecmd.COMMANDS if k in ("remove", "delete", "drop", "undo", "clear")],
      sorted(voicecmd.COMMANDS))
for name in ("remove", "delete", "drop", "clear"):
    check("run_voice_command(%r) is refused" % name, bool(c.run_voice_command(name).get("error")))
say("delete that")
check("'delete that' is dictation", draft()["text"] == "delete that", draft()["text"])
api.draft_clear()
check("draft_clear empties it", c.draft.is_empty())


# ---------------------------------------------------------------------------
# 15. Capture order: parallel transcription, ordered application
# ---------------------------------------------------------------------------
print("\n-- in order --")

got = []
o = point_logger._InOrder(got.append)
o.deliver(3, "c")
o.deliver(1, "a")
check("nothing is applied past a gap", got == ["a"], got)
o.deliver(2, "b")
check("the gap filled, everything drains in order", got == ["a", "b", "c"], got)
o.deliver(2, "late")
check("a number already applied is ignored", got == ["a", "b", "c"], got)

got = []
o = point_logger._InOrder(got.append, stall=0.05)
o.deliver(2, "b")
check("a missing number holds the next", got == [] and o.pending() == 1, got)
time.sleep(0.1)
o.deliver(3, "c")
check("after the stall, the gap is skipped", got == ["b", "c"], got)
o.deliver(1, "a-late")
check("the skipped one, arriving late, is not applied out of order", got == ["b", "c"], got)

got = []
o = point_logger._InOrder(lambda x: (_ for _ in ()).throw(ValueError("boom")) if x == "bad" else got.append(x))
o.deliver(1, "bad")
o.deliver(2, "ok")
check("one failing item does not stop the queue", got == ["ok"], got)

# The race that matters: "trail session X" said first but transcribed slowly,
# a sentence said second but back first. The session must exist before the
# sentence lands, or the sentence gets filed into the previous topic.
print("\n-- the utterance race --")

say("trail session Race origin")
race_old = open_topic()["id"]
say("left in the draft on purpose")
c.run_voice_command("log")
WAV_SESSION, WAV_SENTENCE = b"session-clip", b"sentence-clip"
_real_hear = c.hear


def _slow_hear(wav):
    if wav == WAV_SESSION:
        time.sleep(0.3)
        return {"text": "trail session Race target"}
    return {"text": "said after the session command"}


c.hear = _slow_hear
order = point_logger._InOrder(c.apply_heard)
t1 = threading.Thread(target=c.on_asr_utterance, args=(WAV_SESSION, 1, order))
t2 = threading.Thread(target=c.on_asr_utterance, args=(WAV_SENTENCE, 2, order))
t1.start()
t2.start()
t1.join()
t2.join()
c.hear = _real_hear
check("the sentence waited for the session", open_topic()["title"] == "Race target", open_topic()["title"])
check("and went into the new topic's draft, not the old topic",
      draft()["text"] == "said after the session command"
      and draft()["meta"]["topic_id"] == open_topic()["id"]
      and len(entries_of(race_old)) == 1, (draft()["text"], len(entries_of(race_old))))
api.draft_clear()

# Recording an enrollment sentence: what the live microphone hears of it is
# not dictation.
n_sent = len(SENT)
c._enrolling.set()
c.on_asr_utterance(b"enrollment-clip")
c._enrolling.clear()
check("an utterance during enrollment is skipped, not sent", len(SENT) == n_sent and c.draft.is_empty())
c.hear = lambda wav: (_ for _ in ()).throw(RuntimeError("network"))
c.on_asr_utterance(b"x", 1, point_logger._InOrder(c.apply_heard))
c.hear = _real_hear
check("a transcription crash reports an error and delivers", c.draft.is_empty())


# ---------------------------------------------------------------------------
# 16. Only my voice
# ---------------------------------------------------------------------------
print("\n-- speaker gate --")

OWNER_AMP, OTHER_AMP = 6000, 14000
_tag = [0]


def make_wav(seconds, amp):
    """A loud 200 Hz square wave, unique per call. The fake verifier tells
    voices apart by loudness - enough to drive every branch of the gate."""
    _tag[0] += 1
    n = int(16000 * seconds)
    samples = [amp if (i // 40) % 2 else -amp for i in range(n)]
    samples[-1] = _tag[0]
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(struct.pack("<%dh" % n, *samples))
    return buf.getvalue()


class FakeVerifier:
    def embed(self, pcm, samplerate=16000):
        if len(pcm) / 2.0 / samplerate < point_logger.speaker.MIN_SPEECH_SECONDS:
            return None
        loud = max(abs(x) for x in struct.unpack("<200h", pcm[:400]))
        return [1.0, 0.0] if loud < 10000 else [0.0, 1.0]


def hear(wav):
    """One utterance through the real path: gate, transcription, application."""
    c.on_asr_utterance(wav)


# Not enrolled: no check at all.
w = make_wav(1.5, OTHER_AMP)
SAID[w] = "anyone may speak"
hear(w)
check("no voiceprint: every voice is transcribed", draft()["text"] == "anyone may speak", draft()["text"])
api.draft_clear()

# Enrolled, and the model is not there: fail closed.
c.store.config["speaker"] = {"enabled": True, "embedding": [1.0, 0.0], "threshold": 0.55}
c._verifier = None
w = make_wav(1.5, OWNER_AMP)
SAID[w] = "even the owner"
n_sent = len(SENT)
hear(w)
check("a missing model holds the clip rather than letting every voice in",
      len(SENT) == n_sent and c.draft.is_empty() and len(c.held) == 1, (len(SENT) - n_sent, len(c.held)))
check("and says why - the verifier's own reason",
      c.held_list()[-1]["reason"] == c.verifier()[1] and c.verifier()[1],
      (c.held_list()[-1]["reason"], c.verifier()[1]))
check("the bar says the check could not run", pushes[-1][0] == "held" and "could not run" in pushes[-1][1], pushes[-1])
c.drop_held()

c._verifier = FakeVerifier()

w = make_wav(1.5, OWNER_AMP)
SAID[w] = "the owner speaking"
hear(w)
check("the owner's voice is transcribed", draft()["text"] == "the owner speaking", draft()["text"])

other = make_wav(1.5, OTHER_AMP)
SAID[other] = "log"
n_sent = len(SENT)
n_entries = len(entries_of(open_topic()["id"]))
hear(other)
check("another voice is NOT sent to be transcribed", len(SENT) == n_sent, len(SENT) - n_sent)
check("and changes nothing", draft()["text"] == "the owner speaking"
      and len(entries_of(open_topic()["id"])) == n_entries)
h = c.held_list()
check("it is held aside, with its score", len(h) == 1 and h[0]["score"] == 0.0 and h[0]["reason"] == "another voice", h)
check("the bar says so", pushes[-1][0] == "held" and "Another voice" in pushes[-1][1], pushes[-1])
check("the held list never carries audio", "wav" not in h[0], sorted(h[0]))
check("the held list is JSON for the bridge", bool(json.dumps(api.held_list())))

short_cmd = make_wav(0.5, OTHER_AMP)
SAID[short_cmd] = "log"
hear(short_cmd)
check("a clip too short to check still runs a certain command",
      c.draft.is_empty() and entries_of(open_topic()["id"])[-1]["text"] == "the owner speaking",
      draft()["text"])

short_words = make_wav(0.5, OTHER_AMP)
SAID[short_words] = "yes that one"
hear(short_words)
h = c.held_list()
check("a short clip that is not a command is held, with its words",
      c.draft.is_empty() and h[-1]["text"] == "yes that one"
      and h[-1]["reason"] == "too short to check the voice", h[-1])

# Recovering: the owner's call, always as text.
r = api.held_use(h[0]["id"])
check("'use it' transcribes a held clip now", r.get("ok") and r.get("text") == "log", r)
check("and appends it as TEXT - a held clip never runs a command",
      draft()["text"] == "log" and entries_of(open_topic()["id"])[-1]["text"] == "the owner speaking",
      draft()["text"])
check("it leaves the held list", [x["id"] for x in api.held_list()] == [h[1]["id"]], api.held_list())
api.held_use(h[1]["id"])
check("a held clip with words needs no second call", draft()["text"] == "log yes that one", draft()["text"])
check("a stale id is an error, not a crash", bool(api.held_use(999).get("error")))
check("a junk id is an error, not a crash", bool(api.held_use("x").get("error")))
api.draft_clear()

# Recovering fails: the clip goes back.
lost = make_wav(1.5, OTHER_AMP)             # never mapped: transcription errors
hear(lost)
hid = c.held_list()[-1]["id"]
r = c.use_held(hid)
check("a failed transcription puts the clip back", r.get("error") and c.held_list()[-1]["id"] == hid, r)
c.drop_held()

for i in range(15):
    hear(make_wav(1.2, OTHER_AMP))
h = c.held_list()
check("held clips are capped at %d" % c.HELD_MAX, len(h) == c.HELD_MAX, len(h))
check("the newest are kept", h[-1]["id"] - h[0]["id"] == c.HELD_MAX - 1, [x["id"] for x in h])
check("drop one by hand", len(api.held_drop(h[0]["id"])["held"]) == c.HELD_MAX - 1)
check("drop all by hand", api.held_drop()["held"] == [])

# Threshold and switches.
c.store.config["speaker"]["threshold"] = 0.0
w = make_wav(1.5, OTHER_AMP)
SAID[w] = "a threshold of zero lets everyone in"
hear(w)
check("the threshold is read at the moment of the check", draft()["text"].startswith("a threshold"), draft()["text"])
api.draft_clear()
st = api.speaker_save({"threshold": 7})
check("a threshold is clamped to 1", st["threshold"] == 1.0, st["threshold"])
check("a bad threshold is refused", bool(api.speaker_save({"threshold": "high"}).get("error")))
api.speaker_save({"threshold": 0.55})
st = api.speaker_save({"enabled": False})
check("the check switches off", st["enabled"] is False)
w = make_wav(1.5, OTHER_AMP)
SAID[w] = "switched off"
hear(w)
check("switched off: other voices are transcribed again", draft()["text"] == "switched off")
api.draft_clear()

# Enrolling and checking, with the recorded clips already in hand.
pcm_owner = point_logger.speaker.wav_to_pcm(make_wav(2.0, OWNER_AMP))[0]
c._enroll_clips = [pcm_owner, pcm_owner, pcm_owner]
st = api.speaker_enroll_finish()
cfg_sp = c.store.config["speaker"]
check("enrolling saves a voiceprint and switches the check on",
      st.get("enrolled") and st.get("enabled") and st.get("clips") == 3, st)
check("only numbers are stored, no audio",
      all(isinstance(v, (int, float, str, bool, list)) for v in cfg_sp.values())
      and all(isinstance(x, float) for x in cfg_sp["embedding"]), sorted(cfg_sp))
check("the recorded clips are released", c._enroll_clips == [])
c._enroll_clips = [pcm_owner]
r = api.speaker_check()
check("a check recording scores against the voiceprint",
      r.get("ok") and r.get("match") is True and r.get("score") == 1.0, r)
st = api.speaker_save({"enabled": True, "forget": True})
check("forget wipes the voiceprint and the switch",
      not st["enrolled"] and not st["enabled"] and c.store.config["speaker"]["embedding"] == [], st)
check("the switch will not turn on with nothing enrolled",
      api.speaker_save({"enabled": True})["enabled"] is False)
c._verifier = None
st = api.speaker_status()
check("status reports a missing model", st["model"] is False and st["model_mb"] > 20, st["model_mb"])
for key in ("runtime", "runtime_error", "model", "enabled", "enrolled", "threshold",
            "default_threshold", "clips", "seconds", "consistency", "recorded", "held"):
    check("speaker_status carries %r" % key, key in st)


# ---------------------------------------------------------------------------
# 17. The microphone test with nothing open
# ---------------------------------------------------------------------------
print("\n-- mic levels --")

lv = api.mic_levels(100)
check("no monitor and no live logger -> an empty wave, not an error",
      lv["running"] is False and lv["source"] == "" and lv["hi"] == [], lv)
check("mic_test_stop with nothing open is fine", api.mic_test_stop() == {"ok": True})
check("stopping a recording that never started is an error",
      bool(api.speaker_record_stop().get("error")))
time.sleep(1.6)     # the enrolling flag clears on a timer
check("and it does not leave dictation suppressed", not c._enrolling.is_set())


# ---------------------------------------------------------------------------
# 18. What the windows are given
# ---------------------------------------------------------------------------
print("\n-- payload --")

say("something to show")
payload = c.voice_snapshot()
for key in ("draft", "topic", "topic_id", "subtopic", "state", "detail", "heard",
            "always_on", "enabled", "configured", "listening", "mini", "held", "speaker_on"):
    check("payload carries %r" % key, key in payload, sorted(payload))
for key in ("text", "rev", "sources", "meta", "words", "count_sources", "origin"):
    check("draft carries %r" % key, key in payload["draft"], sorted(payload["draft"]))
check("payload names the topic", payload["topic"] == "Race target", payload["topic"])
check("not listening (no microphone here)", payload["listening"] is False)
check("the payload is JSON for evaluate_js", bool(json.dumps(payload)))

gv = api.get_voice()
check("get_voice returns config, hotkeys, grammar, draft, second_opinion",
      all(k in gv for k in ("config", "hotkeys", "grammar", "draft", "second_opinion")), sorted(gv))
check("no key -> no second opinion reported", gv["second_opinion"] is False)
check("four hotkeys reported", len(gv["hotkeys"]) == 4, gv["hotkeys"])
api.draft_clear()


# ---------------------------------------------------------------------------
# 19. Settings round-trips
# ---------------------------------------------------------------------------
print("\n-- save_voice / save_asr --")

out = api.save_voice({"always_on": False, "keys": {"log": "J"}})
check("save_voice persists always_on", out["config"]["always_on"] is False)
check("save_voice changes only the named key",
      out["config"]["keys"]["log"] == "J" and out["config"]["keys"]["finish"] == "F", out["config"]["keys"])
check("save_voice wrote to disk",
      json.loads(ps.CONFIG_FILE.read_text(encoding="utf-8"))["voice"]["keys"]["log"] == "J")
api.save_voice({"always_on": True, "keys": {"log": "S"}})
saved = json.loads(ps.CONFIG_FILE.read_text(encoding="utf-8"))
saved["voice"] = {"keys": {"log": "K"}}
ps.CONFIG_FILE.write_text(json.dumps(saved), encoding="utf-8")
check("a partial keys dict keeps the defaults for the rest",
      ps.Store().config["voice"]["keys"] == {"log": "K", "finish": "F", "session": "N", "tab": "T"},
      ps.Store().config["voice"]["keys"])

api.save_asr({"enabled": False, "language": "de", "device": "USB Microphone (Realtek)"})
a = c.store.config["asr"]
check("a third language is not saved", a["language"] == "", a["language"])
check("the microphone is saved by name", a["device"] == "USB Microphone (Realtek)", a["device"])
api.save_asr({"enabled": False, "language": "FA", "device": "  "})
a = c.store.config["asr"]
check("Persian is saved", a["language"] == "fa", a["language"])
check("a blank device means the system default", a["device"] == "", a["device"])
check("only Persian and English exist", tuple(point_logger.asr.ALLOWED_LANGUAGES) == ("fa", "en"))


# ---------------------------------------------------------------------------
# 20. The two halves agree on names
# ---------------------------------------------------------------------------
# evaluate_js swallows a ReferenceError and a missed querySelector returns
# null, so a name one side uses and the other never defined fails silently -
# and looks exactly like "voice is quiet". Both directions are pinned.
print("\n-- python/js contract --")

import re  # noqa: E402
import trailmark.ui as ui

check("popup defines and exports voiceState",
      "function voiceState(" in ui.POPUP_HTML and "window.voiceState=voiceState" in ui.POPUP_HTML)
check("popup defines and exports popupMini",
      "function popupMini(" in ui.POPUP_HTML and "window.popupMini=popupMini" in ui.POPUP_HTML)
check("full defines and exports voiceState",
      "function voiceState(" in ui.MAIN_HTML and "window.voiceState=voiceState" in ui.MAIN_HTML)
check("full still exports asrState", "window.asrState=asrState" in ui.MAIN_HTML)

for eid in ("voiceSec", "vState", "vCounts", "vTopic", "vHeard", "vWave", "vDraft",
            "vLog", "miniBtn", "voiceBtn",
            "ptText", "ptKinds", "tpSel", "attChips", "noTopic",
            "unifiedSec", "topicSelWrap", "logPanel", "keyHints"):
    check("popup markup has #%s" % eid, ('id="%s"' % eid) in ui.POPUP_HTML)
for gone_eid in ("vSave", "vTab", "vSess", "vFin"):
    check("voice action button #%s is ripped off" % gone_eid, ('id="%s"' % gone_eid) not in ui.POPUP_HTML)
for k in ("toggle", "attach", "log", "session", "tab", "finish", "hide"):
    check("shortcut hint data-k=%s exists" % k, ('data-k="%s"' % k) in ui.POPUP_HTML)
check("hint flash gamification wired", "function flashKey(" in ui.POPUP_HTML
      and ".flash" in ui.POPUP_HTML)
for eid in ("voiceChip", "vcSw", "vcCmdSw", "vcHkSw", "vcSave", "vcHkStatus",
            "mtBtn", "mtWave", "asrLang", "asrDevice", "asrSensitivity"):
    check("full markup has #%s" % eid, ('id="%s"' % eid) in ui.MAIN_HTML)
# Generated in a template and read back by a binder: two mentions at least,
# one means a half-wired control.
for eid in ("vcKeyLog", "vcKeyFinish", "vcKeySession", "vcKeyTab", "spkRec", "spkSave",
            "spkSw", "spkTh", "spkChk", "spkForget", "spkDl", "heldDropAll"):
    check("full wires #%s at both ends" % eid, ui.MAIN_HTML.count(eid) >= 2, ui.MAIN_HTML.count(eid))
check("the Persian option is offered", 'value="fa"' in ui.MAIN_HTML or "'fa'" in ui.MAIN_HTML
      or '"fa"' in ui.MAIN_HTML)
check("no third language is offered", not re.search(r'value="(de|fr|ar|es|zh)"', ui.MAIN_HTML))

called = set(re.findall(r"api\.([a-z_]+)\(", ui.POPUP_HTML + ui.MAIN_HTML))
missing = sorted(m for m in called if not hasattr(point_logger.Api, m))
check("no window calls a bridge method Api lacks", not missing, missing)
for gone in ("voice_buffer", "voice_drop_comment", "voice_drop_source", "voice_clear",
             "take_clipboard_capture"):
    check("the old bridge call %s is gone from the windows" % gone, gone not in called)

check("the Settings copy names the real held cap",
      ("the last %d stay listed" % point_logger.Controller.HELD_MAX) in ui.MAIN_HTML)
check("Settings discloses that sub-second clips ARE sent to be transcribed",
      "<b>is</b> sent to be transcribed" in ui.MAIN_HTML)
check("mini is narrower and much shorter than the popup",
      point_logger.MINI_W < point_logger.POPUP_W and point_logger.MINI_H < point_logger.POPUP_H // 3)


print("\n-- one name for the feature --")

check("the tray row names the feature",
      point_logger.Controller._voice_label(True) == "Always-on voice: On")
check("the tray row shows Off too",
      point_logger.Controller._voice_label(False) == "Always-on voice: Off")
check("Settings has exactly one card titled Always-on voice",
      ui.MAIN_HTML.count(">Always-on voice</div>") == 1, ui.MAIN_HTML.count(">Always-on voice</div>"))
check("the master switch carries the feature name", 'aria-label="Always-on voice"' in ui.MAIN_HTML)
check("the old label is gone", "Auto-log speech as notes" not in ui.MAIN_HTML)
check("the popup can start it without Settings", "api.toggle_voice()" in ui.POPUP_HTML)
check("the unified voice block is always visible",
      "Unified card: the voice block is always visible" in ui.POPUP_HTML
      or "sec.hidden=false" in ui.POPUP_HTML)
check("the off state tells you how to start it", "Click the microphone above to start" in ui.POPUP_HTML)
check("no copy still asks for the Trail- prefix to log",
      "Say &ldquo;Trail-Log" not in ui.POPUP_HTML + ui.MAIN_HTML
      and 'Say "Trail-Log' not in ui.POPUP_HTML + ui.MAIN_HTML)


print()
print("ALL CHECKS PASSED" if not FAILS else "FAILED: " + ", ".join(FAILS))
sys.exit(1 if FAILS else 0)
