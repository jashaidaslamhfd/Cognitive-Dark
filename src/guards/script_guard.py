#!/usr/bin/env python3
"""ScriptGuard — RAW script text ka independent quality measurement.

Ye producer ke score_script()/script_quality se bilkul alag hai — apni
khud ki word lists, apne thresholds. Sirf scenes ka text dekhta hai.

Fail conditions (USA audience standard):
  • AI-fluff phrases ("in this video", "welcome back", "let me tell you"...)
  • 4 se kam scenes
  • 90 se kam / 170 se zyada words (45-58s Shorts pacing)
  • koi concrete anchor nahi ($, case, study, trial, transcript...)
  • koi named psychology concept nahi (Milgram, Cialdini, gaslighting...)
  • koi engagement CTA nahi (like/comment/follow/save/share)
  • hook aur scene-1 ka koi link nahi (clickbait gap)
  • ALL-CAPS sentences (shouting = bot pattern)
"""

from __future__ import annotations

import re

from guards.base import BaseGuard

FLUFF = [
    "in this video", "welcome back", "have you ever wondered",
    "it is important to remember", "let me tell you", "hello everyone",
    "today we will", "please subscribe", "don't forget to",
    "smash that like", "without further ado", "delve", "tapestry",
    "in today's video", "hey guys", "so basically", "in conclusion",
    "without a doubt", "let's dive in", "first of all",
]

CONCEPTS = [
    "milgram", "stanford", "cialdini", "cognitive dissonance", "anchoring",
    "gaslighting", "confirmation bias", "foot in the door", "scarcity",
    "mirroring", "love bombing", "conditioning", "persuasion",
    "social proof", "amygdala", "prefrontal", "bystander", "stockholm",
    "compliance", "authority bias", "tribalism", "brainwash", "psycholog",
    "behavioral", "neuroscien", "studies show", "research shows",
    "experiment", "false confession", "statement analysis",
]

ANCHORS = [
    "$", "case", "file", "memo", "study", "experiment", "court", "trial",
    "wire", "transcript", "declassified", "million", "billion", "fbi",
    "cia", "police", "percent", "%", "197", "198", "199", "200", "201",
]
ANCHOR_NUM_RE = re.compile(r"\b\d+\s?(k|people|days|hours|years|times|words|minutes)", re.I)

CTA_WORDS = ("like", "comment", "follow", "save", "share", "subscribe", "hit")

HOOK_LINK_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "of", "to", "in", "on", "for",
    "with", "at", "by", "is", "are", "you", "your", "it", "its", "this",
    "that", "they", "them", "who", "what", "when", "where", "why", "how",
}


def _words(text: str) -> list:
    return re.findall(r"[A-Za-z']+", (text or "").lower())


def _overlap(a: str, b: str) -> float:
    sa = {w for w in _words(a) if w not in HOOK_LINK_STOPWORDS}
    sb = {w for w in _words(b) if w not in HOOK_LINK_STOPWORDS}
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / max(1.0, len(sa))


class ScriptGuard(BaseGuard):
    name = "script"

    def check(self, payload: dict) -> object:
        script = payload.get("script") or {}
        scenes = script.get("scenes") or []
        hook = (script.get("hook") or "").strip()
        full = " ".join(str(s.get("caption", "")) for s in scenes)
        words = _words(full)
        n_words = len(words)

        # fluff scan
        low = full.lower()
        fluff_hits = [f for f in FLUFF if f in low]
        # concrete anchors
        anchor_hits = [a for a in ANCHORS if a in low] \
            + [m for m in ANCHOR_NUM_RE.findall(full)]
        # named psych concepts
        concept_hits = [c for c in CONCEPTS if c in low]
        # engagement CTA
        has_cta = any(w in low for w in CTA_WORDS)
        claim_mode = str(script.get("claim_mode", "")).lower()
        sources = script.get("sources") or []
        factual_without_sources = (
            script.get("source") in {"groq", "gemini"}
            and claim_mode != "fictional_composite"
            and not sources
        )
        # hook ↔ scene-1 link (clickbait gap)
        scene1 = scenes[0].get("caption", "") if scenes else ""
        hook_link = _overlap(hook, scene1)
        # ALL-CAPS shouting
        shout = [s for s in re.findall(r"[A-Z]{6,}", full)
                 if s.lower() not in {"fbi", "cia", "nxivm", "mkultra"}]

        est_s = round(n_words / 2.1, 1)
        evidence = {
            "scenes": len(scenes), "words": n_words, "est_s": est_s,
            "fluff_hits": fluff_hits, "anchors": anchor_hits,
            "concepts": concept_hits, "has_cta": has_cta,
            "claim_mode": claim_mode, "source_count": len(sources),
            "hook_link": round(hook_link, 3), "shout": shout,
        }

        issues, warns = [], []
        if fluff_hits:
            issues.append(f"AI-fluff phrases: {fluff_hits[:3]}")
        if len(scenes) < 4:
            issues.append(f"only {len(scenes)} scenes (need >=4)")
        if n_words < 90:
            issues.append(f"script too short ({n_words} words → ~{est_s}s)")
        elif n_words > 170:
            issues.append(f"script too long ({n_words} words → ~{est_s}s)")
        if not anchor_hits:
            issues.append("no concrete anchor ($/case/study/trial/number)")
        if not concept_hits:
            issues.append("no named psychology concept (Milgram/Cialdini/... )")
        if not has_cta:
            issues.append("no engagement CTA (like/comment/follow/save)")
        if factual_without_sources:
            issues.append("factual LLM script has no source ledger")
        if scenes and hook_link < 0.15:
            issues.append(f"hook has no link to scene 1 (overlap {hook_link:.2f}) — clickbait gap")
        if shout:
            warns.append(f"ALL-CAPS shouting: {shout[:3]}")
        if 90 <= n_words < 110:
            warns.append(f"shorter side ({n_words} words → ~{est_s}s)")

        if issues:
            return self._v("FAIL", "; ".join(issues), evidence,
                           fix="Script regenerate karo — fluff hatana, concrete "
                               "case/$/study add karna, psych concept naam se, "
                               "CTA end mein.")
        if warns:
            return self._v("WARN", "; ".join(warns), evidence)
        return self._v("PASS", f"{n_words} words (~{est_s}s), {len(scenes)} scenes, "
                              f"anchors+concepts+CTA sab present", evidence)
