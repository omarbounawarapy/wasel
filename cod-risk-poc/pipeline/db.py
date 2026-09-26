"""SQLite storage. Plain sqlite3; table shapes follow the design doc so a Postgres port is mechanical."""
import datetime as dt
import json
import shutil
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
    created_at TEXT,
    channel TEXT DEFAULT 'mock',  -- mock | whatsapp
    to_wa TEXT,                   -- recipient WhatsApp ID (digits, no +)
    provider_id TEXT,             -- WhatsApp message ID (wamid), set when Meta accepts the send
    delivery TEXT,                -- mock | pending | accepted | sent | delivered | read | failed
    error TEXT
);
CREATE TABLE IF NOT EXISTS wa_inbound (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wamid TEXT UNIQUE,            -- Meta retries webhooks for up to 7 days: the unique key makes that a no-op
    from_wa TEXT, profile_name TEXT, order_id TEXT, type TEXT,
    intent TEXT,                  -- confirm | cancel | location | text
    text TEXT, button_id TEXT, latitude REAL, longitude REAL, context_id TEXT,
    sent_at TEXT, received_at TEXT
);
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


# One send per order per action. Seller replies and location requests are follow-ups, so they repeat.
REPEATABLE_KINDS = ("reply", "location_request", "template")
_INDEXES = f"""
DROP INDEX IF EXISTS one_send_per_order_action;
CREATE UNIQUE INDEX IF NOT EXISTS one_send_per_order_action_v2
    ON messages(order_id, kind) WHERE status = 'sent' AND kind NOT IN {REPEATABLE_KINDS};
CREATE INDEX IF NOT EXISTS messages_provider_id ON messages(provider_id);
CREATE INDEX IF NOT EXISTS wa_inbound_order ON wa_inbound(order_id);
"""
_MESSAGE_COLS = {"channel": "TEXT DEFAULT 'mock'", "to_wa": "TEXT", "provider_id": "TEXT", "delivery": "TEXT",
                 "error": "TEXT"}


def connect(path: Path | None = None) -> sqlite3.Connection:
    # The webhook process writes to the same file as the app: WAL + a busy timeout let them share it.
    conn = sqlite3.connect(str(path or config.DB_PATH), check_same_thread=False, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA)
    have = {r["name"] for r in conn.execute("PRAGMA table_info(messages)")}
    for col, decl in _MESSAGE_COLS.items():  # seed.db predates these columns
        if col not in have:
            conn.execute(f"ALTER TABLE messages ADD COLUMN {col} {decl}")
    conn.executescript(_INDEXES)
    conn.commit()
    return conn


def ensure_db(seed: Path) -> None:
    """Copy the committed seed into place. Both the app and webhook.py call this, whichever starts first."""
    if not config.DB_PATH.exists():
        shutil.copy(seed, config.DB_PATH)


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
    """Mock send. Returns False if a message of this kind was already sent for this order (no duplicate sends)."""
    return claim_message(conn, order_id, kind, body, source, channel="mock", to_wa=None) is not None


def claim_message(conn, order_id, kind, body, source, channel, to_wa) -> int | None:
    """Writes the message as sent BEFORE calling the provider, so a double click can't send twice.
    Returns the row id, or None if this order already has a sent message of this kind."""
    try:
        with tx(conn):
            cur = conn.execute(
                "INSERT INTO messages (order_id, kind, body, source, status, attempt, created_at, channel, to_wa,"
                " delivery) VALUES (?,?,?,?, 'sent', 1, ?, ?, ?, ?)",
                (order_id, kind, body, source, now(), channel, to_wa, "mock" if channel == "mock" else "pending"),
            )
        return cur.lastrowid
    except sqlite3.IntegrityError:
        return None


def mark_accepted(conn, msg_id, provider_id) -> None:
    with tx(conn):
        conn.execute("UPDATE messages SET provider_id=?, delivery='accepted' WHERE id=?", (provider_id, msg_id))


def mark_failed(conn, msg_id, error) -> None:
    """The provider refused the send: status 'failed' frees the one-send slot so the seller can retry."""
    with tx(conn):
        conn.execute("UPDATE messages SET status='failed', delivery='failed', error=? WHERE id=?", (error, msg_id))


_DELIVERY_RANK = {"pending": 0, "accepted": 1, "sent": 2, "delivered": 3, "read": 4}


def update_delivery(conn, provider_id, status, error=None) -> bool:
    """Apply a status webhook. Statuses can arrive out of order, so a status only moves forward
    (sent -> delivered -> read); 'failed' always wins. Returns False for an unknown message ID."""
    r = conn.execute("SELECT id, delivery FROM messages WHERE provider_id=?", (provider_id,)).fetchone()
    if r is None:
        return False
    if status == "failed":
        new = "failed"
    elif r["delivery"] == "failed" or _DELIVERY_RANK.get(status, -1) <= _DELIVERY_RANK.get(r["delivery"], -1):
        return True
    else:
        new = status
    with tx(conn):
        conn.execute("UPDATE messages SET delivery=?, error=COALESCE(?, error) WHERE id=?", (new, error, r["id"]))
    return True


def sent_messages(conn, order_id) -> list[dict]:
    rows = conn.execute("SELECT * FROM messages WHERE order_id=? AND status='sent' ORDER BY id", (order_id,))
    return [dict(r) for r in rows]


def failed_messages(conn, order_id) -> list[dict]:
    rows = conn.execute("SELECT * FROM messages WHERE order_id=? AND delivery='failed' ORDER BY id", (order_id,))
    return [dict(r) for r in rows]


def wa_sends_today(conn) -> int:
    r = conn.execute("SELECT COUNT(*) AS n FROM messages WHERE channel='whatsapp' AND created_at >= ?",
                     (dt.datetime.now(dt.timezone.utc).date().isoformat(),)).fetchone()
    return r["n"]


# --- WhatsApp inbound ---------------------------------------------------------

INBOUND_COLS = ["wamid", "from_wa", "profile_name", "order_id", "type", "intent", "text", "button_id",
                "latitude", "longitude", "context_id", "sent_at"]


def order_for_inbound(conn, from_wa, button_order_id=None, context_id=None) -> str | None:
    """Which order a customer message belongs to: the order named in the tapped button, else the
    outbound message it quotes, else the last order we messaged on that number."""
    if button_order_id and conn.execute("SELECT 1 FROM orders WHERE order_id=?", (button_order_id,)).fetchone():
        return button_order_id
    if context_id:
        r = conn.execute("SELECT order_id FROM messages WHERE provider_id=?", (context_id,)).fetchone()
        if r:
            return r["order_id"]
    r = conn.execute("SELECT order_id FROM messages WHERE to_wa=? AND status='sent' AND order_id IS NOT NULL"
                     " ORDER BY id DESC LIMIT 1", (from_wa,)).fetchone()
    return r["order_id"] if r else None


def save_inbound(conn, msg: dict) -> bool:
    """Returns False for a webhook redelivery of a message we already have."""
    try:
        with tx(conn):
            conn.execute(
                f"INSERT INTO wa_inbound ({','.join(INBOUND_COLS)}, received_at) "
                f"VALUES ({','.join('?' * len(INBOUND_COLS))}, ?)",
                [msg.get(c) for c in INBOUND_COLS] + [now()],
            )
        return True
    except sqlite3.IntegrityError:
        return False


def inbound(conn, order_id=None, limit=200) -> list[dict]:
    if order_id is None:
        rows = conn.execute("SELECT * FROM wa_inbound ORDER BY id DESC LIMIT ?", (limit,))
    else:
        rows = conn.execute("SELECT * FROM wa_inbound WHERE order_id=? ORDER BY id", (order_id,))
    return [dict(r) for r in rows]


def last_inbound_id(conn) -> int:
    r = conn.execute("SELECT MAX(id) AS m FROM wa_inbound").fetchone()
    return r["m"] or 0


def last_inbound_at(conn, from_wa) -> str | None:
    r = conn.execute("SELECT MAX(received_at) AS t FROM wa_inbound WHERE from_wa=?", (from_wa,)).fetchone()
    return r["t"]


def customer_status(conn) -> dict[str, str]:
    """Customer's answer per order. The latest confirm/cancel wins over later chatter or a location pin."""
    out: dict[str, str] = {}
    for r in conn.execute("SELECT order_id, intent FROM wa_inbound WHERE order_id IS NOT NULL ORDER BY id"):
        if r["intent"] in ("confirm", "cancel") or out.get(r["order_id"]) not in ("confirm", "cancel"):
            out[r["order_id"]] = r["intent"]
    return out


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
