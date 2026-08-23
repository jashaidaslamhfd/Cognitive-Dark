#!/usr/bin/env python3
"""
Coercion Files — Multi-Platform Pipeline Orchestrator.

  Script(Groq) → Clips(Pexels/Pixabay) → Voice(Kokoro) → Video(MoviePy)
  → Upload(YouTube + Facebook + Instagram) → ML feedback → Monetization tracker

Every stage runs inside the auto-repair StageRunner (retries + fallbacks).
The ML engine picks the content strategy and is updated with outcomes —
V2.1: rewards/penalties land on the EXACT arm that produced the video,
daily caps + min-gap guards protect platform health, and every published
video_id is attributed back to its formula so real analytics train the bandit.
"""

import argparse
import logging
import os
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("main")

from auto_repair import Preflight, RepairJournal, StageRunner, cleanup, selftest
from clips_downloader import prepare_clips
from config.settings import MIN_POST_GAP_HOURS, OUTPUT_DIR, PLATFORMS
from ml_engine import LearningSystem, text_sha
from monetization_tracker import update_progress
from scheduler import PlatformScheduler
from script_generator import generate_script
from seo import build_platform_package
from tts_engine import generate_voice_segments, release_tts
from video_builder import build_short, generate_thumbnail


def _platform_uploaders(dry_run: bool) -> dict:
    from platforms.facebook import FacebookUploader
    from platforms.instagram import InstagramUploader
    from platforms.youtube import YouTubeUploader
    return {
        "youtube": YouTubeUploader(dry_run=dry_run),
        "facebook": FacebookUploader(dry_run=dry_run),
        "instagram": InstagramUploader(dry_run=dry_run),
    }


def run_pipeline(platforms: list = None, dry_run: bool = False,
                 pillar: str = None, topic: str = None) -> dict:
    start = time.time()
    platforms = platforms or [p for p, c in PLATFORMS.items() if c["enabled"]]
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%f")
    run_root = OUTPUT_DIR / ("dry_runs" if dry_run else "runs") / run_id
    artifact_dir = run_root / "artifacts"
    temp_dir = run_root / "tmp"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    temp_dir.mkdir(parents=True, exist_ok=True)

    # Dry-runs use a disposable journal and in-memory ML state. They must not
    # repair, clean, or rewrite production data files.
    journal = RepairJournal(path=run_root / "run_journal.json" if dry_run else None)
    if not dry_run:
        journal.repair_if_crashed()
        cleanup(keep_dirs=[str(OUTPUT_DIR)], older_than_hours=24)
    journal.start_run(run_id, "short_pipeline")

    # ── preflight ──
    Preflight().run(check_deps=True, strict_deps=True)
    logger.info("🚀 COGNITIVE DARK V2.1 — platforms=%s dry_run=%s",
                ",".join(platforms), dry_run)

    # ── ML engine ──
    ml = LearningSystem(persist=not dry_run)

    # Warm-start the bandit with market intelligence once (idempotent: real
    # per-video evidence is never overwritten). Falls back to curated patterns.
    try:
        from market_intel import analyze, priors_for_bandit
        _analysis = analyze()
        _priors = priors_for_bandit(_analysis)
        existing = sum(1 for a in ml.data["arms"].values() if a.get("n", 0) > 0)
        if existing < len(_priors) * 3:
            ml.apply_seed_priors(priors=_priors, source=_analysis["source"])
            if _analysis.get("curated"):
                logger.warning("🌡 Market intel: %d patterns from %s — CURATED "
                               "believe hain, evidence nahi. Real competitor "
                               "data (YOUTUBE_API_KEY) aane par ye override "
                               "honge.", len(_priors), _analysis["source"])
            else:
                logger.info("🌡 Market intel: %d patterns from %s",
                            len(_priors), _analysis["source"])
    except Exception as exc:
        logger.warning("Market intel warm-start skipped: %s", exc)

    # ── V2.9 VIRAL INTEL: learn from viral channels (live sync, once/week) ──
    try:
        from market_intel import sync_competitor_data
        last_sync = ml.data.get("competitor_sync_ts", "")
        if not dry_run and not last_sync:
            res = sync_competitor_data()
            if res.get("fetched"):
                ml.data["competitor_sync_ts"] = datetime.now(timezone.utc).isoformat()
                ml.save()
                logger.info("📡 Viral competitor sync: %d new videos learned",
                            res["fetched"])
    except Exception as exc:
        logger.warning("Competitor sync skipped: %s", exc)

    # ── V2.9 playbook + viral intel snapshot for the run ──
    try:
        from viral_intel import virality_index
        _v = virality_index(ml.data)
        logger.info("🎯 Virality index: %s (%s) — top patterns: %s",
                    _v["grade"], _v["index"], _v["top_title_formulas"])
    except Exception as exc:
        logger.warning("Virality index skipped: %s", exc)

    # Strategy director — auto-tune only on live runs; preview must be inert.
    try:
        if not dry_run:
            from strategy_director import StrategyDirector
            director = StrategyDirector(ml=ml)
            director.decide()
            director.apply_to_env()
            env_eps = os.environ.get("CD_EPSILON")
            if env_eps:
                ml.cfg["epsilon"] = float(env_eps)
        else:
            director = None
    except Exception as exc:
        logger.warning("Strategy director skipped: %s", exc)
        director = None

    # ── BRAIN ADAPTATION (War Mode) ──
    if os.environ.get("WAR_MODE", "false").lower() == "true" and not pillar and not topic:
        try:
            from autonomous_brain import get_brain
            brain = get_brain()
            decision = brain.decide_next_video()
            pillar = decision["pillar"]
            topic = decision["topic"]
            logger.info("🧠 Autonomous Brain decided: %s (%s)", topic, pillar)
        except Exception as e:
            logger.warning("Brain decision failed: %s", e)

    # ── TREND-SPIKER: live public-feed spike override (opt-in) ──
    if not pillar and not topic:
        try:
            from trend_spiker import get_trend_spike
            _recent = [str(t.get("title", "") or "") for t in
                       (ml.data.get("videos") or [])[-8:]]
            _spike = get_trend_spike(exclude=_recent)
            if _spike:
                topic = _spike["topic"]
                pillar = None  # bandit picks the arm for the spike topic
                logger.info("📈 TREND-SPIKER OVERRIDE: topic=%s (%s)",
                            topic, ", ".join(_spike.get("sources", [])))
        except Exception as e:
            logger.warning("Trend-Spiker skipped: %s", e)

    # ── 1-4. BUILD + 🛂 INDEPENDENT RELEASE GATE (V3.5) ─────────────
    # Har department ka apna independent guard (script, hook, voice,
    # caption, video, seo, ctr, views) + USASupervisor aakhri judge.
    # Video tabhi upload hoti hai jab SAB guards pass karein — warna
    # repair loop naya script banata hai (GATE_MAX_REPAIRS tak), phir
    # video HELD rehti hai aur upload nahi hota.
    from guards.gate import ReleaseGate
    gate = ReleaseGate(report_dir=artifact_dir / "gate_reports")
    max_repairs = int(os.environ.get("GATE_MAX_REPAIRS", "2"))
    gate_verdicts: dict = {}
    publish_times: dict = {}
    packs: dict = {}
    final_video = ""
    thumb = ""
    for _attempt in range(max_repairs + 1):
        # ── 1. Script (ML-chosen strategy) ──
        runner = StageRunner(max_retries=2)
        script = runner.run(generate_script, "script", [], pillar_key=pillar,
                            topic=topic, ml=ml)
        logger.info("📝 %s [%s/%s] (%s)", script["title"], script["pillar"],
                    script["hook_style"], script["source"])
        arm = script.get("arm_key")  # V2.1: the EXACT arm travels with the script

        # ── dedup & variation guard (retry w/ new strategy) ──
        guard = ml.dedup_guard(" ".join(s["caption"] for s in script["scenes"]),
                               script.get("hook", ""))
        retries = 0
        while not guard["allowed"] and retries < 4:
            logger.warning("⛔ Too-similar content (%s) → retrying with fresh strategy (%d)",
                           guard["reason"], retries + 1)
            if arm:
                ml.apply_penalty(arm, "dedup_blocked", 0.3)
            script = generate_script(ml=ml, topic=topic)
            arm = script.get("arm_key")
            guard = ml.dedup_guard(" ".join(s["caption"] for s in script["scenes"]),
                                   script.get("hook", ""))
            retries += 1
        if not guard["allowed"]:
            logger.error("⛔ Could not produce unique content after 4 attempts")
            journal.finish_run(run_id, "blocked", guard["reason"])
            return {"success": False, "reason": guard["reason"]}

        # ── 2. Clips (Pexels → Pixabay → procedural) — 3 DISTINCT cuts per scene ──
        clip_sets = prepare_clips(
            script["scenes"], per_scene=3, cache_dir=temp_dir / "clips")
        scene_visuals = [[c["path"] for c in s] for s in clip_sets]
        asset_ledger = {
            "run_id": run_id,
            "scenes": [
                {
                    "scene": i,
                    "query": script["scenes"][i].get("visual", ""),
                    "assets": [
                        {k: clip.get(k) for k in
                         ("source", "source_id", "source_url", "width", "height", "query")}
                        for clip in scene_clips
                    ],
                }
                for i, scene_clips in enumerate(clip_sets)
            ],
        }
        try:
            import json as _json
            (artifact_dir / "asset_provenance.json").write_text(
                _json.dumps(asset_ledger, ensure_ascii=False, indent=2),
                encoding="utf-8")
        except OSError as exc:
            logger.warning("asset provenance write failed: %s", exc)
        logger.info("🎞️  Clips: %s (%d scenes x %d cuts)",
                    ", ".join(sorted({c["source"] for s in clip_sets for c in s})),
                    len(scene_visuals), len(scene_visuals[0]) if scene_visuals else 0)

        # ── 3. Voice (Kokoro → edge → elevenlabs → silence) ──
        segments = generate_voice_segments(script["scenes"])
        narration_s = sum(s["duration"] for s in segments)
        logger.info("🎙️  Narration: %.1fs", narration_s)

        # V2.5 SHORTS CAP GUARD: >60s = NOT a Short on YouTube; IG/FB Reels also
        # favor <60s. Trim scenes (clips+audio together) to stay 40-58s.
        # V3.6.2: CTA scene (last) kabhi NAHI kat ta — engagement ask hi retention
        # aur likes ka engine hai. Us ki jagah second-last (detail) scene trim
        # hota hai jab tak fit na ho jaye.
        _cta_words = ("like", "comment", "follow", "save", "share", "subscribe", "hit")
        while narration_s > 57 and len(script["scenes"]) > 4:
            last = script["scenes"][-1].get("caption", "").lower()
            has_cta = any(w in last for w in _cta_words)
            idx = len(script["scenes"]) - 2 if has_cta else len(script["scenes"]) - 1
            script["scenes"].pop(idx)
            narration_s -= segments.pop(idx)["duration"]
            scene_visuals.pop(idx)
        # emergency: ab bhi lamba ho to aakhri sahara (CTA ke saath)
        while narration_s > 57 and len(script["scenes"]) > 3:
            script["scenes"].pop()
            narration_s -= segments.pop()["duration"]
            scene_visuals.pop()
        logger.info("✂️  Final scenes: %d (%.1fs narration — Shorts-safe)",
                    len(script["scenes"]), narration_s)
        release_tts()  # free the ~300MB Kokoro model before video render

        # ── 4. Video (USA style: fast cuts + word captions + hook overlay) ──
        final_video = build_short(
            scene_visuals, segments, script["scenes"],
            out_path=str(artifact_dir / "final_video.mp4"),
            hook=script.get("hook", ""), temp_dir=str(temp_dir))
        thumb = generate_thumbnail(scene_visuals[0][0], script.get("hook", ""),
                                   out_dir=str(artifact_dir))
        logger.info("🎬 Built %s + thumbnail", final_video)

        # ── 4b. 🛂 RELEASE GATE: har department ka independent guard ──
        # Guards producer ke self-scores nahi dekhte — sirf raw artifacts
        # (files, text, packages) + real ML outcomes. Supervisor fail-closed.
        core_blocked = False
        for p in platforms:
            if not PLATFORMS.get(p, {}).get("enabled"):
                continue
            pkg = build_platform_package(script, p,
                                         durations=[s["duration"] for s in segments])
            packs[p] = pkg
            sched = PlatformScheduler(p)
            publish_at = sched.next_peak(reserved=ml.claimed_peaks(p))
            try:
                from human_layer import jitter_publish_at
                publish_at = jitter_publish_at(publish_at)
            except Exception:
                pass
            publish_times[p] = publish_at
            verdict = gate.evaluate({
                "platform": p,
                "script": script,
                "segments": segments,
                "video_path": final_video,
                "thumb_path": thumb,
                "package": pkg,
                "publish_at": publish_at,
                "sibling_packages": {op: packs[op] for op in packs if op != p},
                "ml": ml,
            })
            gate_verdicts[p] = verdict
            if not verdict.released and verdict.core_blocked():
                core_blocked = True
        if not core_blocked or _attempt >= max_repairs:
            break
        logger.warning("🔁 GATE repair %d/%d — core guard fail, naya script: %s",
                       _attempt + 1, max_repairs,
                       "; ".join(r for v in gate_verdicts.values()
                                 for r in v.blocking_reasons())[:220])

    # gate payload save (scripts/run_gate.py + audit ke liye)
    try:
        gate.save_payload(
            {p: {"platform": p, "script": script, "segments": segments,
                 "video_path": final_video, "thumb_path": thumb,
                 "package": packs.get(p), "publish_at": publish_times.get(p)}
             for p in gate_verdicts},
            out_dir=artifact_dir)
    except Exception as exc:
        logger.warning("gate payload save failed: %s", exc)

    # ── 5. Upload per platform (algorithm-adapted, volume-guarded) ──
    uploaders = _platform_uploaders(dry_run)
    results = {}
    caption_text = " ".join(s["caption"] for s in script["scenes"])
    ml.register_video({
        "title": script["title"], "hook": script.get("hook", ""),
        "pillar": script["pillar"], "hook_style": script["hook_style"],
        "arm_key": arm,
        "text_sha": text_sha(caption_text),
        "text": caption_text,
        "source": script["source"], "claim_mode": script.get("claim_mode"),
        "sources": script.get("sources", []), "run_id": run_id,
    })

    for p in platforms:
        cfg = PLATFORMS.get(p)
        if not cfg or not cfg.get("enabled"):
            logger.info("⏭️  %s disabled in config", p)
            continue
        # 🛂 GATE verdict: guards/supervisor ne HELD kiya → upload nahi
        verdict = gate_verdicts.get(p)
        if verdict and not verdict.released:
            logger.error("🛂 %s GATE HELD (grade %s) — upload nahi hua: %s",
                         p.upper(), verdict.grade,
                         "; ".join(verdict.blocking_reasons())[:220])
            results[p] = {"platform": p, "ok": False, "gate_blocked": True,
                          "grade": verdict.grade,
                          "reasons": verdict.blocking_reasons()}
            continue
        if not ml.platform_healthy(p):
            logger.warning("⛔ %s quarantined (3+ failures) — skipping", p)
            continue
        # V2.1: daily cap + min-gap guards (consistency beats bursts)
        allowed, why = ml.can_post(p, cfg.get("max_daily", 3), MIN_POST_GAP_HOURS)
        if not allowed and not dry_run:
            logger.info("⏭️  %s skipped: %s", p, why)
            results[p] = {"platform": p, "ok": False, "skipped": True, "reason": why}
            continue

        pkg = packs.get(p) or build_platform_package(
            script, p, durations=[s["duration"] for s in segments])
        # V2.9: 2026-algorithm playbook audit per platform (log only — helps
        # spot weak packages before upload)
        try:
            from algorithm_playbook import audit_package
            _audit = audit_package(pkg, p)
            if _audit.get("passed", 0) < _audit.get("verifiable", _audit.get("total", 1)):
                logger.info("🎛 %s playbook: %d/%d — %s", p.upper(),
                            _audit["passed"], _audit.get("verifiable", _audit.get("total", 1)),
                            "; ".join(c["signal"] for c in _audit["checks"]
                                      if c.get("status") == "fail"))
        except Exception:
            pass
        packs[p] = pkg
        # V2.7: CLAIM the publish slot BEFORE uploading. If another run (e.g.
        # cron + manual dispatch in the same window) already claimed this
        # peak, next_peak() is asked for the next free one. This closes the
        # "two videos go public at the same minute" double-post bug.
        claimed = False
        # publish_at pehle hi compute + jitter ho chuka hai (gate step) —
        # supervisor ne isi window ko USA-audience ke liye validate kiya hai
        sched = PlatformScheduler(p)
        publish_at = publish_times.get(p) or sched.next_peak(
            reserved=ml.claimed_peaks(p))
        if not dry_run:
            for _ in range(6):
                ok_claim, why = ml.claim_publish(p, publish_at, run_id)
                if ok_claim:
                    claimed = True
                    break
                logger.warning("⛔ %s: %s → trying next free peak", p, why)
                publish_at = sched.next_peak(
                    reserved=[*ml.claimed_peaks(p), publish_at])
        try:
            res = uploaders[p].upload(final_video, thumb, pkg,
                                      publish_at=publish_at.isoformat())
            results[p] = res
            if res.get("ok"):
                ml.report_success(p)
                if not res.get("dry_run"):
                    ml.record_post(p)
                    # V2.1: attribute the published id back to the formula
                    vid = res.get("video_id") or res.get("post_id") or res.get("media_id")
                    if vid and arm:
                        ml.record_video_id(p, vid, arm, script["title"])
            elif res.get("skipped"):
                # not a real mistake — just missing config; don't penalize the ML
                logger.info("ℹ️  %s: skipped (config) — no ML penalty", p.upper())
            else:
                if claimed:
                    ml.release_claim(p, publish_at)  # failed — free the slot
                ml.report_failure(p, res.get("error") or res.get("reason", "unknown"))
                if arm:
                    ml.apply_penalty(arm, f"{p}_upload_failed",
                                     ml.cfg["penalty_failure"], platform=p)
        except Exception as exc:
            if claimed:
                ml.release_claim(p, publish_at)
            logger.error("Platform %s raised: %s", p, exc)
            ml.report_failure(p, str(exc))
            if arm:
                ml.apply_penalty(arm, f"{p}_raised",
                                 ml.cfg["penalty_failure"], platform=p)
            results[p] = uploaders[p].result(False, error=str(exc))

    # ── 5b. Content pack for manual posting (CI artifact) ──
    # V2.6: while the IG API link propagates, the runner exposes video +
    # thumbnail + per-platform captions as a downloadable artifact so the
    # owner can post manually in ~1 minute.
    try:
        import json as _json
        with open(artifact_dir / "seo_packages.json", "w",
                  encoding="utf-8") as fh:
            _json.dump({"title": script["title"], "hook": script.get("hook", ""),
                        "packages": packs}, fh, ensure_ascii=False, indent=2)
    except Exception as exc:
        logger.warning("content pack write failed: %s", exc)

    # ── 6. ML feedback — ONLY from real performance ────────────────
    # V3.4: publish hone par reward dena BAND (bonus_consistent = 0). Pehle
    # har upload ko +1.0 milta tha + self-scored quality bonus — bandit ko
    # "sab kuch viral hai" ka jhoota signal milta tha aur weak formulas
    # repeat hote rehte thay jabke views 0 thay. Ab arm ka reward SIRF
    # scripts/fetch_metrics.py se aata hai (real views/likes/retention),
    # jo attribution map ke zariye EXACT arm tak pahunchta hai.
    _script_quality = script.get("script_quality", {}).get("score", 0.0) \
        if isinstance(script.get("script_quality"), dict) else 0.0
    for p, res in results.items():
        if res.get("ok") and not res.get("dry_run") and arm:
            bonus = float(ml.cfg.get("bonus_consistent", 0.0) or 0.0)
            if bonus > 0:
                ml.apply_reward(arm, f"{p}_published", bonus, platform=p,
                                content_quality=_script_quality)
            else:
                logger.info("📊 %s upload OK — NO reward yet. Real metrics "
                            "(views/retention) will decide this arm's fate.", p.upper())
    ml.save()

    # ── 7. Monetization progress snapshot (live runs only) ──
    if not dry_run:
        update_progress()

    # ── V3.0: daily brief (human creator's morning notes) ──
    try:
        from human_layer import write_daily_brief
        _j = journal.data
        _m = {}
        try:
            import json as _json

            from monetization_tracker import PROGRESS_PATH
            _m = _json.loads(PROGRESS_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
        if not dry_run:
            write_daily_brief(ml_data=ml.data, journal=_j, monetization=_m)
            logger.info("☕ Daily brief written — data/daily_brief.md")
    except Exception as exc:
        logger.warning("daily brief skipped: %s", exc)

    published_count = sum(
        1 for r in results.values() if r.get("ok") and not r.get("dry_run"))
    blocked_count = sum(1 for r in results.values() if r.get("gate_blocked"))
    skipped_count = sum(1 for r in results.values() if r.get("skipped"))
    failed_count = sum(
        1 for r in results.values()
        if not r.get("ok") and not r.get("gate_blocked") and not r.get("skipped"))
    success = bool(dry_run or published_count > 0)
    run_status = "success" if success else "blocked"
    journal.finish_run(run_id, run_status,
                       "; ".join(f"{p}:{'OK' if r.get('ok') else 'FAIL'}"
                                 for p, r in results.items()))
    elapsed = time.time() - start
    logger.info("✅ DONE in %.0fs — %s (published=%d blocked=%d skipped=%d failed=%d)",
                elapsed, script["title"], published_count, blocked_count,
                skipped_count, failed_count)
    return {"success": success, "run_id": run_id, "results": results,
            "published_count": published_count, "blocked_count": blocked_count,
            "skipped_count": skipped_count, "failed_count": failed_count,
            "title": script["title"], "elapsed_s": round(elapsed, 1)}


def main():
    ap = argparse.ArgumentParser(description="Coercion Files pipeline")
    ap.add_argument("--platforms", default=None,
                    help="comma list: youtube,facebook,instagram (default: all enabled)")
    ap.add_argument("--dry-run", action="store_true",
                    help="build everything, never call upload APIs")
    ap.add_argument("--pillar", default=None, help="force a content pillar key")
    ap.add_argument("--topic", default=None, help="force a topic")
    ap.add_argument("--selftest", action="store_true",
                    help="run offline smoke tests and exit")
    ap.add_argument("--simulate", action="store_true",
                    help="simulate ML learning (UCB convergence) and exit")
    ap.add_argument("--repeat", type=int, default=1,
                    help="build N videos per run (default: 1)")
    args = ap.parse_args()

    if args.selftest:
        sys.exit(0 if selftest() else 1)
    if args.simulate:
        import random as _r
        ls = LearningSystem(store_path=Path("/tmp/ml_sim.json"))
        ls.data["arms"] = {}
        qual = {"pattern_interrupt": .8, "knowledge_gap": .7, "fear_based": .55,
                "curiosity_trigger": .65, "counterintuitive": .6, "dark_revelation": .5,
                "stoic_echo": .75, "red_flag_checklist": .85}
        for _ in range(300):
            s = ls.choose_strategy()
            base_quality = qual.get(s["hook_style"], 0.60)
            ls.record_outcome(s["arm_key"], base_quality + _r.uniform(-.15, .15))
        print("Top formulas after simulation:")
        for t in ls.best_formulas(6):
            print(f"  {t['pillar']:>16} / {t['hook_style']:<22} mean={t['mean']:.3f} n={t['n']}")
        sys.exit(0)

    platforms = [p.strip() for p in args.platforms.split(",")] if args.platforms else None
    try:
        # Run pipeline N times (for daily volume)
        all_results = []
        for i in range(args.repeat):
            logger.info("=== Video %d/%d ===", i + 1, args.repeat)
            res = run_pipeline(platforms=platforms, dry_run=args.dry_run,
                               pillar=args.pillar, topic=args.topic)
            all_results.append(res)
            if not res.get("success"):
                logger.warning("Video %d failed — continuing to next", i + 1)
                time.sleep(5)
        if all_results and not any(r.get("success") for r in all_results):
            sys.exit(2)
    except Exception as exc:
        logger.error("Pipeline crashed:\n%s", traceback.format_exc())
        if not args.dry_run:
            journal = RepairJournal()
            journal.data.setdefault("current", {}).update(
                {"status": "crashed",
                 "error": LearningSystem._sanitize_reason(str(exc))})
            journal._write()
        sys.exit(1)


if __name__ == "__main__":
    main()
