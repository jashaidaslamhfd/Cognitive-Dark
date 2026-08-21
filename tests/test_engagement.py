"""Tests for engagement layer (V3.1) — like-CTA in scripts, hook gate, audit."""
import subprocess
import sys
from pathlib import Path

from script_generator import _template_script
from viral_intel import score_hook


def _pillar():
    return {"key": "con_artists", "name": "Con Artists", "hooks": ["The hook"],
            "tags": ["a"], "search_terms": ["scam psychology"]}


def test_template_script_cta_mentions_engagement():
    """Har template script mein ya to like/comment ask ya follow CTA hona chahiye."""
    hits = {"like": 0, "comment": 0, "follow": 0, "save": 0, "share": 0}
    for _ in range(30):
        s = _template_script(_pillar(), "warning")
        text = " ".join(sc["caption"] for sc in s["scenes"]).lower()
        for word in hits:
            if word in text:
                hits[word] += 1
    # kuch scripts mein like/comment ask hona chahiye (60% engagement mix)
    assert hits["like"] > 0 or hits["comment"] > 0, f"no engagement CTA: {hits}"
    assert hits["follow"] + hits["save"] + hits["share"] > 0  # mix bhi hai


def test_hook_gate_scores():
    good = score_hook("Stop letting them control you.")["score"]
    weak = score_hook("Here is a video about some things")["score"]
    assert good > weak


def test_analyze_engagement_dry_runs(tmp_path):
    """--dry mode: bina YT creds bhi crash nahi — report file na bane (koi vids)."""
    try:
        import dotenv  # noqa: F401
    except ImportError:
        import pytest
        pytest.skip("python-dotenv not installed in sandbox")
    r = subprocess.run(
        [sys.executable, "scripts/analyze_engagement.py", "--dry"],
        cwd=Path(__file__).resolve().parent.parent,
        capture_output=True, text=True, timeout=60)
    # bina creds ke gracefully exit (0 ya 1 dono chalega, crash nahi)
    assert r.returncode in (0, 1)
    assert "Koi video" in r.stdout or "Videos:" in r.stdout


def test_score_script_strong_script():
    """Achhi script (hook + cta + anchor + psych) ko A/B grade milna chahiye."""
    from viral_intel import score_script, score_script_grade
    good = {
        "hook": "Stop letting them control you.",
        "scenes": [
            {"caption": "Stop letting them control you."},
            {"caption": "The $400k wire transfer happened in 3 days. Cognitive "
                         "dissonance made her send it."},
            {"caption": "Cialdini's scarcity principle explains the urgency. "
                         "If this helped, hit like and comment below."},
        ],
    }
    q = score_script(good)
    assert q["score"] >= 0.7, q
    assert score_script_grade(q["score"]) in ("A — strong script", "B — solid")


def test_score_script_weak_script():
    from viral_intel import score_script
    weak = {"hook": "Hello everyone", "scenes": [
        {"caption": "Welcome back to my channel"}]}
    q = score_script(weak)
    assert q["score"] < 0.5, q


def test_cta_pair_is_useful_and_not_bait():
    """CTA prompts retain a closing action without incentivized engagement."""
    from compulsion_cta import contains_bait, cta_pair, has_engagement
    seen = set()
    for _ in range(60):
        pair = cta_pair()
        text = " ".join(pair)
        assert has_engagement(text), f"no engage word: {text}"
        assert not contains_bait(text), f"engagement bait detected: {text}"
        # variation — har baar same na ho
        seen.add(text[:30])
    assert len(seen) >= 8, f"too repetitive: {len(seen)} unique"


def test_build_engaging_last_scene():
    from compulsion_cta import build_engaging_last_scene, has_engagement
    scene = build_engaging_last_scene("cults")
    assert has_engagement(scene["caption"])
    assert scene["caption_roman"] == scene["caption"]
    assert scene["emotion"] == "revelatory"


def test_llm_cta_instructions_are_policy_safe():
    from compulsion_cta import llm_cta_instructions
    txt = llm_cta_instructions().lower()
    assert "save" in txt and "evidence-led" in txt
    assert "algorithm won't show" not in txt
    assert "artificial like threshold" in txt


def test_yt_package_always_has_keyword():
    """V3.6.3: SEOGuard keyword requirement — YT package title mein keyword
    HAMESHA hona chahiye, chahe CTR boost/title picker kuch bhi chune."""
    import random

    from config.settings import PILLARS
    from seo import build_platform_package
    random.seed(7)
    for _ in range(10):
        script = {
            "hook": "How One Ad Manipulated a Country",
            "title": "How One Ad Manipulated a Country",
            "pillar": "mind_control_history",
            "pillar_name": "Declassified Mind Control",
            "key_points": "• x",
            "tags": ["psychology"],
            "scenes": [{"caption": "How one ad manipulated a country with repeated messaging."},
                       {"caption": "The declassified files show the propaganda campaign ran for months."},
                       {"caption": "Milgram proved obedience rises under authority pressure."},
                       {"caption": "Hit like if this helps you spot manufactured consent. Comment below."}],
        }
        pkg = build_platform_package(script, "youtube", durations=[4.0] * 4)
        kw = next(p["search_terms"][0] for p in PILLARS
                  if p["key"] == "mind_control_history")
        assert kw.lower() in pkg["title"].lower(), pkg["title"]
        assert pkg["title"].count("|") <= 0  # pipe-stuffing wapas nahi


def test_structure_repair_splits_long_scenes_and_pads_short():
    """V3.6.5: LLM ki choti script (3 scenes / 68 words) repair ho kar
    guards ke minimum (4 scenes, 100+ words) par aa jani chahiye. Lambi
    scene (50 words) split honi chahiye."""
    from script_generator import _repair_script_structure
    script = {
        "hook": "Why smart people join cults",
        "title": "The Truth About Watch What They Say When You Say No And Never Trust Them Again",
        "scenes": [
            {"caption": "Why smart people join cults and never see it coming."},
            {"caption": "A documented case file shows the same loop: trust first, "
                        "then isolation, then manufactured urgency, then total "
                        "surrender before the victim even realizes what happened "
                        "to their life savings and their family relationships "
                        "over the following weeks and months."},
            {"caption": "The scammer triggered fear before doubt could form."},
        ],
    }
    out = _repair_script_structure(script)
    words = len(" ".join(s.get("caption", "") for s in out["scenes"]).split())
    assert len(out["scenes"]) >= 4
    assert words >= 100
    assert all(len(s.get("caption", "").split()) <= 38
               for s in out["scenes"])
    # CTA aakhri scene mein
    full = " ".join(s.get("caption", "") for s in out["scenes"]).lower()
    assert any(w in full for w in ("like", "comment", "save", "hit"))
    # title 20-70 chars
    assert 20 <= len(out["title"]) <= 70, out["title"]


def test_structure_repair_clamps_and_normalizes_title():
    from script_generator import _repair_script_structure
    script = {
        "hook": "Can a 5-second pause stop a fraudster",
        "title": "Can a 5\u2011second pause stop a fraudster \u2014 What Nobody Tells You About It All",
        "scenes": [
            {"caption": "Can a five second pause stop a fraudster in real life."},
            {"caption": "The case file shows the scammer demanded instant action every time."},
            {"caption": "Cialdini's scarcity explains why the rush worked on every victim."},
            {"caption": "Comment the sign you recognized first, and hit like."},
        ],
    }
    out = _repair_script_structure(script)
    assert len(out["title"]) <= 70
    assert "\u2011" not in out["title"] and "\u2014" not in out["title"]


def test_hook_sync_replaces_first_sentence_when_mismatch():
    """V3.6.5: LLM script mein purana hook scene 0 mein nahi hota →
    pehla sentence hi naye hook se replace (clickbait gap khatam)."""
    from script_generator import _replace_hook_everywhere
    script = {
        "hook": "Why smart people join cults",
        "title": "Something else entirely",
        "scenes": [{"caption": "The recruiter smiled and said trust me. "
                              "Here is the breakdown."}],
    }
    _replace_hook_everywhere(script, "Old hook that LLM wrote")
    s0 = script["scenes"][0]["caption"]
    assert s0.startswith("Why smart people join cults."), s0
    assert "Why smart people join cults" in script["title"]
