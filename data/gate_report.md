# 🛂 Release Gate Report — INSTAGRAM

- **Decision:** 🔴 HELD  (grade **F**, mode strict)
- **Time:** 2026-08-17T16:07:37.209084+00:00

| Guard | Status | Reason |
|---|---|---|
| ✅ script | PASS | 137 words (~65.2s), 6 scenes, anchors+concepts+CTA sab present |
| ⚠️ hook | WARN | no question/number — command-style hook |
| ❌ voice | FAIL | seg 0: speaking rate 3.65 wps (US target 1.6-3.2); seg 5: speaking rate 3.45 wps (US target 1.6-3.2) |
| ✅ caption | PASS | 6 captions, sab voice ke match, zone 1150..1410 safe |
| ✅ video | PASS | 1080x1920 54.9s 30.0fps audio=yes |
| ✅ seo | PASS | [instagram] title/desc/tags/CTAs 2026-rules OK |
| ✅ ctr | PASS | CTR 0.53 >= 0.45 (instagram) |
| ✅ views | PASS | no real data yet (n_real=0) — monitoring mein jayegi, metrics hi is ka fate decide karenge |

## Supervisor (USA audience, fail-closed)

- ℹ️ copy vs youtube: 43% distinct ✓
- ℹ️ copy vs facebook: 53% distinct ✓
- ℹ️ HOLD: 1 guard fail + 0 supervisor violations
- ✅ Independence audit + USA calibration pass

## Evidence

```json
{
  "script": {
    "scenes": 6,
    "words": 137,
    "est_s": 65.2,
    "fluff_hits": [],
    "anchors": [
      "case",
      "transcript",
      "cia"
    ],
    "concepts": [
      "compliance",
      "psycholog"
    ],
    "has_cta": true,
    "hook_link": 1.0,
    "shout": []
  },
  "hook": {
    "hook": "Watch what they say when you say no",
    "words": 8,
    "chars": 35,
    "strong": [
      "watch",
      "what",
      "when"
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
    "total_s": 52.3,
    "measured": [
      {
        "seg": 0,
        "duration_s": 3.84,
        "rms": 4262.4,
        "silence_ratio": 0.195,
        "wps": 3.65,
        "text_words": 14
      },
      {
        "seg": 1,
        "duration_s": 8.128,
        "rms": 3971.6,
        "silence_ratio": 0.172,
        "wps": 2.34,
        "text_words": 18
      },
      {
        "seg": 2,
        "duration_s": 13.504,
        "rms": 3969.8,
        "silence_ratio": 0.181,
        "wps": 2.44,
        "text_words": 33
      },
      {
        "seg": 3,
        "duration_s": 10.24,
        "rms": 4005.1,
        "silence_ratio": 0.21,
        "wps": 2.44,
        "text_words": 25
      },
      {
        "seg": 4,
        "duration_s": 8.491,
        "rms": 3780.0,
        "silence_ratio": 0.176,
        "wps": 2.12,
        "text_words": 18
      },
      {
        "seg": 5,
        "duration_s": 8.107,
        "rms": 4001.6,
        "silence_ratio": 0.16,
        "wps": 3.45,
        "text_words": 29
      }
    ]
  },
  "caption": {
    "scenes": 6,
    "rows": [
      {
        "scene": 0,
        "words": 14,
        "caption_matches_voice": true
      },
      {
        "scene": 1,
        "words": 18,
        "caption_matches_voice": true
      },
      {
        "scene": 2,
        "words": 33,
        "caption_matches_voice": true
      },
      {
        "scene": 3,
        "words": 25,
        "caption_matches_voice": true
      },
      {
        "scene": 4,
        "words": 18,
        "caption_matches_voice": true
      },
      {
        "scene": 5,
        "words": 29,
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
    "size_bytes": 28625380,
    "duration_s": 54.9,
    "width": 1080,
    "height": 1920,
    "fps": 30.0,
    "has_video": true,
    "has_audio": true,
    "video_bitrate": 3971196,
    "codec": "h264",
    "scene_files": 7,
    "avg_scene_s": 7.84
  },
  "seo": {
    "platform": "instagram",
    "title_len": 35,
    "desc_len": 565,
    "hashtags": 20
  },
  "ctr": {
    "score": 0.53,
    "threshold": 0.45,
    "title": "Watch what they say when you say no",
    "hook": "Watch what they say when you say no",
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
    "shared_stems": 6,
    "title_len": 35
  },
  "views": {
    "platform": "instagram",
    "n_real": 0,
    "real_mean": 0.0,
    "arm_key": "stoic_defense::red_flag::afternoon",
    "prior_n": 3,
    "prior_mean": 0.7,
    "recent_credited": 0,
    "zero_view_streak": 0,
    "quarantined": false,
    "metrics_configured": true
  }
}
```
