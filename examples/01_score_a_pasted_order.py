"""Paste a raw customer message, let the worker score it, print tier, action and reason.

    python examples/01_score_a_pasted_order.py
"""
from _client import client, show, wait_for_version

c = client()
text = "slm n7eb el casque bluetooth, livraison l douar ouled ali 9rib el jemaa, ken nal9ach nra9ed nji ghodwa"
r = c.post("/orders/ingest", json={"kind": "paste", "text": text, "customer_name": "Sami"})
r.raise_for_status()
ref = r.json()["created"][0]
print(f"ingested {ref['order_ref']} ({ref['order_id']}), scoring in ~{r.json()['rescore_eta_s']:.0f} s")
show(wait_for_version(c, ref["order_id"], 1))
