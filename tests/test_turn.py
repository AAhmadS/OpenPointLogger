"""Headless tests for turn.py (noise gate, endpoint policy),
speaker clustering, and the Controller wiring (noise skip, held labels).

No microphone, no network, no model file: PCM is synthetic, the verifier
is bypassed by calling _hold directly with hand-picked embeddings, and
transcription is a fake that counts its calls.

Run:  PYTHONPATH=. .venv/Scripts/python.exe tests/test_turn.py
"""

import io
import json
import math
import pathlib
import struct
import sys
import tempfile
import wave

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

FAILS = []


def check(name, cond, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + name + ((" - " + str(detail)) if detail else ""))
    if not cond:
        FAILS.append(name)


import trailmark.turn as turn
import trailmark.speaker as speaker

SAMPLERATE = 16000
FRAME_SAMPLES = 480  # ~30ms


def _frames_of(samples):
    out = []
    for i in range(0, len(samples), FRAME_SAMPLES):
        chunk = samples[i:i + FRAME_SAMPLES]
        if len(chunk) < FRAME_SAMPLES:
            chunk = chunk + [0] * (FRAME_SAMPLES - len(chunk))
        out.append(struct.pack("<%dh" % len(chunk), *chunk))
    return out


def _sine(seconds, freq=440.0, amplitude=8000):
    n = int(seconds * SAMPLERATE)
    return [int(amplitude * math.sin(2 * math.pi * freq * t / SAMPLERATE)) for t in range(n)]


def _pcm(samples):
    return struct.pack("<%dh" % len(samples), *samples)


def _wav(pcm_bytes):
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLERATE)
        wf.writeframes(pcm_bytes)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# 1. frame_rms / utterance_snr_db
# ---------------------------------------------------------------------------
print("\n-- levels --")

check("silence RMS is 0", turn.frame_rms(b"\x00\x00" * FRAME_SAMPLES) == 0.0)
loud_rms = turn.frame_rms(_frames_of(_sine(0.03, amplitude=10000))[0])
check("a loud tone is above the sensitivity=50 threshold (1100)",
      loud_rms >= 1100, round(loud_rms, 1))

check("empty clip has no measurable SNR",
      turn.utterance_snr_db(b"") is None)
all_loud = _pcm(_sine(1.5, amplitude=8000))
check("an all-loud clip has no floor, so no SNR (fail open)",
      turn.utterance_snr_db(all_loud) is None)
mixed = _pcm([0] * 8000 + _sine(1.0, amplitude=8000))
snr = turn.utterance_snr_db(mixed)
check("speech over digital silence measures a high SNR",
      snr is not None and snr > 20, snr)


# ---------------------------------------------------------------------------
# 2. is_noise_utterance
# ---------------------------------------------------------------------------
print("\n-- noise gate --")

noisy, why = turn.is_noise_utterance(b"")
check("empty is noise", noisy is True and why == "empty", why)
noisy, why = turn.is_noise_utterance(_pcm([0] * SAMPLERATE))
check("a second of silence is noise, not speech", noisy is True, why)
noisy, why = turn.is_noise_utterance(_pcm(_sine(0.2, amplitude=300)))
check("a sub-threshold hum is noise (no speech frames)", noisy is True, why)
noisy, why = turn.is_noise_utterance(mixed)
check("speech with pauses is not noise", noisy is False, (noisy, why))
noisy, why = turn.is_noise_utterance(all_loud)
check("an all-loud clip fails open (not noise)", noisy is False, (noisy, why))

# Steady noise straddling the VAD threshold: frames alternate just above
# and just below it, so everything sits within ~1dB of its own floor.
straddle = []
for i in range(50):
    amp = 1700 if i % 2 else 1400  # RMS ~1202 / ~990 vs threshold 1100
    straddle += _sine(0.03, amplitude=amp)
noisy, why = turn.is_noise_utterance(_pcm(straddle))
check("threshold-straddling flat noise is noise", noisy is True, why)


# ---------------------------------------------------------------------------
# 3. EndpointPolicy
# ---------------------------------------------------------------------------
print("\n-- endpoint --")

p = turn.EndpointPolicy()
check("defaults reproduce today's 800ms tail",
      (p.min_silence_ms, p.max_silence_ms) == (800.0, 2000.0),
      (p.min_silence_ms, p.max_silence_ms))
d = p.decide(799)
check("799ms holds", d["emit"] is False and d["reason"] == "pause-short", d)
d = p.decide(800)
check("800ms emits on the tail", d["emit"] is True and d["reason"] == "min-silence", d)
d = p.decide(2000)
check("the cap emits", d["emit"] is True and d["reason"] == "max-silence", d)
d = p.decide(0)
check("no pause holds with prob 0", d["emit"] is False and d["prob"] == 0.0, d)

p2 = turn.EndpointPolicy(endpoint_fn=lambda pause, t: 0.9)
d = p2.decide(100)
check("a confident model emits early", d["emit"] is True and d["reason"] == "model-complete", d)
p3 = turn.EndpointPolicy(endpoint_fn=lambda pause, t: 0.1)
d = p3.decide(100)
check("an unsure model holds", d["emit"] is False and d["reason"] == "model-hold", d)
d = p3.decide(5000)
check("the cap wins over a holding model", d["emit"] is True and d["reason"] == "max-silence", d)


def _boom(pause, t):
    raise RuntimeError("model missing")


p4 = turn.EndpointPolicy(endpoint_fn=_boom)
d = p4.decide(100)
check("a throwing model emits rather than stalling",
      d["emit"] is True and d["reason"] == "endpoint-error-emit", d)
p5 = turn.EndpointPolicy(endpoint_fn=lambda pause, t: 0.9, threshold=0.95)
check("a custom threshold is honoured",
      p5.decide(100)["emit"] is False, p5.decide(100))


# ---------------------------------------------------------------------------
# 4. speaker clustering
# ---------------------------------------------------------------------------
print("\n-- clustering --")

A = [1.0, 0.0]
B = [0.0, 1.0]
check("two voices separate, same voice joins",
      speaker.cluster_embeddings([A, A, B]) == [0, 0, 1],
      speaker.cluster_embeddings([A, A, B]))
check("None stays None", speaker.cluster_embeddings([A, None, B]) == [0, None, 1])
check("boundary cosine joins (>= threshold)",
      speaker.cluster_embeddings([A, B], threshold=0.0) == [0, 0])
check("labels are dense SPEAKER_%02d in first-appearance order",
      speaker.label_utterances(["x", "y", "z"], [B, A, B]) ==
      {"x": "SPEAKER_00", "y": "SPEAKER_01", "z": "SPEAKER_00"})
check("unknown embeds label empty",
      speaker.label_utterances(["x"], [None]) == {"x": ""})


# ---------------------------------------------------------------------------
# 5. Controller wiring: noise skip + sticky held labels
# ---------------------------------------------------------------------------
print("\n-- wiring --")

import trailmark.point_store as ps  # noqa: E402

tmp = pathlib.Path(tempfile.mkdtemp(prefix="opl_turn_"))
ps.BASE_DIR = tmp
ps.DATA_FILE = tmp / "points.json"
ps.CONFIG_FILE = tmp / "config.json"
ps.ATTACH_DIR = tmp / "attachments"
ps.EXPORT_DIR = tmp / "exports"

import point_logger  # noqa: E402

c = point_logger.Controller()
c.models_dir = lambda: tmp / "models"
c.refresh_full = lambda: None
SENT = []
point_logger.asr.transcribe = lambda cfg, wav: SENT.append(wav) or {"text": "words", "language": "en"}

silent_wav = _wav(_pcm([0] * SAMPLERATE))
r = c.hear(silent_wav)
check("a silent utterance never reaches transcription",
      r == {"noise": True} and SENT == [], (r, len(SENT)))
c.apply_heard({"seq": 1, "wav": silent_wav, "noise": True})
check("applying noise changes nothing and raises nothing",
      c.draft.is_empty() and c.held_list() == [])

tone_wav = _wav(_pcm(_sine(1.5, amplitude=8000)))
r = c.hear(tone_wav)
check("speech is still transcribed", r.get("text") == "words" and len(SENT) == 1, r)

spk_b = c._hold(tone_wav, 0.1, "", "another voice", embedding=[1.0, 0.0])
check("the first strange voice is Speaker B", spk_b == "Speaker B", spk_b)
spk_b2 = c._hold(tone_wav, 0.12, "", "another voice", embedding=[1.0, 0.0])
check("the same voice keeps its label", spk_b2 == "Speaker B", spk_b2)
spk_c = c._hold(tone_wav, 0.05, "", "another voice", embedding=[0.0, 1.0])
check("a second voice is Speaker C", spk_c == "Speaker C", spk_c)
spk_none = c._hold(tone_wav, None, "yes", "too short to check the voice")
check("too short to check carries no label", spk_none == "", spk_none)
h = c.held_list()
check("held labels travel with the list",
      [x["speaker"] for x in h] == ["Speaker B", "Speaker B", "Speaker C", ""], h)
check("neither audio nor embeddings cross the bridge",
      all("wav" not in x and "emb" not in x for x in h), sorted(h[0]))
check("the list is still JSON", bool(json.dumps(h)))
c.drop_held()
c._hold(tone_wav, 0.1, "", "another voice", embedding=[1.0, 0.0])
c._hold(tone_wav, 0.05, "", "another voice", embedding=[0.0, 1.0])
hid_b = c.held_list()[0]["id"]
c.drop_held(hid_b)
check("dropping one voice never renames the rest",
      [x["speaker"] for x in c.held_list()] == ["Speaker C"], c.held_list())
c.drop_held()
c._hold(tone_wav, 0.1, "", "another voice", embedding=[0.0, 1.0])
check("an emptied list restarts at Speaker B (no ghosts kept)",
      c.held_list()[0]["speaker"] == "Speaker B", c.held_list())

print()
print("ALL CHECKS PASSED" if not FAILS else "FAILED: " + ", ".join(FAILS))
sys.exit(1 if FAILS else 0)
