"""Headless tests for the always-on voice session: transcript -> command -> store.

Drives Controller.on_voice_transcript and run_voice_command against a real
Store rooted in a temp directory. No microphone, no transcription call, no
windows - the pywebview surfaces are stubbed, which is the whole reason
on_voice_transcript exists as its own method.

What is actually being pinned here is the contract the owner described:

    talk            -> buffered, NOT logged
    Trail-Save      -> clipboard parked as a source, NOT logged
    Trail-Log       -> the buffered comments AND sources become one point
    Trail-Tab       -> sub-topic on the open topic
    Trail-Session   -> new topic, previous buffer safely landed first
    Trail-Finish    -> topic closed, nothing silently dropped
    removes         -> by hand only
"""

import pathlib
import sys
import tempfile

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


# Temp APPDATA before point_logger imports the store module-level paths.
import point_store as ps  # noqa: E402

tmp = pathlib.Path(tempfile.mkdtemp(prefix="opl_voice_"))
ps.BASE_DIR = tmp
ps.DATA_FILE = tmp / "points.json"
ps.CONFIG_FILE = tmp / "config.json"
ps.ATTACH_DIR = tmp / "attachments"
ps.EXPORT_DIR = tmp / "exports"

import point_logger  # noqa: E402
import clipboard  # noqa: E402

c = point_logger.Controller()

# The windows do not exist headless; push_voice_state walks them and must
# tolerate that. Record every push so the UI contract is testable too.
pushes = []
_orig_push = c.push_voice_state


def _record(state, detail=""):
    pushes.append((state, detail))
    return _orig_push(state, detail)


c.push_voice_state = _record
c.refresh_full = lambda: None

# A controllable clipboard: Trail-Save must never touch the real one.
CLIP = {"type": "none", "value": None, "meta": {}}
clipboard.read = lambda: dict(CLIP)


def entries_of(tid):
    t = c.store.find_topic(tid)
    return (t or {}).get("entries", [])


def open_topic():
    return c._open_topic()


# ---------------------------------------------------------------------------
# 1. Commands with no open topic report, they do not crash or invent one
# ---------------------------------------------------------------------------
print("\n-- no open topic --")

check("no topic to start with", open_topic() is None)
r = c.run_voice_command("log")
check("Trail-Log with no topic errors", bool(r.get("error")), r)
r = c.run_voice_command("tab", "intro")
check("Trail-Tab with no topic errors", bool(r.get("error")), r)
r = c.run_voice_command("finish")
check("Trail-Finish with no topic errors", bool(r.get("error")), r)
check("still no topic invented", open_topic() is None)


# ---------------------------------------------------------------------------
# 2. Trail-Session starts one, named and unnamed
# ---------------------------------------------------------------------------
print("\n-- session --")

r = c.run_voice_command("session", "Rust borrow checker")
check("Trail-Session succeeds", not r.get("error"), r)
t = open_topic()
check("topic is open", t is not None)
check("topic took the spoken title", t["title"] == "Rust borrow checker", t["title"])
tid = t["id"]


# ---------------------------------------------------------------------------
# 3. Talking buffers; it does NOT log
# ---------------------------------------------------------------------------
print("\n-- talking buffers --")

c.on_voice_transcript("the borrow checker rejects this because the lifetime is too short")
c.on_voice_transcript("worth checking whether NLL changed that")
check("two comments buffered", c.voice.snapshot()["count_comments"] == 2,
      c.voice.snapshot()["count_comments"])
check("NOTHING was logged", len(entries_of(tid)) == 0, len(entries_of(tid)))
check("a push reported it was heard", pushes[-1][0] == "heard", pushes[-1])

# Empty and whitespace transcripts must not create empty comments.
c.on_voice_transcript("")
c.on_voice_transcript("    ")
check("blank transcripts ignored", c.voice.snapshot()["count_comments"] == 2,
      c.voice.snapshot()["count_comments"])


# ---------------------------------------------------------------------------
# 4. Trail-Save parks the clipboard, spoken and by hotkey
# ---------------------------------------------------------------------------
print("\n-- save --")

CLIP.update({"type": "link", "value": "https://doc.rust-lang.org/nomicon/"})
c.on_voice_transcript("Trail-Save")
snap = c.voice.snapshot()
check("link parked as a source", snap["count_sources"] == 1, snap["sources"])
check("source is the clipboard link",
      snap["sources"][0]["value"] == "https://doc.rust-lang.org/nomicon/",
      snap["sources"][0])
check("still nothing logged", len(entries_of(tid)) == 0, len(entries_of(tid)))

# Saying it twice on the same clipboard must not cite it twice.
c.on_voice_transcript("trail save")
check("duplicate save deduplicated", c.voice.snapshot()["count_sources"] == 1,
      c.voice.snapshot()["count_sources"])
check("duplicate reported, not silent", pushes[-1][0] == "duplicate", pushes[-1])

# Text on the clipboard becomes a string citation, not a link.
CLIP.update({"type": "text", "value": "Jung, Ralf et al. RustBelt (2018)"})
c.run_voice_command("save", "", via="hotkey")
snap = c.voice.snapshot()
check("text clipboard becomes a string source",
      snap["count_sources"] == 2 and snap["sources"][1]["type"] == "string",
      snap["sources"])

# An empty clipboard is reported rather than parked as a blank source.
CLIP.update({"type": "none", "value": None})
r = c.run_voice_command("save")
check("empty clipboard errors", bool(r.get("error")), r)
check("no phantom source added", c.voice.snapshot()["count_sources"] == 2,
      c.voice.snapshot()["count_sources"])


# ---------------------------------------------------------------------------
# 5. Trail-Log commits comments AND sources as one point
# ---------------------------------------------------------------------------
print("\n-- log --")

r = c.run_voice_command("log")
check("Trail-Log succeeds", not r.get("error"), r)
ents = entries_of(tid)
check("exactly one entry created", len(ents) == 1, len(ents))
e = ents[0]
check("entry text is both comments joined",
      e["text"] == "the borrow checker rejects this because the lifetime is too short "
                   "worth checking whether NLL changed that", e["text"])
check("entry carries both sources", len(e["sources"]) == 2, e["sources"])
check("entry kind is note", e["kind"] == "note", e["kind"])
check("buffer drained after logging", c.voice.is_empty(), c.voice.snapshot())

# Logging an empty buffer is an error, not an empty point.
r = c.run_voice_command("log")
check("Trail-Log on an empty buffer errors", bool(r.get("error")), r)
check("no second entry", len(entries_of(tid)) == 1, len(entries_of(tid)))

# Sources with nothing said is also refused - an entry needs text.
CLIP.update({"type": "link", "value": "https://example.org/orphan"})
c.run_voice_command("save")
r = c.run_voice_command("log")
check("sources with no comment errors", bool(r.get("error")), r)
check("the orphan source is kept, not thrown away",
      c.voice.snapshot()["count_sources"] == 1, c.voice.snapshot())
c.voice.clear()


# ---------------------------------------------------------------------------
# 6. Trail-Tab
# ---------------------------------------------------------------------------
print("\n-- tab --")

r = c.run_voice_command("tab", "open questions")
check("Trail-Tab succeeds", not r.get("error"), r)
check("sub-topic added", "open questions" in open_topic()["subtopics"],
      open_topic()["subtopics"])
# An unnamed tab numbers itself rather than failing.
c.run_voice_command("tab", "")
subs = open_topic()["subtopics"]
check("unnamed tab is numbered", len(subs) == 2 and subs[1].startswith("Tab"), subs)
c.run_voice_command("tab", "")
check("a second unnamed tab does not collide",
      len(open_topic()["subtopics"]) == 3, open_topic()["subtopics"])


# ---------------------------------------------------------------------------
# 7. A new session lands the old buffer in the OLD topic first
# ---------------------------------------------------------------------------
print("\n-- session hand-off --")

c.on_voice_transcript("one last thought about lifetimes")
r = c.run_voice_command("session", "Postgres migration")
check("second session starts", not r.get("error"), r)
old_entries = entries_of(tid)
check("the trailing comment landed in the OLD topic",
      len(old_entries) == 2 and "one last thought" in old_entries[-1]["text"],
      [e["text"] for e in old_entries])
new_t = open_topic()
check("the new topic is now the open one", new_t["title"] == "Postgres migration",
      new_t["title"])
check("the new topic is empty", len(new_t["entries"]) == 0, new_t["entries"])
check("buffer is clean for the new topic", c.voice.is_empty())
new_tid = new_t["id"]


# ---------------------------------------------------------------------------
# 8. Trail-Finish logs what is pending, then closes
# ---------------------------------------------------------------------------
print("\n-- finish --")

c.on_voice_transcript("indexes rebuilt in about four minutes")
r = c.run_voice_command("finish")
check("Trail-Finish succeeds", not r.get("error"), r)
t = c.store.find_topic(new_tid)
check("topic is closed", t["status"] == "closed", t["status"])
check("the pending comment was logged, not dropped",
      len(t["entries"]) == 1 and "four minutes" in t["entries"][0]["text"],
      [e["text"] for e in t["entries"]])
check("buffer cleared", c.voice.is_empty())
# Trail-Finish closes the topic it acted on, not "the session" as a whole.
# The store has always allowed several open topics, and Trail-Session does
# not close the previous one - so finishing the newest hands the context
# back to the one before it, exactly as clicking Close does.
back = open_topic()
check("finishing hands the context back to the previous open topic",
      back is not None and back["id"] == tid, (back or {}).get("title"))


# ---------------------------------------------------------------------------
# 9. Spoken commands reach the same code as the hotkeys
# ---------------------------------------------------------------------------
print("\n-- spoken == pressed --")

c.run_voice_command("session", "Voice parity")
vid = open_topic()["id"]
c.on_voice_transcript("first")
c.on_voice_transcript("Trail-Log")          # spoken
check("spoken Trail-Log logged an entry", len(entries_of(vid)) == 1, len(entries_of(vid)))
c.on_voice_transcript("second")
c.run_voice_command("log", "", via="hotkey")  # pressed
check("pressed log logged an entry", len(entries_of(vid)) == 2, len(entries_of(vid)))
c.on_voice_transcript("Trail-Tab spoken tab")
check("spoken Trail-Tab added the sub-topic",
      "spoken tab" in open_topic()["subtopics"], open_topic()["subtopics"])


# ---------------------------------------------------------------------------
# 10. A sentence that merely mentions a command must not fire it
# ---------------------------------------------------------------------------
print("\n-- no accidental commands --")

before = len(entries_of(vid))
subs_before = list(open_topic()["subtopics"])
for sentence in ["the trail logs are in the folder",
                 "trail log the sources for this one",
                 "I want to finish the trail tomorrow"]:
    c.on_voice_transcript(sentence)
check("none of them logged anything", len(entries_of(vid)) == before,
      len(entries_of(vid)))
check("none of them added a tab", open_topic()["subtopics"] == subs_before,
      open_topic()["subtopics"])
check("all three were buffered as comments",
      c.voice.snapshot()["count_comments"] == 3, c.voice.snapshot()["count_comments"])
check("the topic is still open", open_topic() is not None)
c.voice.clear()


# ---------------------------------------------------------------------------
# 11. always_on off restores the old dictation behaviour
# ---------------------------------------------------------------------------
print("\n-- always_on off --")

c.store.config["voice"]["always_on"] = False
before = len(entries_of(vid))
c.on_voice_transcript("dictated straight in")
check("with always_on off, an utterance logs immediately",
      len(entries_of(vid)) == before + 1, len(entries_of(vid)))
check("and nothing is buffered", c.voice.is_empty(), c.voice.snapshot())
# A command phrase is just text in this mode - no hidden grammar.
c.on_voice_transcript("Trail-Log")
check("a command phrase is logged as text when always_on is off",
      entries_of(vid)[-1]["text"] == "Trail-Log", entries_of(vid)[-1]["text"])
c.store.config["voice"]["always_on"] = True

# commands off: always-on still buffers, but nothing is a command.
c.store.config["voice"]["commands"] = False
c.on_voice_transcript("Trail-Log")
check("with commands off the phrase is buffered, not run",
      c.voice.snapshot()["count_comments"] == 1, c.voice.snapshot())
c.store.config["voice"]["commands"] = True
c.voice.clear()


# ---------------------------------------------------------------------------
# 12. Removes are by hand
# ---------------------------------------------------------------------------
print("\n-- hand removes --")

c.on_voice_transcript("keep this one")
c.on_voice_transcript("drop this one")
api = point_logger.Api(c.store, c)
api.voice_drop_comment(1)
snap = c.voice.snapshot()
check("comment removed by hand", snap["comments"] == ["keep this one"], snap["comments"])
check("a stale index is a no-op, not a crash",
      api.voice_drop_comment(99).get("ok") is False, api.voice_drop_comment(99))
api.voice_clear()
check("voice_clear empties the buffer", c.voice.is_empty())


# ---------------------------------------------------------------------------
# 13. The payload the windows are given
# ---------------------------------------------------------------------------
print("\n-- ui payload --")

c.on_voice_transcript("something to show")
payload = c.voice_snapshot()
for key in ("comments", "sources", "text", "count_comments", "count_sources",
            "empty", "topic", "state", "detail", "always_on", "listening", "mini"):
    check("payload carries %r" % key, key in payload, sorted(payload))
check("payload names the open topic", payload["topic"] == "Voice parity", payload["topic"])
check("payload reports not listening (no microphone here)",
      payload["listening"] is False, payload["listening"])
import json as _json  # noqa: E402
try:
    _json.dumps(payload)
    check("payload is JSON-serialisable for evaluate_js", True)
except Exception as e:
    check("payload is JSON-serialisable for evaluate_js", False, e)

# get_voice must answer without a window, too.
gv = api.get_voice()
check("get_voice returns config/hotkeys/grammar/buffer",
      all(k in gv for k in ("config", "hotkeys", "grammar", "buffer")), sorted(gv))
check("get_voice reports four hotkeys", len(gv["hotkeys"]) == 4, gv["hotkeys"])
check("hotkey report names the combos",
      all(h["combo"] for h in gv["hotkeys"]), gv["hotkeys"])


# ---------------------------------------------------------------------------
# 14. save_voice round-trip
# ---------------------------------------------------------------------------
print("\n-- save_voice --")

out = api.save_voice({"always_on": False, "keys": {"log": "J"}})
check("save_voice persists always_on", out["config"]["always_on"] is False,
      out["config"])
check("save_voice changes only the named key",
      out["config"]["keys"]["log"] == "J" and out["config"]["keys"]["finish"] == "F",
      out["config"]["keys"])
check("save_voice wrote to disk",
      (ps.CONFIG_FILE.exists()
       and _json.loads(ps.CONFIG_FILE.read_text(encoding="utf-8"))["voice"]["keys"]["log"] == "J"),
      ps.CONFIG_FILE.exists())
api.save_voice({"always_on": True, "keys": {"log": "S"}})

# A config file naming only one key must not wipe the other three.
saved = _json.loads(ps.CONFIG_FILE.read_text(encoding="utf-8"))
saved["voice"] = {"keys": {"log": "K"}}
ps.CONFIG_FILE.write_text(_json.dumps(saved), encoding="utf-8")
reloaded = ps.Store()
check("a partial saved keys dict keeps the defaults for the rest",
      reloaded.config["voice"]["keys"] == {"log": "K", "finish": "F",
                                           "session": "N", "tab": "T"},
      reloaded.config["voice"]["keys"])


# ---------------------------------------------------------------------------
# 15. The two halves agree on names
# ---------------------------------------------------------------------------
# evaluate_js swallows a ReferenceError, and a querySelector that misses
# returns null - so a name Python calls that the window never defined, or an
# element the script reaches for that the markup never had, fails silently
# and looks exactly like "voice is quiet". Both directions are pinned here.
print()
print("-- python/js contract --")

import ui  # noqa: E402

check("popup defines voiceState", "function voiceState(" in ui.POPUP_HTML)
check("popup exports voiceState", "window.voiceState=voiceState" in ui.POPUP_HTML)
check("popup defines popupMini", "function popupMini(" in ui.POPUP_HTML)
check("popup exports popupMini", "window.popupMini=popupMini" in ui.POPUP_HTML)
check("full defines voiceState", "function voiceState(" in ui.MAIN_HTML)
check("full exports voiceState", "window.voiceState=voiceState" in ui.MAIN_HTML)
check("full still defines asrState", "window.asrState=asrState" in ui.MAIN_HTML)

# Every id the popup's voice script queries must exist in the popup markup.
for eid in ("voiceSec", "vState", "vCounts", "vTopic", "vHeard", "vList",
            "vHint", "vLog", "vSave", "vTab", "vSess", "vFin", "miniBtn"):
    check("popup markup has #%s" % eid, ('id="%s"' % eid) in ui.POPUP_HTML)

for eid in ("voiceChip", "vcSw", "vcCmdSw", "vcHkSw", "vcSave", "vcHkStatus"):
    check("full markup has #%s" % eid, ('id="%s"' % eid) in ui.MAIN_HTML)

# The four key fields are emitted by a generator rather than written out, so
# the name has to appear at least twice: once where the input is built and
# once where the binder reads it back. One occurrence means a half-wired field.
for eid in ("vcKeyLog", "vcKeyFinish", "vcKeySession", "vcKeyTab"):
    check("full wires #%s at both ends" % eid,
          ui.MAIN_HTML.count(eid) >= 2, ui.MAIN_HTML.count(eid))

# Every bridge method the windows call must exist on Api.
for meth in ("get_voice", "save_voice", "voice_command", "voice_buffer",
             "voice_drop_comment", "voice_drop_source", "voice_clear",
             "set_popup_mini"):
    check("Api.%s exists" % meth, callable(getattr(api, meth, None)))

# And the JS must not reach for one that does not.
import re as _re  # noqa: E402
called = set(_re.findall(r"api\.([a-z_]+)\(", ui.POPUP_HTML + ui.MAIN_HTML))
missing = sorted(m for m in called if not hasattr(point_logger.Api, m))
check("no window calls a bridge method Api lacks", not missing, missing)

# The mini geometry the UI is laid out for must be the geometry Python sets.
check("mini is narrower and much shorter than the popup",
      point_logger.MINI_W < point_logger.POPUP_W
      and point_logger.MINI_H < point_logger.POPUP_H // 3,
      (point_logger.MINI_W, point_logger.MINI_H,
       point_logger.POPUP_W, point_logger.POPUP_H))

# Removes must stay hand-only. Both directions: the grammar must not describe
# a destructive verb, and the dispatcher must refuse one if a caller invents it.
import voicecmd  # noqa: E402

grammar = voicecmd.describe_grammar()
check("no spoken command removes anything",
      not [r for r in grammar
           if any(w in r["summary"].lower() for w in ("remove", "delete", "drop"))],
      [r["command"] for r in grammar])
check("the grammar has no delete verb",
      not [k for k in voicecmd.COMMANDS
           if k in ("remove", "delete", "drop", "undo")],
      sorted(voicecmd.COMMANDS))
for name in ("remove", "delete", "drop", "clear"):
    r = c.run_voice_command(name)
    check("run_voice_command(%r) is refused" % name, bool(r.get("error")), r)


print()
print("ALL CHECKS PASSED" if not FAILS else "FAILED: " + ", ".join(FAILS))
sys.exit(1 if FAILS else 0)
