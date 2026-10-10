"""Render's proxy is not loopback, so uvicorn must read X-Forwarded-Proto from it (issue #73). Offline: no Docker, no network.
The redirect check runs the same proxy middleware uvicorn wraps the app in, with a non-loopback peer."""
from __future__ import annotations

import asyncio
from pathlib import Path

import httpx
from starlette.applications import Starlette
from starlette.staticfiles import StaticFiles
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

ROOT = Path(__file__).resolve().parents[2]


def test_slashless_redirect_keeps_the_forwarded_scheme(tmp_path):
    (tmp_path / "dashboard" / "inbox").mkdir(parents=True)
    (tmp_path / "dashboard" / "inbox" / "index.html").write_text("<!doctype html><title>Wasel</title>")
    from starlette.routing import Mount

    app = Starlette(routes=[Mount("/", app=StaticFiles(directory=tmp_path, html=True))])
    wrapped = ProxyHeadersMiddleware(app, trusted_hosts="*")

    async def fetch():
        transport = httpx.ASGITransport(app=wrapped, client=("203.0.113.9", 5000))
        async with httpx.AsyncClient(transport=transport, base_url="http://demo.example.com") as client:
            return await client.get("/dashboard/inbox", headers={"X-Forwarded-Proto": "https"}, follow_redirects=False)

    response = asyncio.run(fetch())
    assert response.status_code in (307, 308)
    assert response.headers["location"].startswith("https://demo.example.com/")


def test_render_cmd_trusts_the_proxy_headers():
    dockerfile = (ROOT / "deploy" / "render" / "Dockerfile").read_text()
    cmd = next(line for line in dockerfile.splitlines() if line.startswith("CMD"))
    assert "--proxy-headers" in cmd
    assert "--forwarded-allow-ips '*'" in cmd
