# 🛂 Release Gate Report — INSTAGRAM

- **Decision:** 🔴 HELD  (grade **F**, mode strict)
- **Time:** 2026-08-22T04:15:42.877105+00:00

| Guard | Status | Reason |
|---|---|---|
| ✅ script | PASS | 116 words (~55.2s), 6 scenes, anchors+concepts+CTA sab present |
| ❌ hook | FAIL | too long (10 words) — 2s overlay cap |
| ❌ voice | FAIL | seg 0: speaking rate 3.81 wps (US target 1.6-3.2); seg 5: speaking rate 3.54 wps (US target 1.6-3.2) |
| ✅ caption | PASS | 6 captions, sab voice ke match, zone 1150..1410 safe |
| ✅ video | PASS | 1080x1920 46.7s 30.0fps audio=yes |
| ✅ seo | PASS | [instagram] title/desc/tags/CTAs 2026-rules OK |
| ✅ ctr | PASS | CTR 0.53 >= 0.45 (instagram) |
| ✅ views | PASS | no real data yet (n_real=0) — monitoring mein jayegi, metrics hi is ka fate decide karenge |

## Supervisor (USA audience, fail-closed)

- ℹ️ copy vs youtube: 43% distinct ✓
- ℹ️ copy vs facebook: 63% distinct ✓
- ℹ️ HOLD: 2 guard fail + 0 supervisor violations
- ✅ Independence audit + USA calibration pass

## Evidence

```json
{
  "script": {
    "scenes": 6,
    "words": 116,
    "est_s": 55.2,
    "fluff_hits": [],
    "anchors": [
      "case",
      "file",
      "wire",
      "transcript"
    ],
    "concepts": [
      "amygdala",
      "prefrontal"
    ],
    "has_cta": true,
    "hook_link": 1.0,
    "shout": []
  },
  "hook": {
    "hook": "How they get you to say yes before you think",
    "words": 10,
    "chars": 44,
    "strong": [
      "how",
      "before"
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
    "total_s": 44.1,
    "measured": [
      {
        "seg": 0,
        "duration_s": 4.203,
        "rms": 4244.4,
        "silence_ratio": 0.235,
        "wps": 3.81,
        "text_words": 16
      },
      {
        "seg": 1,
        "duration_s": 7.317,
        "rms": 3982.5,
        "silence_ratio": 0.17,
        "wps": 2.46,
        "text_words": 18
      },
      {
        "seg": 2,
        "duration_s": 8.64,
        "rms": 3846.9,
        "silence_ratio": 0.121,
        "wps": 2.08,
        "text_words": 17
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
        "duration_s": 8.896,
        "rms": 3958.8,
        "silence_ratio": 0.202,
        "wps": 1.91,
        "text_words": 17
      },
      {
        "seg": 5,
        "duration_s": 4.523,
        "rms": 4126.6,
        "silence_ratio": 0.198,
        "wps": 3.54,
        "text_words": 16
      }
    ]
  },
  "caption": {
    "scenes": 6,
    "rows": [
      {
        "scene": 0,
        "words": 16,
        "caption_matches_voice": true
      },
      {
        "scene": 1,
        "words": 18,
        "caption_matches_voice": true
      },
      {
        "scene": 2,
        "words": 17,
        "caption_matches_voice": true
      },
      {
        "scene": 3,
        "words": 31,
        "caption_matches_voice": true
      },
      {
        "scene": 4,
        "words": 17,
        "caption_matches_voice": true
      },
      {
        "scene": 5,
        "words": 16,
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
    "size_bytes": 24482578,
    "duration_s": 46.7,
    "width": 1080,
    "height": 1920,
    "fps": 30.0,
    "has_video": true,
    "has_audio": true,
    "video_bitrate": 3995555,
    "codec": "h264",
    "scene_files": 6,
    "avg_scene_s": 7.78
  },
  "seo": {
    "platform": "instagram",
    "title_len": 44,
    "desc_len": 398,
    "hashtags": 5
  },
  "ctr": {
    "score": 0.53,
    "threshold": 0.45,
    "title": "How they get you to say yes before you think",
    "hook": "How they get you to say yes before you think",
    "power_first3": true,
    "keyword": false,
    "number": false,
    "question": true,
    "command": false,
    "hook_link": 1.0,
    "caps_spam": [],
    "double_punct": false,
    "emoji": 0,
    "pipes": 0,
    "shared_stems": 7,
    "title_len": 44
  },
  "views": {
    "platform": "instagram",
    "n_real": 0,
    "real_mean": 0.0,
    "arm_key": "con_artists::warning::morning",
    "prior_n": 7,
    "prior_mean": 1.5,
    "recent_credited": 0,
    "zero_view_streak": 0,
    "quarantined": false,
    "metrics_configured": true
  }
}
```
