"""Streamlit fallback dashboard (06 §1.5): a second deployable that calls the API over API_BASE_URL.
Ships only if the React gate fails (FE0 / FE1 / G4); built here so the prototype has a UI today.

    API_BASE_URL=http://localhost:8000 streamlit run dashboard/app.py

Rules kept from the spec: every customer-derived string that reaches unsafe_allow_html goes through
html.escape; segments are rendered from the server's split (no offset math here); `dir="auto"` on
customer text; copy strings come from 06 §5 (Skeptic's exact strings verbatim)."""
from __future__ import annotations

import html
import os
import uuid

import httpx
import streamlit as st

API = os.environ.get("API_BASE_URL", "http://localhost:8000").rstrip("/")
TIER = {"high": ("HIGH", "#c5221f", "▲"), "medium": ("MED", "#b06000", "◆"), "low": ("LOW", "#137333", "●")}
ACTION = {"confirm": "Confirm with customer", "ship": "Ship", "prepay": "Ask for prepayment",
          "review": "Needs your review", "cancelled": "Cancelled"}
STATUS = {"collecting": "Collecting details", "awaiting_reply": "Waiting for customer", "needs_review": "Needs review",
          "ready_to_ship": "Ready to ship", "shipped": "Shipped", "delivered": "Delivered",
          "refused": "Refused at door", "cancelled": "Cancelled"}
PATH = {"llm": "AI extraction", "fallback_model": "Backup AI model", "fallback_provider": "Backup AI provider",
        "cascade_ack": "No AI needed · short reply", "cascade_cache": "Recorded AI result · no new AI call",
        "rules": "Rules only"}
TRIGGER = {"initial": "First score", "customer_reply": "Customer replied", "no_reply_timeout": "No reply in time",
           "manual": "Manual rescore"}
SELLER_ACTIONS = {"approve": "Approve for shipping", "request_confirmation": "Ask the customer to confirm",
                  "ship": "Mark shipped", "mark_delivered": "Mark delivered", "mark_refused": "Refused at door",
                  "cancel": "Cancel order"}
BANNER_PUBLIC = ("Public demo. Sample orders are synthetic and read-only — use **Try this order** to get your own copy. "
                 "What you add is visible only in this browser and deleted after 2 hours. "
                 "This demo never sends WhatsApp messages.")
TOAST_READONLY = ("Sample orders are read-only so every visitor starts from the same point. "
                  "**Try this order** to work on your own copy.")
CSS = """<style>
mark.hl-risk{background:#fde293;border-bottom:2px dotted #b06000;color:#111;padding:0 1px}
mark.hl-address{background:none;border-bottom:2px solid #137333;color:inherit}
p.bubble{line-height:1.6;text-align:start;margin:0;font-family:system-ui,"Segoe UI","Noto Sans Arabic",Tahoma,sans-serif}
.cust{background:#f1f3f4;border-radius:10px;padding:8px 12px;margin:4px 25% 4px 0}
.ai{background:#e6f4ea;border-radius:10px;padding:8px 12px;margin:4px 0 4px 25%}
.chip{font-size:.75rem;color:#5f6368}
</style>"""

st.set_page_config(page_title="COD Risk", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)
vid = st.session_state.setdefault("visitor_id", str(uuid.uuid4()))
HEAD = {"X-Visitor-Id": vid}


def api(method: str, path: str, **kw):
    try:
        r = httpx.request(method, f"{API}{path}", headers=HEAD, timeout=30, **kw)
    except httpx.HTTPError:
        st.error("No connection to the server. Try again.")
        st.stop()
    if r.status_code >= 400:
        err = r.json().get("error", {}) if r.headers.get("content-type", "").startswith("application/json") else {}
        if err.get("code") == "SEEDED_READ_ONLY":
            st.toast(TOAST_READONLY)
        else:
            st.error(f"{err.get('code', r.status_code)}: {err.get('message', r.text[:200])}")
        return None
    return r.json()


def e(s) -> str:
    return html.escape("" if s is None else str(s))


def render_segments(segs) -> str:
    return "".join(f'<mark class="hl-{s["kind"]}" title="{e(s["label"])}">{e(s["text"])}</mark>' if s["kind"]
                   else e(s["text"]) for s in segs)


def badge(score) -> str:
    if not score:
        return "Scoring…"
    word, color, shape = TIER[score["tier"]]
    delta = "" if score["delta"] is None else (f" ▼{-score['delta']}" if score["delta"] < 0 else f" ▲{score['delta']}")
    return f'<b style="color:{color}">{shape} {word} {score["final_score"]}</b>{delta}'


health = api("GET", "/api/health") or {}
mode = health.get("mode", "public")
st.title("COD Risk")
st.caption({"public": "Public demo", "event": "Live pilot · a person approves every send", "dev": "Dev"}[mode])
if mode == "public":
    st.info(BANNER_PUBLIC)
llm = health.get("llm", {})
if llm.get("cap_reached"):
    st.warning("Today's live-AI budget for this public demo is used up. New text is scored by the rules-only fallback "
               "(marked **rules**). The budget resets at 01:00 Tunis time.")
elif llm.get("fallback_active"):
    st.warning(f"The main AI model is unavailable right now. Scores are coming from {llm.get('last_path')}; "
               "each score shows which path produced it.")

lst = api("GET", "/api/orders") or {"orders": [], "counts": {}}
c = lst["counts"]
if c:
    st.caption(f"{c['needs_review']} need review · {c['awaiting_reply']} waiting for customer · "
               f"{c['ready_to_ship']} ready to ship")
impact = api("GET", "/api/metrics/impact")
if impact and impact.get("n_orders"):
    st.caption(f"Simulated on {impact['n_orders']} synthetic orders: refusal rate "
               f"{impact['baseline_refusal_rate']:.0%} → {impact['projected_refusal_rate']:.0%}, "
               f"{impact['trips_avoided']:.0f} trips and {impact['tnd_saved']:.0f} TND avoided.")

left, right = st.columns([2, 3])
selected = st.query_params.get("order")

with left:
    with st.expander("Paste order"):
        with st.form("paste", clear_on_submit=True):
            if mode == "public":
                st.caption("Visible only in this browser and deleted after 2 hours. Don't paste real customer data.")
            text = st.text_area("Customer message", max_chars=2000,
                                placeholder="Paste the customer's message exactly as they wrote it: Darija, Arabizi "
                                            "or French.")
            if st.form_submit_button("Add order") and text.strip():
                r = api("POST", "/api/orders/ingest", json={"kind": "paste", "text": text})
                if r:
                    st.query_params["order"] = r["created"][0]["order_id"]
                    st.rerun()
    for o in lst["orders"]:
        who = "Sample" if o["is_seeded"] else "Yours"
        st.markdown(f'{badge(o["score"])} · {e(o["order_ref"])} · <bdi>{e(o["customer"]["display_name"])}</bdi> '
                    f'<span class="chip">{who} · {STATUS[o["status"]]}</span>', unsafe_allow_html=True)
        if o["score"]:
            st.caption(o["score"]["reason_short"])
        if st.button(f"Open {o['order_ref']}", key=o["order_id"]):
            st.query_params["order"] = o["order_id"]
            st.rerun()

with right:
    if not selected:
        st.subheader("Select an order")
        st.caption("Pick an order on the left to see why it was scored and what to do next.")
        st.stop()
    d = api("GET", f"/api/orders/{selected}")
    if d is None:
        st.info("This order isn't available any more. Your copies are deleted after 2 hours.")
        st.stop()
    o, caps = d["order"], d["capabilities"]
    st.markdown(f"### {e(o['order_ref'])} · {badge(o['score'])}", unsafe_allow_html=True)
    st.caption(f"{STATUS[o['status']]} · {e(o['product_name'])} · {o['price_tnd'] or '?'} TND · "
               f"zone {o['zone'] or '?'} ({o['zone_source']})")
    if o.get("injection_suspected"):
        st.error("Possible instruction text in the message — check before acting.")
    if caps["read_only"]:
        st.caption("This sample is shared by every visitor, so it's read-only. Make your own copy to send the "
                   "message and simulate the customer's reply.")
        if caps["can_try"] and st.button("Try this order", type="primary"):
            r = api("POST", f"/api/orders/{selected}/try")
            if r:
                st.query_params["order"] = r["order_id"]
                st.rerun()
    if o["rescore_state"] != "idle":
        st.info({"debouncing": "New message · rescoring in a few seconds…",
                 "scoring": "Reading the messages and scoring…",
                 "drafting": "Drafting the message to the customer…"}[o["rescore_state"]])
        if st.button("Refresh"):
            st.rerun()

    if d["assessments"]:
        a = d["assessments"][-1]
        st.markdown("**Why this score**")
        st.write(a["reason"])
        conf = "High confidence" if a["confidence"] == "high" else "Low confidence · check before acting"
        st.caption(f"{conf} · {ACTION[a['action']]} · {PATH[a['path']]}"
                   + (f" · {a['extraction']['model']}" if a.get("extraction") else ""))

    st.markdown("**Conversation**")
    for m in d["conversation"]["messages"]:
        cls = "cust" if m["author"] == "customer" else "ai"
        body = render_segments(m["segments"]) if m["segments"] else e(m["text"] or m["kind"])
        chip = {"simulated": "Simulated", "seed": "Sample data", "dashboard": "Recorded, not sent"}.get(m["origin"], "")
        if m["author"] == "ai":
            chip = "Standard message · Sent (simulated)"
        st.markdown(f'<div class="{cls}"><p class="bubble" dir="auto">{body}</p>'
                    f'<span class="chip">{e(chip)}</span></div>', unsafe_allow_html=True)

    pending = [x for x in d["drafts"] if not x["sent_message_id"]]
    if pending:
        dr = pending[0]
        st.markdown("**Message to customer**")
        st.markdown(f'<p class="bubble" dir="auto">{e(dr["text"])}</p>', unsafe_allow_html=True)
        checks = "Rule checks passed" if dr["prefilter"]["passed"] else f"Blocked: {dr['prefilter']['failures']}"
        st.caption(f"Standard message · no AI-written text · {checks}")
        if caps["can_send_drafts"] and dr["route"] != "blocked" and st.button("Send message", type="primary"):
            if api("POST", f"/api/drafts/{dr['draft_id']}/send"):
                st.rerun()
        if caps["read_only"]:
            st.caption("Make your own copy to send this message.")

    if caps["can_simulate_reply"]:
        with st.container(border=True):
            st.caption("DEMO · Simulate a customer reply. Your reply goes through the same pipeline as a WhatsApp "
                       "message and is marked Simulated in the conversation.")
            if pending:
                st.caption("The message above hasn't been sent. Your simulated reply records it as sent first, "
                           "so the reply answers it.")
            for i, sr in enumerate(d["scripted_replies"]):
                if st.button(f"Scripted reply · instant: {sr[:60]}", key=f"sr{i}"):
                    api("POST", f"/api/conversations/{o['conversation_id']}/simulate-reply",
                        json={"kind": "text", "text": sr})
                    st.rerun()
            with st.form("reply", clear_on_submit=True):
                txt = st.text_area("Reply", placeholder="Type what the customer would reply…", max_chars=600)
                if st.form_submit_button("Send simulated reply") and txt.strip():
                    api("POST", f"/api/conversations/{o['conversation_id']}/simulate-reply",
                        json={"kind": "text", "text": txt})
                    st.rerun()

    if caps["actions"]:
        cols = st.columns(len(caps["actions"]))
        for col, act in zip(cols, caps["actions"], strict=True):
            if col.button(SELLER_ACTIONS[act], key=act):
                api("POST", f"/api/orders/{selected}/actions", json={"action": act})
                st.rerun()

    if d["assessments"]:
        st.markdown("**Score history**")
        for a in reversed(d["assessments"]):
            with st.container(border=True):
                st.markdown(f"v{a['version']} · {TRIGGER[a['trigger']]} · {badge(a)}", unsafe_allow_html=True)
                st.caption(f"Model {round(a['model_score'])}")
                for adj in a["adjustments"]:
                    st.caption(f"Rule: {adj['label']} {adj['effect']} (starting assumption)")
                if a["flags"]:
                    st.caption("Flagged: " + " · ".join(f"{f['label']} “{f['quote']}”" for f in a["flags"]))
                if a["resolved_flags"]:
                    st.caption("Resolved: " + ", ".join(a["resolved_flags"]))
                if a["reason_diff"]:
                    st.write(a["reason_diff"])

st.divider()
build, cfg_hash = health.get("build", {}).get("git_sha", "?"), health.get("config", {}).get("config_hash", "?")
st.caption(f"All orders and customers in this demo are synthetic test data. Build {build} · config {cfg_hash}")
