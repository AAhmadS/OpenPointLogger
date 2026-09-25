"""Spoken command grammar for always-on voice, plus the buffer it fills.

Two pieces, both pure - no audio, no network, no store, no UI. That is
deliberate: the whole point of always-on voice is that it decides, many times
a minute, whether what you just said was an instruction or a thought, and a
decision made that often has to be testable without a microphone.

    match(text)    one transcript in, a command (or None) out
    VoiceBuffer    the comments and sources waiting to be logged

The grammar
-----------
Five commands, each a wake word followed by a verb::

    "Trail-Save"              attach whatever is on the clipboard as a source
    "Trail-Log"               log the buffered comments + sources as one point
    "Trail-Finish"            close the open topic
    "Trail-Session <title>"   start a new topic
    "Trail-Tab <name>"        add a sub-topic to the open topic

Removes are not spoken. Deleting by voice means a misheard word can destroy
work, and there is no undo in the store - so the destructive direction stays
on the mouse, where it is deliberate.

Why the whole utterance has to be the command
---------------------------------------------
A command fires only when the utterance contains *nothing but* the command
(plus the ignorable fillers in ``_FILLERS``, and an argument for the two
commands that take one). "trail log" is a command; "the trail logs are in the
folder" is a comment, and so is "trail log the sources" - because `log` takes
no argument and those words are not filler.

That rule costs the occasional missed command and buys something worth more:
you can talk about Trailmark while talking into Trailmark. The alternative -
matching a command anywhere in the sentence - means the sentence that
mentions it in passing silently closes your topic. Voice activity detection
already cuts on silence, so a command said on its own is its own utterance
anyway, which is how people say them in practice.

Why the matching is fuzzy
-------------------------
The transcript comes back from a speech model, not a keyboard. "Trail-Save"
arrives as "trail save", "trails save", "trail safe", "trial save",
"TrailSave", "تریل سیو", and worse. Every token is therefore matched by
Damerau-Levenshtein distance against a list of spellings that have a real
chance of turning up, with a threshold scaled to word length, and joined
forms ("traillog") are split before matching. Transposition counts as one
edit because "trail"/"trial" is the single most likely mangling of the wake
word and plain Levenshtein scores that as 2.

The tolerance is asymmetric on purpose: a missed command is a re-try, a false
command is lost work. The wake word carries the specificity - "lock" is
accepted for "log" only when "trail" precedes it.
"""

import re
import threading

__all__ = ["match", "normalise", "VoiceBuffer", "COMMANDS", "WAKE_WORDS",
           "describe_grammar"]


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
    "let's", "go", "do", "it", "the",
    "خب",            # khob
    "لطفا",  # lotfan
    "حالا",  # hala
    "خوب",      # khoob
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
#: because anybody says them.
WAKE_WORDS = [
    "trail", "trails", "trial", "trials", "trael", "treyl", "trale", "tale",
    "تریل",        # تریل
    "ترایل",  # ترایل
]

#: command -> what it does and how it is said. ``argument`` is True for the
#: two that name something; for the rest, trailing words mean it was a
#: sentence, not an instruction.
COMMANDS = {
    "save": {
        "verbs": ["save", "saved", "safe", "save's", "sav", "seve", "sev",
                  "سیو"],                      # سیو
        "argument": False,
        "summary": "attach the clipboard as a source",
    },
    "log": {
        "verbs": ["log", "logs", "logged", "logg", "lock", "locke", "lok",
                  "لاگ"],                      # لاگ
        "argument": False,
        "summary": "log the buffered comments and sources as one point",
    },
    "finish": {
        "verbs": ["finish", "finished", "finnish", "finis", "fenish", "finch",
                  "فینیش"],          # فینیش
        "argument": False,
        "summary": "close the open topic",
    },
    "session": {
        "verbs": ["session", "sessions", "sesion", "secession", "cession",
                  "sesh", "سشن"],              # سشن
        "argument": True,
        "summary": "start a new topic, optionally named",
    },
    "tab": {
        "verbs": ["tab", "tabs", "tap", "taps", "taab", "tad",
                  "تب"],                            # تب
        "argument": True,
        "summary": "add a sub-topic, optionally named",
    },
}


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
        for name, spec in COMMANDS.items():
            if _near(tail, spec["verbs"]):
                return head, tail
    return None


def match(text):
    """Classify one transcript.

    Returns ``{"command": <name|None>, "argument": str, "transcript": str}``.
    ``command`` is None for anything that is not an instruction - which is
    the common case, and means "treat this as a comment".
    """
    transcript = str(text or "").strip()
    raw, flat = _flatten(transcript)
    while flat and _is_filler(flat[0]["word"]):
        flat = flat[1:]
    if not flat:
        return {"command": None, "argument": "", "transcript": transcript}

    head, rest = flat[0], flat[1:]
    if not _near(head["word"], WAKE_WORDS):
        joined = _split_joined(head["word"])
        if joined is None:
            return {"command": None, "argument": "", "transcript": transcript}
        # The verb shares the wake word's raw token, and is its last sub-word:
        # everything after that token is argument.
        rest = [{"word": joined[1], "raw": head["raw"], "sub": head["of"] - 1,
                 "of": head["of"]}] + rest
    if not rest:
        return {"command": None, "argument": "", "transcript": transcript}

    verb, tail = rest[0], rest[1:]
    for name, spec in COMMANDS.items():
        if not _near(verb["word"], spec["verbs"]):
            continue
        if spec["argument"]:
            return {"command": name, "argument": _argument(raw, verb, tail),
                    "transcript": transcript}
        if [t for t in tail if not _is_filler(t["word"])]:
            # Words after a command that takes none: this was a sentence.
            break
        return {"command": name, "argument": "", "transcript": transcript}
    return {"command": None, "argument": "", "transcript": transcript}


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


def describe_grammar():
    """One line per command, for Settings and for the mini window's help."""
    pretty = {"save": "Trail-Save", "log": "Trail-Log", "finish": "Trail-Finish",
              "session": "Trail-Session", "tab": "Trail-Tab"}
    return [{"command": name, "say": pretty[name], "summary": spec["summary"],
             "argument": spec["argument"]}
            for name, spec in COMMANDS.items()]


# --- the buffer -------------------------------------------------------------

class VoiceBuffer:
    """What has been said and copied since the last Trail-Log.

    Written from the audio thread (a transcript arrived) and from the Win32
    hotkey thread (Ctrl+Alt+V), read from the pywebview JS-bridge thread (the
    mini window redrawing) - three threads, so every method takes the lock.

    ``take()`` drains and returns in one locked step. Draining separately
    from reading would let a transcript that landed between the two calls be
    logged into one point and then again into the next.
    """

    #: Comments beyond this are dropped oldest-first. A forgotten always-on
    #: session should not grow a single point to megabytes.
    MAX_COMMENTS = 200
    MAX_SOURCES = 100

    def __init__(self):
        self._lock = threading.Lock()
        self._comments = []
        self._sources = []

    def add_comment(self, text):
        text = str(text or "").strip()
        if not text:
            return False
        with self._lock:
            self._comments.append(text)
            del self._comments[:-self.MAX_COMMENTS]
        return True

    def add_source(self, stype, value, note=""):
        """Add one source. Returns False for an unusable type or empty value,
        and for a link or string already in the buffer - saying "Trail-Save"
        twice on the same clipboard should not cite it twice. Images are
        never deduplicated: two screenshots can differ by one pixel and still
        be two different pieces of evidence.
        """
        stype = str(stype or "").strip()
        value = str(value or "").strip()
        if stype not in ("link", "string", "image") or not value:
            return False
        with self._lock:
            if stype != "image":
                for s in self._sources:
                    if s["type"] == stype and s["value"] == value:
                        return False
            self._sources.append({"type": stype, "value": value,
                                  "note": str(note or "").strip()})
            del self._sources[:-self.MAX_SOURCES]
        return True

    def drop_comment(self, index):
        """Remove one buffered comment by position.

        Removes are hand-driven by design - never spoken. A misheard delete
        has no undo, and the store has no trash, so the destructive
        direction stays on the mouse where it takes a deliberate act.

        Out-of-range indexes answer False rather than raising: the UI is
        working from a snapshot that a new transcript may already have
        shifted under it, and a stale click should be a no-op, not a crash
        on the JS bridge thread.
        """
        return self._drop(self._comments, index)

    def drop_source(self, index):
        return self._drop(self._sources, index)

    def _drop(self, target, index):
        try:
            index = int(index)
        except (TypeError, ValueError):
            return {"ok": False, "reason": "bad index"}
        with self._lock:
            if index < 0 or index >= len(target):
                return {"ok": False, "reason": "out of range"}
            target.pop(index)
            return {"ok": True, **self._snapshot_locked()}

    def snapshot(self):
        """A read-only view for the UI. Never hands out the internal lists."""
        with self._lock:
            return self._snapshot_locked()

    def _snapshot_locked(self):
        comments = list(self._comments)
        return {
            "comments": comments,
            "sources": [dict(s) for s in self._sources],
            "text": " ".join(comments),
            "count_comments": len(comments),
            "count_sources": len(self._sources),
            "empty": not comments and not self._sources,
        }

    def take(self):
        """Drain, and return what was drained."""
        with self._lock:
            out = self._snapshot_locked()
            self._comments = []
            self._sources = []
        return out

    def clear(self):
        with self._lock:
            self._comments = []
            self._sources = []

    def is_empty(self):
        with self._lock:
            return not self._comments and not self._sources
