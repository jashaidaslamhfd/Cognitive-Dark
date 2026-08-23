#!/usr/bin/env python3
"""
Coercion Files — Stock Clip Downloader.

Sources (free, royalty-free, monetization-safe):
  • Pexels  — api.pexels.com/videos/search   (Authorization header)
  • Pixabay — pixabay.com/api/videos/        (key query param)

Each scene's `visual` field is a short search query. We fetch a pool of
clips per scene, pick the best (portrait > landscape, resolution, size),
download & cache them, and return paths. If both providers fail or no key
is configured, the pipeline falls back to procedural visuals (visuals.py).
"""

import logging
import os
import time
from pathlib import Path

import requests

from config.settings import (
    CLIP_CACHE,
    CLIP_CACHE_TTL_DAYS,
    CLIP_PROVIDER_ORDER,
    MIN_CLIP_BYTES,
)
from visuals import generate_procedural_scene  # fallback

logger = logging.getLogger("clips_downloader")

PEXELS_KEY = os.environ.get("PEXELS_API_KEY", "")
PIXABAY_KEY = os.environ.get("PIXABAY_API_KEY", "")

UA = {"User-Agent": "CoercionFilesV2/1.0 (+https://github.com/CoercionFiles)"}


# ── Pexels ───────────────────────────────────────────────────
def _pexels_search(query: str, per_page: int = 12) -> list:
    """Return list of candidate clips [{url, width, height, quality, provider}]."""
    if not PEXELS_KEY:
        return []
    resp = requests.get(
        "https://api.pexels.com/videos/search",
        params={"query": query, "per_page": per_page, "orientation": "portrait"},
        headers={"Authorization": PEXELS_KEY, **UA}, timeout=30)
    resp.raise_for_status()
    out = []
    for v in resp.json().get("videos", []):
        for f in v.get("video_files", []):
            if not f.get("link"):
                continue
            out.append({
                "url": f["link"],
                "width": f.get("width", 0), "height": f.get("height", 0),
                "quality": f.get("quality", ""),
                "provider": "pexels", "id": v.get("id"),
                "duration": v.get("duration", 0),
            })
    return out


# ── Pixabay ──────────────────────────────────────────────────
def _pixabay_search(query: str, per_page: int = 12) -> list:
    if not PIXABAY_KEY:
        return []
    resp = requests.get(
        "https://pixabay.com/api/videos/",
        params={"key": PIXABAY_KEY, "q": query, "per_page": per_page,
                "video_type": "film", "min_width": 640, "min_height": 360},
        headers=UA, timeout=30)
    resp.raise_for_status()
    out = []
    for h in resp.json().get("hits", []):
        for size_key in ("medium", "large", "small"):
            f = h.get("videos", {}).get(size_key)
            if not f or not f.get("url"):
                continue
            out.append({
                "url": f["url"],
                "width": f.get("width", 0), "height": f.get("height", 0),
                "quality": size_key,
                "provider": "pixabay", "id": h.get("id"),
                "duration": h.get("duration", 0),
            })
    return out


# ── selection & download ─────────────────────────────────────
def _score(clip: dict) -> float:
    """Prefer portrait 1080p+ (reels-native), penalize tiny/low files."""
    w, h = clip["width"], clip["height"]
    s = 0.0
    if h >= 1920 and 0 < w <= 1080:
        s += 4.0                      # perfect portrait HD
    elif h >= 1080:
        s += 2.0
    elif h >= 720:
        s += 1.0
    s += min(1.0, (h * w) / (1920 * 1080))
    if clip["quality"] in ("hd", "uhd", "large"):
        s += 0.5
    return s


def _probe_valid(path: Path) -> bool:
    """ffprobe gate (2026-08-17): corrupted stock MP4s crash the MoviePy render
    later (same root cause Neuro-Somaa hit). Verify duration/streams NOW and
    reject a broken file so the ranked fallback loop tries the next clip."""
    try:
        import subprocess as _sp
        res = _sp.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, timeout=20,
        )
        if res.returncode != 0:
            return False
        dur = float(res.stdout.strip())
        return dur > 0.5
    except Exception:
        return False


def _download(url: str, dest: Path) -> Path:
    if dest.exists() and dest.stat().st_size > MIN_CLIP_BYTES:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".part")
    with requests.get(url, headers=UA, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(tmp, "wb") as fh:
            fh.writelines(r.iter_content(chunk_size=1 << 16))
    size = tmp.stat().st_size          # V2.1: read size BEFORE unlink
    if size < MIN_CLIP_BYTES:           # (V2 stat()'d after unlink → FileNotFoundError)
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"clip too small: {size} bytes")
    os.replace(tmp, dest)
    # 2026-08-17: ffprobe validation gate — Pexels/Pixabay occasionally serve
    # truncated/corrupt MP4s that pass the size check but crash the render.
    if not _probe_valid(dest):
        dest.unlink(missing_ok=True)
        raise RuntimeError(f"clip failed ffprobe validation: {dest}")
    return dest


def _evict_old_cache() -> None:
    """Drop cached clips older than CLIP_CACHE_TTL_DAYS (V2 never evicted)."""
    if not CLIP_CACHE.exists():
        return
    cutoff = time.time() - CLIP_CACHE_TTL_DAYS * 86400
    try:
        for f in CLIP_CACHE.iterdir():
            if f.is_file() and f.stat().st_mtime < cutoff:
                f.unlink(missing_ok=True)
    except OSError:
        pass


def get_clip_for_scene(scene_idx: int, scene: dict, rank: int = 0,
                       cache_dir: Path = None) -> dict:
    """Fetch the `rank`-th best clip for a scene (rank 0 = best).

    V2.1: the `rank` offset is what gives every scene DISTINCT cuts. V2 always
    returned the single top clip, so per-scene variety was impossible and
    prepare_clips silently degraded to 1 clip + procedural stills.
    Returns {'path': str, 'source': str, ...} or raises if all providers fail.
    """
    query = (scene.get("visual") or "dark city night").strip()[:80]
    candidates = []
    for provider in CLIP_PROVIDER_ORDER:
        try:
            if provider == "pexels":
                candidates += _pexels_search(query)
            elif provider == "pixabay":
                candidates += _pixabay_search(query)
        except Exception as exc:
            logger.warning("Provider %s search failed: %s", provider, exc)
    if not candidates:
        raise RuntimeError("no clips found for query: " + query)

    candidates.sort(key=_score, reverse=True)
    # Deduplicate by file identity, keep ranked order
    seen, ordered = set(), []
    for clip in candidates:
        url = clip["url"]
        ext = Path(url.split("?")[0]).suffix or ".mp4"
        key = f"{clip['provider']}_{clip['id']}_{clip['width']}x{clip['height']}{ext}"
        if key in seen:
            continue
        seen.add(key)
        clip["_cache_key"] = key
        ordered.append(clip)
    if not ordered:
        raise RuntimeError("no unique clips for query: " + query)

    # Walk from the requested rank downward until one downloads cleanly
    cache_root = Path(cache_dir or CLIP_CACHE)
    for idx in range(rank, rank + len(ordered)):
        clip = ordered[idx % len(ordered)]
        dest = cache_root / clip["_cache_key"]
        try:
            path = _download(clip["url"], dest)
            return {"path": str(path), "source": clip["provider"],
                    "source_id": clip.get("id"), "source_url": clip.get("url"),
                    "width": clip["width"], "height": clip["height"],
                    "query": query}
        except Exception as exc:
            logger.warning("clip download failed (%s): %s", clip["url"][:70], exc)
            time.sleep(0.5)
    raise RuntimeError(f"could not download any clip for: {query}")


def prepare_clips(scenes: list, per_scene: int = 3,
                  cache_dir: Path = None) -> list:
    """Fetch `per_scene` distinct clips for every scene (for fast cuts).

    Returns a list (one entry per scene) of lists of clip dicts.
    Falls back to distinct procedural visuals per scene when providers fail.
    """
    if cache_dir is None:
        _evict_old_cache()
    else:
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
    results = []
    for i, scene in enumerate(scenes):
        scene_clips = []
        seen_ids = set()
        # V2.1: request DISTINCT cuts via rank offset (rank k → k-th best clip)
        for rank in range(per_scene):
            try:
                r = get_clip_for_scene(i, scene, rank=rank, cache_dir=cache_dir)
                key = (r.get("source"), r.get("width"), r.get("height"), r.get("path"))
                if key not in seen_ids:
                    scene_clips.append(r)
                    seen_ids.add(key)
            except Exception as exc:
                logger.warning("clip fetch %d (rank %d) failed → procedural (%s)",
                               i, rank, exc)
                break
        # top up with procedural visuals so every scene has per_scene cuts
        while len(scene_clips) < per_scene:
            scene_clips.append({
                "path": generate_procedural_scene(
                    i * 10 + len(scene_clips), scene.get("emotion", "dark")),
                "source": "procedural",
                "source_id": None,
                "source_url": None,
                "query": scene.get("visual", ""),
            })
        results.append(scene_clips)
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_scenes = [
        {"visual": "dark city rain", "emotion": "dark"},
        {"visual": "storm clouds", "emotion": "intense"},
    ]
    for r in prepare_clips(test_scenes):
        print(r["source"], r["path"])
