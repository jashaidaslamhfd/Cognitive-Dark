#!/usr/bin/env python3
"""
Coercion Files — YouTube Uploader (YouTube Data API v3).

• SEO title (≤100), keyword-first description, ≤500-char tags, category 27
• Credentials: accepts EITHER a file path OR a raw JSON string in
  YOUTUBE_CREDENTIALS (fixes the V1 bug where GH Actions passed JSON text
  that os.path.exists() never matched).
• Auto token-refresh so headless scheduled runs stay valid.
• Schedules via `publishAt` (private → public at peak time).
"""

import json
import logging
import os
import tempfile
from datetime import datetime, timedelta, timezone

from .base import BasePlatform

logger = logging.getLogger("youtube")


def _resolve_credentials() -> tuple:
    """Return (creds, is_path). Supports both old JSON and new OAuth env vars."""
    raw = os.environ.get("YOUTUBE_CREDENTIALS", "")

    # New way: separate OAuth secrets (tumhare secrets ke hisaab se)
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    refresh_token = os.environ.get("REFRESH_TOKEN")

    if client_id and client_secret and refresh_token:
        # V2.1: include token_uri + scopes so google-auth can refresh headless.
        # (V2 omitted token_uri → RefreshError on every scheduled run.)
        creds_dict = {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "token_uri": "https://oauth2.googleapis.com/token",
            "scopes": ["https://www.googleapis.com/auth/youtube.upload",
                       "https://www.googleapis.com/auth/youtube.readonly"],
            "type": "authorized_user",
        }
        tmp = os.path.join(tempfile.gettempdir(), "yt_oauth_creds.json")
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(creds_dict, fh)
        logger.info("Using OAuth credentials from separate secrets")
        return tmp, False

    # Old way
    if not raw:
        return None, False
    if os.path.exists(raw):
        return raw, True
    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("YOUTUBE_CREDENTIALS must be a JSON object")
        tmp = os.path.join(tempfile.gettempdir(), "yt_credentials.json")
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh)
        return tmp, False
    except Exception:
        return None, False


class YouTubeUploader(BasePlatform):
    name = "youtube"

    def upload(self, video_path, thumb_path, pkg, publish_at=None):
        if not os.path.exists(video_path):
            return self.result(False, error="video file missing: " + video_path)
        if self.dry_run:
            logger.info("📦 DRY-RUN youtube: %s (publish %s)", pkg["title"], publish_at)
            return self.result(True, dry_run=True, video_id="dry-run")

        cred_path, _ = _resolve_credentials()
        if not cred_path:
            return self._log_skipped("YOUTUBE_CREDENTIALS not configured")

        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload

            with open(cred_path, encoding="utf-8") as fh:
                info = json.load(fh)
            creds = Credentials.from_authorized_user_info(info)
            if (creds.expired or not creds.valid) and creds.refresh_token:
                creds.refresh(Request())      # keep token alive in headless runs
                with open(cred_path, "w", encoding="utf-8") as fh:
                    fh.write(creds.to_json())

            youtube = build("youtube", "v3", credentials=creds)
            privacy_status = os.environ.get("YT_PRIVACY_STATUS", "public").strip().lower()
            if privacy_status not in ("public", "private", "unlisted"):
                privacy_status = "public"

            body = {
                "snippet": {
                    "title": pkg["title"][:100],
                    "description": pkg["description"],
                    # V2.1: clean cap (V2's `x[:500] and x` was a no-op)
                    "tags": [t for t in (pkg.get("tags") or [])][:50],
                    "categoryId": os.environ.get("YT_CATEGORY_ID", "27"),
                    # V2.5: language signals → serves US/English audience first
                    "defaultLanguage": "en",
                    "defaultAudioLanguage": "en-US",
                },
                "status": {
                    "privacyStatus": privacy_status,
                    "selfDeclaredMadeForKids": False,
                },
            }
            # Only scheduled private videos can use publishAt; public videos go live immediately
            if publish_at and privacy_status == "private":
                # V2.1 FIX: publish_at is tz-AWARE (scheduler) → compare against
                # tz-aware now. V2 compared aware-vs-naive → TypeError on EVERY run.
                pa = publish_at
                if isinstance(pa, str):
                    pa = datetime.fromisoformat(pa)
                if pa.tzinfo is None:
                    pa = pa.replace(tzinfo=timezone.utc)
                now = datetime.now(timezone.utc)
                if pa - now > timedelta(hours=23):
                    pa = now + timedelta(hours=23)   # publishAt must be < 24h out
                # YouTube wants RFC3339 UTC with Z suffix
                body["status"]["publishAt"] = pa.astimezone(timezone.utc).strftime(
                    "%Y-%m-%dT%H:%M:%S.000Z")

            media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)
            req = youtube.videos().insert(part="snippet,status", body=body,
                                          media_body=media)
            response = None
            while response is None:
                status, response = req.next_chunk()
                if status and int(status.progress() * 100) % 25 == 0:
                    logger.info("⬆️  YT upload %d%%", int(status.progress() * 100))
            vid = response["id"]
            # V2.2.1: thumbnail failure must NOT kill the upload — the video
            # is already in. (Custom thumbnails also need channel phone-
            # verification in Studio; unverified accounts 403 here.)
            if thumb_path and os.path.exists(thumb_path):
                try:
                    youtube.thumbnails().set(
                        videoId=vid, media_body=MediaFileUpload(thumb_path)).execute()
                except Exception as texc:
                    logger.warning("Thumbnail set failed (non-fatal): %s", texc)
            logger.info("✅ YouTube uploaded: https://youtu.be/%s", vid)
            return self.result(True, video_id=vid, url=f"https://youtu.be/{vid}")
        except Exception as exc:
            logger.error("YouTube upload failed: %s", exc)
            return self.result(False, error=str(exc))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    y = YouTubeUploader(dry_run=True)
    print(y.upload("/tmp/x.mp4", None, {"title": "T", "description": "D", "tags": []}))
