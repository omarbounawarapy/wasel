"""T0.1 and T0.2: builds dataset.json and content.json from the saved API samples and the real page copy.

Run from the repo root: python3 docs/design-explorations/_source/dataset_build.py
Every brand-book screen reads ONLY these two files plus registry.json.
"""
import json, re
from datetime import datetime

D = "docs/design-explorations/_data/"
L = lambda n: json.load(open(D + n))

orders_raw = L("api_orders.json")["orders"]
detail = L("api_order_detail.json")
events_raw = L("api_events.json")["events"]
impact = L("api_metrics_impact.json")
ev = L("api_eval.json")
mon = L("api_monitor.json")
fail = L("api_failures.json")
health = L("api_health.json")

# zones are not in the API list; they come from the seeded reasons ("rural delivery zone", urban otherwise)
RURAL = {"#2601", "#2609", "#2604"}

def clean(s):
    return re.sub(r"[⁦-⁩]", "", s) if isinstance(s, str) else s

orders = []
for o in orders_raw:
    sc = o.get("score") or {}
    orders.append(dict(
        id=o["order_id"], ref=o["order_ref"], conversation_id=o["conversation_id"],
        customer=o["customer"]["display_name"], product=o["product_name"], price_tnd=o["price_tnd"],
        score=sc.get("final_score"), tier_raw=sc.get("tier"), action_raw=sc.get("action"),
        status_raw=o["status"], channel=o["channel"], preview=clean(o.get("last_message_preview")),
        reason_short=clean(sc.get("reason_short")), has_pending_draft=o["has_pending_draft"],
        zone="rural" if o["order_ref"] in RURAL else "urban", updated_at=o["updated_at"],
    ))
orders.sort(key=lambda x: -(x["score"] or 0))

# hero order (#2601): conversation, reasons, draft, scripted reply, rescoring outcome
msgs = []
for m in detail["conversation"]["messages"]:
    msgs.append(dict(author=m["author"], text=m["text"], ts=m["provider_ts"], segments=m.get("segments")))
a = detail["assessments"][0]
hero = dict(
    ref=detail["order"]["order_ref"], customer=detail["customer"]["display_name"], product=detail["order"]["product_name"],
    price_tnd=detail["order"]["price_tnd"],
    messages=msgs,
    flags=[dict(code=f["code"], label=f["label"], quote=f["quote"]) for f in a["flags"]],
    factors=[dict(label=clean(f["label"]), points=round(f["contribution"])) for f in a["top_factors"]],
    base=30,
    reason_text=clean(a["reason"]),
    draft=dict(language=detail["drafts"][0]["language"], text=detail["drafts"][0]["text"], source=detail["drafts"][0]["source"]),
    scripted_reply=detail["scripted_replies"][0],
    # README: after a full address the score falls to 16 ("full address given -32")
    history=[dict(version=1, score=87, label="First score", note="3 warning signs, rural delivery zone, vague address"),
             dict(version=2, score=16, label="After the reply", note="full address given -32")],
    arabic_message="دوار أولاد علي، قريب من الجامع. غالي شوية، مش دايما في الدار",
    french_draft="Bonjour Sami, pouvez-vous nous donner la rue, le numéro et un téléphone pour la livraison ?",
)

events = [dict(ts=e["ts"], type=e["type"], level=e["level"], ref=e["order_ref"], title=e["title"], detail=e["detail"]) for e in events_raw[:24]]

suite_names = {
    "extraction": "Reading customer messages", "outbound": "Safety of drafted replies", "injection": "Resisting tricks",
    "g1_conversations": "Real conversations by a native speaker", "g3_injection": "Tricks written by a native speaker", "prefilter_cases": "Reply rule checks",
}
off = ev["offline"]["results"]
quality = [
    dict(suite=suite_names["extraction"], n=off["extraction"]["n"], metrics=[("Spots real orders", off["extraction"]["is_order_acc"]), ("Reads the address correctly", off["extraction"]["address_within1_acc"]), ("Recognises the language", off["extraction"]["language_acc"])]),
    dict(suite=suite_names["outbound"], n=off["outbound"]["n"], metrics=[("Unsafe replies blocked", off["outbound"]["unsafe_blocked"]), ("Good replies allowed", off["outbound"]["safe_passed"]), ("Overall", off["outbound"]["task_success"])]),
    dict(suite=suite_names["injection"], n=off["injection"]["n"], metrics=[("Tricks detected", off["injection"]["flagged_rate"]), ("Order still scored", off["injection"]["still_scored_rate"]), ("Score not lowered by the trick", off["injection"]["not_promoted_rate"])]),
    dict(suite=suite_names["g1_conversations"], n=off["g1_conversations"]["n"], metrics=[("Spots real orders", off["g1_conversations"]["is_order_acc"]), ("Reads the address correctly", off["g1_conversations"]["address_within1_acc"]), ("Warning signs are right", off["g1_conversations"]["flag_f1"])]),
]

monitor = dict(
    window=mon["window"], n=mon["drift"][0]["n"],
    drift=[dict(name={"language": "Languages customers write in", "address_level": "How precise addresses are", "tier": "Share of risk levels"}[d["feature"]], psi=d["psi"], drifted=d["drifted"]) for d in mon["drift"]],
    safety=[("Invented quotes", 0.0), ("Unreadable AI answers", 0.0), ("Trick attempts", 0.0), ("Fallback used", 0.0)],
    alerts=mon.get("alerts", []),
)

def hm(m): return f"{m // 60:02d}:{m % 60:02d}"
NOW = 14 * 60 + 32
WAIT = {"#2609": 195, "#2601": 190, "#2604": 130, "#2605": 70, "#2603": 40, "#2608": 25, "#2606": 20, "#2602": 15, "#2607": 10}
activity = []
for o in orders:
    t0 = NOW - WAIT[o["ref"]]
    activity.append(dict(t=t0, ts=hm(t0), title="Customer message received", ref=o["ref"], who=o["customer"]))
    activity.append(dict(t=t0 + 1, ts=hm(t0 + 1), title="Order scored", ref=o["ref"], who=o["customer"], detail=str(o["score"])))
    if o["tier_raw"] != "low":
        activity.append(dict(t=t0 + 2, ts=hm(t0 + 2), title="Confirmation drafted", ref=o["ref"], who=o["customer"]))
activity.sort(key=lambda a: -a["t"])
assumptions_plain = [("Cost of one failed delivery trip", "8 TND"), ("Refusals prevented when you ask to confirm", "30%"), ("Refusals prevented when you ask for prepayment", "60%"),
                     ("Customers lost when asking for prepayment", "10%"), ("Gross margin on an order", "25%"), ("Cost of a message", "0 TND")]

dataset = dict(
    note="All data is synthetic (repo seed data and the offline evaluation set). Nothing here is a real customer or a real measurement.",
    generated="2026-10-07",
    shop=dict(name="Synthetic shop", currency="TND", country="Tunisia"),
    now="14:32",
    orders=orders,
    counts=dict(total=len(orders), needs_decision=0, waiting=5, ready=4, high=4, medium=1, low=4, tnd_at_risk=sum(o["price_tnd"] for o in orders if o["tier_raw"] == "high")),
    hero=hero,
    events=events,
    activity=activity,
    impact=dict(tnd_saved=impact["tnd_saved"], trips_avoided=impact["trips_avoided"], n_orders=impact["n_orders"], baseline=impact["baseline_refusal_rate"], projected=impact["projected_refusal_rate"], assumptions=impact["assumptions"], assumptions_plain=assumptions_plain, simulated=True),
    quality=quality, quality_gate="all checks passed",
    monitor=monitor,
    failures=dict(source=fail["source"], sessions=fail["n_sessions"], events=fail["n_events"], findings=fail["findings"]),
    ops=dict(llm_primary=health["llm"]["primary"], chain=health["llm"]["chain_extract"], mode=health["mode"], whatsapp="off (demo mode)", ai_calls=0, typical_ms=None, backup_used=0),
    # same instants as the order list: waiting minutes shown in screens (derived, synthetic)
    waiting_minutes={"#2609": 195, "#2601": 190, "#2604": 130, "#2605": 70, "#2603": 40, "#2608": 25, "#2606": 20, "#2602": 15, "#2607": 10},
)
json.dump(dataset, open("docs/design-explorations/dataset.json", "w"), indent=1, ensure_ascii=False)

content = dict(
    shell=dict(status=["AI scoring live", "WhatsApp off (demo mode)", "Synthetic data"],
               nav_groups=[("Daily work", ["Orders to check", "WhatsApp messages", "Add an order"]), ("Results", ["Money saved", "Activity log"]), ("AI health", ["Quality checks", "Silent failures", "Live monitor", "AI call log"])],
               phone_nav=["Orders", "WhatsApp", "Add", "Money saved", "More"]),
    pages=dict(
        orders=dict(title="Orders to check", subtitle="Wasel reads what each customer wrote and scores how likely the order is to be refused at the door. Riskiest orders are at the top.",
                    guide=["A customer message arrives on WhatsApp, or you paste it.", "Wasel scores the refusal risk and explains why, in the customer's own words.", "Open an order to confirm with the customer, then ship it."],
                    counters=[("Needs your decision", "Wasel is unsure: you decide"), ("Waiting for customer", "A question was sent"), ("Ready to ship", "Confirmed or low risk")],
                    columns=["Order", "Risk", "Next step", "Status", "Why"], next_steps={"confirm": "Confirm with the customer", "prepay": "Ask for prepayment", "ship": "Ship normally", "review": "Check it yourself"},
                    statuses={"awaiting_reply": "Waiting for customer", "needs_review": "Needs your decision", "ready_to_ship": "Ready to ship", "shipped": "Shipped"}),
        order=dict(title="Order detail", sections=["What the customer said", "Message to the customer", "Why this score", "Score history"],
                   hints=["Highlighted words are what Wasel noticed. Hover or focus a highlight to see why.", "Every time the customer writes, Wasel scores the order again."],
                   actions=["Review the message", "Approve for shipping", "Cancel order", "Send the question", "Edit"],
                   verdict_line="Send the drafted question below, then wait for the customer's answer. Wasel rescores as soon as they reply."),
        messages=dict(title="WhatsApp messages", subtitle="Messages your customers send to your WhatsApp business number land here within seconds, already scored.",
                      counters=["Conversations", "Needs your decision", "Waiting for customer"], empty="No WhatsApp messages yet"),
        add=dict(title="Add an order", subtitle="Paste a customer's message exactly as they wrote it, in Darija, Arabizi, Arabic or French. Wasel scores it in a few seconds.",
                 fields=["Customer message", "What the customer wrote", "Customer name", "Product", "Price (TND)", "Delivery zone"], cta="Score this order",
                 examples=["Vague address (Darija)", "Precise address (French)", "Arabic script, a neighbour receives it", "Tries to trick the AI"]),
        impact=dict(title="Money saved", subtitle="How much wasted delivery cost Wasel avoids when you follow its advice. This is a simulation on synthetic orders, not real sales.",
                    blocks=["Estimated wasted-trip cost avoided", "Refused at the door today", "Refused with Wasel", "How this was estimated"]),
        activity=dict(title="Activity log", subtitle="Everything Wasel did, newest first: messages received, scores, drafted replies and anything that needed attention.",
                      counters=["Messages received", "Orders scored", "Replies drafted", "Tricks blocked"], filter="Only warnings"),
        quality=dict(title="Quality checks", subtitle="Before every release, Wasel is tested on hundreds of example conversations. A release only ships when all checks pass.", banner="Release checks: all checks passed"),
        failures=dict(title="Silent failures", subtitle="A demonstration of the silent-failure analyzer on synthetic test conversations. It is not a measurement of real Wasel conversations.",
                      counters=["Test conversations checked", "Silent failures", "Worth a second look"], note="Test data, not real Wasel conversations."),
        monitor=dict(title="Live monitor", subtitle="Watches the last messages Wasel scored and warns you if they start to look different from what it was tested on.", sections=["Are customers writing differently?", "Is the AI behaving?"], ok="Everything looks normal"),
        traces=dict(title="AI call log", subtitle="Every request Wasel made to an AI model: what it was for, which model answered and how long it took. Customer text is never stored here.", counters=["AI calls", "Typical answer time", "Backup model used"], empty="No AI calls yet"),
    ),
    states=dict(empty="Nothing here yet", loading="Loading", error="Could not load this. Check that the Wasel server is running, then refresh the page.", offline="Can't reach the Wasel server. Showing the last data received.", scoring="Scoring"),
    rules=["Risk tier is never carried by colour alone: name, glyph and colour together.", "Customer text uses dir=auto and keeps its original script.", "Show a visible 'Synthetic data' note."],
)
json.dump(content, open("docs/design-explorations/content.json", "w"), indent=1, ensure_ascii=False)
print("orders", len(orders), "events", len(events), "quality suites", len(quality))
