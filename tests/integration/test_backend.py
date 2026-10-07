"""C1 C2 C3 J7 J9 J10 J11 J12 J19 E3 E5 M1 P1–P7 + seed cache hits."""
from __future__ import annotations

import json
import sqlite3
from datetime import timedelta

import pytest

from tests.conftest import T0
from tests.integration.conftest import VID_A, VID_B, hero_id, make_client, settle
from wasel.api import models as M
from wasel.contracts import CustomerHistory, ScoreInput, StructuredFields
from wasel.db import repo
from wasel.db.conn import fresh_db, tx
from wasel.db.purge import purge_sandboxes
from wasel.ids import SeqIds
from wasel.scoring import stub
from wasel.state import ACTIONS, next_status

HERO_V2 = ("ey behi. Douar Ouled Ali, triq el jemaa, dar 14, el bab lazra9 9odem el pharmacie. "
           "ghodwa ba3d 17h nkoun fi dar")


# ---------------------------------------------------------------- seed + M1
def test_seed_all_cache_hits_under_fail_all(dev):
    """Every seeded order scores from the committed cache with every provider failing (zero tokens at boot)."""
    c, core, _ = dev
    rows = core.conn().execute("SELECT a.path FROM risk_assessments a").fetchall()
    assert rows and {r["path"] for r in rows} == {"cascade_cache"}
    assert core.conn().execute("SELECT COUNT(*) FROM llm_usage").fetchone()[0] == 0


def test_health_and_safe_defaults(tmp_path):
    c, core, _ = make_client(tmp_path, mode="garbage")       # unknown APP_MODE -> public
    with c:
        h = c.get("/api/health").json()
        assert h["mode"] == "public" and h["wa_send"] is False and h["webhook"] == "disabled"
        assert h["config"]["config_hash"] and h["llm"]["live_call_cap"] == 80
        assert c.post("/webhook/whatsapp", json={}).status_code in (404, 405)
        assert c.post("/api/webhook/whatsapp", json={}).status_code in (404, 405)
        assert h["llm"]["live_calls_today"] == 0


def test_public_forces_sends_off_even_with_token(tmp_path):
    c, core, _ = make_client(tmp_path, "public", wa_send_enabled=True, wa_token="t", webhook_enabled=True,
                             wa_app_secret="s" * 16, wa_verify_token="v" * 24)
    with c:
        h = c.get("/api/health").json()
        assert h["wa_send"] is False and h["webhook"] == "disabled" and h["wa_token_present"] is True
        assert core.settings.wa_send_effective is False and core.settings.webhook_mounted is False


def test_auto_send_state_is_visible_to_the_ui(tmp_path):
    """health.wa_auto_send is the effective flag (never in public mode); a draft says who sent it."""
    for mode, flag, expected in (("dev", False, False), ("dev", True, True), ("public", True, False)):
        c, _, _ = make_client(tmp_path / f"{mode}{flag}", mode, wa_auto_send=flag)
        with c:
            assert c.get("/api/health").json()["wa_auto_send"] is expected
    c, _, _ = make_client(tmp_path / "send")
    with c:
        d = c.get(f"/api/orders/{hero_id(c)['order_id']}").json()
        draft = next(x for x in d["drafts"] if not x["sent_message_id"])
        assert draft["decided_by"] is None
        assert c.post(f"/api/drafts/{draft['draft_id']}/send").status_code == 200
        d = c.get(f"/api/orders/{hero_id(c)['order_id']}").json()
        assert next(x for x in d["drafts"] if x["draft_id"] == draft["draft_id"])["decided_by"] == "human"


# ---------------------------------------------------------------- C3
def test_responses_validate_against_models(dev):
    c, core, _ = dev
    lst = c.get("/api/orders").json()
    M.OrderListResponse.model_validate(lst)
    assert lst["orders"][0]["score"]["final_score"] >= lst["orders"][-1]["score"]["final_score"]
    d = c.get(f"/api/orders/{hero_id(c)['order_id']}").json()
    M.OrderDetailResponse.model_validate(d)
    M.EventsResponse.model_validate(c.get("/api/events").json())
    M.HealthResponse.model_validate(c.get("/api/health").json())
    M.ImpactResponse.model_validate(c.get("/api/metrics/impact").json())


def test_no_response_model_exposes_phone_or_raw_payload():
    for name in dir(M):
        obj = getattr(M, name)
        if isinstance(obj, type) and issubclass(obj, M.BaseModel):
            assert not {"phone_e164", "raw_payload"} & set(obj.model_fields), name


# ---------------------------------------------------------------- segments (M2-lite)
def test_segments_join_and_highlight_exact_quotes(dev):
    c, _, _ = dev
    d = c.get(f"/api/orders/{hero_id(c)['order_id']}").json()
    for m in d["conversation"]["messages"]:
        if m["segments"] is not None:
            assert "".join(s["text"] for s in m["segments"]) == m["text"]
    risk = [s["text"] for m in d["conversation"]["messages"] for s in (m["segments"] or []) if s["kind"] == "risk"]
    assert {"9rib el jemaa", "ghali chwaya", "mouch dima fi dar"} <= set(risk)
    assert d["assessments"][-1]["tier"] == "high" and d["drafts"][0]["template_id"] == "T_ADDRESS"
    assert all(x["prefilter"]["passed"] and x["route"] != "blocked" for x in d["drafts"])   # static drafts never blocked


def test_script_tag_in_customer_text_stays_text(dev):
    from wasel.api.projections import build_segments
    t = "<script>alert(1)</script> 9rib el jemaa ‮evil"
    segs = build_segments(t, [{"start": 26, "end": 39, "kind": "red_flag", "code": "vague_location"}])
    assert "".join(s.text for s in segs) == t.replace("‮", "")
    assert [s.text for s in segs if s.kind == "risk"] == ["9rib el jemaa"]


# ---------------------------------------------------------------- hero loop through the API
def test_hero_loop_in_dev(dev):
    c, core, clock = dev
    hid = hero_id(c)["order_id"]
    d = c.get(f"/api/orders/{hid}").json()
    r = c.post(f"/api/conversations/{d['order']['conversation_id']}/simulate-reply", json={"kind": "text", "text": HERO_V2})
    assert r.status_code == 202 and r.json()["recorded_draft_id"]          # unsent draft auto-recorded first
    settle(core, clock)
    d = c.get(f"/api/orders/{hid}").json()
    v1, v2 = d["assessments"]
    assert (v1["tier"], v2["tier"]) == ("high", "low") and v2["delta"] < 0
    assert v2["path"] == "cascade_cache" and d["order"]["status"] == "ready_to_ship"
    assert "dar 14" in v2["reason_diff"] and v2["resolved_flags"] == []
    seller = [m for m in d["conversation"]["messages"] if m["author"] == "ai"]
    assert len(seller) == 1 and seller[0]["template_id"] == "T_ADDRESS" and seller[0]["segments"] is None


def test_public_judge_path_and_isolation(public):
    """E5 + P2 + P3 + P4: try hero -> HIGH, reply -> LOW; the seeded hero stays v1 HIGH; B can't see A's copy."""
    c, core, clock = public
    A, B = {"X-Visitor-Id": VID_A}, {"X-Visitor-Id": VID_B}
    seeded = hero_id(c, A)
    assert seeded["read_only"] is True
    r = c.post(f"/api/orders/{seeded['order_id']}/try", headers=A)
    assert r.status_code == 201
    mine = r.json()
    d = c.get(f"/api/orders/{mine['order_id']}", headers=A).json()
    assert d["assessments"][-1]["tier"] == "high" and d["assessments"][-1]["path"] == "cascade_cache"
    assert d["capabilities"]["can_simulate_reply"] and d["scripted_replies"] == [HERO_V2]
    assert core.conn().execute("SELECT COUNT(*) FROM llm_usage").fetchone()[0] == 0     # zero LLM calls
    c.post(f"/api/conversations/{mine['conversation_id']}/simulate-reply", headers=A,
           json={"kind": "text", "text": HERO_V2})
    settle(core, clock)
    assert c.get(f"/api/orders/{mine['order_id']}", headers=A).json()["assessments"][-1]["tier"] == "low"
    # the seeded hero is untouched for the next visitor
    s = c.get(f"/api/orders/{seeded['order_id']}", headers=B).json()
    assert len(s["assessments"]) == 1 and s["assessments"][0]["tier"] == "high"
    # isolation
    assert c.get(f"/api/orders/{mine['order_id']}", headers=B).status_code == 404
    assert mine["order_id"] not in [o["order_id"] for o in c.get("/api/orders", headers=B).json()["orders"]]
    # seeded rows are read-only
    r = c.post(f"/api/orders/{seeded['order_id']}/rescore", headers=A)
    assert r.status_code == 409 and r.json()["error"]["code"] == "SEEDED_READ_ONLY"
    r = c.post(f"/api/conversations/{seeded['conversation_id']}/simulate-reply", headers=A,
               json={"kind": "text", "text": "ey"})
    assert r.status_code == 409
    # writes need a visitor id
    assert c.post("/api/orders/ingest", json={"kind": "paste", "text": "nheb sac"}).status_code == 400
    # pseudonymised display name for visitor rows
    assert d["order"]["customer"]["display_name"].startswith("Customer #")


def test_purge_removes_old_sandbox_rows(public):
    c, core, clock = public
    A = {"X-Visitor-Id": VID_A}
    mine = c.post(f"/api/orders/{hero_id(c, A)['order_id']}/try", headers=A).json()
    seeded_before = core.conn().execute("SELECT COUNT(*) FROM orders WHERE sandbox_id IS NULL").fetchone()[0]
    assert purge_sandboxes(core.conn(), clock.now() + timedelta(hours=2, seconds=1)) == 1
    conn = core.conn()
    assert conn.execute("SELECT COUNT(*) FROM orders WHERE order_id=?", (mine["order_id"],)).fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM messages WHERE conversation_id=?", (mine["conversation_id"],)).fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM orders WHERE sandbox_id IS NULL").fetchone()[0] == seeded_before


# ---------------------------------------------------------------- paste + rules path (live key absent)
def test_paste_scores_on_rules_path_when_llm_down(dev):
    c, core, clock = dev
    r = c.post("/api/orders/ingest", json={"kind": "paste", "text": "nheb el casque bluetooth, rue de Marseille, Sfax"})
    assert r.status_code == 202
    oid = r.json()["created"][0]["order_id"]
    assert c.get(f"/api/orders/{oid}").json()["order"]["rescore_state"] == "debouncing"
    settle(core, clock)
    d = c.get(f"/api/orders/{oid}").json()
    a = d["assessments"][-1]
    assert a["path"] == "rules" and a["confidence"] == "low"
    assert a["action"] in ("ship", "confirm", "prepay")             # same tier mapping as the LLM path, not forced review
    assert d["order"]["status"] != "needs_review" and d["order"]["product_id"] == "P12"


def test_csv_ingest_limits_and_rejects(dev):
    c, _, _ = dev
    csv_text = ("customer_id,customer_name,product,price_tnd,zone,address,note\n"
                "C1,Ali,mixeur,129,rural,douar Sbiba,\nC2,Ines,,,moon,Sfax,\nC3,,,,,,\n")
    r = c.post("/api/orders/ingest", json={"kind": "csv", "csv_text": csv_text}).json()
    assert len(r["created"]) == 1 and [x["row"] for x in r["rejected"]] == [2, 3]


# ---------------------------------------------------------------- debounce, append-only assessments, tier boundary
def test_debounce_and_append_only_versions(dev):
    c, core, clock = dev
    oid = c.post("/api/orders/ingest", json={"kind": "paste", "text": "nheb sac cuir"}).json()["created"][0]["order_id"]
    conv = c.get(f"/api/orders/{oid}").json()["order"]["conversation_id"]
    for t in ("fi Sfax", "nahj el Jazira, dar 12"):
        clock.advance(1)
        c.post(f"/api/conversations/{conv}/simulate-reply", json={"kind": "text", "text": t})
    assert core.drain() == 0                                       # not due yet (last + 4 s)
    assert settle(core, clock, 4) == 1                             # exactly one rescore for the burst
    conn = core.conn()
    v1 = dict(conn.execute("SELECT * FROM risk_assessments WHERE order_id=? AND version=1", (oid,)).fetchone())
    conn.execute("UPDATE orders SET pending_rescore_at=?, pending_trigger='manual' WHERE order_id=?",
                 (repo.utc_iso(clock.now()), oid))
    core.drain()
    assert dict(conn.execute("SELECT * FROM risk_assessments WHERE order_id=? AND version=1", (oid,)).fetchone()) == v1
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO risk_assessments SELECT * FROM risk_assessments WHERE order_id=? AND version=1", (oid,))


def test_order_boundary_after_terminal(dev):
    c, core, clock = dev
    oid = c.post("/api/orders/ingest", json={"kind": "paste", "text": "nheb sac cuir"}).json()["created"][0]["order_id"]
    settle(core, clock)
    c.post(f"/api/orders/{oid}/actions", json={"action": "cancel"})
    conv = c.get(f"/api/orders/{oid}").json()["order"]["conversation_id"]
    r = c.post(f"/api/conversations/{conv}/simulate-reply", json={"kind": "text", "text": "nheb zouz"}).json()
    assert r["order_id"] != oid                                    # terminal -> a new order opens


# ---------------------------------------------------------------- state machine and actions
def test_seller_actions_and_invalid_transition(dev):
    c, core, clock = dev
    oid = c.post("/api/orders/ingest", json={"kind": "paste", "text": "nheb sac cuir, Sfax"}).json()["created"][0]["order_id"]
    settle(core, clock)
    r = c.post(f"/api/orders/{oid}/actions", json={"action": "ship"})
    assert r.status_code == 409 and r.json()["error"]["code"] == "INVALID_TRANSITION"
    assert c.post(f"/api/orders/{oid}/actions", json={"action": "approve"}).json()["status"] == "ready_to_ship"
    assert c.post(f"/api/orders/{oid}/actions", json={"action": "ship"}).json()["status"] == "shipped"
    cust = c.get(f"/api/orders/{oid}").json()["customer"]
    c.post(f"/api/orders/{oid}/actions", json={"action": "mark_refused"})
    after = c.get(f"/api/orders/{oid}").json()["customer"]
    assert (after["completed_orders"], after["refusals_total"]) == (cust["completed_orders"] + 1, cust["refusals_total"] + 1)
    assert c.post(f"/api/orders/{oid}/rescore").status_code == 409


def _result(tier="high", conf="none", path="llm", inj=False, change=False):
    inp = ScoreInput("o", None, "paste", "initial", [], StructuredFields(), CustomerHistory(0, 0), None, T0)
    from wasel.contracts import WindowMessage
    inp = ScoreInput("o", None, "paste", "initial",
                     [WindowMessage("m0", "inbound", "customer", "paste", "text", "nheb sac", None, None, None, False,
                                    T0, True)], StructuredFields(), CustomerHistory(0, 0), None, T0)
    r = stub.score_order(inp)
    from dataclasses import replace
    a = replace(r.assessment, tier=tier, confirmation=conf, path=path, is_order_change=change)
    return replace(r, assessment=a, injection_suspected=inj)


@pytest.mark.parametrize("current,res,trigger,prior,approved,expected", [
    ("collecting", dict(inj=True, tier="low"), "initial", None, None, "needs_review"),
    ("awaiting_reply", dict(conf="declined", tier="low"), "customer_reply", "high", None, "cancelled"),
    ("collecting", dict(change=True), "initial", None, None, "needs_review"),
    ("collecting", dict(path="rules", tier="low"), "initial", None, None, "ready_to_ship"),
    ("collecting", dict(path="rules", tier="medium"), "initial", None, None, "awaiting_reply"),
    ("awaiting_reply", dict(), "no_reply_timeout", "high", None, "needs_review"),
    ("awaiting_reply", dict(conf="ambiguous"), "customer_reply", "high", None, "needs_review"),
    ("ready_to_ship", dict(tier="medium"), "customer_reply", "high", "t", "ready_to_ship"),
    ("ready_to_ship", dict(tier="high"), "customer_reply", "low", "t", "needs_review"),
    ("collecting", dict(tier="low"), "initial", None, None, "ready_to_ship"),
    ("needs_review", dict(tier="medium"), "customer_reply", "high", None, "needs_review"),
    ("collecting", dict(tier="medium"), "initial", None, None, "awaiting_reply"),
])
def test_next_status_table(current, res, trigger, prior, approved, expected):
    assert next_status(current, _result(**res), trigger, prior, approved) == expected


def test_actions_table_shape():
    assert ACTIONS["cancel"][1] == "cancelled" and "shipped" not in ACTIONS["cancel"][0]


# ---------------------------------------------------------------- C2 stub contract / C1 real results persist
def test_stub_scorer_satisfies_contract(tmp_path):
    conn = fresh_db(tmp_path / "c2.db")
    ids = SeqIds()
    from wasel.db.seed import seed_catalog
    from wasel.scoring.config import default_config
    seed_catalog(conn, default_config().catalog)
    with tx(conn):
        cus = repo.get_or_create_customer(conn, ids, T0, sandbox_id=None, display_name="x")
        cnv = repo.create_conversation(conn, ids, T0, customer_id=cus, sandbox_id=None, channel="paste")
        from wasel.ingress.ingest import store_inbound
        st = store_inbound(conn, ids, T0, conversation_id=cnv, origin="paste", text="salam nheb sac", no_debounce=True)
    from wasel.outbound.make_draft import make_draft
    from wasel.worker import drain
    assert drain(conn, T0, stub.score_order, lambda r: make_draft(r), ids=ids) == 1
    conn.execute("UPDATE orders SET pending_rescore_at=?, pending_trigger='customer_reply' WHERE order_id=?",
                 (repo.utc_iso(T0), st.order_id))
    drain(conn, T0, stub.score_order, lambda r: make_draft(r), ids=ids)
    vs = [r[0] for r in conn.execute("SELECT version FROM risk_assessments ORDER BY version")]
    assert vs == [1, 2]


@pytest.mark.parametrize("llm_mode", ["fail_all", "fail_primary"])
def test_fallback_drill_never_errors(tmp_path, llm_mode):
    """E3: hero v1 still scored, every call 200, fallback visible. (fail_primary has no replay fixture for a new
    window, so it ends in rules too: FixtureMissing is caught by the worker -> needs_review + error event, or the rules path.)"""
    c, core, clock = make_client(tmp_path, "dev", llm_mode=llm_mode)
    with c:
        r = c.post("/api/orders/ingest", json={"kind": "paste", "text": "salam, nheb el casque bluetooth. "
                                                                         "Douar Ouled Ali, 9rib el jemaa"})
        assert r.status_code == 202
        settle(core, clock)
        d = c.get(f"/api/orders/{r.json()['created'][0]['order_id']}").json()
        if llm_mode == "fail_all":                                  # rules path: a next step and a drafted question
            assert d["order"]["status"] == "awaiting_reply" and d["order"]["has_pending_draft"]
        else:
            assert d["order"]["status"] in ("awaiting_reply", "needs_review")
        assert c.get("/api/health").status_code == 200


def test_admin_reset_reseeds(dev):
    c, core, clock = dev
    c.post("/api/orders/ingest", json={"kind": "paste", "text": "nheb sac"})
    before = core.conn().execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    assert c.post("/api/admin/reset").status_code == 401
    r = c.post("/api/admin/reset", headers={"X-Admin-Token": "x" * 24}).json()
    assert r["purged_rows"] == before and r["reseeded_orders"] == before - 1
    assert json.loads(json.dumps(r))


def test_committed_mocks_match_api_models():
    """tests/fixtures/api/*.json validate against the Pydantic response models (regenerate with `make mocks`)."""
    from pathlib import Path
    root = Path(__file__).resolve().parents[1] / "fixtures" / "api"
    M.OrderListResponse.model_validate_json((root / "orders.json").read_text(encoding="utf-8"))
    M.OrderDetailResponse.model_validate_json((root / "order_detail.json").read_text(encoding="utf-8"))
    M.OrderDetailResponse.model_validate_json((root / "order_detail_ar.json").read_text(encoding="utf-8"))
    M.HealthResponse.model_validate_json((root / "health.json").read_text(encoding="utf-8"))


def test_extraction_cache_is_read_with_the_active_prompt_version(dev):
    from wasel.llm.prompts import PROMPT_VERSION
    _, core, _ = dev
    assert core.scorer_for(core.conn()).keywords["cache"].prompt_version == PROMPT_VERSION
