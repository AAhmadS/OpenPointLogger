"""Headless tests for asr.py (VAD, transcribe()) and point_logger.Controller
wiring (_log_asr_text).

Three independent checks, each runnable without a microphone, sounddevice,
or network:

1. asr.Vad driven with synthetic int16 PCM frames (silence + a tone burst).
2. asr.transcribe() against a local mock HTTP server (mirrors test_llm.py's
   http.server pattern), plus its error path against a closed port.
3. point_logger.Controller._log_asr_text() against a temp-APPDATA Store with
   one open topic (mirrors test_store.py's isolation pattern).

Run:  PYTHONPATH=. .venv/Scripts/python.exe tests/test_asr.py
"""

import io
import json
import math
import pathlib
import socket
import struct
import sys
import tempfile
import threading
import wave
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

FAILS = []


def check(name, cond, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + name + ((" - " + str(detail)) if detail else ""))
    if not cond:
        FAILS.append(name)


# ---------------------------------------------------------------------------
# 1. Vad on synthetic frames
# ---------------------------------------------------------------------------
# asr.py's Vad.feed docstring documents ~30ms frames at 16kHz mono int16 as
# 480 samples / 960 bytes per call - used as-is here.

import asr  # noqa: E402

SAMPLERATE = 16000
FRAME_SAMPLES = 480
FRAME_BYTES = FRAME_SAMPLES * 2  # 960
FRAME_MS = 30.0


def _silence_frame():
    return b"\x00\x00" * FRAME_SAMPLES


def _tone_frames(seconds, freq=440.0, amplitude=10000, phase0=0.0):
    """Yield ~30ms frames of a sine tone, well above the sensitivity=50
    threshold (1100), tracking phase continuously across frame boundaries."""
    total_samples = int(seconds * SAMPLERATE)
    samples = []
    for n in range(total_samples):
        t = n / SAMPLERATE
        v = int(amplitude * math.sin(2 * math.pi * freq * t + phase0))
        samples.append(v)
    frames = []
    for i in range(0, len(samples), FRAME_SAMPLES):
        chunk = samples[i:i + FRAME_SAMPLES]
        if len(chunk) < FRAME_SAMPLES:
            chunk = chunk + [0] * (FRAME_SAMPLES - len(chunk))
        frames.append(struct.pack("<%dh" % len(chunk), *chunk))
    return frames


# -- silence case: every feed() call returns None ---------------------------
vad_silence = asr.Vad(samplerate=SAMPLERATE, sensitivity=50)
silence_frame = _silence_frame()
num_silence_frames = int(2000 / FRAME_MS)  # ~2 seconds
silence_results = [vad_silence.feed(silence_frame) for _ in range(num_silence_frames)]
check("silence never emits an utterance",
      all(r is None for r in silence_results),
      "non-None at index %s" % ([i for i, r in enumerate(silence_results) if r is not None][:3]))

# -- tone-burst case: exactly one utterance emitted, and it's a valid WAV ---
vad_tone = asr.Vad(samplerate=SAMPLERATE, sensitivity=50)
pre_silence = [silence_frame] * int(500 / FRAME_MS)      # ~0.5s
tone = _tone_frames(1.0)                                  # ~1.0s @ 440Hz, amp 10000
post_silence = [silence_frame] * int(1500 / FRAME_MS)     # ~1.5s

all_frames = pre_silence + tone + post_silence
utterances = []
for f in all_frames:
    out = vad_tone.feed(f)
    if out is not None:
        utterances.append(out)

check("exactly one utterance emitted for one tone burst", len(utterances) == 1, len(utterances))

if utterances:
    wav_bytes = utterances[0]
    try:
        with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
            check("utterance WAV opens cleanly", True)
            check("utterance WAV framerate is 16000", wf.getframerate() == 16000, wf.getframerate())
            check("utterance WAV is mono", wf.getnchannels() == 1, wf.getnchannels())
            check("utterance WAV is 16-bit (sampwidth=2)", wf.getsampwidth() == 2, wf.getsampwidth())
    except Exception as e:
        check("utterance WAV opens cleanly", False, e)
        check("utterance WAV framerate is 16000", False, "n/a")
        check("utterance WAV is mono", False, "n/a")
        check("utterance WAV is 16-bit (sampwidth=2)", False, "n/a")
else:
    check("utterance WAV opens cleanly", False, "no utterance emitted")
    check("utterance WAV framerate is 16000", False, "no utterance emitted")
    check("utterance WAV is mono", False, "no utterance emitted")
    check("utterance WAV is 16-bit (sampwidth=2)", False, "no utterance emitted")


# ---------------------------------------------------------------------------
# 2. transcribe() against a mock HTTP server
# ---------------------------------------------------------------------------

captured = {}


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        captured["path"] = self.path
        captured["auth"] = self.headers.get("Authorization")
        captured["body_has_model_field"] = b'name="model"' in raw
        captured["body_has_file_field"] = b'name="file"' in raw
        resp = json.dumps({"text": "hello"}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(resp)))
        self.end_headers()
        self.wfile.write(resp)

    def log_message(self, *args):
        pass


server = HTTPServer(("127.0.0.1", 0), Handler)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
port = server.server_address[1]

# a tiny real WAV, reused from the tone-burst utterance above if available,
# else a hand-built 1-frame silent WAV
test_wav_bytes = utterances[0] if utterances else asr._pcm_to_wav(silence_frame, SAMPLERATE)

cfg = {
    "endpoint": "http://127.0.0.1:%d" % port,
    "model": "whisper-1",
    "api_key": "test-key-456",
    "language": "",
}

result = asr.transcribe(cfg, test_wav_bytes)
check("transcribe() returns mock text", result.get("text") == "hello", result)
check("request path ends with /audio/transcriptions",
      (captured.get("path") or "").endswith("/audio/transcriptions"), captured.get("path"))
check("Authorization header is Bearer test-key-456",
      captured.get("auth") == "Bearer test-key-456", captured.get("auth"))
check("multipart body contains model field", captured.get("body_has_model_field") is True)
check("multipart body contains file field", captured.get("body_has_file_field") is True)

server.shutdown()

# -- error path: unreachable endpoint (closed port) must not raise ---------
_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
_s.bind(("127.0.0.1", 0))
closed_port = _s.getsockname()[1]
_s.close()  # nothing listens on this port now

cfg_bad = dict(cfg, endpoint="http://127.0.0.1:%d" % closed_port)
try:
    err_result = asr.transcribe(cfg_bad, test_wav_bytes)
    check("transcribe() against a closed port does not raise", True)
    check("transcribe() against a closed port returns a non-empty error",
          bool(err_result.get("error")), err_result)
except Exception as e:
    check("transcribe() against a closed port does not raise", False, e)
    check("transcribe() against a closed port returns a non-empty error", False, "n/a")


# ---------------------------------------------------------------------------
# 3. Controller._log_asr_text wiring, against a temp-APPDATA Store
# ---------------------------------------------------------------------------

import point_store as ps  # noqa: E402

tmp = pathlib.Path(tempfile.mkdtemp(prefix="opl_test_"))
ps.BASE_DIR = tmp
ps.DATA_FILE = tmp / "points.json"
ps.CONFIG_FILE = tmp / "config.json"
ps.ATTACH_DIR = tmp / "attachments"
ps.EXPORT_DIR = tmp / "exports"

import point_logger  # noqa: E402

c = point_logger.Controller()
r = c.store.start_topic("Test topic")
check("start_topic did not error", not r.get("error"), r)
tid = r["topics"][0]["id"]

try:
    c._log_asr_text("This is a transcribed sentence.")
    check("_log_asr_text() with an open topic does not raise", True)
except Exception as e:
    check("_log_asr_text() with an open topic does not raise", False, e)

t = c.store.find_topic(tid)
entries = t.get("entries", []) if t else []
check("exactly one entry was logged", len(entries) == 1, len(entries))
if entries:
    check("logged entry text matches", entries[0].get("text") == "This is a transcribed sentence.",
          entries[0].get("text"))
    check("logged entry kind is 'note'", entries[0].get("kind") == "note", entries[0].get("kind"))
else:
    check("logged entry text matches", False, "no entry")
    check("logged entry kind is 'note'", False, "no entry")

# -- no-open-topic path: closing the topic must suppress further logging --
close_r = c.store.close_topic(tid)
check("close_topic did not error", not close_r.get("error"), close_r)

try:
    c._log_asr_text("should not be logged")
    check("_log_asr_text() with no open topic does not raise", True)
except Exception as e:
    check("_log_asr_text() with no open topic does not raise", False, e)

t2 = c.store.find_topic(tid)
entries2 = t2.get("entries", []) if t2 else []
check("no new entry created once the topic is closed", len(entries2) == 1, len(entries2))

# ---------------------------------------------------------------------------
# 4. The hosted-ASR default is OpenRouter, in all three places it is written
# ---------------------------------------------------------------------------
# The owner picked OpenRouter for both LLM and ASR so one key covers both. The
# endpoint default is spelled out three times - the shipped config, the
# transcribe() fallback, and the settings-save fallback - and a stale copy is
# silent: the user only finds out when their OpenRouter key is rejected by
# OpenAI. One of the three was in fact missed on the first pass, which is why
# this check exists.

OPENROUTER = "https://openrouter.ai/api/v1"

check("DEFAULT_CONFIG['asr']['endpoint'] is OpenRouter",
      ps.DEFAULT_CONFIG["asr"]["endpoint"] == OPENROUTER,
      ps.DEFAULT_CONFIG["asr"]["endpoint"])
check("DEFAULT_CONFIG['asr']['model'] is whisper-1",
      ps.DEFAULT_CONFIG["asr"]["model"] == "whisper-1",
      ps.DEFAULT_CONFIG["asr"]["model"])

# transcribe() with no endpoint must not reach out to anyone but OpenRouter.
# It is given an empty cfg and a 1-byte wav, so it fails at the network, but
# the URL it failed against is the thing under test.
probe = {}
_orig_urlopen = asr.urllib.request.urlopen


def _capture(req, *a, **kw):
    probe["url"] = req.full_url if hasattr(req, "full_url") else str(req)
    raise OSError("blocked by test")


asr.urllib.request.urlopen = _capture
try:
    asr.transcribe({}, b"RIFF....WAVEfmt ")
except Exception as e:
    probe["raised"] = repr(e)
finally:
    asr.urllib.request.urlopen = _orig_urlopen
check("transcribe() with an empty cfg targets OpenRouter",
      probe.get("url", "").startswith(OPENROUTER),
      probe.get("url") or probe.get("raised"))

# save_asr() with a cleared endpoint field must fall back to OpenRouter, not
# to whichever provider was hard-coded first.
api = point_logger.Api(c.store, c)
try:
    api.save_asr({"enabled": False, "endpoint": "", "model": ""})
    saved = c.store.config.get("asr", {})
    check("save_asr('') falls back to OpenRouter",
          saved.get("endpoint") == OPENROUTER, saved.get("endpoint"))
    check("save_asr('') falls back to whisper-1",
          saved.get("model") == "whisper-1", saved.get("model"))
except Exception as e:
    check("save_asr('') does not raise", False, e)



# ---------------------------------------------------------------------------
# 6. Persian or English only: the verdict, and the retry it drives
# ---------------------------------------------------------------------------
print("\n-- Persian or English only --")

V = asr.language_verdict
check("only fa and en are allowed", asr.ALLOWED_LANGUAGES == ("fa", "en"), asr.ALLOWED_LANGUAGES)
for text, detected, want, why in [
    ("I think the borrow checker is right here", None, None, "English stays"),
    ("امروز چند منبع تازه "
     "پیدا کردم", None, None, "Persian stays"),
    ("I read the مقاله today and it was good", None, None,
     "English with a Persian word stays"),
    ("هذا هو المصدر الذي "
     "وجدته في المكتبة", None, "fa",
     "Arabic goes back as Persian"),
    ("یہ ایک ٹیسٹ ہے", None, "fa",
     "Urdu goes back as Persian"),
    ("Je pense que c'est très important", None, "en", "French (accents) goes back as English"),
    ("ik denk dat dit heel belangrijk", None, "en", "Dutch (no English word in six) goes back as English"),
    ("这是一个测试", None, "fa", "another script goes back, Persian first"),
    ("hello there", "english", None, "the provider saying English settles it"),
    ("سلام", "persian", None, "the provider saying Persian settles it"),
    ("hallo", "german", "en", "the provider naming a third language sends it back"),
    ("123 456", None, None, "digits alone are no language"),
    ("", None, None, "nothing is no language"),
]:
    got = V(text, detected)
    check("verdict: %s" % why, got == want, (got, want))

LANG_CALLS = []
LANG_MODE = {"first": {"text": "hello"}, "fail_retry": False}
FA_REPLY = "به نظرم این خیلی مهم است"


class LangHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        marker = b'name="language"\r\n\r\n'
        lang = ""
        if marker in raw:
            lang = raw.split(marker, 1)[1].split(b"\r\n", 1)[0].decode()
        LANG_CALLS.append(lang)
        if lang and LANG_MODE["fail_retry"]:
            self.send_response(500)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if lang == "en":
            body = {"text": "I think this is very important", "language": "english"}
        elif lang == "fa":
            body = {"text": FA_REPLY, "language": "persian"}
        else:
            body = LANG_MODE["first"]
        out = json.dumps(body).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)

    def log_message(self, *args):
        pass


lang_server = HTTPServer(("127.0.0.1", 0), LangHandler)
threading.Thread(target=lang_server.serve_forever, daemon=True).start()
lcfg = {"endpoint": "http://127.0.0.1:%d" % lang_server.server_address[1],
        "model": "whisper-1", "api_key": "test-key", "language": ""}


def run(first, language="", fail_retry=False):
    LANG_CALLS.clear()
    LANG_MODE.update({"first": first, "fail_retry": fail_retry})
    return asr.transcribe(dict(lcfg, language=language), test_wav_bytes)


r = run({"text": "Je pense que c'est très important", "language": "french"})
check("a French decode is decoded again, as English",
      r.get("text") == "I think this is very important" and r.get("language") == "en"
      and r.get("retried") is True, r)
check("...by exactly one retry, with the hint", LANG_CALLS == ["", "en"], LANG_CALLS)
r = run({"text": "هذا هو المصدر الذي",
         "language": "arabic"})
check("an Arabic decode is decoded again, as Persian",
      r.get("language") == "fa" and r.get("text") == FA_REPLY and LANG_CALLS == ["", "fa"], (r, LANG_CALLS))
r = run({"text": "the lifetime is too short", "language": "english"})
check("English costs one request", LANG_CALLS == [""] and r.get("language") == "en"
      and not r.get("retried"), (r, LANG_CALLS))
r = run({"text": "این منبع خوبی است",
         "language": "persian"})
check("Persian costs one request", LANG_CALLS == [""] and r.get("language") == "fa", (r, LANG_CALLS))
r = run({"text": "whatever"}, language="fa")
check("a pinned language is sent once, as the hint", LANG_CALLS == ["fa"] and r.get("language") == "fa",
      (r, LANG_CALLS))
r = run({"text": "the lifetime is too short"}, language="de")
check("a third language in config is ignored, not sent", LANG_CALLS == [""], LANG_CALLS)
r = run({"text": "Je pense que c'est très important", "language": "french"}, fail_retry=True)
check("a failed retry is an error, never the French text",
      "error" in r and "neither Persian nor English" in r["error"] and "text" not in r, r)
check("...and the key is not in it", "test-key" not in r.get("error", ""), r)
lang_server.shutdown()


# ---------------------------------------------------------------------------
# 7. The microphone list: one row per real microphone
# ---------------------------------------------------------------------------
print("\n-- microphone list --")

import types  # noqa: E402


class FakeSD:
    class WasapiSettings:
        def __init__(self, auto_convert=False):
            self.auto_convert = auto_convert

    def __init__(self, apis, devices, default_api=0):
        self._apis, self._devices = apis, devices
        self.default = types.SimpleNamespace(hostapi=default_api)

    def query_hostapis(self, index=None):
        return self._apis if index is None else self._apis[index]

    def query_devices(self):
        return self._devices


MIC = "Microphone Array (AMD Audio Device)"
JABRA = "Headset Microphone (Jabra Evolve2 65)"


def dev(name, api, ins=2, outs=0):
    return {"name": name, "hostapi": api, "max_input_channels": ins, "max_output_channels": outs}


# What one laptop with a headset looks like to PortAudio: the same two
# microphones once per host API (MME cutting names at 31 characters), plus
# the mapper pseudo-devices, a loopback, speakers, and a driver that lists a
# microphone twice. This is the "tens of microphones" list.
RAW = [
    dev("Microsoft Sound Mapper - Input", 0),           # 0  MME
    dev(MIC[:31], 0),                                    # 1
    dev(JABRA[:31], 0, 1),                               # 2
    dev("Stereo Mix (Realtek(R) Audio)", 0),             # 3
    dev("Speakers (Realtek(R) Audio)", 0, 0, 2),         # 4
    dev("Primary Sound Capture Driver", 1),              # 5  DirectSound
    dev(MIC, 1),                                         # 6
    dev(JABRA, 1, 1),                                    # 7
    dev(MIC, 2),                                         # 8  WASAPI
    dev(JABRA, 2, 1),                                    # 9
    dev("Stereo Mix (Realtek(R) Audio)", 2),             # 10
    dev("Speakers (Realtek(R) Audio)", 2, 0, 2),         # 11
    dev(JABRA, 2, 1),                                    # 12 listed twice
    dev(MIC, 3),                                         # 13 WDM-KS
    dev(JABRA, 3, 1),                                    # 14
]
APIS = [{"name": "MME", "default_input_device": 1},
        {"name": "Windows DirectSound", "default_input_device": 6},
        {"name": "Windows WASAPI", "default_input_device": 9},
        {"name": "Windows WDM-KS", "default_input_device": -1}]

_saved_sd = sys.modules.get("sounddevice")
sd = FakeSD(APIS, RAW)
sys.modules["sounddevice"] = sd
try:
    listed = asr.list_devices()
    check("%d raw entries become 2 microphones" % len(RAW), [d["name"] for d in listed] == [JABRA, MIC],
          [d["name"] for d in listed])
    check("the system default is marked, and first", listed and listed[0]["default"]
          and not listed[1]["default"], listed)
    check("a microphone's id is its name, which survives a reboot",
          all(d["id"] == d["name"] for d in listed), listed)
    check("no loopback, speaker or mapper entry",
          not [d for d in listed if "Stereo" in d["name"] or "Speakers" in d["name"]
               or "Mapper" in d["name"] or "Primary" in d["name"]], listed)

    R = asr.resolve_device
    check("'' is the system default", R(sd, "") == (None, None, ""), R(sd, ""))
    idx, extra, note = R(sd, JABRA)
    check("a name opens its WASAPI entry", idx == 9 and note == "", (idx, note))
    check("...converting to 16 kHz", isinstance(extra, FakeSD.WasapiSettings) and extra.auto_convert, extra)
    check("an MME-truncated saved name still finds the microphone", R(sd, MIC[:31])[0] == 8, R(sd, MIC[:31]))
    check("an old saved index is translated by name", R(sd, "2")[0] == 9, R(sd, "2"))
    idx, extra, note = R(sd, "USB Microphone (Blue Yeti)")
    check("an unplugged microphone falls back to the default, and says so",
          idx is None and "not connected" in note, (idx, note))
    check("a stale index falls back too", R(sd, "99")[0] is None and R(sd, "99")[2], R(sd, "99"))
    check("a speaker's index is not a microphone", R(sd, "4")[0] is None, R(sd, "4"))

    # No WASAPI (a stripped driver): the default API, deduplicated.
    sys.modules["sounddevice"] = FakeSD(APIS[:2], [d for d in RAW if d["hostapi"] < 2], default_api=0)
    names = [d["name"] for d in asr.list_devices()]
    check("without WASAPI: the default API, no loopback, no duplicates",
          len(names) == len(set(n.lower() for n in names)) and not [n for n in names if "Stereo" in n]
          and MIC[:31] in names, names)

    sys.modules["sounddevice"] = None      # the import fails
    check("no audio library -> an empty list, not a crash", asr.list_devices() == [])
finally:
    if _saved_sd is not None:
        sys.modules["sounddevice"] = _saved_sd
    else:
        sys.modules.pop("sounddevice", None)


# ---------------------------------------------------------------------------
# 8. The wave: LevelMeter and speech_only
# ---------------------------------------------------------------------------
print("\n-- level meter --")


def pcm(seconds, amp):
    n = int(16000 * seconds)
    return struct.pack("<%dh" % n, *[amp if (i // 20) % 2 else -amp for i in range(n)])


m = asr.LevelMeter(samplerate=16000, threshold_rms=1100)
m.feed(pcm(0.1, 0) + pcm(0.1, 16384))
d = m.read(300)
check("one bucket per 10 ms", len(d["hi"]) == 20 and d["bucket_ms"] == 10, len(d["hi"]))
check("silence reads flat", d["hi"][0] == 0 and d["lo"][0] == 0 and d["rms"][0] == 0,
      (d["hi"][0], d["rms"][0]))
check("a half-scale tone reads half-scale", d["hi"][-1] == 0.5 and d["lo"][-1] == -0.5,
      (d["hi"][-1], d["lo"][-1]))
check("the VAD threshold is on the same scale", abs(d["threshold"] - 1100 / 32768.0) < 1e-3, d["threshold"])
check("the loud part is above it, the silence below",
      d["rms"][-1] >= d["threshold"] > d["rms"][0], (d["rms"][-1], d["threshold"]))
m.feed(pcm(5.0, 1000))
d = m.read(1000)
check("keeps four seconds, not everything", len(d["hi"]) == asr.LevelMeter.KEEP, len(d["hi"]))
check("but counts every bucket, so the page can tell new from old", d["seq"] == 520, d["seq"])
check("read(n) returns the newest n", len(m.read(10)["hi"]) == 10)
check("the payload is JSON for the bridge", bool(json.dumps(m.read(50))))

print("\n-- speech_only --")

check("silence has no speech", asr.speech_only(pcm(1.0, 0)) == b"")
clip = pcm(1.0, 0) + pcm(0.5, 8000) + pcm(1.0, 0)
sp = asr.speech_only(clip)
check("the silence around speech is dropped, a little padding kept",
      0.5 * 32000 <= len(sp) <= 0.85 * 32000, len(sp) / 32000.0)
check("all-speech is kept whole (to the frame)", len(asr.speech_only(pcm(1.0, 8000))) >= 0.97 * 32000)
check("higher sensitivity keeps quieter speech",
      len(asr.speech_only(pcm(1.0, 700), sensitivity=100)) > len(asr.speech_only(pcm(1.0, 700), sensitivity=0)))

print()
print("ALL CHECKS PASSED" if not FAILS else "FAILED: " + ", ".join(FAILS))
sys.exit(1 if FAILS else 0)
