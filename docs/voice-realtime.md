# Realtime voice logging: ASR, noise, and multi-speaker strategy

Owner's value proposition: log realtime voice commands **with evidence and the
lowest possible ASR latency**. This note persists the full research behind the
three original challenges (model, training, data) plus the two follow-ups
(noise-vs-command streaming, multi-speaker one-by-one ASR), with every source.
Last section records what is already implemented in this repo vs what is next.

Conventions: severity wherever a trade-off is judged uses
Critical / High / Medium / Low. Latency numbers are CPU unless stated.

---

## 0. Where the latency really is

`trailmark/asr.py::_transcribe_once` POSTs a WAV to
`<endpoint>/audio/transcriptions` (default OpenRouter) with a 60s timeout.
Even a fast server model costs 1-3s per utterance. Any local CPU engine via
`onnxruntime` (already in `requirements.txt`) beats that by ~10x on utterances
of 2-10s. So: keep OpenRouter as fallback, decode locally first.

Correction that saves a dead end: **Cartesia Sonic is TTS, not ASR.**
Sonic / 3.5 / 3.6 is a state-space-model voice *generator* (sub-90ms
time-to-first-audio, 44 languages). There is no open Sonic ASR checkpoint to
download or fine-tune. What transfers is the *idea*: bounded-state streaming
(SSM / sliding-window) instead of full-utterance attention.

---

## 1. Challenge 1 — ASR model (open-source, low-latency)

Fit for Trailmark = Windows CPU, `sherpa-onnx` + `onnxruntime`, VAD
utterances of 2-10s, target <200ms after end-of-speech.

| Model | Params / size | Latency character | Persian today | Verdict |
|---|---|---|---|---|
| **Moonshine v2 Streaming tiny/small/medium** (Useful Sensors, MIT) | 34M / 123M / 245M; tiny ~26MB | Best TTFT. Sliding-window ergodic encoder, 80ms lookahead, incremental cache. Paper: v2-Tiny 50ms vs Whisper-Tiny 289ms (5.8x); v2-Medium 258ms vs Whisper-Large-v3 11286ms (43x). Medium beats Large-v3 on OpenASR (6.65% vs 7.44% WER) at 1/6 params. | English-only; v1 had "Flavors" multilingual (ar/ja/ko/es/...), v2-fa does not exist yet | **Load first for English.** Drops into the `Vad` -> `transcribe()` seam. |
| **Zipformer streaming transducer 20M** (k2/icefall via `sherpa-onnx`) | 20M / ~73MB (~46MB INT8) | Best full-utterance latency. RNN-T/CTC, no autoregressive loop. True chunk streaming (100ms chunks). 12-77 words/s CPU depending on platform; smallest package. | English checkpoint ready; fa = fine-tune via icefall recipe (§2) | **Second load, and the Persian vehicle.** One architecture to carry fa forward. |
| **Whisper `tiny.en` / `base.en`** via faster-whisper (CTranslate2 int8) or sherpa-onnx int8 | 39M / 74M | Good accuracy, bad streaming shape: fixed 30s window, zero-pad waste, autoregressive decoder grows with length. Still ~0.04-0.07 RTF on desktop CPU. | **Best Persian path today.** Every fa result in §2 is Whisper-based. | English now (`base.en`), fa next (small-fa LoRA). Accept the 30s tax until Zipformer-fa lands. |
| **NVIDIA Parakeet TDT 0.6B v2 / Unified streaming 0.6B** (NeMo, FastConformer+TDT/RNNT) | 600M / ~670MB | Excellent GPU streaming (160ms-2s configurable chunk+right-context; unified offline+streaming; WER 5.9 offline / 6.5 at 560ms). | en-only (+25 European langs in v3). fa = heavy custom fine-tune. | **Do not bundle.** Server/GPU option; wrong for a CPU tray app. |
| SenseVoice-Small, Qwen3-ASR 0.6B, MMS/Omnilingual | 234M-1B | Slower or broken-en in independent CPU benches. | Weak fa. | Skip. |

No open SSM-ASR matches transformers on accuracy yet. Mamba-3 (Mar 2026)
open-sourced kernels and shows the fastest prefill+decode at 1.5B for
*language* modeling, but nobody has published a competitive Mamba-ASR
checkpoint. Moonshine v2's position-free sliding window is the closest
deployed equivalent of the bounded-state idea.

Integration note: `Vad` already emits complete WAVs and
`VoiceLogger._handle_utterance` (`asr.py`) already threads transcription off
the audio callback. That is the seam for a local engine: replace
`_transcribe_once` with a `sherpa-onnx` Offline/OnlineRecognizer when
`cfg["endpoint"]=="local"`, keep the OpenRouter POST as fallback. No UI
change needed.

---

## 2. Challenge 2 — Training (teach it quality Persian)

### 2a. Whisper fine-tune — fastest win, do first

- **Method:** encoder-decoder cross-entropy, base frozen, LoRA/QLoRA
  adapters. Standard fa recipe: `r=32, alpha=64, dropout=0.05` on
  `q_proj+v_proj` only = ~1% of params.
- **Code:** HF `transformers` + `peft`. Copyable repos:
  `Amir-Mohseni/Whisper-Persian` (config.yaml, 500 steps ~= 2h on L4,
  25.8% WER on FLEURS-fa) and `hosseinzr/neyshekar-whisper-large-v3-lora`
  (best documented fa run).
- **Data/label:** 16kHz mono WAV + normalized text. Normalization is the
  whole game: hazm orthography, Arabic ي/ك -> Persian ی/ک, **numbers
  expanded to words** (a digit in output = convention not learned), ZWNJ
  kept. Evaluate WER *and* CER *and* ZWNJ-count — the Neyshekar run went
  37%->8.7% WER but the real signal was 0->116 correct ZWNJs.
- **Time:** small/medium: hours on 1xL4 (500-6000 steps, batch 8-32,
  LR 1e-5-3e-5, early-stop on val WER, patience 3). large-v3 QLoRA on 33k
  Neyshekar clips: **14h19m on 1xL4, peak 5.5GB**, best checkpoint by WER
  not loss. Caveat (Swiss-German sister study): sentence-level-only
  fine-tune destroys long-form segmentation — mix in 30s concatenated
  long-form + a little German/CommonVoice to prevent forgetting.
- **Expectation:** 30-80h clean fa gets a small model past base large-v3
  on fa. `C1Tech/whisper_base_persian` (74M) already beats `large-v3`
  (1550M) on fa benchmarks.

### 2b. Zipformer fine-tune — streaming-fa vehicle, do second

- **Method:** transducer (pruned RNN-T) + CTC auxiliary + SpecAugment.
  Lhotse `CutSet`, SentencePiece BPE 500-2000.
- **Code:** `icefall/egs/librispeech/ASR/zipformer/finetune.py
  --do-finetune 1 --finetune-ckpt <en-pretrained.pt> --base-lr 0.0045`
  (~=1/10 of pretrain LR). New language = new BPE -> re-init
  `decoder+joiner` from scratch (`--init-modules encoder`), keep encoder.
  Adapter variant (`zipformer_adapter/train.py --use-adapters 1
  --adapter-dim 8`) trains **1.15% of params** at near-full accuracy.
- **Data/label:** NeMo-style JSONL `{audio_filepath, duration, text}` +
  `bpe.model`. Same fa normalization as §2a.
- **Time:** 20-30 epochs. <50h adaptation = hours on 2 GPUs; 500-1000h
  new-language = days on 4-8xA100. Heavier than Whisper-LoRA but yields
  the only true-streaming fa model.

### 2c. NeMo Parakeet fine-tune — only if GPU-server

- **Code:** `examples/asr/speech_to_text_finetune.py --config-path ...
  init_from_pretrained_model=nvidia/parakeet-tdt-0.6b-v2
  model.train_ds.manifest_filepath=... trainer.devices=1
  trainer.max_epochs=50`, LR 1e-5-1e-4, `change_vocabulary()` + weight
  transplant on tokenizer expansion (see `jeremy110/Finetune_Nemo_ASR` +
  NeMo issue #13825).
- **Cost warning from practitioners:** 100h is *not enough* for a new
  language on 0.6B (expect ~20% WER only at 1000h+); first loss drop at
  10-20k steps, ~100k steps total; 24GB cards must freeze half the
  encoder + AdamW-8bit + Lhotse dynamic batching. Days on A100, weeks on
  4090.

### 2d. Who manages high quality from low-resource data (fa + ar proxy)

- **Persian builders:** `amirivojdan/shekar-ai` (Neyshekar crowdsourcing,
  CC0, informal classifier + NER in release stats), `hosseinzr` (QLoRA
  recipe), `C1Tech`, `srezas`, `MohammadGholizadeh` (FLEURS-fa), `Peacockery`
  (985h merged corpus + "scribe v4" double-ASR agreement filter — copy this
  filter).
- **Arabic playbook (transferable, ACL/Interspeech 2025):** Casablanca
  corpus (48h fully-supervised, 8 dialects, EMNLP 2024) + NADI 2025 shared
  task. Winning patterns: (1) **15k h weakly-labeled pretrain -> 3k h
  filtered fine-tune**, Conformer-CTC 121M on 8xA100 bf16 = best avg WER
  (Munsit); (2) per-dialect SeamlessM4T-v2 fine-tune 6 epochs when a
  dialect has >200h, **pooled multi-dialect when <10h** (pooled loses only
  ~8% WER vs specialist but wins zero-shot); (3) w2v-BERT-2.0 580M CTC +
  dialect 3-gram LM + kNN voice-conversion augmentation = best
  data-constrained entry; (4) always validate **CER as well as WER** —
  lowest-WER checkpoint != lowest-CER, and CER early-stopping overfits
  less on tiny data. Their augmentation stack (speed perturb + additive
  noise + freq mask + chunk dropout + VC) is exactly how to stretch 40-80h
  of fa.

---

## 3. Challenge 3 — Data (gather, label, synthesize)

### 3a. Labeled fa downloadable today

| Corpus | Hours | Notes |
|---|---|---|
| Common Voice fa v27 | 431h total / 373h validated, 4668 speakers | CC0, read speech, backbone of every fa run |
| `argoveziriii/farsi-asr-unified-cleaned` | **1393h**, 1.28M clips, parquet 16kHz | Largest ready-to-train fa dump |
| `Peacockery/farsi-asr-corpus-v4` | **985h** across 7 corpora (CV25 324h + Thomcles 298h + YouTube 205h + Mana-TTS 97h + Neyshekar 37h + FLEURS 13h + WorldSpeech 11h) | CTC-normalized, machine labels verified by independent Scribe pass |
| ParsVoice (audiobooks) | **2178h**, 1.36M segments, 1803 speakers | Gated, non-commercial research only — pretrain OK, check license before shipping |
| Mana-TTS | 114h single-speaker | CC0 — better as TTS seed than ASR train |
| Neyshekar v5/v6 | 63-79h, 40-50k clips, 35% informal | CC0, best-curated small set, has the informal/colloquial split voice commands need |
| FLEURS `fa_ir` | ~13h | CC-BY, use as held-out eval, not train |

### 3b. Unlabeled at scale + LLM labeling + distillation

- **Scrape pattern (copy ParsVoice):** VAD segment -> ASR pseudo-label ->
  ParsBERT completion classifier -> binary-search boundary opt -> ECAPA-TDNN
  speaker ID -> quality filter. Turns raw YouTube/podcast/audiobook hours
  into `manifest.jsonl` with no hand-labeling.
- **Double-pass agreement (Peacockery scribe-v4):** two independent ASR
  passes, keep only agreeing pairs. Cheap hallucination killer.
- **Normalized Intelligibility gate (EMNLP 2025 Speech Back-Translation):**
  `WER_synth / WER_real` judged by Whisper-large-v3; threshold ~= 0.01 —
  below it, synthetic data *hurts*.
- **Self-refining loop (Twister, 2025):** ASR pseudo-labels -> train TTS ->
  synthesize from large text -> filter/align/augment -> retrain ASR. 6k h
  unlabeled -> **20% err reduction, 50% on code-switch, 10x less real
  data** than pure pseudo-label distillation. Reference: Whisper-large-v3
  itself used 1M h real + 4M h pseudo.
- **Scaling law (Interspeech 2025):** MSE-TTS beats diffusion-TTS under
  ~500h TTS-train; diffusion wins past ~1000h; **TTS must be trained on
  more hours than the ASR will consume**, else synthetic-only training is
  2x worse than real. As *augmentation* (not replacement), expect 30-60%
  relative WER gain — EMNLP 2025 generated 500k h synth in 10 langs from
  tens of hours of seed via XTTS (freeze tokenizer+vocoder, expand BPE,
  fine-tune transformer only on 20-100h) and cut errors >30%.
- **If naive synth fails, add R2S alignment (Interspeech 2025):**
  gradient-reversal + RVQ-CTC discrete-token guidance = +4-5% where plain
  augmentation gave zero.

---

## 4. Challenge 4 — Noise vs voice command, streaming (no waiting)

Current `Vad` (`asr.py`) is energy-only: RMS threshold, 300ms onset, 800ms
end-silence. Loud noise opens utterances; the 800ms tail delays every
command. Fix in three layers, in signal order:

1. **Enhance first (10-32ms, CPU ONNX).** DeepFilterNet3
   (`deepfilter-stream`: 512-sample hop = 10.7ms, ~32ms end-to-end,
   ~0.145 RTF, 16+ streams/CPU; `atten_lim_db=12-20` to blend dry signal
   back so command onsets survive) or DPDFNet `StreamEnhancer` (first
   output after one 20ms window, then ~10ms/blocks). One stream per mic
   thread (GRU state is per-stream). Honest limit: DFN removes stationary
   *and* non-stationary noise but **not background voices** — that is §5's
   job. Cheapest fallback: WebRTC APM (high-pass + NS + AGC).
2. **Neural frame VAD instead of RMS.** Silero v5/v6 (~300K params,
   ~1.2MB, 32ms chunks, LSTM state carried, ~23x realtime, onset 0.5 /
   offset 0.35) or MarbleNet v2 (91.5K params, 20ms frames, trained with
   white+real noise and cough/laugh/breath negatives). Same `feed()`
   interface, probability instead of energy. State machine:
   `silence -> pendingSpeech -> speech -> pendingSilence`
   (`min-speech 250ms, min-silence 100-400ms`).
3. **Endpoint semantically (the "don't wait" trick).** A VAD only hears
   silence; people pause mid-sentence. Run a turn-completion model **once
   per VAD pause** on the last <=8s of the turn: Pipecat Smart Turn
   v3/v3.2 (Whisper-Tiny encoder + head, **8M params / 8MB**, ONNX CPU
   **12-36ms**, 23 languages, ~93%) — `p >= 0.5` emits now, below holds
   (cap `maxSilence 2.0s`); resuming speech continues the same segment.
   Alternatives: LiveKit EOU (text-based, -85% interruptions), VideoSDK
   NAMO (<19ms single-lang), Mimi-codec endpointer + label-delay training
   (-42.7% cutoff error at 160ms median). Net: 800ms tail -> ~160ms median
   + one 12-50ms call. With **partial ASR** (Moonshine-v2 streaming /
   Zipformer online prefix hypotheses), `voicecmd.parse` already matches
   `wake/bare` forms before the endpoint fires; only `argument` form waits
   for the Jev second opinion (6s timeout, fail-closed to text per
   `judge.py`).

What shipped in this repo *now* (no new models, no downloads):
`trailmark/turn.py` — `NoiseGate`/`is_noise_utterance` (speech_only-empty
or SNR<3dB with a measurable floor; all-loud clips fail open to
transcribe, i.e. today's behaviour) consulted in `hear()` *after* the
speaker gate (privacy order kept: another voice is never sent anywhere)
so pure-noise utterances skip the network call; `EndpointPolicy`
(`min_silence_ms` default 800 = today's tail, `max_silence_ms` 2000,
optional `endpoint_fn` with the Smart-Turn signature so the ONNX model
plugs in without changing callers). Next: per-frame gate inside
`VoiceLogger` callback + DeepFilter/Silero/Smart-Turn ONNX behind these
interfaces.

---

## 5. Challenge 5 — Multiple speakers, ASR'd one by one

Ladder, do not start with overlap:

- **Level 0 (have):** one embedding per finished utterance, owner-or-not
  (`speaker.py`, WeSpeaker ResNet34, cosine >= 0.55, needs >= 1.0s).
- **Level 1 (ship next, non-overlap):** diarization + ASR fan-out — same
  PCM to STT (words+timestamps) and diarization (speaker turns), attribute
  words by timestamp overlap. Cloud reference: **pyannote Live-1** (GA Jul
  2026, 100ms WebSocket chunks, sub-300ms, 8 speakers / 10 streams / 5h,
  DIHARD-III **19.8% DER vs 31-39%** for Deepgram/AssemblyAI/Speechmatics,
  gap in missed speech 7.7% vs 20-25%). Local/open: DIART (first open
  streaming, heavier sliding windows), NeMo Streaming Sortformer
  (arrival-order cache, ~1s latency), DiariZen (offline, for export
  re-label). Identity stability across chunks is a *system* property, not
  a model property. Cascade (diarize -> transcribe per segment) still
  beats end-to-end on non-overlap (TagSpeech/AMI: cascade -1.8% DER;
  end-to-end only wins 2-4-speaker overlap, up to 20 points there).
- **Level 2 (true overlap, only if meetings demand it):**
  BUTSpeechFIT DiCoW/SE-DiCoW (STNO masks + FDDT + self-enrollment,
  Apache 2.0, no enrollment needed); NeMo streaming multitalker Parakeet
  (Sortformer activity -> speaker-kernel injection, one instance per
  speaker, 0.08-1.12s); SA-DiCoW+SOT joint decoding (best on synthetic
  LibriMix, but separate-per-speaker still wins on real AMI/NOTSOFAR —
  evidence for staying cascaded); cheapest practical: frozen SI model +
  **769-param overlap head** -> FiLM speaker-conditioned model per
  embedding *only* on overlap segments (68.0%->35.8% WER on overlap at
  +44% compute).

What shipped in this repo *now*: `speaker.cluster_embeddings` /
`label_utterances` (greedy cosine clustering, stable SPEAKER_00.. ids,
`None` -> unknown) + held-clip speaker labels (`Speaker B/C/...`, owner
is A) in `held_list()` and the held push message. No store migration:
entries untouched, held stays memory-only, embeddings stored privately
for clustering and stripped from the bridge payload like `wav`.

Evaluate with three numbers: VAD (missed-utterance / false-segment /
front-clip p95 / endpoint p95), endpointing (`ep50/ep90/ep-cutoff`),
diarization (DER = false-alarm + missed + confusion, per-domain, overlap
split out). No streaming DER + latency pair = batch model in costume.

---

## 6. Build order for Trailmark

1. **Now (English, days):** Moonshine-v2-Tiny streaming locally via
   `sherpa-onnx`, OpenRouter fallback. Measure TTFT after VAD-end;
   target <200ms.
2. **Next (Persian, 1 GPU-week):** Whisper-small/base LoRA on Neyshekar +
   Common Voice fa + FLEURS-train, hazm-normalized, CER-gated eval on
   FLEURS-test. Ship int8.
3. **Then (streaming fa, 2-4 GPU-weeks):** Zipformer fine-tune from en
   checkpoint with fresh fa BPE (or adapters first).
4. **Noise/no-wait (done: heuristic gate + endpoint contract; next:**
   DeepFilter-LL + Silero + Smart-Turn ONNX behind `turn.py`).
5. **Multi-voice (done: utterance clustering + held labels; next:**
   streaming diarization sidecar, overlap-gated target-speaker pass).
6. **Flywheel:** opt-in command utterances -> scribe-v4 pseudo-label pool
   -> XTTS back-translation for rare phrasings (`tab <name>`) -> retrain.
   100h of filtered command-domain audio beats 1000h of generic read
   speech for *your* WER.

---

## 7. Sources

### Cartesia / SSM (why Sonic is not the answer, what transfers)

- Sonic announcement (SSM voice generation, 135ms TTS latency):
  https://cartesia.ai/blog/sonic
- Mamba-3 (inference-first SSM, open kernels):
  https://www.cartesia.ai/blog/mamba-3
- Sonic 3.5 docs (sub-90ms, 42 languages):
  https://docs.cartesia.ai/build-with-cartesia/tts-models/sonic-3-5
- Sonic 3.6 announcement: https://www.cartesia.ai/blog/sonic-3.6
- Sonic product page: https://www.cartesia.ai/sonic
- Sonic 3.6 docs (44 languages): https://docs.cartesia.ai/build-with-cartesia/tts-models/latest
- Realistic TTS page: https://www.cartesia.ai/product/realistic-text-to-speech
- Mamba survey (ACM): https://dl.acm.org/doi/full/10.1145/3819582

### Low-latency open ASR

- Moonshine v2 paper (ergodic streaming encoder):
  https://arxiv.org/html/2602.12241v1
- Moonshine v2 repo: https://github.com/moonshine-ai/moonshine-v2/
- Moonshine repo: https://github.com/moonshine-ai/moonshine/
- Moonshine streaming medium (HF): https://huggingface.co/moonshine-ai/moonshine-streaming-medium
- Moonshine Voice launch (HF blog):
  https://huggingface.co/blog/UsefulSensors/announcing-moonshine-voice
- Moonshine Streaming docs (HF):
  https://huggingface.co/docs/transformers/en/model_doc/moonshine_streaming
- Flavors of Moonshine (language-specific small models): arXiv:2509.02523
- Parakeet unified streaming 0.6b (HF):
  https://huggingface.co/nvidia/parakeet-unified-en-0.6b
- sherpa-onnx Whisper tiny.en: https://k2-fsa.github.io/sherpa/onnx/pretrained_models/whisper/tiny.en.html
- sherpa-onnx Whisper ONNX export: https://k2-fsa.github.io/sherpa/onnx/pretrained_models/whisper/export-onnx.html
- sherpa-onnx Whisper index: https://k2-fsa.github.io/sherpa/onnx/pretrained_models/whisper/index.html
- sherpa-onnx repo: https://github.com/k2-fsa/sherpa-onnx/
- sherpa-onnx Whisper CER issue (mel-padding finding): https://github.com/k2-fsa/sherpa-onnx/issues/2900
- sherpa docs source (tiny.en.rst): https://github.com/k2-fsa/sherpa/blob/32ca9847/docs/source/onnx/pretrained_models/whisper/tiny.en.rst
- faster-whisper: https://github.com/SYSTRAN/faster-whisper
- faster-whisper on CPU (ARM guide): https://learn.arm.com/learning-paths/laptops-and-desktops/dgx_spark_voicechatbot/2_setup/
- Offline transcription CPU benchmark (VoicePing): https://voiceping.net/en/blog/research-offline-speech-transcription-benchmark/

### NeMo / Parakeet training

- NeMo fine-tuning docs: https://docs.nvidia.com/nemo/speech/3.0.0/asr/fine_tuning.html and https://docs.nvidia.com/nemo/speech/nightly/asr/fine_tuning.html
- Riva Parakeet fine-tune tutorial: https://docs.nvidia.com/deeplearning/riva/archives/2-24-0/tutorials/asr-finetune-parakeet-nemo.html
- Riva tutorial notebook: https://github.com/nvidia-riva/tutorials/blob/main/asr-finetune-parakeet-nemo.ipynb (and r2.18.0 copy)
- Parakeet TDT 0.6B v2 collection (NGC): https://catalog.ngc.nvidia.com/orgs/nvidia/-/collections/parakeet-tdt-0.6b-v2/-
- Parakeet v2 TDT fine-tune WER thread (100h vs 1000h, AdamW-8bit, vocab merge): https://github.com/NVIDIA-NeMo/Speech/issues/13825
- Community NeMo vocab-expansion scripts: https://github.com/jeremy110/Finetune_Nemo_ASR

### Persian datasets

- Common Voice fa v26 (431h/373h validated): https://mozilladatacollective.com/datasets/cmqinhw5100v8nr07gyg5gi4v
- Common Voice fa v27: https://mozilladatacollective.com/datasets/cmu5xazgy00finq074vaqo1b3
- Common Voice fa portal: https://commonvoice.mozilla.org/fa/datasets
- Peacockery farsi-asr-corpus-v4 (985h, 7 corpora, scribe-v4): https://huggingface.co/datasets/Peacockery/farsi-asr-corpus-v4
- Common Voice 25 Persian raw: https://huggingface.co/datasets/Reza2kn/Common-Voice-25-Persian-Raw
- FLEURS Farsi full: https://huggingface.co/datasets/MohammadGholizadeh/fleurs-farsi-full
- FLEURS Farsi: https://huggingface.co/datasets/MohammadGholizadeh/fleurs-farsi
- Farsi ASR unified cleaned (1393h parquet): https://huggingface.co/datasets/argoveziriii/farsi-asr-unified-cleaned
- Common Voice 26 Persian clean (43h subset): https://huggingface.co/datasets/pymmdrza/Common-Voice-Speech-26.0-Persian-Clean
- Mana-TTS (114h single-speaker, CC0): https://huggingface.co/datasets/MahtaFetrat/Mana-TTS
- ParsVoice (2178h audiobooks, gated non-commercial): https://huggingface.co/datasets/MohammadJRanjbar/ParsVoice
- Neyshekar repo: https://github.com/amirivojdan/neyshekar
- Neyshekar v5 (HF): https://huggingface.co/datasets/shekar-ai/neyshekar-v5-persian-asr-fa
- Neyshekar (Zenodo): https://zenodo.org/records/22223171

### Persian / low-resource training evidence

- Neyshekar Whisper-large-v3 QLoRA (37%->8.7% WER, ZWNJ learning, 14h on L4): https://huggingface.co/hosseinzr/neyshekar-whisper-large-v3-lora
- Whisper-medium fa LoRA (CV17+FLEURS): https://huggingface.co/srezas/whisper-medium-fa-cv17-fleurs-lora
- Whisper-base Persian (74M beats large-v3 on fa): https://huggingface.co/C1Tech/whisper_base_persian
- Whisper Persian fine-tune + quantize pipeline: https://github.com/Amir-Mohseni/Whisper-Persian
- Optuna-LoRA for low-resource Whisper (Appl. Sci. 2025): https://www.mdpi.com/2076-3417/15/24/13090
- Swiss-German long-form Whisper fine-tune (sentence-to-long-form generation, forgetting): https://www.swisstext.org/wp-content/uploads/2025/05/Fine-tuning-Whisper-on-Low-Resource-Languages-for-Real-World-Applications.pdf
- CBA-Whisper AdaLoRA + curriculum (Interspeech 2025): https://www.isca-archive.org/interspeech_2025/tan25b_interspeech.pdf

### Zipformer / icefall training

- Zipformer supervised fine-tune recipe: https://k2-fsa.github.io/icefall/recipes/Finetune/from_supervised/finetune_zipformer.html
- Same (source rst): https://github.com/k2-fsa/icefall/blob/master/docs/source/recipes/Finetune/from_supervised/finetune_zipformer.rst
- `egs/librispeech/ASR/zipformer/finetune.py`: https://github.com/k2-fsa/icefall/blob/master/egs/librispeech/ASR/zipformer/finetune.py
- `egs/librispeech/ASR/zipformer/train.py`: https://github.com/k2-fsa/icefall/blob/master/egs/librispeech/ASR/zipformer/train.py
- Adapter fine-tune (1.15% params): https://k2-fsa.github.io/icefall/recipes/Finetune/adapter/finetune_adapter.html
- Librispeech RESULTS (commands, mux, beams): https://github.com/k2-fsa/icefall/blob/master/egs/librispeech/ASR/RESULTS.md
- GigaSpeech Zipformer train: https://github.com/k2-fsa/icefall/blob/master/egs/gigaspeech/ASR/zipformer/train.py
- Streaming Zipformer transducer: https://icefall.readthedocs.io/en/latest/recipes/Streaming-ASR/librispeech/zipformer_transducer.html

### Arabic / dialect low-resource playbook

- Dialectal coverage and generalization (ACL 2025): https://aclanthology.org/2025.acl-long.1427.pdf
- Overcoming data scarcity via Whisper fine-tune (arXiv 2506.02627 + Interspeech 2025): https://arxiv.org/pdf/2506.02627v1.pdf and https://www.isca-archive.org/interspeech_2025/ozyilmaz25_interspeech.pdf
- NADI 2025 shared task: https://arxiv.org/html/2509.02038v2
- Munsit NADI 2025 (weakly-supervised pretrain + continual fine-tune): https://aclanthology.org/2025.arabicnlp-sharedtasks.100/
- Casablanca corpus (48h, 8 dialects, EMNLP 2024): https://p.rst.im/q/aclanthology.org/2024.emnlp-main.1211.pdf
- ELYADATA-LIA NADI 2025 (per-dialect SeamlessM4T-v2): https://aclanthology.org/2025.arabicnlp-sharedtasks.105.pdf
- BYZÖ NADI 2025 (CTC + voice-conversion augmentation, CER stopping): https://aclanthology.org/2025.arabicnlp-sharedtasks.102.pdf

### Synthetic data / distillation / pseudo-labeling

- Self-refining ASR with TTS (Twister): https://arxiv.org/html/2506.11130v2
- R2S real-to-synthetic alignment (Interspeech 2025): https://www.isca-archive.org/interspeech_2025/tran25_interspeech.pdf
- Purely synthetic training data (RWTH): https://arxiv.org/html/2407.17997v1
- Scaling laws for synthetic speech (Interspeech 2025): https://www.isca-archive.org/interspeech_2025/minixhofer25_interspeech.html and https://www.isca-archive.org/interspeech_2025/minixhofer25_interspeech.pdf
- Speech Back-Translation at scale (EMNLP 2025): https://aclanthology.org/2025.emnlp-main.629.pdf
- TTS+LLM conversational data (SynData4GenAI 2024): https://www.isca-archive.org/syndata4genai_2024/cornell24_syndata4genai.pdf
- ICASSP 2024 accepted papers (incl. synthetic-speech impact study): https://cmsworkshops.com/ICASSP2024/papers/accepted_papers.php

### Streaming VAD

- MarbleNet v2 frame VAD (HF): https://huggingface.co/nvidia/Frame_VAD_Multilingual_MarbleNet_v2.0/blob/7e42e3ab5f5b5ee95d2815c2e15c4ea8a6519c6a/README.md
- VAD ONNX collection (MarbleNet/FSMN/Silero/DFSMN/FireRed/SmartTurn): https://github.com/DakeQQ/Voice-Activity-Detection-VAD-ONNX
- Streaming MarbleNet small VAD (HF): https://huggingface.co/Mayank022/voice-activity-detection-marblenet
- Silero VAD v6 streaming contract (HF): https://huggingface.co/openEuler/silero-vad
- Silero VAD engram (streaming turns): https://github.com/bubustack/silero-vad-engram/blob/main/README.md
- Silero streaming guide (Soniqo): https://soniqo.audio/guides/vad
- LiveKit Silero VAD stream (source): https://cdn.jsdelivr.net/npm/@livekit/agents-plugin-silero@1.2.0/src/vad.ts
- RealTimeCut VAD (Silero + WebRTC APM): https://github.com/jasonz1360/RealTimeCutVADCXXLibrary

### Streaming enhancement

- DeepFilterNet2 paper: https://ar5iv.labs.arxiv.org/html/2205.05474
- deepfilter-stream (ONNX, ~32ms, 7x realtime): https://github.com/wuxuedaifu/deepfilter-stream and https://pypi.org/project/deepfilter-stream/
- deepfilter-rt (split-streaming ONNX): https://github.com/shimondoodkin/deepfilter-rt
- Per-frame DFN3 for Pipecat (~50ms, tract pulsed): https://github.com/vahidkowsari/pipecat-deepfilternet-stream
- DPDFNet (streaming enhancer): https://github.com/ceva-ip/DPDFNet
- DeepFilterNet3 ONNX export (Soniqo): https://huggingface.co/soniqo/DeepFilterNet3-ONNX
- DFN3 serverless worker notes: https://github.com/dwin-gharibi/runpod-deepfilternet

### Streaming diarization

- Streaming product: https://www.pyannote.ai/streaming
- Streaming tutorial: https://docs.pyannote.ai/tutorials/streaming-real-time
- How the streaming model was built: https://www.pyannote.ai/blog/how-we-built-streaming-diarization
- Live-1 launch: https://www.pyannote.ai/blog/introducing-live-1-streaming-diarization
- Live-1 GA: https://www.pyannote.ai/changelog/streaming-diarization-ga
- Streaming beta: https://www.pyannote.ai/changelog/streaming-diarization-beta
- Streaming benchmark (DIHARD-III): https://www.pyannote.ai/blog/streaming-diarization-benchmark
- WebSocket quickstart: https://www.pyannote.ai/blog/websocket-streaming-quickstart

### Endpointing / turn-taking

- Smart Turn repo: https://github.com/pipecat-ai/smart-turn?tab=readme-ov-file
- Smart Turn v3 CPU (12ms): https://www.daily.co/blog/announcing-smart-turn-v3-with-cpu-inference-in-just-12ms/
- NAC streaming endpointer + label-delay: https://arxiv.org/html/2506.07081v1
- Smart Turn v3.2 ONNX (Soniqo): https://huggingface.co/soniqo/Smart-Turn-v3.2-ONNX
- Smart Turn LiveKit plugin: https://pypi.org/project/smart-turn-livekit/
- Turn-taking guide (Soniqo): https://soniqo.audio/guides/turn
- LiveKit EOU transformer: https://livekit.com/blog/using-a-transformer-to-improve-end-of-turn-detection
- NAMO turn detector research: https://github.com/videosdk-live/NAMO-Turn-Detector-v1/blob/main/RESEARCH.md

### Multi-talker / target-speaker ASR

- TS-ASR-Whisper / DiCoW / SE-DiCoW repo: https://github.com/BUTSpeechFIT/TS-ASR-Whisper
- SA-DiCoW (SOT + diarization conditioning): https://arxiv.org/html/2510.03723v2
- NeMo streaming multitalker tutorial: https://github.com/NVIDIA-NeMo/Speech/blob/main/tutorials/asr/Streaming_Multitalker_ASR.ipynb
- Lightweight overlap transcription (SI+SC FiLM): https://arxiv.org/html/2506.20288
- DiCoW app repo: https://github.com/BUTSpeechFIT/DiCoW
- SC-SOT: https://www.alphaxiv.org/abs/2506.12672
- TagSpeech (ACL 2026): https://aclanthology.org/2026.acl-long.1938.pdf
- TargetDiarization (separation + diarization + ASR): https://github.com/jingzhunxue/TargetDiarization
