"""WhatsApp webhook and send path. Offline: hand-built Meta-shaped
payloads under tests/fixtures/whatsapp/ (fake numbers 21600000001–09 only), signed with a fake test secret."""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
from pathlib import Path

import pytest

from tests.integration.conftest import hero_id, make_client, settle
from wasel.db import repo
from wasel.ingress.whatsapp import parse_payload, verify_signature

FX = Path(__file__).resolve().parents[1] / "fixtures" / "whatsapp"
GOLDEN = json.loads((Path(__file__).resolve().parents[1] / "golden" / "hero.json").read_text(encoding="utf-8"))
SECRET = "test-app-secret-not-real-0001"
VERIFY = "test-verify-token-not-real-000001"
PNID = "100000000000001"
WA = dict(webhook_enabled=True, wa_app_secret=SECRET, wa_verify_token=VERIFY, wa_phone_number_id=PNID)
URL = "/webhook/whatsapp"


def raw(name: str) -> bytes:
    return (FX / f"{name}.json").read_bytes()


def sign(body: bytes, secret: str = SECRET) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def wa_post(client, name: str | None = None, *, body: bytes | None = None, secret: str = SECRET, tamper=False,
            header=True, reserialize=False):
    body = raw(name) if body is None else body
    sig = sign(body, secret)
    if tamper:
        body = body.replace(b"Sfax", b"Sfaz", 1)
    if reserialize:
        body = json.dumps(json.loads(body), separators=(",", ":"), ensure_ascii=False).encode()
    return client.post(URL, content=body, headers={"X-Hub-Signature-256": sig, "Content-Type": "application/json"}
                       if header else {"Content-Type": "application/json"})


@pytest.fixture
def wa(tmp_path):
    c, core, clock = make_client(tmp_path, "dev", **WA)
    with c:
        yield c, core, clock


def msg(conn, wamid):
    return conn.execute("SELECT * FROM messages WHERE channel_message_id=?", (wamid,)).fetchone()


def order_of(conn, wamid):
    return conn.execute("SELECT o.* FROM orders o JOIN order_messages om ON om.order_id=o.order_id JOIN messages m"
                        " ON m.message_id=om.message_id WHERE m.channel_message_id=?", (wamid,)).fetchone()


def n_messages(conn) -> int:
    return conn.execute("SELECT COUNT(*) FROM messages WHERE origin='whatsapp'").fetchone()[0]


# ---------------------------------------------------------------- verify GET
@pytest.mark.parametrize("params,ok", [
    ({"hub.mode": "subscribe", "hub.verify_token": VERIFY, "hub.challenge": "1158201444"}, True),
    ({"hub.mode": "subscribe", "hub.verify_token": VERIFY + "x", "hub.challenge": "1158201444"}, False),
    ({"hub.mode": "subscribe", "hub.verify_token": "", "hub.challenge": "1158201444"}, False),
    ({"hub.mode": "unsubscribe", "hub.verify_token": VERIFY, "hub.challenge": "1158201444"}, False),
    ({"hub.mode": "subscribe", "hub.verify_token": VERIFY, "hub.challenge": "9" * 129}, False),
])
def test_webhook_verify_get(wa, params, ok):
    c, _, _ = wa
    r = c.get(URL, params=params)
    if ok:
        assert r.status_code == 200 and r.headers["content-type"].startswith("text/plain")
        assert r.text == params["hub.challenge"]
    else:
        assert r.status_code == 403 and r.content == b""


def test_verify_get_fixture_query_string(wa):
    c, _, _ = wa
    qs = (FX / "verify_get.txt").read_text().strip().replace("{VERIFY_TOKEN}", VERIFY)
    assert c.get(f"{URL}?{qs}").text == "1158201444"


# ---------------------------------------------------------------- signature
@pytest.mark.parametrize("kw,reason", [
    ({"secret": "wrong-secret-0000000000"}, "mismatch"),
    ({"tamper": True}, "mismatch"),
    ({"reserialize": True}, "mismatch"),
    ({"header": False}, "missing"),
])
def test_webhook_signature_rejected(wa, kw, reason):
    c, core, _ = wa
    r = wa_post(c, "text_inbound", **kw)
    assert r.status_code == 401 and r.json()["error"]["code"] == "UNAUTHORIZED"
    conn = core.conn()
    assert n_messages(conn) == 0
    ev = conn.execute("SELECT * FROM events WHERE type='webhook.rejected'").fetchall()
    assert len(ev) == 1 and json.loads(ev[0]["payload"]) == {"reason": reason}


def test_webhook_signature_malformed_header(wa):
    c, core, _ = wa
    r = c.post(URL, content=raw("text_inbound"), headers={"X-Hub-Signature-256": "sha256=ABC"})
    assert r.status_code == 401 and n_messages(core.conn()) == 0


def test_webhook_signature_valid(wa):
    c, core, _ = wa
    r = wa_post(c, "text_inbound")
    assert r.status_code == 200 and r.json() == {}
    conn = core.conn()
    assert n_messages(conn) == 1
    m = msg(conn, "wamid.TEST1")
    assert m["text"] == "nheb sac cuir, Sfax" and m["origin"] == "whatsapp" and m["raw_payload"] is None
    conv = conn.execute("SELECT * FROM conversations WHERE conversation_id=?", (m["conversation_id"],)).fetchone()
    assert conv["channel"] == "whatsapp" and conv["sandbox_id"] is None
    assert c.get("/api/health").json()["whatsapp"]["last_webhook_at"] is not None


def test_verify_signature_pure():
    body = raw("text_inbound")
    assert verify_signature(SECRET, body, sign(body)) is None
    assert verify_signature("", body, sign(body, "")) == "no_secret"           # empty secret never verifies
    assert verify_signature(SECRET, body, sign(body).upper()) == "malformed"
    assert verify_signature(SECRET, body, None) == "missing"


# ---------------------------------------------------------------- size limit, always 200 after a valid signature
def test_webhook_body_limits(wa):
    c, core, _ = wa
    big = json.dumps({"object": "whatsapp_business_account", "pad": "x" * (1024 * 1024)}).encode()
    r = c.post(URL, content=big, headers={"X-Hub-Signature-256": sign(big)})
    assert r.status_code == 413
    mid = json.dumps({"object": "whatsapp_business_account", "entry": [], "pad": "x" * 200_000}).encode()
    assert c.post(URL, content=mid, headers={"X-Hub-Signature-256": sign(mid)}).status_code == 200   # > 64 KB is fine


def test_webhook_malformed_and_foreign_payloads_still_200(wa):
    c, core, _ = wa
    assert wa_post(c, body=b"{not json").status_code == 200
    foreign = raw("text_inbound").replace(PNID.encode(), b"100000000000999")
    assert wa_post(c, body=foreign).status_code == 200
    odd = json.dumps({"object": "whatsapp_business_account", "entry": [{"changes": [{"value": {"metadata": "x"}}]}]})
    assert wa_post(c, body=odd.encode()).status_code == 200
    conn = core.conn()
    assert n_messages(conn) == 0
    assert conn.execute("SELECT COUNT(*) FROM events WHERE type='webhook.malformed'").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM events WHERE type='webhook.process_error'").fetchone()[0] == 1


# ---------------------------------------------------------------- duplicate wamid
def test_webhook_duplicate_wamid(wa):
    c, core, clock = wa
    conn = core.conn()
    wa_post(c, "text_inbound")
    due = order_of(conn, "wamid.TEST1")["pending_rescore_at"]
    clock.advance(1)
    wa_post(c, "text_inbound")                                      # Meta retry: same payload
    assert n_messages(conn) == 1 and order_of(conn, "wamid.TEST1")["pending_rescore_at"] == due
    assert settle(core, clock) == 1
    oid = order_of(conn, "wamid.TEST1")["order_id"]
    assert len(repo.assessments(conn, oid)) == 1
    wa_post(c, "text_inbound_duplicate")                            # TEST1 again + TEST2 new
    assert n_messages(conn) == 2 and order_of(conn, "wamid.TEST2")["order_id"] == oid


# ---------------------------------------------------------------- status receipts
def test_webhook_status_receipt(wa):
    c, core, clock = wa
    conn = core.conn()
    wa_post(c, "text_inbound")
    settle(core, clock)
    o = order_of(conn, "wamid.TEST1")
    mid = repo.insert_message(conn, core.ids, clock.now(), conversation_id=o["conversation_id"], direction="outbound",
                              author="seller", origin="whatsapp", text="ok", channel_message_id="wamid.OUT1",
                              delivery_status="sent")               # stand-in for an send
    before = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    for name, expect in (("status_delivered", "delivered"), ("status_read", "read"), ("status_delivered", "read")):
        assert wa_post(c, name).status_code == 200
        assert conn.execute("SELECT delivery_status FROM messages WHERE message_id=?", (mid,)).fetchone()[0] == expect
    assert wa_post(c, "status_unknown_wamid").status_code == 200
    assert conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0] == before
    assert repo.get_order(conn, o["order_id"])["pending_rescore_at"] is None


# ---------------------------------------------------------------- out-of-order batch
def test_webhook_out_of_order_batch(wa):
    c, core, _ = wa
    body = json.loads(raw("batch_out_of_order"))
    assert [m.wamid for m in parse_payload(body, PNID).messages] == ["wamid.OOO1", "wamid.OOO2"]
    wa_post(c, "batch_out_of_order")
    conn = core.conn()
    o = order_of(conn, "wamid.OOO1")
    assert [m["text"] for m in repo.order_messages(conn, o["order_id"])] == ["nheb mixeur", "fi Sousse, 9rib el mahatta"]
    assert msg(conn, "wamid.OOO1")["message_id"] < msg(conn, "wamid.OOO2")["message_id"]      # stored in ts order


# ---------------------------------------------------------------- message type mapping
@pytest.mark.parametrize("name,wamid,kind", [
    ("location", "wamid.LOC1", "location"), ("audio", "wamid.AUD1", "unsupported"),
    ("image", "wamid.IMG1", "unsupported"), ("sticker", "wamid.STK1", "unsupported"),
])
def test_webhook_type_mapping(wa, name, wamid, kind):
    c, core, clock = wa
    wa_post(c, "text_inbound")                                      # media follows a text order from the same sender
    wa_post(c, name)
    conn = core.conn()
    m = msg(conn, wamid)
    assert m["kind"] == kind and m["text"] is None
    settle(core, clock)
    o = repo.get_order(conn, order_of(conn, wamid)["order_id"])
    if kind == "location":
        assert (m["location_lat"], m["location_lng"]) == (36.8065, 10.1815)
        assert json.loads(repo.current_assessment(conn, o["order_id"])["context_json"])["has_geo_pin"] is True
    else:
        assert o["status"] == "needs_review"


def test_webhook_text_and_reply_context(wa):
    c, core, _ = wa
    wa_post(c, "text_inbound")
    wa_post(c, "reply_with_context")
    conn = core.conn()
    quoted, reply = msg(conn, "wamid.TEST1"), msg(conn, "wamid.CTX2")
    assert reply["kind"] == "text" and reply["text"] == "ey, dar 12"
    assert reply["reply_to_message_id"] == quoted["message_id"]
    d = c.get(f"/api/orders/{order_of(conn, 'wamid.CTX2')['order_id']}").json()
    views = {m["message_id"]: m for m in d["conversation"]["messages"]}
    assert views[reply["message_id"]]["reply_to"]["message_id"] == quoted["message_id"]


# ---------------------------------------------------------------- phone number stays in customers.phone_e164
def test_sender_phone_never_leaves_the_db(wa, caplog):
    c, core, clock = wa
    caplog.set_level(logging.DEBUG)
    wa_post(c, "text_inbound")
    wa_post(c, "location")
    settle(core, clock)
    conn = core.conn()
    assert {r[0] for r in conn.execute("SELECT phone_e164 FROM customers WHERE phone_e164 IS NOT NULL")} == \
        {"+21600000001"}
    out = c.get("/api/orders").text + c.get("/api/events?limit=500").text
    for o in c.get("/api/orders").json()["orders"]:
        out += c.get(f"/api/orders/{o['order_id']}").text
    prompts = " ".join(r[0] or "" for r in conn.execute("SELECT output_json FROM extraction_runs"))
    for blob in (out, caplog.text, prompts):
        assert "21600000001" not in blob
    assert SECRET not in caplog.text and VERIFY not in caplog.text


def test_access_log_never_carries_the_verify_token(wa):
    from wasel.api.routes_webhook import RedactVerifyToken
    assert any(isinstance(f, RedactVerifyToken) for f in logging.getLogger("uvicorn.access").filters)
    rec = logging.LogRecord("uvicorn.access", logging.INFO, "", 0, '%s - "%s %s HTTP/%s" %d',
                            ("1.2.3.4:5", "GET", f"{URL}?hub.mode=subscribe&hub.verify_token={VERIFY}&hub.challenge=1",
                             "1.1", 200), None)
    RedactVerifyToken().filter(rec)
    assert VERIFY not in rec.getMessage() and f"{URL}?<redacted>" in rec.getMessage()


# ---------------------------------------------------------------- fails closed
@pytest.mark.parametrize("mode,over", [
    ("public", WA),                                                  # every WA var set, still never mounted
    ("dev", {**WA, "wa_app_secret": ""}),
    ("event", {**WA, "wa_app_secret": "x" * 15}),
    ("event", {**WA, "wa_verify_token": "y" * 23}),
    ("event", {**WA, "webhook_enabled": False}),
])
def test_webhook_fails_closed(tmp_path, mode, over):
    c, _, _ = make_client(tmp_path, mode, **over)
    with c:
        assert c.get("/api/health").json()["webhook"] == "disabled"
        assert c.get(URL, params={"hub.mode": "subscribe", "hub.verify_token": VERIFY,
                                  "hub.challenge": "1"}).status_code == 404
        body = raw("text_inbound")
        assert c.post(URL, content=body, headers={"X-Hub-Signature-256": sign(body)}).status_code in (404, 405)


def test_webhook_mounted_in_event_mode(tmp_path):
    c, _, _ = make_client(tmp_path, "event", **WA)
    with c:
        h = c.get("/api/health").json()
        assert (h["mode"], h["webhook"], h["wa_send"]) == ("event", "enabled", False)


# ---------------------------------------------------------------- hero parity: webhook path == paste/seed path
def test_hero_loop_webhook_parity(wa):
    c, core, clock = wa
    conn = core.conn()
    # reference: the seeded hero (same store_inbound path) + simulate-reply, as in test_hero_loop_in_dev
    hid = hero_id(c)["order_id"]
    conv = c.get(f"/api/orders/{hid}").json()["order"]["conversation_id"]
    v2_text = json.loads(raw("hero_v2_reply"))["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"]
    c.post(f"/api/conversations/{conv}/simulate-reply", json={"kind": "text", "text": v2_text})
    settle(core, clock)
    ref = c.get(f"/api/orders/{hid}").json()["assessments"]
    # the same conversation as signed webhook payloads
    assert wa_post(c, "hero_v1_inbound").status_code == 200
    settle(core, clock)
    oid = order_of(conn, "wamid.HERO0")["order_id"]
    draft = repo.unsent_draft(conn, oid)
    assert draft["template_id"] == "T_ADDRESS"
    repo.mark_draft_sent(conn, core.ids, clock.now(), draft, origin="dashboard", delivery="recorded_only",
                         decided_by="human")                          # stand-in for the send
    clock.advance(30)
    assert wa_post(c, "hero_v2_reply").status_code == 200
    settle(core, clock)
    got = c.get(f"/api/orders/{oid}").json()
    v1, v2 = got["assessments"]
    key = ("tier", "final_score", "model_score", "action")
    assert [tuple(a[k] for k in key) for a in (v1, v2)] == [tuple(a[k] for k in key) for a in ref]
    assert (v1["final_score"], v2["final_score"]) == (GOLDEN["v1"]["final"], GOLDEN["v2a"]["final"])
    assert (v1["tier"], v2["tier"]) == ("high", "low") and v2["reason_diff"] and "dar 14" in v2["reason_diff"]
    assert got["order"]["status"] == "ready_to_ship"


# ---------------------------------------------------------------- send (offline: httpx MockTransport as Meta)
def _sender(calls, status=200):
    import httpx

    from wasel.outbound.whatsapp_send import WhatsAppSender

    def handler(request):
        calls.append(json.loads(request.content))
        if status != 200:
            return httpx.Response(status, json={"error": {"code": 131047}})
        return httpx.Response(200, json={"messages": [{"id": "wamid.OUT1"}]})
    return WhatsAppSender("test-token", PNID, "v21.0", transport=httpx.MockTransport(handler))


@pytest.fixture
def wa_send(tmp_path):
    c, core, clock = make_client(tmp_path, "dev", wa_send_enabled=True, wa_token="test-token", **WA)
    with c:
        yield c, core, clock


def _draft_for(c, core, clock):
    wa_post(c, "text_inbound")
    settle(core, clock)
    conn = core.conn()
    o = order_of(conn, "wamid.TEST1")
    if repo.unsent_draft(conn, o["order_id"]) is None:
        c.post(f"/api/orders/{o['order_id']}/actions", json={"action": "request_confirmation"})
    return conn, o, repo.unsent_draft(conn, o["order_id"])


def test_send_draft_goes_out_on_whatsapp_and_tracks_delivery(wa_send):
    c, core, clock = wa_send
    calls: list = []
    core.sender = _sender(calls)
    conn, o, d = _draft_for(c, core, clock)
    r = c.post(f"/api/drafts/{d['draft_id']}/send")
    assert r.status_code == 200 and r.json()["delivery"] == "whatsapp_sent"
    assert calls == [{"messaging_product": "whatsapp", "recipient_type": "individual", "to": "21600000001",
                      "type": "text", "text": {"preview_url": False, "body": d["rendered_text"]}}]
    m = msg(conn, "wamid.OUT1")
    assert m["direction"] == "outbound" and m["delivery_status"] == "sent"
    wa_post(c, "status_delivered")                                  # Meta's status webhook closes the loop
    assert msg(conn, "wamid.OUT1")["delivery_status"] == "delivered"
    assert c.post(f"/api/drafts/{d['draft_id']}/send").status_code == 409


def test_send_failure_is_502_and_draft_stays_unsent(wa_send):
    c, core, clock = wa_send
    core.sender = _sender([], status=400)
    conn, o, d = _draft_for(c, core, clock)
    r = c.post(f"/api/drafts/{d['draft_id']}/send")
    assert r.status_code == 502 and r.json()["error"]["code"] == "WHATSAPP_SEND_FAILED"
    assert repo.unsent_draft(conn, o["order_id"])["draft_id"] == d["draft_id"]


def test_send_retries_transient_5xx_then_succeeds(wa_send):
    import httpx

    from wasel.outbound.whatsapp_send import WhatsAppSender

    c, core, clock = wa_send
    calls: list = []

    def handler(request):
        calls.append(json.loads(request.content))
        if len(calls) < 3:
            return httpx.Response(503, json={"error": {"code": 131030}})
        return httpx.Response(200, json={"messages": [{"id": "wamid.OUT1"}]})

    core.sender = WhatsAppSender("test-token", PNID, "v21.0", transport=httpx.MockTransport(handler),
                                 backoff_s=0.0)
    conn, o, d = _draft_for(c, core, clock)
    r = c.post(f"/api/drafts/{d['draft_id']}/send")
    assert r.status_code == 200 and r.json()["delivery"] == "whatsapp_sent" and len(calls) == 3


def test_send_does_not_retry_permanent_4xx(wa_send):
    c, core, clock = wa_send
    calls: list = []
    core.sender = _sender(calls, status=400)
    conn, o, d = _draft_for(c, core, clock)
    r = c.post(f"/api/drafts/{d['draft_id']}/send")
    assert r.status_code == 502 and len(calls) == 1


def test_send_gives_up_after_max_retries(wa_send):
    c, core, clock = wa_send
    calls: list = []
    core.sender = _sender(calls, status=503)                       # every attempt fails, retryable
    conn, o, d = _draft_for(c, core, clock)
    r = c.post(f"/api/drafts/{d['draft_id']}/send")
    assert r.status_code == 502 and r.json()["error"]["code"] == "WHATSAPP_SEND_FAILED" and len(calls) == 3
    assert repo.unsent_draft(conn, o["order_id"])["draft_id"] == d["draft_id"]


def test_send_refused_outside_24h_window(wa_send):
    c, core, clock = wa_send
    calls: list = []
    core.sender = _sender(calls)
    conn, o, d = _draft_for(c, core, clock)
    clock.advance(25 * 3600)
    r = c.post(f"/api/drafts/{d['draft_id']}/send")
    assert r.status_code == 409 and r.json()["error"]["code"] == "OUTSIDE_24H_WINDOW" and calls == []


def test_auto_send_only_sends_auto_send_drafts(wa_send):
    from wasel.api.commands import auto_send_due
    c, core, clock = wa_send
    calls: list = []
    core.sender = _sender(calls)
    conn, o, d = _draft_for(c, core, clock)
    s = core.settings.model_copy(update={"wa_auto_send": True})
    assert d["route"] != "auto_send" and auto_send_due(conn, core.ids, clock.now(), s, core.sender) == []
    conn.execute("UPDATE outbound_drafts SET route='auto_send' WHERE draft_id=?", (d["draft_id"],))
    assert auto_send_due(conn, core.ids, clock.now(), s, core.sender) == [d["draft_id"]] and len(calls) == 1
    row = conn.execute("SELECT decided_by, delivery FROM outbound_drafts WHERE draft_id=?", (d["draft_id"],)).fetchone()
    assert tuple(row) == ("system", "whatsapp_sent")


def test_auto_send_records_the_send_on_a_simulated_conversation(wa_send):
    """No WhatsApp channel and no sender: a system send is recorded as simulated, so the threshold loop
    (draft cleared -> sent without a click) is visible in the demo."""
    from wasel.api.commands import auto_send_due
    c, core, clock = wa_send
    hid = hero_id(c)["order_id"]
    conn = core.conn()
    if repo.unsent_draft(conn, hid) is None:
        c.post(f"/api/orders/{hid}/actions", json={"action": "request_confirmation"})
        settle(core, clock)
    d = repo.unsent_draft(conn, hid)
    assert d is not None and d["route"] != "auto_send"
    s = core.settings.model_copy(update={"wa_auto_send": True})
    assert auto_send_due(conn, core.ids, clock.now(), s, None) == []
    conn.execute("UPDATE outbound_drafts SET route='auto_send' WHERE draft_id=?", (d["draft_id"],))
    assert auto_send_due(conn, core.ids, clock.now(), s, None) == [d["draft_id"]]
    row = conn.execute("SELECT decided_by, delivery FROM outbound_drafts WHERE draft_id=?", (d["draft_id"],)).fetchone()
    assert tuple(row) == ("system", "recorded_only")


def test_auto_send_never_runs_in_public_mode(tmp_path):
    from wasel.api.commands import auto_send_due
    c, core, clock = make_client(tmp_path, "public", wa_send_enabled=True, wa_token="test-token",
                                 wa_auto_send=True, **WA)
    with c:
        assert auto_send_due(core.conn(), core.ids, clock.now(), core.settings, None) == []


def test_public_mode_never_builds_a_sender(tmp_path):
    c, core, _ = make_client(tmp_path, "public", wa_send_enabled=True, wa_token="test-token", wa_auto_send=True, **WA)
    with c:
        assert core.sender is None
