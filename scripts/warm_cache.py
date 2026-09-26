"""Build data/seed/extraction_cache.jsonl by running every seed conversation (and its scripted replies)
through the real worker in a scratch DB, so the cache keys match exactly what the app computes at boot.

    python -m scripts.warm_cache            # hand mode: data/seed/hand_extractions.json, model 'hand-crafted'
    python -m scripts.warm_cache --live     # live mode: the configured LLM chain (dev key!) records real outputs

A PROMPT_VERSION bump or a seed/template text change requires a rerun (C4 / test_seed_all_cache_hits).
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from app.api.commands import simulate_reply
from app.contracts import CachedExtraction
from app.db import repo
from app.db.cache import SqliteExtractionCache
from app.db.conn import fresh_db
from app.db.seed import CACHE_FILE, load_seed, seed_catalog, seed_conversation
from app.extraction.window import build_window
from app.ids import SeqIds
from app.llm.prompts import PROMPT_VERSION
from app.outbound.make_draft import make_draft
from app.scoring.config import default_config
from app.scoring.score_order import make_scorer
from app.settings import Settings
from app.worker import build_score_input, drain

ROOT = Path(__file__).resolve().parents[1]
HAND_MODEL = "hand-crafted (not an LLM output; run scripts.warm_cache --live)"
NOW = datetime(2026, 9, 26, 12, 0, tzinfo=UTC)


class _HandCache(SqliteExtractionCache):
    """Serves the hand extraction for the next pending window of an order."""

    def __init__(self, conn, pending: dict):
        super().__init__(conn, PROMPT_VERSION)
        self.pending = pending

    def get(self, input_hash):
        hit = super().get(input_hash)
        if hit is None and input_hash in self.pending:
            ext = self.pending[input_hash]
            self.conn.execute("INSERT OR REPLACE INTO extraction_cache VALUES (?,?,?,?,?,?,?,?)",
                              (input_hash, PROMPT_VERSION, "groq", HAND_MODEL, "llm", 1, json.dumps(ext, ensure_ascii=False),
                               "2026-09-26T12:00:00.000000Z"))
            return CachedExtraction(input_hash, "groq", HAND_MODEL, "llm", ext)
        return hit


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--out", default=str(CACHE_FILE))
    a = ap.parse_args(argv)
    cfg = default_config()
    hand = json.loads((ROOT / "data/seed/hand_extractions.json").read_text(encoding="utf-8"))
    settings = Settings(app_mode="dev", demo_mode=True)
    with tempfile.TemporaryDirectory() as d:
        conn = fresh_db(Path(d) / "warm.db")
        ids = SeqIds()
        seed_catalog(conn, cfg.catalog)
        pending: dict = {}
        cache = _HandCache(conn, pending)
        llm = None
        if a.live:
            from app.llm.client import build_client
            llm = build_client("live")
            if not llm.steps:
                print("--live needs GROQ_API_KEY (dev org)", file=sys.stderr)
                return 1
        scorer = make_scorer(cache=cache, llm=llm, meter=None, config=cfg)

        def drafter(req):
            return make_draft(req, config=cfg)

        def expect(order_id, extraction):
            if a.live:
                return
            o = repo.get_order(conn, order_id)
            key = build_window(build_score_input(conn, o, "initial", NOW)).cache_key(PROMPT_VERSION)
            pending[key] = extraction

        for fx in load_seed()["conversations"]:
            oid = seed_conversation(conn, ids, NOW, fx, None)
            expect(oid, hand[fx["key"]]["v1"])
            drain(conn, NOW, scorer, drafter, ids=ids)
            for i, reply in enumerate(fx.get("scripted_replies", [])):
                conv = repo.get_order(conn, oid)["conversation_id"]
                r = simulate_reply(conn, ids, NOW, settings, cfg.raw, None, conv, text=reply)
                conn.execute("UPDATE orders SET pending_rescore_at=? WHERE order_id=?",
                             (repo.utc_iso(NOW), r["order_id"]))
                expect(r["order_id"], hand[fx["key"]]["replies"][i])
                drain(conn, NOW, scorer, drafter, ids=ids)
        rows_ = conn.execute("SELECT * FROM extraction_cache ORDER BY input_hash").fetchall()
        paths = conn.execute("SELECT o.order_no, a.version, a.path, a.tier, a.final_score FROM risk_assessments a"
                             " JOIN orders o USING(order_id) ORDER BY o.order_no, a.version").fetchall()
    with open(a.out, "w", encoding="utf-8") as f:
        for r in rows_:
            f.write(json.dumps({"input_hash": r["input_hash"], "prompt_version": r["prompt_version"],
                                "provider": r["provider"], "model": r["model"], "origin_path": r["origin_path"],
                                "extraction": json.loads(r["extraction_json"])}, ensure_ascii=False) + "\n")
    for p in paths:
        print(f"#{p[0]} v{p[1]} {p[2]:14s} {p[3]:6s} {p[4]}")
    print(f"wrote {len(rows_)} cache entries -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
