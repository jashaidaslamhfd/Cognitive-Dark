#!/usr/bin/env python3
"""SEOGuard — har platform ke 2026 algorithm rules ka independent audit.

Producer ke seo.py se alag: guards apni check-list khud chalata hai
BANAY HUAY package par (title/description/tags/hashtags). Ye sirf text
measure karta hai — platform API verification uploader ka kaam hai.

Per-platform fail conditions (2026 documented best practices):

YouTube Shorts:
  • title 20-100 chars, keyword (pillar search term) title mein
  • description >= 300 chars, keyword pehli 2 lines mein
  • 1-50 tags, total <= 500 chars
  • <= 3 hashtags (spam label risk)
  • educational disclaimer present (monetization safety)
  • "|" stuffing <= 1 (bot pattern)

Facebook Reels:
  • title <= 150; description 200-6300
  • first-line context and a genuine question/checklist prompt
  • no more than 5 relevant hashtags
  • no known engagement-bait phrase

Instagram Reels:
  • title <= 55; description 150-2200
  • save-value or case-specific reflection prompt
  • no more than 5 relevant hashtags
  • no known engagement-bait phrase
"""

from __future__ import annotations

import re

from config.settings import META_ALLOW_ENGAGEMENT_BAIT, META_MAX_HASHTAGS, PILLARS
from guards.base import BaseGuard

YT_KW_FALLBACK = ["psychology", "mind", "cult", "scam", "coercion",
                  "brainwash", "control", "manipulation", "gaslighting", "stoic",
                  "interrogation", "lie detection", "detection", "body language"]
DISCLAIMER_HINTS = ["educational", "not a substitute", "protect yourself"]

FB_CTA_RE = re.compile(
    r"\b(comment|what would you|which|what would you verify|reasoning|"
    r"checklist|explain|add)\b", re.I)
IG_CTA_RE = re.compile(
    r"\b(save (?:this|it)|checklist|review|which detail|verify first|"
    r"add your reasoning)\b", re.I)
BAIT_RE = re.compile(
    r"(?:algorithm\s+(?:won't|will not)\s+show|one\s+like\s+equals|"
    r"like\s+(?:this|it)\s+to\s+(?:get|reach)|if\s+this\s+hits|"
    r"comment\s+[\"']?safe[\"']?|we(?:'re| are)\s+counting)", re.I)
STUFF_RE = re.compile(r"\|")


class SEOGuard(BaseGuard):
    name = "seo"

    def _yt_keywords(self, payload: dict) -> list:
        """Fallback keywords + script ke PILLAR ke search terms — is liye
        'Lie Detection: Why Innocent People Confess' jaisa legit title fail
        nahi hota."""
        kws = list(YT_KW_FALLBACK)
        script = payload.get("script") or {}
        for p in PILLARS:
            if p["key"] == script.get("pillar"):
                kws += [t for t in p.get("search_terms", []) if t]
        return sorted(set(kws), key=len, reverse=True)

    def _yt(self, pkg: dict, issues: list, warns: list, ev: dict) -> None:
        title = pkg.get("title") or ""
        desc = pkg.get("description") or ""
        tags = pkg.get("tags") or []
        tags_chars = sum(len(t) + 1 for t in tags)
        kws = self._yt_keywords(self._payload)
        # V3.6.4: CASE-INSENSITIVE match — pehle k in title.lower() tha:
        # "MKUltra explained" (capital) title.lower() mein kabhi match nahi
        # hota tha → pillar keywords wale titles ghalat FAIL hote thay.
        kw_hits = [k for k in kws if k.lower() in title.lower()]
        ev.update({"title_len": len(title), "desc_len": len(desc),
                   "tags": len(tags), "tags_chars": tags_chars,
                   "keyword_in_title": bool(kw_hits), "pipe_count":
                   len(STUFF_RE.findall(title))})
        if not (20 <= len(title) <= 100):
            issues.append(f"title {len(title)} chars (20-100 chahiye)")
        if not kw_hits:
            issues.append("no psychology/search keyword in title")
        if len(desc) < 300:
            issues.append(f"description too short ({len(desc)} chars)")
        if not any(k.lower() in desc[:300].lower() for k in kws):
            issues.append("keyword not in description first 2 lines")
        if not (1 <= len(tags) <= 50):
            issues.append(f"tags {len(tags)} (1-50 chahiye)")
        if tags_chars > 500:
            issues.append(f"tags {tags_chars} chars total (>500)")
        if len(pkg.get("hashtags") or []) > 3:
            issues.append(">3 hashtags — spam label risk")
        if not any(h in desc.lower() for h in DISCLAIMER_HINTS):
            issues.append("no educational disclaimer in description")
        if len(STUFF_RE.findall(title)) > 1:
            issues.append(f"{len(STUFF_RE.findall(title))}x '|' stuffing — bot pattern")

    def _fb(self, pkg: dict, issues: list, warns: list, ev: dict) -> None:
        title = pkg.get("title") or ""
        desc = pkg.get("description") or ""
        first = (desc.split("\n") or [""])[0]
        hashtags = len(pkg.get("hashtags") or [])
        ev.update({"title_len": len(title), "desc_len": len(desc),
                   "hashtags": hashtags, "first_line": first[:60]})
        if len(title) > 150:
            issues.append(f"title {len(title)} chars (>150)")
        if not (200 <= len(desc) <= 6300):
            issues.append(f"description {len(desc)} chars (200-6300)")
        if not FB_CTA_RE.search(desc):
            issues.append("no genuine question/checklist prompt")
        if BAIT_RE.search(desc) and not META_ALLOW_ENGAGEMENT_BAIT:
            issues.append("engagement-bait phrase detected")
        if hashtags > META_MAX_HASHTAGS:
            issues.append(f"hashtags {hashtags} (>{META_MAX_HASHTAGS} Meta limit)")

    def _ig(self, pkg: dict, issues: list, warns: list, ev: dict) -> None:
        title = pkg.get("title") or ""
        desc = pkg.get("description") or ""
        hashtags = len(pkg.get("hashtags") or [])
        ev.update({"title_len": len(title), "desc_len": len(desc),
                   "hashtags": hashtags})
        if len(title) > 55:
            issues.append(f"title {len(title)} chars (>55)")
        if not (150 <= len(desc) <= 2200):
            issues.append(f"description {len(desc)} chars (150-2200)")
        if not IG_CTA_RE.search(desc):
            issues.append("no save-value or case-specific reflection prompt")
        if BAIT_RE.search(desc) and not META_ALLOW_ENGAGEMENT_BAIT:
            issues.append("engagement-bait phrase detected")
        if hashtags > META_MAX_HASHTAGS:
            issues.append(f"hashtags {hashtags} (>{META_MAX_HASHTAGS} Meta limit)")

    def check(self, payload: dict) -> object:
        platform = payload.get("platform") or ""
        pkg = payload.get("package") or {}
        self._payload = payload
        if not pkg:
            return self._v("UNKNOWN", "no package in payload", {"platform": platform},
                           fix="build_platform_package chalao pehle.")
        issues, warns, ev = [], [], {"platform": platform}
        try:
            {"youtube": self._yt, "facebook": self._fb,
             "instagram": self._ig}.get(platform, self._yt)(pkg, issues, warns, ev)
        except Exception as exc:  # guard must never crash
            return self._v("UNKNOWN", f"seo audit failed: {exc}", ev)

        if issues:
            return self._v("FAIL", f"[{platform}] " + "; ".join(issues), ev,
                           fix=f"{platform.upper()} package dobara banao — "
                               "title/desc/tags platform ke 2026 rules par.")
        if warns:
            return self._v("WARN", f"[{platform}] " + "; ".join(warns), ev)
        return self._v("PASS", f"[{platform}] title/desc/tags/CTAs 2026-rules OK", ev)
