"""Walk the seller's side: read the queue, send the drafted confirmation, then approve and ship a low-risk order.

    python examples/03_seller_workflow.py
"""
from _client import client

c = client()
orders = c.get("/orders").json()["orders"]
print("queue (riskiest first):")
for o in orders:
    s = o["score"]
    print(f"  {o['order_ref']:6} {s['tier']:6} {s['final_score']:3}  {o['status']:15} {s['reason_short'][:70]}")

# 1. a risky order with a drafted question: a human sends it (nothing goes out on its own)
risky = next((o for o in orders if o["has_pending_draft"] and not o["read_only"]), None)
if not risky:
    print("\nno writable order with a pending draft (public mode: run 01 or 02 first with the same visitor)")
else:
    draft = next(x for x in c.get(f"/orders/{risky['order_id']}").json()["drafts"] if x["sent_at"] is None)
    print(f"\ndraft for {risky['order_ref']} ({draft['template_id']}):\n  {draft['text']}")
    sent = c.post(f"/drafts/{draft['draft_id']}/send").json()
    print(f"  sent at {sent['sent_at']} (delivery: {sent['delivery']})")

# 2. a low-risk order: ship it; an action not allowed from the current status comes back as 409
low = next((o for o in orders if o["status"] == "ready_to_ship" and not o["read_only"]), None)
if low:
    r = c.post(f"/orders/{low['order_id']}/actions", json={"action": "ship"})
    print(f"\nship {low['order_ref']}: {r.status_code} -> {r.json()['status']}")
    r = c.post(f"/orders/{low['order_id']}/actions", json={"action": "approve"})
    err = r.json()["error"]
    print(f"approve a shipped order: {r.status_code} {err['code']} allowed={err.get('details', {}).get('allowed')}")
