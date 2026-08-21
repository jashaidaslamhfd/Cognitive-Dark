"""Policy-safe engagement prompts for Coercion Files.

The module name is retained for backwards compatibility, but prompts must not
pressure viewers to like, comment, share, or follow in exchange for reach,
protection, identity validation, or a promised continuation. Prompts should
serve a clear viewer purpose: save a checklist, reflect on the case, or follow
for the next documented case.
"""

from __future__ import annotations

import logging
import random

logger = logging.getLogger("cta")

# These prompts are intentionally utility-led or genuinely conversational.
# Avoid algorithm claims, artificial like thresholds, identity pressure, and
# instructions to comment a keyword solely to manufacture engagement.
CTA_BANK = {
    "save_value": [
        "Save this checklist so you can review it before making a high-pressure decision.",
        "Save this case file. The warning signs are easier to spot when you know the pattern.",
        "Save this guide for later: pause, verify independently, and never act under pressure.",
    ],
    "reflection": [
        "Which part of this pattern was easiest to miss? Share your reading of the case below.",
        "What would you verify first in this situation? Comment with the specific answer that helps others think it through.",
        "Have you seen this pattern described differently? Share the detail that changed your view.",
    ],
    "follow": [
        "Follow Coercion Files for documented case files and practical defenses.",
        "Follow for the next evidence-led case breakdown; every episode separates the claim from the proof.",
        "Follow Coercion Files if you want more case-based psychology and self-defense research.",
    ],
}

# Quality guards use these words to confirm that a script has a closing action.
ENGAGE_WORDS = ("like", "comment", "follow", "save", "share", "hit", "subscribe")

# Explicitly disallowed patterns for Meta-safe output. These are checked in
# tests and can also be used by downstream moderation tooling.
BAIT_PATTERNS = (
    "algorithm won't show",
    "algorithm will not show",
    "one like equals",
    "like this to get",
    "like it to get",
    "if this hits",
    "comment 'safe'",
    "comment \"safe\"",
    "we're counting",
    "we are counting",
)


def cta_pair(seed: int | None = None) -> list[str]:
    """Return one or two natural, non-incentivized closing prompts."""
    rng = random.Random(seed) if seed is not None else random
    primary_name = rng.choices(
        ["save_value", "reflection", "follow"],
        weights=[0.45, 0.35, 0.20],
    )[0]
    out = [rng.choice(CTA_BANK[primary_name])]

    if rng.random() < 0.35:
        secondary_names = [name for name in CTA_BANK if name != primary_name]
        out.append(rng.choice(CTA_BANK[rng.choice(secondary_names)]))
    return out


def has_engagement(text: str) -> bool:
    """Return whether text contains a closing action or conversation prompt."""
    t = (text or "").lower()
    return any(word in t for word in ENGAGE_WORDS)


def contains_bait(text: str) -> bool:
    """Return whether text contains a known incentivized-engagement pattern."""
    lowered = (text or "").lower()
    return any(pattern in lowered for pattern in BAIT_PATTERNS)


def build_engaging_last_scene(
    pillar_key: str | None = None,
    seed: int | None = None,
) -> dict:
    """Build a complete final scene with a useful, non-coercive CTA."""
    pair = cta_pair(seed)
    lines = " ".join(pair)
    if pillar_key:
        logger.debug("CTA generated for pillar=%s", pillar_key)
    return {
        "caption": lines,
        "caption_roman": lines,
        "visual": "documentary case file desk light",
        "emotion": "revelatory",
    }


def llm_cta_instructions() -> str:
    """Instructions for natural, policy-safe LLM closing prompts."""
    return (
        "Use one natural closing prompt that gives the viewer a real reason to "
        "save the checklist, reflect on the case, or follow for another "
        "evidence-led episode. A genuine question is allowed when it relates "
        "to the subject. Never claim that likes unlock reach, never ask viewers "
        "to hit an artificial like threshold, never use identity pressure, and "
        "never ask viewers to comment a keyword solely to manufacture engagement."
    )
