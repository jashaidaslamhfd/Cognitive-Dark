#!/usr/bin/env python3
"""
Coercion Files — BOOST Existing Content (V2.9.8).

Pehle se uploaded videos par views laane ke liye 3 real levers (koi hack nahi,
YouTube ke allowed API operations):

  1. UNSTICK PRIVATE/SCHEDULED videos → public.
     (Pipeline private+publishAt se upload karti hai; agar schedule na chale
      to video hamesha private rehti hai = ZERO impressions = ZERO views.
      Ye views na aane ki SAB SE BADI chhupi hui wajah hai.)

  2. SEO BOOST metadata on existing videos:
     - Title: viral formula (question/stop/warning) + search keyword
       (e.g. pillar ka top search term) agar missing ho.
     - Description: keyword-dense pehli 2 lines + CTA + educational
       disclaimer (agar missing ho).
     - Tags: pillar + niche keywords add (agar missing ho).
     (YouTube search/discovery par metadata ka asar hota hai.)

  3. PLAYLIST: "Coercion Files — Psychology Shorts" bana kar saari public
     videos add — channel organization signal + "up next" autoplay chain
     (darshan ek video se doosri par jate hain = watch time signal).

Saath hi har video ke views ka BEFORE/AFTER report deta hai.

Usage:
  python scripts/boost_existing.py            # dry-run report
  python scripts/boost_existing.py --apply    # asal changes karo
"""

import argparse
import json
import logging
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("boost")

from config.settings import PILLARS

PLAYLIST_TITLE = "Coercion Files — Psychology Shorts"

POWER_WORDS = ["Stop", "Never", "Secret", "Hidden", "Exposed", "Truth", "Warning",
               "Nobody Tells You", "Why", "How", "Instantly"]
EDUCATIONAL_DISCLAIMER = (
    "For educational purposes only — learn to recognize and protect yourself. "
    "Not a substitute for professional advice.")
CTA = "Follow Coercion Files for the psychology they don't teach you in school."


def resolve_creds():
    cid = os.environ.get("GOOGLE_CLIENT_ID")
    csec = os.environ.get("GOOGLE_CLIENT_SECRET")
    rt = os.environ.get("REFRESH_TOKEN")
    if cid and csec and rt:
        return {"client_id": cid, "client_secret": csec, "refresh_token": rt,
                "token_uri": "https://oauth2.googleapis.com/token",
                "scopes": ["https://www.googleapis.com/auth/youtube.upload",
                           "https://www.googleapis.com/auth/youtube.readonly",
                           "https://www.googleapis.com/auth/youtube"],
                "type": "authorized_user"}
    raw = os.environ.get("YOUTUBE_CREDENTIALS", "")
    if not raw:
        return None
    if os.path.exists(raw):
        return json.loads(Path(raw).read_text(encoding="utf-8"))
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def get_service():
    info = resolve_creds()
    if not info:
        sys.exit("YouTube credentials nahi mile (GOOGLE_CLIENT_ID/SECRET/REFRESH_TOKEN)")
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    creds = Credentials.from_authorized_user_info(info)
    if (creds.expired or not creds.valid) and creds.refresh_token:
        creds.refresh(Request())
    return build("youtube", "v3", credentials=creds)


def all_upload_ids(yt):
    ch = yt.channels().list(part="contentDetails", mine=True).execute()["items"][0]
    upl = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    ids, token = [], None
    while True:
        r = yt.playlistItems().list(part="contentDetails", playlistId=upl,
                                    maxResults=50, pageToken=token).execute()
        ids += [i["contentDetails"]["videoId"] for i in r.get("items", [])]
        token = r.get("nextPageToken")
        if not token:
            break
    return ids


def fetch_videos(yt, ids):
    out = []
    for s in range(0, len(ids), 50):
        r = yt.videos().list(part="snippet,status,statistics,contentDetails",
                             id=",".join(ids[s:s + 50])).execute()
        out += r.get("items", [])
    return out


def pillar_keyword(title):
    """Find the best pillar search keyword for a title, or None."""
    t = title.lower()
    best, kw = None, None
    for p in PILLARS:
        for term in p.get("search_terms", []):
            if term in t:
                return term
        if best is None:
            best = p["key"]
            kw = p.get("search_terms", [""])[0]
    # fallback: keyword by topic words
    for w in ("cult", "scam", "gaslight", "narcissist", "stoic", "lie", "mind control",
              "brainwash", "propaganda", "mkultra"):
        if w in t:
            return w + " psychology"
    return kw


def boost_title(old, keyword):
    """Viral-formula + keyword title. Returns new title (≤100 chars)."""
    t = (old or "").strip()
    if not t:
        return t
    # already has keyword? keep, just tidy
    has_kw = keyword and keyword.lower() in t.lower()
    # ensure a power/question/stop start
    starts_power = bool(re.match(r"^(stop|never|why|how|what|the|this|warning|secret|they)",
                                 t, re.I))
    new = t
    if not has_kw and keyword:
        new = f"{t[:70]} | {keyword.title()}"[:100]
    elif not starts_power:
        prefix = "Stop — " if re.search(r"they|you|people", t, re.I) else "Why — "
        new = f"{prefix}{t}"[:100]
    return new if new != t else t


def boost_description(old, keyword):
    d = (old or "").strip()
    kw_line = f"{keyword.title()} psychology: how manipulation works, why it works " \
              f"on you, and how to protect yourself." if keyword else ""
    parts = [p for p in (kw_line, d, CTA, EDUCATIONAL_DISCLAIMER) if p]
    return "\n\n".join(parts)[:4900]


def boost_tags(old, keyword):
    tags = [x.strip() for x in (old or []) if x and x.strip()]
    add = [keyword, f"{keyword} psychology", "psychology facts", "dark psychology",
           "manipulation", "self improvement"] if keyword else []
    seen = set(t.lower() for t in tags)
    for a in add:
        if a.lower() not in seen:
            tags.append(a)
            seen.add(a.lower())
    total, out = 0, []
    for t in tags:
        if total + len(t) + 1 > 490:
            break
        out.append(t)
        total += len(t) + 1
    return out


def ensure_playlist(yt, apply):
    """Find or create the playlist; return playlist_id."""
    pls, token = [], None
    while True:
        r = yt.playlists().list(part="snippet,status", mine=True,
                                maxResults=50, pageToken=token).execute()
        pls += r.get("items", [])
        token = r.get("nextPageToken")
        if not token:
            break
    for pl in pls:
        if pl["snippet"]["title"] == PLAYLIST_TITLE:
            return pl["id"]
    if not apply:
        return None
    r = yt.playlists().insert(part="snippet,status", body={
        "snippet": {"title": PLAYLIST_TITLE,
                    "description": "Coercion Files — daily psychology shorts on "
                                   "cults, con artists, coercion & self-defense."},
        "status": {"privacyStatus": "public"}}).execute()
    return r["id"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true", help="asal changes karo (default: dry-run)")
    ap.add_argument("--limit", type=int, default=200, help="max videos scan (default 200)")
    args = ap.parse_args()
    apply = args.apply
    if apply:
        confirmed = os.environ.get("CONFIRM_BOOST_APPLY", "0").strip().lower()
        if confirmed not in {"1", "true", "yes", "on"}:
            print("❌ --apply blocked: set CONFIRM_BOOST_APPLY=1 after reviewing the dry-run report")
            return 2

    yt = get_service()
    ids = all_upload_ids(yt)[-args.limit:]
    print(f"📼 {len(ids)} uploaded videos mile\n")
    if not ids:
        print("Koi video nahi mili.")
        return 0

    vids = fetch_videos(yt, ids)
    print(f"{'ID':<12} {'STATUS':<9} {'VIEWS':<8} {'ACTIONS':<40}")
    print("-" * 80)
    unstuck = seo_boosted = 0
    playlist_id = ensure_playlist(yt, apply)
    added_to_pl = 0
    already_in_pl = set()

    if playlist_id:
        # existing playlist items (naya banaya hua playlist propagate hone mein
        # thora waqt leta hai — 404 aaye to khali maano)
        token = None
        try:
            while True:
                r = yt.playlistItems().list(part="contentDetails",
                                            playlistId=playlist_id,
                                            maxResults=50, pageToken=token).execute()
                for it in r.get("items", []):
                    already_in_pl.add(it["contentDetails"]["videoId"])
                token = r.get("nextPageToken")
                if not token:
                    break
        except Exception as exc:
            logger.warning("playlist items list failed (fresh playlist?): %s", exc)

    for v in vids:
        vid = v["id"]
        st = v.get("status", {})
        sn = v.get("snippet", {})
        stat = v.get("statistics", {})
        views = int(stat.get("viewCount", 0) or 0)
        status = st.get("privacyStatus", "?")
        title = sn.get("title", "")
        actions = []

        # 1) unstick private/scheduled-past (STATUS-only update)
        if status != "public":
            publish_at = st.get("publishAt", "")
            past = True
            if publish_at:
                try:
                    pa = datetime.fromisoformat(publish_at.replace("Z", "+00:00"))
                    past = pa <= datetime.now(timezone.utc)
                except ValueError:
                    past = True
            if past:
                if apply:
                    try:
                        yt.videos().update(part="status", body={
                            "id": vid, "status": {"privacyStatus": "public"}}).execute()
                        actions.append("PUBLIC!")
                        status = "public"
                    except Exception as exc:
                        actions.append("PUB-ERR")
                        logger.warning("unstick %s failed: %s", vid, exc)
                else:
                    actions.append("would-public")
                unstuck += 1

        # 2) SEO metadata boost (public ya private — dono)
        kw = pillar_keyword(title)
        new_title = boost_title(title, kw) if kw else None
        new_desc = boost_description(sn.get("description", ""), kw) if kw else None
        new_tags = boost_tags(sn.get("tags", []), kw) if kw else None
        changed = (new_title and new_title != title) or \
                  (new_desc and new_desc != sn.get("description", "")) or \
                  (new_tags and new_tags != sn.get("tags", []))
        if changed:
            if apply:
                try:
                    # SNIPPET-only update (categoryId required for update)
                    yt.videos().update(part="snippet", body={
                        "id": vid,
                        "snippet": {"title": new_title or title,
                                    "description": new_desc or sn.get("description", ""),
                                    "tags": new_tags or sn.get("tags", []),
                                    "categoryId": "27",
                                    "defaultLanguage": "en",
                                    "defaultAudioLanguage": "en-US"}}).execute()
                    actions.append("SEO+")
                except Exception as exc:
                    actions.append("SEO-ERR")
                    logger.warning("SEO update %s failed: %s", vid, exc)
            else:
                actions.append("would-SEO")
            seo_boosted += 1

        # 3) playlist (insert failure non-fatal — continue boosting others)
        if status == "public" and playlist_id and vid not in already_in_pl:
            if apply:
                try:
                    yt.playlistItems().insert(part="snippet", body={
                        "snippet": {"playlistId": playlist_id, "resourceId": {
                            "kind": "youtube#video", "videoId": vid}}}).execute()
                    actions.append("PL+")
                except Exception as exc:
                    actions.append("PL-ERR")
                    logger.warning("playlist add %s failed: %s", vid, exc)
            else:
                actions.append("would-PL")
            added_to_pl += 1

        print(f"{vid:<12} {status:<9} {views:<8} {','.join(actions) if actions else '-':<40} {title[:40]}")

    print("\n" + "=" * 80)
    if apply:
        print(f"✅ DONE — {unstuck} private→public, {seo_boosted} SEO boost, "
              f"{added_to_pl} playlist add")
    else:
        print(f"🔎 DRY-RUN — {unstuck} would-public, {seo_boosted} would-SEO, "
              f"{added_to_pl} would-PL. --apply karo to asal changes.")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    sys.exit(main())
