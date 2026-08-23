#!/usr/bin/env python3
"""ReleaseGate — sab guards ka conductor (V3.5).

Flow:
  payload → [producer self-scores STRIP] → 8 independent guards (parallel
  cheezein, ek ek kar ke) → USASupervisor → RELEASED / HELD

Modes (env GATE_MODE):
  strict (default) — koi bhi guard FAIL/UNKNOWN ya supervisor violation
                     = video HELD (upload nahi)
  warn             — report banti hai, publishing STILL blocked by default
  off              — report bypass requested, publishing STILL blocked by default

Publishing bypass additionally requires ALLOW_UNSAFE_PUBLISH=1 and should
only be used in a separately protected operator-approved environment.

Fail-CLOSED: guard agar measure hi na kar sake (UNKNOWN) to video block
hoti hai — "pata nahi" kabhi "pass" nahi hota.

Reports:
  data/gate_report.json — machine-readable (har verdict + evidence)
  data/gate_report.md  — human-readable audit trail
"""

from __future__ import annotations

import copy
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from config.settings import DATA_DIR

logger = logging.getLogger("guards.gate")

PRODUCER_SCORE_KEYS = ("script_quality", "hook_score", "ctr_score",
                       "title_ctr_score", "virality_grade")

CORE_GUARDS = ("script", "hook", "voice", "caption", "video")


@dataclass
class GateReport:
    platform: str
    mode: str
    verdicts: list = field(default_factory=list)
    supervisor: dict = field(default_factory=dict)
    released: bool = False
    grade: str = "F"
    generated_at: str = ""
    written: list = field(default_factory=list)

    def blocking_reasons(self) -> list:
        out = [f"{v.guard}: {v.reason}" for v in self.verdicts if v.blocking]
        out += [f"supervisor: {v}" for v in
                (self.supervisor or {}).get("violations", [])]
        return out

    def core_blocked(self) -> bool:
        return any(v.guard in CORE_GUARDS and v.blocking for v in self.verdicts)


class ReleaseGate:
    def __init__(self, mode: str = None, report_dir=None, observer=None):
        self.mode = (mode or os.environ.get("GATE_MODE", "strict")).strip().lower()
        self.report_dir = Path(report_dir or DATA_DIR)
        self.observer = observer  # injected for tests

    # ── guard construction ────────────────────────────────────────
    def _guards(self, platform: str) -> list:
        from guards.caption_guard import CaptionGuard
        from guards.ctr_guard import CTRGuard
        from guards.hook_guard import HookGuard
        from guards.script_guard import ScriptGuard
        from guards.seo_guard import SEOGuard
        from guards.video_guard import VideoGuard
        from guards.views_guard import ViewsGuard
        from guards.voice_guard import VoiceGuard
        return [
            ScriptGuard(self.observer),
            HookGuard(self.observer),
            VoiceGuard(self.observer),
            CaptionGuard(self.observer),
            VideoGuard(self.observer),
            SEOGuard(self.observer),
            CTRGuard(self.observer),
            ViewsGuard(self.observer),
        ]

    # ── producer-score strip (independence guarantee) ─────────────
    @staticmethod
    def _sanitize(payload: dict) -> dict:
        """Guards ko RAW reality milti hai — producer ki self-praise nahi."""
        out = copy.deepcopy(payload)
        script = out.get("script")
        if isinstance(script, dict):
            for k in PRODUCER_SCORE_KEYS:
                script.pop(k, None)
            out["script"] = script
        out.pop("ml_scores", None)
        out.pop("producer_notes", None)
        return out

    # ── main entry ────────────────────────────────────────────────
    def evaluate(self, payload: dict) -> GateReport:
        platform = payload.get("platform") or "youtube"
        report = GateReport(platform=platform, mode=self.mode,
                            generated_at=datetime.now(timezone.utc).isoformat())

        if self.mode == "off":
            unsafe_allowed = os.environ.get("ALLOW_UNSAFE_PUBLISH", "0").strip().lower() in {
                "1", "true", "yes", "on"
            }
            report.released = unsafe_allowed
            report.grade = "OFF" if unsafe_allowed else "F"
            report.supervisor = {
                "released": unsafe_allowed,
                "violations": [] if unsafe_allowed else [
                    "GATE_MODE=off requires ALLOW_UNSAFE_PUBLISH=1"
                ],
                "note": "GATE_MODE=off",
            }
            report.written = self._write_reports(report)
            self._log(report)
            return report

        clean = self._sanitize(payload)
        verdicts = []
        for guard in self._guards(platform):
            try:
                v = guard.check(clean)
            except Exception as exc:  # guard crash = UNKNOWN (fail-closed)
                logger.error("Guard %s crashed: %s", guard.name, exc)
                v = guard._v("UNKNOWN", f"guard crashed: {exc}",
                             {"error": str(exc)[:200]})
            verdicts.append(v)
        report.verdicts = verdicts

        from guards.supervisor import USASupervisor
        sup = USASupervisor().review(clean, verdicts)
        report.supervisor = sup

        if self.mode == "strict":
            report.released = bool(sup.get("released"))
        else:
            unsafe_allowed = os.environ.get("ALLOW_UNSAFE_PUBLISH", "0").strip().lower() in {
                "1", "true", "yes", "on"
            }
            report.released = bool(unsafe_allowed and sup.get("released"))
            if not unsafe_allowed:
                sup.setdefault("violations", []).append(
                    f"GATE_MODE={self.mode} is audit-only; publishing requires "
                    "ALLOW_UNSAFE_PUBLISH=1"
                )
                report.supervisor = sup
        report.grade = sup.get("grade", "F")

        report.written = self._write_reports(report)
        self._log(report)
        return report

    # ── reporting ─────────────────────────────────────────────────
    def _write_reports(self, report: GateReport) -> list:
        written = []
        data = {
            "platform": report.platform, "mode": report.mode,
            "released": report.released, "grade": report.grade,
            "generated_at": report.generated_at,
            "verdicts": [v.to_dict() for v in report.verdicts],
            "supervisor": report.supervisor,
        }
        self.report_dir.mkdir(parents=True, exist_ok=True)
        try:
            jp = self.report_dir / f"gate_report_{report.platform}.json"
            serialized = json.dumps(data, indent=2, ensure_ascii=False)
            jp.write_text(serialized, encoding="utf-8")
            latest = self.report_dir / "gate_report.json"
            latest.write_text(serialized, encoding="utf-8")
            written.extend([str(jp), str(latest)])
        except OSError as exc:
            logger.warning("gate json report write failed: %s", exc)
        try:
            mp = self.report_dir / f"gate_report_{report.platform}.md"
            markdown = self._markdown(report, data)
            mp.write_text(markdown, encoding="utf-8")
            latest = self.report_dir / "gate_report.md"
            latest.write_text(markdown, encoding="utf-8")
            written.extend([str(mp), str(latest)])
        except OSError as exc:
            logger.warning("gate md report write failed: %s", exc)
        return written

    @staticmethod
    def _markdown(report: GateReport, data: dict) -> str:
        icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌", "UNKNOWN": "❓"}
        lines = [
            f"# 🛂 Release Gate Report — {report.platform.upper()}",
            "",
            f"- **Decision:** {'🟢 RELEASED' if report.released else '🔴 HELD'}  "
            f"(grade **{report.grade}**, mode {report.mode})",
            f"- **Time:** {report.generated_at}",
            "",
            "| Guard | Status | Reason |",
            "|---|---|---|",
        ]
        for v in report.verdicts:
            lines.append(f"| {icon.get(v.status, '?')} {v.guard} | "
                         f"{v.status} | {v.reason[:160]} |")
        sup = report.supervisor or {}
        lines += ["", "## Supervisor (USA audience, fail-closed)", ""]
        for v in sup.get("violations", []):
            lines.append(f"- ❌ {v}")
        for n in sup.get("notes", []):
            lines.append(f"- ℹ️ {n}")
        if not sup.get("violations"):
            lines.append("- ✅ Independence audit + USA calibration pass")
        lines += ["", "## Evidence", "", "```json",
                  json.dumps({v.guard: v.evidence for v in report.verdicts},
                             ensure_ascii=False, indent=2, default=str)[:8000],
                  "```", ""]
        return "\n".join(lines)

    def _log(self, report: GateReport) -> None:
        fails = [v.guard for v in report.verdicts if v.blocking]
        warns = [v.guard for v in report.verdicts if v.status == "WARN"]
        if report.released:
            logger.info("🛂 GATE [%s]: %s RELEASED grade=%s%s",
                        report.platform.upper(),
                        "🟢" if self.mode != "warn" else "⚠️(warn-mode)",
                        report.grade,
                        f" warns={warns}" if warns else "")
        else:
            logger.error("🛂 GATE [%s]: 🔴 HELD grade=%s blocked=%s "
                         "violations=%s",
                         report.platform.upper(), report.grade, fails,
                         report.supervisor.get("violations", []))

    # ── payload persistence (for scripts/run_gate.py) ────────────
    @staticmethod
    def serialize_payload(payload: dict) -> dict:
        out = copy.deepcopy(payload)
        out.pop("ml", None)
        return out

    def save_payload(self, payload: dict, out_dir=None) -> str:
        import json as _json
        out_dir = Path(out_dir or self.report_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "gate_payload.json"
        path.write_text(_json.dumps(self.serialize_payload(payload), indent=2,
                                    ensure_ascii=False, default=str),
                        encoding="utf-8")
        return str(path)

    def evaluate_from_file(self, path) -> list:
        """Re-run the gate on a saved payload file (all platforms)."""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        # fresh ML store inject karo taake views-guard REAL outcomes dekh sake
        try:
            from ml_engine import LearningSystem
            ml = LearningSystem()
        except Exception:
            ml = None
        reports = []
        for plat, payload in data.items():
            payload["platform"] = plat
            payload["ml"] = ml
            reports.append(self.evaluate(payload))
        return reports
