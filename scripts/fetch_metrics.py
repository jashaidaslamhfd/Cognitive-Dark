#!/usr/bin/env python3
"""
Coercion Files — Metrics Sync (closes the ML learning loop).

Pulls real analytics from all three platforms and:
  1. CREDITS the exact formula behind each published video — every uploaded
     video_id is attributed to its ML arm (see ml_engine.record_video_id);
     here we fetch that video's views/likes/comments/watch_time and push a
     reward onto the responsible arm, so the bandit genuinely learns what
     goes viral.
  2. Rewards consistency — channel/page growth applies a small bonus to the
     arms that were recently active.
  3. Detects low-retention videos and applies penalties so the ML learns
     what NOT to produce.
  4. Updates the monetization progress snapshot.
  5. Writes data/metrics_report.md for a quick human review.

Runs on a schedule in CI. Platforms without tokens are skipped gracefully.

FIXES (V3.1):
  • Facebook video-level crediting added (was missing — FB videos never
    learned from → bandit blind on FB platform).
  • Instagram video-level crediting added (was missing — IG reels never
    learned from → bandit blind on IG platform).
  • Facebook watch_time + engagement metrics from Graph API insights.
  • YouTube approximate retention from view-to-like ratio (no extra scope).
  • Low-retention penalty: videos with <30% estimated retention get
    penalized so the ML learns to avoid weak formulas.
  • Per-platform separate learning: YouTube, FB, IG arms now learn independently.
"""

import contextlib
import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("fetch_metrics")

from ml_engine import LearningSystem
from monetization_tracker import PROGRESS_PATH, update_progress

# ── YouTube helpers ──────────────────────────────────────────────

def _resolve_yt_creds():
    """Same resolution rules as platforms/youtube.py (path | JSON | split env)."""
    raw = os.environ.get("YOUTUBE_CREDENTIALS", "")
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    refresh_token = os.environ.get("REFRESH_TOKEN")
    if client_id and client_secret and refresh_token:
        info = {
            "client_id": client_id, "client_secret": client_secret,
            "refresh_token": refresh_token,
            "token_uri": "https://oauth2.googleapis.com/token",
            "scopes": [
                "https://www.googleapis.com/auth/youtube.readonly",
                "https://www.googleapis.com/auth/yt-analytics.readonly",
            ],
            "type": "authorized_user",
        }
        return info
    if not raw:
        return None
    if os.path.exists(raw):
        with open(raw, encoding="utf-8") as fh:
            return json.load(fh)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _yt_service():
    info = _resolve_yt_creds()
    if not info:
        return None
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    creds = Credentials.from_authorized_user_info(info)
    if (creds.expired or not creds.valid) and creds.refresh_token:
        creds.refresh(Request())
    return build("youtube", "v3", credentials=creds)


def youtube_metrics() -> dict:
    """Channel-level subs/views via the Data API."""
    try:
        yt = _yt_service()
        if yt is None:
            return {}
        ch = yt.channels().list(part="statistics", mine=True).execute()["items"][0]
        stats = ch["statistics"]
        return {
            "subs": int(stats.get("subscriberCount", 0)),
            "views": int(stats.get("viewCount", 0)),
            "videos": int(stats.get("videoCount", 0)),
        }
    except Exception as exc:
        logger.warning("YouTube channel metrics unavailable: %s", exc)
        return {}


# ── V3.7 REAL CTR pipeline ────────────────────────────────────────
# CTR = Views ÷ Impressions. Ye system ka PEHLA real CTR measurement hai:
#   • YouTube  → youtubeAnalytics v2 (impressions metric; yt-analytics
#                readonly scope chahiye — creds mein already list hai)
#   • Facebook → /{video-id}/video_insights (post_impressions +
#                post_video_views)
#   • Instagram→ /{media-id}/insights (impressions/reach + plays)
# Data na ho (scope/token/permission) → CTR bheja hi nahi jata; reward.py
# isay "unknown" treat karta hai — kabhi guess nahi. Is CTR se reward.py
# ka 10% CTR-weight ab REAL data se chalta hai.

def ctr_from(views: int, impressions: int) -> float | None:
    """CTR = views / impressions (0..1). None agar impressions unknown/0.
    Clamp 0..1 — views impressions se zyada kabhi nahi (data glitch se)."""
    if not impressions or int(impressions) <= 0:
        return None
    return round(max(0.0, min(1.0, float(views) / float(impressions))), 4)


def _yt_analytics():
    """youtubeAnalytics v2 service — impressions/CTR ke liye.

    None agar creds nahi hain ya token mein yt-analytics scope nahi
    (graceful — CTR bas skip hota hai, baqi metrics chalti hain).
    """
    info = _resolve_yt_creds()
    if not info:
        return None
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        creds = Credentials.from_authorized_user_info(info)
        if (creds.expired or not creds.valid) and creds.refresh_token:
            creds.refresh(Request())
        return build("youtubeAnalytics", "v2", credentials=creds)
    except Exception as exc:
        logger.warning("YouTube Analytics unavailable (CTR skip): %s", exc)
        return None


def yt_ctr_for_video(analytics, video_id: str, days: int = 14) -> tuple:
    """(views, impressions, ctr) for ONE video from Analytics API.

    Returns (None, None, None) agar data nahi / scope nahi / error.
    """
    if analytics is None:
        return None, None, None
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=days)
    try:
        rep = analytics.reports().query(
            ids="channel==MINE",
            startDate=start.isoformat(),
            endDate=end.isoformat(),
            metrics="views,impressions",
            dimensions="video",
            filters=f"video=={video_id}",
        ).execute()
        rows = rep.get("rows") or []
        if not rows:
            return None, None, None
        a_views = int(rows[0][0] or 0)
        impressions = int(rows[0][1] or 0)
        return a_views, impressions, ctr_from(a_views, impressions)
    except Exception as exc:
        # V3.7.2: `impressions` metric sirf YPP/content-owner channels par
        # hai (chhote channel par 400 "Unknown identifier"). Fallback:
        # sirf views — accurate count phir bhi milta hai, CTR unknown rehta
        # hai (honest — koi guess nahi).
        if "impressions" in str(exc) or "Unknown identifier" in str(exc):
            try:
                rep = analytics.reports().query(
                    ids="channel==MINE",
                    startDate=start.isoformat(),
                    endDate=end.isoformat(),
                    metrics="views",
                    dimensions="video",
                    filters=f"video=={video_id}",
                ).execute()
                rows = rep.get("rows") or []
                if rows:
                    return int(rows[0][0] or 0), None, None
            except Exception:
                pass
            return None, None, None
        logger.warning("YT Analytics for %s failed (scope/permission?): %s",
                       video_id[:12], exc)
        return None, None, None


def _insight_totals(resp: dict) -> dict:
    """Meta insights response → {metric_name: total}."""
    out = {}
    for entry in (resp or {}).get("data", []):
        total = 0
        for v in entry.get("values", []):
            try:
                total += int(v.get("value", 0) or 0)
            except (TypeError, ValueError):
                continue
        out[entry.get("name")] = total
    return out


def _estimate_yt_retention(views: int, likes: int, comments: int) -> float:
    """Approximate retention from engagement signals (no Analytics API scope needed).
    Real retention needs youtubeAnalytics API. This estimate is conservative:
      - likes/views ratio: ~3-5% is normal for Shorts, >5% = good retention
      - comments/views ratio: >0.5% = strong engagement = likely high retention
      - Heavily penalized if views but near-zero engagement (swipe-away signal).

    ⚠️ V3.6: ye ESTIMATE hai, measurement nahi. reward.py is ko
    `retention_estimated` flag ke saath alag treat karta hai (half weight,
    viral bonus NAHI) — fabricated retention ab bandit ko dhoka nahi de
    sakti. Agar YT Analytics scope (yt-analytics.readonly) available ho to
    asal retention use karo — wahan se `retention_measured` milega.
    """
    if views <= 0:
        return 0.0
    like_ratio = likes / views
    comment_ratio = comments / views
    # Base on like ratio (typical Shorts: 2-8%)
    est = 0.15 + like_ratio * 8.0  # 0.15 base + scaled likes
    # Boost for comments (strong signal of retention)
    est += comment_ratio * 20.0
    # Penalty for near-zero engagement relative to views
    if like_ratio < 0.01 and comments == 0 and views > 50:
        est *= 0.4  # swipe-away territory
    return round(min(0.95, max(0.05, est)), 3)


def youtube_credit_videos(ml: LearningSystem) -> int:
    """Credit each uncredited, attributed YouTube video with real stats."""
    # V3.7: pending (uncredited) + refreshable (stale: 0-views/CTR-less) — dono real data se update hote hain
    ids = [v for v in ml.pending_video_ids("youtube") if str(v) != "dry-run"]
    ids += [v for v in ml.refreshable_video_ids("youtube") if v not in ids]
    if not ids:
        return 0
    try:
        yt = _yt_service()
        if yt is None:
            return 0
        analytics = _yt_analytics()   # V3.7: CTR ke liye (scope na ho to None)
        credited = 0
        for chunk_start in range(0, len(ids), 50):
            chunk = ids[chunk_start:chunk_start + 50]
            resp = yt.videos().list(part="statistics", id=",".join(chunk)).execute()
            for item in resp.get("items", []):
                st = item.get("statistics", {})
                views = int(st.get("viewCount", 0))
                likes = int(st.get("likeCount", 0))
                comments = int(st.get("commentCount", 0))
                retention = _estimate_yt_retention(views, likes, comments)
                metrics = {
                    "views": views, "likes": likes, "comments": comments,
                    "retention": retention,
                    "retention_estimated": True,   # V3.6: ye guess hai
                    "platform": "youtube",
                }
                # V3.7: REAL impressions + CTR (Analytics API) — data ho to
                # views bhi Analytics ke accurate count se update
                a_views, impressions, ctr = yt_ctr_for_video(analytics, item["id"])
                if a_views is not None and a_views > 0:
                    metrics["views"] = a_views
                if ctr is not None:
                    metrics["ctr"] = ctr
                    metrics["impressions"] = impressions
                    logger.info("YT credit: %s → views=%d impressions=%s "
                                "CTR=%.1f%% (REAL)", item["id"][:16], metrics["views"],
                                impressions, ctr * 100)
                else:
                    logger.info("YT credit: %s → views=%d likes=%d "
                                "retention≈%.0f%% (CTR: impressions metric "
                                "unavailable — YPP hone par khud aa jayega)",
                                item["id"][:16], metrics["views"], likes, retention * 100)
                ml.credit_video(item["id"], metrics)
                credited += 1
        return credited
    except Exception as exc:
        logger.warning("YouTube video credit failed: %s", exc)
        return 0


# ── Facebook helpers ──────────────────────────────────────────────

def _fb_service():
    """Return (token, page_id) or (None, None)."""
    tok = os.environ.get("FB_ACCESS_TOKEN", "")
    page = os.environ.get("FB_PAGE_ID", "")
    if tok and page:
        return tok, page
    # fallback to alternate secret names
    tok = os.environ.get("FACEBOOK_ACCESS_TOKEN", tok)
    page = os.environ.get("FACEBOOK_PAGE_ID", page)
    return (tok or None), (page or None)


def facebook_metrics() -> dict:
    """Page-level followers via Graph API."""
    tok, page = _fb_service()
    if not tok or not page:
        return {}
    try:
        import requests
        r = requests.get(
            f"https://graph.facebook.com/v25.0/{page}",
            params={"access_token": tok, "fields": "fan_count,followers_count"},
            timeout=30,
        )
        r.raise_for_status()
        d = r.json()
        return {"followers": d.get("followers_count", d.get("fan_count", 0))}
    except Exception as exc:
        logger.warning("FB page metrics unavailable: %s", exc)
        return {}


def facebook_credit_videos(ml: LearningSystem) -> int:
    """Credit each uncredited Facebook video with real stats.

    Fetches video-level stats from the Graph API and applies rewards/penalties
    to the arms that produced them. Also fetches insights (watch time) when
    available.
    """
    # V3.7: pending (uncredited) + refreshable (stale: 0-views/CTR-less) — dono real data se update hote hain
    ids = [v for v in ml.pending_video_ids("facebook") if str(v) != "dry-run"]
    ids += [v for v in ml.refreshable_video_ids("facebook") if v not in ids]
    if not ids:
        return 0
    tok, page = _fb_service()
    if not tok or not page:
        logger.warning("FB credit skipped — no token/page configured")
        return 0
    try:
        import requests
        credited = 0
        for vid in ids:
            try:
                # V3.7.2: VALID video-node fields — pehle "stats,insights"
                # fields maang rahe thay jo FB video node par exist hi nahi
                # karte (400 → silent skip → FB credit kabhi nahi hota tha)
                r = requests.get(
                    f"https://graph.facebook.com/v25.0/{vid}",
                    params={
                        "access_token": tok,
                        "fields": "id,title,description,length,created_time,"
                                  "permalink_url",
                    },
                    timeout=30,
                )
                if r.status_code >= 400:
                    logger.warning("FB video %s GET fail: %s", vid[:16], r.text[:150])
                    continue
                data = r.json()
                duration_secs = float(data.get("length", 0) or 0)

                # insights: views / watch-time / impressions / complete-views
                views = watch_time_secs = impressions = 0
                ins = {}
                metric_status = {}
                try:
                    # V3.7.5: PER-METRIC collection — har metric alag se try,
                    # jo valid ho use hota hai (account-specific metric sets
                    # ka pakka solution; invalid ka reason log hota hai)
                    ins = {}
                    for m in ("post_video_views", "post_video_view_time",
                              "post_impressions", "post_video_avg_time_watched",
                              "post_video_complete_views_organic"):
                        try:
                            rm = requests.get(
                                f"https://graph.facebook.com/v25.0/{vid}/video_insights",
                                params={"access_token": tok, "metric": m,
                                        "timeout": 30},
                                timeout=30)
                            if rm.status_code == 200:
                                ins[m] = _insight_totals(rm.json()).get(m, 0)
                                metric_status[m] = "measured"
                            else:
                                metric_status[m] = "unavailable"
                                logger.warning("FB metric %s (%s): %s", m,
                                               vid[:16], rm.text[:120])
                        except Exception:
                            metric_status[m] = "error"
                    views = int(ins.get("post_video_views", 0) or 0)
                    wt = ins.get("post_video_view_time", 0) or 0
                    if wt > 1000:      # ms → seconds
                        wt = wt / 1000.0
                    watch_time_secs = int(wt)
                    impressions = int(ins.get("post_impressions", 0) or 0)
                except Exception as exc:
                    logger.warning("FB video_insights %s failed: %s", vid[:16], exc)

                # likes/comments: summary edges (permission na ho to 0)
                likes = comments = shares = 0
                try:
                    rl = requests.get(
                        f"https://graph.facebook.com/v25.0/{vid}/likes",
                        params={"access_token": tok, "summary": "true",
                                "limit": "0", "timeout": 30}, timeout=30)
                    if rl.status_code == 200:
                        likes = int((rl.json().get("summary") or {})
                                    .get("total_count", 0) or 0)
                except Exception:
                    pass
                try:
                    rc = requests.get(
                        f"https://graph.facebook.com/v25.0/{vid}/comments",
                        params={"access_token": tok, "summary": "true",
                                "limit": "0", "timeout": 30}, timeout=30)
                    if rc.status_code == 200:
                        comments = int((rc.json().get("summary") or {})
                                       .get("total_count", 0) or 0)
                except Exception:
                    pass

                metrics = {
                    "views": views,
                    "likes": likes,
                    "comments": comments,
                    "shares": shares,
                    "watch_time_seconds": watch_time_secs,
                    "duration_seconds": duration_secs,
                    "platform": "facebook",
                    "metric_status": metric_status,
                    "views_status": "measured" if "post_video_views" in ins else "unavailable",
                    "impressions_status": "measured" if "post_impressions" in ins else "unavailable",
                }
                # V3.6: retention sirf MEASURED (real watch time) par
                retention_note = "unknown (no watch-time data)"
                if views > 0 and watch_time_secs > 0 and duration_secs > 0:
                    retention = min(0.95, watch_time_secs / (views * duration_secs))
                    metrics["retention"] = round(retention, 3)
                    metrics["retention_estimated"] = False   # MEASURED
                    retention_note = f"{retention * 100:.0f}%"
                elif views > 0:
                    metrics["retention_estimated"] = True    # koi guess nahi
                # V3.7: REAL CTR — sirf jab views METRIC available tha
                # (post_video_views na ho to views=0 "unknown" hai, 0% nahi)
                if "post_video_views" in ins:
                    ctr = ctr_from(views, impressions)
                    if ctr is not None:
                        metrics["ctr"] = ctr
                        metrics["impressions"] = impressions
                        logger.info("FB credit: %s → views=%d impressions=%s "
                                    "CTR=%.1f%% (REAL)", vid[:16], views, impressions,
                                    ctr * 100)
                else:
                    logger.info("FB credit: %s → views metric unavailable "
                                "(watch-time %ds real)", vid[:16], watch_time_secs)
                ml.credit_video(vid, metrics)
                credited += 1
                logger.info("FB credit: %s → views=%d watch=%ds retention=%s",
                            vid[:16], views, watch_time_secs, retention_note)
            except Exception as exc:
                logger.warning("FB video %s credit error: %s", vid[:16], exc)
        return credited
    except Exception as exc:
        logger.warning("Facebook video credit batch failed: %s", exc)
        return 0


# ── Instagram helpers ──────────────────────────────────────────────

def _ig_service():
    """Return (token, ig_id) or (None, None)."""
    tok = os.environ.get("IG_ACCESS_TOKEN", "")
    ig = os.environ.get("IG_BUSINESS_ACCOUNT_ID", "")
    if not tok or not ig:
        tok = os.environ.get("INSTAGRAM_ACCESS_TOKEN", tok)
        ig = os.environ.get("INSTAGRAM_USER_ID", ig)
        tok = os.environ.get("FACEBOOK_ACCESS_TOKEN", tok)  # fallback
    return (tok or None), (ig or None)


def instagram_metrics() -> dict:
    """IG account-level followers via Graph API."""
    tok, ig = _ig_service()
    if not tok or not ig:
        return {}
    try:
        import requests
        r = requests.get(
            f"https://graph.facebook.com/v25.0/{ig}",
            params={"access_token": tok, "fields": "followers_count,media_count"},
            timeout=30,
        )
        r.raise_for_status()
        d = r.json()
        return {"followers": d.get("followers_count", 0)}
    except Exception as exc:
        logger.warning("IG account metrics unavailable: %s", exc)
        return {}


def instagram_credit_videos(ml: LearningSystem) -> int:
    """Credit each uncredited IG Reel with real stats.

    Fetches IG media-level stats: plays, likes, comments, saved, shares.
    Also applies per-platform arm learning (IG learns separately from YT/FB).
    """
    # V3.7: pending (uncredited) + refreshable (stale: 0-views/CTR-less) — dono real data se update hote hain
    ids = [v for v in ml.pending_video_ids("instagram") if str(v) != "dry-run"]
    ids += [v for v in ml.refreshable_video_ids("instagram") if v not in ids]
    if not ids:
        return 0
    tok, ig = _ig_service()
    if not tok or not ig:
        logger.warning("IG credit skipped — no token/account configured")
        return 0
    try:
        import requests
        credited = 0
        for media_id in ids:
            try:
                # V3.7.2: VALID media-node fields — pehle plays/shares/
                # saved_count direct fields maang rahe thay jo IG media node
                # par exist nahi karte (400 → silent skip → IG credit kabhi
                # nahi hota tha). Ye sab INSIGHTS metrics hain.
                r = requests.get(
                    f"https://graph.facebook.com/v25.0/{media_id}",
                    params={
                        "access_token": tok,
                        "fields": "id,caption,media_type,permalink,timestamp,"
                                  "comments_count,like_count",
                    },
                    timeout=30,
                )
                if r.status_code >= 400:
                    logger.warning("IG media %s GET fail: %s", media_id[:16],
                                   r.text[:150])
                    continue
                data = r.json()
                likes = int(data.get("like_count", 0) or 0)
                comments = int(data.get("comments_count", 0) or 0)

                # insights: plays/reach/impressions/saved/shares (valid metrics)
                plays = impressions = saved = shares = 0
                ins = {}
                metric_status = {}
                try:
                    # V3.7.5: PER-METRIC collection (FB ki tarah) — har metric
                    # alag se, valid ones hi use hote hain
                    ins = {}
                    for m in ("plays", "video_views", "impressions", "reach",
                              "saved", "shares", "likes", "comments"):
                        try:
                            rm = requests.get(
                                f"https://graph.facebook.com/v25.0/{media_id}/insights",
                                params={"access_token": tok, "metric": m,
                                        "timeout": 30},
                                timeout=30)
                            if rm.status_code == 200:
                                ins[m] = _insight_totals(rm.json()).get(m, 0)
                                metric_status[m] = "measured"
                            else:
                                metric_status[m] = "unavailable"
                                logger.warning("IG metric %s (%s): %s", m,
                                               media_id[:16], rm.text[:120])
                        except Exception:
                            metric_status[m] = "error"
                    plays = int(ins.get("plays", 0) or 0) \
                        or int(ins.get("video_views", 0) or 0)
                    impressions = int(ins.get("impressions", 0) or 0) \
                        or int(ins.get("reach", 0) or 0)
                    saved = int(ins.get("saved", 0) or 0)
                    shares = int(ins.get("shares", 0) or 0)
                except Exception as exc:
                    logger.warning("IG insights %s failed: %s", media_id[:16], exc)

                # V3.6: fabricated retention hata di. Pehle
                # `retention = 0.10 + engagement_rate * 10` jaisa GUESS
                # bana kar reward function ko "measured retention" bata diya
                # jata tha — IG ke saves/shares real hain, retention nahi.
                # Ab sirf REAL metrics jate hain; reward.py ko retention
                # nahi milti to wo use "unknown" treat karta hai.
                metrics = {
                    "views": plays,
                    "likes": likes,
                    "comments": comments,
                    "shares": shares,
                    "saves": saved,
                    "retention_estimated": True,   # koi retention data nahi
                    "platform": "instagram",
                    "metric_status": metric_status,
                    "views_status": "measured" if ("plays" in ins or "video_views" in ins) else "unavailable",
                    "impressions_status": "measured" if ("impressions" in ins or "reach" in ins) else "unavailable",
                }
                # V3.7: REAL CTR — sirf jab views metric (plays/video_views)
                # ASAL mein available tha. Warna plays=0 "unknown" hai —
                # 0% CTR likhna jhoot hota (media product type restriction)
                if "plays" in ins or "video_views" in ins:
                    ctr = ctr_from(plays, impressions)
                    if ctr is not None:
                        metrics["ctr"] = ctr
                        metrics["impressions"] = impressions
                        logger.info("IG credit: %s → plays=%d impressions=%s "
                                    "CTR=%.1f%% (REAL)", media_id[:16],
                                    plays, impressions, ctr * 100)
                else:
                    logger.info("IG credit: %s → plays metric unavailable "
                                "(reach=%s saved=%s real)", media_id[:16],
                                impressions, saved)
                ml.credit_video(media_id, metrics)
                credited += 1
                logger.info("IG credit: %s → plays=%d likes=%d saved=%d "
                            "retention=unknown (real saves/shares credited)",
                            media_id[:16], plays, likes, saved)
            except Exception as exc:
                logger.debug("IG media %s credit error: %s", media_id[:16], exc)
        return credited
    except Exception as exc:
        logger.warning("Instagram video credit batch failed: %s", exc)
        return 0


# ── Growth rewards (REMOVED in V3.6 — fuzzy attribution) ────────────
# Channel-level growth (subs/followers gained) ko "recent arms" par reward
# dena REALITY par based nahi tha: growth kis VIDEO ki wajah se hui, ye koi
# nahi jaanta — sab recent formulas ko credit dena bandit ko dhoka tha.
# Video-level crediting (upar) hi asal attribution hai: har video ka real
# performance us ke EXACT arm tak jata hai.

def apply_growth_rewards(ml: LearningSystem, prog: dict) -> None:
    """V3.6: no-op — fuzzy growth attribution hata di gayi.

    Channel growth ko 'recent arms' par reward dena band kar diya hai
    kyunke ye bata hi nahi sakte ke growth kis video ki wajah se hui.
    Video-level crediting (upar) hi asal, exact attribution hai.
    """
    return  # intentional no-op


# ── Main ─────────────────────────────────────────────────────────────

def main():
    yt = youtube_metrics()
    fb = facebook_metrics()
    ig = instagram_metrics()

    prev = {}
    with contextlib.suppress(OSError, json.JSONDecodeError):
        prev = json.loads(PROGRESS_PATH.read_text(encoding="utf-8"))

    overrides = {}
    for plat, cur, key in (("youtube", yt, "subs"),
                           ("facebook", fb, "followers"),
                           ("instagram", ig, "followers")):
        if cur:
            overrides[plat] = {
                **cur,
                "last_growth": cur[key] - prev.get(plat, {}).get(key, cur[key]),
            }

    prog = update_progress(overrides=overrides or None)
    ml = LearningSystem()

    # 1) Credit individual videos per platform (real views → arm reward)
    yt_cred = youtube_credit_videos(ml)
    fb_cred = facebook_credit_videos(ml)
    ig_cred = instagram_credit_videos(ml)

    # 2) Reward channel-level growth
    apply_growth_rewards(ml, prog)

    # 3) Persist
    ml.save()

    # 4) Generate report
    summary = ml.summary()
    report = Path("data/metrics_report.md")
    report.parent.mkdir(exist_ok=True)

    # V3.7: REAL CTR table — credited videos jinke impressions+CTR aaye
    ctr_rows = []
    for vid, a in ml.data.get("attribution", {}).items():
        m = a.get("metrics") or {}
        if m.get("ctr") is not None:
            ctr_rows.append(
                f"- **{a.get('platform', '?'):10}** `{vid[:16]}` → "
                f"CTR **{m['ctr'] * 100:.1f}%** "
                f"({int(m.get('impressions', 0)):,} impressions → "
                f"{int(m.get('views', 0)):,} views)")
    ctr_block = ("\n".join(ctr_rows) if ctr_rows else
                 "_(abhi koi video impressions ke saath credit nahi hui — "
                 "CTR agle run mein aayega)_")

    availability_rows = []
    for vid, a in ml.data.get("attribution", {}).items():
        m = a.get("metrics") or {}
        if not m:
            continue
        availability_rows.append(
            f"- **{a.get('platform', '?'):10}** `{vid[:16]}` → "
            f"views={m.get('views_status', 'legacy/unknown')}, "
            f"impressions={m.get('impressions_status', 'legacy/unknown')}"
        )
    availability_block = ("\n".join(availability_rows) if availability_rows else
                          "_(abhi metric availability records nahi hain)_")

    report.write_text(
        f"# 📊 Coercion Files — Metrics Report\n\n"
        f"*Updated: {datetime.now(timezone.utc).isoformat()}*\n\n"
        f"**ML:** {summary['arms_tested']} arms · {summary['videos_tracked']} videos · "
        f"{summary['attributed_videos']} attributed · {summary['rewards']} rewards · "
        f"{summary['penalties']} penalties\n\n"
        f"**Videos credited this run:** YT={yt_cred} · FB={fb_cred} · IG={ig_cred}\n\n"
        f"## 🎯 REAL CTR (impressions-based, no guesses)\n\n{ctr_block}\n\n"
        f"## Metric availability (zero ≠ unavailable)\n\n{availability_block}\n\n"
        f"**Best formulas:** " +
        (", ".join(f"{b['pillar']}/{b['hook_style']} ({b['mean']})"
                   for b in summary["best_formulas"]) or "none yet") + "\n\n"
        f"```json\n{json.dumps(prog, indent=2, ensure_ascii=False)}\n```\n",
        encoding="utf-8",
    )
    print(f"Metrics synced → {report}")
    print(f"  YT credited={yt_cred} · FB credited={fb_cred} · IG credited={ig_cred}")
    if ctr_rows:
        print(f"  🎯 REAL CTR: {len(ctr_rows)} videos with impressions data")


if __name__ == "__main__":
    main()
