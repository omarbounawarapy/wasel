"""WhatsApp webhook receiver. Run: python webhook.py   (then expose it: cloudflared tunnel --url http://localhost:8000)

Meta has no endpoint to poll for inbound messages; it POSTs them here. This process verifies each delivery
and writes messages and delivery statuses to the same SQLite file as the Streamlit app, which polls it.

    GET  /webhook   Meta's verification handshake (hub.verify_token must equal WHATSAPP_VERIFY_TOKEN)
    POST /webhook   Messages and statuses, rejected unless X-Hub-Signature-256 matches WHATSAPP_APP_SECRET
    GET  /healthz   Liveness
"""
import json
import logging
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pipeline import config, db, whatsapp  # noqa: E402

MAX_BODY = 1_000_000
log = logging.getLogger("webhook")


class Handler(BaseHTTPRequestHandler):
    server_version = "cod-risk-webhook"
    conn = None          # set by make_server
    lock = threading.Lock()  # one shared connection, one writer at a time
    verify_token = ""
    app_secret = ""

    def _reply(self, code: int, body: str = "", ctype: str = "text/plain") -> None:
        data = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/healthz":
            return self._reply(200, "ok")
        if url.path != "/webhook":
            return self._reply(404, "not found")
        q = {k: v[0] for k, v in parse_qs(url.query).items()}
        if q.get("hub.mode") == "subscribe" and self.verify_token and q.get("hub.verify_token") == self.verify_token:
            log.info("webhook verified by Meta")
            return self._reply(200, q.get("hub.challenge", ""))
        return self._reply(403, "verification failed")

    def do_POST(self):
        if urlparse(self.path).path != "/webhook":
            return self._reply(404, "not found")
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > MAX_BODY:
            return self._reply(413 if length > MAX_BODY else 400, "bad length")
        raw = self.rfile.read(length)
        if not whatsapp.verify_signature(raw, self.headers.get("X-Hub-Signature-256"), self.app_secret):
            log.warning("rejected POST with a bad or missing signature")
            return self._reply(403, "bad signature")
        try:
            payload = json.loads(raw)
        except ValueError:
            return self._reply(400, "bad json")
        try:
            with self.lock:
                result = whatsapp.handle_webhook(self.conn, payload)
        except Exception:  # 500 makes Meta retry; the unique wamid makes the retry a no-op
            log.exception("failed to store webhook")
            return self._reply(500, "error")
        log.info("stored %s", result)
        return self._reply(200, json.dumps(result), "application/json")

    def log_message(self, fmt, *args):  # route http.server's access log through logging
        log.debug(fmt, *args)


def make_server(host: str, port: int, conn, verify_token: str, app_secret: str) -> ThreadingHTTPServer:
    handler = type("BoundHandler", (Handler,), {"conn": conn, "verify_token": verify_token,
                                                "app_secret": app_secret})
    return ThreadingHTTPServer((host, port), handler)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    verify_token, app_secret = config.secret("WHATSAPP_VERIFY_TOKEN"), config.secret("WHATSAPP_APP_SECRET")
    missing = [k for k, v in (("WHATSAPP_VERIFY_TOKEN", verify_token), ("WHATSAPP_APP_SECRET", app_secret)) if not v]
    if missing:
        sys.exit(f"Set {', '.join(missing)} first (see .env.example).")
    db.ensure_db(config.ROOT / "seed.db")
    conn = db.connect()
    port = int(os.environ.get("PORT", 8000))
    server = make_server("0.0.0.0", port, conn, verify_token, app_secret)
    log.info("listening on :%d  (callback URL: https://<your tunnel>/webhook, db: %s)", port, config.DB_PATH)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
