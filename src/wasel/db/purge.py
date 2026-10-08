"""purge_sandboxes (public mode, every PURGE_INTERVAL_S) and reset_all (admin reset)."""
from __future__ import annotations

from datetime import datetime, timedelta

from wasel.clock import utc_iso
from wasel.db.conn import tx

PURGE_SQL = """
CREATE TEMP TABLE _vc AS SELECT conversation_id FROM conversations WHERE sandbox_id IS NOT NULL AND opened_at < :cutoff;
CREATE TEMP TABLE _vo AS SELECT order_id FROM orders WHERE conversation_id IN (SELECT conversation_id FROM _vc);
DELETE FROM events           WHERE order_id IN (SELECT order_id FROM _vo) OR (sandbox_id IS NOT NULL AND ts < :cutoff);
UPDATE orders SET current_assessment_id = NULL WHERE order_id IN (SELECT order_id FROM _vo);
DELETE FROM outbound_drafts  WHERE order_id IN (SELECT order_id FROM _vo);
DELETE FROM risk_assessments WHERE order_id IN (SELECT order_id FROM _vo);
DELETE FROM extraction_runs  WHERE order_id IN (SELECT order_id FROM _vo);
DELETE FROM order_messages   WHERE order_id IN (SELECT order_id FROM _vo);
DELETE FROM orders           WHERE order_id IN (SELECT order_id FROM _vo);
DELETE FROM messages         WHERE conversation_id IN (SELECT conversation_id FROM _vc);
DELETE FROM conversations    WHERE conversation_id IN (SELECT conversation_id FROM _vc);
DELETE FROM customers        WHERE sandbox_id IS NOT NULL AND customer_id NOT IN (SELECT customer_id FROM conversations);
DELETE FROM extraction_cache WHERE sandbox_id IS NOT NULL AND created_at < :cutoff;
DELETE FROM llm_usage        WHERE ts < :usage_cutoff;
"""


def purge_sandboxes(conn, now: datetime, ttl_s: int = 7200) -> int:
    """Deletes visitor rows older than the TTL with all their children, including the cache rows made from their
    text. Returns the number of orders purged."""
    params = {"cutoff": utc_iso(now - timedelta(seconds=ttl_s)), "usage_cutoff": utc_iso(now - timedelta(days=2))}
    with tx(conn):
        conn.execute("DROP TABLE IF EXISTS temp._vc")
        conn.execute("DROP TABLE IF EXISTS temp._vo")
        n = 0
        for stmt in [s.strip() for s in PURGE_SQL.split(";") if s.strip()]:
            cur = conn.execute(stmt, {k: v for k, v in params.items() if f":{k}" in stmt})
            if stmt.startswith("DELETE FROM orders"):
                n = cur.rowcount
        conn.execute("DROP TABLE _vc")
        conn.execute("DROP TABLE _vo")
    return n


def reset_all(conn) -> int:
    """Deletes every order-side row and the cache rows made from visitor text; keeps catalog, the other
    extraction_cache rows and llm_usage. The caller reseeds."""
    with tx(conn):
        n = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        conn.execute("UPDATE orders SET current_assessment_id = NULL")
        for t in ("events", "outbound_drafts", "risk_assessments", "extraction_runs", "order_messages", "orders",
                  "messages", "conversations", "customers"):
            conn.execute(f"DELETE FROM {t}")
        conn.execute("DELETE FROM extraction_cache WHERE sandbox_id IS NOT NULL")
    return n
