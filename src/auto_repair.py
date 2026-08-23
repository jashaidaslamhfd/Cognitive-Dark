#!/usr/bin/env python3
"""
Coercion Files — Auto-Repair System.

The self-healing layer of the pipeline:

  • preflight()      — health checks BEFORE the run (python, ffmpeg, fonts,
                       disk space, importability of deps, presence of keys).
  • run_stage()      — every pipeline stage executes inside a retry wrapper
                       with exponential backoff; on repeated failure a
                       declared fallback chain is consulted.
  • RepairJournal    — persistent run journal (data/run_journal.json). On
                       startup detects a crashed previous run and repairs
                       stale state (cleans half-written outputs, resets locks).
  • cleanup()        — removes temp segments/images older than TTL while
                       keeping final deliverables.
  • selftest()       — fast offline smoke tests; exits non-zero on failure.
  • PlatformHealth   — wired to ML engine: quarantine platforms that fail.
"""

import contextlib
import json
import logging
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("auto_repair")


# ─────────────────────────────────────────────────────────────
def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_cmd(cmd: list, timeout: int = 120) -> tuple:
    """Run a shell command; return (ok, stdout)."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           check=False)
        return (r.returncode == 0, (r.stdout or r.stderr).strip())
    except Exception as exc:
        return False, str(exc)


def which(bin_name: str) -> bool:
    return shutil.which(bin_name) is not None


# ─────────────────────────────────────────────────────────────
class Preflight:
    """Collect system health facts; failures vs warnings."""

    CRITICAL = ["ffmpeg", "ffprobe", "python3"]
    WARNING = ["espeak-ng"]  # needed only for Kokoro OOD words

    def __init__(self):
        self.checks = {}

    def run(self, check_deps: bool = True, check_keys: bool = False,
            strict_deps: bool = False) -> dict:
        self.checks["system"] = {b: which(b) for b in self.CRITICAL}
        self.checks["warn"] = {b: which(b) for b in self.WARNING}

        if check_deps:
            self.checks["deps"] = self._importable([
                "moviepy", "PIL", "numpy", "requests", "soundfile", "dotenv",
            ])
            if strict_deps:
                missing_deps = [k for k, v in self.checks["deps"].items() if not v]
                if missing_deps:
                    raise SystemExit(
                        f"❌ Preflight FAILED — missing Python dependencies: {missing_deps}")

        # disk space on output dir
        try:
            st = shutil.disk_usage(Path("output").resolve())
            self.checks["disk_mb_free"] = round(st.free / 1048576)
        except Exception:
            self.checks["disk_mb_free"] = None

        if check_keys:
            self.checks["keys"] = {
                k: bool(os.environ.get(k)) for k in
                ("GROQ_API_KEY", "PEXELS_API_KEY", "PIXABAY_API_KEY",
                 "YOUTUBE_CREDENTIALS", "FB_ACCESS_TOKEN", "IG_ACCESS_TOKEN")
            }

        missing = [k for k, v in self.checks.get("system", {}).items() if not v]
        if missing:
            raise SystemExit(
                f"❌ Preflight FAILED — missing system binaries: {missing}. "
                f"Install: sudo apt-get install ffmpeg fonts-dejavu espeak-ng")
        return self.checks

    @staticmethod
    def _importable(modules: list) -> dict:
        import importlib
        out = {}
        for m in modules:
            try:
                importlib.import_module(m)
                out[m] = True
            except Exception:
                out[m] = False
        return out


# ─────────────────────────────────────────────────────────────
class RepairJournal:
    """Tracks run state across executions; repairs stale runs on boot."""

    def __init__(self, path: Path = None):
        self.path = Path(path or os.environ.get(
            "CD_JOURNAL_PATH", "data/run_journal.json"))
        self.data = self._read()

    def _read(self) -> dict:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

    def _write(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # V2.8: keep a snapshot so a CI-corrupted journal never erases history
        with contextlib.suppress(OSError):
            shutil.copy2(self.path, self.path.with_suffix(self.path.suffix + ".bak"))
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data, indent=2, ensure_ascii=False),
                       encoding="utf-8")
        os.replace(tmp, self.path)

    def start_run(self, run_id: str, kind: str) -> None:
        self.data["current"] = {"run_id": run_id, "kind": kind,
                                "started": now_iso(), "status": "running"}
        self.data.setdefault("history", []).append(self.data["current"])
        self._write()

    def repair_if_crashed(self) -> list:
        """If the previous run never finished, clean its leftovers."""
        cur = self.data.get("current") or {}
        repaired = []
        if cur.get("status") == "running":
            logger.warning("🔧 Previous run %s did not finish — repairing state",
                           cur.get("run_id"))
            # clean half-written segments/outputs
            for d in ("output/segments", "output/tmp", "data/tmp"):
                p = Path(d)
                if p.exists():
                    for f in p.iterdir():
                        if f.is_file():
                            f.unlink(missing_ok=True)
                    repaired.append(d)
            self.data["current"]["status"] = "repaired"
            self._write()
        return repaired

    def finish_run(self, run_id: str, status: str, note: str = "") -> None:
        cur = self.data.get("current") or {}
        if cur.get("run_id") == run_id:
            cur["status"] = status
            cur["finished"] = now_iso()
            cur["note"] = note
            if len(self.data["history"]) > 50:
                self.data["history"] = self.data["history"][-50:]
            self._write()

    def last_run(self) -> dict:
        cur = self.data.get("current") or {}
        return cur


# ─────────────────────────────────────────────────────────────
class StageRunner:
    """Retry-with-backoff wrapper around any pipeline stage."""

    def __init__(self, max_retries: int = 3, base_backoff: float = 4.0):
        self.max_retries = max_retries
        self.base_backoff = base_backoff

    def run(self, fn, name: str, fallbacks: list = None, *args, **kwargs):
        """Run `fn`; on failure try each fallback; finally raise/report."""
        chain = [fn, *list(fallbacks or [])]
        last_exc = None
        for attempt, call in enumerate(chain):
            for retry in range(self.max_retries if attempt == 0 else 1):
                try:
                    result = call(*args, **kwargs)
                    if result is not None:
                        return result
                except Exception as exc:
                    last_exc = exc
                    logger.warning("⚠️ %s attempt %d/%d failed: %s",
                                   name, retry + 1, self.max_retries, exc)
                    if retry < self.max_retries - 1:
                        time.sleep(self.base_backoff * (2 ** retry))
        raise RuntimeError(f"Stage '{name}' failed after all retries/fallbacks: {last_exc}")


# ─────────────────────────────────────────────────────────────
def cleanup(keep_dirs: list = None, older_than_hours: float = 48.0,
            keep_latest_videos: int = 20) -> None:
    """Remove stale temp files; keep recent final videos."""
    keep_dirs = keep_dirs or ["output"]
    now = time.time()
    removed = 0
    for base in keep_dirs:
        p = Path(base)
        if not p.exists():
            continue
        for f in p.rglob("*"):
            if not f.is_file():
                continue
            if "final" in f.name or "thumbnail" in f.name:
                continue  # keep deliverables
            age_h = (now - f.stat().st_mtime) / 3600
            if age_h > older_than_hours:
                try:
                    f.unlink(missing_ok=True)
                    removed += 1
                except OSError:
                    pass
    # keep only the N most recent final videos
    finals = sorted(Path("output").glob("final_*.mp4"),
                    key=lambda p: p.stat().st_mtime, reverse=True)
    for old in finals[keep_latest_videos:]:
        old.unlink(missing_ok=True)
    if removed:
        logger.info("🧹 Cleanup removed %d stale temp files", removed)


# ─────────────────────────────────────────────────────────────
def selftest() -> bool:
    """Fast offline smoke test of the whole stack."""
    ok = True
    tests = []

    def t(name, fn):
        nonlocal ok
        try:
            fn()
            tests.append((name, "PASS"))
            print(f"  ✅ {name}")
        except Exception as exc:
            ok = False
            tests.append((name, f"FAIL: {exc}"))
            print(f"  ❌ {name}: {exc}")

    print("🧪 Auto-Repair Selftest:")

    def _script():
        import sys as _s
        _s.path.insert(0, "src")
        from script_generator import generate_script
        s = generate_script()
        assert s.get("scenes") and len(s["scenes"]) >= 3, "no scenes"

    def _scheduler():
        from scheduler import PlatformScheduler
        for p in ("youtube", "facebook", "instagram"):
            n = PlatformScheduler(p).next_peak()
            assert n.tzinfo is not None, "naive datetime"

    def _ml():
        from ml_engine import LearningSystem
        ls = LearningSystem(store_path=Path("/tmp/selftest_ml.json"))
        s = ls.choose_strategy()
        ls.record_outcome(s["arm_key"], 2.0)
        g = ls.dedup_guard("hello world test")
        assert g["allowed"] is True
        ls.apply_penalty(s["arm_key"], "selftest")
        ls.save()

    def _seo():
        from seo import build_platform_package
        p = build_platform_package({"title": "Test", "hook": "Hook here",
                                    "key_points": "x", "tags": ["a"]}, "youtube")
        assert len(p["title"]) <= 100

    def _video():
        from video_builder import build_short
        from visuals import generate_procedural_scene
        # build with procedural visuals only (no API keys needed)
        scenes = [{"caption": "Test one two three.",
                   "caption_roman": "Test one two three.",
                   "emotion": "dark"} for _ in range(2)]
        scene_visuals = [[generate_procedural_scene(i * 10 + k, "dark",
                           out_dir="output/tmp/selftest") for k in range(3)]
                         for i in range(2)]
        segs = [{"path": None, "duration": 2.5, "text": s["caption"]} for s in scenes]
        out = build_short(scene_visuals, segs, scenes,
                          out_path="output/tmp/selftest_video.mp4")
        assert Path(out).exists() and Path(out).stat().st_size > 10000

    def _gate():
        # Independent Release Gate: chalta hai + HONEST report deta hai
        # (selftest payload mein audio missing hai → voice guard ko FAIL
        # karna chahiye — fail-closed, jhoot nahi)
        from guards.gate import ReleaseGate
        g = ReleaseGate(mode="strict")
        payload = {
            "platform": "youtube",
            "script": {"hook": "Why smart people join cults",
                       "title": "Why Smart People Join Cults",
                       "arm_key": "cults::question_hook::morning",
                       "scenes": [
                           {"caption": "Why smart people join cults."},
                           {"caption": "The $400k wire transfer happened in 3 days."},
                           {"caption": "Milgram proved obedience is social."},
                           {"caption": "Cialdini's scarcity explains the rush."},
                           {"caption": "Hit like if this helped you spot it."}]},
            "segments": [{"path": None, "duration": 2.5, "text": "x"}],
            "video_path": "output/tmp/selftest_video.mp4",
            "thumb_path": None,
            "package": {"title": "Why Smart People Join Cults",
                        "description": "psychology — how cults recruit. "
                        "Educational, protect yourself. #psychology",
                        "tags": ["psychology"], "hashtags": ["psychology"],
                        "hook": "Why smart people join cults"},
            "publish_at": None,
            "ml": None,
        }
        rep = g.evaluate(payload)
        assert rep.verdicts and len(rep.verdicts) >= 8, "gate ne sab guards nahi chalaye"
        # audio missing → voice FAIL (honest, fail-closed) → released False
        assert rep.released is False, "gate ne missing-audio video ko release kar diya"
        assert any(v.guard == "voice" and v.blocking for v in rep.verdicts)

    t("script generator (template fallback)", _script)
    t("scheduler (DST-aware, per-platform)", _scheduler)
    t("ml engine (UCB + reward/penalty + dedup)", _ml)
    t("seo packaging", _seo)
    t("video builder (procedural, offline)", _video)
    t("release gate (independent guards, fail-closed)", _gate)
    return ok


# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ok = selftest()
    sys.exit(0 if ok else 1)
