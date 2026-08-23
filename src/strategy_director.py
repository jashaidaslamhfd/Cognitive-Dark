#!/usr/bin/env python3
"""
Coercion Files - Strategy Director (V2.8 — human-mind layer).

Rolling performance (last N videos) dekh khud ba khud in cheezon ko tune karta
hai taake owner ko manually settings na badalni parein:

  • epsilon (exploration rate) - agar rewards barh rahe to exploit zyada,
    warna explore zyada
  • voice speed - USA retention ke liye 1.05-1.12 ke darmyan re-tune
  • per-pillar preference - top pillars ko zyada weight, dead pillars ko kam
  • daily cadence cap - agar quality gir rahi hai to volume kam; agar har
    video achhi to cap barhao
  • minimum post gap - agar same-burst se reach gir rahi hai to gap barhao

V2.8 — HUMAN-MIND LAYER (insaan jaisa sochna):
  • Momentum detection — "hot streak" (lagaatar jite) par exploit karo, aur
    "slump" (3+ kamiyabi nahi) par fresh exploration + volume kam. Insaan bhi
    aisa karta hai: jeet pe double-down, haar pe sabse alag try karo.
  • Variety guard — ek hi pillar 3 baar lagatar mat do; weight dampen karo
    (audience bore na ho).
  • Narrative memory — `data/strategy_notes.md`: har decision ki wajah
    insaani zaban mein likhi jati hai, taake aap (aur ML) samajh sakein
    "yeh isliye kar raha hai kyunki..."
  • Pillar weights are pushed into the ML store so the bandit ACTUALLY uses
    them (before they lived only in director's own state file).

Decisions `data/strategy_state.json` mein save hote hain, aur pipeline inhein
env/ML config override ki tarah istemal karta hai. Har adjustment chhota
(damping) hai taake ek kharab din poori strategy na bigaar de.
"""

from __future__ import annotations

import dataclasses
import json
import logging
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from config.settings import DATA_DIR

logger = logging.getLogger("director")

STATE_PATH = DATA_DIR / "strategy_state.json"
NOTES_PATH = DATA_DIR / "strategy_notes.md"


@dataclass
class StrategyState:
    epsilon: float = 0.15
    kokoro_speed: float = 1.08
    pillar_weights: dict = None
    daily_caps: dict = None
    min_gap_hours: float = 3.0
    momentum: str = "cold_start"        # hot | steady | slump | cold_start
    updated_at: str = ""
    last_mean_reward: float = 0.0
    last_engagement: float = 0.0
    decision_log: list = None

    def __post_init__(self):
        if self.pillar_weights is None:
            self.pillar_weights = {}
        if self.daily_caps is None:
            self.daily_caps = {"youtube": 4, "facebook": 4, "instagram": 3}
        if self.decision_log is None:
            self.decision_log = []


class StrategyDirector:
    def __init__(self, ml=None, state_path: Path = STATE_PATH,
                 notes_path: Path = None):
        self.ml = ml
        self.state_path = Path(state_path)
        if notes_path is None:
            notes_path = (NOTES_PATH if self.state_path == STATE_PATH
                          else self.state_path.with_name("strategy_notes.md"))
        self.notes_path = Path(notes_path)
        self.state = self._load()

    # ── persistence ──
    def _load(self) -> StrategyState:
        try:
            d = json.loads(self.state_path.read_text(encoding="utf-8"))
            fields = {f.name: f.default for f in dataclasses.fields(StrategyState)}
            for k, v in fields.items():
                d.setdefault(k, v)
            return StrategyState(**{k: v for k, v in d.items() if k in fields})
        except (OSError, json.JSONDecodeError, TypeError):
            return StrategyState()

    def save(self) -> None:
        self.state.updated_at = datetime.now(timezone.utc).isoformat()
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(asdict(self.state), indent=2, ensure_ascii=False),
                       encoding="utf-8")
        os.replace(tmp, self.state_path)

    # ── compute rolling stats from ML reward_log ──
    def _rolling(self, n: int = 20) -> dict:
        if not self.ml:
            return {"mean": 0.0, "engagement": 0.0, "n": 0}
        rewards = self.ml.data.get("reward_log", [])[-n:]
        if not rewards:
            return {"mean": 0.0, "engagement": 0.0, "n": 0}
        vals = [r.get("reward", 0) for r in rewards]
        mean = sum(vals) / len(vals)
        # Engagement approximated from how many penalty-free rewards > 0.5
        positive = sum(1 for v in vals if v > 0.5) / len(vals)
        return {"mean": mean, "engagement": positive, "n": len(vals)}

    # ── pillar performance → weights ──
    def _pillar_scores(self) -> dict:
        """V3.4: sirf REAL outcomes se pillar score banta hai (n_real ≥ 2).
        Pehle seeded priors ko hi "experience" maan kar pillars ko weight
        de diye jaate thay — director bhi jhooti tareef par decisions leta
        tha. Ab effective mean = (prior*prior_n + real_sum) / (prior_n + n)
        aur tabhi count hota hai jab kam az kam 2 REAL outcomes hon."""
        if not self.ml:
            return {}
        scores = {}
        for key, arm in self.ml.data.get("arms", {}).items():
            n_real = int(arm.get("n", 0) or 0)
            if n_real < 2:
                continue
            mean, _n_eff, _n = self.ml._eff_stats(arm)
            pillar = key.split("::", 1)[0]
            scores.setdefault(pillar, []).append(mean)
        out = {}
        for pillar, means in scores.items():
            out[pillar] = round(sum(means) / len(means), 3)
        return out

    # ── human-mind layer: momentum / slump / variety ──
    def _outcome_series(self, n: int = 15) -> list:
        """Merge reward+penalty logs into one time-ordered outcome series."""
        if not self.ml:
            return []
        seq = []
        for r in self.ml.data.get("reward_log", [])[-n:]:
            seq.append((r.get("ts", ""), r.get("reward", 0)))
        for p in self.ml.data.get("penalty_log", [])[-n:]:
            seq.append((p.get("ts", ""), -abs(p.get("penalty", 0))))
        seq.sort(key=lambda x: x[0])
        return seq[-n:]

    @staticmethod
    def _momentum_of(series: list) -> str:
        if not series:
            return "cold_start"
        tail = [v for _, v in series[-4:]]
        wins = sum(1 for v in tail if v > 0.5)
        losses = sum(1 for v in tail if v <= 0.2)
        if wins >= 3:
            return "hot"
        if losses >= 3:
            return "slump"
        return "steady"

    def decide(self) -> StrategyState:
        """Run one tuning pass and persist the new state."""
        stats = self._rolling(20)
        s = self.state
        log = []

        # 1) epsilon - exploit more as rewards improve
        old_eps = s.epsilon
        if stats["n"] >= 8:
            target_eps = 0.10 if stats["mean"] > 1.0 else (0.20 if stats["mean"] < 0.4 else 0.15)
            s.epsilon = round(old_eps + 0.4 * (target_eps - old_eps), 3)
            if abs(s.epsilon - old_eps) > 0.005:
                log.append(f"epsilon {old_eps}→{s.epsilon} (mean_reward={stats['mean']:.2f})")

        # 2) voice speed - nudge within safe USA-cadence band based on engagement
        old_speed = s.kokoro_speed
        if stats["n"] >= 10:
            if stats["engagement"] < 0.4 and s.kokoro_speed < 1.12:
                s.kokoro_speed = round(min(1.12, s.kokoro_speed + 0.01), 3)
            elif stats["engagement"] > 0.7 and s.kokoro_speed > 1.05:
                s.kokoro_speed = round(max(1.05, s.kokoro_speed - 0.01), 3)
            if abs(s.kokoro_speed - old_speed) > 0.002:
                log.append(f"voice_speed {old_speed}→{s.kokoro_speed}")

        # 3) pillar weights from real per-pillar rewards
        pscores = self._pillar_scores()
        if pscores:
            for pillar, score in pscores.items():
                prev = s.pillar_weights.get(pillar, 1.0)
                # 0.3 (bad) → 0.7 weight; 1.5+ (great) → 1.25 weight
                target = max(0.6, min(1.25, 0.8 + score * 0.35))
                s.pillar_weights[pillar] = round(prev + 0.5 * (target - prev), 3)
            log.append("pillar weights updated from real performance")

        # 4) cadence & gap - if mean reward < 0.4, reduce burst (more gap)
        old_gap = s.min_gap_hours
        if stats["n"] >= 8:
            target_gap = 4.0 if stats["mean"] < 0.4 else (2.0 if stats["mean"] > 1.2 else 3.0)
            s.min_gap_hours = round(old_gap + 0.5 * (target_gap - old_gap), 2)
            if abs(s.min_gap_hours - old_gap) > 0.1:
                log.append(f"min_gap_hours {old_gap}→{s.min_gap_hours}")

        # 5) HUMAN MIND: momentum — exploit a hot streak, heal a slump
        series = self._outcome_series()
        momentum = self._momentum_of(series)
        s.momentum = momentum
        if momentum == "hot":
            s.epsilon = round(min(s.epsilon, 0.08), 3)
            log.append(f"🔥 hot streak (wins in last 4) — exploiting winners (epsilon→{s.epsilon})")
        elif momentum == "slump":
            s.epsilon = round(max(s.epsilon, 0.25), 3)
            caps = dict(s.daily_caps)
            for p in caps:
                caps[p] = max(2, caps[p] - 1)   # less volume while cold
            s.daily_caps = caps
            s.min_gap_hours = max(s.min_gap_hours, 4.0)
            log.append(f"❄️ slump detected — fresh exploration (epsilon→{s.epsilon}, "
                       f"daily caps {caps})")
        elif momentum == "cold_start":
            s.epsilon = 0.20
            log.append("🧊 cold start — exploring broadly to find the winning formula")

        # 6) HUMAN MIND: variety guard — never 3x the same pillar in a row
        if self.ml:
            recent = [v.get("pillar") for v in self.ml.data.get("videos", [])[-3:]
                      if v.get("pillar")]
            if len(recent) == 3 and len(set(recent)) == 1:
                p = recent[0]
                s.pillar_weights[p] = round(s.pillar_weights.get(p, 1.0) * 0.7, 3)
                log.append(f"🔄 variety guard: {p} 3x in a row — weight dampened "
                           f"to {s.pillar_weights[p]} (audience needs fresh air)")

        s.last_mean_reward = round(stats["mean"], 3)
        s.last_engagement = round(stats["engagement"], 3)
        if log:
            s.decision_log.append({"ts": datetime.now(timezone.utc).isoformat(),
                                   "changes": log})
            s.decision_log = s.decision_log[-20:]
            for entry in log:
                logger.info("🎛 %s", entry)
        self.save()
        # Push pillar weights into the ML store so the bandit actually uses them
        if self.ml and self.ml.store_ok:
            try:
                self.ml.data["pillar_weights"] = dict(s.pillar_weights)
                self.ml.data["strategy"] = {
                    "momentum": s.momentum, "epsilon": s.epsilon,
                    "min_gap_hours": s.min_gap_hours,
                    "daily_caps": s.daily_caps,
                    "updated_at": s.updated_at,
                }
                self.ml.save()
            except Exception as exc:
                logger.warning("Could not sync strategy to ML store: %s", exc)
        self.write_notes()
        return s

    def write_notes(self) -> None:
        """Human-readable strategy journal (the ML's 'why' — like a planner's diary)."""
        s = self.state
        best = self.ml.best_formulas(3) if self.ml else []
        lines = [
            "# 🧠 Strategy Notes (auto — Strategy Director)",
            "",
            f"*Updated: {datetime.now(timezone.utc).isoformat()}*",
            "",
            f"**Momentum:** {s.momentum}",
            f"**Mean reward (last 20):** {s.last_mean_reward}  |  "
            f"**Engagement:** {s.last_engagement}",
            "",
            "**Current settings:**",
            f"- epsilon (exploration): {s.epsilon}",
            f"- voice speed: {s.kokoro_speed}",
            f"- min gap between posts: {s.min_gap_hours}h",
            f"- daily caps: {s.daily_caps}",
            "",
            "**Top formulas right now:**",
        ]
        if best:
            for b in best:
                lines.append(f"- `{b['pillar']}` / `{b['hook_style']}` — "
                             f"mean {b['mean']} (n={b['n']})")
        else:
            lines.append("- still exploring (not enough data yet)")
        lines += ["", "**Recent decisions (kyun kya kar raha hoon):**"]
        for d in s.decision_log[-8:]:
            lines.append(f"- {d.get('ts', '')[:16]}: {', '.join(d.get('changes', []))}")
        lines += [
            "",
            "---",
            "_This file is the ML's human-readable memory of WHY it is doing "
            "what it is doing. Koi bhi video/post is 'soch' ke hisaab se banti hai._",
        ]
        out = "\n".join(lines)
        try:
            self.notes_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.notes_path.with_suffix(".tmp")
            tmp.write_text(out, encoding="utf-8")
            os.replace(tmp, self.notes_path)
        except OSError as exc:
            logger.warning("notes write failed: %s", exc)

    def apply_to_env(self) -> None:
        """Push decided values into the process environment so TTS/scheduler/ml pick them up."""
        s = self.state
        os.environ["KOKORO_SPEED"] = str(s.kokoro_speed)
        os.environ["MIN_POST_GAP_HOURS"] = str(s.min_gap_hours)
        # epsilon/weights consumed by ML via override helper below
        os.environ["CD_EPSILON"] = str(s.epsilon)

    def pillar_weight(self, pillar_key: str) -> float:
        return float(self.state.pillar_weights.get(pillar_key, 1.0))


def current_director(ml=None) -> StrategyDirector:
    return StrategyDirector(ml=ml)
