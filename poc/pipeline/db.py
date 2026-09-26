"""SQLite storage. Plain sqlite3; table shapes follow the design doc so a Postgres port is mechanical."""
import datetime as dt
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY,
    created_at TEXT, governorate TEXT, zone_tier TEXT,
    address_text TEXT, note_text TEXT, product_category TEXT,
    value_tnd REAL, item_count INTEGER, channel TEXT,
    is_first_order INTEGER, prior_orders INTEGER, prior_refusals INTEGER,
    refused INTEGER,              -- seeded outcome label (NULL for live orders)
    is_live INTEGER DEFAULT 0,
    status TEXT DEFAULT 'new'     -- new | decided
);
CREATE TABLE IF NOT EXISTS extractions (
    order_id TEXT, prompt_version TEXT, source TEXT, flags TEXT, failed INTEGER,
    latency_ms INTEGER, cache_hit INTEGER,
    UNIQUE(order_id, prompt_version)
);
CREATE TABLE IF NOT EXISTS scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT, model_version TEXT, score REAL, tier TEXT,
    contribs TEXT, action TEXT, explanation TEXT, created_at TEXT
);
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT, kind TEXT, body TEXT, source TEXT, status TEXT, attempt INTEGER,
    created_at TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS one_send_per_order_action
    ON messages(order_id, kind) WHERE status = 'sent';
CREATE TABLE IF NOT EXISTS judge_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT, attempt INTEGER, approved INTEGER, source TEXT,
    checks TEXT, reason TEXT, draft TEXT, created_at TEXT
);
CREATE TABLE IF NOT EXISTS decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT, action TEXT, created_at TEXT
);
CREATE TABLE IF NOT EXISTS llm_cache (
    key TEXT PRIMARY KEY, response TEXT, created_at TEXT
);
CREATE TABLE IF NOT EXISTS live_calls (
    day TEXT PRIMARY KEY, n INTEGER
);
"""

ORDER_COLS = [
    "order_id", "created_at", "governorate", "zone_tier", "address_text", "note_text",
    "product_category", "value_tnd", "item_count", "channel", "is_first_order",
    "prior_orders", "prior_refusals",
]


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def connect(path: Path | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path or config.DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


@contextmanager
def tx(conn: sqlite3.Connection):
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


# --- orders -----------------------------------------------------------------

def upsert_order(conn, order: dict, refused=None, is_live=False) -> None:
    vals = [order[c] for c in ORDER_COLS]
    vals[ORDER_COLS.index("is_first_order")] = int(bool(order["is_first_order"]))
    conn.execute(
        f"INSERT OR REPLACE INTO orders ({','.join(ORDER_COLS)}, refused, is_live) "
        f"VALUES ({','.join('?' * len(ORDER_COLS))}, ?, ?)",
        vals + [None if refused is None else int(refused), int(is_live)],
    )


def save_extraction(conn, order_id, ext) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO extractions VALUES (?,?,?,?,?,?,?)",
        (order_id, config.PROMPT_VERSION, ext.source,
         ext.flags.model_dump_json() if ext.flags else None,
         int(ext.failed), ext.latency_ms, int(ext.cache_hit)),
    )


def save_score(conn, order_id, model_version, s) -> None:
    conn.execute(
        "INSERT INTO scores (order_id, model_version, score, tier, contribs, action, explanation, created_at)"
        " VALUES (?,?,?,?,?,?,?,?)",
        (order_id, model_version, s.score, s.tier, json.dumps(s.contribs), s.action, s.explanation, now()),
    )


_LATEST = """
SELECT o.*, s.score, s.tier, s.action, s.explanation, s.contribs,
       e.flags, e.failed AS extraction_failed, e.source AS extraction_source,
       e.latency_ms AS extraction_ms, e.cache_hit
FROM orders o
JOIN scores s ON s.id = (SELECT MAX(id) FROM scores WHERE order_id = o.order_id)
LEFT JOIN extractions e ON e.order_id = o.order_id AND e.prompt_version = ?
"""


def list_orders(conn) -> list[dict]:
    rows = conn.execute(_LATEST + " ORDER BY o.is_live DESC, s.score DESC", (config.PROMPT_VERSION,))
    return [dict(r) for r in rows]


def get_order(conn, order_id) -> dict | None:
    r = conn.execute(_LATEST + " WHERE o.order_id = ?", (config.PROMPT_VERSION, order_id)).fetchone()
    return dict(r) if r else None


def record_decision(conn, order_id, action) -> None:
    with tx(conn):
        conn.execute("INSERT INTO decisions (order_id, action, created_at) VALUES (?,?,?)",
                     (order_id, action, now()))
        conn.execute("UPDATE orders SET status='decided' WHERE order_id=?", (order_id,))


def last_decision(conn, order_id) -> str | None:
    r = conn.execute("SELECT action FROM decisions WHERE order_id=? ORDER BY id DESC LIMIT 1",
                     (order_id,)).fetchone()
    return r["action"] if r else None


# --- messages / judge -------------------------------------------------------

def log_judge(conn, order_id, attempt, verdict, draft_body) -> None:
    with tx(conn):
        conn.execute(
            "INSERT INTO judge_log (order_id, attempt, approved, source, checks, reason, draft, created_at)"
            " VALUES (?,?,?,?,?,?,?,?)",
            (order_id, attempt, int(verdict.approved), verdict.source, json.dumps(verdict.checks),
             verdict.reason, draft_body, now()),
        )


def judge_log(conn, limit=50) -> list[dict]:
    rows = conn.execute("SELECT * FROM judge_log ORDER BY id DESC LIMIT ?", (limit,))
    return [dict(r) for r in rows]


def send_message(conn, order_id, kind, body, source) -> bool:
    """Returns False if a message of this kind was already sent for this order (no duplicate sends)."""
    try:
        with tx(conn):
            conn.execute(
                "INSERT INTO messages (order_id, kind, body, source, status, attempt, created_at)"
                " VALUES (?,?,?,?, 'sent', 1, ?)",
                (order_id, kind, body, source, now()),
            )
        return True
    except sqlite3.IntegrityError:
        return False


def sent_messages(conn, order_id) -> list[dict]:
    rows = conn.execute("SELECT * FROM messages WHERE order_id=? AND status='sent' ORDER BY id", (order_id,))
    return [dict(r) for r in rows]


# --- LLM cache and live-call cap ---------------------------------------------

def cache_get(conn, key):
    r = conn.execute("SELECT response FROM llm_cache WHERE key=?", (key,)).fetchone()
    return json.loads(r["response"]) if r else None


def cache_put(conn, key, response) -> None:
    with tx(conn):
        conn.execute("INSERT OR REPLACE INTO llm_cache VALUES (?,?,?)", (key, json.dumps(response), now()))


def live_calls_today(conn) -> int:
    r = conn.execute("SELECT n FROM live_calls WHERE day=?", (dt.date.today().isoformat(),)).fetchone()
    return r["n"] if r else 0


def bump_live_calls(conn) -> None:
    with tx(conn):
        conn.execute(
            "INSERT INTO live_calls VALUES (?, 1) ON CONFLICT(day) DO UPDATE SET n = n + 1",
            (dt.date.today().isoformat(),),
        )
