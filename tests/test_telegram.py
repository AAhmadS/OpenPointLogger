"""Headless tests for telegram_bridge.py (pairing, classification, message
routing) and point_logger.Controller's on_telegram_message wiring.

Every check here drives telegram_bridge.TelegramBridge.handle_update()
directly against a small in-memory FakeTransport - no real UrllibTransport
is ever constructed, no real .env is ever touched, and nothing here talks
to a real network. Mirrors test_asr.py's mock-server / direct-call split:
transport-level behaviour is faked, the pure classifier and the bridge's
routing logic are exercised for real.

Run:  PYTHONPATH=. .venv/Scripts/python.exe tests/test_telegram.py
"""

import base64
import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

# Unlike the other tests/test_*.py scripts, the strings under test here are
# real bot reply text and legitimately contain non-ASCII (a checkmark, arrows
# in the pairing prompt) - printed straight to stdout that can crash on a
# non-UTF-8 Windows console codepage. errors="backslashreplace" makes that
# merely cosmetic instead of a spurious test failure.
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(errors="backslashreplace")
    except Exception:
        pass

import telegram_bridge  # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + name + ((" - " + str(detail)) if detail else ""))
    if not cond:
        FAILS.append(name)


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

class FakeTransport:
    """Implements the same three methods UrllibTransport does. Never opens
    a socket - send_message just records, get_file_bytes returns canned
    bytes keyed by file_id. get_updates is not needed here: every check
    drives handle_update() directly rather than running the poll loop."""

    def __init__(self):
        self.sent = []  # [(chat_id, text), ...]
        self.files = {}  # file_id -> (bytes, filename)

    def send_message(self, chat_id, text):
        self.sent.append((chat_id, text))

    def get_file_bytes(self, file_id):
        return self.files.get(file_id, (b"", "photo.jpg"))

    def get_updates(self, offset=0, timeout=25):  # pragma: no cover - unused
        return []


def _msg(chat_id, username="", **fields):
    m = {"chat": {"id": chat_id}, "from": {"username": username}}
    m.update(fields)
    return m


def _update(msg):
    return {"update_id": 1, "message": msg}


def make_bridge(cfg, transport=None, on_message=None, open_topics=None):
    transport = transport or FakeTransport()
    on_state_calls = []
    on_message_calls = []

    def on_state(state, detail):
        on_state_calls.append((state, detail))

    def default_on_message(kind, payload):
        on_message_calls.append((kind, payload))
        return None

    bridge = telegram_bridge.TelegramBridge(
        transport,
        get_cfg=lambda: cfg,
        save_cfg=lambda updates: cfg.setdefault("telegram", {}).update(updates or {}),
        on_state=on_state,
        on_message=on_message or default_on_message,
        get_open_topics=(lambda: open_topics) if open_topics is not None else None,
    )
    return bridge, transport, on_state_calls, on_message_calls


def _last_sent_to(transport, chat_id):
    for cid, text in reversed(transport.sent):
        if cid == chat_id:
            return text
    return None


def _sent_count_to(transport, chat_id):
    return sum(1 for cid, _ in transport.sent if cid == chat_id)


# ---------------------------------------------------------------------------
# 1. Pairing
# ---------------------------------------------------------------------------

cfg1 = {"telegram": {"pairing_code": "ABCDEF", "chat_id": None, "username": ""}}
bridge1, t1, states1, msgs1 = make_bridge(cfg1, open_topics=[])

bridge1.handle_update(_update(_msg(100, username="alice", text="/start WRONGCODE")))
check("wrong pairing code gets the no-match reply",
      "didn't match" in (_last_sent_to(t1, 100) or ""), _last_sent_to(t1, 100))
check("wrong pairing code does not set chat_id", cfg1["telegram"].get("chat_id") is None)

bridge1.handle_update(_update(_msg(100, username="alice", text="/start ABCDEF")))
check("right pairing code gets the paired reply",
      "Paired with this desktop" in (_last_sent_to(t1, 100) or ""), _last_sent_to(t1, 100))
check("right pairing code sets chat_id", cfg1["telegram"].get("chat_id") == 100)
check("right pairing code sets username", cfg1["telegram"].get("username") == "alice")

# re-pairing from a second, different chat is fine
bridge1.handle_update(_update(_msg(200, username="bob", text="/start ABCDEF")))
check("re-pairing from a different chat updates chat_id", cfg1["telegram"].get("chat_id") == 200)
check("re-pairing updates username", cfg1["telegram"].get("username") == "bob")

# a non-start message from an unpaired chat (300) gets "not paired", once
bridge1.handle_update(_update(_msg(300, username="eve", text="hello there")))
bridge1.handle_update(_update(_msg(300, username="eve", text="hello again")))
check("unpaired chat gets exactly one 'not paired' reply",
      _sent_count_to(t1, 300) == 1, t1.sent)
check("'not paired' reply text",
      "not paired" in (_last_sent_to(t1, 300) or "").lower(), _last_sent_to(t1, 300))
check("unpaired chat's messages never reach on_message", len(msgs1) == 0, msgs1)


# ---------------------------------------------------------------------------
# 2. Text message from the paired chat
# ---------------------------------------------------------------------------

cfg2 = {"telegram": {"pairing_code": "ZZZ111", "chat_id": 555, "username": "carol"}}
bridge2, t2, states2, msgs2 = make_bridge(cfg2, open_topics=[])

bridge2.handle_update(_update(_msg(555, username="carol", text="a plain note about something")))
check("exactly one on_message call for a text message", len(msgs2) == 1, msgs2)
if msgs2:
    kind, payload = msgs2[0]
    check("text message routes with kind 'note'", kind == "note", kind)
    check("text payload carries the message text",
          payload.get("text") == "a plain note about something", payload)


# ---------------------------------------------------------------------------
# 3. URL message
# ---------------------------------------------------------------------------

cfg3 = {"telegram": {"pairing_code": "URLURL", "chat_id": 555, "username": "carol"}}
bridge3, t3, states3, msgs3 = make_bridge(cfg3, open_topics=[])

bridge3.handle_update(_update(_msg(555, text="https://github.com/x")))
check("exactly one on_message call for a URL message", len(msgs3) == 1, msgs3)
if msgs3:
    kind, payload = msgs3[0]
    check("URL message routes with kind 'link'", kind == "link", kind)
    check("link payload carries the URL", payload.get("source_link") == "https://github.com/x", payload)
    check("link payload's text is the host", payload.get("text") == "github.com", payload)


# ---------------------------------------------------------------------------
# 4. Photo, with and without a caption
# ---------------------------------------------------------------------------

cfg4 = {"telegram": {"pairing_code": "PICPIC", "chat_id": 555, "username": "carol"}}
bridge4, t4, states4, msgs4 = make_bridge(cfg4, open_topics=[])
photo_bytes = b"\x89PNG\r\n\x1a\n" + b"not-a-real-png-just-test-bytes"
t4.files["file-with-caption"] = (photo_bytes, "photo.jpg")
t4.files["file-no-caption"] = (photo_bytes, "photo.png")

bridge4.handle_update(_update(_msg(
    555, photo=[{"file_id": "file-with-caption", "width": 90, "height": 90, "file_size": 900},
               {"file_id": "small", "width": 10, "height": 10, "file_size": 10}],
    caption="a labelled photo")))
check("photo with caption produced exactly one on_message call", len(msgs4) == 1, msgs4)
if msgs4:
    kind, payload = msgs4[0]
    check("photo message routes with kind 'photo'", kind == "photo", kind)
    check("photo payload text is the caption", payload.get("text") == "a labelled photo", payload)
    sources = payload.get("sources") or []
    check("photo payload carries one image source", len(sources) == 1, sources)
    if sources:
        expected_url = "data:image/jpeg;base64," + base64.b64encode(photo_bytes).decode("ascii")
        check("photo data URL matches the downloaded bytes", sources[0].get("value") == expected_url)
        check("photo source type is 'image'", sources[0].get("type") == "image", sources[0])

bridge4.handle_update(_update(_msg(
    555, photo=[{"file_id": "file-no-caption", "width": 50, "height": 50, "file_size": 500}])))
check("photo without caption produced a second on_message call", len(msgs4) == 2, msgs4)
if len(msgs4) == 2:
    _kind, payload_nc = msgs4[1]
    check("photo without caption falls back to 'Telegram photo'",
          payload_nc.get("text") == "Telegram photo", payload_nc)


# ---------------------------------------------------------------------------
# 5. /topic command
# ---------------------------------------------------------------------------

cfg5 = {"telegram": {"pairing_code": "TOPTOP", "chat_id": 555, "username": "carol"}}
open_topics_5 = [{"id": "t-rust", "title": "Rust borrow checker"},
                  {"id": "t-ml", "title": "ML papers"}]
bridge5, t5, states5, msgs5 = make_bridge(cfg5, open_topics=open_topics_5)

bridge5.handle_update(_update(_msg(555, text="/topic rust BORROW checker")))
check("case-insensitive /topic match switches topic_id",
      cfg5["telegram"].get("topic_id") == "t-rust", cfg5["telegram"])
check("/topic match gets a confirmation reply",
      "Switched" in (_last_sent_to(t5, 555) or ""), _last_sent_to(t5, 555))

bridge5.handle_update(_update(_msg(555, text="/topic nonexistent topic name")))
check("/topic with no match does not change topic_id",
      cfg5["telegram"].get("topic_id") == "t-rust", cfg5["telegram"])
no_match_reply = _last_sent_to(t5, 555) or ""
check("/topic with no match lists open topic titles",
      "Rust borrow checker" in no_match_reply and "ML papers" in no_match_reply, no_match_reply)


# ---------------------------------------------------------------------------
# 6. Unknown command
# ---------------------------------------------------------------------------

cfg6 = {"telegram": {"pairing_code": "HLPHLP", "chat_id": 555, "username": "carol"}}
bridge6, t6, states6, msgs6 = make_bridge(cfg6, open_topics=[])

try:
    bridge6.handle_update(_update(_msg(555, text="/bogus something")))
    unknown_ok = True
except Exception as e:
    unknown_ok = False
    unknown_err = e
check("unknown command does not raise", unknown_ok, locals().get("unknown_err"))
help_reply = _last_sent_to(t6, 555) or ""
check("unknown command gets a non-empty help reply", bool(help_reply.strip()), help_reply)
check("unknown command never reaches on_message", len(msgs6) == 0, msgs6)


# ---------------------------------------------------------------------------
# 7. No open topic - tested at point_logger's on_telegram_message layer,
# since that is where topic resolution and the "no open topic" reply live
# (telegram_bridge.py itself never resolves topics - see its on_message
# docstring). Mirrors test_asr.py's temp-APPDATA Store isolation pattern.
# ---------------------------------------------------------------------------

import point_store as ps  # noqa: E402

tmp = pathlib.Path(tempfile.mkdtemp(prefix="opl_test_tg_"))
ps.BASE_DIR = tmp
ps.DATA_FILE = tmp / "points.json"
ps.CONFIG_FILE = tmp / "config.json"
ps.ATTACH_DIR = tmp / "attachments"
ps.EXPORT_DIR = tmp / "exports"

import point_logger  # noqa: E402

c = point_logger.Controller()
check("no topics exist yet", c.store.last_open_topic() is None)

reply = c.on_telegram_message("note", {"text": "should not be logged"})
check("on_telegram_message with no open topic returns the expected reply",
      reply == "No open topic on the desktop — start one first", reply)
check("no entry was created anywhere", all(not t.get("entries") for t in c.store._topics))

r = c.store.start_topic("A telegram-fed topic")
tid = r["topics"][0]["id"]
reply2 = c.on_telegram_message("note", {"text": "now this should log"})
check("on_telegram_message logs once a topic is open",
      reply2 == "Logged to 'A telegram-fed topic'", reply2)
t = c.store.find_topic(tid)
entries = t.get("entries", []) if t else []
check("exactly one entry was logged", len(entries) == 1, len(entries))
if entries:
    check("logged entry text matches", entries[0].get("text") == "now this should log", entries[0])
    check("logged entry kind is 'note'", entries[0].get("kind") == "note", entries[0].get("kind"))


# ---------------------------------------------------------------------------
# 8. parse_dotenv
# ---------------------------------------------------------------------------

dotenv_text = "\n".join([
    "# a comment line",
    "",
    "export TELEGROM_BOT=DUMMY-VALUE-123",
    "OTHER_KEY=\"quoted value\"",
])
parsed = telegram_bridge.parse_dotenv(dotenv_text)
check("parse_dotenv reads the misspelled key",
      parsed.get("TELEGROM_BOT") == "DUMMY-VALUE-123", parsed)
check("parse_dotenv strips a leading 'export '", "TELEGROM_BOT" in parsed, parsed)
check("parse_dotenv strips matching quotes", parsed.get("OTHER_KEY") == "quoted value", parsed)
check("parse_dotenv skips comment lines", "# a comment line" not in parsed, parsed)


# ---------------------------------------------------------------------------
# 9. Store.state() never leaks the token
# ---------------------------------------------------------------------------

import json as _json  # noqa: E402

secret_marker = "FAKE-NOT-A-REAL-TOKEN-abcdef123456"
c.store.config["telegram"]["token"] = secret_marker
state = c.store.state()
check("state()'s telegram section reports token_set=True",
      state["config"]["telegram"].get("token_set") is True, state["config"]["telegram"])
check("state()'s telegram section masks the token itself",
      state["config"]["telegram"].get("token") == "", state["config"]["telegram"])
dumped = _json.dumps(state)
check("the real token string never appears anywhere in json.dumps(state)",
      secret_marker not in dumped)
check("the live config dict itself was not mutated by state()",
      c.store.config["telegram"]["token"] == secret_marker)


print()
print("ALL CHECKS PASSED" if not FAILS else "FAILED: " + ", ".join(FAILS))
sys.exit(1 if FAILS else 0)
