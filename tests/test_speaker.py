"""Headless tests for speaker.py (fbank features, cosine/enroll math,
download_model, wav_to_pcm) plus an optional model-backed section.

The default run needs no network and no model file: numpy is required (it
is already in the venv), onnxruntime is monkeypatched out of sys.modules
for the "import works without it" check, and download_model() is tested
against a monkeypatched urlopen rather than the real network.

The model-backed section (embed() on real audio, scored against
DEFAULT_THRESHOLD) runs only when TRAILMARK_SPEAKER_MODEL points at a copy
of wespeaker_en_voxceleb_resnet34_LM.onnx on disk. Point it at the
scratchpad copy to exercise it:

  TRAILMARK_SPEAKER_MODEL=<path>.onnx PYTHONPATH=. .venv/Scripts/python.exe tests/test_speaker.py

Run:  PYTHONPATH=. .venv/Scripts/python.exe tests/test_speaker.py
"""

import hashlib
import io
import os
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


# ---------------------------------------------------------------------------
# 1. import speaker works with onnxruntime hidden
# ---------------------------------------------------------------------------

_hidden = {}
for _mod in ("onnxruntime",):
    if _mod in sys.modules:
        _hidden[_mod] = sys.modules.pop(_mod)

import builtins  # noqa: E402

_real_import = builtins.__import__


def _blocking_import(name, *args, **kwargs):
    if name == "onnxruntime" or name.startswith("onnxruntime."):
        raise ImportError("onnxruntime hidden for test")
    return _real_import(name, *args, **kwargs)


builtins.__import__ = _blocking_import
try:
    import speaker  # noqa: E402

    check("import speaker succeeds without onnxruntime", True)
    ok, why = speaker.available()
    check("available() reports False without onnxruntime", ok is False, why)
    check("available() reason mentions onnxruntime", "onnxruntime" in why.lower(), why)
except Exception as e:
    check("import speaker succeeds without onnxruntime", False, e)
finally:
    builtins.__import__ = _real_import

for _mod, _obj in _hidden.items():
    sys.modules[_mod] = _obj

ok, why = speaker.available()
check("available() reports True with numpy+onnxruntime installed", ok is True, why)


# ---------------------------------------------------------------------------
# 2. fbank: shape, determinism, CMN property
# ---------------------------------------------------------------------------

import numpy as np  # noqa: E402


def _sine_pcm(seconds, freq=220.0, amplitude=8000, samplerate=16000):
    n = int(seconds * samplerate)
    t = np.arange(n) / samplerate
    samples = (amplitude * np.sin(2 * np.pi * freq * t)).astype(np.int16)
    return samples.tobytes()


sine_pcm = _sine_pcm(1.0)
feat = speaker.fbank(sine_pcm, samplerate=16000)
check("fbank shape has 80 mel bins", feat.shape[1] == 80, feat.shape)
# 1.0s @ 16kHz, 25ms window / 10ms shift, snip_edges=True:
# num_frames = 1 + floor((16000-400)/160) = 1 + 97 = 98
check("fbank frame count matches snip_edges formula", feat.shape[0] == 98, feat.shape)

feat2 = speaker.fbank(sine_pcm, samplerate=16000)
check("fbank is deterministic on identical input", np.array_equal(feat, feat2), None)

bin_means = feat.mean(axis=0)
check("fbank CMN: per-bin mean over time is ~0",
      float(np.max(np.abs(bin_means))) < 1e-4, float(np.max(np.abs(bin_means))))

short_pcm = _sine_pcm(0.01)  # far under one 25ms frame
feat_short = speaker.fbank(short_pcm, samplerate=16000)
check("fbank on sub-frame audio returns an empty (0, 80) array",
      feat_short.shape == (0, 80), feat_short.shape)


# ---------------------------------------------------------------------------
# 3. cosine basics
# ---------------------------------------------------------------------------

check("cosine(a, a) == 1.0 for a unit vector",
      abs(speaker.cosine([1.0, 0.0, 0.0], [1.0, 0.0, 0.0]) - 1.0) < 1e-9)
check("cosine(a, -a) == -1.0",
      abs(speaker.cosine([1.0, 0.0], [-1.0, 0.0]) - (-1.0)) < 1e-9)
check("cosine(a, b) == 0.0 for orthogonal vectors",
      abs(speaker.cosine([1.0, 0.0], [0.0, 1.0])) < 1e-9)
check("cosine() with a zero vector returns 0.0 rather than raising",
      speaker.cosine([0.0, 0.0], [1.0, 0.0]) == 0.0)


# ---------------------------------------------------------------------------
# 4. is_owner
# ---------------------------------------------------------------------------

check("is_owner(score >= threshold) is True", speaker.is_owner(0.6, 0.55) is True)
check("is_owner(score < threshold) is False", speaker.is_owner(0.5, 0.55) is False)
check("is_owner(score == threshold) is True (boundary inclusive)", speaker.is_owner(0.55, 0.55) is True)


# ---------------------------------------------------------------------------
# 5. enroll() math with a fake verifier
# ---------------------------------------------------------------------------

class _FakeVerifier:
    """Maps known PCM byte-strings to fixed, hand-picked embeddings, so the
    enroll() math (mean-of-normalised, consistency=min-pairwise, the
    <2-usable-clips error) can be checked exactly without any model."""

    def __init__(self, mapping, min_seconds=0.0):
        self._mapping = mapping
        self.min_seconds = min_seconds

    def embed(self, pcm_bytes, samplerate=16000):
        return self._mapping.get(pcm_bytes)


clip_a = b"CLIP_A"
clip_b = b"CLIP_B"
clip_c = b"CLIP_C"  # unusable -> embed() returns None

vec_a = [1.0, 0.0, 0.0]
vec_b = [0.0, 1.0, 0.0]  # orthogonal to a: pairwise cosine 0.0

fv = _FakeVerifier({clip_a: vec_a, clip_b: vec_b, clip_c: None})
res = speaker.enroll(fv, [clip_a, clip_b, clip_c], samplerate=16000)
check("enroll() drops the unusable clip and keeps 2", res.get("clips") == 2, res)
check("enroll() consistency is the min pairwise cosine (0.0 here)",
      res.get("consistency") is not None and abs(res["consistency"] - 0.0) < 1e-9, res.get("consistency"))
expected_mean = np.array(vec_a, dtype=np.float64) + np.array(vec_b, dtype=np.float64)
expected_mean = expected_mean / np.linalg.norm(expected_mean)
got_mean = np.array(res["embedding"], dtype=np.float64)
check("enroll() embedding is the re-normalised mean of the clip embeddings",
      bool(np.allclose(got_mean, expected_mean, atol=1e-9)), res.get("embedding"))

res_one = speaker.enroll(fv, [clip_a, clip_c], samplerate=16000)
check("enroll() with < 2 usable clips returns an error, not a crash",
      "error" in res_one, res_one)

res_zero = speaker.enroll(fv, [], samplerate=16000)
check("enroll() with 0 clips returns an error", "error" in res_zero, res_zero)


# ---------------------------------------------------------------------------
# 6. download_model() against a monkeypatched urlopen
# ---------------------------------------------------------------------------

tmp_models = pathlib.Path(tempfile.mkdtemp(prefix="opl_speaker_test_"))

GOOD_PAYLOAD = os.urandom(4096)
GOOD_SHA = hashlib.sha256(GOOD_PAYLOAD).hexdigest()
BAD_PAYLOAD = os.urandom(4096)  # deliberately does not match speaker.MODEL_SHA256


class _FakeResponse:
    def __init__(self, payload):
        self._buf = io.BytesIO(payload)
        self.headers = {"Content-Length": str(len(payload))}

    def read(self, n=-1):
        return self._buf.read(n)

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _make_urlopen(payload):
    def _urlopen(req, timeout=60):
        return _FakeResponse(payload)

    return _urlopen


_orig_urlopen = speaker.urllib.request.urlopen
_orig_sha = speaker.MODEL_SHA256

try:
    speaker.MODEL_SHA256 = GOOD_SHA
    speaker.urllib.request.urlopen = _make_urlopen(GOOD_PAYLOAD)
    progress_calls = []
    result = speaker.download_model(tmp_models, progress=lambda d, t: progress_calls.append((d, t)))
    dest = speaker.model_path(tmp_models)
    check("download_model() with a matching hash reports ok", result.get("ok") is True, result)
    check("download_model() with a matching hash lands the file", dest.is_file(), dest)
    check("download_model() landed file has the right bytes",
          dest.is_file() and dest.read_bytes() == GOOD_PAYLOAD, None)
    check("download_model() progress callback was invoked", len(progress_calls) > 0, progress_calls)
    part = dest.with_suffix(dest.suffix + ".part")
    check("download_model() success leaves no .part file", not part.exists(), part)

    dest.unlink()

    speaker.urllib.request.urlopen = _make_urlopen(BAD_PAYLOAD)
    result_bad = speaker.download_model(tmp_models)
    check("download_model() with a bad hash returns an error", "error" in result_bad, result_bad)
    check("download_model() with a bad hash leaves no final file", not dest.exists(), dest)
    check("download_model() with a bad hash leaves no .part file", not part.exists(), part)
finally:
    speaker.urllib.request.urlopen = _orig_urlopen
    speaker.MODEL_SHA256 = _orig_sha


# ---------------------------------------------------------------------------
# 7. model_ready()
# ---------------------------------------------------------------------------

_orig_bytes = speaker.MODEL_BYTES
try:
    fake_model = speaker.model_path(tmp_models)
    fake_model.write_bytes(b"x" * 123)
    speaker.MODEL_BYTES = 123
    check("model_ready() is True when size matches MODEL_BYTES", speaker.model_ready(tmp_models) is True)
    speaker.MODEL_BYTES = 124
    check("model_ready() is False when size does not match", speaker.model_ready(tmp_models) is False)
    check("model_ready() is False for a missing models dir",
          speaker.model_ready(pathlib.Path(tempfile.mkdtemp(prefix="opl_speaker_missing_"))) is False)
finally:
    speaker.MODEL_BYTES = _orig_bytes


# ---------------------------------------------------------------------------
# 8. wav_to_pcm round-trip
# ---------------------------------------------------------------------------

pcm_in = struct.pack("<8h", 100, -100, 200, -200, 300, -300, 400, -400)
bio = io.BytesIO()
with wave.open(bio, "wb") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(16000)
    wf.writeframes(pcm_in)
wav_bytes = bio.getvalue()

pcm_out, sr_out = speaker.wav_to_pcm(wav_bytes)
check("wav_to_pcm round-trips PCM bytes exactly", pcm_out == pcm_in, (pcm_out, pcm_in))
check("wav_to_pcm returns the samplerate written", sr_out == 16000, sr_out)


# ---------------------------------------------------------------------------
# 9. model-backed section (real ONNX model, real test audio)
# ---------------------------------------------------------------------------

model_env = os.environ.get("TRAILMARK_SPEAKER_MODEL")
if not model_env:
    print()
    print("SKIP model-backed section (TRAILMARK_SPEAKER_MODEL not set)")
else:
    model_file = pathlib.Path(model_env)
    if not model_file.is_file():
        check("TRAILMARK_SPEAKER_MODEL points at an existing file", False, model_file)
    else:
        wav_dir = pathlib.Path(
            os.environ.get(
                "TRAILMARK_SPEAKER_WAVS",
                str(pathlib.Path(tempfile.gettempdir())),
            )
        )
        # Default lookup: alongside the model file, in a wavs/ subdirectory,
        # which is how the scratchpad copy used to build this module is laid
        # out. Overridable via TRAILMARK_SPEAKER_WAVS.
        default_wavs = model_file.parent / "wavs"
        if default_wavs.is_dir():
            wav_dir = default_wavs

        def _load(name):
            with wave.open(str(wav_dir / name), "rb") as wf:
                return wf.readframes(wf.getnframes()), wf.getframerate()

        enroll_files = {
            "fangjun": ["fangjun-sr-1.wav", "fangjun-sr-2.wav", "fangjun-sr-3.wav"],
            "leijun": ["leijun-sr-1.wav", "leijun-sr-2.wav"],
            "liudehua": ["liudehua-sr-1.wav", "liudehua-sr-2.wav"],
        }
        test_files = {
            "fangjun": ["fangjun-test-sr-1.wav", "fangjun-test-sr-2.wav"],
            "leijun": ["leijun-test-sr-1.wav", "leijun-test-sr-2.wav", "leijun-test-sr-3.wav"],
            "liudehua": ["liudehua-test-sr-1.wav", "liudehua-test-sr-2.wav"],
        }

        missing = [
            f
            for files in list(enroll_files.values()) + list(test_files.values())
            for f in files
            if not (wav_dir / f).is_file()
        ]
        if missing:
            check("model-backed test audio is present", False, f"missing {missing} under {wav_dir}")
        else:
            verifier = speaker.Verifier(str(model_file))
            enrolled = {}
            for spk, files in enroll_files.items():
                clips = [_load(f)[0] for f in files]
                sr = _load(files[0])[1]
                res = speaker.enroll(verifier, clips, samplerate=sr)
                check(f"enroll({spk}) succeeds", "embedding" in res, res.get("error"))
                if "embedding" in res:
                    enrolled[spk] = res["embedding"]

            targets = []
            non_targets = []
            for true_spk, files in test_files.items():
                for f in files:
                    pcm, sr = _load(f)
                    emb = verifier.embed(pcm, samplerate=sr)
                    if emb is None:
                        check(f"embed({f}) returns a vector", False, "got None")
                        continue
                    for enr_spk, enr_emb in enrolled.items():
                        score = speaker.cosine(emb, enr_emb)
                        (targets if enr_spk == true_spk else non_targets).append(score)

            if targets and non_targets:
                check(
                    "every target score beats every non-target score at DEFAULT_THRESHOLD's gap",
                    min(targets) > max(non_targets),
                    (min(targets), max(non_targets)),
                )
                check(
                    "lowest target score clears DEFAULT_THRESHOLD",
                    min(targets) >= speaker.DEFAULT_THRESHOLD,
                    (min(targets), speaker.DEFAULT_THRESHOLD),
                )
                check(
                    "highest non-target score stays under DEFAULT_THRESHOLD",
                    max(non_targets) < speaker.DEFAULT_THRESHOLD,
                    (max(non_targets), speaker.DEFAULT_THRESHOLD),
                )


print()
print("ALL CHECKS PASSED" if not FAILS else "FAILED: " + ", ".join(FAILS))
sys.exit(1 if FAILS else 0)
