"""WhatsApp Cloud API: sending, the webhook receiver, and mapping customer replies to orders. No network."""
import hashlib
import hmac
import json
import shutil
import sqlite3
import threading
import urllib.error
import urllib.request

import pytest

from pipeline import config, db, whatsapp
from pipeline.whatsapp import WhatsAppClient, WhatsAppError
import webhook

SECRET = "app-secret"
DEMO = "21620123456"


class FakeResponse:
    def __init__(self, status, data):
        self.status_code, self._data = status, data

    def json(self):
        return self._data


class FakeWA(WhatsAppClient):
    """Real client, fake transport: records payloads, returns scripted responses."""

    def __init__(self, fail: WhatsAppError | None = None):
        super().__init__("token", "PNID", "+216 20 123 456")
        self.payloads, self.fail, self.n = [], fail, 0

    def _post(self, payload):
        self.payloads.append(payload)
        if self.fail:
            raise self.fail
        self.n += 1
        return f"wamid.OUT{self.n}"


def text_payload(body, wamid="wamid.IN1", sender=DEMO, context=None):
    msg = {"from": sender, "id": wamid, "timestamp": "1790000000", "type": "text", "text": {"body": body}}
    if context:
        msg["context"] = {"from": "15550000000", "id": context}
    return {"object": "whatsapp_business_account", "entry": [{"id": "WABA", "changes": [{"field": "messages", "value": {
        "messaging_product": "whatsapp", "contacts": [{"profile": {"name": "Amira"}, "wa_id": sender}],
        "messages": [msg]}}]}]}


def wrap(value):
    return {"object": "whatsapp_business_account",
            "entry": [{"id": "WABA", "changes": [{"field": "messages", "value": value}]}]}


@pytest.fixture
def seeded(conn, order):
    db.upsert_order(conn, order)
    db.upsert_order(conn, dict(order, order_id="T-2"))
    conn.commit()
    return conn


# --- client -------------------------------------------------------------------------------------

def test_client_payloads(monkeypatch):
    sent = []

    def fake_post(url, headers, json, timeout):
        sent.append((url, headers, json))
        return FakeResponse(200, {"messages": [{"id": "wamid.X"}]})

    monkeypatch.setattr(whatsapp.requests, "post", fake_post)
    c = WhatsAppClient("tok", "123", "+216 20 123 456", api_version="v25.0")
    assert c.send_buttons(c.demo_to, "hi", [("confirm:T-1", "Oui")], reply_to="wamid.Q") == "wamid.X"
    url, headers, body = sent[0]
    assert url == "https://graph.facebook.com/v25.0/123/messages"
    assert headers["Authorization"] == "Bearer tok"
    assert body["to"] == DEMO and body["context"] == {"message_id": "wamid.Q"}
    assert body["interactive"]["action"]["buttons"][0] == {"type": "reply", "reply": {"id": "confirm:T-1", "title": "Oui"}}
    c.send_location_request(DEMO, "where?")
    assert sent[1][2]["interactive"] == {"type": "location_request_message", "body": {"text": "where?"},
                                         "action": {"name": "send_location"}}
    c.send_template(DEMO, "hello_world", "en_US")
    assert sent[2][2]["template"] == {"name": "hello_world", "language": {"code": "en_US"}}


def test_client_error_is_explained(monkeypatch):
    err = {"error": {"message": "(#131030) Recipient phone number not in allowed list", "code": 131030,
                     "error_data": {"details": "Recipient phone number not in allowed list"}}}
    monkeypatch.setattr(whatsapp.requests, "post", lambda *a, **k: FakeResponse(400, err))
    with pytest.raises(WhatsAppError) as e:
        WhatsAppClient("tok", "123", DEMO).send_text(DEMO, "hi")
    assert e.value.code == 131030 and "allowed list" in str(e.value) and "API Setup" in str(e.value)


def test_get_client_needs_token_number_id_and_demo_number(monkeypatch):
    for k in ("WHATSAPP_TOKEN", "WHATSAPP_PHONE_NUMBER_ID", "WHATSAPP_DEMO_TO"):
        monkeypatch.delenv(k, raising=False)
    assert whatsapp.get_client() is None
    monkeypatch.setenv("WHATSAPP_TOKEN", "t")
    monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", "1")
    assert whatsapp.get_client() is None
    monkeypatch.setenv("WHATSAPP_DEMO_TO", "+216 20-123-456")
    assert whatsapp.get_client().demo_to == DEMO


@pytest.mark.parametrize("register", ["derja_latin", "fr", "ar"])
def test_reply_interfaces_fit_whatsapp_limits(register):
    for bid, title in whatsapp.buttons_for("ORD-0299", register):
        assert len(title) <= 20 and len(bid) <= 256
    assert len(whatsapp.LOCATION_REQUEST[register]) <= 1024


# --- parsing ------------------------------------------------------------------------------------

@pytest.mark.parametrize("text,intent", [
    ("EYH", "confirm"), ("oui !", "confirm"), ("إيه", "confirm"), ("ok 👍", "confirm"),
    ("LE", "cancel"), ("non.", "cancel"), ("لا", "cancel"),
    ("le livreur peut passer demain ?", "text"), ("eyh ama ba3d 17h", "text"),
])
def test_text_intent(text, intent):
    assert whatsapp.text_intent(text) == intent


def test_parse_button_location_and_statuses():
    inbound, statuses = whatsapp.parse_webhook(wrap({
        "contacts": [{"profile": {"name": "Amira"}, "wa_id": DEMO}],
        "messages": [
            {"from": DEMO, "id": "wamid.B", "timestamp": "1790000000", "type": "interactive",
             "context": {"id": "wamid.OUT1"},
             "interactive": {"type": "button_reply", "button_reply": {"id": "cancel:T-2", "title": "Non, annuler"}}},
            {"from": DEMO, "id": "wamid.L", "timestamp": "1790000001", "type": "location",
             "location": {"latitude": 35.1676, "longitude": 8.8365, "name": "Pharmacie Ennour"}},
            {"from": DEMO, "id": "wamid.S", "timestamp": "1790000002", "type": "sticker", "sticker": {}},
        ],
        "statuses": [{"id": "wamid.OUT1", "status": "failed", "timestamp": "1790000003", "recipient_id": DEMO,
                      "errors": [{"code": 131047, "title": "Re-engagement message"}]}],
    }))
    b, loc, sticker = inbound
    assert (b["intent"], b["button_id"], b["context_id"], b["profile_name"]) == ("cancel", "cancel:T-2", "wamid.OUT1", "Amira")
    assert (loc["intent"], loc["latitude"], loc["text"]) == ("location", 35.1676, "Pharmacie Ennour")
    assert sticker["intent"] == "text" and sticker["text"] == "[sticker message]"
    assert statuses[0]["status"] == "failed" and "131047" in statuses[0]["error"]


def test_signature():
    raw = b'{"a":1}'
    good = "sha256=" + hmac.new(SECRET.encode(), raw, hashlib.sha256).hexdigest()
    assert whatsapp.verify_signature(raw, good, SECRET)
    assert not whatsapp.verify_signature(raw + b" ", good, SECRET)
    assert not whatsapp.verify_signature(raw, None, SECRET)
    assert not whatsapp.verify_signature(raw, good, "")  # no secret configured = reject, never accept


# --- sending and mapping ------------------------------------------------------------------------

def test_deliver_sends_once_and_maps_replies_back(seeded):
    wa = FakeWA()
    assert whatsapp.deliver(seeded, wa, "T-1", "confirm_sms", "Commande prête. OUI ?", "llm",
                            buttons=whatsapp.buttons_for("T-1", "fr")).ok
    assert whatsapp.deliver(seeded, wa, "T-1", "confirm_sms", "again", "llm").error == "already sent"
    assert len(wa.payloads) == 1 and wa.payloads[0]["to"] == DEMO
    msg = db.sent_messages(seeded, "T-1")[0]
    assert (msg["channel"], msg["provider_id"], msg["delivery"]) == ("whatsapp", "wamid.OUT1", "accepted")

    # A plain "oui" with no button and no quote maps to the last order messaged on that number.
    whatsapp.handle_webhook(seeded, text_payload("oui"))
    assert db.customer_status(seeded) == {"T-1": "confirm"}
    # A quoted reply maps through the quoted message's ID.
    whatsapp.deliver(seeded, wa, "T-2", "confirm_sms", "Commande T-2", "llm")
    whatsapp.handle_webhook(seeded, text_payload("c'est moi", wamid="wamid.IN2", context="wamid.OUT1"))
    assert db.inbound(seeded, "T-1")[-1]["text"] == "c'est moi"
    # Chatter after a confirmation doesn't erase it.
    assert db.customer_status(seeded)["T-1"] == "confirm"


def test_button_tap_names_its_order(seeded):
    wa = FakeWA()
    whatsapp.deliver(seeded, wa, "T-1", "confirm_sms", "a", "llm")
    whatsapp.deliver(seeded, wa, "T-2", "confirm_sms", "b", "llm")
    whatsapp.handle_webhook(seeded, wrap({"messages": [{"from": DEMO, "id": "wamid.B", "timestamp": "1", "type": "interactive",
                                                        "interactive": {"button_reply": {"id": "cancel:T-1", "title": "x"}}}]}))
    assert db.customer_status(seeded) == {"T-1": "cancel"}


def test_failed_send_frees_the_slot_for_a_retry(seeded):
    down = FakeWA(fail=WhatsAppError("token expired", 190))
    res = whatsapp.deliver(seeded, down, "T-1", "confirm_sms", "a", "llm")
    assert not res.ok and "token expired" in res.error
    assert db.sent_messages(seeded, "T-1") == [] and db.failed_messages(seeded, "T-1")[0]["error"] == "token expired"
    assert whatsapp.deliver(seeded, FakeWA(), "T-1", "confirm_sms", "a", "llm").ok


def test_replies_repeat_but_action_messages_do_not(seeded):
    wa = FakeWA()
    for _ in range(3):
        assert whatsapp.deliver(seeded, wa, "T-1", "reply", "Merci", "human").ok
    assert len(db.sent_messages(seeded, "T-1")) == 3


def test_daily_cap(seeded, monkeypatch):
    monkeypatch.setattr(config, "WA_SENDS_PER_DAY", 2)
    wa = FakeWA()
    assert whatsapp.deliver(seeded, wa, "T-1", "reply", "a", "human").ok
    assert whatsapp.deliver(seeded, wa, "T-1", "reply", "b", "human").ok
    assert "daily" in whatsapp.deliver(seeded, wa, "T-1", "reply", "c", "human").error
    assert len(wa.payloads) == 2


def test_mock_mode_sends_nothing(seeded):
    assert whatsapp.deliver(seeded, None, "T-1", "confirm_sms", "a", "static_template").ok
    assert db.sent_messages(seeded, "T-1")[0]["delivery"] == "mock"


def test_status_only_moves_forward(seeded):
    whatsapp.deliver(seeded, FakeWA(), "T-1", "confirm_sms", "a", "llm")
    for status in ("delivered", "sent", "read", "delivered"):  # out of order, as Meta may send them
        db.update_delivery(seeded, "wamid.OUT1", status)
    assert db.sent_messages(seeded, "T-1")[0]["delivery"] == "read"
    db.update_delivery(seeded, "wamid.OUT1", "failed", "gone")
    assert db.sent_messages(seeded, "T-1")[0]["delivery"] == "failed"
    assert not db.update_delivery(seeded, "wamid.UNKNOWN", "read")


def test_window(seeded):
    assert not whatsapp.window_open(seeded, DEMO)
    whatsapp.handle_webhook(seeded, text_payload("salam"))
    assert whatsapp.window_open(seeded, DEMO)
    seeded.execute("UPDATE wa_inbound SET received_at='2020-01-01T00:00:00+00:00'")
    assert not whatsapp.window_open(seeded, DEMO)


def test_old_seed_db_is_migrated(tmp_path):
    path = tmp_path / "old.db"
    shutil.copy(config.ROOT / "seed.db", path)
    conn = db.connect(path)
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(messages)")}
    assert {"channel", "to_wa", "provider_id", "delivery", "error"} <= cols
    assert db.send_message(conn, "ORD-0001", "confirm_sms", "a", "llm")
    assert not db.send_message(conn, "ORD-0001", "confirm_sms", "b", "llm")
    conn.close()


# --- webhook server -----------------------------------------------------------------------------

@pytest.fixture
def server(tmp_path, order):
    conn = db.connect(tmp_path / "hook.db")
    db.upsert_order(conn, order)
    conn.commit()
    srv = webhook.make_server("127.0.0.1", 0, conn, "verify-me", SECRET)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}", conn
    srv.shutdown()
    conn.close()


def http(url, body: bytes | None = None, sig: str | None = None):
    req = urllib.request.Request(url, data=body, method="POST" if body is not None else "GET")
    if sig:
        req.add_header("X-Hub-Signature-256", sig)
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def sign(raw: bytes) -> str:
    return "sha256=" + hmac.new(SECRET.encode(), raw, hashlib.sha256).hexdigest()


def test_webhook_verification_handshake(server):
    url, _ = server
    assert http(f"{url}/webhook?hub.mode=subscribe&hub.verify_token=verify-me&hub.challenge=1158201444") == (200, "1158201444")
    assert http(f"{url}/webhook?hub.mode=subscribe&hub.verify_token=wrong&hub.challenge=1")[0] == 403
    assert http(f"{url}/healthz") == (200, "ok")


def test_webhook_stores_signed_messages_once(server):
    url, conn = server
    whatsapp.deliver(conn, FakeWA(), "T-1", "confirm_sms", "a", "llm")
    raw = json.dumps(text_payload("eyh")).encode()
    assert http(f"{url}/webhook", raw, sign(raw))[0] == 200
    status, body = http(f"{url}/webhook", raw, sign(raw))  # Meta redelivery
    assert status == 200 and json.loads(body)["duplicates"] == 1
    assert [m["intent"] for m in db.inbound(conn, "T-1")] == ["confirm"]


def test_webhook_rejects_unsigned_and_forged(server):
    url, conn = server
    raw = json.dumps(text_payload("eyh")).encode()
    assert http(f"{url}/webhook", raw)[0] == 403
    assert http(f"{url}/webhook", raw, "sha256=" + "0" * 64)[0] == 403
    assert db.inbound(conn) == []


def test_webhook_db_error_returns_500_so_meta_retries(server, monkeypatch):
    url, _ = server
    def boom(*a):
        raise sqlite3.OperationalError("database is locked")
    monkeypatch.setattr(whatsapp, "handle_webhook", boom)
    raw = json.dumps(text_payload("eyh")).encode()
    assert http(f"{url}/webhook", raw, sign(raw))[0] == 500


# --- setup: .env loading and the pre-demo check ---------------------------------------------------

def test_dotenv_is_loaded_and_the_shell_wins(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text('# comment\nexport WA_T1="quoted"\nWA_T2=+216 20 123 456\nWA_T3=from-file\nWA_T4=\nnot a pair\n')
    monkeypatch.delenv("COD_NO_DOTENV")
    for k in ("WA_T1", "WA_T2", "WA_T4"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("WA_T3", "from-shell")
    config._load_dotenv(env)
    assert config.os.environ["WA_T1"] == "quoted" and config.os.environ["WA_T2"] == "+216 20 123 456"
    assert config.os.environ["WA_T3"] == "from-shell" and "WA_T4" not in config.os.environ


def test_phone_info_proves_token_without_sending(monkeypatch):
    got = []
    monkeypatch.setattr(whatsapp.requests, "get", lambda url, headers, timeout, params: got.append((url, params))
                        or FakeResponse(200, {"display_phone_number": "15550001111", "id": "123"}))
    monkeypatch.setattr(whatsapp.requests, "post", lambda *a, **k: pytest.fail("phone_info must not send"))
    assert WhatsAppClient("tok", "123", DEMO, api_version="v25.0").phone_info()["display_phone_number"] == "15550001111"
    assert got[0][0] == "https://graph.facebook.com/v25.0/123" and "display_phone_number" in got[0][1]["fields"]


def test_setup_check_end_to_end(server, tmp_path, monkeypatch, capsys):
    import scripts.whatsapp_check as check
    url, _ = server
    env = {"WHATSAPP_TOKEN": "tok", "WHATSAPP_PHONE_NUMBER_ID": "123", "WHATSAPP_DEMO_TO": "+216 20 123 456",
           "WHATSAPP_APP_SECRET": SECRET, "WHATSAPP_VERIFY_TOKEN": "verify-me"}
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "hook.db")  # the server fixture's DB
    real_get, real_post, sent = whatsapp.requests.get, whatsapp.requests.post, []

    def fake_get(url, **kw):  # Meta is faked; the webhook calls go to the real local server
        if "graph.facebook.com" not in url:
            return real_get(url, **kw)
        return FakeResponse(200, {"display_phone_number": "15550001111", "verified_name": "Test"})

    def fake_post(url, **kw):
        if "graph.facebook.com" not in url:
            return real_post(url, **kw)
        sent.append(kw["json"])
        return FakeResponse(200, {"messages": [{"id": "wamid.X"}]})

    monkeypatch.setattr(whatsapp.requests, "get", fake_get)
    monkeypatch.setattr(whatsapp.requests, "post", fake_post)
    assert check.main(["--send", "test", "--webhook", url]) == 0  # the webhook part goes through real HTTP
    out = capsys.readouterr().out
    assert "handshake passed" in out and "signed POST accepted" in out and "wamid.X" in out
    assert sent == [{"messaging_product": "whatsapp", "recipient_type": "individual", "to": DEMO, "type": "text",
                     "text": {"body": "test"}}]
    monkeypatch.setenv("WHATSAPP_APP_SECRET", "wrong")
    assert check.main(["--webhook", url]) == 1
    assert "different WHATSAPP_APP_SECRET" in capsys.readouterr().out
