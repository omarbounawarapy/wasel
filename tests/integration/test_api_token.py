"""Access token on /api outside public mode (API_TOKEN, 24+ characters)."""
from __future__ import annotations

from tests.integration.conftest import make_client

TOKEN = "t" * 24


def test_api_needs_the_token_when_set(tmp_path):
    c, _, _ = make_client(tmp_path, "dev", api_token=TOKEN)
    with c:
        r = c.get("/api/orders")
        assert r.status_code == 401 and r.json()["error"]["code"] == "UNAUTHORIZED"
        assert c.get("/api/orders", headers={"Authorization": "Bearer " + "x" * 24}).status_code == 401
        assert c.get("/api/orders", headers={"Authorization": "Bearer " + TOKEN}).status_code == 200
        assert c.get("/api/orders", headers={"X-Api-Token": TOKEN}).status_code == 200
        assert c.get("/docs").status_code == 401
        assert c.get("/openapi.json").status_code == 401


def test_health_and_session_stay_open(tmp_path):
    c, _, _ = make_client(tmp_path, "dev", api_token=TOKEN)
    with c:
        assert c.get("/api/health").status_code == 200
        assert c.get("/api/session").json() == {"required": True, "authenticated": False}


def test_login_sets_an_httponly_cookie_that_unlocks_the_api(tmp_path):
    c, _, _ = make_client(tmp_path, "dev", api_token=TOKEN)
    with c:
        assert c.post("/api/session", json={"token": "nope"}).status_code == 401
        r = c.post("/api/session", json={"token": TOKEN})
        assert r.status_code == 200
        cookie = r.headers["set-cookie"].lower()
        assert "httponly" in cookie and "samesite=strict" in cookie
        assert c.get("/api/orders").status_code == 200
        assert c.get("/api/session").json()["authenticated"] is True
        c.delete("/api/session")
        assert c.get("/api/orders").status_code == 401


def test_short_token_is_ignored_and_public_mode_is_never_gated(tmp_path):
    c, _, _ = make_client(tmp_path, "dev", api_token="short")
    with c:
        assert c.get("/api/orders").status_code == 200
        assert c.get("/api/session").json()["required"] is False
    (tmp_path / "p").mkdir()
    c, _, _ = make_client(tmp_path / "p", "public", api_token=TOKEN)
    with c:
        assert c.get("/api/health").json()["mode"] == "public"
        assert c.get("/api/orders", headers={"X-Visitor-Id": "00000000-0000-4000-8000-00000000000a"}).status_code == 200


def test_admin_reset_keeps_its_own_token(tmp_path):
    c, _, _ = make_client(tmp_path, "dev", api_token=TOKEN)
    with c:
        assert c.post("/api/admin/reset", headers={"X-Admin-Token": "x" * 24}).status_code == 200
