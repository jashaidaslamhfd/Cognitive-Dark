# 🛂 Release Gate Report — YOUTUBE

- **Decision:** 🔴 HELD  (grade **F**, mode strict)
- **Time:** 2026-08-16T20:28:19.044391+00:00

| Guard | Status | Reason |
|---|---|---|
| ❌ script | FAIL | script too short (30 words → ~14.3s) |
| ⚠️ hook | WARN | no question/number — command-style hook |
| ❌ voice | FAIL | 1/1 segments have NO audio — TTS silence fallback (silent video is not releasable); narration too short: 0.0s (< 35.0s) |
| ❌ caption | FAIL | scene 0: caption ≠ voice text (sunai vs dikhai alag) |
| ❌ video | FAIL | duration 5.9s < 35.0s |
| ❌ seo | FAIL | [youtube] description too short (74 chars) |
| ✅ ctr | PASS | CTR 0.68 >= 0.5 (youtube) |
| ⚠️ views | WARN | metrics pipeline (fetch_metrics) ke liye koi token configured nahi — rewards ka source band hai |

## Supervisor (USA audience, fail-closed)

- ℹ️ HOLD: 5 guard fail + 0 supervisor violations
- ✅ Independence audit + USA calibration pass

## Evidence

```json
{
  "script": {
    "scenes": 5,
    "words": 30,
    "est_s": 14.3,
    "fluff_hits": [],
    "anchors": [
      "$",
      "wire",
      "cia",
      "k",
      "days"
    ],
    "concepts": [
      "milgram",
      "cialdini",
      "scarcity"
    ],
    "has_cta": true,
    "hook_link": 1.0,
    "shout": []
  },
  "hook": {
    "hook": "Why smart people join cults",
    "words": 5,
    "chars": 27,
    "strong": [
      "why"
    ],
    "cliche": [],
    "question": false,
    "interrupt": true,
    "numbers": 0,
    "weak_opener": false,
    "dangling": false
  },
  "voice": {
    "segments": 1,
    "missing": 1,
    "total_s": 0.0,
    "measured": [
      {
        "seg": 0,
        "path": null,
        "missing": true,
        "text_words": 1
      }
    ]
  },
  "caption": {
    "scenes": 5,
    "rows": [
      {
        "scene": 0,
        "words": 5,
        "caption_matches_voice": false
      },
      {
        "scene": 1,
        "words": 8,
        "caption_matches_voice": null
      },
      {
        "scene": 2,
        "words": 5,
        "caption_matches_voice": null
      },
      {
        "scene": 3,
        "words": 5,
        "caption_matches_voice": null
      },
      {
        "scene": 4,
        "words": 8,
        "caption_matches_voice": null
      }
    ],
    "chunk_png_missing": 3,
    "caption_zone": "1150..1410",
    "words_per_chunk": 2
  },
  "video": {
    "path": "output/tmp/selftest_video.mp4",
    "exists": true,
    "size_bytes": 2066855,
    "duration_s": 5.9,
    "width": 1080,
    "height": 1920,
    "fps": 30.0,
    "has_video": true,
    "has_audio": true,
    "video_bitrate": 2647846,
    "codec": "h264",
    "scene_files": 2,
    "avg_scene_s": 2.95
  },
  "seo": {
    "platform": "youtube",
    "title_len": 27,
    "desc_len": 74,
    "tags": 1,
    "tags_chars": 11,
    "keyword_in_title": true,
    "pipe_count": 0
  },
  "ctr": {
    "score": 0.68,
    "threshold": 0.5,
    "title": "Why Smart People Join Cults",
    "hook": "Why smart people join cults",
    "power_first3": true,
    "keyword": true,
    "number": false,
    "question": true,
    "command": false,
    "hook_link": 1.0,
    "caps_spam": [],
    "double_punct": false,
    "emoji": 0,
    "pipes": 0,
    "shared_stems": 5,
    "title_len": 27
  },
  "views": {
    "platform": "youtube",
    "n_real": 0,
    "real_mean": 0.0,
    "arm_key": "cults::question_hook::morning",
    "recent_credited": 0,
    "zero_view_streak": 0,
    "quarantined": false,
    "metrics_configured": false
  }
}
```
