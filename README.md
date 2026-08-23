# 🧠 Coercion Files — Mature ML Multi-Platform Growth Engine

**YouTube + Facebook + Instagram** automation system for the Coercion Files channel. **Machine-learning-driven, multi-platform, self-repairing** — V3 upgrades
the bandit to production-grade Bayesian online learning that also learns from real
top-channel competitor patterns (not just your own videos).

## 🆕 V3.5 — Independent Release Gate (2026-08-13) — "har cheez ka apna guard + supervisor"

Full architecture: [`GATE_ARCHITECTURE.md`](GATE_ARCHITECTURE.md). Summary:

- **IndependentObserver** — system ke scores par rely nahi karta; RAW artifacts
  measure karta hai (ffprobe, WAV analysis, real ML outcomes)
- **8 independent guards** (`src/guards/`) — script, hook, voice, caption,
  video, seo (YT/FB/IG 2026 rules), ctr, views (real performance)
- **Producer self-scores guards tak pahunch hi nahi sakte** — gate unhein
  strip kar deta hai; guards sirf asal cheez dekhte hain
- **USASupervisor** — aakhri judge: independence audit + USA-audience
  calibration (English, no Urdu tokens, no British spelling, $, ET publish
  window) + cross-platform distinctness. Fail-CLOSED — "pata nahi" kabhi
  pass nahi hota
- **Video tabhi upload hoti hai jab SAB guards pass karein** — warna repair
  loop naya script banata hai (GATE_MAX_REPAIRS=2), phir HELD
- `GATE_MODE`: strict (default) | warn | off
- Har run ke baad `data/gate_report.md` + `.json` (CI commit = audit trail);
  standalone re-judge: `python scripts/run_gate.py`
- Gate ne 3 real bugs bhi pakre: Urdu CTA templates (English kar diye),
  hook-override ke baad scene-1 purana hook (clickbait gap — sync fix),
  currency regex false-positive
- 173 tests (27 naye guard tests), Ruff clean

## 🆕 V3.4 — Honest Scoring (2026-08-13) — "system ab jhoot nahi bolta"
## 🆕 V3.4 — Honest Scoring (2026-08-13) — "system ab jhoot nahi bolta"

Full details: [`HONEST_SCORING_FIX.md`](HONEST_SCORING_FIX.md). Summary:

- **Scorers ab weak content ko weak keh sakte hain** — hook/CTR/title/script scorers ke inflated bases (0.5-0.55) hata diye; weak hook ab FAIL hota hai, weak title ab "D — rewrite" grade pa sakta hai
- **ML sirf REAL metrics se seekhta hai** — publish hone par self-reward (`bonus_consistent`) band; `fetch_metrics.py` ke real views/retention hi arm ka fate decide karte hain. Legacy store ke fake "published" rewards one-time purge ho jate hain
- **Seed priors ab double-count nahi hote** — pehle prior 2x weight ke saath arm mein merge tha (real data aadha asar karta tha) aur seeded arms kabhi "cold" nahi dikhte thay (exploration kabhi fire nahi hoti thi)
- **Recency penalty + pillar weights ab ASAL selection par asar karti hain** (pehle argmax ke BAAD lagti thin — silent no-op)
- **Reward gate ab honest hai** — missing retention = "unknown" (pehle "passed" bolta tha); missing voice data = neutral 0.5 (pehle free perfect 1.0)
- **Virality index bina real performance ke kabhi "viral-ready" nahi kehta**
- **Video fixes** — CTA end-card ka text ab actually dikhta hai (pehle canvas ke bahar draw hota tha = khali dark box); thumbnails ab cover-crop hote hain (pehle landscape frames 9:16 mein squish ho jate thay); titles ab "Hook | Keyword" stuffing aur toote grammar ke baghair
- 143 tests (naya `tests/test_honesty.py` in sab ko lock karta hai), Ruff clean

## 🆕 V3 — Mature ML (2026-08-08)

- **Bayesian Thompson sampling** (`src/bandit.py`) — posterior per arm, explore/exploit
  via uncertainty; UCB1 still available as fallback
- **Market intelligence** (`src/market_intel.py`) — learns pillar/hook priors from real
  top-channel competitor titles in `data/competitor_seed.txt` (67 viral patterns);
  live YouTube search when `YOUTUBE_API_KEY` is set
- **Multi-signal reward** (`src/reward.py`) — retention 34% + completion 16% +
  engagement 22% + views 14% + CTR 9% + voice quality 5%
- **Per-platform learning** — YouTube/FB/Instagram now learn separately
- **Strategy director** (`src/strategy_director.py`) — auto-tunes epsilon, voice
  speed, pillar weights, posting gap from rolling results
- **ML diagnostics** (`src/ml_diagnostics.py`) — maturity stage
  (EXPLORING → LEARNING → CONVERGING → MATURE) + posterior confidence intervals
- 78 tests, Ruff clean, CI green, full selftest renders a real MP4

## 🆕 V2.1 — Audit Fix Pass (2026-08-04)

Every finding of the full-codebase audit is fixed (critical → minor):

**Uploads unblocked**
- YouTube `publishAt` no longer crashes (aware-vs-naive datetime fix; RFC3339 `Z` format; <24h clamp)
- YouTube OAuth-from-secrets now includes `token_uri` + scopes → headless token refresh works
- Facebook scheduling sends Unix epoch (was ISO string → API rejected); `FB_REELS_ENDPOINT` honored with auto-fallback to `/videos`
- Instagram Reels now carry their caption on the resumable path; `video_length` sent in milliseconds (was file-size in bytes)

**ML upgraded (V2's loop was disconnected — now closed)**
- Rewards/penalties land on the **exact arm** that produced the video (V2 wrote them to different keys, so the bandit never learned)
- **Per-video attribution**: every published `video_id` is mapped to its formula; `scripts/fetch_metrics.py` pulls real views/likes/comments and credits the responsible arm (`reward_from_metrics` is now wired in, was dead code)
- Channel/page growth applies consistency bonuses to recently active arms
- Every mutation auto-saves (V2 lost end-of-run rewards); recency decay re-tests stale formulas
- **Volume discipline**: daily caps (`max_daily`) + `MIN_POST_GAP_HOURS` enforced per platform — consistency over bursts, the 2026 algorithm signal

**Content quality**
- Karaoke captions use a **sliding window** — the current word-chunk stays visible for the whole caption (V2 froze after the first 2 lines)
- Fast cuts now get **3 genuinely distinct clips** per scene (rank-offset selection; V2 returned the same top clip → stills)
- SEO power-word titles actually append the power word; acronyms (FBI, CIA) preserved
- Kokoro speed default consistent (1.08x USA style everywhere); torch pipeline cached; onnx-first chain
- Procedural visuals vectorized (numpy) + off-by-one palette fix

**Infrastructure**
- War Mode fixed: missing `niche_strategy` module created (brain works again, topics banked per pillar)
- `deep_repair.py` runs (import-order crash fixed) + real repair logic (schema heal, stale-quarantine release)
- Crash-journal order corrected (repair runs **before** marking the new run, real crash detection restored)
- Monetization metrics no longer clobbered by defaults every run; `print_plan` f-string fixed
- Workflows: secrets accept both naming schemes (`||` fallback), Kokoro model cached in War Mode, `fonts-dejavu` installed, concurrency serialized, failures no longer hidden by `|| echo`, music `.wav` files now committable

---

```
Script (Groq/Gemini) → Clips (Pexels/Pixabay) → Voice (Kokoro TTS)
→ Video (MoviePy) → Upload (YouTube + Facebook + Instagram) → ML feedback loop
```

## 🎬 USA Viral Style (built-in)

The video package is engineered for the top USA faceless-channel look:

| Element | Style |
|---|---|
| **Fast cuts** | Every scene micro-cut into ~2.4s sub-clips with a zoom-punch on each cut |
| **Captions** | Word-by-word karaoke captions — spoken words white, **current word pops yellow**, upcoming dimmed (Hormozi/Beast style) |
| **Hook overlay** | Big red hook badge in the first 2.2s + loop-trick re-hook at the end |
| **Voice** | Kokoro deep male (`am_fenrir`) at **1.08x** — energetic, punchy, USA cadence |
| **Titles** | Hook-first, keyword in first 40 chars, Title Case, power words, ≤70 chars |
| **Tags** | Broad + specific + branded mix, ≤500 chars |
| **Description** | Keyword-dense first lines, "What you'll learn" bullets, chapter timestamps, hashtags, CTA |

Tuning via env: `USA_CUT_SECS`, `CAPTION_GROUP_WORDS`, `KOKORO_SPEED`, `VIDEO_THREADS`.

---

## ✅ What changed vs V1 (all audit fixes applied)

| V1 problem | V2 fix |
|---|---|
| MoviePy crash (`moviepy.editor` removed in 2.x) | `moviepy==1.0.3` pinned + `compat.py` shim; **verified renders real MP4s** |
| YT upload broken in GH Actions (creds = JSON text) | `_resolve_credentials()` auto-detects file **or** raw JSON, writes temp file, auto-refreshes tokens |
| Scheduler DST bug (hardcoded UTC-5) | `zoneinfo.America/New_York` — verified `-04:00` (EDT) in test runs |
| README quick-start missing ffmpeg | Preflight fails loudly with install instructions; selftest checks |
| Dead code (history dedup, retention flags, long-form) | Real ML dedup (works — verified consecutive runs produce unique content); flags removed; long-form documented as roadmap |
| Single-platform | **YouTube + Facebook + Instagram** uploaders (platform-native copy per algorithm) |
| No learning | **ML engine** (UCB1 bandit + reward/penalty + dedup + platform health) |

---

## 🎯 Niche conversion (2026 trend-researched)

**Old:** "Dark Psychology & Manipulation Tactics" *(monetization-risk framing)*
**New:** **"The Psychology of Influence — Dark Psychology for Self-Defense"**

| Pillar | Trend |
|---|---|
| Psychological Self-Defense | 🔥 #1 viral angle |
| Influence & Persuasion | 🔥 evergreen + advertiser-friendly |
| Dark Personality Awareness | 🔥 narcissist/psychopath content dominates feeds |
| Body Language & Micro-Expressions | 🔥 top search cluster |
| Cognitive Biases & Brain Traps | 🔥 breakout 2026 format |
| Toxic Relationships & Red Flags | 🔥 biggest psychology sub-niche |
| Stoicism × Modern Psychology | 🔥 #1 trending fusion |
| Mind Control & Dark History | 📈 true-crime crossover |

Why: raw "dark psychology" gets flagged as harmful/reused content (blocks YPP/FB CMP).
The educational **"protect yourself"** framing keeps the dark hook-power but is
monetization-safe on all three platforms.

---

## 🧠 ML Learning Engine (`src/ml_engine.py`)

The system **learns from its mistakes and rewards strong output**:

- **UCB1 multi-armed bandit** over `(pillar × hook-style × day-part)` — explores when
  unsure, exploits the best-performing content formulas once evidence exists.
  *(Verified: 300-round simulation correctly surfaces `red_flag_checklist` as top arm.)*
- **Rewards** for strong output: high retention / engagement / views / growth
  (`reward_from_metrics()` maps platform analytics → scalar reward).
- **Penalties** for mistakes: upload failures, spam/dedup blocks, low retention.
  Failures also quarantine a platform after 3 consecutive errors.
- **0% spam-detection guarantee:** dedup guard blocks exact duplicates *and* enforces
  minimum variation vs recent posts; on block the pipeline **retries with a fresh
  strategy** instead of posting repeats. *(Verified: 2 consecutive runs → 2 unique videos.)*
- **Learning persists across CI runs:** `data/learning_store.json` is committed back
  to the repo by the workflow.

Run the simulation to see it learn:
```bash
python src/main.py --simulate
```

---

## 📈 Monetization Plan (2026 thresholds — research-verified)

| Platform | Path | Threshold | 30-day target |
|---|---|---|---|
| YouTube | Shorts-views path | 1,000 subs + 10M Shorts views/90d | 2 Shorts/day + 1 long-form/week |
| YouTube | early tier (fan funding) | 500 subs + 3M Shorts views/90d | realistic first win |
| Facebook | Content Monetization | 5,000 followers + 60k min/60d | 2 Reels/day |
| Facebook | Stars (first money) | 500 followers | reachable in ~30 days |
| Instagram | Partner program | 500 followers + 60 active days | 2 Reels/day |

```bash
python src/monetization_tracker.py    # live progress vs targets
python scripts/fetch_metrics.py       # pulls real analytics → feeds ML rewards
```

> ⚠️ **Honest reality check:** going from 7 subs → 1,000 subs + 4,000 hrs in exactly
> 30 days is a stretch for any fresh channel. The system is engineered for the
> *fastest legitimate* path (daily consistent posting at peak times + retention-focused
> Shorts), and the first real milestone is **YouTube early tier + FB Stars + IG base**.

---

## 🚀 Quick Start

```bash
# 1. deps (Ubuntu/CI)
sudo apt-get install -y ffmpeg fonts-dejavu espeak-ng
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt kokoro-onnx onnxruntime

# 2. config
cp .env.example .env    # fill keys (Groq, Pexels, FB, IG, YT credentials)

# 3. music assets (once)
python scripts/generate_music.py

# 4. offline smoke test
python src/main.py --selftest

# 5. dry-run (builds a real video, NO uploads)
python src/main.py --dry-run

# 6. real run
python src/main.py --platforms youtube,facebook,instagram
```

---

## 🔑 Required Secrets (`.env` / GH Actions secrets)

| Key | Used for |
|---|---|
| `GROQ_API_KEY` | Script generation (primary LLM) |
| `GEMINI_API_KEY` | Script fallback LLM |
| `PEXELS_API_KEY` / `PIXABAY_API_KEY` | Stock video clips |
| `YOUTUBE_CREDENTIALS` | YouTube upload — file path **or** raw OAuth JSON |
| `FB_PAGE_ID` + `FB_ACCESS_TOKEN` | Facebook Reels upload |
| `IG_BUSINESS_ACCOUNT_ID` + `IG_ACCESS_TOKEN` | Instagram Reels upload |

---

## 🔧 Platform Uploaders

- **YouTube** (`platforms/youtube.py`): Data API v3, resumable upload, custom thumbnail,
  SEO title/desc/tags (≤500 chars), `publishAt` scheduling at peak hours, auto token-refresh.
- **Facebook** (`platforms/facebook.py`): Graph API `/{page-id}/video_reels` (Reels → 
  in-stream-ad eligible), multipart file upload (no hosting needed), platform-native caption.
- **Instagram** (`platforms/instagram.py`): Reels container flow
  (`media` → poll `status_code` → `media_publish`), with **resumable rupload** path so it
  works from ephemeral runners without hosting the video publicly.

Each platform gets **native, distinct copy** (`seo.py`) — different titles, captions,
hashtag sets, and CTAs per algorithm (identical cross-post text is a spam signal).

---

## 🛡️ Auto-Repair System (`src/auto_repair.py`)

- **Preflight** — fails fast with clear messages if ffmpeg/ffprobe/fonts/imports missing.
- **StageRunner** — every stage wrapped in retry-with-backoff + declared fallback chains.
- **RepairJournal** — detects a crashed previous run and cleans half-written state on boot.
- **cleanup()** — deletes stale temp files, keeps deliverables.
- **selftest()** — 5 offline smoke tests (script, scheduler, ML, SEO, video render).

---

## 🗂️ Structure

```
config/settings.py          — niche strategy, pillars, platforms, ML hyperparams
src/main.py                 — orchestrator (auto-repair + ML + multi-platform)
src/ml_engine.py            — UCB1 bandit, attribution, volume guards, dedup, health
src/niche_strategy.py       — per-pillar viral topic bank (feeds the Autonomous Brain)
src/autonomous_brain.py     — War Mode decision engine (ML strategy → topic)
src/script_generator.py     — Groq → Gemini → template (ML-informed prompts)
src/seo.py                  — platform-native titles/captions/hashtags
src/clips_downloader.py     — Pexels → Pixabay → procedural fallback
src/tts_engine.py           — Kokoro ONNX → edge-tts → ElevenLabs → silence
src/video_builder.py        — memory-safe scene rendering + ffmpeg concat
src/scheduler.py            — DST-safe per-platform peak hours
src/monetization_tracker.py — 30-day monetization progress vs targets
src/auto_repair.py          — preflight, retries, journal, cleanup, selftest
src/platforms/              — youtube.py, facebook.py, instagram.py
scripts/generate_music.py   — compact dark-ambient beds (~4MB each)
scripts/fetch_metrics.py    — analytics sync → ML rewards
.github/workflows/          — daily pipeline + metrics sync + memory persistence
```

---

## ⚠️ Notes & Caveats

- **Kokoro model** (~360MB) auto-downloads on first TTS use into `data/models/kokoro`
  (cached in CI). Needs `espeak-ng` for out-of-dictionary words.
- **Instagram Reels API** requires a Business/Creator account linked to the FB Page,
  and app review for `instagram_content_publish`. Resumable upload works without hosting.
- **Free APIs** (Pexels/Pixabay/Edge-TTS) can rate-limit — the fallback chain handles it.
- **MoviePy is pinned to 1.0.3** on purpose; don't upgrade blindly (2.x broke the API).
- Long-form (10-15 min) is the next roadmap item for the watch-hours path.


## Storage Optimization
- Diagnostic dumps and audit logs are retained as 90-day GitHub Actions artifacts instead of inflating git repository history.


## Operational safety controls

Dry-runs are read-only with respect to production learning data. A preview writes only to `output/dry_runs/<run_id>/`, including the video, thumbnail, gate reports, gate payload, asset provenance ledger, and disposable journal. Live runs use `output/runs/<run_id>/`; skipped, gate-held, or credential-missing platforms are reported explicitly and do not count as a successful publication.

Every generated run includes `asset_provenance.json`. Downloaded clips carry provider, provider ID, source URL, dimensions, and query metadata; procedural fallbacks are labeled separately. LLM scripts must carry a source ledger unless explicitly marked `fictional_composite`, and descriptions disclose either their sources or their illustrative status.

Meta metrics are stored with explicit availability states. `unavailable`, `permission_denied`, and `error` are not treated as zero views and do not train or penalize the learning bandit. To protect live accounts, `GATE_MODE=warn` and `GATE_MODE=off` remain audit-only unless `ALLOW_UNSAFE_PUBLISH=1` is explicitly set. Destructive repair, boost, and social cleanup commands require their corresponding confirmation environment variable after the dry-run report has been reviewed.

The standalone gate runner discovers the newest run-scoped payload automatically:

```bash
python scripts/run_gate.py --json
```

For a one-off preview:

```bash
GATE_MODE=strict python src/main.py --platforms instagram \
  --topic "How to spot an urgent bank scam" --dry-run
```
