#!/usr/bin/env python3
"""
Coercion Files — FB / IG Old-Content Cleanup (runs in CI with secrets).

Actions:
  list     — print all FB page videos + IG media with age & views/plays
  cleanup  — DELETE posts older than 14 days with < 5 views/plays.
             NEVER touches anything newer than 7 days.

Rationale: dead 0-view posts from the old niche dilute the page's topic
signal and make the grid look abandoned; removing them re-sharpens the
algorithm's understanding of the page. (Watch-time-contributing or viral
old posts are kept automatically by the views threshold.)
"""

import logging
import os
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

logging.basicConfig(level=logging.ERROR)
V = "v25.0"
NOW = datetime.now(timezone.utc)

OLD_DAYS = 14        # older than this = candidate
SAFE_DAYS = 7        # newer than this = untouchable
MIN_VIEWS = 5        # keep anything that ever got traction
DELETE_MANIFEST = Path(os.environ.get("SOCIAL_DELETE_MANIFEST", "data/social_delete_manifest.json"))


def age_days(ts: str) -> float:
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return (NOW - dt).total_seconds() / 86400
    except Exception:
        return 999


def fb_videos(tok, page):
    out, url = [], f"https://graph.facebook.com/{V}/{page}/videos"
    while url:
        r = requests.get(url, params={"access_token": tok,
                                      "fields": "id,title,created_time,views",
                                      "limit": 100}, timeout=30)
        r.raise_for_status()
        d = r.json()
        out += d.get("data", [])
        url = d.get("paging", {}).get("next")
    return out


def ig_media(tok, ig):
    out, url = [], f"https://graph.facebook.com/{V}/{ig}/media"
    while url:
        r = requests.get(url, params={"access_token": tok,
                                      "fields": "id,media_type,timestamp,permalink",
                                      "limit": 50}, timeout=30)
        r.raise_for_status()
        d = r.json()
        out += d.get("data", [])
        url = d.get("paging", {}).get("next")
    for m in out:  # fetch plays per media
        try:
            r = requests.get(f"https://graph.facebook.com/{V}/{m['id']}/insights",
                             params={"access_token": tok, "metric": "plays"},
                             timeout=30)
            vals = r.json().get("data", [{}])[0].get("values", [])
            m["plays"] = vals[0].get("value", 0) if vals else 0
        except Exception:
            m["plays"] = 0
    return out


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else "list"
    if action == "cleanup":
        confirmed = os.environ.get("CONFIRM_SOCIAL_DELETE", "0").strip().lower()
        if confirmed not in {"1", "true", "yes", "on"}:
            print("❌ cleanup blocked: set CONFIRM_SOCIAL_DELETE=1 after reviewing the dry-run list")
            return 2
    tok = os.environ.get("FB_ACCESS_TOKEN", "")
    page = os.environ.get("FB_PAGE_ID", "")
    ig = os.environ.get("IG_BUSINESS_ACCOUNT_ID", "")
    itok = os.environ.get("IG_ACCESS_TOKEN", "") or tok

    print("═" * 66)
    print(f"🧹 SOCIAL CLEANUP ({action}) — rule: age>{OLD_DAYS}d & views<{MIN_VIEWS}, "
          f"safe<{SAFE_DAYS}d")
    print("═" * 66)

    candidates = []

    # ── FACEBOOK ──
    print("\n▶ FACEBOOK PAGE VIDEOS")
    if not tok or not page:
        print("  ❌ no credentials")
    else:
        try:
            for m in fb_videos(tok, page):
                a = age_days(m.get("created_time", ""))
                v = int(m.get("views", 0) or 0)
                tag = ""
                if a > OLD_DAYS and v < MIN_VIEWS and a > SAFE_DAYS:
                    tag = "→ DELETE" if action == "cleanup" else "→ would delete"
                    candidates.append({"platform": "facebook", "id": m["id"],
                                       "age_days": round(a, 2), "views": v})
                    if action == "cleanup":
                        dr = requests.delete(
                            f"https://graph.facebook.com/{V}/{m['id']}",
                            params={"access_token": tok}, timeout=30)
                        dr.raise_for_status()
                print(f"  {m['id']}  age={a:5.0f}d views={v:4} {tag} | "
                      f"{(m.get('title') or '(no title)')[:40]}")
        except Exception as e:
            print("  ❌", str(e)[:160])

    # ── INSTAGRAM ──
    print("\n▶ INSTAGRAM MEDIA")
    if not ig or not itok:
        print("  ❌ no credentials")
    else:
        try:
            for m in ig_media(itok, ig):
                a = age_days(m.get("timestamp", ""))
                p = int(m.get("plays", 0) or 0)
                tag = ""
                if a > OLD_DAYS and p < MIN_VIEWS and a > SAFE_DAYS:
                    tag = "→ DELETE" if action == "cleanup" else "→ would delete"
                    candidates.append({"platform": "instagram", "id": m["id"],
                                       "age_days": round(a, 2), "plays": p})
                    if action == "cleanup":
                        dr = requests.delete(
                            f"https://graph.facebook.com/{V}/{m['id']}",
                            params={"access_token": itok}, timeout=30)
                        dr.raise_for_status()
                print(f"  {m['id']}  age={a:5.0f}d plays={p:4} {tag} | "
                      f"{m.get('media_type')} {m.get('permalink', '')[-24:]}")
        except Exception as e:
            body = getattr(getattr(e, "response", None), "text", "")
            print("  ❌", str(e)[:120], "|", body[:300])

    if candidates:
        DELETE_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
        DELETE_MANIFEST.write_text(json.dumps({
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "candidates": candidates,
        }, indent=2), encoding="utf-8")
        print(f"\nManifest: {DELETE_MANIFEST}")
    print("\n✅ done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
