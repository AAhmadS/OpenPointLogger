"""Telegram bridge: bot-token transport, pure message classification, and the
polling bridge that turns a paired Telegram chat into a remote input for the
log.

Three independent pieces, deliberately decoupled so each is testable on its
own (mirrors asr.py's Vad / VoiceLogger / transcribe split):

- ``parse_dotenv`` / ``load_token``: pure text -> token resolution. No
  network, no Telegram API shape.
- ``classify_message``: a pure classifier from a Telegram ``message`` object
  into a small typed dict. No network, no state.
- ``UrllibTransport``: the only thing in this module that talks to
  api.telegram.org, via stdlib ``urllib`` (same pattern as llm.py/asr.py -
  no ``requests`` dependency). Every URL it builds is under the
  ``api.telegram.org`` host.
- ``TelegramBridge``: the polling orchestration. It never touches
  ``urllib`` itself - it is handed a transport object (``UrllibTransport``
  in production, a fake with the same three methods in tests) at
  construction, so ``handle_update`` can be driven directly in a test with
  zero real HTTP.

Token discipline: the bot token is never printed, logged, echoed into an
error message, or truncated-and-shown anywhere in this module. Errors from
the transport carry an HTTP status or a generic message, never the token or
the request URL's token segment.
"""

import base64
import json
import os
import re
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

API_HOST = "api.telegram.org"
MAX_FILE_BYTES = 8 * 1024 * 1024

#: Checked in this order against a discovered .env - the real key is
#: "TELEGROM_BOT" (misspelled, matched as-is), with the two "correctly"
#: spelled variants accepted too so a hand-fixed .env still works.
_ENV_KEYS = ("TELEGROM_BOT", "TELEGRAM_BOT", "TELEGRAM_BOT_TOKEN")

_URL_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.\-]*://\S+$")


# ---------------------------------------------------------------------------
# Token resolution
# ---------------------------------------------------------------------------

def parse_dotenv(text):
    """Parse KEY=VALUE lines from .env-style text into a dict.

    Pure and testable: takes text, not a path. Blank lines and lines
    starting with ``#`` are skipped; an optional leading ``export `` on the
    key side is stripped; a value wrapped in matching single or double
    quotes has the quotes stripped. Malformed lines (no ``=``) are ignored
    rather than raising.
    """
    out = {}
    for raw_line in (text or "").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):]
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in ("'", '"'):
            val = val[1:-1]
        if key:
            out[key] = val
    return out


def _env_search_dirs():
    """The three directories load_token searches for a .env, in order:
    the running executable's own folder, this module's folder, then the
    per-user Trailmark app-data folder. Duplicates (the common case when
    running from source, where argv[0] and this file share a folder) are
    not de-duplicated - reading the same non-existent or same-content file
    twice is harmless and keeps this a plain, auditable list.
    """
    dirs = []
    try:
        dirs.append(Path(sys.argv[0]).resolve().parent)
    except Exception:
        pass
    try:
        dirs.append(Path(__file__).resolve().parent)
    except Exception:
        pass
    appdata = os.environ.get("APPDATA")
    if appdata:
        dirs.append(Path(appdata) / "Trailmark")
    return dirs


def load_token(cfg):
    """Resolve the bot token to use right now.

    Returns ``(token, source)`` where ``source`` is ``"config"`` (a
    non-empty ``config.telegram.token``), ``"env"`` (found in a ``.env``
    file), or ``"none"`` (nothing configured anywhere). ``config.token``
    always wins when non-empty, so a user who has pasted a token into
    Settings is never silently overridden by a stray .env on disk.
    """
    cfg = cfg or {}
    token = str((cfg.get("telegram") or {}).get("token") or "").strip()
    if token:
        return token, "config"
    for d in _env_search_dirs():
        try:
            p = d / ".env"
            if not p.exists():
                continue
            data = parse_dotenv(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        for key in _ENV_KEYS:
            v = str(data.get(key) or "").strip()
            if v:
                return v, "env"
    return "", "none"


# ---------------------------------------------------------------------------
# Message classification (pure)
# ---------------------------------------------------------------------------

def classify_message(msg):
    """Classify one Telegram ``message`` object.

    Returns one of:
      {"type": "photo", "file_id": str, "caption": str}
      {"type": "command", "name": str, "args": str}
      {"type": "link", "url": str, "host": str}
      {"type": "text", "text": str}

    A photo always wins (a photo's own text lives in "caption", never
    "text"). A leading "/" is a command regardless of what follows -
    "/topic <name>" -> name="topic" args="<name>"; an "@botname" suffix on
    the command word (as Telegram sends in group chats) is stripped. A URL
    is detected either from a "url"/"text_link" entity or, failing that,
    from the whole message being a bare URL - a URL mentioned inside a
    longer sentence is deliberately left as plain text (matches clipboard.py's
    same "embedded URL stays text" rule).
    """
    msg = msg or {}
    photos = msg.get("photo")
    if isinstance(photos, list) and photos:
        largest = max(
            photos,
            key=lambda p: p.get("file_size") or (p.get("width", 0) * p.get("height", 0)),
        )
        return {"type": "photo", "file_id": largest.get("file_id"),
                "caption": str(msg.get("caption") or "")}

    text = str(msg.get("text") or "")

    if text.startswith("/"):
        body = text[1:]
        name, _, args = body.partition(" ")
        name = name.split("@", 1)[0].strip().lower()
        return {"type": "command", "name": name, "args": args.strip()}

    url = None
    for ent in (msg.get("entities") or []):
        etype = ent.get("type")
        if etype == "text_link" and ent.get("url"):
            url = ent["url"]
            break
        if etype == "url":
            off = int(ent.get("offset", 0))
            length = int(ent.get("length", 0))
            candidate = text[off:off + length]
            if candidate:
                url = candidate
                break
    if not url and _URL_RE.match(text.strip()):
        url = text.strip()

    if url:
        host = urlparse(url).netloc or url
        return {"type": "link", "url": url, "host": host}

    return {"type": "text", "text": text}


def _mime_for_filename(filename):
    ext = (filename or "").rsplit(".", 1)[-1].lower()
    return {
        "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
        "gif": "image/gif", "webp": "image/webp", "bmp": "image/bmp",
    }.get(ext, "image/jpeg")


# ---------------------------------------------------------------------------
# Transport
# ---------------------------------------------------------------------------

class TelegramApiError(Exception):
    """A Telegram Bot API call failed. ``status`` is the HTTP status code,
    or 0 for a transport-level failure (DNS, connect, timeout) that never
    got as far as a response."""

    def __init__(self, status, message=""):
        super().__init__(message or ("Telegram API HTTP %s" % status))
        self.status = status


class UrllibTransport:
    """The only thing in this module that makes a real network call, via
    stdlib ``urllib`` - mirrors the request/urlopen/HTTPError pattern in
    llm.py and asr.py, no third-party HTTP library. Every URL built here is
    under the ``api.telegram.org`` host; nothing else is ever contacted.
    The token is interpolated into the URL path (Telegram's own API shape)
    and never appears in a returned error.
    """

    def __init__(self, token):
        self._token = token

    def _request(self, req, timeout):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
        except urllib.error.HTTPError as e:
            raise TelegramApiError(e.code, "Telegram API returned HTTP %s" % e.code)
        except Exception as e:
            raise TelegramApiError(0, "Request failed: %s" % e)
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception as e:
            raise TelegramApiError(0, "Bad response: %s" % e)

    def get_updates(self, offset=0, timeout=25):
        """Long-poll for new updates. Socket timeout is 35s - 10s of slack
        over the 25s long-poll timeout asked of the server."""
        url = ("https://%s/bot%s/getUpdates?timeout=%d&offset=%d"
               "&allowed_updates=%%5B%%22message%%22%%5D") % (API_HOST, self._token, timeout, offset)
        req = urllib.request.Request(url, method="GET")
        data = self._request(req, timeout=35)
        return data.get("result") or []

    def send_message(self, chat_id, text):
        """Plain text only - no parse_mode is ever sent, so a stray
        Markdown/HTML special character in a topic title or a logged note
        can never be mis-parsed or break the request."""
        url = "https://%s/bot%s/sendMessage" % (API_HOST, self._token)
        body = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode("utf-8")
        req = urllib.request.Request(
            url, data=body, method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"})
        return self._request(req, timeout=20)

    def get_file_bytes(self, file_id):
        """getFile then download, capped at MAX_FILE_BYTES. Raises rather
        than silently truncating when the file is too large, so the caller
        can turn that into a reply instead of shipping a corrupt image."""
        url = "https://%s/bot%s/getFile" % (API_HOST, self._token)
        body = urllib.parse.urlencode({"file_id": file_id}).encode("utf-8")
        req = urllib.request.Request(
            url, data=body, method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"})
        data = self._request(req, timeout=20)
        file_path = ((data.get("result") or {}).get("file_path") or "").strip()
        if not file_path:
            raise TelegramApiError(0, "No file_path in getFile response")
        file_url = "https://%s/file/bot%s/%s" % (API_HOST, self._token, file_path)
        req2 = urllib.request.Request(file_url, method="GET")
        try:
            with urllib.request.urlopen(req2, timeout=30) as resp:
                raw = resp.read(MAX_FILE_BYTES + 1)
        except urllib.error.HTTPError as e:
            raise TelegramApiError(e.code, "File download returned HTTP %s" % e.code)
        except Exception as e:
            raise TelegramApiError(0, "File download failed: %s" % e)
        if len(raw) > MAX_FILE_BYTES:
            raise ValueError("Photo exceeds the 8MB size limit.")
        filename = file_path.rsplit("/", 1)[-1] or "photo.jpg"
        return raw, filename


# ---------------------------------------------------------------------------
# Bridge
# ---------------------------------------------------------------------------

class TelegramBridge:
    """Polls getUpdates on a daemon thread and turns paired-chat messages
    into calls back into point_logger.

    Construction:
      transport         - an UrllibTransport (or, in tests, a fake with the
                           same get_updates/send_message/get_file_bytes shape).
      get_cfg()         - returns the live config dict (same shape as
                           Store.config, unmasked - this runs inside the
                           desktop process, never over the JS bridge).
      save_cfg(updates) - merges ``updates`` (a dict of the fields that
                           changed: chat_id/username on pairing,
                           topic_id on a /topic switch) into
                           config["telegram"] and persists it. Kept as a
                           narrow merge callback rather than handing this
                           class the whole Store, so it has no dependency on
                           point_store's shape beyond the "telegram" section.
      on_state(state, detail) - mirrors push_asr_state's contract: called on
                           every state transition ("error", ...). Never
                           receives the token as detail.
      on_message(kind, payload) - called for a non-command message from the
                           paired chat. ``kind`` is "note"/"link"/"photo".
                           May return a reply string, which is sent back to
                           the chat as-is; returning None/"" sends nothing.
                           This is where point_logger resolves the target
                           topic and calls store.add_entry - kept out of
                           this module so TelegramBridge has no dependency
                           on point_store at all.
      get_open_topics() - returns currently-open topics as
                           [{"id": ..., "title": ...}, ...], for /topic
                           matching. Optional; defaults to "no open topics"
                           if not given.

    ``handle_update`` is pure with respect to the network - it only ever
    calls the injected transport - so a test can drive it directly with a
    fake transport and assert on recorded send_message calls / on_message
    calls, with zero real HTTP.
    """

    def __init__(self, transport, get_cfg, save_cfg, on_state, on_message, get_open_topics=None):
        self._transport = transport
        self._get_cfg = get_cfg
        self._save_cfg = save_cfg
        self._on_state = on_state
        self._on_message = on_message
        self._get_open_topics = get_open_topics or (lambda: [])
        self._stop_event = threading.Event()
        self._thread = None
        self._offset = 0
        # Chat ids already told "not paired", this bridge instance only -
        # cleared by restarting the bridge (apply_telegram stop/start), so a
        # stray sender is not nagged forever but also not nagged on every
        # single message in one session.
        self._warned_chat_ids = set()

    # -- lifecycle ----------------------------------------------------------

    def start(self):
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        t = self._thread
        if t is not None:
            t.join(timeout=5)
        self._thread = None

    def _safe_state(self, state, detail=""):
        try:
            self._on_state(state, detail)
        except Exception:
            pass

    def _run(self):
        backoff = 1
        while not self._stop_event.is_set():
            try:
                updates = self._transport.get_updates(offset=self._offset, timeout=25)
            except TelegramApiError as e:
                if e.status in (401, 404):
                    self._safe_state("error", "Token rejected")
                    return
                self._safe_state("error", "Telegram connection error")
                if self._stop_event.wait(backoff):
                    return
                backoff = min(30, backoff * 2)
                continue
            except Exception:
                self._safe_state("error", "Telegram connection error")
                if self._stop_event.wait(backoff):
                    return
                backoff = min(30, backoff * 2)
                continue

            backoff = 1
            for update in updates:
                try:
                    self._offset = max(self._offset, int(update.get("update_id", 0)) + 1)
                except Exception:
                    pass
                if self._stop_event.is_set():
                    return
                try:
                    self.handle_update(update)
                except Exception:
                    self._safe_state("error", "Error handling a Telegram message")
            if self._stop_event.is_set():
                return

    # -- pure(ish) update handling -------------------------------------------

    def _reply(self, chat_id, text):
        try:
            self._transport.send_message(chat_id, text)
        except Exception:
            pass

    @staticmethod
    def _topic_list_text(topics):
        titles = [t.get("title", "") for t in (topics or []) if t.get("title")]
        return ", ".join(titles) if titles else "(none open)"

    @staticmethod
    def _help_text():
        return ("Commands: send text, a link, or a photo to log a point, or "
                "/topic <name> to switch which open topic new points go to.")

    def _handle_topic_command(self, chat_id, args):
        name = (args or "").strip()
        topics = self._get_open_topics() or []
        if not name:
            self._reply(chat_id, "Usage: /topic <name>. Open topics: %s" % self._topic_list_text(topics))
            return
        match = next((t for t in topics if (t.get("title") or "").strip().lower() == name.lower()), None)
        if not match:
            self._reply(chat_id, "No open topic named '%s'. Open topics: %s"
                        % (name, self._topic_list_text(topics)))
            return
        self._save_cfg({"topic_id": match.get("id")})
        self._reply(chat_id, "Switched to topic '%s'." % match.get("title", ""))

    def _deliver(self, kind, payload, chat_id):
        try:
            reply_text = self._on_message(kind, payload)
        except Exception:
            self._safe_state("error", "on_message handler failed")
            return
        if reply_text:
            self._reply(chat_id, reply_text)

    def _handle_photo(self, classified, chat_id):
        file_id = classified.get("file_id")
        caption = (classified.get("caption") or "").strip()
        try:
            raw, filename = self._transport.get_file_bytes(file_id)
        except ValueError:
            self._reply(chat_id, "That photo is too large (over 8MB) to log.")
            return
        except Exception:
            self._reply(chat_id, "Could not download that photo.")
            return
        mime = _mime_for_filename(filename)
        data_url = "data:%s;base64,%s" % (mime, base64.b64encode(raw).decode("ascii"))
        text = caption or "Telegram photo"
        payload = {"sources": [{"type": "image", "value": data_url}], "text": text}
        self._deliver("photo", payload, chat_id)

    def handle_update(self, update):
        """Handle one Telegram update. Pure with respect to the network in
        the sense that it only ever calls out through ``self._transport``
        (injected) - a test drives this directly with a fake transport.
        """
        message = (update or {}).get("message")
        if not message:
            return
        chat = message.get("chat") or {}
        chat_id = chat.get("id")
        frm = message.get("from") or {}
        username = str(frm.get("username") or "")
        classified = classify_message(message)

        cfg = self._get_cfg() or {}
        tg_cfg = cfg.get("telegram") or {}
        pairing_code = str(tg_cfg.get("pairing_code") or "")
        paired_chat_id = tg_cfg.get("chat_id")

        if classified["type"] == "command" and classified["name"] == "start":
            code = classified.get("args") or ""
            if pairing_code and code == pairing_code:
                self._save_cfg({"chat_id": chat_id, "username": username})
                self._reply(chat_id, "Paired with this desktop ✓ — send me text, links or photos.")
            else:
                self._reply(chat_id, "Pairing code didn't match. Open Trailmark → Settings → "
                                     "Telegram and send /start <code>.")
            return

        if paired_chat_id is None or chat_id != paired_chat_id:
            if chat_id not in self._warned_chat_ids:
                self._warned_chat_ids.add(chat_id)
                self._reply(chat_id, "This desktop is not paired with you.")
            return

        if classified["type"] == "command":
            if classified["name"] == "topic":
                self._handle_topic_command(chat_id, classified.get("args") or "")
            else:
                self._reply(chat_id, self._help_text())
            return

        if classified["type"] == "text":
            self._deliver("note", {"text": classified["text"]}, chat_id)
        elif classified["type"] == "link":
            self._deliver("link", {"source_link": classified["url"], "text": classified["host"]}, chat_id)
        elif classified["type"] == "photo":
            self._handle_photo(classified, chat_id)
