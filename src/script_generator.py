#!/usr/bin/env python3
"""
Coercion Files — Script Generator.

  • Primary : Groq (Llama-3.3-70B, JSON mode)
  • Fallback: Gemini 2.0 Flash
  • Fallback: randomized template bank (offline-safe)
  • ML loop : the prompt is enriched with the ML engine's best-performing
    hook styles & pillars, so the system writes toward what already works.

Every script follows the viral retention structure:
  HOOK (0-3s pattern interrupt) → STAKES → PAYOFF/EVIDENCE → TWIST → CTA
And is framed educationally ("protect yourself") for monetization safety.
"""

import json
import logging
import os
import random
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import HOOK_STYLES, NICHE, PILLARS
from ml_engine import LearningSystem

logger = logging.getLogger("script_generator")

GROQ_KEY = os.environ.get("GROQ_API_KEY", "")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")

SYSTEM_PROMPT = """You are the lead investigative writer for "Coercion Files" — a premium, high-retention documentary channel analyzing FORENSIC SOCIAL ENGINEERING, HIGH-STAKES PSYCHOLOGICAL DECEPTION, and SELF-DEFENSE for a smart USA audience.

AUDIENCE: USA adults (25-50), skeptical, analytical, interested in true-crime psychology, financial deception, workplace power dynamics, and self-defense.

TONE & STYLE (HUMAN DOCUMENTARY FEEL):
1. NO GENERIC AI FLUFF: Never say "In this video", "Welcome back", "Have you ever wondered", "It is important to remember", or list boring generic bullet points.
2. IN MEDIAS RES HOOK: Start scene 1 immediately in the middle of a high-stakes, shocking, or concrete situation (a specific scenario, real date/number, or dangerous psychological trap). Max 8 words for the hook overlay.
3. CONCRETE ANCHORS: Use tangible details (e.g., "$400k wire transfer", "3-word text message", "1-on-1 meeting", "police interrogation transcript", "declassified memo").
4. HUMAN PACING: Write in short, rhythmic, punchy sentences with natural breath pauses (use '—' and '...' where natural). Avoid long academic run-on sentences.
5. 4-BEAT RETENTION ARC:
   - Beat 1 (0-3s): The Disruptor Hook (curiosity/danger gap).
   - Beat 2 (3-15s): The Psychological Exploit (how the brain glitch is triggered).
   - Beat 3 (15-38s): The Forensic Case Breakdown / Concrete Real Example.
   - Beat 4 (38-55s): The Tactical Immunity (the 1 phrase or action to disarm it) + Loop CTA.
6. MONETIZATION SAFETY: Strictly educational/documentary framing. We decode deception to PROTECT viewers, never to teach malicious harm.
7. TARGET DURATION: 48-58 seconds (approx 110-145 spoken words total across scenes).
8. CINEMATIC VISUAL PROMPTS: Generate specific, moody, documentary b-roll search terms (e.g., "bank vault cctv dark", "redacted fbi document desk", "shadowed interrogation room", "smartphone notification late night", "rain reflection city neon dark") NOT generic smiling stock models.
9. POLICY-SAFE CLOSING (critical): Beat 4 ends with one natural utility or reflection prompt. Invite viewers to save a genuinely useful checklist, answer a question directly related to the case, or follow for another evidence-led episode. Never claim that likes unlock reach, never request an artificial like threshold, never use identity pressure, and never ask viewers to comment a keyword solely to manufacture engagement. Keep it to 1-2 punchy sentences in an authentic documentary voice.

OUTPUT — ONLY valid JSON, no markdown formatting:
{
  "title": "High CTR Viral Title (<=70 chars, search keyword included)",
  "hook": "Exact 2-second hook text shown on screen (<=85 chars)",
  "scenes": [
    {
      "caption": "Punchy human narration for this scene",
      "caption_roman": "Same text",
      "visual": "Specific moody cinematic b-roll query (2-4 words)",
      "emotion": "dark|mysterious|intense|chilling|revelatory"
    }
  ],
  "tags": ["up to 10", "targeted", "usa", "tags"],
  "description": "Engaging 3-sentence description with search keywords and educational disclaimer",
  "key_points": "• Point 1\\n• Point 2\\n• Point 3"
}
Output ONLY the raw JSON object."""


def _groq_with(model: str, prompt: str) -> str:
    url = "https://api.groq.com/openai/v1/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.85,
        "max_tokens": 2200,
        "response_format": {"type": "json_object"},
    }
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {GROQ_KEY}",
                 "Content-Type": "application/json",
                 # V2.9.14: Cloudflare (error 1010) blocks Python-urllib's
                 # default UA → 403 on valid keys. Send a real UA.
                 "User-Agent": "CoercionFiles-CI/1.0"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        return json.loads(resp.read())["choices"][0]["message"]["content"]


def _groq(prompt: str) -> str:
    """V2.2.1: Groq DEPRECATED the Llama chat models (403 on
    llama-3.3-70b-versatile). Walk a model ladder: gpt-oss-120b → 20b → legacy.
    Override via GROQ_MODELS env (comma list) or GROQ_MODEL (single)."""
    single = os.environ.get("GROQ_MODEL", "").strip()
    models = ([single] if single else
              [m.strip() for m in os.environ.get(
                  "GROQ_MODELS",
                  "openai/gpt-oss-120b,openai/gpt-oss-20b,llama-3.3-70b-versatile"
              ).split(",") if m.strip()])
    import time as _time
    last_exc = None
    for attempt in range(3):
        for model in models:
            try:
                return _groq_with(model, prompt)
            except Exception as exc:
                last_exc = exc
                logger.warning("Groq model %s failed: %s", model, exc)
                if "429" in str(exc) or "TOO_MANY_REQUESTS" in str(exc):
                    # V3.7.5: rate-limit storm — back off once per round, then
                    # walk the ladder again (quota often recovers in ~30s).
                    _time.sleep(25 * (attempt + 1))
                break  # switch to fallback provider chain
    raise last_exc


def _gemini_with(model: str, prompt: str) -> str:
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{model}:generateContent")
    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 2200, "temperature": 0.85,
                             "responseMimeType": "application/json"},
    }
    # key in header (x-goog-api-key) — safer than URL query string
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "x-goog-api-key": GEMINI_KEY,
                 # V2.9.14: same Cloudflare/UA guard as Groq
                 "User-Agent": "CoercionFiles-CI/1.0"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = json.loads(resp.read())
        return data["candidates"][0]["content"]["parts"][0]["text"]


def _gemini(prompt: str) -> str:
    """V2.2.2: model ladder — older flash models get deprecated over time."""
    models = [m.strip() for m in os.environ.get(
        "GEMINI_MODELS", "gemini-2.5-flash-lite,gemini-3-flash,gemini-2.5-flash").split(",") if m.strip()]
    last_exc = None
    for model in models:
        try:
            return _gemini_with(model, prompt)
        except Exception as exc:
            last_exc = exc
            logger.warning("Gemini model %s failed: %s", model, exc)
    raise last_exc


def _replace_hook_everywhere(script: dict, old_hook: str) -> None:
    """V3.5: hook override ke saath scene-1 aur title bhi update karo.

    V3.6.5: agar purana hook scene 0 mein NAHI milta (LLM scripts aksar
    scene 0 ka pehla sentence alag likh dete hain), to scene 0 ka PEHLA
    sentence hi naye hook se replace ho jata hai — taake overlay aur
    narration ka link 100% rehta hai (clickbait gap kabhi nahi).
    """
    new_hook = script.get("hook", "")
    if not new_hook or not script.get("scenes"):
        return
    old_low = (old_hook or "").strip().lower()
    s0 = script["scenes"][0]
    cap = s0.get("caption", "")
    idx = cap.lower().find(old_low) if old_low else -1
    if idx >= 0:
        new_cap = (cap[:idx] + new_hook + cap[idx + len(old_hook):]).strip()
    else:
        # LLM ne scene 0 ko hook se shuru nahi kiya → pehla sentence replace
        first_end = cap.find(". ")
        if first_end > 0:
            rest = cap[first_end + 2:].strip()
            new_cap = f"{new_hook}. {rest}" if rest else new_hook
        else:
            new_cap = f"{new_hook}. {cap}" if cap else new_hook
    s0["caption"] = new_cap
    s0["caption_roman"] = new_cap
    title = script.get("title", "")
    if old_low and old_low in title.lower():
        script["title"] = re.sub(re.escape(old_hook), new_hook, title,
                                 flags=re.I)
    elif new_hook.lower() not in title.lower() and len(new_hook) + 2 <= 70:
        # title mein hook ka zikr nahi → natural "Hook: Title-core" merge
        script["title"] = f"{new_hook}: {title}"[:70]


def _repair_script_structure(script: dict) -> dict:
    """V3.6.5: LLM scripts ki DETERMINISTIC post-repair.

    CI mein LLM scripts guard fail karti thin (68 words / 3 scenes / 50-word
    scene / 81-char title). Regeneration unreliable hai — LLM phir bhi choti
    script deta hai. Ye offline repair GUARANTEED structure theek karti hai:

      1. 45+ words wali scene → 2 scenes mein split (caption guard + voice
         segment length dono theek)
      2. scenes < 4 → template bank se detail/concept scene append
      3. total words < 100 → detail scene append (45-58s narration)
      4. title > 70 chars → word-boundary clamp (CTR guard rule)
      5. fallback claims stay generic/fictional unless a source ledger is present
      6. unicode punctuation normalize (dash/quote variants -> ASCII) — supervisor ki
         ASCII/USA check ke liye
      7. V3.7: per-scene MINIMUM caption length (seg0 >= 9 words, baqi >= 16 words)
         — VoiceGuard seg-too-short (1.5s) aur over-pace (>3.2 wps) failures rokti hai.
         Chota caption = chota segment = guard fail. Ye pool se guaranteed extension
         attach karti hai (voice 45-58s sweet spot intact rehta hai).
    """

    # 6) V3.7: per-scene minimum caption length — VoiceGuard pacing failures fix
    MIN_WORDS_S0 = 9
    MIN_WORDS_OTHER = 16
    _pool = [
        "In a fictional composite case, the brain notices the pattern before the person can name it.",
        "Case notes in this educational example follow a simple sequence: trust, isolation, then urgency.",
        "Cognitive overload can narrow attention, making one pressured option feel like the only option.",
        "A case-study style example shows that control can sound calm instead of aggressive.",
        "The example uses a transcript-style moment to show how a boundary gets tested one step at a time.",
        "Your nervous system can move into a defensive baseline when pressure never seems to stop.",
        "Behavioral psychology calls this compliance pressure: small agreements can make a later request feel normal.",
        "The safer move is to name the tactic and create time before agreeing to anything important.",
    ]
    _pool_idx = 0

    # 1) split lambi scenes (sentence boundary par)
    out_scenes = []
    for sc in script.get("scenes", []):
        cap = sc.get("caption", "") or ""
        # 38+ words → split (VoiceGuard 15s cap: ~2.5 wps par 38 words
        # ≈ 15s ke qareeb; aadha hone par ~7.5s — safe zone)
        if len(cap.split()) > 38:
            sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", cap)
                         if s.strip()]
            parts = None
            if len(sentences) >= 2:
                mid = len(sentences) // 2
                parts = (" ".join(sentences[:mid]), " ".join(sentences[mid:]))
            else:
                # ek hi lamba sentence → word midpoint par split
                ws = cap.split()
                half = len(ws) // 2
                parts = (" ".join(ws[:half]), " ".join(ws[half:]))
            if parts:
                for part in parts:
                    new_sc = dict(sc)
                    new_sc["caption"] = part
                    new_sc["caption_roman"] = part
                    out_scenes.append(new_sc)
                continue
        out_scenes.append(sc)
    script["scenes"] = out_scenes

    # V3.7: har scene ko minimum word length tak extend karo — chote segments
    # VoiceGuard ko fail karate hain (seg too short / speaking rate > 3.2 wps).
    def _scene_words(sc: dict) -> int:
        return len((sc.get("caption") or "").split())

    for idx, sc in enumerate(script["scenes"]):
        need = MIN_WORDS_S0 if idx == 0 else MIN_WORDS_OTHER
        if _scene_words(sc) < need:
            cap = (sc.get("caption") or "").strip()
            ext = _pool[_pool_idx % len(_pool)]
            _pool_idx += 1
            cap = f"{cap.rstrip('.')}" if cap.endswith(".") else cap
            cap = (cap.rstrip(". ") + ". " + ext) if cap.strip() else ext
            sc["caption"] = cap.strip()
            sc["caption_roman"] = sc["caption"]

    # hook ↔ scene 1 LINK guarantee (V3.6.5): narration ka pehla sentence
    # hamesha hook se shuru hota hai — overlay aur voice ka clickbait gap
    # kabhi nahi. LLM scripts aksar scene 0 ko alag shuru karti thin.
    hook = (script.get("hook") or "").strip()
    if hook and script["scenes"]:
        s0 = script["scenes"][0]
        cap = (s0.get("caption") or "").strip()
        cap_low = cap.lower()
        first_end = cap.find(". ")
        first_sent = cap[:first_end].lower() if first_end > 0 else cap_low
        # hook ke words pehle sentence mein hain?
        hook_words = {w for w in re.findall(r"[a-z']+", hook.lower())}
        sent_words = set(re.findall(r"[a-z']+", first_sent))
        link = len(hook_words & sent_words) / max(1, len(hook_words))
        if link < 0.5:
            rest = cap[first_end + 2:].strip() if first_end > 0 else ""
            new_cap = f"{hook}. {rest}" if rest else hook
            s0["caption"] = new_cap
            s0["caption_roman"] = new_cap

    # 2+3) choti script → template-bank detail scene(s) append
    words = len(" ".join(s.get("caption", "") for s in script["scenes"]).split())
    extras = [
        {"caption": "In a fictional composite case, the pressure sequence is "
                    "trust, isolation, then urgency. Treat this as an "
                    "educational illustration, not a report about a named person.",
         "visual": "redacted case file dark desk", "emotion": "chilling"},
        {"caption": "Cognitive overload explains why an urgent message can "
                    "shrink attention. Pause long enough to compare the "
                    "request with independent evidence.",
         "visual": "vintage psychology study dark", "emotion": "mysterious"},
        {"caption": "Case notes can reveal the boundary test: a small request "
                    "first, a private channel next, and pressure after that. "
                    "Name the sequence before you respond.",
         "visual": "case documents dim light", "emotion": "dark"},
        {"caption": "Save this checklist for a calmer review later. Which "
                    "detail would you verify first before taking action?",
         "visual": "dark city night reflection", "emotion": "revelatory"},
    ]
    cta_extra = extras.pop()
    while len(script["scenes"]) < 4 or words < 100:
        extra = extras[len(script["scenes"]) % len(extras)]
        sc = {"caption": extra["caption"], "caption_roman": extra["caption"],
              "visual": extra["visual"], "emotion": extra["emotion"]}
        script["scenes"].append(sc)
        words += len(extra["caption"].split())
        if words >= 100:
            break
    # engagement CTA guarantee — aakhri scene mein hona hi chahiye
    # (word-boundary match: "following" mein "follow" nahi milna chahiye)
    full_low = " ".join(s.get("caption", "") for s in script["scenes"]).lower()
    if not re.search(r"\b(like|comment|follow|save|share|subscribe|hit)\b",
                     full_low):
        script["scenes"].append(
            {"caption": cta_extra["caption"], "caption_roman": cta_extra["caption"],
             "visual": cta_extra["visual"], "emotion": cta_extra["emotion"]})

    # 4) title clamp 20-70 chars (word boundary) + unicode normalize
    title = (script.get("title") or "").strip()
    title = title.replace("\u2011", "-").replace("\u2013", "-") \
                 .replace("\u2014", "-").replace("\u2018", "'") \
                 .replace("\u2019", "'").replace("\u201c", '"') \
                 .replace("\u201d", '"')
    if len(title) > 70:
        cut = title[:70].rsplit(" ", 1)[0]
        title = cut.rstrip(":|,- ") if cut else title[:70]
    if len(title) < 20:
        hook = (script.get("hook") or "").strip()
        if hook and len(title) + len(hook) + 2 <= 70:
            title = f"{hook}: {title}"
    script["title"] = title

    # scenes ke andar bhi unicode normalize (supervisor ASCII check)
    for sc in script["scenes"]:
        for key in ("caption", "caption_roman"):
            val = (sc.get(key) or "")
            sc[key] = (val.replace("\u2011", "-").replace("\u2013", "-")
                          .replace("\u2014", "-").replace("\u2018", "'")
                          .replace("\u2019", "'").replace("\u201c", '"')
                          .replace("\u201d", '"'))
    return script


def _parse_script(text: str) -> dict:
    if text.startswith("```"):
        text = re.sub(r"^```\w*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    script = json.loads(text)
    assert "title" in script and "scenes" in script, "missing title/scenes"
    assert len(script["scenes"]) >= 3, "need >=3 scenes"
    for s in script["scenes"]:
        s.setdefault("caption", "")
        s.setdefault("caption_roman", s["caption"])
        s.setdefault("visual", "dark moody city night cinematic")
        s.setdefault("emotion", "dark")
    script.setdefault("hook", script["scenes"][0].get("caption", "")[:80])
    script.setdefault("tags", ["psychology", "dark psychology", "manipulation"])
    script.setdefault("sources", [])
    script.setdefault("claim_mode", "factual")
    return script


def _template_script(pillar: dict, hook_style: str, topic: str = None) -> dict:
    """Offline template bank — randomized forensic human storytelling per pillar."""
    topic_label = (topic or "").strip()[:80]
    hook = topic_label or random.choice(pillar["hooks"])

    # Forensic narrative setups (Concrete human case anchors)
    narrative_setups = {
        pillar.get("key"): [
            f"In a fictional composite {pillar['name'].lower()} case, pressure begins with a request that sounds reasonable. Then the other person tries to control the timeline.",
            f"This educational {pillar['name'].lower()} case follows a familiar pattern: connection first, narrowed choices next, and urgency at the end.",
            f"A case-study style example of {pillar['name'].lower()} shows why a calm pause protects judgment better than a fast answer.",
        ]
    }

    forensic_proofs = [
        "Cognitive overload can narrow attention when a message demands an instant answer, so the safest first step is to create time.",
        "Confirmation bias can make a dramatic story feel true before independent evidence is checked; verify the sender through a separate channel.",
        "Behavioral psychology describes compliance pressure: a small agreement can make a later request feel more ordinary than it is.",
        "The useful concept is authority bias: a title, uniform, or confident tone can sound persuasive without proving the request is legitimate.",
    ]

    # V3.5: second concrete detail — template scripts 86-94 words ki thin
    # (ScriptGuard 90+ chahta hai) aur ek hi proof thin. Ye scene script ko
    # ~105+ words tak le jata hai + retention ke liye ek aur forensic detail.
    second_details = [
        "Case notes in this fictional composite example show the sequence clearly: trust first, isolation next, urgency last.",
        "A transcript-style example shows the pressure staying polite while the available choices quietly disappear.",
        "The case-study pattern is easy to test: ask who benefits, what evidence exists, and why the deadline cannot wait.",
        "In this educational example, control stays quiet; the warning sign is not volume but the removal of independent verification.",
    ]

    tactical_shields = [
        "The universal defense is simple: the second you feel pressured to act instantly, force a 24-hour pause. Real opportunities survive sleep; scams don't.",
        "Your tactical shield is to name the tactic aloud: 'Why is this urgent?' The moment urgency is questioned, the manipulator loses leverage.",
        "The psychological antidote is unwavering boundary clarity: never make a financial or emotional commitment under manufactured time pressure.",
        "Remember: legitimate authorities will never demand instant secrecy or immediate wire transfers. Pause, breathe, and verify independently.",
    ]

    # Policy-safe utility/reflection CTA. The compatibility module name
    # remains compulsion_cta, but its prompt bank must not incentivize
    # likes, comments, shares, or follows with reach or identity pressure.
    try:
        from compulsion_cta import cta_pair
        _cta_lines = cta_pair()
        cta = " ".join(_cta_lines)
    except Exception:
        cta = ("Save this checklist if you want to review the pattern later. "
               "Which detail would you have verified first?")

    setup_pool = narrative_setups.get(pillar.get("key")) or next(
        iter(narrative_setups.values()))
    setup = random.choice(setup_pool)
    proof = random.choice(forensic_proofs)
    detail = random.choice(second_details)
    shield = random.choice(tactical_shields)

    topic_visual = topic_label or pillar["name"]
    visuals = [
        f"{topic_visual} documentary evidence dark",
        "bank cctv footage dark",
        "redacted case file desk",
        "shadowed figure corridor night",
        "smartphone screen notification dark",
        "rain on window city neon",
        "interrogation room mirror dark",
        "financial chart red drop",
        "cyber security glitch screen dark",
    ]


    scenes = [
        {
            "caption": f"{hook}. Here is the exact case breakdown.",
            "caption_roman": f"{hook}. Here is the exact case breakdown.",
            "visual": visuals[0],
            "emotion": "intense",
        },
        {
            "caption": setup,
            "caption_roman": setup,
            "visual": visuals[1],
            "emotion": "mysterious",
        },
        {
            "caption": proof,
            "caption_roman": proof,
            "visual": visuals[2],
            "emotion": "dark",
        },
        {
            "caption": detail,
            "caption_roman": detail,
            "visual": visuals[3],
            "emotion": "chilling",
        },
        {
            "caption": shield,
            "caption_roman": shield,
            "visual": visuals[4],
            "emotion": "revelatory",
        },
        {
            "caption": cta,
            "caption_roman": cta,
            "visual": visuals[5],
            "emotion": "revelatory",
        },
    ]

    # V3.5: title ke pehle 3 words mein keyword/power hona chahiye (CTRGuard
    # rule). Agar hook khud keyword se shuru nahi hota to keyword prefix karo.
    title = f"{hook} | Forensic Psychology"
    kw = (pillar.get("search_terms") or ["psychology"])[0]
    first3 = " ".join(title.split()[:3]).lower()
    if kw.lower() not in first3 and "psychology" not in first3:
        title = f"{kw.title()}: {hook}"[:100]

    return {
        "title": title,
        "hook": hook,
        "scenes": scenes,
        "tags": pillar["tags"][:10],
        "description": (f"{hook} — Forensic case breakdown: how high-stakes deception works "
                        f"and the exact psychological defense to protect yourself. "
                        f"{NICHE['angle']} #psychology #truecrime #scams"),
        "key_points": "• The psychological exploit explained\n• How the brain trap works\n• 1-step tactical defense",
        "pillar": pillar["key"],
        "pillar_name": pillar["name"],
        "sources": [],
        "claim_mode": "fictional_composite",
    }


def generate_script(pillar_key: str = None, hook_style: str = None,
                    ml: LearningSystem = None, topic: str = None) -> dict:
    """Generate one short-form script (45-58s)."""
    # ── strategy selection (ML-informed) ──
    arm_key = None
    if ml is not None and not pillar_key:
        chosen = ml.choose_strategy()
        pillar = next(p for p in PILLARS if p["key"] == chosen["pillar"])
        hook_style = hook_style or chosen["hook_style"]
        arm_key = chosen["arm_key"]   # V2.1: exact arm travels with the script
    else:
        pillar = next((p for p in PILLARS if p["key"] == pillar_key), None)
        if pillar is None:
            pillar = random.choice(PILLARS)
        hook_style = hook_style or random.choice(HOOK_STYLES)
        if ml is not None:
            # forced pillar — still attribute to a consistent arm key
            from ml_engine import current_day_part
            arm_key = ml.arm_key(pillar["key"], hook_style, current_day_part())

    # ── ML insights fed back into the prompt (closing the learning loop) ──
    learned_hint = ""
    if ml is not None:
        best = ml.best_formulas(3)
        if best:
            learned_hint = ("\n\nPERFORMANCE DATA (learn what works): recent top "
                            "formulas were pillars/styles: "
                            + ", ".join(f"{b['pillar']}/{b['hook_style']}"
                                        f"(score {b['mean']})" for b in best)
                            + ". Weight your choice toward these when relevant.")

    prompt = f"""Create a YouTube Short script (45-58 seconds) for the pillar "{pillar['name']}".
Hook style: {hook_style}.
Topic: {topic or pillar['name']}.
Pillar hooks for inspiration: {', '.join(pillar['hooks'][:5])}.
Return JSON with `claim_mode` (`factual` or `fictional_composite`) and a `sources` array of URLs for every factual claim. If you cannot cite a claim, make it a clearly labeled fictional composite example. Never invent statistics, cases, institutions, or study findings.
{learned_hint}
Write it now — valid JSON only."""

    # ── LLM chain (V2.9.13: provider preference — self-healing) ──
    # V3.1: HOOK QUALITY GATE — weak hook (score < 1.0) = weak engagement
    # (97 views / 0 likes ka sabab). Weak hook par naya script regenerate
    # karte hain (max 3 attempts) taake first-2-second pattern-interrupt
    # strong ho.
    _state_path = Path(__file__).resolve().parent.parent / "data" / "llm_state.json"
    preferred = None
    try:
        if _state_path.exists():
            preferred = json.loads(_state_path.read_text(encoding="utf-8")).get("provider")
    except (OSError, json.JSONDecodeError):
        preferred = None

    script = None
    source = None
    hook_score = 0.0
    for _attempt in range(4):
        script = None
        source = None
        providers = {"groq": (_groq, GROQ_KEY), "gemini": (_gemini, GEMINI_KEY)}
        order = [pp for pp in (preferred, "gemini", "groq") if pp in providers]
        for name in order:
            fn, key = providers[name]
            if not key:
                continue
            try:
                script = _parse_script(fn(prompt))
                source = name
                break
            except Exception as exc:
                logger.warning("%s failed: %s", name, exc)
        if script is None:
            script = _template_script(pillar, hook_style, topic=topic)
            source = "template"
            logger.info("Using template fallback (no LLM key or LLM failed)")
        try:
            from viral_intel import score_hook
            hook_score = score_hook(script.get("hook", ""))["score"]
        except Exception:
            hook_score = 1.0
        # V3.1: DURATION CHECK — LLM scripts 34s par aa rahi thin (target 45-58s).
        # Choti script = weak retention + Shorts shelf par nuksan.
        _words = len(" ".join(str(sc.get("caption", ""))
                              for sc in script.get("scenes", [])).split())
        _est = _words / 2.2
        too_short = _est < 38 and source in ("groq", "gemini")
        # V3.4: gate ab 0.60 hai (honest scale) — 0.85 purane inflated scale
        # ka tha jahan base hi 0.55 tha. Ab weak hook genuinely regenerate
        # hota hai, sirf praise nahi milti.
        if hook_score >= 0.60 and not too_short:
            break
        if too_short and _attempt < 3:
            prompt += ("\n\nIMPORTANT: The previous script was too short "
                       f"(~{_est:.0f}s, target 48-58s). Make it LONGER: "
                       "extend to ~120-140 spoken words with one more concrete "
                       "forensic detail and a named psychology concept only "
                       "when it has a source in the sources list. Never invent "
                       "statistics, cases, institutions, or study findings.")
            logger.warning("Script too short (~%ds) — retrying with 'make longer' hint",
                           round(_est))
        else:
            logger.warning("Hook weak (score %.2f) — regenerating script (attempt %d/4)",
                           hook_score, _attempt + 2)
    # V3.1 + V3.4: hook fallback — regen ke baad bhi weak ho to documented
    # strong hook se override. V3.4: (1) threshold 0.60 honest scale,
    # (2) CURATED pillar hooks ko priority (pehle fragment-generator pehle
    # chalta tha — "Stop letting them" jaise aadhe hooks overlay par chale
    # jaate thay), (3) replacement tabhi jab wo GENUINELY behtar score kare.
    if hook_score < 0.60:
        candidates = ([h for h in pillar.get("hooks", []) if h]
                      if pillar.get("hooks") else [])
        try:
            from viral_intel import random_boosted_hook as _rbh
            candidates += [_rbh(), _rbh()]
        except Exception:
            pass
        best, best_score = None, hook_score
        for cand in candidates:
            cand = cand[:85]
            try:
                from viral_intel import score_hook as _sh
                cs = _sh(cand)["score"]
            except Exception:
                cs = 0.0
            if cs > best_score:
                best, best_score = cand, cs
        if best:
            _old_hook = script.get("hook", "")
            script["hook"] = best
            _replace_hook_everywhere(script, _old_hook)   # V3.5: scene1+title sync
            hook_score = best_score
            logger.info("Hook overridden with strong documented hook (score %.2f)",
                        hook_score)
    # CTA repair — append a useful or genuinely conversational closing prompt
    # when the generated script has no closing action.
    _full = " ".join(sc.get("caption", "") for sc in script.get("scenes", [])).lower()
    _has_cta = bool(re.search(
        r"\b(like|comment|follow|save|share|subscribe|hit)\b", _full))
    if not _has_cta and len(script.get("scenes", [])) < 6:
        try:
            from compulsion_cta import build_engaging_last_scene
            script["scenes"].append(build_engaging_last_scene(pillar.get("key")))
            logger.info("CTA repair: policy-safe closing scene appended")
        except Exception:
            pass

    # ── V3.1: FULL SCRIPT QUALITY GATE — sirf hook nahi, poora script ──
    # score_script: hook(0.25) + cta(0.20) + anchor(0.20) + psych(0.15) +
    # structure(0.10) + duration(0.10). Weak (C/D) → documented pillar hook
    # + repair list store. Ye score script ke saath travels karta hai taake
    # ML engagement doctor isay use kar sake.
    _quality = {"score": 0.5, "issues": ["unknown"], "components": {}}
    try:
        from viral_intel import score_script as _score_script
        from viral_intel import score_script_grade
        _quality = _score_script(script)
        if _quality["score"] < 0.65:
            # repair: documented strong hook override (human creator ki
            # swipe file — pillar hooks settings mein already curated hain)
            pillar_hooks = ([h for h in pillar["hooks"] if h]
                            if pillar.get("hooks") else [])
            if pillar_hooks:
                _old_hook = script.get("hook", "")
                script["hook"] = random.choice(pillar_hooks)[:85]
                _replace_hook_everywhere(script, _old_hook)   # V3.5 sync
                logger.info("SCRIPT quality gate: weak score %.2f → hook replaced "
                            "with proven pillar hook", _quality["score"])
                try:
                    hook_score = score_hook(script.get("hook", ""))["score"]
                except Exception:
                    hook_score = 1.0
                _quality = _score_script(script)  # re-score
        logger.info("SCRIPT quality: %.2f (%s) issues=%s",
                    _quality["score"], score_script_grade(_quality["score"]),
                    _quality.get("issues", []))
    except Exception as exc:
        logger.warning("script quality gate skipped: %s", exc)

    # remember which provider worked (self-healing order)
    if source in ("groq", "gemini"):
        try:
            _state_path.parent.mkdir(parents=True, exist_ok=True)
            _state_path.write_text(json.dumps({"provider": source}), encoding="utf-8")
        except OSError:
            pass

    script["source"] = source
    script["hook_score"] = round(hook_score, 3)
    script["script_quality"] = _quality
    script["pillar"] = pillar["key"]
    script["pillar_name"] = pillar["name"]
    script["hook_style"] = hook_style
    script["arm_key"] = arm_key or LearningSystem.arm_key(
        pillar["key"], hook_style, "any")
    script.setdefault("tags", pillar["tags"][:10])
    script.setdefault("sources", [])
    script.setdefault("claim_mode", "factual" if source in ("groq", "gemini") else "fictional_composite")

    # ── V3.1: CTR-OPTIMIZED TITLE — generate high-CTR title variants ──
    # V3.4: threshold 0.55 (honest scale) + sirf tab replace karo jab naya
    # title GENUINELY behtar score kare (pehle blind replace hota tha).
    try:
        from ctr_optimizer import describe_ctr_grade, pick_best_title, score_title_ctr, suggest_ctr_improved_title
        _title_score = score_title_ctr(script.get("title", ""), "youtube")
        if _title_score.score < 0.55:
            _variants = suggest_ctr_improved_title(
                script.get("hook", script.get("title", "")),
                "youtube",
                pillar_keywords=[p["key"] for p in PILLARS]
            )
            if _variants:
                _best = pick_best_title(script.get("hook", ""), _variants, "youtube")
                if score_title_ctr(_best, "youtube").score > _title_score.score:
                    script["title"] = _best
                    logger.info("CTR title boost: %s → %s (%s)",
                                _title_score.title[:40], script["title"][:40],
                                describe_ctr_grade(
                                    score_title_ctr(script["title"], "youtube").score))
    except Exception as exc:
        logger.warning("CTR title optimization skipped: %s", exc)

    # ── V3.6.5: DETERMINISTIC STRUCTURE REPAIR (aakhri guarantee) ──
    # LLM scripts CI mein choti (68 words / 3 scenes / 50-word scene /
    # 81-char title) aa kar guards fail karti thin. Ye offline repair
    # scenes split/append + title clamp + unicode normalize karta hai —
    # guards ke liye structure hamesha theek.
    _before_words = len(" ".join(sc.get("caption", "")
                                  for sc in script.get("scenes", [])).split())
    _before_scenes = len(script.get("scenes", []))
    script = _repair_script_structure(script)
    _after_words = len(" ".join(sc.get("caption", "")
                                 for sc in script.get("scenes", [])).split())
    if (_after_words != _before_words or
            _before_scenes != len(script.get("scenes", []))):
        logger.info("🧩 Structure repair: %d→%d scenes, %d→%d words",
                    _before_scenes, len(script.get("scenes", [])),
                    _before_words, _after_words)

    return script


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    s = generate_script()
    print(json.dumps(s, indent=2, ensure_ascii=False))
