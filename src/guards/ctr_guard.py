#!/usr/bin/env python3
"""CTRGuard — title/hook ke CTR ka independent measurement.

Producer ke ctr_optimizer.py se alag implementation: apne signals, apne
weights. Ye check karta hai:
  • pehle 3 words power/keyword rakhte hain (mobile feed)
  • number / question / command present
  • title 20-70 chars (FB/IG ke apne caps)
  • title aur hook connected hain (overlap >= 0.25 — bait-and-switch nahi)
  • no ALL-CAPS spam words, no "!!", no emoji flood, no "|" stuffing
  • threshold: YT >= 0.50, FB/IG >= 0.45 (honest scale)
"""

from __future__ import annotations

import re

from guards.base import BaseGuard

POWER = {"stop", "never", "secret", "why", "how", "what", "when", "would",
         "warning", "truth", "danger", "trap", "hidden", "exposed", "signs", "scam", "cult",
         "confess", "escape", "control", "money", "brainwash", "mind",
         "watch", "look", "if"}
KW = ["psychology", "coercion", "cult", "con", "mind", "brainwash", "scam",
      "manipulation", "dark", "behavioral", "truth", "lies", "control",
      "gaslighting", "red flag", "stoic", "interrogation", "lie detection"]
CAPS_SPAM = {"BUG", "TRAP", "FLAG", "EXPOSED", "PROOF", "WARNING", "SHOCKING",
             "OMG", "WOW"}
STOPWORDS = {"the", "a", "an", "and", "or", "but", "of", "to", "in", "on",
             "for", "with", "at", "by", "is", "are", "you", "your", "it",
             "this", "that"}

NUMBER_RE = re.compile(r"\$\s?\d+|\b\d+\b")
QUESTION_RE = re.compile(r"\b(why|how|what|when|would you|do you|can you)\b", re.I)
COMMAND_RE = re.compile(r"\b(stop|never|don'?t|quit|avoid)\b", re.I)

THRESHOLD = {"youtube": 0.50, "facebook": 0.45, "instagram": 0.45}


def _tokens(text: str) -> set:
    return {w for w in re.findall(r"[A-Za-z']+", (text or "").lower())
            if w not in STOPWORDS}


def _stem(w: str) -> str:
    """Word stem (first 4 chars) — 'cult'/'cults', 'scam'/'scams',
    'sign'/'signs' ek hi maane jate hain (V3.6.1). 4-char prefix is liye:
    5-char stem par 'cult'(4) vs 'cults'(5) phir bhi mismatch tha."""
    return w[:4]


def _overlap(a: str, b: str) -> float:
    """Title↔hook connection — STEM-based. Pehle exact-token match tha,
    is liye '3 Signs You're in a Cult' vs 'Why smart people join cults'
    jaisa legit pair 0.0 overlap deta tha aur strong title FAIL hota tha."""
    ta = {_stem(w) for w in _tokens(a)}
    tb = {_stem(w) for w in _tokens(b)}
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(1.0, len(ta))


class CTRGuard(BaseGuard):
    name = "ctr"

    def check(self, payload: dict) -> object:
        platform = payload.get("platform") or "youtube"
        pkg = payload.get("package") or {}
        script = payload.get("script") or {}
        title = (pkg.get("title") or script.get("title") or "").strip()
        hook = (script.get("hook") or "").strip()

        score = 0.25   # honest base
        comp = {}
        issues = []

        words = title.split()
        first3 = " ".join(words[:3]).lower()
        has_power_first3 = any(w in POWER for w in _tokens(first3))
        has_kw = any(k in title.lower() for k in KW)
        has_number = bool(NUMBER_RE.search(title))
        is_question = bool(QUESTION_RE.search(title))
        is_command = bool(COMMAND_RE.search(title))
        caps_spam = [c for c in CAPS_SPAM if re.search(rf"\b{c}\b", title)]
        double_punct = bool(re.search(r"[!?]{2,}", title))
        emoji_count = len(re.findall(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]", title))
        pipe_count = title.count("|")
        link = _overlap(title, hook)
        # shared stems count (1 meaningful shared keyword kaafi hai —
        # bait-and-switch tab hota hai jab ZERO connection ho)
        shared_stems = len({_stem(w) for w in _tokens(title)} &
                           {_stem(w) for w in _tokens(hook)})

        comp.update({"power_first3": has_power_first3, "keyword": has_kw,
                     "number": has_number, "question": is_question,
                     "command": is_command, "hook_link": round(link, 3),
                     "caps_spam": caps_spam, "double_punct": double_punct,
                     "emoji": emoji_count, "pipes": pipe_count,
                     "shared_stems": shared_stems,
                     "title_len": len(title)})

        if has_power_first3:
            score += 0.18
        if has_kw:
            score += 0.15
        if has_number:
            score += 0.12
        if is_question:
            score += 0.10
        if is_command:
            score += 0.10

        if not (20 <= len(title) <= 70):
            issues.append(f"title {len(title)} chars (20-70 optimal)")
        if not has_power_first3 and not has_kw:
            issues.append("first 3 words mein na power word na keyword — "
                          "mobile feed par CTR weak")
        if caps_spam:
            issues.append(f"ALL-CAPS spam: {caps_spam}")
        if double_punct:
            issues.append("double punctuation '!!' — bot pattern")
        if emoji_count > 1:
            issues.append(f"{emoji_count} emojis — spammy")
        if pipe_count > 1:
            issues.append(f"{pipe_count}x '|' stuffing")
        if shared_stems == 0:
            issues.append("title↔hook disconnected (0 shared keywords) — bait-and-switch")

        score = round(min(1.0, max(0.0, score)), 3)
        threshold = THRESHOLD.get(platform, 0.45)
        evidence = {"score": score, "threshold": threshold,
                    "title": title[:60], "hook": hook[:60], **comp}
        if issues:
            return self._v("FAIL", "; ".join(issues), evidence,
                           fix="Title rewrite karo — pehle 3 words mein "
                               "power/keyword, hook se connected.")
        if score < threshold:
            return self._v("FAIL", f"CTR score {score} < {threshold} "
                                   f"({platform} honest threshold)", evidence,
                           fix="High-CTR title variants try karo (number/question/"
                               "command + keyword).")
        return self._v("PASS", f"CTR {score} >= {threshold} ({platform})", evidence)
