#!/usr/bin/env python3
"""
Coercion Files — USA-STYLE Platform SEO Packaging.

USA viral-channel conventions applied:
  • TITLES — hook first, KEYWORD in the first 40 chars, power words, Title
    Case, numbers when possible, ≤70 chars for Shorts (best CTR).
  • DESCRIPTIONS — first 2 lines keyword-dense, "What you'll learn" bullets,
    a "chapter" timestamp block, hashtags, CTA, educational disclaimer.
  • TAGS (YouTube) — broad + specific + branded mix, ≤500 chars total.
  • Platform-native copy — every platform gets distinct text (spam signal if
    identical), tuned to each algorithm (FB = comments, IG = saves/shares).
"""

import logging
import random

from config.settings import META_MAX_HASHTAGS, PILLARS

logger = logging.getLogger("seo")

# V3.4: all-caps spam fragments ("BUG", "TRAP", "FLAG") hata diye — ye titles
# ko bot-like bana dete hain aur CTR girate hain. Sirf natural power words.
POWER_WORDS = ["Secret", "Instantly", "Never", "Shocking", "Hidden", "Exposed",
               "Deadly", "Brutal", "Finally", "Revealed", "Stop", "Warning",
               "Truth", "Nobody Tells You", "They Don't Want You to Know"]

PLATFORM_HASHTAGS = {
    "youtube": ["#psychology", "#truecrime", "#mindcontrol"],
    # Meta currently recommends relevant, low-volume hashtags; keep the
    # default package at five or fewer and select a pillar-specific subset.
    "facebook": ["#psychology", "#scamawareness", "#coercivecontrol",
                 "#behavioralscience", "#selfdefense"],
    "instagram": ["#psychology", "#scamawareness", "#coercivecontrol",
                  "#behavioralscience", "#selfdefense"],
}

CTA_IG = ["Save this checklist for your next high-pressure conversation.",
          "Save this case file so you can review the warning signs later.",
          "Which detail would you verify first? Add your reasoning below."]
CTA_FB = ["What would you verify first in this situation? Explain below.",
          "Which detail changed your view of the case? Let us know.",
          "Which sign was easiest to miss? Share your reasoning below.",
          "What would you add to this practical checklist?"]

EDUCATIONAL_DISCLAIMER = (
    "⚠️ For educational purposes only — learn to recognize and protect yourself. "
    "Not a substitute for professional advice.")

CHAPTER_NAMES = ["The Hook", "What's Really Happening", "The Pattern Nobody Sees",
                 "Why It Works On You", "How To Protect Yourself", "The Takeaway",
                 "Follow For More"]


def _chapters(durations: list) -> str:
    """V2.5: REAL chapter timestamps computed from actual scene durations
    (V2's were static/fake — YouTube penalizes misleading chapters)."""
    if not durations:
        return ""
    lines, t = [], 0.0
    for i, d in enumerate(durations):
        mm, ss = int(t // 60), int(t % 60)
        lines.append(f"{mm:02d}:{ss:02d} {CHAPTER_NAMES[i] if i < len(CHAPTER_NAMES) else 'More'}")
        t += d
    return "⏱ CHAPTERS:\n" + "\n".join(lines)


def _title_case_word(w: str, first: bool, stop: set) -> str:
    # Preserve acronyms (FBI, CIA, MKUltra) — all-caps tokens stay as-is
    if w.isupper() and len(w) >= 2:
        return w
    if first or w.lower() not in stop:
        if "-" in w:  # "30-second" → "30-Second"
            return "-".join(p.capitalize() for p in w.split("-"))
        return w.capitalize()
    return w.lower()


def _power_title(hook: str, max_len: int = 70) -> str:
    """USA-style title: hook-first, Title Case, keyword density, ≤ max_len.

    V3.4: random power-word append ("...: Truth") hata diya — wo double-colon
    titles banata tha ("Hook: Truth: Keyword") jo bot-pattern lagte hain aur
    CTR gira dete hain. Titles ab saaf rehte hain; weak titles ko honest CTR
    scorer pehchaan kar grammatical variants se fix karta hai.
    """
    t = hook.strip()
    # strip trailing punctuation for cleaner titles
    t = t.rstrip("?!.").strip()
    words = t.split()
    stop = {"a", "an", "the", "and", "or", "but", "of", "to", "in", "on", "for",
            "with", "at", "by", "is", "are", "you", "your", "it", "its"}
    tt = " ".join(_title_case_word(w, i == 0, stop) for i, w in enumerate(words))
    return tt[:max_len]


def _platform_ctr_title(hook: str, platform: str, max_len: int) -> str:
    """FB/IG titles bhi CTR-optimized (V3.6.2): pehle raw hook jata tha —
    pehle 3 words mein na power na keyword → CTRGuard FAIL. Ab weak hook ka
    best grammatical variant select hota hai; strong hook untouched."""
    try:
        from ctr_optimizer import pick_best_title, score_title_ctr, suggest_ctr_improved_title
        base = hook[:max_len]
        if score_title_ctr(base, platform).score >= 0.45:
            return base
        variants = suggest_ctr_improved_title(hook, platform)
        if not variants:
            return base
        best = pick_best_title(hook, variants, platform)
        return (best if score_title_ctr(best, platform).score >
                score_title_ctr(base, platform).score else base)[:max_len]
    except Exception:
        return hook[:max_len]


def _title(script: dict, platform: str) -> str:
    hook = script.get("hook", "") or script.get("title", "")
    candidates = []
    if platform == "youtube":
        # V2.1.5: SEARCH-INTENT titles. On dormant/legacy channels the feed
        # test-batch is weak, but SEARCH views don't depend on channel history.
        kw = "psychology facts"
        for p in PILLARS:
            if p["key"] == script.get("pillar"):
                kw = p["search_terms"][0]
                break
        t = _power_title(hook, 58)
        candidates.append(t[:100])
        # V3.4: keyword NATURAL tareeqe se merge hota hai — "Hook: Keyword"
        # (colon, ek hi jagah, natural). Pehle "| Psychology Facts" pipe-append
        # hota tha jo YouTube 2026 mein keyword-stuffing / bot-pattern lagta
        # hai aur CTR ko nuqsan deta hai.
        kw_in_hook = kw.lower() in hook.lower()
        if not kw_in_hook and len(t) + len(kw) + 2 <= 95:
            candidates.append(f"{t}: {kw.title()}"[:100])
        # 2-3 variants for the viral scorer to choose between
        if not kw_in_hook:
            candidates.append(_power_title(f"{hook}: {kw}", 58)[:100])
    elif platform == "facebook":
        return _platform_ctr_title(hook, platform, 58)  # FB feed ~58 chars
    elif platform == "instagram":
        return _platform_ctr_title(hook, platform, 55)
    # V2.9: let the viral-pattern scorer pick the strongest variant
    try:
        from viral_intel import pick_title_variant
        chosen = pick_title_variant(hook, [c for c in candidates if c])
    except Exception:
        chosen = (candidates[0] if candidates else _power_title(hook, 70))[:100]
    return chosen


def _provenance_note(script: dict) -> str:
    sources = [str(s).strip() for s in (script.get("sources") or []) if str(s).strip()]
    if sources:
        return "SOURCES:\n" + "\n".join(f"- {s}" for s in sources[:8])
    if script.get("claim_mode") == "fictional_composite":
        return "Illustrative composite example for education; not a report about a named person or verified incident."
    return "Source verification required before publication."


def _description(script: dict, platform: str, durations: list = None) -> str:
    hook = script.get("hook", "")
    key_points = script.get("key_points", "")
    provenance = _provenance_note(script)
    if platform == "youtube":
        keyword = script.get("pillar_name", "psychology")
        chapters = _chapters(durations) if durations else ""
        desc = (f"{script.get('title','')} — {hook}\n"
                f"{keyword}: how manipulation works, why it works on you, and "
                f"exactly how to protect yourself.\n\n"
                f"{chapters}\n\n"
                f"🔍 WHAT YOU'LL LEARN:\n{key_points}\n\n"
                f"📌 SUBSCRIBE for daily psychology shorts — new uploads daily.\n"
                f"{EDUCATIONAL_DISCLAIMER}\n\n{provenance}\n\n"
                f"{' '.join(PLATFORM_HASHTAGS['youtube'])}")
        return desc[:4500]
    if platform == "facebook":
        first = random.choice([
            f"🚨 {hook}",
            f"🧠 {hook}",
            f"Most people never notice this pattern. {hook}",
        ])
        cta = random.choice(CTA_FB)
        desc = (f"{first}\n\n{key_points}\n\n"
                f"{cta}\n\n{EDUCATIONAL_DISCLAIMER}\n\n{provenance}\n\n"
                f"{' '.join(PLATFORM_HASHTAGS['facebook'])}")
        return desc[:6300]
    if platform == "instagram":
        cta = random.choice(CTA_IG)
        tags = PLATFORM_HASHTAGS["instagram"][:]
        random.shuffle(tags)
        desc = (f"{hook}\n\n{key_points}\n\n"
                f"📌 {cta}\n\n{EDUCATIONAL_DISCLAIMER}\n\n{provenance}\n\n"
                f"{' '.join(tags[:META_MAX_HASHTAGS])}")
        return desc[:2200]
    return script.get("description", "")[:4500]


def _tags(script: dict, platform: str) -> list:
    if platform != "youtube":
        return []  # FB/IG use hashtags in caption
    base = [t.strip() for t in (script.get("tags") or []) if t.strip()]
    pillar = script.get("pillar_name", "")
    if pillar:
        base += [pillar, f"{pillar} psychology", f"{pillar} examples"]
    base += ["psychology facts", "dark psychology", "manipulation",
             "self improvement", "mindset"]
    # dedupe, keep order
    seen, out = set(), []
    for t in base:
        k = t.lower()
        if k not in seen:
            seen.add(k)
            out.append(t)
    # ≤500 chars total
    final, total = [], 0
    for t in out:
        if total + len(t) + 1 > 500:
            break
        final.append(t)
        total += len(t) + 1
    return final


def _ctr_boost_title(hook: str, platform: str) -> str:
    """Apply CTR-boosting patterns to a title for maximum click-through.

    YouTube Shorts-specific: first 3 words are everything on mobile.
    Uses proven 2026 CTR patterns for psychology/true-crime niche.
    """
    hook = hook.strip().rstrip("?.!")
    if not hook:
        return ""

    # Pattern 1: Number + specificity (highest CTR in 2026 psychology niche)
    if len(hook.split()) <= 5 and random.random() < 0.35:
        numbers = ["3", "7", "10", "11", "12", "21", "50", "100"]
        hook = f"{random.choice(numbers)} {hook[0].lower() + hook[1:]}" if hook else hook

    # Pattern 2: Question mark → curiosity gap (YouTube Shorts feed loves questions)
    if not hook.endswith("?") and random.random() < 0.25:
        question_words = ["Why", "How", "What", "When", "Why do"]
        hook = f"{random.choice(question_words)} {hook[0].lower() + hook[1:]}?"

    return hook[:70]


def _youtube_title_optimizations(script: dict, base_title: str) -> list[str]:
    """Generate multiple CTR-optimized title variants for YouTube A/B thinking.

    YouTube Shorts: ≤70 chars ideal, first 40 chars most important (mobile),
    keyword in first 100 chars of description.
    """
    hook = script.get("hook", "") or script.get("title", "")
    variants = []

    # V1: Hook-first (strong pattern interrupt)
    variants.append(_power_title(hook, 70))

    # V2: Number + hook (specificity CTR boost)
    n_title = _ctr_boost_title(hook, "youtube")
    if n_title and n_title != variants[0]:
        variants.append(_power_title(n_title, 70))

    # V3: Question format (curiosity gap)
    q_title = _ctr_boost_title(hook, "youtube")
    if q_title and q_title not in variants:
        variants.append(_power_title(q_title, 70))

    # Deduplicate and cap
    seen, out = set(), []
    for v in variants:
        key = v.lower().strip()
        if key and key not in seen and len(v) > 15:
            seen.add(key)
            out.append(v)
    return out[:5]


def build_platform_package(script: dict, platform: str,
                           durations: list = None) -> dict:
    """Return {title, description, tags, hashtags, hook} for a platform."""
    if platform == "youtube":
        # YouTube: SEO keyword title (longer, search-intent) + CTR optimization
        title = _title(script, platform)
        # V3.4: CTR boost sirf tab jab score GENUINELY weak ho (<0.55 honest
        # scale — pehle 0.70 ka threshold tha jo har normal title ko trigger
        # karta tha aur random rewrites titles ko kharaab kar dete thay).
        try:
            from ctr_optimizer import describe_ctr_grade, pick_best_title, score_title_ctr, suggest_ctr_improved_title
            _ctr_score = score_title_ctr(title, "youtube")
            if _ctr_score.score < 0.55:
                _variants = suggest_ctr_improved_title(
                    script.get("hook", script.get("title", "")),
                    "youtube",
                    pillar_keywords=[p["key"] for p in PILLARS]
                )
                if _variants:
                    # sab variants + original score karo — sirf tab replace
                    # karo jab koi variant sach mein behtar ho
                    ctr_title = pick_best_title(script.get("hook", ""), _variants, "youtube")
                    if score_title_ctr(ctr_title, "youtube").score > _ctr_score.score:
                        title = ctr_title
                        logger.info("CTR boost: %s (%s)",
                                    title[:55], describe_ctr_grade(
                                        score_title_ctr(title, "youtube").score))
        except Exception:
            pass
        # V3.6.3: SEARCH-KEYWORD GUARANTEE — SEOGuard ke mutabiq title mein
        # keyword ZAROORI hai. Title picker/CTR boost kabhi keyword-less
        # variant chun lete hain → natural ": Keyword" merge (no pipe
        # stuffing, bot-pattern wapas nahi aata).
        kw = "psychology facts"
        for p in PILLARS:
            if p["key"] == script.get("pillar"):
                kw = p["search_terms"][0]
                break
        if kw.lower() not in title.lower() and len(title) + len(kw) + 2 <= 100:
            title = f"{title[:80]}: {kw.title()}"[:100]
    else:
        title = _title(script, platform)

    hashtags = PLATFORM_HASHTAGS.get(platform, [])
    if platform in {"facebook", "instagram"}:
        hashtags = hashtags[:META_MAX_HASHTAGS]
    return {
        "platform": platform,
        "title": title,
        "description": _description(script, platform, durations),
        "tags": _tags(script, platform),
        "hashtags": hashtags,
        "hook": script.get("hook", ""),
    }


if __name__ == "__main__":
    import sys
    sys.path.insert(0, "src")
    from script_generator import generate_script
    s = generate_script()
    for p in ("youtube", "facebook", "instagram"):
        pkg = build_platform_package(s, p)
        print(f"\n=== {p.upper()} ===")
        print("TITLE :", pkg["title"])
        print("DESC  :", pkg["description"][:150].replace("\n", " | "))
        print("TAGS  :", pkg["tags"][:6])
