"""Streaming noise gate and endpoint policy for always-on voice.

Two small pure pieces that sit around the existing energy VAD (asr.Vad)
without changing its defaults:

- ``is_noise_utterance``: post-utterance reject. A VAD that only measures
  loudness emits steady noise (fan, hum, room hiss) as happily as speech.
  This re-reads the finished clip's own frames: nothing above the VAD's
  threshold, or everything within a few dB of its own floor, means there
  was no speech modulation in it. The caller (``Controller.hear``) then
  skips the transcription round trip entirely - the cheapest latency win
  there is, and fail-open: whenever no floor can be measured (an all-loud
  clip, e.g. a short command) the answer is "not noise", i.e. today's
  behaviour. Privacy order is kept by the caller: the speaker gate runs
  first, so this never sees audio the gate would have held.
- ``EndpointPolicy``: the "don't wait out the noise" contract. A VAD only
  hears silence, so a fixed 800ms tail waits the same 800ms after a
  finished sentence and after a mid-thought pause. The policy asks, once
  per pause, for P(turn complete) - today from pause length alone against
  ``min_silence_ms``/``max_silence_ms``, tomorrow from a Smart-Turn-style
  audio model via ``endpoint_fn`` with the same signature
  (``(pause_ms, turn_seconds) -> float`` in [0,1]). The cap always wins,
  and a throwing model emits rather than stalling the conversation.

Plug-in points for the heavier stages from docs/voice-realtime.md, all
behind these interfaces so no caller changes: a DeepFilterNet/DPDFNet
frame enhancer before the VAD, a Silero/MarbleNet frame-probability VAD
replacing the RMS check inside ``Vad.feed``, and a Smart-Turn ONNX model
as ``EndpointPolicy.endpoint_fn``. Nothing here imports them; stdlib only.
"""

import math
import struct

__all__ = ["frame_rms", "utterance_snr_db", "is_noise_utterance",
           "EndpointPolicy", "DEFAULT_MIN_SILENCE_MS",
           "DEFAULT_MAX_SILENCE_MS", "DEFAULT_SNR_DB_MIN"]

#: Matches asr.Vad's tail today, so wiring the policy in changes nothing
#: until the config moves it.
DEFAULT_MIN_SILENCE_MS = 800.0
#: A vetoed pause can never hold the turn longer than this.
DEFAULT_MAX_SILENCE_MS = 2000.0
#: Below this modulation the clip is flat enough to be steady noise.
DEFAULT_SNR_DB_MIN = 3.0

_FRAME_MS = 30.0


def _threshold_for(sensitivity):
    """The RMS threshold asr.Vad would use, without importing asr at module
    load (point_logger imports both; keep this module dependency-free)."""
    s = max(0, min(100, 50 if sensitivity is None else sensitivity))
    return 2000.0 - 18.0 * s


def frame_rms(frame_bytes):
    """RMS of one int16 mono frame."""
    count = len(frame_bytes) // 2
    if count == 0:
        return 0.0
    samples = struct.unpack("<%dh" % count, frame_bytes[: count * 2])
    return (sum(s * s for s in samples) / count) ** 0.5


def _frames(pcm_bytes, samplerate=16000, frame_ms=_FRAME_MS):
    step = max(1, int(round(samplerate * frame_ms / 1000.0)) * 2)
    return [pcm_bytes[i:i + step] for i in range(0, len(pcm_bytes), step)]


def utterance_snr_db(pcm_bytes, samplerate=16000, sensitivity=50):
    """Loud-frame mean RMS over quiet-floor mean RMS, in dB.

    Returns None when no floor can be measured (empty clip, or every frame
    loud - a short command has no silence to compare against). None means
    "unmeasurable", and every caller treats it as not-noise.
    """
    frames = _frames(pcm_bytes or b"", samplerate)
    if not frames:
        return None
    threshold = _threshold_for(sensitivity)
    loud = [frame_rms(f) for f in frames if frame_rms(f) >= threshold]
    quiet = [frame_rms(f) for f in frames if frame_rms(f) < threshold]
    if not loud or not quiet:
        # No speech frames at all is decided by is_noise_utterance; here it
        # only means no floor to measure against (an all-loud short clip).
        return None
    floor = sum(quiet) / len(quiet)
    # Digital silence floors at exactly 0.0 - that is infinite SNR (speech
    # over silence), not unmeasurable: clamp to one LSB instead.
    floor = max(floor, 1.0)
    return 20.0 * math.log10((sum(loud) / len(loud)) / floor)


def is_noise_utterance(pcm_bytes, samplerate=16000, sensitivity=50,
                       snr_db_min=DEFAULT_SNR_DB_MIN):
    """(is_noise, reason) for one finished utterance's PCM.

    Noise here means *steady* noise - fan, hum, hiss, room tone held past
    the VAD tail - not background voices (a diarization problem, see
    speaker.cluster_embeddings) and not transient knocks (the VAD's onset
    requirement already eats those). Conservative on purpose: a clip that
    cannot be measured fails open to transcription.
    """
    pcm_bytes = pcm_bytes or b""
    if not pcm_bytes:
        return True, "empty"
    threshold = _threshold_for(sensitivity)
    frames = _frames(pcm_bytes, samplerate)
    if not any(frame_rms(f) >= threshold for f in frames):
        return True, "no speech frames"
    snr = utterance_snr_db(pcm_bytes, samplerate, sensitivity)
    if snr is not None and snr < snr_db_min:
        return True, "flat: %.1f dB over its own floor" % snr
    return False, ""


class EndpointPolicy:
    """When a VAD pause ends the turn: now, or keep listening.

    ``min_silence_ms`` is today's 800ms tail, so the default policy
    reproduces today's behaviour exactly. ``max_silence_ms`` caps a hold.
    ``endpoint_fn(pause_ms, turn_seconds) -> float`` is the Smart-Turn
    slot: P(turn complete) from audio prosody. ``threshold`` applies to
    the model only; the cap always emits regardless of it.
    """

    def __init__(self, min_silence_ms=DEFAULT_MIN_SILENCE_MS,
                 max_silence_ms=DEFAULT_MAX_SILENCE_MS,
                 endpoint_fn=None, threshold=0.5):
        self.min_silence_ms = float(min_silence_ms)
        self.max_silence_ms = float(max_silence_ms)
        self.endpoint_fn = endpoint_fn
        self.threshold = float(threshold)

    def decide(self, pause_ms, turn_seconds=None):
        """{"emit": bool, "prob": float, "reason": str}. Pure - safe to call
        from the audio callback thread; the model call itself belongs on
        the caller's thread (it costs 12-50ms)."""
        pause_ms = max(0.0, float(pause_ms or 0.0))
        if self.endpoint_fn is not None:
            try:
                prob = float(self.endpoint_fn(pause_ms, turn_seconds))
            except Exception:
                # A failing model must never stall the conversation: emit,
                # and say so, the same fail-open direction as the hear path.
                return {"emit": True, "prob": 1.0, "reason": "endpoint-error-emit"}
            prob = max(0.0, min(1.0, prob))
            if pause_ms >= self.max_silence_ms:
                return {"emit": True, "prob": prob, "reason": "max-silence"}
            if prob >= self.threshold:
                return {"emit": True, "prob": prob, "reason": "model-complete"}
            return {"emit": False, "prob": prob, "reason": "model-hold"}
        if pause_ms >= self.max_silence_ms:
            return {"emit": True, "prob": 1.0, "reason": "max-silence"}
        if pause_ms >= self.min_silence_ms:
            return {"emit": True, "prob": 0.75, "reason": "min-silence"}
        base = self.min_silence_ms if self.min_silence_ms > 0 else 1.0
        return {"emit": False, "prob": 0.5 * pause_ms / base,
                "reason": "pause-short"}
