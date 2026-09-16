"""Tests for platform credential resolution and FB epoch conversion."""
import json
from pathlib import Path

import platforms.youtube as yt
from platforms.facebook import _to_epoch


def test_youtube_resolve_none_without_env(monkeypatch):
    for k in ("YOUTUBE_CREDENTIALS", "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "REFRESH_TOKEN"):
        monkeypatch.delenv(k, raising=False)
    assert yt._resolve_credentials() == (None, False)


def test_youtube_resolve_split_oauth(monkeypatch, tmp_path):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "cid")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "csec")
    monkeypatch.setenv("REFRESH_TOKEN", "rtok")
    monkeypatch.delenv("YOUTUBE_CREDENTIALS", raising=False)
    path, is_path = yt._resolve_credentials()
    assert is_path is False
    data = json.loads(Path(path).read_text())
    assert data["client_id"] == "cid"
    assert data["refresh_token"] == "rtok"
    assert data["token_uri"] == "https://oauth2.googleapis.com/token"
    assert "youtube.upload" in " ".join(data["scopes"])


def test_youtube_resolve_raw_json(monkeypatch, tmp_path):
    raw = json.dumps({"type": "authorized_user", "client_id": "x"})
    monkeypatch.setenv("YOUTUBE_CREDENTIALS", raw)
    for k in ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "REFRESH_TOKEN"):
        monkeypatch.delenv(k, raising=False)
    path, is_path = yt._resolve_credentials()
    assert is_path is False
    assert json.loads(Path(path).read_text())["client_id"] == "x"


def test_fb_epoch_handles_none_str_and_naive():
    assert _to_epoch(None) == ""
    assert _to_epoch("not-a-date") == ""
    epoch = _to_epoch("2026-08-07T12:00:00+00:00")
    assert epoch.isdigit()
    assert int(epoch) > 1_700_000_000
    # Naive datetime must be treated as UTC rather than crash
    from datetime import datetime
    assert _to_epoch(datetime(2026, 8, 7, 12, 0, 0)).isdigit()


def test_instagram_duration_ms_fallback(monkeypatch):
    import platforms.instagram as ig
    # Force ffprobe failure path -> safe default without raising
    monkeypatch.setattr(ig.subprocess, "run", lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError()))
    assert ig._duration_ms("missing.mp4") == 60_000


def test_facebook_reels_handshake_phases(monkeypatch, tmp_path):
    """Verify Facebook Reels only uses valid {start, finish} phases and direct upload_url."""
    import requests

    from platforms.facebook import FacebookUploader

    fb = FacebookUploader()
    test_video = tmp_path / "test.mp4"
    test_video.write_bytes(b"dummy video binary content")

    calls = []

    class MockResponse:
        def __init__(self, json_data, status_code=200):
            self._json = json_data
            self.status_code = status_code
            self.text = json.dumps(json_data)

        def json(self):
            return self._json

        def raise_for_status(self):
            pass

    def mock_post(url, *args, **kwargs):
        data = kwargs.get("data")
        headers = kwargs.get("headers")
        calls.append({"url": url, "data": data, "headers": headers})
        if "video_reels" in url:
            if isinstance(data, dict) and data.get("upload_phase") == "start":
                return MockResponse({"video_id": "vid123", "upload_url": "https://rupload.facebook.com/mock-upload"})
            elif isinstance(data, dict) and data.get("upload_phase") == "finish":
                return MockResponse({"success": True, "id": "vid123"})
        if "rupload.facebook.com" in url:
            return MockResponse({"success": True})
        return MockResponse({"id": "vid123"})

    monkeypatch.setattr(requests, "post", mock_post)
    res = fb._reels_resumable("page1", "token1", str(test_video), "test caption")
    assert res.get("success") is True

    # Assert no invalid "transfer" phase was called
    for call in calls:
        if isinstance(call["data"], dict):
            phase = call["data"].get("upload_phase")
            assert phase in ("start", "finish", None), f"Invalid upload_phase {phase}"


def test_instagram_resumable_headers(monkeypatch, tmp_path):
    """Verify Instagram resumable upload sends octet-stream and Content-Length."""
    import requests

    from platforms.instagram import InstagramUploader

    ig = InstagramUploader()
    ig.token = "test-token"
    ig.ig_id = "test-ig-id"
    test_video = tmp_path / "test.mp4"
    test_video.write_bytes(b"1234567890")

    calls = []

    class MockResponse:
        def __init__(self, json_data, status_code=200):
            self._json = json_data
            self.status_code = status_code
            self.text = json.dumps(json_data)

        def json(self):
            return self._json

        def raise_for_status(self):
            pass

    def mock_post(url, *args, **kwargs):
        headers = kwargs.get("headers")
        calls.append({"url": url, "headers": headers, "data": kwargs.get("data")})
        if "/media" in url:
            return MockResponse({"id": "container_123", "uri": "https://rupload.facebook.com/mock-ig-upload"})
        return MockResponse({"result": "ok"})

    monkeypatch.setattr(requests, "post", mock_post)
    cid = ig._upload_resumable(str(test_video), "my caption")
    assert cid == "container_123"

    rupload_call = next(c for c in calls if "mock-ig-upload" in c["url"])
    assert rupload_call["headers"]["Content-Type"] == "application/octet-stream"
    assert rupload_call["headers"]["Content-Length"] == "10"
    assert rupload_call["headers"]["file_size"] == "10"
