#!/usr/bin/env python3
"""
Coercion Files — 2026 Algorithm Video Repair Tool.

Pehle se upload ki gayi saari videos ko scan karta hai aur har platform ke
2026 algorithm signals ke hisaab se optimize karta hai:

YOUTUBE (2026 Shorts Algorithm):
  ✅ Private/scheduled past-due → PUBLIC (zero views ki #1 wajah)
  ✅ Title CTR boost: number/question/stop/warning pattern + keyword
  ✅ Description: first 2 lines keyword-dense + chapters + CTA + disclaimer
  ✅ Tags: ≤500 chars, pillar + niche keywords
  ✅ Thumbnail review
  ✅ Playlist: "Coercion Files — Psychology Shorts" (autoplay chain)
  ✅ End-screen + info card signals (metadata)

FACEBOOK (2026 Reels Algorithm):
  ✅ Public post check (private = zero reach)
  ✅ First-3s hook caption
  ✅ 5-8 relevant hashtags
  ✅ Comment CTA ("What would you add? Comments mein batao")
  ✅ Share CTA
  ✅ Native 9:16 format check

INSTAGRAM (2026 Reels Algorithm):
  ✅ Account health check (business/creator, linked page)
  ✅ Save/share/replay signals
  ✅ 15-20 hashtags
  ✅ "Save this" value framing
  ✅ 9:16, <90s format

Usage:
  python scripts/repair_all_videos.py             # dry-run report
  python scripts/repair_all_videos.py --apply     # asal changes
  python scripts/repair_all_videos.py --fix-public  # sirf private→public
  python scripts/repair_all_videos.py --audit     # sirf audit/report
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
logger = logging.getLogger("repair")

from config.settings import PILLARS

# ── Global trackers ───────────────────────────────────────────────

STATS = {
    "youtube": {"scanned": 0, "fixed_public": 0, "seo_boosted": 0, "playlist_add": 0,
                "thumbnail_updated": 0, "not_shorts_ready": 0,
                "total_views_before": 0, "total_views_after": 0},
    "facebook": {"scanned": 0, "fixed_public": 0, "caption_updated": 0, "hashtag_fixed": 0,
                 "total_views_before": 0, "total_views_after": 0},
    "instagram": {"scanned": 0, "account_fixed": 0, "caption_updated": 0,
                  "hashtag_fixed": 0, "total_views_before": 0,
                  "manual_fixes": 0},
}


# ═══════════════════════════════════════════════════════════════════
# YOUTUBE REPAIR
# ═══════════════════════════════════════════════════════════════════

YOUTUBE_SHORTS_MAX_SEC = 180
YOUTUBE_SHORTS_MIN_SEC = 1
YOUTUBE_SHORTS_ASPECT_MAX = 1.0  # square ok, landscape nahi
PLAYLIST_TITLE = "Coercion Files — Psychology Shorts"

POWER_WORDS = ["Stop", "Never", "Secret", "Hidden", "Exposed", "Truth", "Warning",
               "Nobody Tells You", "Why", "How", "The"]
EDUCATIONAL_DISCLAIMER = (
    "For educational purposes only — learn to recognize and protect yourself. "
    "Not a substitute for professional advice.\n\n"
    "🔍 What you'll learn:\n"
    "• The psychological exploit explained\n"
    "• How the brain trap works\n"
    "• 1-step tactical defense\n\n"
    "📌 Subscribe for daily psychology shorts — new uploads daily.\n\n"
    "#psychology #truecrime #mindcontrol #psychologyfacts"
)
CTA = "Follow Coercion Files for the psychology they don't teach you in school."


def yt_resolve_creds():
    cid = os.environ.get("GOOGLE_CLIENT_ID")
    csec = os.environ.get("GOOGLE_CLIENT_SECRET")
    rt = os.environ.get("REFRESH_TOKEN")
    if cid and csec and rt:
        return {"client_id": cid, "client_secret": csec, "refresh_token": rt,
                "token_uri": "https://oauth2.googleapis.com/token",
                "scopes": [
                    "https://www.googleapis.com/auth/youtube.upload",
                    "https://www.googleapis.com/auth/youtube.readonly",
                    "https://www.googleapis.com/auth/youtube",
                    "https://www.googleapis.com/auth/yt-analytics.readonly",
                ],
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


def yt_get_service():
    info = yt_resolve_creds()
    if not info:
        print("❌ YouTube credentials nahi mile.")
        return None
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    creds = Credentials.from_authorized_user_info(info)
    if (creds.expired or not creds.valid) and creds.refresh_token:
        creds.refresh(Request())
    if creds.expired or not creds.valid:
        print("❌ YouTube token expired aur refresh nahi ho raha.")
        return None
    return build("youtube", "v3", credentials=creds)


def yt_all_video_ids(yt):
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


def yt_fetch_videos(yt, ids):
    out = []
    for s in range(0, len(ids), 50):
        r = yt.videos().list(
            part="snippet,status,statistics,contentDetails",
            id=",".join(ids[s:s + 50])).execute()
        out += r.get("items", [])
    return out


def yt_parse_duration(iso_dur):
    import re as _re
    if not iso_dur:
        return None
    m = _re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?", iso_dur)
    if not m:
        return None
    h = int(m.group(1) or 0)
    mn = int(m.group(2) or 0)
    sec = float(m.group(3) or 0)
    return h * 3600 + mn * 60 + sec


def yt_is_shorts_ready(item):
    """Check if a video is technically eligible for Shorts feed."""
    issues = []
    cd = item.get("contentDetails", {})
    dur = yt_parse_duration(cd.get("duration", ""))
    if dur is None:
        issues.append("duration unknown")
    elif dur < YOUTUBE_SHORTS_MIN_SEC:
        issues.append(f"too short ({dur:.1f}s)")
    elif dur > YOUTUBE_SHORTS_MAX_SEC:
        issues.append(f"too long ({dur:.0f}s > {YOUTUBE_SHORTS_MAX_SEC}s)")

    # Aspect ratio from contentDetails
    if cd.get("dimension") == "2d":
        w = cd.get("width", 0)
        h = cd.get("height", 0)
        if w and h:
            ratio = w / h
            if ratio > YOUTUBE_SHORTS_ASPECT_MAX + 0.05:
                issues.append(f"landscape {w}x{h} (ratio {ratio:.2f})")

    # Privacy
    st = item.get("status", {})
    if st.get("privacyStatus") != "public":
        issues.append(f"privacy={st.get('privacyStatus')}")
    elif st.get("privacyStatus") == "public" and st.get("publishAt"):
        # Scheduled but not yet — check if past due
        try:
            pa = datetime.fromisoformat(st["publishAt"].replace("Z", "+00:00"))
            if pa > datetime.now(timezone.utc):
                issues.append(f"scheduled future {pa.isoformat()[:16]}")
        except ValueError:
            pass

    # Check for madeForKids (should be false for educational content)
    if st.get("selfDeclaredMadeForKids", False):
        issues.append("madeForKids=True (Shorts feed restricted)")

    # Embeddable check
    if st.get("embeddable") is False:
        issues.append("not embeddable")

    return issues


def _is_keyword_segment(seg: str) -> bool:
    """Kya title ka ye segment ek RECOGNIZED keyword merge hai (valid)? """
    key = seg.strip().lower().rstrip(".!?")
    if not key:
        return False
    for p in PILLARS:
        for term in p.get("search_terms", []):
            if key == term.lower():
                return True
    return key.endswith("psychology") or key.endswith("explained")


def yt_keyword_for_title(title):
    """Find matching pillar keyword for a given title."""
    t = title.lower()
    for p in PILLARS:
        for term in p.get("search_terms", []):
            if term in t:
                return term
    for w in ("cult", "scam", "gaslight", "narcissist", "stoic", "lie", "mind control",
              "brainwash", "propaganda", "mkultra", "manipulation", "psychology"):
        if w in t:
            return w + " psychology"
    return None


def _clean_legacy_title(title: str) -> str:
    """V3.6-repair-6: legacy title chains ka pura cleanup.

    Purane runs ne ye junk inject kiya tha (examples live channel se):
      • "The Truth: " / "Stop: " / "Why: " colon-prefixes
      • ": Never", ": TRAP", ": Hidden", ": Silently" power-word suffixes
      • ": Mass Psychology" double keyword merges
      • "| Mkultra Explained | ..." pipe chains

    Rules (deterministic, safe — natural titles untouched):
      A) leading "{power}: " strip jab remainder >=4 words ho
      B) pipes: sirf pehla segment (>=4 words) rehta hai
      C) >=2 colons + last segment <=4 words → last segment drop (loop)
      D) last segment single power-word → drop
    Keyword satisfaction token-based hota hai (boost mein) taake dobara
    double-merge na ho.
    """
    t = (title or "").strip()
    if not t:
        return t

    power_low = {w.lower() for w in (
        "Secret", "Instantly", "Never", "Shocking", "Hidden", "Exposed",
        "Deadly", "Silently", "Brutal", "Finally", "Nobody Tells You",
        "They Don't Want You to Know", "Revealed", "Stop", "Master",
        "BUG", "TRAP", "FLAG", "EXPOSED", "PROOF", "WARNING", "Truth")}
    prefix_low = {p.lower() for p in (
        "The Truth", "Stop", "Why", "Warning", "Never", "The Secret", "Truth")}

    # A) colon-prefixes (em-dash bhi — purane formats)
    changed = True
    while changed:
        changed = False
        # V3.6-repair-6: em-dash format mein "Why — Title" (spaces ke saath)
        # hota hai — "why—" match nahi hota. Sufixes: ": " aur " — ".
        for suffix in (": ", " — "):
            for pfx in [*prefix_low, "Don't", "Watch"]:
                if t.lower().startswith(pfx.lower() + suffix):
                    rest = t[len(pfx) + len(suffix):].strip()
                    if len(rest.split()) >= 4:
                        t = rest
                        changed = True
                        break
            if changed:
                break

    # B) pipe chains → pehla segment (jab wo substantive ho)
    parts = [p.strip() for p in t.split("|")]
    if len(parts) > 1 and len(parts[0].split()) >= 4:
        t = parts[0]

    # C) double-colon chains: last short segment drop (loop).
    # Keyword-aware (V3.6-repair-8): "Case #375: The Hook: Con Artist
    # Psychology" jaisi VALID titles ka keyword drop nahi hota (warna
    # merge use wapas add kar deta = har run par bekaar loop).
    changed = True
    while changed:
        changed = False
        segs = [p.strip() for p in t.split(":")]
        if len(segs) >= 3:
            last_low = segs[-1].lower().rstrip(".!?")
            second_low = segs[-2].lower().rstrip(".!?")
            n_words = len(segs[-1].split())
            drop = False
            if last_low in power_low:
                drop = True                       # junk power-word
            elif n_words <= 4 and second_low in power_low:
                drop = True                       # middle junk ke saath keyword redundant
            elif n_words <= 4 and not _is_keyword_segment(segs[-1]):
                drop = True                       # generic short suffix (old junk)
            if drop:
                t = ": ".join(segs[:-1]).strip()
                changed = True

    # D) trailing single power-word (": Never" / ": Hidden" style)
    changed = True
    while changed:
        changed = False
        m = re.search(r":\s*([^:]+)$", t)
        if m:
            seg = m.group(1).strip()
            if seg.lower().rstrip(".!?") in power_low:
                t = t[:m.start()].strip()
                changed = True

    return t.strip()


def yt_boost_title(title, keyword):
    """Generate CTR-optimized title for 2026 YouTube Shorts.

    V3.6-repair: legacy artifacts ("Why —", ": Never", "| Keyword") clean
    karta hai, phir natural "Hook: Keyword" merge. Idempotent.
    """
    t = _clean_legacy_title(title)
    if not t:
        return t, False

    # V3.6-repair-7: cleanup ka apna change bhi count hota hai — pehle
    # changed=False + sirf keyword-merge isay True karta tha, is liye jin
    # titles ka cleanup hua par keyword satisfied tha unki update SKIP ho
    # jati thi (title_changed False rehta tha).
    changed = t != title
    new = t

    # 1) Keyword NATURAL merge — sirf jab keyword sach mein missing ho.
    # Token-based satisfaction: agar keyword ka koi token (>=4 chars,
    # stopwords ke siwa) title mein pehle se hai, to dobara merge nahi —
    # "the Cult Recruitment Pipeline" jaisi titles par "Cult Psychology"
    # dobara add nahi hota (double-colon junk wapas nahi banta).
    if keyword:
        kw_tokens = [w for w in keyword.lower().split()
                     if len(w) >= 4 and w not in ("your", "what", "they", "that", "this")]
        satisfied = (keyword.lower() in new.lower()
                     or any(w in new.lower() for w in kw_tokens))
        if not satisfied and len(new) + len(keyword) + 2 <= 100:
            new = f"{new[:80]}: {keyword.title()}"[:100]
            changed = True

    # V3.6-repair-6: prefix-adder HATA DIYA. Ye block hi "The Truth: " /
    # "Stop: " / "Why: " junk banata tha — cleaner strip karta, ye wapas
    # jod deta (circular). Repair ka kaam sirf junk REMOVE karna hai,
    # naya inject karna nahi. Title ab waise hi chhoda jata hai jaise
    # cleanup ke baad hai — original hooks pehle se strong hain.

    return new[:100], changed


def yt_boost_description(old_desc, keyword):
    """Build 2026-optimized description.

    V3.6: IDEMPOTENT — dobara chalane par duplicate chapters/keyword-line
    nahi bante (pehle har repair run description ko aur lamba kar deta tha).
    """
    existing = (old_desc or "").strip()
    existing_low = existing.lower()
    kw_line = ""
    if keyword and keyword.lower() not in existing_low[:300]:
        kw_line = (
            f"{keyword.title()} psychology: how manipulation works, why it works "
            f"on you, and exactly how to protect yourself.\n\n"
        )

    chapters = ("⏱ CHAPTERS:\n00:00 The Hook\n00:03 What's Really Happening\n"
                "00:15 The Pattern\n00:25 How To Protect Yourself\n"
                "00:35 The Takeaway\n\n")
    if "chapters" in existing_low:
        chapters = ""   # pehle se hain — duplicate mat banao

    has_disclaimer = "educational" in existing_low
    has_cta = any(w in existing_low for w in ("subscribe", "follow", "like"))

    parts = [kw_line, chapters]
    if existing:
        # Keep existing if it has good content
        parts.append(existing)
    else:
        parts.append(f"⚠️ For educational purposes only.\n\n{CTA}")
    if not has_disclaimer:
        parts.append(EDUCATIONAL_DISCLAIMER)
    if not has_cta and not existing:
        parts.append(f"\n{CTA}")

    changed = bool(kw_line or chapters or not has_disclaimer
                   or (not has_cta and not existing))
    return "\n\n".join(p for p in parts if p).strip()[:4900], changed


def yt_boost_tags(old_tags, keyword):
    """Optimize tags for 2026 YouTube search."""
    tags = [x.strip() for x in (old_tags or []) if x and x.strip()]
    if not keyword:
        return tags, False

    additions = [
        keyword,
        f"{keyword} psychology",
        "psychology facts",
        "dark psychology",
        "manipulation",
        "self improvement",
        "mindset",
        "behavioral psychology",
    ]
    added_any = False
    for a in additions:
        if a.lower() not in {t.lower() for t in tags}:
            tags.append(a)
            added_any = True

    # Keep within 500 chars
    total, out = 0, []
    for t in tags:
        if total + len(t) + 1 > 490:
            break
        out.append(t)
        total += len(t) + 1
    return out, added_any


def yt_audit_and_repair(yt, apply=False, fix_public_only=False):
    """Scan all YouTube videos and fix per 2026 algorithm."""
    ids = yt_all_video_ids(yt)
    if not ids:
        print("❌ Koi YouTube video nahi mili channel par.")
        return

    STATS["youtube"]["scanned"] = len(ids)
    videos = yt_fetch_videos(yt, ids)
    print(f"\n{'='*78}\n📺 YOUTUBE: {len(videos)} videos scan kiye\n{'='*78}")

    total_views_before = 0
    playlist_id = None
    already_in_playlist = set()

    # Get playlist
    if apply:
        pls = []
        token = None
        while True:
            r = yt.playlists().list(part="snippet,status", mine=True,
                                    maxResults=50, pageToken=token).execute()
            pls += r.get("items", [])
            token = r.get("nextPageToken")
            if not token:
                break
        for pl in pls:
            if pl["snippet"]["title"] == PLAYLIST_TITLE:
                playlist_id = pl["id"]
                break
        if not playlist_id:
            try:
                r = yt.playlists().insert(part="snippet,status", body={
                    "snippet": {"title": PLAYLIST_TITLE,
                                "description": "Coercion Files — daily psychology shorts "
                                               "on cults, con artists, coercion & self-defense."},
                    "status": {"privacyStatus": "public"}}).execute()
                playlist_id = r["id"]
                print(f"✅ Playlist bana: {PLAYLIST_TITLE} ({playlist_id})")
            except Exception as exc:
                print(f"⚠️ Playlist create failed: {exc}")

        # Get existing playlist items
        if playlist_id:
            token = None
            try:
                while True:
                    r = yt.playlistItems().list(part="contentDetails",
                                                playlistId=playlist_id,
                                                maxResults=50, pageToken=token).execute()
                    for it in r.get("items", []):
                        already_in_playlist.add(it["contentDetails"]["videoId"])
                    token = r.get("nextPageToken")
                    if not token:
                        break
            except Exception:
                pass

    for v in videos:
        vid = v["id"]
        st = v.get("status", {})
        sn = v.get("snippet", {})
        stats = v.get("statistics", {})
        views = int(stats.get("viewCount", 0) or 0)
        total_views_before += views
        status = st.get("privacyStatus", "?")
        title = sn.get("title", "")
        desc = sn.get("description", "")
        tags = sn.get("tags", [])

        issues = yt_is_shorts_ready(v)
        # shorts-readiness issues (non-privacy/madeForKids) → counter mein
        # jama karo taake summary bata sake kitne videos Shorts-feed ke liye
        # ready NAHI hain (pehle ye variable calculate ho kar phenk diya
        # jata tha — dead code).
        if any("privacy" not in i and "madeForKids" not in i for i in issues):
            STATS["youtube"]["not_shorts_ready"] += 1
        actions = []

        # ── 1. Fix privacy (private/scheduled→public) ──
        if status != "public":
            publish_at = st.get("publishAt", "")
            is_past_due = False
            if publish_at:
                try:
                    pa = datetime.fromisoformat(publish_at.replace("Z", "+00:00"))
                    is_past_due = pa <= datetime.now(timezone.utc)
                except ValueError:
                    is_past_due = True

            if is_past_due:
                if apply:
                    try:
                        yt.videos().update(part="status", body={
                            "id": vid,
                            "status": {"privacyStatus": "public",
                                       "selfDeclaredMadeForKids": False}}).execute()
                        actions.append("🔴→PUBLIC")
                        STATS["youtube"]["fixed_public"] += 1
                        status = "public"
                    except Exception as exc:
                        actions.append(f"ERR:{exc}")
                        logger.warning("unstick %s failed: %s", vid, exc)
                else:
                    actions.append("would:PUBLIC")
            elif not is_past_due and apply and fix_public_only:
                actions.append("scheduled-future")
            elif not is_past_due:
                actions.append(f"scheduled:{publish_at[:16]}")

        # ── 2. SEO Metadata Boost ──
        keyword = yt_keyword_for_title(title)
        new_title, title_changed = yt_boost_title(title, keyword) if keyword else (title, False)
        new_desc, desc_changed = yt_boost_description(desc, keyword) if keyword else (desc, False)
        new_tags, tags_changed = yt_boost_tags(tags, keyword) if keyword else (tags, False)

        if (title_changed or desc_changed or tags_changed) and not fix_public_only:
            if apply:
                # V3.6-repair FIX: videos.update(part="snippet") ko title
                # field CHAHIYE hota hai — title ke baghair API "invalid or
                # empty video title" error deta hai (23 SEO-ERR ka root
                # cause). Title hamesha bhejo (changed ho ya na ho).
                if not (title or "").strip():
                    actions.append("SEO-skip: empty title")
                else:
                    try:
                        body = {
                            "id": vid,
                            "snippet": {
                                "title": (new_title or title)[:100],
                                "description": (new_desc or desc or "")[:4900],
                                "tags": (new_tags or tags or [])[:50],
                                "categoryId": "27",
                                "defaultLanguage": "en",
                                "defaultAudioLanguage": "en-US",
                            }
                        }
                        yt.videos().update(part="snippet", body=body).execute()
                        actions.append("SEO+")
                        STATS["youtube"]["seo_boosted"] += 1
                    except Exception as exc:
                        actions.append(f"SEO-ERR:{exc}")
                        logger.warning("SEO update %s failed: %s", vid, exc)
            else:
                actions.append("would:SEO")

        # ── 3. Playlist add ──
        if status == "public" and playlist_id and vid not in already_in_playlist:
            if apply and not fix_public_only:
                try:
                    yt.playlistItems().insert(part="snippet", body={
                        "snippet": {"playlistId": playlist_id, "resourceId": {
                            "kind": "youtube#video", "videoId": vid}}}).execute()
                    actions.append("PL+")
                    STATS["youtube"]["playlist_add"] += 1
                    already_in_playlist.add(vid)
                except Exception as exc:
                    actions.append(f"PL-ERR:{exc}")
            elif not apply:
                actions.append("would:PL")

        # Report
        issue_str = " | ".join(issues) if issues else "✅ Shorts-ready"
        print(f"  {vid} [{status:8}] views={views:<6} | {issue_str}")
        print(f"    title: {title[:60]}")
        if actions:
            print(f"    actions: {', '.join(actions)}")

    # Summary
    print(f"\n{'='*60}")
    print("YOUTUBE SUMMARY:")
    print(f"  Total videos    : {STATS['youtube']['scanned']}")
    print(f"  Total views     : {total_views_before}")
    print(f"  Not Shorts-ready: {STATS['youtube']['not_shorts_ready']}")
    print(f"  Fixed → public  : {STATS['youtube']['fixed_public']}")
    print(f"  SEO boosted     : {STATS['youtube']['seo_boosted']}")
    print(f"  Playlist added  : {STATS['youtube']['playlist_add']}")
    print(f"{'='*60}\n")


# ═══════════════════════════════════════════════════════════════════
# FACEBOOK REPAIR
# ═══════════════════════════════════════════════════════════════════

FB_HASHES_RECOMMENDED = 8
FB_HASHTAGS_BANK = [
    "#psychology", "#truecrime", "#mindcontrol", "#scams", "#gaslighting",
    "#coercivecontrol", "#stoicism", "#psychologyfacts", "#manipulation",
    "#mentalhealth", "#selfimprovement", "#bodylanguage",
]


def fb_get_service():
    tok = os.environ.get("FB_ACCESS_TOKEN", "") or os.environ.get("FACEBOOK_ACCESS_TOKEN", "")
    page = os.environ.get("FB_PAGE_ID", "") or os.environ.get("FACEBOOK_PAGE_ID", "")
    if not tok or not page:
        print("❌ FB_ACCESS_TOKEN / FB_PAGE_ID configure karein.")
        return None, None
    return tok, page


def fb_update_post_text(tok: str, vid: str, text: str) -> tuple[bool, str]:
    """FB video/post ka text update — ladder: caption → description → message.

    Page videos kabhi video-node hote hain (description editable), kabhi
    page-post hote hain (message editable). Teeno try karte hain — pehli
    kaamyabi wapas. Koi guess nahi: har field ASAL mein try hota hai.
    """
    import requests
    # V3.6-repair-10: description pehle — video nodes isi mein store
    # karte hain; caption POST par FB silent 200 deta tha bina kuch change
    # kiye (loop ka root cause)
    for field in ("description", "caption", "message"):
        try:
            r = requests.post(
                f"https://graph.facebook.com/v25.0/{vid}",
                params={"access_token": tok},
                data={field: text[:6300]},
                timeout=30)
            if r.status_code == 200:
                return True, field
        except Exception:
            continue
    return False, ""


def fb_scan_and_repair(apply=False, fix_public_only=False):
    """Scan FB page videos and optimize per 2026 Reels algorithm."""
    tok, page = fb_get_service()
    if not tok or not page:
        return

    print(f"\n{'='*78}\n📘 FACEBOOK: Page {page} scan kar raha hoon\n{'='*78}")

    import requests

    # V3.6-repair: Reels/videos POSTS mein hote hain (video-library edge
    # mein nahi). PRIMARY: /{page}/posts (pagination + token) — video-type
    # posts ke message repair karte hain. Fallback: /{page}/videos edge.
    video_ids = []
    next_url = f"https://graph.facebook.com/v25.0/{page}/posts"
    params = {"access_token": tok,
              "fields": "id,type,status,message,created_time",
              "limit": 100}
    pages_seen = 0
    while next_url and pages_seen < 10:
        try:
            r = requests.get(next_url,
                             params=params if "access_token" not in next_url else None,
                             timeout=30)
            if r.status_code >= 400:
                print(f"⚠️ FB posts error: {r.text[:200]}")
                break
            data = r.json()
            items = data.get("data", [])
            if pages_seen == 0:
                print(f"📘 FB posts page 1: {len(items)} items "
                      f"(types: {sorted({str(i.get('type')) for i in items})})")
            for item in items:
                if item.get("type") == "video":
                    video_ids.append(item.get("id"))
            nxt = data.get("paging", {}).get("next")
            next_url = (nxt if "access_token" in nxt else f"{nxt}&access_token={tok}") \
                if nxt else None
            pages_seen += 1
        except Exception as exc:
            print(f"⚠️ FB scan error: {exc}")
            break

    # Fallback (PRIMARY in practice): video library edge — 35 published
    # videos mile. V3.6-repair-4: status ab DICT hai (video_status +
    # publishing_phase.publish_status), string nahi — dict==str comparison
    # hamesha False tha is liye kuch select nahi hota tha.
    if not video_ids:
        try:
            r = requests.get(
                f"https://graph.facebook.com/v25.0/{page}/videos",
                params={"access_token": tok,
                        "fields": "id,title,status",
                        "limit": 100},
                timeout=30)
            if r.status_code >= 400:
                print(f"⚠️ FB videos edge error: {r.text[:200]}")
            else:
                vids = r.json().get("data", [])
                print(f"📘 FB video library: {len(vids)} videos")
                for item in vids:
                    st = item.get("status")
                    published = ((st.get("publishing_phase", {}).get("publish_status") == "published"
                                  or st.get("video_status") == "ready")
                                 if isinstance(st, dict) else st == "published")
                    if published:
                        video_ids.append(item.get("id"))
        except Exception as exc:
            print(f"⚠️ FB videos edge scan error: {exc}")

    # Deduplicate
    video_ids = list(dict.fromkeys(video_ids))
    STATS["facebook"]["scanned"] = len(video_ids)

    if not video_ids:
        print("⚠️ Koi Facebook video nahi mili (ya API access nahi hai).")
        return

    print(f"📘 FB: {len(video_ids)} videos mil Gaye\n")

    for vid in video_ids:
        try:
            # V3.6-repair-4: do node types — post ids (pageid_videoid,
            # underscore wale) par message fields, video-library ids (plain
            # numeric) par title/description fields. Galat fields maangne
            # par API 400 deta hai — ab sahi fields type ke mutabiq.
            is_post = "_" in str(vid)
            fields = (("id,message,status,created_time,permalink_url,"
                       "reactions.summary(total_count),"
                       "comments.summary(total_count)") if is_post
                      else ("id,title,description,caption,status,length,"
                            "created_time,permalink_url"))
            r = requests.get(
                f"https://graph.facebook.com/v25.0/{vid}",
                params={"access_token": tok, "fields": fields,
                        "timeout": 30},
                timeout=30)
            if r.status_code >= 400 and not is_post and "caption" in fields:
                # video-node par caption field kabhi invalid hota hai →
                # bina caption ke retry (V3.6-repair-9 safety)
                fields2 = fields.replace(",caption", "")
                r = requests.get(
                    f"https://graph.facebook.com/v25.0/{vid}",
                    params={"access_token": tok, "fields": fields2,
                            "timeout": 30},
                    timeout=30)
            if r.status_code >= 400:
                print(f"  ⚠️ FB {vid[:20]}: GET fail — {r.text[:150]}")
                continue

            data = r.json()
            # V3.6-repair-5: status dict ho sakta hai — f"{dict:10}" Python
            # mein TypeError deta hai (unsupported format string), jis ki
            # wajah se har item ka print silently crash ho jata tha.
            st_raw = data.get("status", "unknown")
            status = (st_raw.get("publishing_phase", {}).get(
                "publish_status", st_raw.get("video_status", "?"))
                if isinstance(st_raw, dict) else str(st_raw))
            if is_post:
                caption = data.get("message", "") or ""
                reactions = (data.get("reactions", {}) or {}).get("summary", {})
                comments_n = (data.get("comments", {}) or {}).get("summary", {})
                like_count = int(reactions.get("total_count", 0) or 0)
                comment_count = int(comments_n.get("total_count", 0) or 0)
            else:
                # V3.6-repair-9: read bhi caption field dekhta hai — update
                # caption mein hota tha par read sirf description → har run
                # dobara fix karta tha (loop)
                caption = (data.get("description", "") or data.get("caption", "")
                           or data.get("title", "") or "")
                like_count = comment_count = 0

            actions = []
            is_ok = True

            # ── Caption/Message boost (REAL fix, V3.6) ──
            if not caption or len(caption) < 20:
                keyword = None
                for p in PILLARS:
                    for term in p.get("search_terms", []):
                        if term in caption.lower():
                            keyword = term
                            break
                    if keyword:
                        break

                new_caption = "🚨 Psychology pattern you need to see.\n\n"
                if keyword:
                    new_caption += f"{keyword.title()} psychology: how this manipulation works and how to protect yourself.\n\n"
                new_caption += "👇 What would you add? Drop your thoughts in the comments.\n\n"
                new_caption += CTA + "\n\n"
                new_caption += " ".join(FB_HASHTAGS_BANK[:FB_HASHES_RECOMMENDED])

                if apply and not fix_public_only:
                    ok_upd, via = fb_update_post_text(tok, vid, new_caption)
                    if ok_upd:
                        # V3.6-repair-10: verify — FB kabhi silent 200 deta
                        # hai bina kuch change kiye. Read-back se asal
                        # change confirm karo; no-op par fake 'fixed' count
                        # NAHI (honest reporting).
                        try:
                            rv = requests.get(
                                f"https://graph.facebook.com/v25.0/{vid}",
                                params={"access_token": tok, "fields": fields,
                                        "timeout": 30},
                                timeout=30)
                            if rv.status_code == 200:
                                d2 = rv.json()
                                now_txt = (d2.get("description", "") or
                                           d2.get("caption", "") or
                                           d2.get("message", "") or "")
                                if len(now_txt or "") >= 20:
                                    actions.append(f"caption+ (via {via}) ✓")
                                    STATS["facebook"]["caption_updated"] += 1
                                    caption = new_caption
                                else:
                                    actions.append("cap-NOOP: API 200 par "
                                                   "koi change nahi (FB limitation)")
                            else:
                                actions.append(f"caption+ (via {via}) — verify fail {rv.status_code}")
                        except Exception:
                            actions.append(f"caption+ (via {via}) — verify error")
                    else:
                        actions.append("cap-ERR: all fields failed")
                else:
                    actions.append("would:caption+")
            else:
                # Message theek hai par hashtags kam → REAL hashtag fix
                hashtag_count = len(re.findall(r"#\w+", caption))
                if hashtag_count < 4:
                    missing = [h for h in FB_HASHTAGS_BANK
                               if h.lower() not in caption.lower()]
                    add = missing[: (FB_HASHES_RECOMMENDED - hashtag_count)]
                    if add and apply and not fix_public_only:
                        new_text = caption.rstrip() + "\n\n" + " ".join(add)
                        ok_upd, via = fb_update_post_text(tok, vid, new_text)
                        if ok_upd:
                            actions.append(f"hashtags+ ({hashtag_count}→{hashtag_count + len(add)}, via {via})")
                            STATS["facebook"]["hashtag_fixed"] += 1
                            caption = new_text
                        else:
                            actions.append(f"hash-ERR (had {hashtag_count})")
                    elif add:
                        actions.append(f"would:hashtags+ ({hashtag_count}→{hashtag_count + len(add)})")

            print(f"  {vid[:20]} status={status:10} likes={like_count:<4} comments={comment_count:<4} | {' | '.join(actions) if actions else '✅ OK'}")
            if not is_ok:
                print(f"    caption: {(caption or '')[:80]}")

        except Exception as exc:
            # V3.6-repair-5: errors ab VISIBLE hain (pehle debug mein
            # chhupe rehte thay aur pata hi nahi chalta tha ke kya fail hua)
            print(f"  ⚠️ FB {vid[:20]}: error — {exc}")

    print(f"\n{'='*60}")
    print("FACEBOOK SUMMARY:")
    print(f"  Scanned         : {STATS['facebook']['scanned']}")
    print(f"  Total views     : {STATS['facebook']['total_views_before']}")
    print(f"  Captions fixed  : {STATS['facebook']['caption_updated']}")
    print(f"  Hashtags fixed  : {STATS['facebook']['hashtag_fixed']}")
    print(f"{'='*60}\n")


# ═══════════════════════════════════════════════════════════════════
# INSTAGRAM REPAIR
# ═══════════════════════════════════════════════════════════════════

IG_HASHTAGS_BANK = [
    "#psychology", "#truecrime", "#mindcontrol", "#manipulation",
    "#gaslighting", "#coercivecontrol", "#stoicism", "#scamawareness",
    "#mentalhealth", "#selfimprovement", "#bodylanguage", "#emotionalintelligence",
    "#toxicrelationships", "#psychologytips", "#humanbehavior",
    "#interrogation", "#brainwashing", "#factsvideo", "#foryou", "#viral",
]


def ig_get_service():
    tok = (os.environ.get("IG_ACCESS_TOKEN", "") or
           os.environ.get("INSTAGRAM_ACCESS_TOKEN", "") or
           os.environ.get("FACEBOOK_ACCESS_TOKEN", ""))
    ig_id = (os.environ.get("IG_BUSINESS_ACCOUNT_ID", "") or
             os.environ.get("INSTAGRAM_USER_ID", ""))
    if not tok or not ig_id:
        print("❌ IG_ACCESS_TOKEN / IG_BUSINESS_ACCOUNT_ID configure karein.")
        return None, None
    return tok, ig_id


def ig_check_account(tok, ig_id):
    """Check if IG account is properly configured for publishing.

    V3.6: invalid field "nutrients" hata diya — Graph API error 100 deta
    tha aur account check fail ho kar IG repair kabhi start nahi hota tha.
    """
    import requests
    try:
        r = requests.get(
            f"https://graph.facebook.com/v25.0/{ig_id}",
            params={"access_token": tok,
                    "fields": "followers_count,media_count,username,biography",
                    "timeout": 30},
            timeout=30)
        if r.status_code >= 400:
            print(f"  ⚠️ IG account error: {r.text[:300]}")
            return False, r.json()
        data = r.json()
        followers = data.get("followers_count", 0)
        media_count = data.get("media_count", 0)
        print(f"  ✅ Account OK — followers={followers}, media={media_count}")
        return True, data
    except Exception as exc:
        print(f"  ❌ Account check failed: {exc}")
        return False, {}


def ig_scan_and_repair(apply=False, fix_public_only=False):
    """Scan IG reels and optimize per 2026 algorithm."""
    tok, ig_id = ig_get_service()
    if not tok or not ig_id:
        return

    print(f"\n{'='*78}\n📸 INSTAGRAM: Account {ig_id} scan kar raha hoon\n{'='*78}")

    ok, _account_data = ig_check_account(tok, ig_id)
    if not ok:
        print("⚠️ IG account properly configure nahi hai — fix karein phir try karein.")
        return

    import requests

    # Get recent media (Reels) — V3.6: PEHLI request mein bhi access_token
    # zaroori tha; pehle sirf pagination mein tha → pehli call 400 ho kar
    # "koi reels nahi mili" bol deti thi. IG repair kabhi chala hi nahi.
    media_ids = []
    next_url = f"https://graph.facebook.com/v25.0/{ig_id}/media"

    while next_url:
        try:
            r = requests.get(next_url,
                             params={"access_token": tok, "fields":
                                     "id,media_type", "limit": 100}
                             if "access_token" not in next_url else None,
                             timeout=30)
            if r.status_code >= 400:
                print(f"⚠️ IG media error: {r.text[:200]}")
                break
            data = r.json()
            for item in data.get("data", []):
                if item.get("media_type") in ("REELS", "VIDEO"):
                    media_ids.append(item.get("id"))
            nxt = data.get("paging", {}).get("next")
            next_url = (nxt if "access_token" in nxt else f"{nxt}&access_token={tok}") \
                if nxt else None
        except Exception as exc:
            print(f"⚠️ IG scan error: {exc}")
            break

    STATS["instagram"]["scanned"] = len(media_ids)

    if not media_ids:
        print("⚠️ Koi Instagram Reels nahi mili (ya API access limit hai).")
        return

    print(f"📸 IG: {len(media_ids)} Reels mil Gaye\n")

    ig_manual_fixes = []   # V3.6-repair: API caption edit support nahi karta

    for mid in media_ids:
        try:
            # V3.6-repair FIX: pehle sirf CORE fields (always available) —
            # insights/saved_count jaise risky fields ki wajah se poora GET
            # 400 ho kar 73 reels ke baad bhi 0 fixes hoti thin. Insights ab
            # alag se try hote hain — fail ho to bhi caption repair chalti hai.
            r = requests.get(
                f"https://graph.facebook.com/v25.0/{mid}",
                params={
                    "access_token": tok,
                    "fields": ("id,caption,media_type,permalink,thumbnail_url,"
                               "timestamp,like_count,comments_count"),
                    "timeout": 30
                },
                timeout=30)
            if r.status_code >= 400:
                print(f"  ⚠️ reel {mid[:16]}: GET fail {r.status_code} — {r.text[:120]}")
                continue

            data = r.json()
            caption = data.get("caption", "") or ""
            likes = int(data.get("like_count", 0) or 0)
            comments = int(data.get("comments_count", 0) or 0)
            plays = shares = saved = 0
            # insights alag se (optional) — metric: plays, reach, saved, shares
            try:
                ri = requests.get(
                    f"https://graph.facebook.com/v25.0/{mid}/insights",
                    params={"access_token": tok,
                            "metric": "plays,reach,saved,shares",
                            "timeout": 30},
                    timeout=30)
                if ri.status_code == 200:
                    for entry in ri.json().get("data", []):
                        vals = entry.get("values", [])
                        if not vals:
                            continue
                        total = sum(int(v.get("value", 0) or 0) for v in vals)
                        if entry.get("name") == "plays":
                            plays = total
                        elif entry.get("name") == "saved":
                            saved = total
                        elif entry.get("name") == "shares":
                            shares = total
            except Exception:
                pass  # insights optional — repair is ke baghair bhi chalti hai

            STATS["instagram"]["total_views_before"] += plays  # V3.6: pehle overwrite hota tha — sirf aakhri reel ka count rehta tha

            actions = []

            # ── Caption optimization ──
            has_save_cta = any(w in caption.lower() for w in ["save", "bookmark", "keep"])
            hashtag_count = len(re.findall(r"#\w+", caption or ""))
            needs_upgrade = (not caption or len(caption) < 50 or
                            hashtag_count < 15 or not has_save_cta)

            if needs_upgrade:
                # V3.6-repair HONEST: Instagram Graph API published media ke
                # captions EDIT nahi karta (sirf comment_enabled toggle hai —
                # Meta docs). API se fix impossible hai → har weak caption ki
                # improved version MANUAL LIST mein likhte hain (permalink ke
                # saath) taake owner 1 minute mein khud apply kar sake.
                title = ""
                lines = caption.split("\n") if caption else []
                for line in lines:
                    if len(line) > 10 and not line.startswith("#"):
                        title = line.strip()
                        break

                new_caption = f"🚨 {title or 'Psychology Fact'}\n\n"
                new_caption += "Save this for your next conversation — "
                new_caption += "you'll need it.\n\n"
                new_caption += CTA + "\n\n"
                new_caption += " ".join(IG_HASHTAGS_BANK[:20])

                permalink = data.get("permalink", "")
                ig_manual_fixes.append({
                    "media_id": mid, "permalink": permalink,
                    "current": (caption or "")[:200],
                    "suggested": new_caption,
                })
                actions.append(f"manual-fix #{(len(ig_manual_fixes))} "
                               f"(hashtags={hashtag_count}, save_cta={has_save_cta})")

            # ── Engagement stats ──
            engagement_rate = (likes + comments * 2 + shares * 3 + saved * 4) / max(1, plays) * 100

            print(f"  {mid[:16]} plays={plays:<6} likes={likes:<5} saved={saved:<4} "
                  f"eng={engagement_rate:.1f}% | {' | '.join(actions) if actions else '✅ OK'}")
            if caption:
                print(f"    caption: {(caption or '')[:80]}")

        except Exception as exc:
            logger.debug("IG reel %s error: %s", mid, exc)

    print(f"\n{'='*60}")
    # V3.6-repair: MANUAL FIX LIST — IG API caption edit support nahi karta
    if ig_manual_fixes:
        try:
            _ig = Path(__file__).resolve().parent.parent / "data" / "ig_caption_fixes.md"
            _ig.parent.mkdir(parents=True, exist_ok=True)
            _lines = [
                "# 📸 Instagram Caption Fixes (MANUAL — API edit support nahi karta)",
                "",
                f"*{len(ig_manual_fixes)} reels ki improved captions — apply karo: "
                "IG app mein reel kholo → ⋮ → Edit → caption paste karo.*",
                "",
            ]
            for i, fx in enumerate(ig_manual_fixes[:30], 1):
                _lines += [
                    f"## {i}. {fx['permalink'] or fx['media_id']}",
                    "",
                    "**Suggested caption:**",
                    "```",
                    fx["suggested"],
                    "```",
                    "",
                ]
                if fx["current"]:
                    _lines += [f"*(Current: {fx['current']}...)*", ""]
            _ig.write_text("\n".join(_lines), encoding="utf-8")
            print(f"  📝 Manual fixes list: {_ig} ({len(ig_manual_fixes)} reels)")
        except OSError as exc:
            print(f"  ⚠️ Manual list write failed: {exc}")

    print("INSTAGRAM SUMMARY:")
    print(f"  Scanned         : {STATS['instagram']['scanned']}")
    print(f"  Captions fixed  : {STATS['instagram']['caption_updated']}  "
          "(API caption edit support NAHI karta — manual list mein)")
    STATS["instagram"]["manual_fixes"] = len(ig_manual_fixes)
    print(f"  Manual fixes    : {len(ig_manual_fixes)}")
    print(f"{'='*60}\n")


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    ap = argparse.ArgumentParser(
        description="Coercion Files — 2026 Algorithm Video Repair Tool")
    ap.add_argument("--apply", action="store_true",
                    help="asal changes karo (default: dry-run report only)")
    ap.add_argument("--fix-public", action="store_true",
                    help="sirf private→public fix karo (YouTube)")
    ap.add_argument("--audit", action="store_true",
                    help="sirf scan/report — koi change nahi")
    ap.add_argument("--skip-yt", action="store_true", help="YouTube skip karo")
    ap.add_argument("--skip-fb", action="store_true", help="Facebook skip karo")
    ap.add_argument("--skip-ig", action="store_true", help="Instagram skip karo")
    args = ap.parse_args()

    apply = args.apply or args.fix_public
    fix_public_only = args.fix_public and not args.apply
    audit_only = args.audit
    if apply:
        confirmed = os.environ.get("CONFIRM_REPAIR_APPLY", "0").strip().lower()
        if confirmed not in {"1", "true", "yes", "on"}:
            print("❌ apply/fix-public blocked: set CONFIRM_REPAIR_APPLY=1 after reviewing audit output")
            return 2

    mode = "APPLY" if apply else "DRY-RUN"
    if fix_public_only:
        mode = "FIX-PUBLIC-ONLY"
    elif audit_only:
        mode = "AUDIT-ONLY"

    print(f"\n{'#'*78}")
    print("# Coercion Files — 2026 Algorithm Video Repair")
    print(f"# Mode: {mode} | Time: {datetime.now(timezone.utc).isoformat()}")
    print(f"{'#'*78}\n")

    if not args.skip_yt:
        yt = yt_get_service()
        if yt:
            if audit_only or fix_public_only:
                yt_audit_and_repair(yt, apply=args.apply, fix_public_only=fix_public_only)
            else:
                yt_audit_and_repair(yt, apply=apply)
        else:
            print("⚠️ YouTube skip — credentials nahi hain")

    if not args.skip_fb:
        fb_scan_and_repair(apply=apply, fix_public_only=fix_public_only)

    if not args.skip_ig:
        ig_scan_and_repair(apply=apply, fix_public_only=fix_public_only)

    # ── V3.6: repair REPORT file — CI isay commit karta hai (audit trail) ──
    try:
        _rp = Path(__file__).resolve().parent.parent / "data" / "repair_report.md"
        _rp.parent.mkdir(parents=True, exist_ok=True)
        _rp.write_text(
            f"# 🛠️ 2026 Algorithm Video Repair Report\n\n"
            f"*Mode: {mode} | Time: {datetime.now(timezone.utc).isoformat()}*\n\n"
            f"## 📺 YouTube\n"
            f"- Scanned: {STATS['youtube']['scanned']}\n"
            f"- Not Shorts-ready: {STATS['youtube']['not_shorts_ready']}\n"
            f"- → Public kiye: {STATS['youtube']['fixed_public']}\n"
            f"- SEO boosted: {STATS['youtube']['seo_boosted']}\n"
            f"- Playlist added: {STATS['youtube']['playlist_add']}\n"
            f"- Thumbnails updated: {STATS['youtube']['thumbnail_updated']}\n"
            f"- Total views: {STATS['youtube']['total_views_before']}\n\n"
            f"## 📘 Facebook\n"
            f"- Scanned: {STATS['facebook']['scanned']}\n"
            f"- Captions fixed: {STATS['facebook']['caption_updated']}\n"
            f"- Hashtags fixed (REAL API updates): {STATS['facebook']['hashtag_fixed']}\n"
            f"- Total views: {STATS['facebook']['total_views_before']}\n\n"
            f"## 📸 Instagram\n"
            f"- Scanned: {STATS['instagram']['scanned']}\n"
            f"- Captions fixed (API): {STATS['instagram']['caption_updated']} "
            f"(IG API caption edit support nahi karta)\n"
            f"- Manual fixes (data/ig_caption_fixes.md): {STATS['instagram']['manual_fixes']}\n"
            f"- Total plays: {STATS['instagram']['total_views_before']}\n",
            encoding="utf-8")
        print(f"📄 Report: {_rp}")
    except OSError as exc:
        print(f"⚠️ Report write failed: {exc}")

    # Final totals
    print(f"\n{'#'*78}")
    print(f"# FINAL REPORT — {mode}")
    print(f"{'#'*78}")
    print(f"""
📺 YOUTUBE:
   Videos scanned  : {STATS['youtube']['scanned']}
   Not Shorts-ready: {STATS['youtube']['not_shorts_ready']}
   → Public kiye   : {STATS['youtube']['fixed_public']}
   SEO boosted     : {STATS['youtube']['seo_boosted']}
   Playlist add    : {STATS['youtube']['playlist_add']}

📘 FACEBOOK:
   Videos scanned  : {STATS['facebook']['scanned']}
   Captions fixed  : {STATS['facebook']['caption_updated']}
   Hashtags fixed  : {STATS['facebook']['hashtag_fixed']}

📸 INSTAGRAM:
   Reels scanned   : {STATS['instagram']['scanned']}
   Captions fixed  : {STATS['instagram']['caption_updated']}
""")


if __name__ == "__main__":
    raise SystemExit(main())
