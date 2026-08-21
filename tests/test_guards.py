"""Independent Release Gate tests (V3.5).

Har test ek guard ki independence ya fail-closed honesty verify karta hai.
Sab se important tests:
  • weak hook/script ko guard FAIL karta hai
  • missing audio (silence fallback) ko VoiceGuard FAIL karta hai
  • no real data par ViewsGuard pass hota hai MAGAR proven-weak formula par FAIL
  • producer ke self-scores gate mein strip ho jate hain (guards unhein
    dekh hi nahi sakte)
  • supervisor bina evidence / UNKNOWN measurement par HOLD karta hai
  • full-pass payload (real wavs + real ffmpeg video) → RELEASED
"""
import math
import shutil
import struct
import wave
from pathlib import Path

import pytest

from guards.gate import PRODUCER_SCORE_KEYS, ReleaseGate

# ── helpers ──────────────────────────────────────────────────────


def _write_tone_wav(path: Path, seconds: float = 10.0, freq: float = 220.0,
                    rate: int = 22050, amp: int = 12000) -> Path:
    """Real audible sine WAV (VoiceGuard ke liye)."""
    n = int(seconds * rate)
    frames = bytearray()
    for i in range(n):
        s = int(amp * math.sin(2 * math.pi * freq * i / rate))
        frames += struct.pack("<h", s)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(bytes(frames))
    return path


def _write_silence_wav(path: Path, seconds: float = 10.0, rate: int = 22050) -> Path:
    return _write_tone_wav(path, seconds, freq=1.0, amp=0)


def _strong_script() -> dict:
    """Ek acha USA-standard script (sab text-guards pass karein)."""
    hook = "Why smart people join cults"
    scenes = [
        {"caption": f"{hook}. Here is the exact case breakdown from the files.",
         "caption_roman": "same", "visual": "dark city", "emotion": "dark"},
        {"caption": "In a documented 2023 case file, a $400,000 wire transfer "
                    "was approved in eleven minutes without a single question "
                    "being asked by the victim.",
         "caption_roman": "same", "visual": "bank", "emotion": "intense"},
        {"caption": "The FBI transcript shows the scammer manufactured urgency "
                    "first, because fear triggers the amygdala and shuts down "
                    "the prefrontal cortex before any doubt can form.",
         "caption_roman": "same", "visual": "files", "emotion": "chilling"},
        {"caption": "Milgram's experiment proved obedience rises under "
                    "authority. Cialdini's scarcity principle explains exactly "
                    "why the manufactured deadline worked.",
         "caption_roman": "same", "visual": "study", "emotion": "mysterious"},
        {"caption": "Hit like if this pattern helps you spot the trap before "
                    "it closes. Comment the sign you recognized first — I read "
                    "every comment.",
         "caption_roman": "same", "visual": "night", "emotion": "revelatory"},
    ]
    return {"title": "Why Smart People Join Cults: Cult Psychology",
            "hook": hook, "scenes": scenes,
            "tags": ["cult psychology", "psychology", "scams"],
            "arm_key": "cults::question_hook::morning"}


def _good_yt_package() -> dict:
    return {
        "platform": "youtube",
        "title": "Why Smart People Join Cults: Cult Psychology",
        "description": (
            "Cult psychology: how coercion works, why smart people fall for it, "
            "and exactly how to protect yourself.\n\n"
            "🔍 WHAT YOU'LL LEARN:\n• the recruitment pattern\n• the brain trap\n"
            "• the one-minute defense\n\n"
            "📌 Follow for daily psychology shorts.\n"
            "⚠️ For educational purposes only — learn to recognize and protect "
            "yourself. Not a substitute for professional advice.\n\n"
            "#psychology #truecrime #mindcontrol"),
        "tags": ["cult psychology", "psychology facts", "dark psychology",
                 "manipulation", "self improvement", "mindset"],
        "hashtags": ["psychology", "truecrime", "mindcontrol"],
        "hook": "Why smart people join cults",
    }


def _segments(tmp_path: Path, n: int = 4, seconds: float = 10.0) -> list:
    texts = [
        "Why smart people join dangerous cults every single year without "
        "realizing the recruitment pattern until it is far too late",
        "In a documented case file a four hundred thousand dollar wire "
        "transfer was approved in eleven minutes without a single question",
        "The FBI transcript shows the scammer triggered fear first because "
        "the amygdala shuts down the prefrontal cortex before doubt forms",
        "Milgram proved obedience rises under authority while Cialdini "
        "explains exactly how manufactured urgency disables good judgment",
    ]
    segs = []
    for i in range(n):
        p = _write_tone_wav(tmp_path / f"seg_{i}.wav", seconds=seconds)
        segs.append({"path": str(p), "duration": seconds,
                     "text": texts[i % len(texts)]})
    return segs


def _mk_video(tmp_path: Path, seconds: float = 40.0) -> Path:
    """Real 1080x1920 mp4 with audio via ffmpeg (VideoGuard pass ke liye)."""
    out = tmp_path / "final.mp4"
    import subprocess
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i",
         f"testsrc2=size=1080x1920:rate=30:duration={seconds}",
         "-f", "lavfi", "-i", "sine=frequency=440:duration=" + str(seconds),
         "-c:v", "libx264", "-preset", "ultrafast", "-threads", "4",
         "-b:v", "4000k", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-shortest", str(out)],
        check=True, capture_output=True, timeout=280)
    return out


# ── 1. HookGuard: weak hook fail, strong pass ────────────────────


def test_hook_guard_blocks_weak_hook():
    from guards.hook_guard import HookGuard
    g = HookGuard()
    for weak in ["Let me tell you about psychology",
                 "Stop letting them", "Welcome to my channel"]:
        v = g.check({"script": {"hook": weak}})
        assert v.status == "FAIL", (weak, v.reason)
    v = g.check({"script": {"hook": "Why smart people join cults"}})
    assert v.status in ("PASS", "WARN"), v.reason


def test_hook_guard_passes_concrete_hook():
    from guards.hook_guard import HookGuard
    v = HookGuard().check(
        {"script": {"hook": "They stole $400k with 3 words"}})
    assert v.status in ("PASS", "WARN"), v.reason


# ── 2. ScriptGuard: fluff fail, concrete pass ────────────────────


def test_script_guard_blocks_fluff():
    from guards.script_guard import ScriptGuard
    fluff = {"hook": "Hello everyone", "scenes": [
        {"caption": "Hello everyone and welcome back to my channel."},
        {"caption": "In this video we will talk about many things."},
        {"caption": "Let me tell you something interesting."},
        {"caption": "Please subscribe for more."}]}
    v = ScriptGuard().check({"script": fluff})
    assert v.status == "FAIL", v.reason
    assert "fluff" in v.reason.lower() or "anchor" in v.reason.lower()


def test_script_guard_passes_strong_script():
    from guards.script_guard import ScriptGuard
    v = ScriptGuard().check({"script": _strong_script()})
    assert v.status in ("PASS", "WARN"), v.reason


# ── 3. VoiceGuard: silence/missing = FAIL (fail-closed) ─────────


def test_voice_guard_fails_missing_audio():
    from guards.voice_guard import VoiceGuard
    segs = [{"path": None, "duration": 4.0, "text": "hello world " * 4}]
    v = VoiceGuard().check({"segments": segs})
    assert v.status == "FAIL"
    assert "NO audio" in v.reason or "silence" in v.reason


def test_voice_guard_fails_silent_wav(tmp_path: Path):
    from guards.voice_guard import VoiceGuard
    p = _write_silence_wav(tmp_path / "silent.wav", seconds=5.0)
    segs = [{"path": str(p), "duration": 5.0, "text": "word " * 11}]
    v = VoiceGuard().check({"segments": segs})
    assert v.status == "FAIL", v.reason
    assert "silence" in v.reason.lower()


def test_voice_guard_passes_real_wavs(tmp_path: Path):
    from guards.voice_guard import VoiceGuard
    segs = _segments(tmp_path, n=4, seconds=10.0)
    v = VoiceGuard().check({"segments": segs})
    assert v.status in ("PASS", "WARN"), v.reason


# ── 4. CaptionGuard: mismatch = FAIL ────────────────────────────


def test_caption_guard_fails_voice_mismatch():
    from guards.caption_guard import CaptionGuard
    script = {"scenes": [{"caption": "Caption text one"}, {"caption": "Two"}]}
    segs = [{"path": None, "text": "Completely different voice text"},
            {"path": None, "text": "Also different"}]
    v = CaptionGuard().check({"script": script, "segments": segs})
    assert v.status == "FAIL"
    assert "≠" in v.reason or "match" in v.reason.lower()


def test_caption_guard_passes_matching():
    from guards.caption_guard import CaptionGuard
    script = {"scenes": [{"caption": "Same text here."}, {"caption": "Same two."}]}
    segs = [{"path": None, "text": "Same text here."},
            {"path": None, "text": "Same two."}]
    v = CaptionGuard().check({"script": script, "segments": segs})
    assert v.status in ("PASS", "WARN"), v.reason


# ── 5. VideoGuard: silent/wrong-format video = FAIL ─────────────


def test_video_guard_unknown_when_missing():
    from guards.video_guard import VideoGuard
    v = VideoGuard().check({"video_path": "/nonexistent/x.mp4"})
    assert v.status == "UNKNOWN"   # measure nahi kar saka → fail-closed


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg needed")
def test_video_guard_measures_real_video(tmp_path: Path):
    from guards.video_guard import VideoGuard
    good = _mk_video(tmp_path, seconds=40.0)
    v = VideoGuard().check({"video_path": str(good)})
    assert v.status in ("PASS", "WARN"), v.reason
    ev = v.evidence
    assert ev["width"] == 1080 and ev["height"] == 1920
    assert ev["has_audio"] is True


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg needed")
def test_video_guard_fails_silent_video(tmp_path: Path):
    from guards.video_guard import VideoGuard
    out = tmp_path / "silent.mp4"
    import subprocess
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i",
         "testsrc2=size=1080x1920:rate=30:duration=40",
         "-c:v", "libx264", "-preset", "ultrafast", "-threads", "4",
         "-b:v", "4000k", "-pix_fmt", "yuv420p",
         str(out)], check=True, capture_output=True, timeout=280)
    v = VideoGuard().check({"video_path": str(out)})
    assert v.status == "FAIL"
    assert "audio" in v.reason.lower()


# ── 6. SEOGuard: per-platform 2026 rules ────────────────────────


def test_seo_guard_yt_fails_missing_keyword_and_disclaimer():
    from guards.seo_guard import SEOGuard
    pkg = {"title": "Amazing Video", "description": "short desc",
           "tags": [], "hashtags": []}
    v = SEOGuard().check({"platform": "youtube", "package": pkg})
    assert v.status == "FAIL", v.reason


def test_seo_guard_yt_passes_good_package():
    from guards.seo_guard import SEOGuard
    v = SEOGuard().check({"platform": "youtube", "package": _good_yt_package()})
    assert v.status in ("PASS", "WARN"), v.reason


def test_seo_guard_yt_passes_interrogation_pillar_title():
    """'Lie Detection: Why Innocent People Confess' legit hai — pillar ke
    search terms keyword list mein aane chahiye (false negative fix)."""
    from guards.seo_guard import SEOGuard
    pkg = {"title": "Lie Detection: Why Innocent People Confess",
           "description": ("Lie detection psychology: how interrogation works, "
                           "why innocent people confess under pressure, and the "
                           "exact signs investigators watch for. This is a "
                           "documented breakdown of statement analysis and body "
                           "language cues from real interrogation cases.\n\n"
                           "⚠️ For educational purposes only — learn to "
                           "recognize and protect yourself. Not a substitute "
                           "for professional advice.\n\n"
                           "#psychology #truecrime #interrogation"),
           "tags": ["lie detection", "psychology", "interrogation"],
           "hashtags": ["psychology", "truecrime"]}
    payload = {"platform": "youtube", "package": pkg,
               "script": {"pillar": "interrogation"}}
    v = SEOGuard().check(payload)
    assert v.status in ("PASS", "WARN"), v.reason


def test_seo_guard_ig_fails_without_save_cta():
    from guards.seo_guard import SEOGuard
    pkg = {"title": "Signs to know",
           "description": "Signs you should know about. Read the caption. "
                          "Educational disclaimer for your safety.",
           "tags": [], "hashtags": ["psychology"] * 12}
    v = SEOGuard().check({"platform": "instagram", "package": pkg})
    assert v.status == "FAIL", v.reason


# ── 7. CTRGuard: weak title fail, strong pass ───────────────────


def test_ctr_guard_blocks_weak_title():
    from guards.ctr_guard import CTRGuard
    pkg = {"title": "video about things", "description": "x", "tags": [],
           "hashtags": []}
    script = {"hook": "Why smart people join cults"}
    v = CTRGuard().check({"platform": "youtube", "package": pkg,
                          "script": script})
    assert v.status == "FAIL", v.reason


def test_ctr_guard_passes_strong_title():
    from guards.ctr_guard import CTRGuard
    pkg = _good_yt_package()
    v = CTRGuard().check({"platform": "youtube", "package": pkg,
                          "script": {"hook": "Why smart people join cults"}})
    assert v.status in ("PASS", "WARN"), v.reason


# ── 8. ViewsGuard: real performance hi maanta hai ───────────────


def test_views_guard_passes_without_data(tmp_path: Path, monkeypatch):
    from guards.views_guard import ViewsGuard
    from ml_engine import LearningSystem
    monkeypatch.setenv("FB_ACCESS_TOKEN", "test-token")  # metrics pipeline on
    ml = LearningSystem(store_path=tmp_path / "store.json")
    v = ViewsGuard().check({"ml": ml, "platform": "youtube",
                            "script": {"arm_key": "cults::warning::morning"}})
    assert v.status == "PASS"    # no data = monitoring (block nahi)
    assert "no real data" in v.reason


def test_views_guard_blocks_proven_weak_formula(tmp_path: Path):
    from guards.views_guard import ViewsGuard
    from ml_engine import LearningSystem
    ml = LearningSystem(store_path=tmp_path / "store.json")
    key = "cults::warning::morning"
    for _ in range(4):
        ml.record_outcome(key, -0.5)   # real outcomes: formula fail ho raha
    v = ViewsGuard().check({"ml": ml, "platform": "youtube",
                            "script": {"arm_key": key}})
    assert v.status == "FAIL"
    assert "PROVEN weak" in v.reason


def test_views_guard_passes_working_formula(tmp_path: Path, monkeypatch):
    from guards.views_guard import ViewsGuard
    from ml_engine import LearningSystem
    monkeypatch.setenv("FB_ACCESS_TOKEN", "test-token")
    ml = LearningSystem(store_path=tmp_path / "store.json")
    key = "cults::warning::morning"
    for _ in range(3):
        ml.record_outcome(key, 2.0)
    v = ViewsGuard().check({"ml": ml, "platform": "youtube",
                            "script": {"arm_key": key}})
    assert v.status == "PASS", v.reason


# ── 9. Independence: producer scores gate mein strip ho jate hain ─


def test_producer_scores_never_reach_guards():
    payload = {"platform": "youtube", "script": {
        "hook": "x", "title": "y",
        "script_quality": {"score": 1.0}, "hook_score": 0.99}}
    clean = ReleaseGate._sanitize(payload)
    script = clean["script"]
    for k in PRODUCER_SCORE_KEYS:
        assert k not in script, f"{k} leak hua guards tak"


# ── 10. Supervisor: fail-closed ─────────────────────────────────


def test_supervisor_holds_on_unknown_measurement():
    from guards.base import GuardVerdict
    from guards.supervisor import USASupervisor
    verdicts = [GuardVerdict("voice", "PASS", "ok", {"measured": 1}),
                GuardVerdict("video", "UNKNOWN", "probe fail", {})]
    out = USASupervisor().review({"script": {}, "package": {}}, verdicts)
    assert out["released"] is False
    assert any("fail-closed" in v or "unknown" in v.lower()
               for v in out["violations"])


def test_supervisor_holds_on_urdu_tokens():
    from guards.base import GuardVerdict
    from guards.supervisor import USASupervisor
    script = {"hook": "Achhi video hai", "title": "Psychology tips",
              "scenes": [{"caption": "Yeh cheez kaam karti hai."}]}
    verdicts = [GuardVerdict("hook", "PASS", "ok", {"words": 3})]
    out = USASupervisor().review({"script": script, "package": {}}, verdicts)
    assert out["released"] is False
    assert any("non-English" in v or "English" in v for v in out["violations"])


def test_supervisor_rejects_british_spelling():
    from guards.base import GuardVerdict
    from guards.supervisor import USASupervisor
    script = {"hook": "Why behaviour changes", "title": "The colour of control",
              "scenes": [{"caption": "Behaviour changes slowly."}]}
    verdicts = [GuardVerdict("hook", "PASS", "ok", {"words": 3})]
    out = USASupervisor().review({"script": script, "package": {}}, verdicts)
    assert out["released"] is False
    assert any("British" in v for v in out["violations"])


def test_supervisor_currency_no_false_positive():
    """'rs.' regex "transfers." jaisi English par false-positive NAHIN de."""
    from guards.base import GuardVerdict
    from guards.supervisor import USASupervisor
    script = {"hook": "Why bank transfers fail",
              "title": "Bank transfers explained",
              "scenes": [{"caption": "She approved the transfer in minutes. "
                                     "The money moved before she could think."}]}
    verdicts = [GuardVerdict("hook", "PASS", "ok", {"words": 3})]
    out = USASupervisor().review({"script": script, "package": {}}, verdicts)
    assert out["released"] is True, out["violations"]


def test_hook_override_syncs_scene_and_title():
    """Producer ka hook-override ab scene-1 + title bhi update karta hai
    (purana bug: overlay naya hook, narration purana = clickbait gap)."""
    from script_generator import _replace_hook_everywhere
    script = {
        "hook": "Weak hook here",
        "title": "Weak hook here | Forensic Psychology",
        "scenes": [{"caption": "Weak hook here. Here is the exact case "
                               "breakdown.", "caption_roman": "x"}]}
    script["hook"] = "Why smart people join cults"   # override
    _replace_hook_everywhere(script, "Weak hook here")
    assert script["scenes"][0]["caption"].startswith("Why smart people join cults")
    assert "Weak hook" not in script["scenes"][0]["caption"]
    assert script["title"].startswith("Why smart people join cults")


# ── 11. Gate integration: weak payload = HELD, strong = RELEASED ─


def test_gate_holds_weak_payload(tmp_path: Path):
    gate = ReleaseGate(mode="strict", report_dir=tmp_path)
    payload = {
        "platform": "youtube",
        "script": {"hook": "Welcome to my channel",
                   "title": "video",
                   "arm_key": "cults::warning::morning",
                   "script_quality": {"score": 0.99},  # producer ki khud-tareef
                   "scenes": [{"caption": "Welcome to my channel everyone."},
                              {"caption": "Please subscribe."}]},
        "segments": [{"path": None, "duration": 3.0, "text": "x"}],
        "video_path": "/nonexistent.mp4",
        "thumb_path": None,
        "package": {"title": "video", "description": "x", "tags": [],
                    "hashtags": []},
        "publish_at": None, "ml": None,
    }
    rep = gate.evaluate(payload)
    assert rep.released is False
    assert rep.grade == "F"
    assert rep.blocking_reasons()
    assert (tmp_path / "gate_report.json").exists()
    assert (tmp_path / "gate_report.md").exists()


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg needed")
def test_gate_full_release_with_real_artifacts(tmp_path: Path, monkeypatch):
    """Pura stack: real wavs + real ffmpeg video + strong script/packages →
    SAB guards pass → supervisor RELEASES."""
    import re as _re
    monkeypatch.setenv("FB_ACCESS_TOKEN", "test-token")
    gate = ReleaseGate(mode="strict", report_dir=tmp_path)
    video = _mk_video(tmp_path, seconds=40.0)
    script = _strong_script()
    # captions VOICE text ke exact match hone chahiye (caption guard) —
    # har scene ki wav duration us ke words ke hisaab se (~2.1 wps US pace)
    segs = []
    for i, sc in enumerate(script["scenes"]):
        n_words = len(_re.findall(r"[A-Za-z']+", sc["caption"]))
        dur = max(1.5, round(n_words / 2.1, 1))
        p = _write_tone_wav(tmp_path / f"seg_{i}.wav", seconds=dur)
        segs.append({"path": str(p), "duration": dur, "text": sc["caption"]})
    payload = {
        "platform": "youtube",
        "script": script,
        "segments": segs,
        "video_path": str(video),
        "thumb_path": None,
        "package": _good_yt_package(),
        "publish_at": None,
        "ml": None,
    }
    rep = gate.evaluate(payload)
    for v in rep.verdicts:
        print(f"  {v.guard}: {v.status} — {v.reason[:90]}")
    assert rep.released is True, rep.blocking_reasons()
    assert rep.grade in ("A", "B", "C")


def test_gate_warn_mode_never_blocks(tmp_path: Path):
    gate = ReleaseGate(mode="warn", report_dir=tmp_path)
    payload = {"platform": "youtube", "script": {"hook": ""},
               "segments": [], "video_path": "/nonexistent.mp4",
               "package": {}, "ml": None}
    rep = gate.evaluate(payload)
    assert rep.released is True     # report banti hai, block nahi
    assert rep.verdicts             # guards phir bhi chale


def test_ctr_guard_stem_overlap_not_blocked():
    """V3.6.1: 'cult'/'cults' jaisa plural title↔hook pair legit hai —
    stem overlap se match hona chahiye, block nahi."""
    from guards.ctr_guard import CTRGuard
    v = CTRGuard().check({
        "platform": "youtube",
        "package": {"title": "3 Signs You're in a Cult: Warning Psychology"},
        "script": {"hook": "Why smart people join cults"},
    })
    assert v.status in ("PASS", "WARN"), v.reason
    assert v.evidence["hook_link"] > 0


def test_seo_guard_capital_keyword_case_insensitive():
    """V3.6.4: 'MKUltra Explained' jaisa capital keyword title.lower() mein
    case-sensitive check se kabhi match nahi hota tha — pillar keywords
    wale titles ghalat FAIL hote thay."""
    from guards.seo_guard import SEOGuard
    pkg = {
        "title": "Watch What They Say When You Say No: Mkultra Explained",
        "description": ("Mkultra explained: how one ad campaign manipulated "
                        "a country, and how to protect yourself from the same "
                        "pattern. Documented psychology case breakdown with "
                        "the exact propaganda techniques decoded so viewers "
                        "can spot them early. Educational — not a substitute "
                        "for professional advice. #psychology #truecrime"),
        "tags": ["mkultra", "psychology", "propaganda"],
        "hashtags": ["psychology", "truecrime"],
    }
    payload = {"platform": "youtube", "package": pkg,
               "script": {"pillar": "mind_control_history"}}
    v = SEOGuard().check(payload)
    assert v.status in ("PASS", "WARN"), v.reason


def test_ctr_guard_watch_hook_passes():
    """'Watch what they say...' pattern-interrupt hook hai — guard ki POWER
    list mein watch nahi tha → ghalat FAIL."""
    from guards.ctr_guard import CTRGuard
    v = CTRGuard().check({
        "platform": "facebook",
        "package": {"title": "Watch what they say when you say no"},
        "script": {"hook": "Watch what they say when you say no"},
    })
    assert v.status in ("PASS", "WARN"), v.reason


# ── 10. Meta policy-safe Instagram packaging ─────────────────────


def test_seo_guard_ig_passes_policy_safe_package():
    from guards.seo_guard import SEOGuard

    pkg = {
        "title": "What Nobody Tells You About Coercion",
        "description": (
            "Save this checklist for your next high-pressure conversation. "
            "This evidence-led case explains how coercion works, what to verify "
            "before acting, and how to protect your judgment. "
            "For educational purposes only — learn to recognize patterns and "
            "protect yourself. "
            "#psychology #coercivecontrol #selfdefense"
        ),
        "tags": [],
        "hashtags": ["psychology", "coercivecontrol", "selfdefense"],
    }
    verdict = SEOGuard().check({"platform": "instagram", "package": pkg})
    assert verdict.status == "PASS", verdict.reason


def test_seo_guard_meta_rejects_bait_and_excess_hashtags():
    from guards.seo_guard import SEOGuard

    pkg = {
        "title": "What Nobody Tells You About Coercion",
        "description": (
            "Like this to get the video to someone who needs it. "
            "Save the case file for later review. "
            "Educational purposes only — protect yourself."
        ),
        "tags": [],
        "hashtags": ["one", "two", "three", "four", "five", "six"],
    }
    verdict = SEOGuard().check({"platform": "instagram", "package": pkg})
    assert verdict.status == "FAIL", verdict.reason
    assert "engagement-bait" in verdict.reason
    assert "hashtags" in verdict.reason


def test_ctr_guard_accepts_natural_instagram_question_title():
    from guards.ctr_guard import CTRGuard

    pkg = {"title": "What Nobody Tells You About Coercion"}
    verdict = CTRGuard().check({
        "platform": "instagram",
        "package": pkg,
        "script": {"hook": "What Nobody Tells You About Coercion"},
    })
    assert verdict.status == "PASS", verdict.reason
