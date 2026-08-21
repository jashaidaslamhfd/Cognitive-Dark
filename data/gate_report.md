# 🛂 Release Gate Report — INSTAGRAM

- **Decision:** 🟢 RELEASED  (grade **B**, mode strict)
- **Time:** 2026-08-21T04:29:30.337759+00:00

| Guard | Status | Reason |
|---|---|---|
| ✅ script | PASS | 130 words (~61.9s), 6 scenes, anchors+concepts+CTA sab present |
| ⚠️ hook | WARN | no question/number — command-style hook |
| ✅ voice | PASS | 6 segments, 49.8s, all audible, US pace OK |
| ✅ caption | PASS | 6 captions, sab voice ke match, zone 1150..1410 safe |
| ✅ video | PASS | 1080x1920 52.4s 30.0fps audio=yes |
| ✅ seo | PASS | [instagram] title/desc/tags/CTAs 2026-rules OK |
| ✅ ctr | PASS | CTR 0.53 >= 0.45 (instagram) |
| ✅ views | PASS | no real data yet (n_real=0) — monitoring mein jayegi, metrics hi is ka fate decide karenge |

## Supervisor (USA audience, fail-closed)

- ℹ️ copy vs youtube: 42% distinct ✓
- ℹ️ copy vs facebook: 48% distinct ✓
- ✅ Independence audit + USA calibration pass

## Evidence

```json
{
  "script": {
    "scenes": 6,
    "words": 130,
    "est_s": 61.9,
    "fluff_hits": [],
    "anchors": [
      "case",
      "transcript",
      "declassified"
    ],
    "concepts": [
      "confirmation bias",
      "scarcity",
      "behavioral"
    ],
    "has_cta": true,
    "hook_link": 1.0,
    "shout": []
  },
  "hook": {
    "hook": "How One Ad Manipulated a Country",
    "words": 6,
    "chars": 32,
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
    "total_s": 49.8,
    "measured": [
      {
        "seg": 0,
        "duration_s": 4.053,
        "rms": 4111.8,
        "silence_ratio": 0.22,
        "wps": 2.96,
        "text_words": 12
      },
      {
        "seg": 1,
        "duration_s": 9.493,
        "rms": 3917.1,
        "silence_ratio": 0.184,
        "wps": 2.11,
        "text_words": 20
      },
      {
        "seg": 2,
        "duration_s": 9.301,
        "rms": 3910.9,
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
        "rms": 4007.7,
        "silence_ratio": 0.184,
        "wps": 2.83,
        "text_words": 22
      },
      {
        "seg": 5,
        "duration_s": 8.32,
        "rms": 4047.0,
        "silence_ratio": 0.198,
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
        "words": 12,
        "caption_matches_voice": true
      },
      {
        "scene": 1,
        "words": 20,
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
    "size_bytes": 27623548,
    "duration_s": 52.4,
    "width": 1080,
    "height": 1920,
    "fps": 30.0,
    "has_video": true,
    "has_audio": true,
    "video_bitrate": 4017235,
    "codec": "h264",
    "scene_files": 6,
    "avg_scene_s": 8.73
  },
  "seo": {
    "platform": "instagram",
    "title_len": 32,
    "desc_len": 555,
    "hashtags": 20
  },
  "ctr": {
    "score": 0.53,
    "threshold": 0.45,
    "title": "How One Ad Manipulated a Country",
    "hook": "How One Ad Manipulated a Country",
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
    "shared_stems": 5,
    "title_len": 32
  },
  "views": {
    "platform": "instagram",
    "n_real": 0,
    "real_mean": 0.0,
    "arm_key": "mind_control_history::warning::morning",
    "prior_n": 3,
    "prior_mean": 0.85,
    "recent_credited": 0,
    "zero_view_streak": 0,
    "quarantined": false,
    "metrics_configured": true
  }
}
```
