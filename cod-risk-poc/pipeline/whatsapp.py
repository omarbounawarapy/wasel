"""WhatsApp Cloud API (Meta): send messages, verify and parse webhooks.

Sending is one HTTPS call per message to graph.facebook.com. Receiving has no polling endpoint on Meta's
side: Meta POSTs every inbound message and delivery status to a webhook. `webhook.py` verifies the
signature and writes them to SQLite through `handle_webhook`; the app polls that table.

Synthetic orders have no phone numbers, so every send goes to one configured demo number
(WHATSAPP_DEMO_TO). A public demo URL can never message anyone else.
"""
import datetime as dt
import hashlib
import hmac
import re
from typing import NamedTuple

import requests

from . import config, db


class WhatsAppError(RuntimeError):
    def __init__(self, message: str, code: int | None = None):
        super().__init__(message)
        self.code = code


# Codes a demo is likely to hit, with what to do about them.
HINTS = {
    131047: "more than 24 h since the customer last wrote. Ask them to message the business number first, "
            "or send the opener template",
    131030: "this number isn't in the test number's allowed list. Add it under WhatsApp > API Setup > To",
    190: "access token invalid or expired. Temporary tokens last 24 h: generate a new one in API Setup",
    100: "bad parameter. Check WHATSAPP_PHONE_NUMBER_ID: it is the phone number ID from API Setup, "
         "not the phone number or the WhatsApp Business Account ID",
    131026: "undeliverable: the number may not be on WhatsApp",
    130429: "throughput limit hit, wait and retry",
    131056: "too many messages to this number in a short time, wait and retry",
}


def explain_error(code: int | None, message: str) -> str:
    hint = HINTS.get(code)
    return f"{message} ({code})" + (f": {hint}" if hint else "") if code else message


def normalize(number: str) -> str:
    """'+216 20 123 456' -> '21620123456' (the format the API takes and webhooks send)."""
    digits = re.sub(r"\D", "", number or "")
    return digits[2:] if digits.startswith("00") else digits


class WhatsAppClient:
    def __init__(self, token: str, phone_number_id: str, demo_to: str, api_version: str = config.WA_API_VERSION):
        self.token, self.phone_number_id = token, phone_number_id
        self.demo_to = normalize(demo_to)
        self.base = f"https://graph.facebook.com/{api_version}/{phone_number_id}"
        self.url = f"{self.base}/messages"

    def _call(self, method: str, url: str, **kw) -> dict:
        send = requests.get if method == "GET" else requests.post
        try:
            r = send(url, headers={"Authorization": f"Bearer {self.token}"}, timeout=config.WA_TIMEOUT_S, **kw)
        except requests.RequestException as e:
            raise WhatsAppError(f"network error: {e}") from e
        try:
            data = r.json()
        except ValueError:
            data = {}
        if r.status_code >= 400 or "error" in data:
            err = data.get("error") or {}
            detail = (err.get("error_data") or {}).get("details") or err.get("message") or f"HTTP {r.status_code}"
            raise WhatsAppError(explain_error(err.get("code"), detail), err.get("code"))
        return data

    def phone_info(self) -> dict:
        """The business number behind WHATSAPP_PHONE_NUMBER_ID. Proves the token and the ID without sending."""
        return self._call("GET", self.base, params={"fields": "display_phone_number,verified_name,quality_rating"})

    def _post(self, payload: dict) -> str:
        data = self._call("POST", self.url, json=payload)
        try:
            return data["messages"][0]["id"]
        except (KeyError, IndexError, TypeError) as e:
            raise WhatsAppError(f"unexpected response: {data}") from e

    @staticmethod
    def _base(to: str, reply_to: str | None) -> dict:
        payload = {"messaging_product": "whatsapp", "recipient_type": "individual", "to": to}
        if reply_to:
            payload["context"] = {"message_id": reply_to}
        return payload

    def send_text(self, to: str, body: str, reply_to: str | None = None) -> str:
        return self._post({**self._base(to, reply_to), "type": "text", "text": {"body": body}})

    def send_buttons(self, to: str, body: str, buttons: list[tuple[str, str]], reply_to: str | None = None) -> str:
        return self._post({**self._base(to, reply_to), "type": "interactive", "interactive": {
            "type": "button", "body": {"text": body},
            "action": {"buttons": [{"type": "reply", "reply": {"id": i, "title": t}} for i, t in buttons]}}})

    def send_location_request(self, to: str, body: str) -> str:
        return self._post({**self._base(to, None), "type": "interactive", "interactive": {
            "type": "location_request_message", "body": {"text": body}, "action": {"name": "send_location"}}})

    def send_template(self, to: str, name: str, lang: str) -> str:
        return self._post({**self._base(to, None), "type": "template",
                           "template": {"name": name, "language": {"code": lang}}})


def get_client() -> WhatsAppClient | None:
    token, pnid, to = (config.secret(k) for k in ("WHATSAPP_TOKEN", "WHATSAPP_PHONE_NUMBER_ID", "WHATSAPP_DEMO_TO"))
    return WhatsAppClient(token, pnid, to) if token and pnid and normalize(to) else None


def opener_template() -> tuple[str, str]:
    """Business-initiated messages outside the 24 h window must be approved templates. Every new
    WhatsApp app gets 'hello_world'; a real deployment would register a utility template per action."""
    return (config.secret("WHATSAPP_TEMPLATE") or "hello_world", config.secret("WHATSAPP_TEMPLATE_LANG") or "en_US")


# --- reply interfaces --------------------------------------------------------------------------

# Button titles: max 20 characters. The button ID carries the order, so a tap maps to it exactly.
BUTTON_TITLES = {
    "confirm": {"derja_latin": "EYH, nakked", "fr": "Oui, je confirme", "ar": "إيه، نأكّد"},
    "cancel": {"derja_latin": "LE, nbatel", "fr": "Non, annuler", "ar": "لا، نبطّل"},
}
LOCATION_REQUEST = {
    "derja_latin": "Ab3athelna el location mte3ek bech el livreur yal9ak bel sehel.",
    "fr": "Envoyez-nous votre position pour que le livreur vous trouve facilement.",
    "ar": "ابعثلنا اللوكاسيون متاعك باش الليفرور يلقاك بالساهل.",
}
QUICK_REPLIES = {
    "derja_latin": ["Ya3tik essa7a, t2akedet el commande.", "Mafhemnech, tnajem t3awed?",
                    "Behi, el commande tbatlet."],
    "fr": ["Merci, votre commande est confirmée.", "Pouvez-vous préciser, s'il vous plaît ?",
           "C'est noté, la commande est annulée."],
    "ar": ["يعطيك الصحة، تأكدت الكوموند.", "ما فهمناش، تنجم تعاود؟", "باهي، الكوموند تبطلت."],
}


def buttons_for(order_id: str, register: str) -> list[tuple[str, str]]:
    return [(f"{intent}:{order_id}", BUTTON_TITLES[intent][register]) for intent in ("confirm", "cancel")]


# A whole-message yes/no, so "le livreur est passé" isn't read as "LE" (no).
_END = r"[\s!.,؟?👍🙏]*"
_YES = re.compile(r"(eyh|eh|ey+|iy+eh|ih|oui+|yes|ok|okay|d'accord|nakked|n2aked|bahi|behi|mrigel|"
                  r"إيه|ايه|اي|نعم|أكيد|اكيد|باهي|مريقل)" + _END, re.IGNORECASE)
_NO = re.compile(r"(le|la|lé|non|no|nbatel|batel|لا|نبطل|بطل)" + _END, re.IGNORECASE)


def text_intent(text: str) -> str:
    t = (text or "").strip()
    if _YES.fullmatch(t):
        return "confirm"
    if _NO.fullmatch(t):
        return "cancel"
    return "text"


def button_intent(button_id: str | None) -> tuple[str, str | None]:
    intent, _, order_id = (button_id or "").partition(":")
    return (intent, order_id or None) if intent in ("confirm", "cancel") else ("text", None)


# --- webhooks ----------------------------------------------------------------------------------

def verify_signature(raw_body: bytes, header: str | None, app_secret: str) -> bool:
    """X-Hub-Signature-256 is 'sha256=' + HMAC-SHA256(app secret, raw request body)."""
    if not app_secret or not header or not header.startswith("sha256="):
        return False
    expected = hmac.new(app_secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header[len("sha256="):])


def _iso(ts) -> str | None:
    try:
        return dt.datetime.fromtimestamp(int(ts), dt.timezone.utc).isoformat(timespec="seconds")
    except (TypeError, ValueError):
        return None


def parse_webhook(payload: dict) -> tuple[list[dict], list[dict]]:
    """Split a webhook body into inbound messages and delivery statuses of our outbound messages."""
    inbound, statuses = [], []
    for entry in payload.get("entry") or []:
        for change in entry.get("changes") or []:
            if change.get("field") != "messages":
                continue
            v = change.get("value") or {}
            names = {c.get("wa_id"): (c.get("profile") or {}).get("name") for c in v.get("contacts") or []}
            for m in v.get("messages") or []:
                typ = m.get("type")
                rec = dict(wamid=m.get("id"), from_wa=m.get("from"), profile_name=names.get(m.get("from")),
                           type=typ, intent="text", text=None, button_id=None, latitude=None, longitude=None,
                           context_id=(m.get("context") or {}).get("id"), sent_at=_iso(m.get("timestamp")))
                if typ == "text":
                    rec["text"] = (m.get("text") or {}).get("body", "")
                    rec["intent"] = text_intent(rec["text"])
                elif typ == "interactive":
                    i = m.get("interactive") or {}
                    reply = i.get("button_reply") or i.get("list_reply") or {}
                    rec["button_id"], rec["text"] = reply.get("id"), reply.get("title")
                    rec["intent"] = button_intent(rec["button_id"])[0]
                elif typ == "button":  # quick-reply button on a template
                    b = m.get("button") or {}
                    rec["button_id"], rec["text"] = b.get("payload"), b.get("text")
                    rec["intent"] = button_intent(rec["button_id"])[0]
                    if rec["intent"] == "text":
                        rec["intent"] = text_intent(rec["text"])
                elif typ == "location":
                    loc = m.get("location") or {}
                    rec["latitude"], rec["longitude"] = loc.get("latitude"), loc.get("longitude")
                    rec["text"] = ", ".join(x for x in (loc.get("name"), loc.get("address")) if x) or None
                    rec["intent"] = "location"
                else:
                    rec["text"] = f"[{typ} message]"
                if rec["wamid"] and rec["from_wa"]:
                    inbound.append(rec)
            for s in v.get("statuses") or []:
                errs = s.get("errors") or []
                error = None
                if errs:
                    e = errs[0]
                    detail = (e.get("error_data") or {}).get("details") or e.get("title") or e.get("message") or ""
                    error = explain_error(e.get("code"), detail)
                if s.get("id") and s.get("status"):
                    statuses.append(dict(provider_id=s["id"], status=s["status"], error=error))
    return inbound, statuses


def handle_webhook(conn, payload: dict) -> dict:
    inbound, statuses = parse_webhook(payload)
    new = 0
    for rec in inbound:
        _, button_order = button_intent(rec["button_id"])
        rec["order_id"] = db.order_for_inbound(conn, rec["from_wa"], button_order, rec["context_id"])
        new += db.save_inbound(conn, rec)
    known = sum(db.update_delivery(conn, s["provider_id"], s["status"], s["error"]) for s in statuses)
    return {"messages": new, "duplicates": len(inbound) - new, "statuses": known}


# --- sending -----------------------------------------------------------------------------------

class Sent(NamedTuple):
    ok: bool
    error: str = ""


def window_open(conn, wa_id: str) -> bool:
    """Free-form messages (text, buttons, location requests) need a customer message in the last 24 h."""
    last = db.last_inbound_at(conn, wa_id)
    if not last:
        return False
    age = dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(last)
    return age < dt.timedelta(hours=config.WA_WINDOW_HOURS)


def deliver(conn, client: WhatsAppClient | None, order_id: str | None, kind: str, body: str, source: str, *,
            buttons: list[tuple[str, str]] | None = None, location_request: bool = False,
            template: tuple[str, str] | None = None, reply_to: str | None = None) -> Sent:
    """Send through WhatsApp when configured, else record a mock send. The row is claimed before the
    API call (no double send on a double click) and released if Meta refuses it (the seller can retry)."""
    if client is None:
        return Sent(True) if db.send_message(conn, order_id, kind, body, source) else Sent(False, "already sent")
    if db.wa_sends_today(conn) >= config.WA_SENDS_PER_DAY:
        return Sent(False, f"daily WhatsApp cap reached ({config.WA_SENDS_PER_DAY} sends)")
    msg_id = db.claim_message(conn, order_id, kind, body, source, channel="whatsapp", to_wa=client.demo_to)
    if msg_id is None:
        return Sent(False, "already sent")
    try:
        if template:
            wamid = client.send_template(client.demo_to, *template)
        elif location_request:
            wamid = client.send_location_request(client.demo_to, body)
        elif buttons:
            wamid = client.send_buttons(client.demo_to, body, buttons, reply_to)
        else:
            wamid = client.send_text(client.demo_to, body, reply_to)
    except WhatsAppError as e:
        db.mark_failed(conn, msg_id, str(e))
        return Sent(False, str(e))
    db.mark_accepted(conn, msg_id, wamid)
    return Sent(True)
