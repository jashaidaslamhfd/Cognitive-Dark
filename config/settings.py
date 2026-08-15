#!/usr/bin/env python3
"""
Coercion Files — Global Configuration & Converted Niche Strategy.

Niche conversion (2026 trend-researched):
  OLD: "Dark Psychology & Manipulation Tactics"  →  monetization-risk framing
  NEW: "The Psychology of Influence — Dark Psychology for Self-Defense"

Why this conversion (verified 2026 trends):
  • "Dark psychology" raw-form is high-viewership but frequently flagged as
    harmful/reused content by YouTube & Meta → blocks monetization.
  • The trending, advertiser-friendly psychology sub-niches are: Stoicism,
    cognitive biases, red flags / gaslighting awareness, body language,
    influence & persuasion ethics, psychological self-defense.
  • "Protect yourself / spot manipulation" framing keeps the dark-psych DNA
    (hook power) while being Educational → safe for YPP / FB CMP / IG partner.
"""

import os
from pathlib import Path

# ─────────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("CD_DATA_DIR", ROOT / "data"))
OUTPUT_DIR = Path(os.environ.get("CD_OUTPUT_DIR", ROOT / "output"))
CLIP_CACHE = DATA_DIR / "clips"
TMP_DIR = OUTPUT_DIR / "tmp"
DATA_DIR.mkdir(exist_ok=True)
TMP_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────────────────────
# Channel identity
# ─────────────────────────────────────────────────────────────
CHANNEL_NAME = "Coercion Files"
CHANNEL_TAGLINE = "The Psychology of Coercion — Documented, Decoded, Defended"
TARGET_COUNTRY = "US"
TARGET_LANGUAGE = "en"
# V2.2 positioning: fresh channel (2019 legacy channel retired to archive).
# Create the new channel with EXACTLY this name/handle so CTAs match.
CHANNEL_URL = "https://youtube.com/@coercionfiles"
CHANNEL_ID = ""  # fill after channel creation (Studio → Settings → Advanced)

NICHE = {
    "name": "Coercion Files — The Psychology of Coercion & Defense",
    "parent_niche": "True-Crime Psychology / Behavioral Science",
    "angle": ("Documented cases of coercion, cults, con artistry and mind "
              "control — decoded so viewers can spot the pattern and defend "
              "themselves. Story-driven, evidence-first, educational."),
    "why_trending": (
        "2026's breakout format is true-crime x psychology: cult docs, con-"
        "artist breakdowns and declassified mind-control history dominate "
        "retention charts, while generic 'dark psychology facts' are "
        "saturated. Story arcs hold viewers 2-3x longer than fact lists."
    ),
    "safety": (
        "ALWAYS educational/documentary: explain HOW coercion worked so "
        "viewers can PROTECT themselves. Never instruct how to manipulate. "
        "Include educational disclaimer in every description."
    ),
}

# ─────────────────────────────────────────────────────────────
# Content pillars (V2.2 — Coercion Files positioning)
# ─────────────────────────────────────────────────────────────
PILLARS = [
    {
        "key": "cults",
        "name": "Cult Psychology Decoded",
        "trend": "very high — cult documentaries are retention monsters",
        "hooks": [
            "Why Smart People Join Dangerous Cults",
            "The Cult That Banned These 3 Questions",
            "How Cults Isolate You From Family",
            "Love Bombing: The Cult Recruitment Pipeline",
            "Jonestown: 900 People Obeyed. Why?",
            "NXIVM: A Cult Hidden Inside a Self-Help Brand",
            "How Members Finally Escaped",
            "The Leader Trick That Kills Doubt Instantly",
        ],
        "search_terms": ["cult psychology", "how cults brainwash", "signs of a cult",
                         "love bombing cult", "jonestown explained"],
        "tags": ["cult psychology", "brainwashing", "love bombing", "coercive control",
                 "psychology documentary", "mind control"],
    },
    {
        "key": "con_artists",
        "name": "Con Artists & Scam Psychology",
        "trend": "very high — scam breakdowns are viral + advertiser-safe",
        "hooks": [
            "The Con Artist With 3 Simultaneous Wives",
            "Anatomy of a Perfect Confidence Trick",
            "Why Victims Wire Money Again and Again",
            "The Tinder Swindler Playbook Explained",
            "Urgency: The Trick That Stops You Thinking",
            "How Scammers Script Your First Message",
            "The Pigeon Drop: Oldest Con Alive",
            "One Question That Exposes Most Scammers",
        ],
        "search_terms": ["con artist psychology", "how scams work", "romance scam signs",
                         "confidence trick explained", "spot a scammer"],
        "tags": ["scam psychology", "con artists", "fraud", "romance scam",
                 "social engineering", "psychology facts"],
    },
    {
        "key": "mind_control_history",
        "name": "Declassified Mind Control",
        "trend": "high — MKUltra/true-history crossover is evergreen",
        "hooks": [
            "MKUltra: The CIA's Mind-Control Program",
            "The Files They Didn't Burn",
            "Cold War Plans to Weaponize Hypnosis",
            "Project Stargate: The Psychic Spy Program",
            "Radio Rwanda: Broadcasts That Built Hate",
            "How One Ad Manipulated a Country",
            "The Experiment That Crossed Every Line",
            "What Declassified Papers Actually Show",
        ],
        "search_terms": ["MKUltra explained", "cia mind control", "project stargate",
                         "psychological experiments history", "propaganda psychology"],
        "tags": ["MKUltra", "mind control", "declassified", "psychology history",
                 "propaganda", "true crime"],
    },
    {
        "key": "interrogation",
        "name": "Interrogation & Lie Detection",
        "trend": "high — interrogation content has elite retention",
        "hooks": [
            "Why Innocent People Confess",
            "The Question Sequence That Catches Liars",
            "Silence: The Interrogator's Weapon",
            "How Detectives Read Baseline Behavior",
            "Words That Betray You: Statement Analysis",
            "The Reid Technique Under the Microscope",
            "Micro-Expressions Interviewers Watch For",
            "How to Answer a Manipulative Question",
        ],
        "search_terms": ["lie detection", "interrogation psychology", "how to spot a liar",
                         "false confessions psychology", "body language lying"],
        "tags": ["lie detection", "interrogation", "body language", "psychology",
                 "statement analysis", "true crime"],
    },
    {
        "key": "coercive_control",
        "name": "Coercive Control Awareness",
        "trend": "very high — biggest psychology sub-niche, evergreen",
        "hooks": [
            "Coercive Control: The Invisible Abuse",
            "The Daily Rules Abusers Enforce",
            "How Abusers Turn Family Against You",
            "Financial Abuse: Control Through Money",
            "Why Leaving Is the Most Dangerous Time",
            "The Cycle That Keeps Victims Returning",
            "Blame-Shifting: The Language of Control",
            "Document Everything: Protect Yourself",
        ],
        "search_terms": ["coercive control signs", "emotional abuse signs",
                         "gaslighting examples", "toxic relationship red flags",
                         "narcissist abuse"],
        "tags": ["coercive control", "emotional abuse", "gaslighting", "red flags",
                 "toxic relationships", "psychology"],
    },
    {
        "key": "mass_psychology",
        "name": "Crowds, Propaganda & Feed Manipulation",
        "trend": "high — 'the algorithm is manipulating you' meta-angle pops",
        "hooks": [
            "How Crowds Change Your Brain in Minutes",
            "The Feed That Outrages You on Purpose",
            "Why Misinformation Spreads 6x Faster",
            "Astroturfing: Fake Grassroots Movements",
            "Fear Headlines: Rewiring Your Attention",
            "The Bandwagon Effect in Your Feed",
            "Overton Window: Shifting What's Normal",
            "Manufactured Consent in 60 Seconds",
        ],
        "search_terms": ["mass psychology", "propaganda techniques", "how algorithms manipulate",
                         "misinformation psychology", "crowd psychology"],
        "tags": ["mass psychology", "propaganda", "media manipulation", "crowd psychology",
                 "misinformation", "psychology facts"],
    },
    {
        "key": "brainwashing_myths",
        "name": "Brainwashing: Myth vs Science",
        "trend": "medium-high — myth-busting is shareable + authoritative",
        "hooks": [
            "Brainwashing Is Not What You Think",
            "The Manchurian Candidate Myth",
            "You Can't Be Brainwashed by One Video",
            "What Real Coercive Persuasion Requires",
            "The POW Controversy, Explained",
            "Did Deprogramming Ever Work?",
            "Thought Reform: The 6 Conditions",
            "Your Phone Isn't Brainwashing You. Worse.",
        ],
        "search_terms": ["brainwashing myth", "is brainwashing real", "coercive persuasion",
                         "thought reform", "manchurian candidate"],
        "tags": ["brainwashing", "psychology myths", "coercion", "psychology science",
                 "mind control", "facts"],
    },
    {
        "key": "stoic_defense",
        "name": "Mental Immunity (Stoic Defense)",
        "trend": "very high — stoicism fusion remains #1 philosophy trend",
        "hooks": [
            "Stoic Immunity Against Manipulation",
            "Marcus Aurelius on Handling Liars",
            "The 5-Second Stoic Pause",
            "Epictetus: Control Only Your Judgments",
            "Premeditation of Evils as a Shield",
            "How Stoics Defuse Insults Instantly",
            "Amor Fati: The Unhackable Mindset",
            "The Stoic Rule Cults Can't Break",
        ],
        "search_terms": ["stoicism manipulation", "stoic mindset", "marcus aurelius quotes",
                         "emotional control", "mental toughness"],
        "tags": ["stoicism", "marcus aurelius", "mental toughness", "emotional control",
                 "psychology", "mindset"],
    },
]

# ─────────────────────────────────────────────────────────────
# Hook styles (true-crime flavored; ML learns which perform)
# ─────────────────────────────────────────────────────────────
HOOK_STYLES = [
    "case_file",        # "Case #12: the salesman who wasn't a salesman"
    "chilling_fact",    # "The detail nobody noticed until it was too late"
    "question_hook",    # "Would you have spotted the lie?"
    "warning",          # "If this happens in your first chat, run"
    "plot_twist",       # "The victim defended him. Here's why."
    "timeline",         # "Day 1: charm. Day 30: control."
    "confession",       # "The recruiter later admitted the script"
    "red_flag",         # "Three signs, in order, every time"
]

# ─────────────────────────────────────────────────────────────
# Video specs
# ─────────────────────────────────────────────────────────────
FPS = 30
VIDEO_THREADS = int(os.environ.get("VIDEO_THREADS", "0")) or max(1, (os.cpu_count() or 2) - 1)
SHORTS = {"width": 1080, "height": 1920, "min_s": 40, "max_s": 58}
LONG_FORM = {"width": 1280, "height": 720, "min_s": 480, "max_s": 900}
SQUARE = {"width": 1080, "height": 1080}  # optional IG feed variant

# ─────────────────────────────────────────────────────────────
# Platforms
# ─────────────────────────────────────────────────────────────
PLATFORMS = {
    "youtube": {
        "enabled": True,
        "format": "shorts",            # shorts | long
        "width": SHORTS["width"], "height": SHORTS["height"],
        "category": "27",              # Education
        "max_daily": 4,
        "timezone": "America/New_York",
        "peak_hours": [7, 12, 17, 20],  # EST/EDT (4 windows)
        "hashtags": 3,
        "algorithm_notes": ("Retention first 5s + 100% watch-through drive the "
                            "Shorts feed; title keyword in first 100 chars; "
                            "description keyword-dense first 2 lines."),
    },
    "facebook": {
        "enabled": True,
        "format": "reels",             # reels | video
        "width": SHORTS["width"], "height": SHORTS["height"],
        "max_daily": 4,
        "timezone": "America/New_York",
        "peak_hours": [9, 13, 17, 20],
        "hashtags": 8,
        "algorithm_notes": ("FB Reels: first-3s hook + comments in first hour "
                            "drive reach; 9:16 <90s posts to Reels tab; "
                            "engagement (shares, reactions) is the top signal."),
    },
    "instagram": {
        "enabled": True,
        "format": "reels",
        "width": SHORTS["width"], "height": SHORTS["height"],
        "max_daily": 4,
        "timezone": "America/New_York",
        "peak_hours": [11, 14, 17, 19],
        "hashtags": 20,                # IG allows 30; 15-20 sweet spot
        "algorithm_notes": ("IG Reels: watch-time %, replay, shares, saves; "
                            "post at 11am-2pm / 7-9pm EST; save-value content "
                            "('save this') boosts distribution."),
    },
}

# ─────────────────────────────────────────────────────────────
# Monetization targets (2026 thresholds — research-verified)
# ─────────────────────────────────────────────────────────────
MONETIZATION = {
    "youtube": {
        "full_ytp": {"subs": 1000, "watch_hours": 4000, "shorts_views_90d": 10_000_000},
        "tier1": {"subs": 500, "watch_hours": 3000, "shorts_views_90d": 3_000_000},
        "strategy": "Daily Shorts (Shorts-views path) + weekly 10-15min long-form (watch-hours path)",
    },
    "facebook": {
        "cmp": {"followers": 5000, "minutes_60d": 60_000, "uploads_30d": 5},
        "stars": {"followers": 500},
        "strategy": "Daily Reels (60-90s, qualifies for in-stream ads) + long-form weekly",
    },
    "instagram": {
        "partner": {"followers": 500, "days_active": 60, "plays_60d": 3_000_000},
        "strategy": "Daily Reels; bonuses/partner are invite-driven — prioritize saves & shares",
    },
    "plan_days": 30,
    "daily_posts_per_platform": {"youtube": 2, "facebook": 2, "instagram": 2},
    "weekly_long_form": 1,
}

# ─────────────────────────────────────────────────────────────
# Posting discipline (2026 algorithm: consistency beats bursts)
# ─────────────────────────────────────────────────────────────
MIN_POST_GAP_HOURS = float(os.environ.get("MIN_POST_GAP_HOURS", "3.0"))

# ─────────────────────────────────────────────────────────────
# Music
# ─────────────────────────────────────────────────────────────
MUSIC_VOLUME = float(os.environ.get("MUSIC_VOLUME", "0.18"))
MUSIC_DIR = ROOT / "assets" / "music"

# ─────────────────────────────────────────────────────────────
# TTS
# ─────────────────────────────────────────────────────────────
TTS_PRIMARY = os.environ.get("TTS_PRIMARY", "kokoro")   # kokoro | onnx | edge | elevenlabs
KOKORO_VOICE = os.environ.get("KOKORO_VOICE", "am_fenrir")  # deep authoritative male
KOKORO_SPEED = float(os.environ.get("KOKORO_SPEED", "1.00"))  # energetic USA pace,
                                                     # lekin VoiceGuard 3.2 wps cap ke andar (2.9 wps @1.00)
KOKORO_LANG = "a"  # American English
VOICE_STYLE = os.environ.get("VOICE_STYLE", "usa")  # usa = faster, punchy, authoritative

# ─────────────────────────────────────────────────────────────
# USA VIRAL STYLE (fast cuts + word captions)
# ─────────────────────────────────────────────────────────────
USA_STYLE = {
    "cut_seconds": float(os.environ.get("USA_CUT_SECS", "2.4")),   # fast cut length
    "min_cut_seconds": 1.4,                                        # don't go shorter
    "caption_words_per_group": int(os.environ.get("CAPTION_GROUP_WORDS", "2")),
    # V2.3: 1150 = above the Shorts UI overlay (title/hashtags/buttons cover
    # the bottom ~25% of the frame). V2.2's 1520 sat hidden under the UI.
    "caption_y": 1150,          # safe zone on 1080x1920 canvas
    "caption_h": 260,
    "highlight_color": (255, 210, 60),   # yellow pop on current word (USA style)
    "dim_future_alpha": 120,             # upcoming words dimmed
    "past_color": (255, 255, 255),       # spoken words white
    "punch_zoom": 0.10,                  # zoom-punch strength per cut
    "punch_duration": 0.35,              # punch settles in .35s
    "hook_seconds": 2.2,
    "loop_seconds": 1.4,
}

# ─────────────────────────────────────────────────────────────
# Clip providers
# ─────────────────────────────────────────────────────────────
CLIP_PROVIDER_ORDER = ["pexels", "pixabay"]  # fallback chain
CLIP_CACHE_TTL_DAYS = 30
MIN_CLIP_BYTES = 100_000

# ─────────────────────────────────────────────────────────────
# ML engine
# ─────────────────────────────────────────────────────────────
ML_STORE_PATH = DATA_DIR / "learning_store.json"
LEARNING = {
    "epsilon": 0.10,          # residual random exploration (Thompson is primary)
    "policy": "thompson",     # thompson | ucb — mature bandit policy
    "ucb_c": 2.0,             # UCB1 exploration constant
    "min_plays_before_greedy": 6,
    "dedup_window": 60,       # videos to compare against for variation
    "min_variation": 0.35,    # min 1 - token-overlap vs recent posts
    "reward_retention": 0.6,  # weight of retention on reward
    "reward_engagement": 0.3,
    "reward_views": 0.1,
    "penalty_failure": -2.0,  # upload/API failure
    "penalty_low_retention": -1.0,
    "bonus_viral": 3.0,       # reward for strong output
    # V3.4 HONESTY: 0.0 — publish karna performance NAHI hai. Pehle har
    # successful upload +1.0 reward deta tha, jis se bandit ko lagta tha ke
    # har formula kaam kar raha hai (chahe views 0 hon) aur weak content
    # repeat hota rehta tha. Ab reward SIRF real metrics se aata hai
    # (scripts/fetch_metrics.py → credit_video).
    "bonus_consistent": 0.0,
    "per_platform": True,     # track arm performance per platform
}

# ─────────────────────────────────────────────────────────────
# Independent Release Gate (V3.5) — reality-check layer
# Har department ka apna independent guard; supervisor aakhri judge.
# Video tabhi upload hoti hai jab SAB guards pass karein.
#   strict (default) = koi fail/unknown → HELD (upload nahi)
#   warn             = report banti hai, block nahi (emergency)
#   off              = gate skip
# ─────────────────────────────────────────────────────────────
GATE = {
    "mode": os.environ.get("GATE_MODE", "strict"),
    "max_repairs": int(os.environ.get("GATE_MAX_REPAIRS", "2")),
    "report_dir": DATA_DIR,
}
