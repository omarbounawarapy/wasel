"""python -m scripts.smoke URL  (M3, 05 §5). No key needed. One line per step; exits 1 on the first failure.
1 health (public: sends and webhook off)  2 GET /  3 try hero (public) or paste it (event/dev) -> HIGH
4 scripted reply -> LOW, lower score  5 public: rescore on the seeded hero -> 409  6 SMOKE PASS"""
from __future__ import annotations

import sys
import time
import uuid

import httpx


def main(url: str) -> int:
    url = url.rstrip("/")
    vid = str(uuid.uuid4())
    h = {"X-Visitor-Id": vid}
    t0 = time.monotonic()
    c = httpx.Client(timeout=30)

    def step(name, ok, detail=""):
        print(f"{'ok ' if ok else 'FAIL'} {name} {detail} ({time.monotonic() - t0:.1f}s)")
        if not ok:
            sys.exit(1)

    health = c.get(f"{url}/api/health").json()
    mode = health["mode"]
    step("health", mode != "public" or (health["wa_send"] is False and health["webhook"] == "disabled"),
         f"mode={mode} cap={health['llm']['live_call_cap']}")
    step("GET /", c.get(f"{url}/").status_code in (200, 404))
    orders = c.get(f"{url}/api/orders", headers=h).json()["orders"]
    seeded = next(o for o in orders if o.get("seed_key") == "hero" and o["is_seeded"])
    detail = c.get(f"{url}/api/orders/{seeded['order_id']}", headers=h).json()
    reply = detail["scripted_replies"][0]
    if mode == "public":
        r = c.post(f"{url}/api/orders/{seeded['order_id']}/try", headers=h).json()
        oid, cid = r["order_id"], r["conversation_id"]
    else:
        text = "\n".join(m["text"] for m in detail["conversation"]["messages"] if m["author"] == "customer")
        r = c.post(f"{url}/api/orders/ingest", headers=h, json={"kind": "paste", "text": text}).json()
        oid, cid = r["created"][0]["order_id"], r["created"][0]["conversation_id"]

    def wait_version(v, timeout=20):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            d = c.get(f"{url}/api/orders/{oid}", headers=h).json()
            if d["order"]["rescore_state"] == "idle" and len(d["assessments"]) >= v:
                return d["assessments"][v - 1]
            time.sleep(1)
        return None

    v1 = wait_version(1)
    step("v1 HIGH", v1 is not None and v1["tier"] == "high", f"{v1 and v1['final_score']} {v1 and v1['path']}")
    c.post(f"{url}/api/conversations/{cid}/simulate-reply", headers=h, json={"kind": "text", "text": reply})
    v2 = wait_version(2)
    step("v2 LOW", v2 is not None and v2["tier"] == "low" and v2["final_score"] < v1["final_score"],
         f"{v2 and v2['final_score']}")
    if mode == "public":
        r = c.post(f"{url}/api/orders/{seeded['order_id']}/rescore", headers=h)
        step("seeded read-only", r.status_code == 409)
    print(f"SMOKE PASS {url} {mode} v1={v1['final_score']} v2={v2['final_score']} {time.monotonic() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"))
