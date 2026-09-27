"""Spoken commands for always-on voice, and the draft they act on.

Two pieces, both pure - no audio, no network, no store, no UI. That is
deliberate: always-on voice decides, many times a minute, whether what you
just said was an instruction or a thought, and a decision made that often has
to be testable without a microphone.

    parse(text)    one transcript in: which command it COULD be, and in what form
    decide(...)    the parse plus a second opinion, if any, in; command or text out
    Draft          the one editable draft that voice and typing both write into

The commands
------------
Plain words, said on their own or with a name::

    "log"               file the draft (text + sources) as one point
    "save"              attach whatever is on the clipboard as a source
    "finish"            close the open topic
    "session <title>"   start a new topic
    "tab <name>"        add a sub-topic to the open topic

"Trail-Log" and the rest still work - "trail" in front is accepted and makes
the command certain - but nobody has to say it any more.

Removes are not spoken. Deleting by voice means a misheard word can destroy
work, and there is no undo in the store - so the destructive direction stays
on the mouse or the keyboard, in the draft, where it is deliberate.

Command or text: who decides
----------------------------
Without a wake word, "log" is a command and "log files are rotated nightly" is
a note - and "session management is tricky" parses exactly like "session
Rust borrow checker". Code cannot tell a title from a sentence; a person can,
instantly. So the split is:

* **Code finds the candidates.** ``parse`` says which command the words could
  be and in which *form*: ``wake`` ("trail log"), ``bare`` (the utterance is
  just the verb, give or take "please"), ``argument`` ("session" or "tab"
  followed by more words). Most utterances are no candidate at all and never
  leave this module.
* **Code decides the certain ones.** ``wake`` and ``bare`` fire without a
  question - a lone "log" is not a judgement.
* **Jev decides the ``argument`` form**: is what follows the word a name
  ("Rust borrow checker") or the rest of a sentence ("management is
  tricky")? See ``judge.command_intents`` for the question and its numbers.
* **When Jev cannot answer** - no key, no network, timeout - it stays text.
  That is the fail-closed direction: the words land in the draft where they
  can be seen and edited, and nothing is filed, closed or created by
  accident.

A command at the END of a sentence ("... that's the idea, log") is dictation.
That form was built and measured and no question separated it: list-shaped
dictation ("our verbs are open, edit, log") reads as a finished thought
followed by a command just as well as the real thing does. Say the command
on its own - the pause before it is what makes it one.

Matching
--------
With the wake word, verbs are matched fuzzily (Damerau-Levenshtein), because
"trail" already carries the intent and ASR mangles the rest: "trial lock",
"trailsave". Without it, only the spellings listed in ``COMMANDS`` count -
fuzzy matching a bare word would make "dog" a log command.
"""

import re
import threading

__all__ = ["parse", "decide", "normalise", "Draft", "COMMANDS", "WAKE_WORDS",
           "CERTAIN_FORMS", "OPINION_FORMS", "describe_grammar"]


# --- normalisation ----------------------------------------------------------

#: Arabic-script letters that Persian ASR output mixes with their Persian
#: equivalents. Normalised so "تریل" matches however it came back.
_LETTER_FOLD = {
    "ي": "ی",  # ARABIC YEH -> FARSI YEH
    "ك": "ک",  # ARABIC KAF -> KEHEH
    "ى": "ی",  # ALEF MAKSURA -> FARSI YEH
    "ة": "ه",  # TEH MARBUTA -> HEH
}

#: Eastern Arabic and Persian digits -> ASCII, so a spoken number in an
#: argument ("trail tab فصل ۲") survives into the sub-topic name intact.
_DIGIT_FOLD = {}
for _i in range(10):
    _DIGIT_FOLD[chr(0x0660 + _i)] = str(_i)   # Arabic-Indic
    _DIGIT_FOLD[chr(0x06F0 + _i)] = str(_i)   # Extended (Persian)

#: Everything that is punctuation to a human but a character to str.split().
#: Includes the Persian comma/semicolon/question mark, the Arabic tatweel, and
#: the zero-width non-joiner, which Persian text is full of.
_PUNCT_RE = re.compile(
    "[" + re.escape(".,!?;:'\"()\\[\\]{}<>/\\\\|@#$%^&*_+=~`‘’“”"
                    "،؛؟۔«»–—ـ") + "]")

#: Said around a command and meaning nothing. Kept short on purpose - every
#: word here is a word that can no longer block a false positive.
_FILLERS = {
    "ok", "okay", "kay", "now", "please", "hey", "so", "um", "uh", "er", "ah",
    "and", "then", "alright", "right", "yeah", "yep", "well", "just", "lets",
    "let's", "go", "do", "it", "the", "this", "that",
    "خب",            # khob
    "لطفا",  # lotfan
    "حالا",  # hala
    "خوب",      # khoob
    "کن", "بکن", "کنید", "اینو",   # kon, bokon, konid ("do it"), ino ("this")
}


def normalise(text):
    """Lowercase, fold Persian letters and digits, drop punctuation, split.

    Returns a list of tokens. The hyphen in "Trail-Save" is punctuation, so
    the written form and the spoken form normalise to the same two tokens.
    """
    s = str(text or "")
    s = "".join(_LETTER_FOLD.get(ch, _DIGIT_FOLD.get(ch, ch)) for ch in s)
    s = s.replace("‌", " ").replace("-", " ").replace("‑", " ")
    s = _PUNCT_RE.sub(" ", s)
    return s.lower().split()


# --- fuzzy matching ---------------------------------------------------------

def _damerau(a, b):
    """Edit distance counting a transposition of adjacent characters as one.

    Plain Levenshtein calls "trail"/"trial" two edits, which is the same cost
    as two unrelated substitutions - too blunt for the one mangling the wake
    word suffers most.
    """
    if a == b:
        return 0
    la, lb = len(a), len(b)
    if not la:
        return lb
    if not lb:
        return la
    prev2 = None
    prev = list(range(lb + 1))
    for i in range(1, la + 1):
        cur = [i] + [0] * lb
        for j in range(1, lb + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
            if (i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]):
                cur[j] = min(cur[j], prev2[j - 2] + 1)
        prev2, prev = prev, cur
    return prev[lb]


def _tolerance(word):
    """How many edits a word of this length may absorb and still match.

    Short words get one edit because at three or four letters a second edit
    is most of the word; longer ones get two because that is roughly one
    mangled syllable.
    """
    n = len(word)
    if n <= 4:
        return 1
    if n <= 6:
        return 1
    return 2


def _near(token, spellings):
    """True when ``token`` is one of ``spellings`` or within tolerance of one."""
    if token in spellings:
        return True
    for want in spellings:
        if abs(len(token) - len(want)) > _tolerance(want):
            continue
        if _damerau(token, want) <= _tolerance(want):
            return True
    return False



# --- the grammar ------------------------------------------------------------

#: Spellings of the wake word with a real chance of coming back from ASR.
#: "trial" and "tale" are here because they are what the model produces, not
#: because anybody says them. Optional now - it makes a command certain.
WAKE_WORDS = [
    "trail", "trails", "trial", "trials", "trael", "treyl", "trale", "tale",
    "تریل",        # تریل
    "ترایل",  # ترایل
]

#: command -> what it does and how it is said.
#:
#: ``plain`` is what counts WITHOUT the wake word, matched exactly: the word
#: itself and its Persian transliteration. ``verbs`` is the fuzzy list used
#: only after "trail", where the wake word already carries the intent and the
#: mangled spellings ("lock", "safe") are worth catching.
#:
#: ``argument`` is True for the two that name something; for the rest, words
#: after the verb mean it was a sentence, not an instruction.
COMMANDS = {
    "log": {
        "plain": ["log", "لاگ"],
        "verbs": ["log", "logs", "logged", "logg", "lock", "locke", "lok",
                  "لاگ"],
        "argument": False,
        "say": "Log",
        "summary": "file the draft - text and sources - as one point",
    },
    "save": {
        "plain": ["save", "سیو"],
        "verbs": ["save", "saved", "safe", "save's", "sav", "seve", "sev",
                  "سیو"],
        "argument": False,
        "say": "Save",
        "summary": "attach the clipboard to the draft as a source",
    },
    "finish": {
        "plain": ["finish", "finished", "فینیش"],
        "verbs": ["finish", "finished", "finnish", "finis", "fenish", "finch",
                  "فینیش"],
        "argument": False,
        "say": "Finish",
        "summary": "log what is in the draft, then close the topic",
    },
    "session": {
        "plain": ["session", "سشن", "سیشن"],
        "verbs": ["session", "sessions", "sesion", "secession", "cession",
                  "sesh", "سشن", "سیشن"],
        "argument": True,
        "say": "Session <name>",
        "summary": "start a new topic, named or dated",
    },
    "tab": {
        "plain": ["tab", "تب"],
        "verbs": ["tab", "tabs", "tap", "taps", "taab", "tad", "تب"],
        "argument": True,
        "say": "Tab <name>",
        "summary": "add a sub-topic and file what follows under it",
    },
}

#: Forms code decides alone, and forms that need a second opinion.
CERTAIN_FORMS = ("wake", "bare")
OPINION_FORMS = ("argument",)

def _is_filler(word):
    return word in _FILLERS


def _flatten(transcript):
    """Raw whitespace tokens, plus every normalised sub-word tagged with the
    raw token it came from.

    Matching happens over the sub-words (so "Trail-Session" is a wake word
    and a verb), but an argument is sliced out of the RAW tokens (so
    "borrow-checker" stays one hyphenated word and a title keeps its
    capitals). Keeping both in step is what this function is for - the two
    lists are different lengths, so neither index works in the other.
    """
    raw = str(transcript or "").split()
    flat = []
    for ri, tok in enumerate(raw):
        subs = normalise(tok)
        for si, sub in enumerate(subs):
            flat.append({"word": sub, "raw": ri, "sub": si, "of": len(subs)})
    return raw, flat


def _split_joined(token):
    """Split "traillog" into ("trail", "log") when ASR dropped the space.

    Tries every split point rather than assuming the wake word's length,
    because the wake word itself may have arrived mangled.
    """
    for i in range(2, len(token) - 1):
        head, tail = token[:i], token[i:]
        if not _near(head, WAKE_WORDS):
            continue
        for spec in COMMANDS.values():
            if _near(tail, spec["verbs"]):
                return head, tail
    return None


def _plain(word, with_argument=None):
    """The command whose plain spelling ``word`` is, or None."""
    for name, spec in COMMANDS.items():
        if with_argument is not None and spec["argument"] != with_argument:
            continue
        if word in spec["plain"]:
            return name
    return None


def _fuzzy(word, with_argument=None):
    for name, spec in COMMANDS.items():
        if with_argument is not None and spec["argument"] != with_argument:
            continue
        if _near(word, spec["verbs"]):
            return name
    return None


def _result(transcript, command=None, argument="", form=None):
    return {"command": command, "argument": argument, "transcript": transcript,
            "form": form}


def parse(text):
    """Which command one transcript COULD be, and in what form.

    Returns ``{"command", "argument", "transcript", "form"}``. ``command`` is
    None for the common case - a thought, not an instruction. ``form`` says
    how sure code is (see the module docstring): ``wake`` and ``bare`` are
    certain, ``argument`` needs a second opinion.
    """
    transcript = str(text or "").strip()
    raw, flat = _flatten(transcript)
    i = 0
    while i < len(flat) and _is_filler(flat[i]["word"]):
        i += 1
    body = flat[i:]
    if not body:
        return _result(transcript)

    woke = _wake(transcript, raw, body)
    if woke is not None:
        return woke

    head, rest = body[0], body[1:]
    name = _plain(head["word"])
    if name:
        content = [t for t in rest if not _is_filler(t["word"])]
        if not content:
            return _result(transcript, name, "", "bare")
        if COMMANDS[name]["argument"]:
            return _result(transcript, name, _argument(raw, head, rest), "argument")
        # "log files are rotated nightly": a no-argument verb followed by a
        # sentence is a sentence.
    return _result(transcript)


def _wake(transcript, raw, body):
    """The wake-word form: "trail log", "Trail-Session Rust", "traillog".

    Returns None when the utterance does not start with the wake word, or
    starts with it but is not a command ("trail log the sources" - log takes
    no argument, so that was a sentence about trail logs).
    """
    head, rest = body[0], body[1:]
    if not _near(head["word"], WAKE_WORDS):
        joined = _split_joined(head["word"])
        if joined is None:
            return None
        # The verb shares the wake word's raw token, and is its last sub-word:
        # everything after that token is argument.
        rest = [{"word": joined[1], "raw": head["raw"], "sub": head["of"] - 1,
                 "of": head["of"]}] + rest
    if not rest:
        return None
    verb, tail = rest[0], rest[1:]
    name = _fuzzy(verb["word"])
    if name is None:
        return None
    if COMMANDS[name]["argument"]:
        return _result(transcript, name, _argument(raw, verb, tail), "wake")
    if [t for t in tail if not _is_filler(t["word"])]:
        return None
    return _result(transcript, name, "", "wake")


def _argument(raw, verb, tail):
    """Everything said after the verb, taken verbatim from the raw tokens.

    The rare case first: the verb was not the last sub-word of its own raw
    token ("trail-tab-intro"), so the remainder of that token is recovered
    from the normalised sub-words - lowercased, which is the price of a
    spelling nobody actually says. Everything from the next raw token on is
    copied as the speaker said it.
    """
    parts = []
    if verb["sub"] + 1 < verb["of"]:
        parts.extend(t["word"] for t in tail if t["raw"] == verb["raw"])
    parts.extend(raw[verb["raw"] + 1:])
    while parts and _is_filler(normalise(parts[-1])[-1] if normalise(parts[-1]) else ""):
        parts.pop()
    return " ".join(parts).strip().rstrip(".،,!?؟؛;:").strip()


def decide(parsed, verdict=None):
    """Turn a parse and a second opinion into one action.

    ``verdict`` is the second opinion's answer AFTER its threshold was
    applied: "command", "text", or None when there was no answer (no key, no
    network, timeout). Only the ``argument`` form ever reads it.

    Returns ``{"action": "command"|"text", "command", "argument", "text",
    "reason"}``; for text, ``text`` is the whole transcript.

    Without a confident "command" the answer is text. A title read as a
    sentence costs one edit in the draft; a sentence read as a title closes
    the topic being dictated into, files half a thought, or opens a topic
    called "management is tricky".
    """
    transcript = parsed.get("transcript") or ""
    name = parsed.get("command")
    form = parsed.get("form")
    if not name:
        return {"action": "text", "command": None, "argument": "",
                "text": transcript, "reason": "not-a-command"}
    if form in CERTAIN_FORMS:
        return {"action": "command", "command": name,
                "argument": parsed.get("argument") or "", "text": "",
                "reason": form}
    if verdict == "command":
        return {"action": "command", "command": name,
                "argument": parsed.get("argument") or "", "text": "",
                "reason": "second-opinion"}
    reason = "second-opinion-text" if verdict == "text" else "no-opinion"
    return {"action": "text", "command": None, "argument": "",
            "text": transcript, "reason": reason}


def describe_grammar():
    """One row per command, for Settings and for the voice bar's help."""
    return [{"command": name, "say": spec["say"], "summary": spec["summary"],
             "argument": spec["argument"], "persian": spec["plain"][-1]}
            for name, spec in COMMANDS.items()]


# --- the draft --------------------------------------------------------------

def _join(a, b):
    """Append ``b`` to ``a`` the way dictation reads: one space between."""
    a = a or ""
    b = (b or "").strip()
    if not b:
        return a
    if not a or a.endswith((" ", "\n", "\t")):
        return a + b
    return a + " " + b


class Draft:
    """The one point being written - by voice, by hand, or both at once.

    Dictation appends to it, the keyboard edits it, "log" and the Log button
    file it. There is no separate voice buffer any more: what you said is
    text in a box, and you fix a misheard word the way you fix a typo.

    Written from the audio pipeline, the Win32 hotkey thread and the JS
    bridge, so every method takes the lock.

    Concurrent edits
    ----------------
    Every change bumps ``rev``. The window sends its whole text back with
    the ``rev`` it was editing (``set_text``). If nothing happened since,
    that is the new text. If dictation appended meanwhile, the appended
    pieces are re-applied after the edited text - so typing never erases a
    sentence that arrived while you typed. If the draft was logged or
    cleared meanwhile, only text typed onto the END of the logged draft is
    kept (it was not part of what was filed); an edit in the middle of text
    that is already filed is refused, and the window reloads.
    """

    #: A draft is one point. Past this, appends are refused rather than
    #: silently trimmed - the words are never dropped without being said so.
    MAX_CHARS = 100000
    MAX_SOURCES = 100
    #: How far back a window's ``rev`` may lag and still be merged.
    HISTORY = 64
    KINDS = ("", "claim", "note", "quote")

    def __init__(self):
        self._lock = threading.Lock()
        self._rev = 0
        self._text = ""
        self._origin = ""          # "" | "voice" | "hand"
        self._sources = []
        self._next_sid = 1
        self._meta = {"topic_id": "", "subtopic": "", "kind": ""}
        self._history = []         # (rev, op, piece, text_after)

    # -- writes --

    def _bump(self, op, piece=""):
        self._rev += 1
        self._history.append((self._rev, op, piece, self._text))
        del self._history[:-self.HISTORY]

    def append(self, text, origin="voice"):
        """Dictation lands here. Returns False only for empty text or a full draft."""
        text = str(text or "").strip()
        if not text:
            return False
        with self._lock:
            if len(self._text) + len(text) + 1 > self.MAX_CHARS:
                return False
            self._text = _join(self._text, text)
            if not self._origin:
                self._origin = origin
            elif self._origin != origin:
                self._origin = "hand"
            self._bump("append", text)
        return True

    def set_text(self, text, base_rev):
        """The window's edit. See the class docstring for the merge rules.

        Returns ``{"ok": True, "merged": bool, **snapshot}`` or
        ``{"ok": False, "reason": ..., **snapshot}``; either way the snapshot
        is what the window should now show.
        """
        text = str(text if text is not None else "")
        if len(text) > self.MAX_CHARS:
            with self._lock:
                return {"ok": False, "reason": "too long", **self._snapshot_locked()}
        try:
            base_rev = int(base_rev)
        except (TypeError, ValueError):
            base_rev = -1
        with self._lock:
            if base_rev == self._rev:
                return self._set_locked(text, merged=False)
            later = [h for h in self._history if h[0] > base_rev]
            # A rev older than the kept history cannot be merged: the ops
            # between it and now are no longer known.
            known = (any(h[0] == base_rev for h in self._history)
                     or (base_rev == 0 and (not self._history
                                            or self._history[0][0] == 1)))
            if base_rev > self._rev or not known or not later:
                return {"ok": False, "reason": "stale", **self._snapshot_locked()}
            ops = [h[1] for h in later]
            if "set" in ops or "restore" in ops:
                return {"ok": False, "reason": "stale", **self._snapshot_locked()}
            cut = max((i for i, op in enumerate(ops) if op in ("take", "clear")),
                      default=None)
            if cut is None:
                merged = text
                for h in later:
                    if h[1] == "append":
                        merged = _join(merged, h[2])
                return self._set_locked(merged, merged=True)
            base_text = self._text_at(base_rev)
            if base_text is None or not text.startswith(base_text):
                return {"ok": False, "reason": "logged", **self._snapshot_locked()}
            merged = text[len(base_text):].strip()
            for h in later[cut + 1:]:
                if h[1] == "append":
                    merged = _join(merged, h[2])
            return self._set_locked(merged, merged=True)

    def _text_at(self, rev):
        if rev == 0:
            return ""
        for h in self._history:
            if h[0] == rev:
                return h[3]
        return None

    def _set_locked(self, text, merged):
        if text != self._text:
            self._text = text
            self._origin = "hand" if text.strip() else ""
            self._bump("set")
        return {"ok": True, "merged": merged, **self._snapshot_locked()}

    def add_source(self, stype, value, note="", origin="voice"):
        """Add one source; returns its id, or 0 when it was not added.

        0 for an unusable type or empty value, and for a link or string
        already in the draft - saying "save" twice on the same clipboard
        should not cite it twice. Images are never deduplicated: two
        screenshots can differ by one pixel and still be two pieces of
        evidence.
        """
        stype = str(stype or "").strip()
        value = str(value or "").strip()
        if stype not in ("link", "string", "image") or not value:
            return 0
        with self._lock:
            if stype != "image":
                for s in self._sources:
                    if s["type"] == stype and s["value"] == value:
                        return 0
            if len(self._sources) >= self.MAX_SOURCES:
                return 0
            sid = self._next_sid
            self._next_sid += 1
            self._sources.append({"id": sid, "type": stype, "value": value,
                                  "note": str(note or "").strip(),
                                  "origin": origin})
            self._bump("source")
        return sid

    def drop_source(self, sid):
        """Remove one source by id. Hand-driven only - voice never removes.

        By id, not position: the window is working from a snapshot that a
        "save" may already have shifted, and a stale click must remove the
        chip that was clicked or nothing.
        """
        try:
            sid = int(sid)
        except (TypeError, ValueError):
            return {"ok": False, "reason": "bad id"}
        with self._lock:
            for i, s in enumerate(self._sources):
                if s["id"] == sid:
                    self._sources.pop(i)
                    self._bump("source")
                    return {"ok": True, **self._snapshot_locked()}
            return {"ok": False, "reason": "gone", **self._snapshot_locked()}

    def set_meta(self, fields):
        """Where the draft will be filed: topic, sub-topic, kind.

        Unknown keys are ignored and a kind outside KINDS is refused, so a
        window can send its whole form without this becoming a way to write
        arbitrary state.
        """
        fields = fields if isinstance(fields, dict) else {}
        with self._lock:
            changed = False
            for key in ("topic_id", "subtopic"):
                if key in fields:
                    v = str(fields[key] or "").strip()
                    if v != self._meta[key]:
                        self._meta[key] = v
                        changed = True
            if "kind" in fields:
                v = str(fields["kind"] or "").strip()
                if v in self.KINDS and v != self._meta["kind"]:
                    self._meta["kind"] = v
                    changed = True
            if changed:
                self._bump("meta")
            return self._snapshot_locked()

    def meta(self):
        with self._lock:
            return dict(self._meta)

    def take(self):
        """Drain for filing, and return everything - image data included.

        Where it goes (topic, sub-topic) survives; the kind does not, because
        it was a property of that one point.
        """
        with self._lock:
            out = {"text": self._text.strip(),
                   "origin": self._origin,
                   "sources": [{"type": s["type"], "value": s["value"],
                                "note": s["note"], "origin": s["origin"]}
                               for s in self._sources],
                   "meta": dict(self._meta),
                   "rev": self._rev}
            self._text = ""
            self._origin = ""
            self._sources = []
            self._meta["kind"] = ""
            self._bump("take")
        return out

    def restore(self, taken):
        """Put back what take() returned, because filing it failed.

        Take-then-file rather than read-then-file-then-drain: draining after
        the write would also drain a sentence that arrived during it, and
        that sentence was never filed. Whatever arrived meanwhile stays, after
        the restored text.
        """
        taken = taken if isinstance(taken, dict) else {}
        with self._lock:
            text = str(taken.get("text") or "")
            self._text = _join(text, self._text) if text else self._text
            if taken.get("origin") and self._origin and taken["origin"] != self._origin:
                self._origin = "hand"
            else:
                self._origin = self._origin or str(taken.get("origin") or "")
            back = []
            for s in taken.get("sources") or []:
                back.append({"id": self._next_sid, "type": s.get("type"),
                             "value": s.get("value"), "note": s.get("note") or "",
                             "origin": s.get("origin") or "voice"})
                self._next_sid += 1
            self._sources = (back + self._sources)[:self.MAX_SOURCES]
            kind = (taken.get("meta") or {}).get("kind") or ""
            if kind in self.KINDS and not self._meta["kind"]:
                self._meta["kind"] = kind
            self._bump("restore")

    def clear(self):
        with self._lock:
            self._text = ""
            self._origin = ""
            self._sources = []
            self._meta["kind"] = ""
            self._bump("clear")

    # -- reads --

    def is_empty(self):
        with self._lock:
            return not self._text.strip() and not self._sources

    def snapshot(self):
        """A read-only view for the windows. Never hands out image data -
        a screenshot is megabytes, and this travels on every push."""
        with self._lock:
            return self._snapshot_locked()

    def _snapshot_locked(self):
        text = self._text
        return {
            "rev": self._rev,
            "text": text,
            "origin": self._origin,
            "words": len(text.split()),
            "sources": [{"id": s["id"], "type": s["type"],
                         "value": "" if s["type"] == "image" else s["value"],
                         "note": s["note"], "origin": s["origin"]}
                        for s in self._sources],
            "count_sources": len(self._sources),
            "meta": dict(self._meta),
            "empty": not text.strip() and not self._sources,
        }
