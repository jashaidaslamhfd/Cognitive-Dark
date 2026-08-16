#!/usr/bin/env python3
"""
Coercion Files — Voice Engine (Kokoro primary).

Chain:  Kokoro TTS (open-source, offline, deep authoritative male)
        → edge-tts (Microsoft free endpoint)
        → ElevenLabs (premium, if key set)
        → silence (last resort, but the video builder still works)

Kokoro model files (auto-downloaded on first use, ~360 MB):
  • model : kokoro-v1.0.onnx     (from thewh1teagle/kokoro-onnx releases)
  • voices: voices-v1.0.bin
Set KOKORO_MODEL_DIR to a persistent location (CI: cache/restore step).
"""

import asyncio
import logging
import os
import shutil
import subprocess
import urllib.request
from pathlib import Path

from config.settings import KOKORO_SPEED as _CFG_KOKORO_SPEED

logger = logging.getLogger("tts_engine")

MODEL_URL = ("https://github.com/thewh1teagle/kokoro-onnx/releases/download/"
             "model-files-v1.0/kokoro-v1.0.onnx")
VOICES_URL = ("https://github.com/thewh1teagle/kokoro-onnx/releases/download/"
              "model-files-v1.0/voices-v1.0.bin")

KOKORO_VOICE = os.environ.get("KOKORO_VOICE", "am_fenrir")
# 2026-08-17: weighted voice rotation pool. Fenrir stays the brand voice (~60%
# of videos) for consistency; a small pool of adult EN voices rotates so the
# channel doesn't sound like one machine narrator. KOKORO_VOICE remains the
# deterministic override; set VOICE_ROTATE="auto" to enable the pool. Pool is
# "voice1:w1,voice2:w2,..." (weights normalised internally).
_VOICES_ENV = os.environ.get("KOKORO_VOICE_POOL", "am_fenrir:60,am_adam:15,am_michael:15,af_heart:10")
VOICES = [v.split(":")[0] for v in _VOICES_ENV.split(",") if v.split(":")[0]]
_WEIGHTS = [float(v.split(":")[1]) for v in _VOICES_ENV.split(",") if ":" in v]
if len(VOICES) != len(_WEIGHTS):
    _WEIGHTS = [1 / len(VOICES)] * len(VOICES) if VOICES else [1.0]
_total_w = sum(_WEIGHTS) or 1.0
_WEIGHTS = [w / _total_w for w in _WEIGHTS]
_VOICE_ROTATE = os.environ.get("VOICE_ROTATE", "off").strip().lower()


def _resolve_voice(topic: str = "", attempt: int = 0) -> str:
    """Deterministic-but-varied voice: brand voice usually, pool occasionally.

    The same topic always gets the same voice (idempotent across retries);
    different topics see variety. """
    if _VOICE_ROTATE != "auto" or not VOICES:
        return KOKORO_VOICE
    import hashlib as _h
    h = int(_h.sha256(f"{topic}".encode()).hexdigest(), 16)
    r = (h % 10_000) / 10_000.0
    acc = 0.0
    for v, w in zip(VOICES, _WEIGHTS):
        acc += w
        if r <= acc:
            return v
    return VOICES[0]
# V2.1: default matches config.settings / README USA-style 1.08x (V2 drifted
# to 0.98x here → narration sounded slow & low-energy unless env was set).
# Single source of truth: config.settings; env var KOKORO_SPEED overrides.
KOKORO_SPEED = float(os.environ.get("KOKORO_SPEED", str(_CFG_KOKORO_SPEED)))
KOKORO_MODEL_DIR = Path(os.environ.get("KOKORO_MODEL_DIR", "data/models/kokoro"))


def _download(url: str, dest: Path, min_bytes: int = 100_000) -> Path:
    if dest.exists() and dest.stat().st_size > min_bytes:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".part")
    logger.info("⬇️  Downloading %s → %s", url.split("/")[-1], dest)
    req = urllib.request.Request(url, headers={"User-Agent": "CoercionFilesV2/1.0"})
    with urllib.request.urlopen(req, timeout=600) as resp, open(tmp, "wb") as fh:
        shutil.copyfileobj(resp, fh)
    os.replace(tmp, dest)
    return dest


def _ensure_kokoro_files():
    """Download model+voices if missing; returns (model_path, voices_path)."""
    model = _download(MODEL_URL, KOKORO_MODEL_DIR / "kokoro-v1.0.onnx",
                      min_bytes=10_000_000)
    voices = _download(VOICES_URL, KOKORO_MODEL_DIR / "voices-v1.0.bin",
                       min_bytes=1_000_000)
    return str(model), str(voices)


# ── Kokoro (ONNX) ────────────────────────────────────────────
_kokoro_pipe = None


def _kokoro_onnx_tts(text: str, out_path: str) -> float:
    global _kokoro_pipe
    # bound onnxruntime memory on small runners (OMP threads)
    os.environ.setdefault("OMP_NUM_THREADS", "2")
    os.environ.setdefault("OMP_WAIT_POLICY", "PASSIVE")
    import soundfile as sf
    from kokoro_onnx import Kokoro

    if _kokoro_pipe is None:
        model, voices = _ensure_kokoro_files()
        _kokoro_pipe = Kokoro(model, voices)

    voice = _resolve_voice()
    if voice != KOKORO_VOICE:
        logger.info("🎙️  rotating narrator voice: %s → %s", KOKORO_VOICE, voice)
    samples, sr = _kokoro_pipe.create(text, voice=voice,
                                      speed=KOKORO_SPEED, lang="en-us")
    if len(samples) < sr:  # <1s = likely failed/empty
        raise RuntimeError("Kokoro produced <1s of audio")
    sf.write(out_path, samples, sr)
    return len(samples) / sr


# ── Kokoro (full torch pipeline, optional) ───────────────────
_kokoro_torch_pipe = None


def _kokoro_torch_tts(text: str, out_path: str) -> float:
    global _kokoro_torch_pipe
    import soundfile as sf
    from kokoro import KPipeline  # full package (heavier: torch+spacy)

    # V2.1: cache the pipeline. V2 rebuilt KPipeline on EVERY scene (reloading
    # the model + spacy each time) → minutes of wasted time per video.
    if _kokoro_torch_pipe is None:
        _kokoro_torch_pipe = KPipeline(lang_code="a")
    parts = []
    for _gs, _ps, audio in _kokoro_torch_pipe(text, voice=KOKORO_VOICE,
                                            speed=KOKORO_SPEED):
        parts.append(audio)
    import numpy as np
    full = np.concatenate(parts)
    sf.write(out_path, full, 24000)
    return len(full) / 24000


# ── Edge-TTS fallback ────────────────────────────────────────
def _edge_tts(text: str, out_path: str) -> float:
    import edge_tts
    mp3 = out_path + ".mp3"

    async def _gen():
        # V3.6.5: rate +4% — USA punchy pace, stable wps zone.
        # +8% par chhote words wale segments 3.26-3.57 wps ho kar
        # VoiceGuard (max 3.2) fail karte thay. +4% → ~2.3-2.8 wps
        # (zone 1.6-3.2 ke andar hamesha).
        c = edge_tts.Communicate(text, "en-US-GuyNeural", rate="+4%", pitch="-3Hz")
        await c.save(mp3)

    asyncio.run(_gen())
    subprocess.run(["ffmpeg", "-y", "-i", mp3, "-ar", "24000", "-ac", "1",
                    "-acodec", "pcm_s16le", out_path],
                   check=True, capture_output=True)
    os.remove(mp3)
    return _duration(out_path)


# ── ElevenLabs fallback ──────────────────────────────────────
def _elevenlabs(text: str, out_path: str) -> float:
    import json
    key = os.environ.get("ELEVENLABS_API_KEY", "")
    if not key:
        raise RuntimeError("no ELEVENLABS_API_KEY")
    voice_id = os.environ.get("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB")
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        data=json.dumps({"text": text, "model_id": "eleven_monolingual_v1",
                         "voice_settings": {"stability": 0.5,
                                            "similarity_boost": 0.75,
                                            "style": 0.3}}).encode(),
        headers={"xi-api-key": key, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = resp.read()
    if len(data) < 4000:
        raise RuntimeError("ElevenLabs returned tiny payload")
    mp3 = out_path + ".mp3"
    Path(mp3).write_bytes(data)
    subprocess.run(["ffmpeg", "-y", "-i", mp3, "-ar", "24000", "-ac", "1",
                    "-acodec", "pcm_s16le", out_path], check=True, capture_output=True)
    os.remove(mp3)
    return _duration(out_path)


def _duration(wav: str) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration", "-of", "default=nw=1:nk=1", wav],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


# ── Public API ───────────────────────────────────────────────
def release_tts() -> None:
    """Free the Kokoro model from RAM before heavy stages (video render)."""
    global _kokoro_pipe, _kokoro_torch_pipe
    _kokoro_pipe = None
    _kokoro_torch_pipe = None
    import gc
    gc.collect()
    logger.info("🧹 TTS resources released")


def generate_voice_segments(scenes: list, output_dir: str = "output/voice") -> list:
    """Generate one WAV per scene. Returns segments with path/duration/text."""
    os.makedirs(output_dir, exist_ok=True)
    primary = os.environ.get("TTS_PRIMARY", "kokoro")
    chain = {
        "kokoro": [_kokoro_torch_tts, _kokoro_onnx_tts, _edge_tts, _elevenlabs],
        "onnx": [_kokoro_onnx_tts, _edge_tts, _elevenlabs],
        "edge": [_edge_tts, _elevenlabs],
        "elevenlabs": [_elevenlabs, _edge_tts],
    }.get(primary, [_kokoro_onnx_tts, _edge_tts, _elevenlabs])

    segments = []
    for i, scene in enumerate(scenes):
        text = (scene.get("caption") or "").strip()
        if not text:
            segments.append({"path": None, "duration": 3.0, "text": ""})
            continue
        wav = os.path.join(output_dir, f"seg_{i:02d}.wav")
        done = False
        for fn in chain:
            try:
                d = fn(text, wav)
                segments.append({"path": wav, "duration": d, "text": text,
                                 "voice": getattr(fn, "__name__", "?")})
                logger.info("Voice seg %d: %.1fs via %s", i, d, fn.__name__)
                done = True
                break
            except Exception as exc:
                logger.warning("TTS %s failed: %s", fn.__name__, exc)
        if not done:
            logger.warning("All TTS failed for scene %d → silence", i)
            segments.append({"path": None, "duration": 4.5, "text": text})
    return segments


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test = [{"caption": "You've been lied to about how influence really works.",
             "visual": "dark"}, {"caption": "Follow Coercion Files for more.",
                                  "visual": "dark"}]
    segs = generate_voice_segments(test)
    for s in segs:
        print(s["duration"], s.get("voice"), s["text"][:40])
