"""HTTP client for the FastAPI backend (src/wasel/). The frontend reads and writes only through this module.

API_BASE_URL points at the backend (default http://localhost:8000). Tests set OVERRIDE to an in-process
TestClient so the real backend runs without a socket."""
from __future__ import annotations

import os
import uuid
from typing import Any

import httpx

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000").rstrip("/")
TIMEOUT = float(os.environ.get("API_TIMEOUT_S", "30"))
OVERRIDE: Any = None                      # tests: an httpx.Client-compatible object (FastAPI TestClient)


class ApiError(Exception):
    """A 4xx/5xx from the backend (code + message from its error body) or no connection at all (status 0)."""

    def __init__(self, status: int, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.status, self.code, self.message = status, code, message


def new_visitor_id() -> str:
    return str(uuid.uuid4())


class Api:
    def __init__(self, visitor_id: str, base_url: str | None = None):
        self.base_url = (base_url or API_BASE_URL).rstrip("/")
        self.headers = {"X-Visitor-Id": visitor_id}  # public mode: sandbox owner; ignored in event/dev

    def _call(self, method: str, path: str, **kw) -> Any:
        try:
            if OVERRIDE is not None:
                r = OVERRIDE.request(method, path, headers=self.headers, **kw)
            else:
                r = httpx.request(method, self.base_url + path, headers=self.headers, timeout=TIMEOUT, **kw)
        except httpx.HTTPError as e:
            raise ApiError(0, "NO_CONNECTION", f"can't reach the backend at {self.base_url} ({type(e).__name__})") from e
        if r.status_code >= 400:
            err = {}
            if r.headers.get("content-type", "").startswith("application/json"):
                err = (r.json() or {}).get("error", {}) or {}
            raise ApiError(r.status_code, err.get("code", str(r.status_code)), err.get("message", r.text[:200]))
        return r.json()

    # --- reads -------------------------------------------------------------------------------------
    def health(self) -> dict:
        return self._call("GET", "/api/health")

    def orders(self, tier: str | None = None, include_collecting: bool = False, limit: int = 200) -> dict:
        params: dict[str, Any] = {"limit": limit, "include_collecting": str(include_collecting).lower()}
        if tier:
            params["tier"] = tier
        return self._call("GET", "/api/orders", params=params)

    def order(self, order_id: str) -> dict:
        return self._call("GET", f"/api/orders/{order_id}")

    def events(self, after: int = 0, order_id: str | None = None, limit: int = 200) -> dict:
        params: dict[str, Any] = {"after": after, "limit": limit}
        if order_id:
            params["order_id"] = order_id
        return self._call("GET", "/api/events", params=params)

    def recent_events(self, keep: int = 200, max_pages: int = 20) -> list[dict]:
        """The API pages forward from `after`; walk to the end and keep the newest `keep`."""
        out, after = [], 0
        for _ in range(max_pages):
            page = self.events(after=after, limit=200)
            out.extend(page["events"])
            if len(page["events"]) < 200:
                break
            after = page["last_seq"]
        return out[-keep:]

    def monitor(self) -> dict:
        return self._call("GET", "/api/monitor")

    def traces(self, role: str | None = None, limit: int = 100) -> dict:
        params: dict[str, Any] = {"limit": limit}
        if role:
            params["role"] = role
        return self._call("GET", "/api/traces", params=params)

    def eval_reports(self) -> dict:
        return self._call("GET", "/api/eval")

    def failures(self, source: str = "synthetic") -> dict:
        return self._call("GET", "/api/failures", params={"source": source})

    def failure_session(self, session_id: str, source: str = "synthetic") -> dict:
        return self._call("GET", f"/api/failures/sessions/{session_id}", params={"source": source})

    def impact(self) -> dict:
        return self._call("GET", "/api/metrics/impact")

    # --- commands ----------------------------------------------------------------------------------
    def ingest_paste(self, text: str, customer_name: str | None = None, structured: dict | None = None) -> dict:
        body: dict[str, Any] = {"kind": "paste", "text": text}
        if customer_name:
            body["customer_name"] = customer_name
        if structured:
            body["structured"] = {k: v for k, v in structured.items() if v not in (None, "")}
        return self._call("POST", "/api/orders/ingest", json=body)

    def try_order(self, order_id: str) -> dict:
        return self._call("POST", f"/api/orders/{order_id}/try")

    def simulate_text(self, conversation_id: str, text: str) -> dict:
        return self._call("POST", f"/api/conversations/{conversation_id}/simulate-reply",
                          json={"kind": "text", "text": text})

    def simulate_location(self, conversation_id: str, lat: float, lng: float) -> dict:
        return self._call("POST", f"/api/conversations/{conversation_id}/simulate-reply",
                          json={"kind": "location", "lat": lat, "lng": lng})

    def rescore(self, order_id: str) -> dict:
        return self._call("POST", f"/api/orders/{order_id}/rescore")

    def action(self, order_id: str, action: str) -> dict:
        return self._call("POST", f"/api/orders/{order_id}/actions", json={"action": action})

    def send_draft(self, draft_id: str) -> dict:
        return self._call("POST", f"/api/drafts/{draft_id}/send")
