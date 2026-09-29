"""WhatsApp Cloud API send. One text message per call, bounded retries on transient
failures only (transport errors, 408/429/5xx), no logging of the recipient or the body. Built only when
settings.wa_send_effective (never in public mode)."""
from __future__ import annotations

import logging
import time

import httpx

RETRYABLE_STATUS = {408, 429, *range(500, 600)}

log = logging.getLogger("cod.wa_send")
GRAPH = "https://graph.facebook.com"


class SendFailed(Exception):
    """The WhatsApp send failed. `reason` is a short code: an HTTP status (`http_400:131047` with the Graph error code
    when there is one), an exception class name, or `bad_response`.
    """

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


class WhatsAppSender:
    """Sends text messages through the WhatsApp Cloud (Graph) API. Blocking."""

    def __init__(self, token: str, phone_number_id: str, api_version: str = "v21.0", *, timeout_s: float = 10.0,
                 transport: httpx.BaseTransport | None = None, retries: int = 2, backoff_s: float = 0.5):
        self.token, self.phone_number_id = token, phone_number_id
        self.api_version = api_version or "v21.0"
        self.timeout_s, self._transport = timeout_s, transport
        self.retries, self.backoff_s = retries, backoff_s

    def send_text(self, to_e164: str, text: str) -> str:
        """Returns the wamid of the sent message. Raises SendFailed(reason).

        Transient failures (network errors, HTTP 408/429/5xx) are retried up to `retries` extra times with
        exponential backoff; permanent 4xx errors fail on the first attempt."""
        body = {"messaging_product": "whatsapp", "recipient_type": "individual", "to": to_e164.lstrip("+"),
                "type": "text", "text": {"preview_url": False, "body": text}}
        last_reason = "unknown"
        for attempt in range(self.retries + 1):
            try:
                with httpx.Client(timeout=self.timeout_s, transport=self._transport) as c:
                    r = c.post(f"{GRAPH}/{self.api_version}/{self.phone_number_id}/messages", json=body,
                               headers={"Authorization": f"Bearer {self.token}"})
            except httpx.HTTPError as e:
                last_reason = type(e).__name__
                if attempt < self.retries:
                    log.warning("whatsapp send transient error %s (attempt %d/%d), retrying",
                                last_reason, attempt + 1, self.retries + 1)
                    time.sleep(self.backoff_s * 2 ** attempt)
                    continue
                raise SendFailed(last_reason) from e
            if r.status_code != 200:
                try:
                    code = r.json().get("error", {}).get("code")
                except ValueError:
                    code = None
                reason = f"http_{r.status_code}" + (f":{code}" if code else "")
                log.warning("whatsapp send failed: http %s code %s", r.status_code, code)
                if r.status_code in RETRYABLE_STATUS and attempt < self.retries:
                    log.warning("whatsapp send retryable (attempt %d/%d), retrying", attempt + 1, self.retries + 1)
                    last_reason = reason
                    time.sleep(self.backoff_s * 2 ** attempt)
                    continue
                raise SendFailed(reason)
            try:
                return r.json()["messages"][0]["id"]
            except (ValueError, KeyError, IndexError, TypeError) as e:
                raise SendFailed("bad_response") from e
        raise SendFailed(last_reason)
