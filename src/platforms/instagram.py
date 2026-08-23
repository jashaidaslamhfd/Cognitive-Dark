#!/usr/bin/env python3
"""
Coercion Files — Instagram Uploader (Instagram Graph API, Reels).

Flow (documented 2026 API):
  1) POST /{ig-user-id}/media  {media_type: REELS, video_url|upload_type}
  2) poll /{container-id}?fields=status_code until FINISHED
  3) POST /{ig-user-id}/media_publish {creation_id}

Two upload paths:
  • PUBLIC URL : if IG_VIDEO_URL_BASE is set (host the mp4 on a CDN/bucket),
    pass `video_url`. Most reliable.
  • RESUMABLE  : direct chunked upload to rupload.ig-api-upload — no hosting
    needed; works from ephemeral runners (GitHub Actions).
Requires an Instagram Business/Creator account LINKED to the Facebook Page and
an access token with instagram_content_publish + instagram_basic.
"""

import logging
import mimetypes
import os
import subprocess
import time

import requests

from .base import BasePlatform

logger = logging.getLogger("instagram")

# V2.2.3: use the graph.FACEBOOK host — it accepts the long-lived PAGE token
# (the graph.instagram.com host needs an IG-native token, which is why every
# run died with 'Cannot parse access token'). Resumable uploads move to the
# facebook rupload host accordingly.
GRAPH = "https://graph.facebook.com"
API_VERSION = "v25.0"
RUP_URL = "https://rupload.facebook.com/ig-api-upload"


def _duration_ms(video_path: str) -> int:
    """Video duration in MILLISECONDS (IG resumable container requirement)."""
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", video_path],
            capture_output=True, text=True, timeout=30, check=True)
        return int(float(r.stdout.strip()) * 1000)
    except Exception:
        return 60_000  # safe default: 60s


class InstagramUploader(BasePlatform):
    name = "instagram"

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    def _container(self, payload) -> str:
        url = f"{GRAPH}/{API_VERSION}/{self.ig_id}/media"
        r = requests.post(url, params={"access_token": self.token}, data=payload,
                          headers=self._headers(), timeout=120)
        if r.status_code >= 400:
            # V2.1.1: surface the API error body (token/scope/link issues show here)
            raise RuntimeError(f"IG container HTTP {r.status_code}: {r.text[:500]}")
        cid = r.json().get("id")
        if not cid:
            raise RuntimeError(f"no container id: {r.text[:300]}")
        return cid

    def _wait_ready(self, container_id: str, timeout_s: int = 300) -> None:
        url = f"{GRAPH}/{API_VERSION}/{container_id}"
        for _ in range(timeout_s // 10):
            r = requests.get(url, params={"access_token": self.token,
                                          "fields": "status_code"}, timeout=30)
            r.raise_for_status()
            st = r.json().get("status_code")
            if st == "FINISHED":
                return
            if st == "ERROR":
                raise RuntimeError(f"IG container ERROR: {r.text}")
            time.sleep(10)
        raise TimeoutError("IG container did not finish processing")

    def _publish(self, container_id: str) -> str:
        url = f"{GRAPH}/{API_VERSION}/{self.ig_id}/media_publish"
        r = requests.post(url, params={"access_token": self.token},
                          data={"creation_id": container_id},
                          headers=self._headers(), timeout=120)
        r.raise_for_status()
        media_id = r.json().get("id")
        if not media_id:
            raise RuntimeError(f"IG publish returned no media id: {r.text[:300]}")
        return media_id

    def _upload_resumable(self, video_path: str, caption: str = "") -> str:
        """Chunked direct upload (no public hosting needed)."""
        size = os.path.getsize(video_path)
        # V2.1 FIX: video_length must be duration in MILLISECONDS (V2 sent the
        # file size in bytes → container rejected / wrong metadata), and the
        # caption was dropped entirely on this path (Reels published silent of text).
        payload = {
            "media_type": "REELS",
            "upload_type": "resumable",
            "video_length": str(_duration_ms(video_path)),
            "share_to_feed": "true",
        }
        if caption:
            payload["caption"] = caption[:2200]
        # Create the container here so we get the EXACT rupload URI the API
        # returns (v26.0+). Building `{RUP_URL}/{API_VERSION}/{id}` ourselves
        # hit a 404 — Meta versions the upload host independently of the
        # Graph API version (observed: container uri = .../ig-api-upload/v26.0).
        url = f"{GRAPH}/{API_VERSION}/{self.ig_id}/media"
        r = requests.post(url, params={"access_token": self.token}, data=payload,
                          headers=self._headers(), timeout=120)
        if r.status_code >= 400:
            raise RuntimeError(f"IG container HTTP {r.status_code}: {r.text[:500]}")
        data = r.json()
        container = data.get("id")
        if not container:
            raise RuntimeError(f"no container id: {data}")
        upload_uri = data.get("uri") or f"{RUP_URL}/{API_VERSION}/{container}"
        mime = mimetypes.guess_type(video_path)[0] or "video/mp4"
        # Official IG resumable protocol: POST the raw file to the returned
        # URI with OAuth auth, offset, and file_size. Bearer on this endpoint
        # can produce a misleading 404 even when the Graph token is valid.
        with open(video_path, "rb") as fh:
            r = requests.post(
                upload_uri, data=fh,
                headers={"Authorization": f"OAuth {self.token}",
                         "offset": "0",
                         "file_size": str(size),
                         "Content-Type": mime}, timeout=1800)
        if r.status_code >= 400:
            raise RuntimeError(f"IG rupload HTTP {r.status_code}: {r.text[:400]}")
        return container

    def upload(self, video_path, thumb_path, pkg, publish_at=None):
        self.token = os.environ.get("IG_ACCESS_TOKEN", "") or os.environ.get("FB_ACCESS_TOKEN", "")
        self.ig_id = os.environ.get("IG_BUSINESS_ACCOUNT_ID", "") or os.environ.get("INSTAGRAM_USER_ID", "")
        if not self.token or not self.ig_id:
            return self._log_skipped("IG_ACCESS_TOKEN / IG_BUSINESS_ACCOUNT_ID not configured")
        if not os.path.exists(video_path):
            return self.result(False, error="video file missing")

        if self.dry_run:
            logger.info("📦 DRY-RUN instagram: %s", pkg["title"])
            return self.result(True, dry_run=True, video_id="dry-run")

        try:
            base = os.environ.get("IG_VIDEO_URL_BASE", "").rstrip("/")
            if base:
                video_url = f"{base}/{os.path.basename(video_path)}"
                container = self._container({
                    "media_type": "REELS",
                    "video_url": video_url,
                    "caption": pkg["description"][:2200],
                    "share_to_feed": "true",
                })
            else:
                container = self._upload_resumable(video_path,
                                                   caption=pkg.get("description", ""))
            self._wait_ready(container)
            media_id = self._publish(container)
            verified = False
            try:
                vr = requests.get(
                    f"{GRAPH}/{API_VERSION}/{media_id}",
                    params={"access_token": self.token,
                            "fields": "id,permalink,timestamp"}, timeout=30)
                verified = vr.status_code == 200 and vr.json().get("id") == media_id
            except Exception as verify_exc:
                logger.warning("Instagram publish verification unavailable: %s", verify_exc)
            logger.info("✅ Instagram Reel: %s (delivery_verified=%s)", media_id, verified)
            return self.result(True, media_id=media_id,
                               delivery_verified=verified,
                               url=f"https://instagram.com/reel/{media_id}")
        except Exception as exc:
            logger.error("Instagram upload failed: %s", exc)
            return self.result(False, error=str(exc))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    i = InstagramUploader(dry_run=True)
    print(i.upload("/tmp/x.mp4", None, {"title": "T", "description": "D"}))
