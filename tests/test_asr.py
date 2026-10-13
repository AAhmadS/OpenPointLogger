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

# Persian verdict labels print as-is; a cp1252 console would otherwise abort
# the run with UnicodeEncodeError before the Persian cases are reached.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

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

import trailmark.asr as asr

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

import trailmark.point_store as ps # noqa: E402

tmp = pathlib.Path(tempfile.mkdtemp(prefix="opl_test_"))
ps.BASE_DIR = tmp
ps.DATA_FILE = tmp / "points.json"
ps.CONFIG_FILE = tmp / "config.json"
ps.ATTACH_DIR = tmp / "attachments"
ps.EXPORT_DIR = tmp / "exports"

import point_logger as point_logger

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


# ---------------------------------------------------------------------------
# 9. Handsfree survival: tolerant matching, fingerprints, watcher decisions
# ---------------------------------------------------------------------------
print("\n-- handsfree survival --")

check("normalisation folds case, punctuation and spacing",
      asr._norm_device_name("WH-1000XM4  Hands-Free") == asr._norm_device_name("wh 1000xm4 hands free"),
      (asr._norm_device_name("WH-1000XM4  Hands-Free"), asr._norm_device_name("wh 1000xm4 hands free")))

HF = "WH-1000XM4 Hands-Free"
HF2 = "Headset Microphone (Jabra Evolve2 65)"
CANDS = [(0, HF, 2), (1, MIC, 2), (2, HF2, 2), (3, "Stereo Mix (Realtek(R) Audio)", 2)]
M = asr._match_device
check("exact name matches", M(HF, CANDS) == 0, M(HF, CANDS))
check("case does not matter", M("wh-1000xm4 hands-free", CANDS) == 0)
check("hyphens vs spaces do not matter", M("WH 1000XM4 Hands Free", CANDS) == 0)
check("a reconnected qualifier still matches",
      M("Headset (Jabra EVOLVE2 65)", CANDS) == 2, M("Headset (Jabra EVOLVE2 65)", CANDS))
check("legacy MME truncation still matches", M(MIC[:31], [(0, MIC, 2)]) == 0)
check("'Microphone Array' does not match 'Headset Microphone'",
      M("Microphone Array", [(0, "Headset Microphone", 2)]) is None)
check("a single shared word is not a match",
      M("Microphone", [(0, "Headset Microphone", 2)]) is None)
check("nothing matches an empty list", M(HF, []) is None)
check("blank wanted matches nothing", M("  ", CANDS) is None)

HF_RAW = [dev(HF, 2), dev(MIC, 2), dev(HF2, 2),
          dev("Stereo Mix (Realtek(R) Audio)", 2)]
HF_APIS = [{"name": "Windows WASAPI", "default_input_device": 0}]
hf_sd = FakeSD(HF_APIS, HF_RAW)
check("resolve_device_name reports the present device",
      asr.resolve_device_name(hf_sd, "wh 1000xm4 hands-free") == HF,
      asr.resolve_device_name(hf_sd, "wh 1000xm4 hands-free"))
check("resolve_device_name is '' for a missing device",
      asr.resolve_device_name(hf_sd, "USB Microphone (Blue Yeti)") == "")
check("resolve_device_name is '' for the default", asr.resolve_device_name(hf_sd, "") == "")
check("resolve_device_name never raises without audio",
      asr.resolve_device_name(None, HF) == "")
idx, _extra, note = asr.resolve_device(hf_sd, "USB Microphone (Blue Yeti)")
check("fallback still opens the default", idx is None, (idx, note))
check("fallback note names the microphone actually used",
      "not connected" in note and HF in note, note)

fp1 = asr.device_fingerprint(hf_sd)
# Same default at index 0, the rest rotated: ordering must not matter, and
# the default must still resolve to the same device.
fp_reordered = asr.device_fingerprint(FakeSD(HF_APIS, [HF_RAW[0], HF_RAW[2], HF_RAW[1], HF_RAW[3]]))
check("fingerprint ignores ordering", fp1 == fp_reordered, (fp1, fp_reordered))
fp_new_default = asr.device_fingerprint(
    FakeSD([{"name": "Windows WASAPI", "default_input_device": 1}], HF_RAW))
check("a Windows default-flip changes the fingerprint", fp_new_default != fp1)
fp_unplugged = asr.device_fingerprint(FakeSD(HF_APIS, [d for d in HF_RAW if HF not in d["name"]]))
check("an unplug shrinks the fingerprint",
      len(fp_unplugged[0]) == len(fp1[0]) - 1, (fp1[0], fp_unplugged[0]))
check("query failure answers empty, not a crash", asr.device_fingerprint(None) == ((), ""))

D = c._asr_watch_decide
BASE = {"now": 1000.0, "wanted": HF, "wanted_present": HF, "fallback_from": None,
        "default": HF, "prev_default": HF, "alive": True, "cb_age": 0.0, "cooldown": False}
check("cooldown suppresses everything",
      D(dict(BASE, cooldown=True, alive=False)) is None)
check("steady state is quiet", D(dict(BASE)) is None)
check("unplug falls back, naming both ends",
      D(dict(BASE, wanted_present=""))[0] == "lost"
      and HF in D(dict(BASE, wanted_present=""))[1]
      and "until it comes back" in D(dict(BASE, wanted_present=""))[1])
check("no repeat while already fallen back",
      D(dict(BASE, wanted_present="", fallback_from=HF)) is None)
check("replug returns to the headset",
      D(dict(BASE, fallback_from=HF))[0] == "reconnected")
check("unplug with no default waits instead",
      D(dict(BASE, wanted_present="", default="")) == (
          "lost", "“%s” disconnected - waiting for a microphone." % HF))
check("default-flip restarts onto the new default",
      D({"now": 1000.0, "wanted": "", "wanted_present": "", "fallback_from": None,
         "default": MIC, "prev_default": HF, "alive": True,
         "cb_age": 0.0, "cooldown": False})[0] == "default_changed")
check("same default is quiet",
      D(dict(BASE, wanted="", wanted_present="", prev_default=HF, default=HF)) is None)
check("a dead thread restarts",
      D(dict(BASE, wanted="", wanted_present="", prev_default="", default="",
             alive=False))[0] == "died")
check("a silent stream restarts",
      D(dict(BASE, wanted="", wanted_present="", prev_default="", default="",
             cb_age=99.0))[0] == "stalled")
check("device news beats a dead thread",
      D(dict(BASE, wanted_present="", alive=False))[0] == "lost")

lg = asr.VoiceLogger({}, lambda w, s: None, lambda s, d: None)
check("a fresh logger reports not alive", lg.alive() is False)
check("callback age is a non-negative float",
      isinstance(lg.callback_age(), float) and lg.callback_age() >= 0.0)

import trailmark.ui as ui  # noqa: E402
import re as _re  # noqa: E402
# Served-page hygiene: a real NUL in the served HTML truncates the whole
# window at the native WebView2 string boundary - blank window, zero errors.
# Python interprets backslash escapes when ui.py is imported, so this asserts
# on the RUNTIME strings exactly as pywebview serves them, not on file text.
from trailmark.brand import ICON_DATA_URI as _ICON  # noqa: E402
_served_main = ui.MAIN_HTML.replace("__ICON__", _ICON).replace("__BASE_CSS__", ui.BASE_CSS)
_served_pop = ui.POPUP_HTML.replace("__ICON__", _ICON).replace("__BASE_CSS__", ui.BASE_CSS)
for _name, _html in (("MAIN_HTML", _served_main), ("POPUP_HTML", _served_pop)):
    _bad = [c for c in _html if ord(c) < 0x20 and c not in ("\t", "\n", "\r")]
    check("served %s has no control chars" % _name, not _bad, list(map(hex, map(ord, _bad)))[:5])
for eid in ("mtDevNote", "hfHint"):
    check("settings markup has #%s" % eid, ('id="%s"' % eid) in ui.MAIN_HTML)
check("asrState renders the watcher 'switched' state",
      '"switched"' in ui.MAIN_HTML and "devNoteFromSwitch" in ui.MAIN_HTML)
check("Api.asr_device_status exists", callable(getattr(point_logger.Api, "asr_device_status", None)))
called = set(_re.findall(r"api\.([a-z_]+)\(", ui.POPUP_HTML + ui.MAIN_HTML))
missing = sorted(m for m in called if not hasattr(point_logger.Api, m))
check("no window calls a bridge method Api lacks", not missing, missing)


# ---------------------------------------------------------------------------
# 10. Test records, plays back, and retunes live; held buffer holds three
# ---------------------------------------------------------------------------
print("\n-- record, playback, live sensitivity, held cap --")

mon = asr.MicMonitor(device="", sensitivity=50)
t50 = asr.Vad(sensitivity=50).threshold / 32768.0
check("monitor starts at the configured threshold", abs(mon.meter.threshold - t50) < 1e-6,
      mon.meter.threshold)
mon.set_sensitivity(100)
t100 = asr.Vad(sensitivity=100).threshold / 32768.0
check("retune moves the speech line without reopening", abs(mon.meter.threshold - t100) < 1e-6
      and mon.running is False, mon.meter.threshold)
before = mon.meter.threshold
mon.set_sensitivity("junk")
check("a junk value is ignored, not raised", mon.meter.threshold == before)
mon.set_sensitivity(-5)
check("out-of-range clamps",
      abs(mon.meter.threshold - asr.Vad(sensitivity=0).threshold / 32768.0) < 1e-6)

try:
    asr.play_pcm(b"")
    check("playing nothing is refused", False, "no raise")
except RuntimeError as e:
    check("playing nothing is refused", "Nothing recorded" in str(e), str(e))
except Exception as e:
    check("playing nothing is refused without audio access", False, repr(e))

r = c.mic_test_play()
check("play with no recording errors, not crashes",
      isinstance(r, dict) and "error" in r and "test" in r["error"], r)
check("bad sensitivity is an error, not a crash",
      c.mic_test_sensitivity("junk").get("error") is not None)
check("sensitivity with nothing running is a quiet ok",
      c.mic_test_sensitivity(80).get("ok") is True)
check("held buffer holds three", c.HELD_MAX == 3, c.HELD_MAX)
try:
    st = c.speaker_status()
    check("speaker_status reports the held cap", st.get("held_max") == 3, st.get("held_max"))
except Exception as e:
    check("speaker_status reports the held cap", False, e)

for meth in ("mic_test_play", "mic_test_sensitivity"):
    check("Api.%s exists" % meth, callable(getattr(point_logger.Api, meth, None)))
check("settings markup has #mtPlay", 'id="mtPlay"' in ui.MAIN_HTML)
check("full wires #mtPlay at both ends",
      ui.MAIN_HTML.count("mtPlay") >= 2, ui.MAIN_HTML.count("mtPlay"))
check("mic dropdown locks during a test",
      'id="asrDevice" class="input" ${micTestOn?"disabled":""}' in ui.MAIN_HTML)

print()
print("ALL CHECKS PASSED" if not FAILS else "FAILED: " + ", ".join(FAILS))
sys.exit(1 if FAILS else 0)
