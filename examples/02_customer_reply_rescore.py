"""The demo moment: a HIGH-risk seeded order, the customer replies with a full address, the order is rescored.

    python examples/02_customer_reply_rescore.py
"""
from _client import client, show, wait_for_version

c = client()
hero = next(o for o in c.get("/orders").json()["orders"] if o.get("seed_key") == "hero")
d = c.get(f"/orders/{hero['order_id']}").json()
if d["capabilities"]["read_only"]:                      # public mode: seeded rows are read-only, work on a copy
    hero = c.post(f"/orders/{hero['order_id']}/try").json()
    d = wait_for_version(c, hero["order_id"], 1)
print("before the reply:")
show(d)

v = d["order"]["score"]["version"]
reply = d["scripted_replies"][0] if d["scripted_replies"] else "Douar Ouled Ali, triq el jemaa, dar 14. nkoun ghodwa."
print(f"\ncustomer replies: {reply!r}")
c.post(f"/conversations/{d['conversation']['conversation_id']}/simulate-reply", json={"kind": "text", "text": reply})

after = wait_for_version(c, hero["order_id"], v + 1)
print("after the reply:")
show(after)
diff = max(after["assessments"], key=lambda a: a["version"])["reason_diff"]
if diff:
    print(f"  diff:   {diff}")
