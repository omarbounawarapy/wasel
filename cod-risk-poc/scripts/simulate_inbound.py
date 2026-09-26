"""Post a signed fake WhatsApp webhook to a running webhook.py, to rehearse the inbound flow without a phone.

    python scripts/simulate_inbound.py --text "eyh"
    python scripts/simulate_inbound.py --button confirm:ORD-0042
    python scripts/simulate_inbound.py --location 35.1676,8.8365
    python scripts/simulate_inbound.py --status read --wamid wamid.XXX

Signs with WHATSAPP_APP_SECRET and sends from WHATSAPP_DEMO_TO, the same way Meta would.
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

from pipeline import config  # noqa: E402
from pipeline.whatsapp import normalize  # noqa: E402


def payload(args, sender: str) -> dict:
    value = {"messaging_product": "whatsapp", "metadata": {"display_phone_number": "15550000000",
                                                          "phone_number_id": "SIMULATED"}}
    if args.status:
        value["statuses"] = [{"id": args.wamid, "status": args.status, "timestamp": str(int(time.time())),
                              "recipient_id": sender}]
    else:
        msg = {"from": sender, "id": f"wamid.SIM{uuid.uuid4().hex}", "timestamp": str(int(time.time()))}
        if args.button:
            msg |= {"type": "interactive", "interactive": {"type": "button_reply", "button_reply": {
                "id": args.button, "title": args.button.split(":")[0]}}}
        elif args.location:
            lat, lon = (float(x) for x in args.location.split(","))
            msg |= {"type": "location", "location": {"latitude": lat, "longitude": lon}}
        else:
            msg |= {"type": "text", "text": {"body": args.text}}
        value |= {"contacts": [{"profile": {"name": "Demo customer"}, "wa_id": sender}], "messages": [msg]}
    return {"object": "whatsapp_business_account",
            "entry": [{"id": "SIMULATED", "changes": [{"field": "messages", "value": value}]}]}


def main() -> None:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--text")
    g.add_argument("--button", help="button id, e.g. confirm:ORD-0042")
    g.add_argument("--location", help="lat,lon")
    g.add_argument("--status", choices=["sent", "delivered", "read", "failed"])
    ap.add_argument("--wamid", help="outbound message ID, with --status")
    ap.add_argument("--url", default="http://localhost:8000/webhook")
    args = ap.parse_args()
    if args.status and not args.wamid:
        ap.error("--status needs --wamid")
    secret, sender = config.secret("WHATSAPP_APP_SECRET"), normalize(config.secret("WHATSAPP_DEMO_TO"))
    if not secret or not sender:
        sys.exit("Set WHATSAPP_APP_SECRET and WHATSAPP_DEMO_TO first.")
    raw = json.dumps(payload(args, sender)).encode()
    sig = "sha256=" + hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    r = requests.post(args.url, data=raw, headers={"Content-Type": "application/json", "X-Hub-Signature-256": sig},
                      timeout=10)
    print(r.status_code, r.text)


if __name__ == "__main__":
    main()
