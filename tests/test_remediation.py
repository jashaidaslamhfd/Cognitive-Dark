import json
from datetime import datetime, timezone

from config.settings import PILLARS
from ml_engine import LearningSystem
from script_generator import _template_script
from seo import _description


def test_read_only_ml_dry_run_does_not_persist(tmp_path):
    store = tmp_path / "store.json"
    store.write_text(json.dumps({"arms": {}, "videos": [], "attribution": {},
                                "post_log": {}, "publish_claims": {},
                                "penalty_log": [], "reward_log": [],
                                "health": {}}), encoding="utf-8")
    before = store.read_text(encoding="utf-8")
    ml = LearningSystem(store_path=store, persist=False)
    ml.record_post("instagram")
    ml.apply_reward("cults::warning::morning", "preview", 1.0)
    assert store.read_text(encoding="utf-8") == before
    assert not ml.events_path.exists()


def test_claim_release_is_replayable(tmp_path):
    store = tmp_path / "store.json"
    ml = LearningSystem(store_path=store)
    publish_at = datetime(2030, 1, 1, tzinfo=timezone.utc)
    assert ml.claim_publish("instagram", publish_at, "run-a")[0]
    ml.release_claim("instagram", publish_at)
    assert not ml.data["publish_claims"].get("instagram")

    store.unlink()
    backup = store.with_suffix(store.suffix + ".bak")
    if backup.exists():
        backup.unlink()
    rebuilt = LearningSystem(store_path=store)
    assert not rebuilt.data["publish_claims"].get("instagram")


def test_unavailable_views_are_not_credited(tmp_path):
    ml = LearningSystem(store_path=tmp_path / "store.json")
    arm = "cults::warning::morning"
    ml.record_video_id("instagram", "media-1", arm, "title")
    assert ml.credit_video("media-1", {
        "views": 0,
        "views_status": "unavailable",
        "impressions_status": "unavailable",
        "platform": "instagram",
    }) == 0.0
    record = ml.data["attribution"]["media-1"]
    assert record["credited"] is False
    assert record["metrics_status"] == "unavailable"
    assert ml.data["arms"].get(arm, {}).get("n", 0) == 0


def test_template_fallback_respects_requested_topic():
    script = _template_script(PILLARS[1], "warning", topic="How to spot an urgent bank scam")
    assert "How to spot an urgent bank scam" in script["hook"]
    assert "How to spot an urgent bank scam" in script["title"]
    assert script["claim_mode"] == "fictional_composite"


def test_description_discloses_sources_or_composite_status():
    script = {
        "title": "A Test",
        "hook": "A case study about pressure",
        "key_points": "case study; authority bias; save this checklist",
        "pillar_name": "Psychology",
        "claim_mode": "fictional_composite",
        "sources": [],
    }
    text = _description(script, "instagram")
    assert "Illustrative composite example" in text
    assert text.count("#") <= 5
