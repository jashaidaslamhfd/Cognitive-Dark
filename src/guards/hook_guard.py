#!/usr/bin/env python3
"""HookGuard — 2-second overlay hook ka independent reality check.

Producer ke score_hook() se alag: apni strong-words list, apne rules.
Hook ke liye fail conditions (USA Shorts standard):
  • 3 se kam ya 9 se zyada words
  • 85 chars se lamba (overlay readable nahi)
  • weak opener ("welcome", "hello", "in this", "let me"...)
  • dangling fragment ("Stop letting them", "Nobody tells you")
  • cliché ("you won't believe", "mind blowing"...)
  • na strong word, na pattern-interrupt (question/imperative/number/$)
"""

from __future__ import annotations

import re

from guards.base import BaseGuard

STRONG = {
    "stop", "never", "secret", "why", "how", "warning", "truth", "danger",
    "lies", "trick", "trap", "hidden", "exposed", "nobody", "signs",
    "before", "what", "if", "when", "watch", "instantly", "confess",
    "escape", "banned", "refused", "control", "money", "scam", "cult",
    "stole", "wired", "obeyed", "mind", "brainwash",
}
WEAK_OPENERS = ["welcome", "hello", "hey", "hi ", "let me", "in this",
                "today", "have you", "so ", "basically", "um ", "okay",
                "guys", "everyone"]
DANGLERS = {"them", "they", "it", "this", "that", "you", "to", "at", "in",
            "of", "with", "when", "if", "and", "or", "up", "out", "on",
            "for", "from", "into", "your", "their", "about", "people"}
CLICHES = ["mind blowing", "shocking truth", "you won't believe",
           "wait for it", "blow your mind", "changed my life",
           "number one", "life hack", "game changer"]
INTERRUPT_RE = re.compile(r"\b(why|how|stop|never|don'?t|watch|look|what|if)\b", re.I)
NUMBER_RE = re.compile(r"\$\s?\d+|\b\d+\b")
QUESTION_END = re.compile(r"\?\s*$")


class HookGuard(BaseGuard):
    name = "hook"

    def check(self, payload: dict) -> object:
        script = payload.get("script") or {}
        hook = (script.get("hook") or "").strip()
        if not hook:
            return self._v("FAIL", "hook empty", {"hook": ""},
                           fix="Hook required — 3-9 words, pattern-interrupt.")

        words = re.findall(r"[A-Za-z']+", hook.lower())
        n_words = len(words)
        strong_hits = [w for w in words if w in STRONG]
        cliche_hits = [c for c in CLICHES if c in hook.lower()]
        opener = hook.lower().split()
        weak_open = opener and any(
            hook.lower().lstrip().startswith(w) for w in WEAK_OPENERS)
        is_question = bool(QUESTION_END.search(hook))
        interrupt = bool(INTERRUPT_RE.search(hook)) or bool(NUMBER_RE.search(hook))
        dangling = (n_words <= 3 and words
                    and words[-1] in DANGLERS)
        n_anchors = len(NUMBER_RE.findall(hook))

        evidence = {
            "hook": hook, "words": n_words, "chars": len(hook),
            "strong": strong_hits, "cliche": cliche_hits,
            "question": is_question, "interrupt": interrupt,
            "numbers": n_anchors, "weak_opener": weak_open,
            "dangling": dangling,
        }

        issues = []
        warns = []
        if n_words < 3:
            issues.append(f"too short ({n_words} words) — no payoff")
        elif n_words > 12:
            issues.append(f"too long ({n_words} words) — 2s overlay cap")
        elif n_words > 8:
            warns.append(f"{n_words} words — slightly long for 2s overlay")
        if len(hook) > 85:
            issues.append(f"{len(hook)} chars — overlay cap 85")
        if weak_open:
            issues.append("weak opener — 'welcome/in this/let me' = swipe-away")
        if dangling:
            issues.append(f"incomplete hook (fragment) — '{hook}' ka payoff do")
        if cliche_hits:
            issues.append(f"cliché: {cliche_hits}")
        if not strong_hits and not interrupt:
            issues.append("no strong word AND no pattern-interrupt "
                          "(question/imperative/number/$ chahiye)")

        if issues:
            return self._v("FAIL", "; ".join(issues), evidence,
                           fix="Hook rewrite karo: 4-8 words, command/question/"
                               "number se shuru, concrete payoff.")
        warns = []
        if n_words in (3,):
            warns.append("3-word hook — minimum hai, payoff tight hai")
        if not is_question and not n_anchors:
            warns.append("no question/number — command-style hook")
        if warns:
            return self._v("WARN", "; ".join(warns), evidence)
        return self._v("PASS", f"{n_words} words, interrupt={'yes' if interrupt else 'no'}, "
                              f"strong={strong_hits}", evidence)
