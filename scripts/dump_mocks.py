"""python -m scripts.dump_mocks: writes mocks/{orders,order_detail,health}.json from a seeded in-process app in
public mode, with the hero taken through the reply loop. The mocks therefore validate against
app/api/models.py by construction; tests/integration/test_backend.py checks the committed copies."""
from __future__ import annotations

import json
import tempfile
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from app.clock import FrozenClock
from app.ids import SeqIds
from app.llm.client import build_client
from app.main import create_app
from app.settings import Settings
from ml.hero import T0

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    vid = str(uuid.UUID(int=0xC0FFEE, version=4))
    h = {"X-Visitor-Id": vid}
    with tempfile.TemporaryDirectory() as d:
        clock = FrozenClock(T0)
        app = create_app(Settings(app_mode="public", db_path=str(Path(d) / "m.db"), worker_enabled=False),
                         clock=clock, llm=build_client("fail_all"), ids=SeqIds(), worker_enabled=False)
        with TestClient(app) as c:
            core = app.state.core
            hero = next(o for o in c.get("/api/orders", headers=h).json()["orders"] if o["seed_key"] == "hero")
            mine = c.post(f"/api/orders/{hero['order_id']}/try", headers=h).json()
            reply = c.get(f"/api/orders/{mine['order_id']}", headers=h).json()["scripted_replies"][0]
            c.post(f"/api/conversations/{mine['conversation_id']}/simulate-reply", headers=h,
                   json={"kind": "text", "text": reply})
            clock.advance(5)
            core.drain()
            orders = c.get("/api/orders", headers=h).json()
            ar = next(o["order_id"] for o in orders["orders"] if o["seed_key"] == "ar_area")
            out = {"orders.json": orders,
                   "order_detail.json": c.get(f"/api/orders/{mine['order_id']}", headers=h).json(),
                   "order_detail_ar.json": c.get(f"/api/orders/{ar}", headers=h).json(),
                   "health.json": c.get("/api/health").json()}
    (ROOT / "mocks").mkdir(exist_ok=True)
    for name, body in out.items():
        (ROOT / "mocks" / name).write_text(json.dumps(body, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("wrote mocks/" + name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
