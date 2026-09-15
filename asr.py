"""Auto-ASR: speech-to-text auto-logging.

Three independent pieces, deliberately decoupled so each is testable on its own:

- ``Vad``: pure PCM-in / WAV-out voice-activity detector. No device access, no
  network. Feed it raw int16 mono frames and it hands back a finished
  utterance as WAV bytes when one ends.
- ``VoiceLogger``: the live orchestration class. Owns a daemon thread that
  opens a ``sounddevice.RawInputStream``, feeds a ``Vad`` instance, and calls
  back into the caller per utterance and per state transition. It does not
  transcribe or log anything itself.
- ``transcribe`` / ``test_capture``: network and one-shot-recording helpers,
  each usable without the other two.

``sounddevice`` is imported lazily (function-local) everywhere it is needed,
so ``import asr`` succeeds on a machine that never installs it, and so a
test suite can exercise ``Vad`` and ``transcribe`` without a microphone or a
working sounddevice install.
"""

import io
import json
import struct
import threading
import time
import urllib.error
import urllib.request
import uuid
import wave


class Vad:
    """Feed short chunks of raw int16 mono PCM; get back finished utterances.

    ``feed()`` is sized for ~30ms frames: at 16kHz mono int16 that is 480
    samples / 960 bytes per call. That is the frame size the timing
    constants below (onset, end-silence, hard cap) are tuned against, and
    what ``VoiceLogger`` feeds it in practice. A different frame size still
    works (RMS and duration are computed from the actual byte length of
    whatever is passed in) but timing will be quantized to that frame size
    instead of ~30ms.

    No dependency on sounddevice or any other I/O - safe to unit test with
    synthetic bytes.
    """

    def __init__(self, samplerate=16000, sensitivity=50):
        self.samplerate = samplerate
        sensitivity = max(0, min(100, sensitivity if sensitivity is not None else 50))
        # sensitivity 0..100 -> RMS threshold 2000..200, linear and inverted:
        # sensitivity=0 requires a loud voice (threshold 2000), sensitivity=100
        # picks up a whisper (threshold 200). Higher sensitivity = lower threshold.
        self.threshold = 2000 - 18 * sensitivity

        self._onset_ms_required = 300.0
        self._end_silence_ms_required = 800.0
        self._max_utterance_ms = 30000.0
        self._preroll_ms_target = 300.0

        self._voiced_ms = 0.0
        self._silence_ms = 0.0
        self._utterance_ms = 0.0
        self._in_utterance = False
        self._frames = []  # frames captured since utterance start (pre-roll included)
        self._preroll = []  # rolling buffer of recent frames while not in an utterance

    @staticmethod
    def _rms(frame_bytes):
        count = len(frame_bytes) // 2
        if count == 0:
            return 0.0
        samples = struct.unpack("<%dh" % count, frame_bytes[: count * 2])
        total = sum(s * s for s in samples)
        return (total / count) ** 0.5

    def _frame_ms(self, frame_bytes):
        return (len(frame_bytes) // 2 / self.samplerate) * 1000.0

    def feed(self, frame_bytes):
        """Feed one chunk of raw int16 mono PCM.

        Returns complete utterance WAV bytes when an utterance just ended
        (either by trailing silence or by hitting the 30s hard cap), else
        None.
        """
        frame_ms = self._frame_ms(frame_bytes)
        if frame_ms <= 0:
            return None
        voiced = self._rms(frame_bytes) >= self.threshold

        if not self._in_utterance:
            self._preroll.append(frame_bytes)
            kept, kept_ms = [], 0.0
            for f in reversed(self._preroll):
                kept.append(f)
                kept_ms += self._frame_ms(f)
                if kept_ms >= self._preroll_ms_target:
                    break
            self._preroll = list(reversed(kept))

            self._voiced_ms = self._voiced_ms + frame_ms if voiced else 0.0

            if self._voiced_ms >= self._onset_ms_required:
                self._in_utterance = True
                self._frames = list(self._preroll)
                self._utterance_ms = sum(self._frame_ms(f) for f in self._frames)
                self._silence_ms = 0.0
                self._preroll = []
                self._voiced_ms = 0.0
            return None

        self._frames.append(frame_bytes)
        self._utterance_ms += frame_ms
        self._silence_ms = 0.0 if voiced else self._silence_ms + frame_ms

        if self._silence_ms >= self._end_silence_ms_required or self._utterance_ms >= self._max_utterance_ms:
            return self._finish()
        return None

    def _finish(self):
        frames, self._frames = self._frames, []
        self._in_utterance = False
        self._voiced_ms = self._silence_ms = self._utterance_ms = 0.0
        self._preroll = []
        return _pcm_to_wav(b"".join(frames), self.samplerate)


def _pcm_to_wav(pcm_bytes, samplerate):
    bio = io.BytesIO()
    with wave.open(bio, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(samplerate)
        wf.writeframes(pcm_bytes)
    return bio.getvalue()


class VoiceLogger:
    """Live capture + VAD orchestration. Does not transcribe or log.

    ``cfg``: the asr config dict - keys read are ``sensitivity`` (0-100,
        passed to ``Vad``) and ``device`` (sounddevice device id/name, or
        None/"" for the default input device). ``endpoint``/``model``/
        ``api_key``/``language`` are not read here; they belong to
        ``transcribe``.
    ``on_utterance(wav_bytes)``: called once per detected utterance, from the
        capture thread, with complete WAV bytes. This class does not call
        ``transcribe`` itself - that, and logging the result, is the
        caller's job, done after this callback returns.
    ``on_state(state, detail)``: called on every state transition, from the
        capture thread. States emitted here: "listening" (stream open, no
        utterance in progress - emitted once right after the stream opens,
        and again after every ``on_utterance`` call returns), "error" (any
        failure - sounddevice not importable, device/stream open failure, an
        exception from the callback or from ``on_utterance``/``on_state``
        itself; ``detail`` is ``str(exception)`` and never includes an API
        key, which isn't in scope at this layer), and "off" (emitted once
        from ``stop()``, after the stream/thread is actually torn down).
        "transcribing" is intentionally not emitted here - the caller emits
        that itself, if it wants to, between ``on_utterance`` firing and its
        own call to ``transcribe()``.
    """

    def __init__(self, cfg, on_utterance, on_state):
        self.cfg = dict(cfg or {})
        self.on_utterance = on_utterance
        self.on_state = on_state
        self._thread = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    def start(self):
        """Start the capture thread.

        Idempotent: if a capture thread is already running, this is a no-op
        (call ``stop()`` first if you want to restart with new config).
        The sounddevice import and the ``RawInputStream`` open happen inside
        the spawned thread, not here - so a sounddevice import failure, a
        missing device, or any other startup error surfaces only via
        ``on_state("error", ...)``, never as an exception raised out of
        ``start()``.
        """
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._stop_event = threading.Event()
            thread = threading.Thread(target=self._run, daemon=True)
            self._thread = thread
        thread.start()

    def stop(self):
        """Stop the capture thread and emit on_state("off", "")."""
        with self._lock:
            thread = self._thread
            self._stop_event.set()
        if thread is not None:
            thread.join(timeout=5)
        with self._lock:
            self._thread = None
        self._emit_state("off", "")

    def _emit_state(self, state, detail):
        try:
            self.on_state(state, detail)
        except Exception:
            pass  # a broken UI callback must not take down the capture thread

    def _handle_utterance(self, utterance):
        """Runs on its own short-lived thread, spawned per utterance from the
        audio callback - never on the audio callback itself. This is what
        keeps ``on_utterance`` (transcription, a slow network call) off the
        real-time capture thread; see the comment at the call site."""
        try:
            self.on_utterance(utterance)
        except Exception as e:
            self._emit_state("error", str(e))
        self._emit_state("listening", "")

    def _run(self):
        try:
            import sounddevice as sd
        except Exception as e:
            self._emit_state("error", "sounddevice is not available: %s" % e)
            return

        samplerate = 16000
        blocksize = int(samplerate * 0.03)  # ~30ms frames = 480 samples / 960 bytes
        vad = Vad(samplerate=samplerate, sensitivity=self.cfg.get("sensitivity", 50))
        device = self.cfg.get("device") or None
        stop_event = self._stop_event

        def callback(indata, frames, time_info, status):
            if stop_event.is_set():
                return
            try:
                utterance = vad.feed(bytes(indata))
            except Exception as e:
                self._emit_state("error", str(e))
                return
            if utterance is not None:
                # PortAudio's callback must return promptly - on_utterance
                # (transcription, an up-to-60s network call in practice) is
                # therefore handed to its own thread rather than run inline
                # here, so a slow transcription cannot block/overflow the
                # real-time audio stream and drop the next utterance's audio.
                threading.Thread(target=self._handle_utterance,
                                 args=(utterance,), daemon=True).start()

        try:
            stream_kwargs = dict(
                samplerate=samplerate,
                channels=1,
                dtype="int16",
                blocksize=blocksize,
                callback=callback,
            )
            if device is not None:
                stream_kwargs["device"] = device
            with sd.RawInputStream(**stream_kwargs):
                self._emit_state("listening", "")
                while not stop_event.is_set():
                    time.sleep(0.1)
        except Exception as e:
            self._emit_state("error", str(e))


def list_devices():
    """Return [{"id": <int>, "name": <str>}, ...] for input-capable devices.

    Swallows any failure (sounddevice not installed, no audio subsystem,
    query error) and returns [] instead - this must work on a
    microphone-less/sounddevice-less dev machine.
    """
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        return [
            {"id": idx, "name": d.get("name", "")}
            for idx, d in enumerate(devices)
            if d.get("max_input_channels", 0) > 0
        ]
    except Exception:
        return []


def _multipart_body(fields, files):
    """Hand-build a multipart/form-data body (no requests/urllib3 helper in stdlib).

    ``fields``: {name: str_value}. ``files``: {name: (filename, content_type, bytes)}.
    Returns (body_bytes, content_type_header_value).
    """
    boundary = uuid.uuid4().hex
    parts = []
    for name, value in fields.items():
        parts.append((
            "--%s\r\n"
            "Content-Disposition: form-data; name=\"%s\"\r\n\r\n"
            "%s\r\n" % (boundary, name, value)
        ).encode("utf-8"))
    for name, (filename, content_type, data) in files.items():
        header = (
            "--%s\r\n"
            "Content-Disposition: form-data; name=\"%s\"; filename=\"%s\"\r\n"
            "Content-Type: %s\r\n\r\n" % (boundary, name, filename, content_type)
        ).encode("utf-8")
        parts.append(header + data + b"\r\n")
    parts.append(("--%s--\r\n" % boundary).encode("utf-8"))
    return b"".join(parts), "multipart/form-data; boundary=%s" % boundary


def transcribe(cfg, wav_bytes):
    """POST wav_bytes to <endpoint>/audio/transcriptions. Pure function, no device access.

    cfg keys: endpoint (default "https://api.openai.com/v1", trailing slash
    stripped), model (default "whisper-1"), api_key, language (sent only if
    truthy). Works unmodified against any provider that speaks the same
    OpenAI-shaped multipart contract (e.g. Groq's
    "https://api.groq.com/openai/v1" + "whisper-large-v3-turbo") - no
    provider-specific branching.

    Returns {"text": str} on success, or {"error": str} - mirrors llm.py's
    HTTPError/generic-exception handling shape. The API key is never
    included in a returned error string.
    """
    endpoint = (cfg.get("endpoint") or "https://api.openai.com/v1").strip().rstrip("/")
    model = (cfg.get("model") or "").strip() or "whisper-1"
    api_key = (cfg.get("api_key") or "").strip()
    language = (cfg.get("language") or "").strip()

    fields = {"model": model}
    if language:
        fields["language"] = language
    files = {"file": ("utterance.wav", "audio/wav", wav_bytes)}
    body, content_type = _multipart_body(fields, files)

    url = "%s/audio/transcriptions" % endpoint
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": "Bearer %s" % api_key,
            "Content-Type": content_type,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode("utf-8")
        except Exception:
            detail = ""
        return {"error": "Provider returned HTTP %s: %s" % (e.code, detail[:300])}
    except Exception as e:
        return {"error": "Request failed: %s" % e}
    try:
        return {"text": data["text"]}
    except Exception as e:
        return {"error": "Unexpected provider response: %s" % e}


def test_capture(cfg, seconds=5):
    """Record `seconds` of raw audio (no VAD gating), transcribe it, return the result.

    Backs a "Test N seconds" UI button only - never calls on_utterance and
    never logs anything. Lazy-imports sounddevice; if it can't be imported,
    or the recording itself fails, returns {"error": ...} rather than
    raising.
    """
    try:
        import sounddevice as sd
    except Exception as e:
        return {"error": "sounddevice is not installed: %s" % e}

    samplerate = 16000
    device = cfg.get("device") or None
    try:
        stream_kwargs = dict(samplerate=samplerate, channels=1, dtype="int16")
        if device is not None:
            stream_kwargs["device"] = device
        chunks = []
        with sd.RawInputStream(**stream_kwargs) as stream:
            remaining = int(seconds * samplerate)
            chunk_frames = max(1, samplerate // 10)  # ~100ms per read
            while remaining > 0:
                to_read = min(remaining, chunk_frames)
                data, _overflowed = stream.read(to_read)
                chunks.append(bytes(data))
                remaining -= to_read
        pcm_bytes = b"".join(chunks)
    except Exception as e:
        return {"error": "Recording failed: %s" % e}

    wav_bytes = _pcm_to_wav(pcm_bytes, samplerate)
    return transcribe(cfg, wav_bytes)
