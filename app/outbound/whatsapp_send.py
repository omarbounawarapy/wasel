"""WhatsApp Cloud API send (S-2; 01 §4, SD §9). One text message per call, no retries, no logging of the
recipient or the body. Built only when settings.wa_send_effective (never in public mode)."""
from __future__ import annotations

import logging

import httpx

log = logging.getLogger("cod.wa_send")
GRAPH = "https://graph.facebook.com"


class SendFailed(Exception):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


class WhatsAppSender:
    def __init__(self, token: str, phone_number_id: str, api_version: str = "v21.0", *, timeout_s: float = 10.0,
                 transport: httpx.BaseTransport | None = None):
        self.token, self.phone_number_id = token, phone_number_id
        self.api_version = api_version or "v21.0"
        self.timeout_s, self._transport = timeout_s, transport

    def send_text(self, to_e164: str, text: str) -> str:
        """Returns the wamid of the sent message. Raises SendFailed(reason)."""
        body = {"messaging_product": "whatsapp", "recipient_type": "individual", "to": to_e164.lstrip("+"),
                "type": "text", "text": {"preview_url": False, "body": text}}
        try:
            with httpx.Client(timeout=self.timeout_s, transport=self._transport) as c:
                r = c.post(f"{GRAPH}/{self.api_version}/{self.phone_number_id}/messages", json=body,
                           headers={"Authorization": f"Bearer {self.token}"})
        except httpx.HTTPError as e:
            raise SendFailed(type(e).__name__) from e
        if r.status_code != 200:
            try:
                code = r.json().get("error", {}).get("code")
            except ValueError:
                code = None
            log.warning("whatsapp send failed: http %s code %s", r.status_code, code)
            raise SendFailed(f"http_{r.status_code}" + (f":{code}" if code else ""))
        try:
            return r.json()["messages"][0]["id"]
        except (ValueError, KeyError, IndexError, TypeError) as e:
            raise SendFailed("bad_response") from e
