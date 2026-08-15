# 🛂 Release Gate Report — INSTAGRAM

- **Decision:** 🟢 RELEASED  (grade **B**, mode strict)
- **Time:** 2026-08-15T16:29:46.750186+00:00

| Guard | Status | Reason |
|---|---|---|
| ✅ script | PASS | 139 words (~66.2s), 6 scenes, anchors+concepts+CTA sab present |
| ⚠️ hook | WARN | no question/number — command-style hook |
| ✅ voice | PASS | 6 segments, 55.3s, all audible, US pace OK |
| ✅ caption | PASS | 6 captions, sab voice ke match, zone 1150..1410 safe |
| ⚠️ video | WARN | avg scene 9.63s > 9.0s (fast cuts missing) |
| ✅ seo | PASS | [instagram] title/desc/tags/CTAs 2026-rules OK |
| ✅ ctr | PASS | CTR 0.68 >= 0.45 (instagram) |
| ✅ views | PASS | no real data yet (n_real=0) — monitoring mein jayegi, metrics hi is ka fate decide karenge |

## Supervisor (USA audience, fail-closed)

- ℹ️ copy vs youtube: 38% distinct ✓
- ℹ️ copy vs facebook: 48% distinct ✓
- ✅ Independence audit + USA calibration pass

## Evidence

```json
{
  "script": {
    "scenes": 6,
    "words": 139,
    "est_s": 66.2,
    "fluff_hits": [],
    "anchors": [
      "$",
      "case",
      "file",
      "wire",
      "transcript"
    ],
    "concepts": [
      "behavioral"
    ],
    "has_cta": true,
    "hook_link": 1.0,
    "shout": []
  },
  "hook": {
    "hook": "Why Victims Wire Money Again and Again",
    "words": 7,
    "chars": 38,
    "strong": [
      "why",
      "money"
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
    "total_s": 55.3,
    "measured": [
      {
        "seg": 0,
        "duration_s": 4.565,
        "rms": 3698.3,
        "silence_ratio": 0.185,
        "wps": 2.85,
        "text_words": 13
      },
      {
        "seg": 1,
        "duration_s": 11.072,
        "rms": 3570.3,
        "silence_ratio": 0.122,
        "wps": 1.72,
        "text_words": 22
      },
      {
        "seg": 2,
        "duration_s": 8.832,
        "rms": 3674.6,
        "silence_ratio": 0.107,
        "wps": 2.38,
        "text_words": 21
      },
      {
        "seg": 3,
        "duration_s": 11.115,
        "rms": 3589.1,
        "silence_ratio": 0.184,
        "wps": 2.79,
        "text_words": 31
      },
      {
        "seg": 4,
        "duration_s": 8.512,
        "rms": 3557.9,
        "silence_ratio": 0.14,
        "wps": 2.7,
        "text_words": 22
      },
      {
        "seg": 5,
        "duration_s": 11.179,
        "rms": 3446.0,
        "silence_ratio": 0.179,
        "wps": 2.86,
        "text_words": 34
      }
    ]
  },
  "caption": {
    "scenes": 6,
    "rows": [
      {
        "scene": 0,
        "words": 13,
        "caption_matches_voice": true
      },
      {
        "scene": 1,
        "words": 22,
        "caption_matches_voice": true
      },
      {
        "scene": 2,
        "words": 21,
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
        "words": 34,
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
    "size_bytes": 30186808,
    "duration_s": 57.8,
    "width": 1080,
    "height": 1920,
    "fps": 30.0,
    "has_video": true,
    "has_audio": true,
    "video_bitrate": 3976577,
    "codec": "h264",
    "scene_files": 6,
    "avg_scene_s": 9.63
  },
  "seo": {
    "platform": "instagram",
    "title_len": 54,
    "desc_len": 568,
    "hashtags": 20
  },
  "ctr": {
    "score": 0.68,
    "threshold": 0.45,
    "title": "The Truth About Why Victims Wire Money Again and Again",
    "hook": "Why Victims Wire Money Again and Again",
    "power_first3": true,
    "keyword": true,
    "number": false,
    "question": true,
    "command": false,
    "hook_link": 0.714,
    "caps_spam": [],
    "double_punct": false,
    "emoji": 0,
    "pipes": 0,
    "shared_stems": 5,
    "title_len": 54
  },
  "views": {
    "platform": "instagram",
    "n_real": 0,
    "real_mean": 0.0,
    "arm_key": "con_artists::warning::afternoon",
    "prior_n": 7,
    "prior_mean": 1.5,
    "recent_credited": 0,
    "zero_view_streak": 0,
    "quarantined": false,
    "metrics_configured": true
  }
}
```
