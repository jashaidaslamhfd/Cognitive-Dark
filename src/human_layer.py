#!/usr/bin/env python3
"""
Coercion Files — Human Layer (V3.0).

System ko ek REAL human creator ki tarah behave karwata hai — not a bot.

 1) NATURAL VARIATION   — har post copy mein "human quirks": varied title
    casing, description openers, CTA rotation, hashtag count jitter, small
    publish-time jitter (0-8 min). Bot fingerprints (har post identical
    format, exact same minute) algorithm ko spam signal dete hain.

 2) CREATOR INTUITION   — StrategyDirector ke numbers ke upar insaani zaban
    mein "kyun" likhta hai: hot streak par "double down", slump par
    "pivot", outlier par "lean in". Aise hi jaise ek creator sochta hai.

 3) DAILY BRIEF         — data/daily_brief.md: subah ka "planner". Kal kya
    chala, aaj kya post karna hai, kya karna hai (comments reply, IG check),
    kya avoid karna hai. Ye file CI mein commit hoti hai — aap padh sakte ho
    system ki roz ki soch.

 4) COMMENT ENGINE      — (scripts/engage_comments.py) YouTube/FB/IG ke
    comments nikalta hai, insaani tone mein jawab DRAFT karta hai (LLM se),
    queue mein rakhta hai (aap approve karo). Optional auto-reply positive
    comments par (AUTO_REPLY_COMMENTS=true).

Sab kuch READ/write bounded hai, memory-safe, aur pehle se banaye gaye
fail-safe (event diary) ke saath chalta hai.
"""

from __future__ import annotations

import json
import logging
import os
import random
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from config.settings import DATA_DIR, META_MAX_HASHTAGS

logger = logging.getLogger("human_layer")

BRIEF_PATH = DATA_DIR / "daily_brief.md"
REPLY_QUEUE = DATA_DIR / "reply_queue.json"

# ── 1) Natural variation pools (insaani copy quirks) ──────────────
TITLE_CASE_VARIANTS = ["title", "sentence", "upper"]
DESC_OPENERS = [
    "Most people never notice this pattern. {hook}",
    "Here's how it actually works. {hook}",
    "You've felt this before, even if you couldn't name it. {hook}",
    "This one is documented. {hook}",
    "Psychologists have studied this for decades. {hook}",
    "It hides in plain sight. {hook}",
]
CTA_POOL = [
    "Follow Coercion Files for the psychology they don't teach you in school.",
    "Follow for documented cases that protect you.",
    "Follow Coercion Files — coercion decoded daily.",
    "Follow to see the pattern before it sees you.",
    "Follow Coercion Files for daily psychology shorts.",
]
HOOK_OPENERS = [
    "Stop letting them", "Why smart people", "Nobody tells you",
    "The trick they", "How they get you", "Never say this",
    "The warning they ignored", "Watch what they say", "If they do this, run",
]
# emoji "signatures" — har post 1-2, kabhi 0 (bilkul insaan jaisa)
EMOJI_BANK = ["🧠", "🚨", "🔥", "⚠️", "🎯", "📌", "💡", "🗝️", "🕵️", "🧩"]


def jitter_minutes(base_min: int = 8, seed: int | None = None) -> int:
    """Publish-time jitter: 0..base_min random minutes (human, not robot)."""
    rng = random.Random(seed) if seed is not None else random
    return rng.randint(0, base_min)


def jitter_publish_at(dt, base_min: int = 8):
    """Return dt shifted forward by 0..base_min minutes (tz-aware safe)."""
    if dt is None:
        return dt
    return dt + timedelta(minutes=jitter_minutes(base_min))


def vary_title(title: str, seed: int | None = None) -> str:
    """Insaan jaisa title — kabhi Title Case, kabhi Sentence case, kabhi UPPER."""
    if not title:
        return title
    rng = random.Random(seed) if seed is not None else random
    style = rng.choice(TITLE_CASE_VARIANTS)
    if style == "upper":
        return title.upper()[:100]
    if style == "sentence":
        return title[:1].upper() + title[1:].lower()[:99]
    return title[:100]


def vary_description(desc: str, hook: str = "", seed: int | None = None) -> str:
    """Description ka pehla line rotate karta hai — har post same nahi."""
    if not desc:
        return desc
    rng = random.Random(seed) if seed is not None else random
    opener = rng.choice(DESC_OPENERS).format(hook=hook or "")
    parts = desc.split("\n\n", 1)
    rest = parts[1] if len(parts) > 1 else desc
    return f"{opener}\n\n{rest}"[:4900]


def vary_cta(desc: str, seed: int | None = None) -> str:
    """Rotation of CTA lines so feed looks native, not templated."""
    if not desc:
        return desc
    rng = random.Random(seed) if seed is not None else random
    cta = rng.choice(CTA_POOL)
    # replace an existing "Follow ..." line if present
    desc = re.sub(r"Follow [^\n.]*\.", cta, desc, count=1)
    if cta not in desc:
        desc = f"{desc}\n\n{cta}"
    return desc[:6300]


def vary_hashtags(tags: list, platform: str, seed: int | None = None) -> list:
    """Hashtag count jitter — har post mein count thora kam/zyada (bot nahi)."""
    if not tags:
        return tags
    rng = random.Random(seed) if seed is not None else random
    max_h = (META_MAX_HASHTAGS if platform in {"facebook", "instagram"}
             else 3 if platform == "youtube" else 8)
    n = rng.randint(max(1, max_h - 2), max_h)
    shuffled = tags[:]
    rng.shuffle(shuffled)
    return shuffled[:n]


def maybe_emoji(seed: int | None = None) -> str:
    """Kabhi emoji, kabhi nahi — 70% time 1-2 emojis."""
    rng = random.Random(seed) if seed is not None else random
    if rng.random() < 0.3:
        return ""
    return rng.choice(EMOJI_BANK)


# ── 2) Creator intuition — insaani reasoning on top of ML numbers ──
def creator_intuition(ml_data: dict | None) -> list[str]:
    """Plain-language "soch" — kyun kya karna hai (human creator voice)."""
    if not ml_data:
        return ["Cold start: kuch bhi achha lag raha hai to usay repeat karo, "
                "warna naya pillar try karo."]
    notes = []
    arms = ml_data.get("arms", {})
    scored = []
    for key, arm in arms.items():
        # V3.4: sirf REAL outcomes (n >= 2) — priors sirf belief hain, "kya
        # chala" nahi. Pehle seeded priors hi intuition ko "hot streak" ka
        # jhoota ehsaas dete thay.
        n_real = int(arm.get("n", 0) or 0)
        if n_real < 2:
            continue
        pn = int(arm.get("prior_n", 0) or 0)
        pm = float(arm.get("prior_mean", 0.0) or 0.0)
        rewards = float(arm.get("rewards", 0.0) or 0.0)
        mean = (pm * pn + rewards) / (pn + n_real)
        scored.append((mean, key, n_real))
    scored.sort(reverse=True)
    if scored:
        mean, key, n = scored[0]
        pillar = key.split("::")[0]
        if mean >= 1.2:
            notes.append(f"🔥 {pillar} strong formula chala raha hai (mean {mean:.2f}, "
                         f"n={n}) — double down: aaj isi pillar par 2 videos banao.")
        elif mean >= 0.8:
            notes.append(f"👍 {pillar} theek chal raha hai — use karo par explore "
                         f"bhi karte raho.")
        else:
            notes.append(f"🔄 {pillar} kharab hai ({mean:.2f}) — pivot: aaj koi "
                         f"bilkul naya pillar try karo (variety = naya data).")
    # last run outcome
    logs = ml_data.get("reward_log", [])[-5:] + ml_data.get("penalty_log", [])[-5:]
    wins = sum(1 for e in logs if e.get("reward", 0) > 0.5)
    losses = sum(1 for e in logs if (e.get("penalty", 0) or 0) > 1)
    if wins >= 3:
        notes.append("🏆 Wins ka streak hai — kuch mat badlo, bas chalta rakho.")
    elif losses >= 3:
        notes.append("🧊 Slump hai — thora ruk ke naya angle try karo (volume kam, "
                     "quality zyada).")
    if not notes:
        notes.append("[i] Data abhi kam hai — explore karo, jaldi results mat maango.")
    return notes[:4]


# ── 3) Daily brief — subah ka planner ───────────────────────────
def generate_daily_brief(ml_data: dict | None = None,
                         journal: dict | None = None,
                         monetization: dict | None = None) -> str:
    """Human-readable daily planner; system ki roz ki 'soch'."""
    now = datetime.now(timezone.utc)
    today = now.strftime("%A, %Y-%m-%d")
    lines = [
        "# ☕ Daily Brief — Creator's Morning Notes",
        "",
        f"*{today}* (auto-generated, insaani soch mein)",
        "",
        "## Kal kya hua",
    ]
    # last run from journal
    hist = (journal or {}).get("history", [])
    if hist:
        last = hist[-1]
        lines.append(f"- Last run: {last.get('started', '')[:16]} → "
                     f"**{last.get('note', '?')}**")
    else:
        lines.append("- Koi run abhi nahi hua.")
    # monetization snapshot
    if monetization:
        for plat in ("youtube", "facebook", "instagram"):
            b = monetization.get(plat, {})
            pct = b.get("pct", {})
            if pct:
                lines.append(f"- {plat.title()}: " +
                             ", ".join(f"{k} {v}%" for k, v in pct.items()))
    lines += ["", "## Aaj ka plan (creator ki tarah)", ""]
    lines.append("- **Post**: Daily Pipeline (scheduled) — 3 platforms, LLM scripts.")
    lines.append("- **Reply to comments**: 10 min — comments se algorithm boost "
                 "milta hai (replies = community signal).")
    lines.append("- **Check Instagram**: ab linked hai — verify pehla reel live hai.")
    lines += ["", "## Intuition (kyun kya)", ""]
    lines += [f"- {n}" for n in creator_intuition(ml_data)]
    lines += ["", "## Aaj avoid karna", ""]
    lines.append("- Do runs ek saath mat karo (min-gap guard khud rok deta hai — "
                 "sahi hai).")
    lines.append("- Kisi ek pillar ko 3 baar lagatar mat do (audience bore).")
    lines += ["", "---", "_Yeh brief roz update hota hai (Mission Control / daily "
              "pipeline). System insaani soch se chalta hai, bot nahi._"]
    return "\n".join(lines)


def write_daily_brief(ml_data: dict | None = None, journal: dict | None = None,
                      monetization: dict | None = None) -> Path:
    out = generate_daily_brief(ml_data, journal, monetization)
    try:
        BRIEF_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = BRIEF_PATH.with_suffix(".tmp")
        tmp.write_text(out, encoding="utf-8")
        os.replace(tmp, BRIEF_PATH)
    except OSError as exc:
        logger.warning("brief write failed: %s", exc)
    return BRIEF_PATH


# ── 4) Reply queue helpers (comment engine UI) ───────────────────
def load_reply_queue() -> list:
    try:
        if REPLY_QUEUE.exists():
            return json.loads(REPLY_QUEUE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        pass
    return []


def save_reply_queue(queue: list) -> None:
    try:
        REPLY_QUEUE.parent.mkdir(parents=True, exist_ok=True)
        tmp = REPLY_QUEUE.with_suffix(".tmp")
        tmp.write_text(json.dumps(queue, indent=2, ensure_ascii=False),
                       encoding="utf-8")
        os.replace(tmp, REPLY_QUEUE)
    except OSError as exc:
        logger.warning("reply queue write failed: %s", exc)
