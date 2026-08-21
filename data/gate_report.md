# 🛂 Release Gate Report — INSTAGRAM

- **Decision:** 🔴 HELD  (grade **F**, mode strict)
- **Time:** 2026-08-21T16:03:27.031737+00:00

| Guard | Status | Reason |
|---|---|---|
| ✅ script | PASS | 126 words (~60.0s), 6 scenes, anchors+concepts+CTA sab present |
| ⚠️ hook | WARN | no question/number — command-style hook |
| ✅ voice | PASS | 6 segments, 48.7s, all audible, US pace OK |
| ✅ caption | PASS | 6 captions, sab voice ke match, zone 1150..1410 safe |
| ✅ video | PASS | 1080x1920 51.3s 30.0fps audio=yes |
| ✅ seo | PASS | [instagram] title/desc/tags/CTAs 2026-rules OK |
| ❌ ctr | FAIL | first 3 words mein na power word na keyword — mobile feed par CTR weak |
| ✅ views | PASS | no real data yet (n_real=0) — monitoring mein jayegi, metrics hi is ka fate decide karenge |

## Supervisor (USA audience, fail-closed)

- ℹ️ copy vs youtube: 40% distinct ✓
- ℹ️ copy vs facebook: 43% distinct ✓
- ℹ️ HOLD: 1 guard fail + 0 supervisor violations
- ✅ Independence audit + USA calibration pass

## Evidence

```json
{
  "script": {
    "scenes": 6,
    "words": 126,
    "est_s": 60.0,
    "fluff_hits": [],
    "anchors": [
      "case",
      "transcript"
    ],
    "concepts": [
      "confirmation bias",
      "scarcity",
      "statement analysis"
    ],
    "has_cta": true,
    "hook_link": 1.0,
    "shout": []
  },
  "hook": {
    "hook": "How Detectives Read Baseline Behavior",
    "words": 5,
    "chars": 37,
    "strong": [
      "how"
    ],
    "cliche": [],
    "question": false,
    "interrupt": true,
    "numbers": 0,
    "weak_opener": false,
    "dangling": false
  },
  "voice": {
    "segments": 6,
    "missing": 0,
    "total_s": 48.7,
    "measured": [
      {
        "seg": 0,
        "duration_s": 4.352,
        "rms": 4122.4,
        "silence_ratio": 0.205,
        "wps": 2.53,
        "text_words": 11
      },
      {
        "seg": 1,
        "duration_s": 8.085,
        "rms": 3847.6,
        "silence_ratio": 0.167,
        "wps": 2.1,
        "text_words": 17
      },
      {
        "seg": 2,
        "duration_s": 9.301,
        "rms": 3912.9,
        "silence_ratio": 0.15,
        "wps": 2.37,
        "text_words": 22
      },
      {
        "seg": 3,
        "duration_s": 10.539,
        "rms": 4021.1,
        "silence_ratio": 0.175,
        "wps": 2.94,
        "text_words": 31
      },
      {
        "seg": 4,
        "duration_s": 8.128,
        "rms": 4006.5,
        "silence_ratio": 0.184,
        "wps": 2.83,
        "text_words": 22
      },
      {
        "seg": 5,
        "duration_s": 8.32,
        "rms": 4045.7,
        "silence_ratio": 0.192,
        "wps": 2.64,
        "text_words": 23
      }
    ]
  },
  "caption": {
    "scenes": 6,
    "rows": [
      {
        "scene": 0,
        "words": 11,
        "caption_matches_voice": true
      },
      {
        "scene": 1,
        "words": 17,
        "caption_matches_voice": true
      },
      {
        "scene": 2,
        "words": 22,
        "caption_matches_voice": true
      },
      {
        "scene": 3,
        "words": 31,
        "caption_matches_voice": true
      },
      {
        "scene": 4,
        "words": 22,
        "caption_matches_voice": true
      },
      {
        "scene": 5,
        "words": 23,
        "caption_matches_voice": true
      }
    ],
    "chunk_png_missing": 0,
    "caption_zone": "1150..1410",
    "words_per_chunk": 2
  },
  "video": {
    "path": "/home/runner/work/Cognitive-Dark/Cognitive-Dark/output/final_video.mp4",
    "exists": true,
    "size_bytes": 27106229,
    "duration_s": 51.3,
    "width": 1080,
    "height": 1920,
    "fps": 30.0,
    "has_video": true,
    "has_audio": true,
    "video_bitrate": 4027424,
    "codec": "h264",
    "scene_files": 6,
    "avg_scene_s": 8.55
  },
  "seo": {
    "platform": "instagram",
    "title_len": 55,
    "desc_len": 567,
    "hashtags": 20
  },
  "ctr": {
    "score": 0.35,
    "threshold": 0.45,
    "title": "What Nobody Tells You About How Detectives Read Baselin",
    "hook": "How Detectives Read Baseline Behavior",
    "power_first3": false,
    "keyword": false,
    "number": false,
    "question": true,
    "command": false,
    "hook_link": 0.5,
    "caps_spam": [],
    "double_punct": false,
    "emoji": 0,
    "pipes": 0,
    "shared_stems": 4,
    "title_len": 55
  },
  "views": {
    "platform": "instagram",
    "n_real": 0,
    "real_mean": 0.0,
    "arm_key": "interrogation::warning::afternoon",
    "prior_n": 5,
    "prior_mean": 1.25,
    "recent_credited": 0,
    "zero_view_streak": 0,
    "quarantined": false,
    "metrics_configured": true
  }
}
```
