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


print()
print("ALL CHECKS PASSED" if not FAILS else "FAILED: " + ", ".join(FAILS))
sys.exit(1 if FAILS else 0)
