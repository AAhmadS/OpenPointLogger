"""Speaker verification: is this utterance the enrolled owner talking?

Trailmark's always-on voice logging picks up other people talking in the
background. Before an utterance is sent for transcription, the pipeline can
check whether the voice matches the enrolled owner, using a fixed speaker
embedding model (WeSpeaker ResNet34, ONNX) and cosine similarity against an
enrolled reference embedding.

This module builds and measures that check: model download/verification,
Kaldi-compatible fbank features in pure numpy, ONNX inference, enrollment,
and scoring. It does not decide what to do with a low score, does not touch
the microphone, and does not know about the VAD, the tray UI, or the log -
the integrating engineer wires this into the pipeline.

``numpy`` and ``onnxruntime`` are imported lazily, function-local, so
``import speaker`` succeeds on a machine that has neither installed yet
(mirrors the ``sounddevice``-lazy pattern in asr.py). Call ``available()``
before doing anything that needs them.
"""

import hashlib
import io
import os
import urllib.request
import wave

# ---------------------------------------------------------------------------
# Model identity
# ---------------------------------------------------------------------------

MODEL_FILE = "wespeaker_en_voxceleb_resnet34_LM.onnx"
MODEL_URL = (
    "https://github.com/k2-fsa/sherpa-onnx/releases/download/"
    "speaker-recongition-models/wespeaker_en_voxceleb_resnet34_LM.onnx"
)

# Pinned from the release's checksum.txt (k2-fsa/sherpa-onnx, tag
# speaker-recongition-models) AND independently recomputed with
# hashlib.sha256 over the downloaded 26,530,550-byte file. Both matched:
#   e9848563da86f263117134dfd7ad63c92355b37de492b55e325400c9d9c39012
MODEL_SHA256 = "e9848563da86f263117134dfd7ad63c92355b37de492b55e325400c9d9c39012"
MODEL_BYTES = 26530550

# DEFAULT_THRESHOLD is measured, not a convention. Enrolling 3
# Mandarin-speaking test identities (fangjun, leijun, liudehua) from the
# sherpa-onnx speaker-recognition-models release - 2-3 "-sr-" clips each -
# and scoring every held-out "-test-" clip (7 clips, 21 scores) against
# every enrolled speaker gave a clean separation: lowest target (same
# -speaker) cosine score 0.6561, highest non-target (different-speaker)
# score 0.3598, a 0.2962-wide gap with no overlap. The raw midpoint of that
# gap is ~0.508; DEFAULT_THRESHOLD is set above the midpoint, at 0.55,
# biased toward the target side - because a missed match just means "ask
# again" / fall back to logging as unverified, while a false accept lets a
# stranger's speech through as if it were the owner, which is the worse
# failure, and rejecting is the cheap direction to be wrong in. HONEST
# LIMIT: this was measured on three Mandarin speakers on clean,
# single-speaker recordings - not on the owner, who speaks Persian and
# English, on a laptop microphone array, in a room with other people
# talking. Treat this constant as a reasonable starting point that MUST be
# re-measured (or at least sanity-checked) against real owner enrollment
# audio before being trusted to gate anything.
DEFAULT_THRESHOLD = 0.55

# Below this, embed() returns None rather than a noisy embedding. Measured
# by cutting fangjun-test-sr-1.wav to 1.0s/1.5s/2.0s/3.0s and scoring each
# against the enrolled fangjun (true) and liudehua (false) embeddings: even
# the 1.0s cut landed clearly on the right side (true 0.6034 vs false
# 0.1375, a 0.4659 gap), so 1.0s is the floor rather than a cautious
# multiple of it - shorter than this was not tested and is not claimed safe.
MIN_SPEECH_SECONDS = 1.0

_SAMPLE_RATE = 16000
_NUM_MEL_BINS = 80
_FRAME_LENGTH_MS = 25.0
_FRAME_SHIFT_MS = 10.0
_FFT_SIZE = 512
_PREEMPH_COEFF = 0.97
_MEL_LOW_FREQ = 20.0


# ---------------------------------------------------------------------------
# Availability / download
# ---------------------------------------------------------------------------

def available():
    """(True, "") if onnxruntime + numpy are importable, else (False, why)."""
    try:
        import numpy  # noqa: F401
    except ImportError as exc:
        return False, f"numpy is not installed ({exc})"
    try:
        import onnxruntime  # noqa: F401
    except ImportError as exc:
        return False, f"onnxruntime is not installed ({exc})"
    return True, ""


def model_path(models_dir):
    import pathlib

    return pathlib.Path(models_dir) / MODEL_FILE


def model_ready(models_dir):
    """True if the model file exists and is exactly MODEL_BYTES long.

    The SHA256 is checked once, at download time (download_model) - not on
    every start, since hashing a 26MB file on every app launch is wasted
    work once the byte count already proves nothing truncated or replaced
    it since the verified download.
    """
    p = model_path(models_dir)
    try:
        return p.is_file() and p.stat().st_size == MODEL_BYTES
    except OSError:
        return False


def download_model(models_dir, progress=None, timeout=60):
    """Download MODEL_FILE into models_dir, verifying its SHA256.

    Streams to ``<file>.part`` and only ``os.replace``s it into place once
    the hash checks out, so a reader never sees a partial or corrupt file.
    On any failure (network error or hash mismatch) the ``.part`` is removed
    and nothing is left behind.

    Returns {"ok": True, "path": str(final_path)} or {"error": str}.
    ``progress(done_bytes, total_bytes)``, if given, is called after each
    chunk; total_bytes may be 0 if the server did not send Content-Length.
    """
    p = model_path(models_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    part = p.with_suffix(p.suffix + ".part")

    hasher = hashlib.sha256()
    done = 0
    try:
        req = urllib.request.Request(MODEL_URL, headers={"User-Agent": "Trailmark"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            total = int(resp.headers.get("Content-Length") or 0)
            with open(part, "wb") as f:
                while True:
                    chunk = resp.read(1 << 16)
                    if not chunk:
                        break
                    f.write(chunk)
                    hasher.update(chunk)
                    done += len(chunk)
                    if progress is not None:
                        progress(done, total)
    except Exception as exc:  # noqa: BLE001 - report, don't leak a traceback
        try:
            if part.exists():
                part.unlink()
        except OSError:
            pass
        return {"error": f"download failed: {exc}"}

    digest = hasher.hexdigest()
    if digest != MODEL_SHA256:
        try:
            part.unlink()
        except OSError:
            pass
        return {"error": f"checksum mismatch: got {digest}, expected {MODEL_SHA256}"}

    os.replace(part, p)
    return {"ok": True, "path": str(p)}


# ---------------------------------------------------------------------------
# WAV <-> PCM
# ---------------------------------------------------------------------------

def wav_to_pcm(wav_bytes):
    """(int16 mono PCM bytes, samplerate) out of a WAV file's bytes."""
    with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
        return wf.readframes(wf.getnframes()), wf.getframerate()


# ---------------------------------------------------------------------------
# Kaldi-compatible fbank, pure numpy
# ---------------------------------------------------------------------------

def _mel_filterbank(num_bins, fft_size, samplerate, low_freq, high_freq):
    """Triangular mel filterbank, Kaldi's mel-computations.cc convention.

    Returns a [num_fft_bins, num_bins] numpy array where num_fft_bins =
    fft_size // 2 + 1 (rfft bin count), so it can be applied as
    ``power_spectrum @ mel_filterbank``.
    """
    import numpy as np

    def mel_scale(freq):
        return 1127.0 * np.log(1.0 + freq / 700.0)

    num_fft_bins = fft_size // 2 + 1
    nyquist = samplerate / 2.0
    if high_freq <= 0.0:
        high_freq = nyquist + high_freq

    mel_low = mel_scale(low_freq)
    mel_high = mel_scale(high_freq)
    mel_freq_delta = (mel_high - mel_low) / (num_bins + 1)

    fft_bin_freqs = np.arange(num_fft_bins) * samplerate / fft_size
    fft_bin_mels = mel_scale(fft_bin_freqs)  # [num_fft_bins]

    bin_idx = np.arange(num_bins)
    left_mel = mel_low + bin_idx * mel_freq_delta
    center_mel = mel_low + (bin_idx + 1) * mel_freq_delta
    right_mel = mel_low + (bin_idx + 2) * mel_freq_delta

    # [num_fft_bins, num_bins] broadcast
    m = fft_bin_mels[:, None]
    up = (m - left_mel[None, :]) / (center_mel - left_mel)[None, :]
    down = (right_mel[None, :] - m) / (right_mel - center_mel)[None, :]
    weights = np.minimum(up, down)
    weights = np.maximum(weights, 0.0)
    return weights.astype(np.float64)


def fbank(pcm_bytes, samplerate=16000):
    """Kaldi-compatible 80-bin log-mel filterbank features, mean-normalised.

    16 kHz, 25 ms window / 10 ms shift, povey window, pre-emphasis 0.97, per
    -frame DC offset removal, dither 0, snip_edges=True, power spectrum with
    a 512-point FFT (next pow2 of the 400-sample window), mel range 20 Hz -
    Nyquist, natural log with an epsilon floor, then per-bin mean
    normalisation (CMN) over the utterance - the WeSpeaker convention (the
    model has no separate CMVN input; it expects already-normalised feats).

    Input PCM is int16 mono, matching WeSpeaker's "scale to int16 range"
    convention (the samples already are int16 range; nothing to rescale).
    CMN makes any fixed input scale mostly irrelevant to the final feature,
    but the pipeline follows the documented convention rather than relying
    on that side-effect.

    Returns a numpy float32 array shaped [num_frames, 80]. Empty (shape
    (0, 80)) if there are fewer samples than one frame.
    """
    import numpy as np

    waveform = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float64)

    frame_length = int(round(_FRAME_LENGTH_MS / 1000.0 * samplerate))
    frame_shift = int(round(_FRAME_SHIFT_MS / 1000.0 * samplerate))
    num_samples = waveform.shape[0]

    if num_samples < frame_length:
        return np.zeros((0, _NUM_MEL_BINS), dtype=np.float32)

    num_frames = 1 + (num_samples - frame_length) // frame_shift

    # Povey window: (0.5 - 0.5*cos(2*pi*n/(N-1)))^0.85
    n = np.arange(frame_length)
    povey_window = (0.5 - 0.5 * np.cos(2.0 * np.pi * n / (frame_length - 1))) ** 0.85

    # Build all frames at once: [num_frames, frame_length]
    starts = np.arange(num_frames) * frame_shift
    idx = starts[:, None] + np.arange(frame_length)[None, :]
    frames = waveform[idx]  # copy, safe to mutate

    # Per-frame DC offset removal (dither is 0, so nothing to add first).
    frames = frames - frames.mean(axis=1, keepdims=True)

    # Pre-emphasis: y[0] = x[0]*(1-coeff), y[i] = x[i] - coeff*x[i-1].
    preemphasized = np.empty_like(frames)
    preemphasized[:, 0] = frames[:, 0] * (1.0 - _PREEMPH_COEFF)
    preemphasized[:, 1:] = frames[:, 1:] - _PREEMPH_COEFF * frames[:, :-1]

    windowed = preemphasized * povey_window[None, :]

    spectrum = np.fft.rfft(windowed, n=_FFT_SIZE, axis=1)
    power = spectrum.real ** 2 + spectrum.imag ** 2  # [num_frames, num_fft_bins]

    mel_fb = _mel_filterbank(_NUM_MEL_BINS, _FFT_SIZE, samplerate, _MEL_LOW_FREQ, samplerate / 2.0)
    mel_energies = power @ mel_fb  # [num_frames, 80]

    eps = np.finfo(np.float32).eps
    feat = np.log(np.maximum(mel_energies, eps))

    # CMN: per-bin mean over time, so each bin has ~0 mean over the clip.
    feat = feat - feat.mean(axis=0, keepdims=True)

    return feat.astype(np.float32)


# ---------------------------------------------------------------------------
# ONNX inference
# ---------------------------------------------------------------------------

class Verifier:
    """Wraps an onnxruntime session for the WeSpeaker embedding model.

    ``embed()`` may be called from several threads at once: ORT's
    ``Session.run`` is documented thread-safe, and this class keeps no
    mutable state of its own between calls, so no lock is needed here.
    """

    def __init__(self, model_file):
        import onnxruntime as ort

        so = ort.SessionOptions()
        so.intra_op_num_threads = 2
        so.inter_op_num_threads = 1
        self._session = ort.InferenceSession(
            str(model_file), sess_options=so, providers=["CPUExecutionProvider"]
        )
        self._input_name = self._session.get_inputs()[0].name
        self._output_name = self._session.get_outputs()[0].name

    def embed(self, pcm_bytes, samplerate=16000):
        """L2-normalised embedding (list[float]), or None if too short."""
        import numpy as np

        num_samples = len(pcm_bytes) // 2
        if num_samples / float(samplerate) < MIN_SPEECH_SECONDS:
            return None

        feat = fbank(pcm_bytes, samplerate=samplerate)
        if feat.shape[0] == 0:
            return None

        feed = {self._input_name: feat[None, :, :].astype(np.float32)}
        (out,) = self._session.run([self._output_name], feed)
        vec = np.asarray(out[0], dtype=np.float64)
        norm = np.linalg.norm(vec)
        if norm <= 0.0:
            return None
        return (vec / norm).tolist()


# ---------------------------------------------------------------------------
# Scoring / enrollment
# ---------------------------------------------------------------------------

def cosine(a, b):
    """Cosine similarity between two equal-length vectors."""
    import numpy as np

    va = np.asarray(a, dtype=np.float64)
    vb = np.asarray(b, dtype=np.float64)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    if denom <= 0.0:
        return 0.0
    return float(np.dot(va, vb) / denom)


def enroll(verifier, clips, samplerate=16000):
    """Enroll a speaker from several int16 PCM clips.

    Returns {"embedding": [...], "clips": n, "seconds": float,
    "consistency": float} where embedding is the mean of the clips'
    L2-normalised embeddings, re-normalised, and consistency is the
    minimum pairwise cosine similarity between the individual clip
    embeddings (a rough self-consistency check on the enrollment audio).
    Needs at least 2 usable clips (clips shorter than MIN_SPEECH_SECONDS
    are dropped first); returns {"error": str} otherwise.
    """
    import numpy as np

    embeddings = []
    seconds = 0.0
    for clip in clips:
        emb = verifier.embed(clip, samplerate=samplerate)
        if emb is None:
            continue
        embeddings.append(np.asarray(emb, dtype=np.float64))
        seconds += len(clip) / 2.0 / float(samplerate)

    if len(embeddings) < 2:
        return {"error": f"need >= 2 usable clips, got {len(embeddings)}"}

    consistency = min(
        cosine(embeddings[i], embeddings[j])
        for i in range(len(embeddings))
        for j in range(i + 1, len(embeddings))
    )

    mean_vec = np.mean(embeddings, axis=0)
    norm = np.linalg.norm(mean_vec)
    if norm <= 0.0:
        return {"error": "degenerate mean embedding (zero norm)"}
    mean_vec = mean_vec / norm

    return {
        "embedding": mean_vec.tolist(),
        "clips": len(embeddings),
        "seconds": seconds,
        "consistency": consistency,
    }


def is_owner(score, threshold):
    """True if a cosine score clears the given threshold."""
    return score >= threshold
