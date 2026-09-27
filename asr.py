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
- ``LevelMeter`` / ``MicMonitor``: what the microphone is hearing right now,
  as a short rolling waveform, for the live wave in Settings and on the bar.
- ``list_devices`` / ``resolve_device``: one entry per physical input.

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
import unicodedata
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


def wav_to_pcm(wav_bytes):
    """(int16 mono PCM bytes, samplerate) out of a WAV this module wrote."""
    with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
        return wf.readframes(wf.getnframes()), wf.getframerate()


# ---------------------------------------------------------------------------
# What the microphone is hearing
# ---------------------------------------------------------------------------

class LevelMeter:
    """A rolling picture of the last few seconds of audio, for drawing.

    Every 10 ms of audio becomes one bucket holding the lowest and highest
    sample and the RMS, each scaled to -1..1 (0..1 for RMS). That is enough to
    draw the signal as a wave - flat in silence, swelling when someone speaks -
    at a hundred points a second, which is what a 300-pixel strip can show.

    ``threshold`` is the VAD's RMS threshold on the same 0..1 scale, so a
    drawing can mark which buckets were loud enough to count as speech. The
    wave and the sensitivity slider then describe the same thing.

    Written from the audio callback, read from the JS-bridge thread: a lock,
    and ``read`` copies.
    """

    BUCKET_MS = 10
    KEEP = 400          # four seconds of buckets

    def __init__(self, samplerate=16000, threshold_rms=None):
        self.samplerate = samplerate
        self._per_bucket = max(1, samplerate * self.BUCKET_MS // 1000)
        self._lock = threading.Lock()
        self._lo, self._hi, self._rms = [], [], []
        self._seq = 0
        self.threshold = (threshold_rms / 32768.0) if threshold_rms else 0.0

    def feed(self, frame_bytes):
        count = len(frame_bytes) // 2
        if not count:
            return
        samples = struct.unpack("<%dh" % count, frame_bytes[: count * 2])
        lo, hi, rms = [], [], []
        step = self._per_bucket
        for i in range(0, count, step):
            chunk = samples[i:i + step]
            lo.append(min(chunk) / 32768.0)
            hi.append(max(chunk) / 32768.0)
            rms.append((sum(s * s for s in chunk) / len(chunk)) ** 0.5 / 32768.0)
        with self._lock:
            self._lo.extend(lo)
            self._hi.extend(hi)
            self._rms.extend(rms)
            self._seq += len(lo)
            extra = len(self._lo) - self.KEEP
            if extra > 0:
                del self._lo[:extra], self._hi[:extra], self._rms[:extra]

    def read(self, last=300):
        """The newest ``last`` buckets, oldest first, rounded for the bridge."""
        last = max(1, min(int(last or 300), self.KEEP))
        with self._lock:
            lo, hi, rms = self._lo[-last:], self._hi[-last:], self._rms[-last:]
            seq = self._seq
        return {"seq": seq, "bucket_ms": self.BUCKET_MS,
                "threshold": round(self.threshold, 4),
                "lo": [round(v, 3) for v in lo],
                "hi": [round(v, 3) for v in hi],
                "rms": [round(v, 4) for v in rms]}


def speech_only(pcm, sensitivity=50, samplerate=16000, pad_ms=150):
    """The voiced part of a clip: 30 ms frames above the VAD's own threshold,
    each kept with ``pad_ms`` either side, silence between them dropped.

    Used on BOTH sides of the speaker check - the enrollment recordings and
    every utterance checked against them - so the two embeddings are made
    from the same kind of audio. A voiceprint enrolled from clips that were
    half silence would be compared against utterances that are not.
    """
    frame = int(samplerate * 0.03) * 2
    threshold = Vad(samplerate=samplerate, sensitivity=sensitivity).threshold
    frames = [pcm[i:i + frame] for i in range(0, len(pcm) - frame + 1, frame)]
    if not frames:
        return b""
    loud = []
    for f in frames:
        n = len(f) // 2
        samples = struct.unpack("<%dh" % n, f)
        loud.append((sum(x * x for x in samples) / n) ** 0.5 >= threshold)
    pad = max(0, int(round(pad_ms / 30.0)))
    keep = [False] * len(frames)
    for i, on in enumerate(loud):
        if on:
            for j in range(max(0, i - pad), min(len(frames), i + pad + 1)):
                keep[j] = True
    return b"".join(f for f, k in zip(frames, keep) if k)


class MicMonitor:
    """Open a microphone just to watch it - no VAD, no transcription, nothing
    kept. Backs the "Test microphone" wave in Settings.

    Stops itself after ``max_seconds`` so a Settings page left open does not
    hold the microphone forever; the page restarts it if it is still looking.
    """

    def __init__(self, device="", sensitivity=50, max_seconds=30, keep_audio=False):
        self.device = device
        self.sensitivity = sensitivity
        self.max_seconds = max_seconds
        self.meter = LevelMeter(threshold_rms=Vad(sensitivity=sensitivity).threshold)
        self.error = ""
        self.note = ""
        # Enrollment records through this same class: the wave the user sees
        # while reading a sentence is the audio being kept. Off for the plain
        # microphone test, which keeps nothing.
        self.keep_audio = keep_audio
        self._audio = bytearray()
        self._stop = threading.Event()
        self._thread = None
        self._opened = threading.Event()

    @property
    def running(self):
        return bool(self._thread is not None and self._thread.is_alive())

    def start(self, wait=1.5):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        # Wait for the open to succeed or fail, so the caller can say which.
        self._opened.wait(wait)
        return {"ok": not self.error, "error": self.error, "note": self.note}

    def stop(self):
        self._stop.set()
        t = self._thread
        if t is not None:
            t.join(timeout=3)

    def audio(self):
        """What was kept (16 kHz mono int16 PCM), after stop()."""
        return bytes(self._audio)

    def _run(self):
        try:
            import sounddevice as sd
        except Exception as e:
            self.error = "sounddevice is not available: %s" % e
            self._opened.set()
            return
        meter, stop = self.meter, self._stop

        def callback(indata, frames, time_info, status):
            if not stop.is_set():
                meter.feed(bytes(indata))

        try:
            kwargs, self.note = _stream_kwargs(sd, self.device)
            kwargs.update(samplerate=16000, channels=1, dtype="int16",
                          blocksize=480, callback=callback)
            with _ComThread(), sd.RawInputStream(**kwargs):
                self._opened.set()
                deadline = time.time() + self.max_seconds
                while not stop.is_set() and time.time() < deadline:
                    time.sleep(0.05)
        except Exception as e:
            self.error = "Could not open the microphone: %s" % e
        finally:
            self._opened.set()


class VoiceLogger:
    """Live capture + VAD orchestration. Does not transcribe or log.

    ``cfg``: the asr config dict - keys read are ``sensitivity`` (0-100,
        passed to ``Vad``) and ``device`` (sounddevice device id/name, or
        None/"" for the default input device). ``endpoint``/``model``/
        ``api_key``/``language`` are not read here; they belong to
        ``transcribe``.
    ``on_utterance(wav_bytes, seq)``: called once per detected utterance, on
        its own short-lived thread, with complete WAV bytes and its capture
        order (1, 2, 3...). Those threads finish in any order; ``seq`` is how
        the caller puts the results back in the order they were said. This class does not call
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
        # What the open stream is hearing, for the live wave. Fed from the
        # audio callback whether or not anything is being said.
        self.meter = LevelMeter(
            threshold_rms=Vad(sensitivity=self.cfg.get("sensitivity", 50)).threshold)
        # Capture order. Utterances are handed to their own threads and those
        # finish in whatever order the network allows; the caller needs this
        # to put them back in the order they were said.
        self._seq = 0

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

    def _handle_utterance(self, utterance, seq):
        """Runs on its own short-lived thread, spawned per utterance from the
        audio callback - never on the audio callback itself. This is what
        keeps ``on_utterance`` (transcription, a slow network call) off the
        real-time capture thread; see the comment at the call site."""
        try:
            self.on_utterance(utterance, seq)
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
        stop_event = self._stop_event
        meter = self.meter

        def callback(indata, frames, time_info, status):
            if stop_event.is_set():
                return
            data = bytes(indata)
            try:
                meter.feed(data)
                utterance = vad.feed(data)
            except Exception as e:
                self._emit_state("error", str(e))
                return
            if utterance is not None:
                # PortAudio's callback must return promptly - on_utterance
                # (transcription, an up-to-60s network call in practice) is
                # therefore handed to its own thread rather than run inline
                # here, so a slow transcription cannot block/overflow the
                # real-time audio stream and drop the next utterance's audio.
                # The sequence number is taken HERE, on the one thread that
                # sees utterances in the order they were said.
                self._seq += 1
                threading.Thread(target=self._handle_utterance,
                                 args=(utterance, self._seq), daemon=True).start()

        try:
            stream_kwargs, note = _stream_kwargs(sd, self.cfg.get("device"))
            stream_kwargs.update(
                samplerate=samplerate,
                channels=1,
                dtype="int16",
                blocksize=blocksize,
                callback=callback,
            )
            with _ComThread(), sd.RawInputStream(**stream_kwargs):
                self._emit_state("listening", note)
                while not stop_event.is_set():
                    time.sleep(0.1)
        except Exception as e:
            self._emit_state("error", str(e))


# ---------------------------------------------------------------------------
# Which microphones exist
# ---------------------------------------------------------------------------
#
# Windows exposes every input through four audio APIs at once - MME,
# DirectSound, WASAPI and WDM-KS - and PortAudio lists each separately. A
# laptop with one microphone array therefore showed thirteen "microphones",
# several of them the same device under a name MME truncates to 31
# characters. WASAPI is the API that names each endpoint once, in full, so
# the list is built from it alone, and a device is remembered by NAME: the
# indexes shift whenever a USB microphone is plugged in, and a stored index
# silently becomes a different device.
#
# "Stereo Mix" and its relatives are not microphones. They record whatever
# the computer is playing, and Settings promises that Trailmark never listens
# to system audio - so they are left out, not merely sorted last.

_LOOPBACK_WORDS = ("stereo mix", "stereomix", "what u hear", "wave out mix",
                   "loopback", "mixage st", "mezcla est")


def _is_loopback(name):
    n = (name or "").lower()
    return any(w in n for w in _LOOPBACK_WORDS)


def _preferred_hostapi(sd):
    """Index of the WASAPI host API, or None where there is none."""
    try:
        for i, api in enumerate(sd.query_hostapis()):
            if "wasapi" in str(api.get("name", "")).lower():
                return i
    except Exception:
        pass
    return None


def _input_devices(sd):
    """[(index, name, hostapi)] for real microphones on the preferred API.

    Falls back to the default host API when WASAPI is missing, and to every
    API (deduplicated by name) when even that yields nothing.
    """
    devices = list(sd.query_devices())
    want = _preferred_hostapi(sd)
    if want is None:
        try:
            want = sd.default.hostapi
        except Exception:
            want = None
    rows = [(i, str(d.get("name", "")).strip(), d.get("hostapi"))
            for i, d in enumerate(devices)
            if d.get("max_input_channels", 0) > 0
            and not _is_loopback(d.get("name"))]
    picked = [r for r in rows if want is None or r[2] == want]
    if not picked:
        seen, picked = set(), []
        for r in rows:
            if r[1].lower() not in seen:
                seen.add(r[1].lower())
                picked.append(r)
    return picked


def list_devices():
    """[{"id": name, "name": name, "default": bool}] - one per microphone.

    ``id`` is the name, because that is what survives a reboot or a USB
    microphone being plugged in. The system default comes first.

    Swallows any failure (sounddevice not installed, no audio subsystem,
    query error) and returns [] instead - this must work on a
    microphone-less/sounddevice-less dev machine.
    """
    try:
        import sounddevice as sd
        rows = _input_devices(sd)
        default_idx = None
        api = _preferred_hostapi(sd)
        try:
            if api is not None:
                default_idx = sd.query_hostapis(api).get("default_input_device")
        except Exception:
            default_idx = None
        out, seen = [], set()
        for idx, name, _api in rows:
            if name.lower() in seen:
                continue
            seen.add(name.lower())
            out.append({"id": name, "name": name, "default": idx == default_idx})
        out.sort(key=lambda d: not d["default"])
        return out
    except Exception:
        return []


def resolve_device(sd, wanted):
    """(device index or None, extra_settings or None, note) for ``wanted``.

    ``wanted`` is a name from list_devices(), "" for the system default, or -
    from configs written before names were used - a bare index. An index is
    translated to its device's name first, because the index it was saved
    under may now be a different device on a different API.

    A name that is no longer present (the headset was unplugged) falls back
    to the default microphone and says so in ``note``, rather than failing to
    open: the user asked to be listened to.
    """
    wanted = "" if wanted is None else str(wanted).strip()
    if not wanted:
        return None, None, ""
    devices = list(sd.query_devices())
    if wanted.isdigit():
        i = int(wanted)
        if 0 <= i < len(devices) and devices[i].get("max_input_channels", 0) > 0:
            wanted = str(devices[i].get("name", "")).strip()
        else:
            return None, None, "The saved microphone is gone - using the default."
    low = wanted.lower()
    for idx, name, api in _input_devices(sd):
        # MME cuts names at 31 characters, so an old saved name may be a
        # prefix of the full one.
        if name.lower() == low or (len(low) >= 20 and name.lower().startswith(low)):
            extra = None
            if api is not None and api == _preferred_hostapi(sd):
                # WASAPI in shared mode only opens at the device's own rate
                # (48 kHz here) unless asked to convert. The VAD and every
                # transcription endpoint want 16 kHz.
                try:
                    extra = sd.WasapiSettings(auto_convert=True)
                except Exception:
                    extra = None
            return idx, extra, ""
    return None, None, "“%s” is not connected - using the default microphone." % wanted


class _ComThread:
    """COM initialised for the life of a block, on Windows only.

    PortAudio's WASAPI backend talks COM, and COM is initialised only on the
    thread that loaded PortAudio. Every stream here is opened from a worker
    thread, so without this a WASAPI device fails to START (not to open) with
    an "Unanticipated host error" that names WDM-KS - measured, and the reason
    the old list's MME entries appeared to be the only ones that worked.
    """

    def __enter__(self):
        self._hr = None
        try:
            import ctypes
            self._hr = ctypes.windll.ole32.CoInitializeEx(None, 0)
        except Exception:
            self._hr = None
        return self

    def __exit__(self, *exc):
        # S_OK (0) and S_FALSE (1) both take a reference that must be given
        # back; RPC_E_CHANGED_MODE means the thread already had its own.
        if self._hr in (0, 1):
            try:
                import ctypes
                ctypes.windll.ole32.CoUninitialize()
            except Exception:
                pass
        return False


def _stream_kwargs(sd, wanted):
    """Stream arguments for a device, plus a note to show if it fell back."""
    idx, extra, note = resolve_device(sd, wanted)
    kwargs = {}
    if idx is not None:
        kwargs["device"] = idx
    if extra is not None:
        kwargs["extra_settings"] = extra
    return kwargs, note


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


# ---------------------------------------------------------------------------
# Persian or English, and nothing else
# ---------------------------------------------------------------------------
#
# A speech model left to detect the language picks from about a hundred, and
# for this owner it picks wrong in two predictable ways: Persian comes back as
# Arabic or Urdu (same script, different letters, sometimes a translation),
# and accented English comes back as some other Latin-script language. Noise
# comes back as anything at all.
#
# The request can only name one language, so it cannot say "Persian or
# English". What it can do is decode once without a hint and, when the answer
# is outside the two, decode again with the hint that fits. In a world of two
# languages the choice is simple: English is the only one written in Latin
# script, so Latin means English and every other script means Persian. The
# retry costs a second request only when the first one missed.
#
# The check reads the text, not a language field, because the configured
# provider (an OpenAI-shaped endpoint of unknown make) is not guaranteed to
# return one. When it does, it is used.

ALLOWED_LANGUAGES = ("fa", "en")

_LANG_NAMES = {"en": "en", "english": "en", "fa": "fa", "farsi": "fa",
               "persian": "fa", "per": "fa", "fas": "fa", "eng": "en"}

#: Letters Persian has and Arabic does not, and the two Persian forms of
#: yeh and kaf. Their presence settles an Arabic-script transcript as Persian.
_PERSIAN_MARKS = set("پچژگکی")      # پ چ ژ گ ک ی
#: Letters that only turn up when the model decoded Urdu.
_URDU_MARKS = set("ٹڈڑںہھے")    # ٹ ڈ ڑ ں ہ ھ ے
#: Arabic yeh and kaf, teh marbuta, and vowel marks - Arabic output, when
#: nothing Persian is present alongside them.
_ARABIC_MARKS = set("يكة") | {chr(c) for c in range(0x064B, 0x0653)}


def _script_counts(text):
    latin = arabic = other = accented = 0
    for ch in text or "":
        if not ch.isalpha():
            continue
        cp = ord(ch)
        if (0x0600 <= cp <= 0x06FF or 0x0750 <= cp <= 0x077F
                or 0xFB50 <= cp <= 0xFDFF or 0xFE70 <= cp <= 0xFEFF):
            arabic += 1
        elif "LATIN" in unicodedata.name(ch, ""):
            latin += 1
            if cp > 0x7F:
                accented += 1
        else:
            other += 1
    return latin, arabic, other, accented


def language_verdict(text, detected=None, allowed=ALLOWED_LANGUAGES):
    """None when ``text`` is already Persian or English, else the code to
    decode it again in ("fa" or "en").

    ``detected`` is the provider's own language field when it sent one, as a
    code or a name. Pure function - the tests drive it with strings.
    """
    text = (text or "").strip()
    if detected:
        code = _LANG_NAMES.get(str(detected).strip().lower())
        if code in allowed:
            return None
    latin, arabic, other, accented = _script_counts(text)
    if not (latin or arabic or other):
        # Digits, punctuation or nothing. No language to be wrong about -
        # unless the provider said it was something else.
        if detected and _LANG_NAMES.get(str(detected).strip().lower()) not in allowed:
            return "fa" if "fa" in allowed else allowed[0]
        return None
    if other > max(latin, arabic):
        return "fa" if "fa" in allowed else allowed[0]
    if arabic >= latin:
        chars = set(text)
        if chars & _URDU_MARKS:
            return "fa"
        if not (chars & _PERSIAN_MARKS) and (chars & _ARABIC_MARKS):
            return "fa"
        if detected:        # named a language that is not Persian
            return "fa"
        return None
    # Mostly Latin. Persian words mixed in are normal speech for this owner
    # and leave it English. Letters English does not use, or six words with
    # not one English function word among them, send it back. Both tests are
    # tuned to over-fire on purpose: re-decoding English as English returns
    # the same English and costs one request, while missing a French or Dutch
    # decode files a translation the owner never said.
    if accented:
        return "en"
    words = [w.strip(".,!?;:'\"()").lower() for w in text.split()]
    words = [w for w in words if w.isalpha() and w.isascii()]
    if len(words) >= 6 and not (set(words) & _ENGLISH_FUNCTION_WORDS):
        return "en"
    if detected:
        return "en"
    return None


_ENGLISH_FUNCTION_WORDS = set("""
the a an and or but if of to in on at by for with from as is are was were be been
it its this that these those i you he she we they me my your our their not no do
does did have has had can will would should could so than then there here what
which who how why when just also about into over more some any all
""".split())


def transcribe(cfg, wav_bytes):
    """Speech to Persian or English text.

    ``cfg["language"]`` pins one: "fa" or "en". Anything else (the default,
    "") means either of the two - decode once without a hint, and again with
    the right one if the first answer was in a third language. See the
    comment above ``language_verdict``.

    Returns {"text": str, "language": "fa"|"en"|""} or {"error": str}.
    """
    language = (cfg.get("language") or "").strip().lower()
    if language in ALLOWED_LANGUAGES:
        out = _transcribe_once(cfg, wav_bytes, language)
        if "text" in out:
            out["language"] = language
        return out
    first = _transcribe_once(cfg, wav_bytes, "")
    if "error" in first:
        return first
    retry = language_verdict(first.get("text"), first.get("detected"))
    if retry is None:
        return {"text": first["text"], "language": _guess_language(first["text"])}
    second = _transcribe_once(cfg, wav_bytes, retry)
    if "error" in second:
        # The first answer is in a language this app does not take, and the
        # retry failed. Saying so beats filing text nobody asked for.
        return {"error": "Heard something that was neither Persian nor English, "
                         "and the retry failed: " + second["error"]}
    return {"text": second["text"], "language": retry, "retried": True}


def _guess_language(text):
    latin, arabic, _other, _acc = _script_counts(text)
    if not (latin or arabic):
        return ""
    return "fa" if arabic >= latin else "en"


def _transcribe_once(cfg, wav_bytes, language):
    """POST wav_bytes to <endpoint>/audio/transcriptions. Pure function, no device access.

    cfg keys: endpoint (default "https://openrouter.ai/api/v1", trailing slash
    stripped), model (default "whisper-1"), api_key. ``language`` is sent only
    if truthy. Works unmodified against any provider that speaks the same
    OpenAI-shaped multipart contract (e.g. Groq's
    "https://api.groq.com/openai/v1" + "whisper-large-v3-turbo") - no
    provider-specific branching.

    Returns {"text": str, "detected": str} on success, or {"error": str} -
    mirrors llm.py's HTTPError/generic-exception handling shape. The API key
    is never included in a returned error string.
    """
    endpoint = (cfg.get("endpoint") or "https://openrouter.ai/api/v1").strip().rstrip("/")
    model = (cfg.get("model") or "").strip() or "whisper-1"
    api_key = (cfg.get("api_key") or "").strip()
    language = (language or "").strip()

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
        return {"text": data["text"], "detected": str(data.get("language") or "")}
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
    try:
        stream_kwargs, _note = _stream_kwargs(sd, cfg.get("device"))
        stream_kwargs.update(samplerate=samplerate, channels=1, dtype="int16")
        chunks = []
        with _ComThread(), sd.RawInputStream(**stream_kwargs) as stream:
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
