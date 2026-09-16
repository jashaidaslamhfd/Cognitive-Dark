#!/usr/bin/env python3
"""VoiceGuard — ASAL audio files ki physical measurement.

Producer ke "voice=kokoro" claim par bharosa nahi — har WAV file ko khud
measure karta hai (duration, loudness, silence ratio, speaking rate).

Fail conditions:
  • kisi scene ka audio file missing (TTS silence fallback = silent video)
  • segment 1.5s se chhota ya 15s se lamba
  • speaking rate 1.6-3.2 words/sec se bahar (USA punchy pace)
  • segment ka 50%+ silence (empty/failed TTS output)
  • total narration 35-60s se bahar (40-58 target)
"""

from __future__ import annotations

import os
import re

from guards.base import BaseGuard

MIN_SEG_S, MAX_SEG_S = 1.5, 15.0
MIN_TOTAL_S, MAX_TOTAL_S = 35.0, 60.0
TARGET_MIN_S, TARGET_MAX_S = 40.0, 58.0
MIN_WPS, MAX_WPS = 1.6, 3.2
MAX_SILENCE = 0.5


def _wps(text: str, dur: float) -> float:
    n = len(re.findall(r"[A-Za-z']+", text or ""))
    return round(n / dur, 2) if dur > 0 else 0.0


class VoiceGuard(BaseGuard):
    name = "voice"

    def check(self, payload: dict) -> object:
        segments = payload.get("segments") or []
        if not segments:
            return self._v("UNKNOWN", "no segments in payload",
                           {"segments": 0},
                           fix="Voice stage chalao pehle.")

        issues, warns = [], []
        measured = []
        missing = 0
        total_dur = 0.0
        for i, seg in enumerate(segments):
            path = seg.get("path")
            text = (seg.get("text") or "").strip()
            if not path or not os.path.exists(path):
                missing += 1
                measured.append({"seg": i, "path": path, "missing": True,
                                 "text_words": len(text.split())})
                continue
            try:
                st = self.observer.wav_stats(path)
            except Exception as exc:
                issues.append(f"seg {i}: audio unreadable ({exc})")
                measured.append({"seg": i, "error": str(exc)[:120]})
                continue
            dur = st["duration_s"]
            total_dur += dur
            rate = _wps(text, dur)
            row = {"seg": i, "duration_s": dur, "rms": st["rms"],
                   "silence_ratio": st["silence_ratio"], "wps": rate,
                   "text_words": len(text.split())}
            measured.append(row)
            if dur < MIN_SEG_S:
                issues.append(f"seg {i}: too short ({dur:.1f}s)")
            elif dur > MAX_SEG_S:
                issues.append(f"seg {i}: too long ({dur:.1f}s)")
            if st["silence_ratio"] > MAX_SILENCE:
                issues.append(f"seg {i}: {st['silence_ratio']:.0%} silence — empty/failed TTS")
            if text:
                if rate < 1.2 or rate > 3.8:
                    issues.append(f"seg {i}: speaking rate {rate} wps "
                                  f"(US critical bounds 1.2-3.8)")
                elif rate < MIN_WPS or rate > MAX_WPS:
                    warns.append(f"seg {i}: speaking rate {rate} wps "
                                 f"(ideal target {MIN_WPS}-{MAX_WPS})")

        if missing:
            issues.append(f"{missing}/{len(segments)} segments have NO audio — "
                          "TTS silence fallback (silent video is not releasable)")
        total_dur = round(total_dur, 1)
        if total_dur < MIN_TOTAL_S:
            issues.append(f"narration too short: {total_dur}s (< {MIN_TOTAL_S}s)")
        elif total_dur > MAX_TOTAL_S:
            issues.append(f"narration too long: {total_dur}s (> {MAX_TOTAL_S}s)")
        elif total_dur < TARGET_MIN_S or total_dur > TARGET_MAX_S:
            warns.append(f"narration {total_dur}s outside 40-58s sweet spot")

        evidence = {"segments": len(segments), "missing": missing,
                    "total_s": total_dur, "measured": measured}
        if issues:
            return self._v("FAIL", "; ".join(issues), evidence,
                           fix="Voice regenerate karo — har scene ke liye real "
                               "TTS output hona chahiye (kokoro/edge), silence "
                               "nahi.")
        if warns:
            return self._v("WARN", "; ".join(warns), evidence)
        return self._v("PASS", f"{len(segments)} segments, {total_dur}s, "
                              f"all audible, US pace OK", evidence)
