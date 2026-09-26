"""Check the live WhatsApp setup step by step before a demo. Reads the same .env / secrets as the app.

    python scripts/whatsapp_check.py                          # config + token + phone number ID (sends nothing)
    python scripts/whatsapp_check.py --send "test from COD"   # + a real text to WHATSAPP_DEMO_TO (needs the 24 h window)
    python scripts/whatsapp_check.py --template               # + hello_world to WHATSAPP_DEMO_TO (works outside it)
    python scripts/whatsapp_check.py --webhook https://<tunnel host>   # + webhook.py reachable through the tunnel

--webhook runs Meta's verification handshake against the URL, then posts a signed status update for an
unknown message ID: it proves the tunnel, the verify token, the app secret and the DB write, and stores nothing.
Exit code 0 when every check that ran passed.
"""
import argparse
import hashlib
import hmac
import json
import sys
import time
import uuid
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline import config, db, whatsapp  # noqa: E402

KEYS = ["WHATSAPP_TOKEN", "WHATSAPP_PHONE_NUMBER_ID", "WHATSAPP_DEMO_TO", "WHATSAPP_APP_SECRET",
        "WHATSAPP_VERIFY_TOKEN"]


class Report:
    def __init__(self):
        self.failed = 0

    def ok(self, msg: str) -> None:
        print(f"  OK    {msg}")

    def fail(self, msg: str) -> None:
        self.failed += 1
        print(f"  FAIL  {msg}")

    def warn(self, msg: str) -> None:
        print(f"  WARN  {msg}")


def check_config(r: Report) -> dict[str, str]:
    print("Config (.env, shell or .streamlit/secrets.toml)")
    vals = {k: config.secret(k) for k in KEYS}
    for k, v in vals.items():
        (r.ok if v else r.fail)(f"{k} {'set' if v else 'missing'}")
    to = whatsapp.normalize(vals["WHATSAPP_DEMO_TO"])
    if to and len(to) < 10:
        r.fail(f"WHATSAPP_DEMO_TO={to} looks like it has no country code (Tunisia: 216 + 8 digits)")
    elif to:
        r.ok(f"messages go to {to}")
    return vals


def check_meta(r: Report, client: whatsapp.WhatsAppClient) -> bool:
    print("Meta Graph API")
    try:
        info = client.phone_info()
    except whatsapp.WhatsAppError as e:
        r.fail(f"token / phone number ID refused: {e}")
        return False
    r.ok(f"token works, business number {info.get('display_phone_number')} "
         f"({info.get('verified_name')}, quality {info.get('quality_rating', 'n/a')})")
    return True


def check_window(r: Report, client: whatsapp.WhatsAppClient) -> None:
    conn = db.connect() if config.DB_PATH.exists() else None
    last = db.last_inbound_at(conn, client.demo_to) if conn else None
    if conn and whatsapp.window_open(conn, client.demo_to):
        r.ok(f"24 h window open (last message from the demo phone at {last} UTC)")
    else:
        r.warn("no message from the demo phone in the last 24 h (as far as app.db knows): free-form sends, "
               "buttons and location requests will fail with 131047. Message the business number from the "
               "demo phone first, or use --template")


def send(r: Report, client: whatsapp.WhatsAppClient, text: str | None, template: bool) -> None:
    print("Send")
    try:
        if template:
            name, lang = whatsapp.opener_template()
            wamid = client.send_template(client.demo_to, name, lang)
            what = f"template {name} ({lang})"
        else:
            wamid = client.send_text(client.demo_to, text)
            what = "text"
    except whatsapp.WhatsAppError as e:
        r.fail(f"send refused: {e}")
        return
    r.ok(f"Meta accepted the {what}: {wamid}. Check the demo phone; if it never arrives, webhook.py logs "
         "a 'failed' status with the reason")


def check_webhook(r: Report, base: str, verify_token: str, app_secret: str) -> None:
    url = base.rstrip("/")
    url = url if url.endswith("/webhook") else url + "/webhook"
    print(f"Webhook {url}")
    challenge = uuid.uuid4().hex[:10]
    try:
        g = requests.get(url, params={"hub.mode": "subscribe", "hub.verify_token": verify_token,
                                      "hub.challenge": challenge}, timeout=10)
    except requests.RequestException as e:
        r.fail(f"not reachable: {e}. Is webhook.py running and the tunnel up?")
        return
    if g.status_code == 200 and g.text == challenge:
        r.ok("verification handshake passed: paste this URL and the verify token into Meta's webhook config")
    elif g.status_code == 403:
        r.fail("handshake refused: webhook.py has a different WHATSAPP_VERIFY_TOKEN (restart it after editing .env)")
    else:
        r.fail(f"handshake got HTTP {g.status_code}: {g.text[:120]!r}. Wrong URL, or the tunnel points elsewhere")
        return
    payload = {"object": "whatsapp_business_account", "entry": [{"id": "CHECK", "changes": [{"field": "messages",
               "value": {"messaging_product": "whatsapp", "statuses": [{
                   "id": f"wamid.CHECK{uuid.uuid4().hex}", "status": "read", "timestamp": str(int(time.time()))}]}}]}]}
    raw = json.dumps(payload).encode()
    sig = "sha256=" + hmac.new(app_secret.encode(), raw, hashlib.sha256).hexdigest()
    try:
        p = requests.post(url, data=raw, headers={"Content-Type": "application/json", "X-Hub-Signature-256": sig},
                          timeout=10)
    except requests.RequestException as e:
        r.fail(f"signed POST failed: {e}")
        return
    if p.status_code == 200:
        r.ok("signed POST accepted and written to the DB: inbound messages will reach the app")
    elif p.status_code == 403:
        r.fail("signed POST refused: webhook.py has a different WHATSAPP_APP_SECRET (App settings > Basic)")
    else:
        r.fail(f"signed POST got HTTP {p.status_code}: {p.text[:120]!r}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--send", metavar="TEXT", help="send this text to WHATSAPP_DEMO_TO")
    g.add_argument("--template", action="store_true", help="send the opener template to WHATSAPP_DEMO_TO")
    ap.add_argument("--webhook", metavar="URL", help="public URL of webhook.py (the tunnel)")
    args = ap.parse_args(argv)

    r = Report()
    vals = check_config(r)
    client = whatsapp.get_client()
    if client is None:
        r.fail("sending is in mock mode: WHATSAPP_TOKEN, WHATSAPP_PHONE_NUMBER_ID and WHATSAPP_DEMO_TO are all needed")
    elif check_meta(r, client):
        check_window(r, client)
        if args.send or args.template:
            send(r, client, args.send, args.template)
    if args.webhook:
        if vals["WHATSAPP_VERIFY_TOKEN"] and vals["WHATSAPP_APP_SECRET"]:
            check_webhook(r, args.webhook, vals["WHATSAPP_VERIFY_TOKEN"], vals["WHATSAPP_APP_SECRET"])
        else:
            r.fail("--webhook needs WHATSAPP_VERIFY_TOKEN and WHATSAPP_APP_SECRET")
    print("All checks passed." if not r.failed else f"{r.failed} check(s) failed.")
    return 1 if r.failed else 0


if __name__ == "__main__":
    sys.exit(main())
