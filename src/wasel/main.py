"""create_app(): FastAPI factory. A zero-arg call works (uvicorn --factory).
One container, one process: /api/*, the worker loop, and the static bundle at / (mounted last, if built)."""
from __future__ import annotations

import asyncio
import json
import logging
import threading
from contextlib import asynccontextmanager
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from wasel.api import models as M
from wasel.api.errors import ApiError, validation_details
from wasel.api.routes import admin, router
from wasel.api.routes_webhook import install_log_redaction, webhook
from wasel.clock import Clock, SystemClock, utc_iso
from wasel.db.cache import SqliteExtractionCache
from wasel.db.conn import connect, create_schema, fresh_db, schema_problem, stamp_schema, tx
from wasel.db.purge import purge_history, purge_sandboxes, reset_all
from wasel.db.seed import load_seed, seed_all, seed_cache, sync_catalog
from wasel.db.snapshot import Snapshotter, restore, store_from_url
from wasel.db.usage import SqliteUsageMeter
from wasel.envutil import env
from wasel.ids import IdGen, UlidIds
from wasel.llm.client import ChainClient, build_client
from wasel.llm.prompts import PROMPT_VERSION
from wasel.outbound.make_draft import make_draft
from wasel.paths import ROOT
from wasel.ratelimit import AddressLimiter
from wasel.scoring.config import load_config
from wasel.scoring.model import load_model, model_problem
from wasel.scoring.score_order import make_scorer
from wasel.settings import Settings
from wasel.worker import drain, process_due, run_loop

log = logging.getLogger("cod.main")
MAX_BODY = 64 * 1024
ORDER_TIMEOUT_S = 25.0       # hard limit for scoring one order (above the AI chain's 20 s); past it: needs_review
TICK_BUDGET_S = 3.0          # the worker takes no new order in a tick once this many seconds have passed
# script-src 'unsafe-inline': the Next.js static export (web/dist) boots from inline <script> tags.
# XSS stays covered by React text nodes + the no-dangerouslySetInnerHTML rule.
SECURITY_HEADERS = {
    "Content-Security-Policy": ("default-src 'self'; script-src 'self' 'unsafe-inline'; img-src 'self' data:; "
                                "style-src 'self' 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'; "
                                "base-uri 'none'"),
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
}


def _setup_logging(log_level: str) -> None:
    """Configure root logging with a stderr handler.

    The format includes timestamp, level and logger name. Runs once: if handlers already exist, it does nothing.
    This ensures boot messages (`mode=...`, `seeded N orders`) and warnings reach the host log (e.g. Render logs).

    Args:
        log_level: Root logger level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    if logging.getLogger().handlers:    # already configured: nothing to do (tests may call create_app twice)
        return
    level = getattr(logging, log_level.upper(), logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s", "%Y-%m-%d %H:%M:%S")
    handler = logging.StreamHandler()
    handler.setFormatter(fmt)
    handler.setLevel(level)
    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler)


class AppState:
    """Process-wide application state, held at `app.state.core`: settings, clock, id generator, LLM client and scoring
    config, plus the worker's bookkeeping (last tick, purge and webhook times).

    Database connections are per thread. Created by create_app.
    """

    def __init__(self, settings: Settings, clock: Clock, ids: IdGen, llm):
        self.settings, self.clock, self.ids, self.llm = settings, clock, ids, llm
        self.config = load_config(settings.scoring_config)
        self.db_path = str(ROOT / settings.db_path) if not Path(settings.db_path).is_absolute() else settings.db_path
        self._local = threading.local()
        self._tick_lock = threading.Lock()
        self.limiter = AddressLimiter()                 # per-client-address limits, public mode
        self._degraded_logged = False                   # so the ok -> degraded transition is logged once
        self.started_at = clock.now()
        self.last_tick_at = None
        self.last_purge_at = None
        self.model_problem: tuple[str, str] | None = None   # (code, reason) from the boot check of the model file
        self.seed_unscored = 0                          # seeded orders without an assessment after the last seeding
        self.last_webhook_at = None                     # last POST with a valid signature
        self.no_reply_s = self.config.raw["timeouts"]["no_reply_s"]["demo" if settings.demo_mode else "prod"]
        self.snapshot_store = store_from_url(settings.snapshot_url)     # set only on hosts with an ephemeral disk
        if self.snapshot_store is not None and settings.seed_mode == "always":
            log.warning("SNAPSHOT_URL ignored: SEED_ON_BOOT resolves to 'always', so the DB is rebuilt at every boot")
            self.snapshot_store = None
        self.snapshotter = Snapshotter(self.snapshot_store, settings.snapshot_interval_s) if self.snapshot_store \
            else None
        self.sender = None                              # only when sending is effective (never public mode)
        if settings.wa_send_effective and settings.wa_phone_number_id:
            from wasel.outbound.whatsapp_send import WhatsAppSender
            self.sender = WhatsAppSender(settings.wa_token, settings.wa_phone_number_id, settings.wa_api_version)

    # one connection per thread (see src/wasel/db/conn.py)
    def conn(self):
        """This thread's database connection, opened on first use."""
        c = getattr(self._local, "conn", None)
        if c is None:
            c = self._local.conn = connect(self.db_path)
        return c

    def meter(self, conn=None):
        """A new usage meter for `conn` (default: this thread's) with the caps from settings."""
        s = self.settings
        return SqliteUsageMeter(conn or self.conn(), daily_cap=s.daily_cap, public=s.is_public,
                                visitor_10min=s.visitor_llm_cap_10min, visitor_day=s.visitor_llm_cap_day,
                                tokens_per_model_day=s.live_llm_tokens_per_model_day,
                                siblings=self.limiter.siblings if s.is_public else None,
                                address_cap=None if s.daily_cap is None else max(1, int(s.daily_cap * s.addr_llm_share)))

    def scorer_for(self, conn):
        """A Scorer using `conn`'s extraction cache, the LLM client and a usage meter on the same connection."""
        return make_scorer(cache=SqliteExtractionCache(conn, PROMPT_VERSION), llm=self.llm,
                           meter=self.meter(conn), config=self.config)

    def seed_scorer(self, conn):
        """The scorer for the demo seed: an empty LLM chain, so no provider is called at boot whatever keys are set. The
        committed samples come from the extraction cache; the answered samples take the rules path."""
        return make_scorer(cache=SqliteExtractionCache(conn, PROMPT_VERSION), llm=ChainClient([], deadline_s=20.0),
                           meter=self.meter(conn), config=self.config)

    @property
    def draft_llm(self):
        """rewrite + judge runs only with DRAFT_LLM=true and a provider configured; else static templates."""
        return self.llm if self.settings.draft_llm and getattr(self.llm, "steps", None) else None

    def drafter(self, req):
        """Draft a message with make_draft. LLM rewrite and judge are used only when draft_llm is enabled; otherwise
        static templates.
        """
        return make_draft(req, llm=self.draft_llm, meter=self.meter() if self.draft_llm else None,
                          config=self.config)

    def tick(self, now) -> None:
        """One worker step on this thread's connection. `wait_for_tick` blocks until a running one has finished."""
        with self._tick_lock:
            self._tick(now)

    def wait_for_tick(self) -> None:
        """Return once no tick is running. The loop task can be cancelled while its tick thread is still scoring."""
        with self._tick_lock:
            pass

    def _tick(self, now) -> None:
        conn = self.conn()
        meter = self.meter(conn)
        scorer = make_scorer(cache=SqliteExtractionCache(conn, PROMPT_VERSION), llm=self.llm,
                             meter=meter, config=self.config)
        process_due(conn, now, scorer, self.drafter, ids=self.ids, meter=meter,
                    no_reply_s=self.no_reply_s if self.settings.no_reply_enabled else None,
                    budget_s=TICK_BUDGET_S, order_timeout_s=ORDER_TIMEOUT_S)
        if self.settings.wa_auto_send and not self.settings.is_public:
            from wasel.api.commands import auto_send_due
            auto_send_due(conn, self.ids, now, self.settings, self.sender, on_sent=self.flush)

    def purge(self, now) -> int:
        """Delete visitor sandbox rows older than the TTL. Returns the number of orders purged."""
        return purge_sandboxes(self.conn(), now, self.settings.sandbox_ttl_s)

    def purge_history(self, now) -> dict[str, int]:
        """Apply the retention days to events, llm_usage and extraction_runs (any mode)."""
        s = self.settings
        return purge_history(self.conn(), now, events_days=s.retention_events_days,
                             usage_days=s.retention_llm_usage_days, runs_days=s.retention_extraction_runs_days)

    def drain(self, conn=None, order_id: str | None = None):
        """Score everything that is due now (or only `order_id`), repeatedly, until nothing is left. Returns the
        number of orders scored."""
        conn = conn or self.conn()
        return drain(conn, self.clock.now(), self.scorer_for(conn), self.drafter, ids=self.ids,
                     only_order_id=order_id, order_timeout_s=ORDER_TIMEOUT_S)

    def boot(self) -> None:
        """Prepare the database at startup.

        With seed mode 'always' the DB is rebuilt from schema.sql and reseeded; otherwise the schema is created if
        missing. Rescore states left over from a previous run are reset ('debouncing' if a rescore is pending, else
        'idle'). Loads the product catalog every time, in every seed mode.
        Seeds the demo orders when the mode is 'always', or 'if_empty' and there are no orders.
        """
        self.model_problem = model_problem(str(self.config.root / self.config.raw["model"]["file"]))
        if self.model_problem:
            log.error("%s: %s", *self.model_problem)
            if self.model_problem[0] == "model_mismatch" and not self.settings.is_public:
                raise RuntimeError(f"refusing to start: {self.model_problem[1]}")
        mode = self.settings.seed_mode
        restored = False
        if mode == "always":
            conn = fresh_db(self.db_path)
            self._local.conn = conn
        else:
            Path(self.db_path).parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            restored = self.snapshot_store is not None and restore(self.snapshot_store, self.db_path)
            conn = self.conn()
            if not conn.execute("SELECT name FROM sqlite_master WHERE name='orders'").fetchone():
                create_schema(conn)
        self.check_schema(conn)
        self.migrate_cache_owner(conn)
        self.migrate_send_claim(conn)
        stamp_schema(conn)                              # adopts an unversioned database once; no-op when current
        self.rearm_interrupted(conn)
        conn.execute("UPDATE orders SET rescore_state = CASE WHEN pending_rescore_at IS NOT NULL THEN 'debouncing'"
                     " ELSE 'idle' END")
        added, changed = sync_catalog(conn, self.config.catalog)        # every mode: orders reference the catalog
        if added or changed:
            log.info("catalog: %d added %s, %d changed %s", len(added), added, len(changed), changed)
        empty = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 0
        if mode == "always" or (mode == "if_empty" and empty):
            n = seed_all(conn, self.ids, self.clock.now(), self.seed_scorer(conn), self.drafter, self.config.catalog)
            log.info("seeded %d orders", n)
            self.seed_unscored = conn.execute(
                "SELECT COUNT(*) FROM orders o JOIN conversations c USING (conversation_id)"
                " WHERE c.seed_key IS NOT NULL AND o.sandbox_id IS NULL AND o.current_assessment_id IS NULL").fetchone()[0]
            if self.seed_unscored:
                log.error("seed_unscored: %d seeded orders have no assessment (check PROMPT_VERSION and make warm)",
                          self.seed_unscored)
        if restored:
            self.snapshotter.seed_digest(conn)          # what was just restored is already stored

    def check_schema(self, conn) -> None:
        """Refuse to start on a database that another schema version made (user_version is neither 0 nor current)."""
        problem = schema_problem(conn.execute("PRAGMA user_version").fetchone()[0])
        if problem:
            raise RuntimeError(f"refusing to start: {problem}")

    def migrate_cache_owner(self, conn) -> None:
        """Add extraction_cache.sandbox_id to a database made before it existed.

        The old rows cannot be told apart from rows made from a visitor's text, so they are dropped and the committed
        seed cache is loaded again. It is only a cache: the next scoring of the same text calls the model once more.
        """
        if any(r["name"] == "sandbox_id" for r in conn.execute("PRAGMA table_info(extraction_cache)")):
            return
        with tx(conn):
            conn.execute("ALTER TABLE extraction_cache ADD COLUMN sandbox_id TEXT")
            conn.execute("DELETE FROM extraction_cache")
        seed_cache(conn, self.clock.now())
        log.warning("extraction_cache had no sandbox_id column: old rows dropped, seed cache reloaded")

    def migrate_send_claim(self, conn) -> None:
        """Add outbound_drafts.sending_at to a database made before send claims existed. Existing drafts are kept:
        a NULL claim is simply free."""
        if any(r["name"] == "sending_at" for r in conn.execute("PRAGMA table_info(outbound_drafts)")):
            return
        with tx(conn):
            conn.execute("ALTER TABLE outbound_drafts ADD COLUMN sending_at TEXT")

    def rearm_interrupted(self, conn) -> int:
        """Queue a rescore for every open order whose last scoring did not finish, and return how many.

        That is an order a stop left in 'scoring' or 'drafting' (the claim clears the pending time, so nothing else
        would score it again), and an order, other than one in 'needs_review', whose newest customer message is newer
        than its current assessment and has no rescore pending.
        """
        newest = ("(SELECT MAX(m.received_at) FROM messages m WHERE m.conversation_id = o.conversation_id"
                  " AND m.direction = 'inbound')")
        with tx(conn):
            cur = conn.execute(
                "UPDATE orders AS o SET pending_rescore_at=?, pending_trigger='customer_reply', updated_at=?"
                " WHERE pending_rescore_at IS NULL AND status NOT IN ('shipped','delivered','refused','cancelled')"
                " AND (rescore_state IN ('scoring','drafting') OR (status <> 'needs_review' AND " + newest + " >"
                " COALESCE((SELECT a.created_at FROM risk_assessments a"
                "           WHERE a.assessment_id = o.current_assessment_id), '')))",
                (utc_iso(self.clock.now()),) * 2)
        if cur.rowcount:
            log.info("re-armed %d interrupted rescores", cur.rowcount)
        return cur.rowcount

    def snapshot(self, now, *, force: bool = False) -> bool:
        """Save the DB to the snapshot store if one is configured and a save is due (or `force`). Never raises."""
        return self.snapshotter is not None and self.snapshotter.tick(self.conn(), now, force=force)

    def flush(self) -> bool:
        """Make the snapshot store current before a boundary operation returns. True when there is no store or it
        now holds this content. Never raises."""
        return self.snapshotter is None or self.snapshotter.flush(self.conn(), self.clock.now())

    def reset(self) -> tuple[int, int]:
        """Delete every order and its related rows, then reseed. Returns (orders deleted, orders reseeded)."""
        conn = self.conn()
        purged = reset_all(conn)
        n = seed_all(conn, self.ids, self.clock.now(), self.seed_scorer(conn), self.drafter, self.config.catalog)
        return purged, n

    def health(self, conn) -> M.HealthResponse:
        """Build the /api/health payload from settings, this DB and the worker state."""
        s, now = self.settings, self.clock.now()
        day = now.strftime("%Y-%m-%d")
        calls = conn.execute("SELECT COUNT(*) FROM llm_usage WHERE day=?", (day,)).fetchone()[0]
        recent = conn.execute("SELECT path, created_at FROM risk_assessments ORDER BY created_at DESC LIMIT 1").fetchone()
        five = utc_iso(now - timedelta(minutes=5))
        # sample conversations (seed_key) are not traffic: their rules scores at boot do not mean the AI is down
        fb = conn.execute("SELECT a.path FROM risk_assessments a JOIN orders o ON o.order_id = a.order_id"
                          " JOIN conversations c ON c.conversation_id = o.conversation_id"
                          " WHERE a.created_at >= ? AND c.seed_key IS NULL AND a.path IN"
                          " ('fallback_model','fallback_provider','rules') ORDER BY a.created_at DESC LIMIT 1",
                          (five,)).fetchone()
        pending = conn.execute("SELECT COUNT(*) FROM orders WHERE pending_rescore_at IS NOT NULL").fetchone()[0]
        # where the Groq steps run: only a self-hosted GROQ_BASE_URL can carry a serving label, so the label is never
        # shown for the hosted Groq API
        base_url = env("GROQ_BASE_URL")
        serving_host = urlparse(base_url).hostname if base_url else None
        serving_label = env("LLM_SERVING_LABEL") if serving_host else None
        lm = load_model(str(self.config.root / self.config.raw["model"]["file"]))
        cap = s.daily_cap
        worker_stale = s.worker_enabled and (self.last_tick_at is None or (now - self.last_tick_at).total_seconds() > 10)
        sn = self.snapshotter
        reasons = [r for r, on in (("llm_fallback", fb), ("worker_stale", worker_stale),
                                   ("snapshot_failing", sn is not None and sn.failing),
                                   ("seed_unscored", self.seed_unscored),
                                   (self.model_problem[0] if self.model_problem else "", self.model_problem)) if on]
        if reasons and not self._degraded_logged:
            log.warning("health ok -> degraded: %s", ", ".join(reasons))
        self._degraded_logged = bool(reasons)
        return M.HealthResponse(
            status="degraded" if reasons else "ok",
            degraded_reasons=reasons,
            snapshot=M.HealthSnapshot(
                enabled=sn is not None, last_saved_at=utc_iso(sn.last_saved_at) if sn and sn.last_saved_at else None,
                failures=sn.failures if sn else 0, last_error=sn.last_error if sn else None,
                size_bytes=sn.size_bytes if sn else None), mode=s.app_mode, wa_send=s.wa_send_effective,
            webhook="enabled" if s.webhook_mounted else "disabled", db=True, demo_mode=s.demo_mode,
            build=M.HealthBuild(git_sha=s.git_sha, started_at=utc_iso(self.started_at)),
            config=M.HealthConfig(config_hash=self.config.short_hash, prompt_version=PROMPT_VERSION,
                                  classifier_version=lm.classifier_version if lm else "none",
                                  seed_version=load_seed()["version"]),
            llm=M.HealthLLM(llm_mode=s.llm_mode, chain_extract=getattr(self.llm, "chain_names", []),
                            chain_judge=getattr(self.draft_llm, "chain_names", []),
                            primary=getattr(self.llm, "primary", "rules"), fallback_active=fb is not None,
                            fallback_reason=f"recent path {fb['path']}" if fb else None,
                            last_path=recent["path"] if recent else None,
                            last_call_at=None, remaining_tokens=None, live_calls_today=calls, live_call_cap=cap,
                            cap_reached=cap is not None and calls >= cap,
                            visitor_cap={"per_10min": s.visitor_llm_cap_10min, "per_day": s.visitor_llm_cap_day}
                            if s.is_public else None,
                            serving_label=serving_label, serving_host=serving_host),
            whatsapp=M.HealthWhatsApp(
                last_webhook_at=utc_iso(self.last_webhook_at) if self.last_webhook_at else None),
            worker=M.HealthWorker(last_tick_at=utc_iso(self.last_tick_at) if self.last_tick_at else None,
                                  pending=pending,
                                  last_purge_at=utc_iso(self.last_purge_at) if self.last_purge_at else None),
            wa_token_present=bool(s.wa_token),
            real_rows=conn.execute("SELECT COUNT(*) FROM conversations WHERE channel='whatsapp'").fetchone()[0],
            sandbox_orders=conn.execute("SELECT COUNT(*) FROM orders WHERE sandbox_id IS NOT NULL").fetchone()[0],
            wa_auto_send=s.wa_auto_send and not s.is_public,
            degraded_reason=self.model_problem[0] if self.model_problem else "seed_unscored" if self.seed_unscored else None,
            degraded_detail=self.model_problem[1] if self.model_problem else None)


class BodyLimit:
    """Refuse a request body over MAX_BODY with the 413 envelope, whether or not it declares its length.

    A declared Content-Length is checked up front. Without one (chunked transfer) the bytes are counted as the
    handler reads them, and the response is replaced by the 413 as soon as the limit is passed, so the rest of
    the body is never read. The webhook has its own 1 MiB limit.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["path"] == "/webhook/whatsapp":
            return await self.app(scope, receive, send)
        declared = dict(scope["headers"]).get(b"content-length", b"")
        if declared.isdigit() and int(declared) > MAX_BODY:
            return await self._refuse(send)
        seen, over = 0, False

        async def counted():
            nonlocal seen, over
            msg = await receive()
            if msg["type"] == "http.request":
                seen += len(msg.get("body", b""))
                if seen > MAX_BODY:
                    over = True
                    return {"type": "http.request", "body": b"", "more_body": False}    # stop reading
            return msg

        async def guarded(msg):
            if over:
                if msg["type"] == "http.response.start":
                    await self._refuse(send)
                return                                  # drop whatever the handler made of the truncated body
            await send(msg)

        await self.app(scope, counted, guarded)

    @staticmethod
    async def _refuse(send) -> None:
        body = json.dumps({"error": {"code": "PAYLOAD_TOO_LARGE", "message": "body over 64 KB"}}).encode()
        headers = [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())]
        headers += [(k.lower().encode(), v.encode()) for k, v in SECURITY_HEADERS.items()]
        await send({"type": "http.response.start", "status": 413, "headers": headers})
        await send({"type": "http.response.body", "body": body})


class HostOriginGuard:
    """Outside public mode, refuse a request for a Host that is not allowed (400) and a state-changing request from
    another origin (403 BAD_ORIGIN).

    The first stops DNS rebinding: a page whose name resolves to 127.0.0.1 would otherwise be same-origin to the
    API. The second stops a cross-site form post to routes that take no body. A request without an Origin header
    (curl, the dashboard server, Meta's webhook) is not affected by the second check.
    """

    def __init__(self, app, allowed_hosts: list[str], frontend_origin: str):
        self.app = app
        self.hosts = {h.strip().lower() for h in allowed_hosts if h.strip()}
        self.frontend = frontend_origin.rstrip("/").lower()

    @staticmethod
    def _hostname(value: str) -> str:
        value = value.strip().lower()
        if value.startswith("["):                       # IPv6 literal: keep the brackets, drop the port
            return value[:value.find("]") + 1] if "]" in value else value
        return value.split(":")[0]

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = {k.decode("latin-1"): v.decode("latin-1") for k, v in scope["headers"]}
        host = headers.get("host", "")
        if self._hostname(host) not in self.hosts:
            return await self._reply(send, 400, "BAD_HOST", "host not allowed (see ALLOWED_HOSTS)")
        origin = headers.get("origin")
        if origin and scope["method"] in ("POST", "PUT", "PATCH", "DELETE"):
            o = origin.rstrip("/").lower()
            if o != self.frontend and o.split("://", 1)[-1] != host.lower():
                return await self._reply(send, 403, "BAD_ORIGIN", "cross-origin request refused")
        await self.app(scope, receive, send)

    @staticmethod
    async def _reply(send, status: int, code: str, message: str) -> None:
        body = json.dumps({"error": {"code": code, "message": message}}).encode()
        headers = [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())]
        headers += [(k.lower().encode(), v.encode()) for k, v in SECURITY_HEADERS.items()]
        await send({"type": "http.response.start", "status": status, "headers": headers})
        await send({"type": "http.response.body", "body": body})


def create_app(settings: Settings | None = None, *, clock: Clock | None = None, llm=None,
               ids: IdGen | None = None, worker_enabled: bool | None = None) -> FastAPI:
    """Build the FastAPI app. `create_app()` with no arguments works as a uvicorn factory.

    `settings` default to the environment. `llm` defaults to build_client for `settings.llm_mode`. `worker_enabled`
    overrides `settings.worker_enabled`; when on, the lifespan starts the background worker loop after boot().
    Requests declaring a body over 64 KB are refused (1 MiB for the webhook) and every response gets security headers.
    Mode-dependent: /docs is off in public mode, CORS only in dev, the admin router mounts only with a long enough
    admin token, the webhook router only when `settings.webhook_mounted`. The web bundle in web/dist, if built, is
    served at /.
    """
    settings = settings or Settings()
    if llm is None:
        llm = build_client(settings.llm_mode)
    state = AppState(settings, clock or SystemClock(), ids or UlidIds(), llm)
    run_worker = settings.worker_enabled if worker_enabled is None else worker_enabled

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        state.boot()
        task = asyncio.create_task(run_loop(state)) if run_worker else None
        yield
        if task:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
            await asyncio.to_thread(state.wait_for_tick)        # the cancelled tick's thread may still be writing
        await asyncio.to_thread(state.snapshot, state.clock.now(), force=True)     # last write before the disk goes

    app = FastAPI(title="Wasel", lifespan=lifespan, docs_url=None if settings.is_public else "/docs",
                  redoc_url=None)
    app.state.core = state

    @app.exception_handler(ApiError)
    async def _api_error(_: Request, e: ApiError):
        return JSONResponse(e.body(), status_code=e.status, headers=e.headers)

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(request: Request, e: StarletteHTTPException):
        if not request.url.path.startswith("/api"):
            return await http_exception_handler(request, e)
        if e.status_code == 404:                        # the web mount answers before the router can say 405
            from starlette.routing import Match, Mount
            routes = [r for r in request.app.router.routes if not isinstance(r, Mount)]
            allow = [m for m in ("GET", "POST", "PUT", "PATCH", "DELETE") if any(
                r.matches({"type": "http", "path": request.url.path, "method": m})[0] == Match.FULL for r in routes)]
            if allow:
                e = StarletteHTTPException(405, headers={"Allow": ", ".join(allow)})
        code = {404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED"}.get(e.status_code, "HTTP_ERROR")
        msg = {404: "no such endpoint", 405: "method not allowed for this endpoint"}.get(e.status_code, str(e.detail))
        return JSONResponse({"error": {"code": code, "message": msg}}, status_code=e.status_code,
                            headers=getattr(e, "headers", None))

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, e: RequestValidationError):
        message, details = validation_details(e.errors())
        err = {"code": "VALIDATION_ERROR", "message": message}
        if details:
            err["details"] = details
        return JSONResponse({"error": err}, status_code=422)

    app.add_middleware(BodyLimit)
    if not settings.is_public:
        app.add_middleware(HostOriginGuard, allowed_hosts=settings.allowed_hosts.split(","),
                           frontend_origin=settings.frontend_origin)

    _setup_logging(settings.log_level)

    @app.middleware("http")
    async def _security_headers(request: Request, call_next):
        resp = await call_next(request)
        for k, v in SECURITY_HEADERS.items():
            resp.headers[k] = v
        return resp

    if settings.app_mode == "dev":
        from fastapi.middleware.cors import CORSMiddleware
        app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_origin], allow_methods=["*"],
                           allow_headers=["*"])
    app.include_router(router)
    if settings.admin_mounted:
        app.include_router(admin)
    if settings.webhook_mounted:                        # fail closed; public mode never mounts it
        app.include_router(webhook)
        install_log_redaction()
    log.info("mode=%s webhook=%s wa_send=%s", settings.app_mode, "enabled" if settings.webhook_mounted else "disabled",
             settings.wa_send_effective)
    dist = ROOT / "web" / "dist"
    if dist.exists():
        app.mount("/", WebBundle(directory=str(dist), html=True), name="web")
    app.openapi = lambda: _openapi(app)                 # the error envelope replaces FastAPI's default 422 body
    return app


class WebBundle(StaticFiles):
    """The web UI at `/`. A path under /api that no route matched is an API 404 (JSON), not the UI's 404 page."""

    async def get_response(self, path: str, scope):
        if scope["path"] == "/api" or scope["path"].startswith("/api/"):
            raise StarletteHTTPException(404)
        return await super().get_response(path, scope)


def _openapi(app: FastAPI) -> dict:
    """The OpenAPI document with every 422 pointing at ErrorEnvelope instead of HTTPValidationError."""
    if app.openapi_schema:
        return app.openapi_schema
    from fastapi.openapi.utils import get_openapi
    doc = get_openapi(title=app.title, version=app.version, routes=app.routes, description=app.description)
    ref = {"$ref": "#/components/schemas/ErrorEnvelope"}
    for ops in doc["paths"].values():
        for op in ops.values():
            r = op.get("responses", {})
            if "422" in r:
                r["422"] = {"description": "VALIDATION_ERROR; `details` maps field names to messages",
                            "content": {"application/json": {"schema": ref}}}
    for name in ("HTTPValidationError", "ValidationError"):
        doc.get("components", {}).get("schemas", {}).pop(name, None)
    app.openapi_schema = doc
    return doc
