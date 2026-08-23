#!/usr/bin/env python3
"""
Coercion Files — Facebook duplicate video detector & remover.

Ek hi title ki multiple videos ko pakarta hai, views ke hisaab se sab se
zyada-views wali copy rakhta hai, baqi DELETE karta hai (--apply se).

Default dry-run: sirf report, delete nahi karta.
Usage:
  python scripts/fb_dedupe.py            # dry-run, dekho kaunsi delete hogi
  python scripts/fb_dedupe.py --apply    # actually delete duplicate copies
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

V = "v25.0"
GRAPH = "https://graph.facebook.com"


def get(url, params):
    r = requests.get(url, params=params, timeout=60)
    if r.status_code >= 400:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:300]}")
    return r.json()


def list_videos(tok, page):
    out, url = [], f"{GRAPH}/{V}/{page}/videos"
    params = {"access_token": tok,
              "fields": "id,title,description,created_time,views",
              "limit": 100}
    while url:
        d = get(url, params)
        out += d.get("data", [])
        url = d.get("paging", {}).get("next")
        params = None
    return out


def delete_video(tok, vid):
    r = requests.delete(f"{GRAPH}/{V}/{vid}", params={"access_token": tok}, timeout=60)
    if r.status_code >= 400:
        raise RuntimeError(f"delete {vid} HTTP {r.status_code}: {r.text[:200]}")
    return r.json()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="actually delete duplicates (default: dry-run)")
    args = ap.parse_args()
    if args.apply:
        confirmed = os.environ.get("CONFIRM_FB_DELETE", "0").strip().lower()
        if confirmed not in {"1", "true", "yes", "on"}:
            sys.exit("--apply blocked: set CONFIRM_FB_DELETE=1 after reviewing the dry-run")

    tok = os.environ.get("FB_ACCESS_TOKEN", "")
    page = os.environ.get("FB_PAGE_ID", "")
    if not tok or not page:
        sys.exit("FB_PAGE_ID / FB_ACCESS_TOKEN required")

    vids = list_videos(tok, page)
    print(f"Total videos on page: {len(vids)}\n")

    # Group by normalized title (fall back to description)
    groups = {}
    for v in vids:
        title = (v.get("title") or v.get("description") or "(no title)").strip()
        key = title.lower()
        groups.setdefault(key, []).append(v)

    to_delete = []
    print("=" * 70)
    for _key, copies in groups.items():
        if len(copies) < 2:
            continue
        copies.sort(key=lambda x: int(x.get("views", 0) or 0), reverse=True)
        keep = copies[0]
        dups = copies[1:]
        print(f"DUPLICATE: {keep.get('title') or '(no title)'}")
        print(f"  ✅ KEEP  id={keep['id']}  views={keep.get('views',0)}  "
              f"created={keep.get('created_time','')[:10]}")
        for d in dups:
            print(f"  🗑️  DEL   id={d['id']}  views={d.get('views',0)}  "
                  f"created={d.get('created_time','')[:10]}")
            to_delete.append(d)
        print()

    if not to_delete:
        print("Koi duplicate nahi mili — sab clear.")
        return

    print("=" * 70)
    manifest = Path(os.environ.get("FB_DELETE_MANIFEST", "data/fb_delete_manifest.json"))
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps({
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "action": "apply" if args.apply else "dry-run",
        "keep": [copies[0].get("id") for copies in groups.values() if copies],
        "to_delete": to_delete,
    }, indent=2), encoding="utf-8")
    print(f"Manifest: {manifest}")
    if not args.apply:
        print(f"DRY-RUN: {len(to_delete)} duplicate(s) delete hongi. "
              f"Review manifest, then set CONFIRM_FB_DELETE=1 for --apply")
        return

    print(f"Deleting {len(to_delete)} duplicate(s)...")
    for d in to_delete:
        try:
            delete_video(tok, d["id"])
            print(f"  ✅ deleted {d['id']} "
                  f"({(d.get('title') or '')[:40]})")
        except Exception as e:
            print(f"  ❌ {d['id']}: {e}")
    print("Done.")


if __name__ == "__main__":
    raise SystemExit(main())
