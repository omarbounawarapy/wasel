"""create_app(): FastAPI factory. A zero-arg call works (uvicorn --factory).
One container, one process: /api/*, the worker loop, and the static bundle at / (mounted last, if built)."""
from __future__ import annotations

import asyncio
import logging
import threading
from contextlib import asynccontextmanager
from datetime import timedelta
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from wasel.api import models as M
from wasel.api.errors import ApiError, validation_details
from wasel.api.routes import admin, router
from wasel.api.routes_webhook import install_log_redaction, webhook
from wasel.clock import Clock, SystemClock, utc_iso
from wasel.db.cache import SqliteExtractionCache
from wasel.db.conn import connect, create_schema, fresh_db
from wasel.db.purge import purge_sandboxes, reset_all
from wasel.db.seed import load_seed, seed_all, sync_catalog
from wasel.db.snapshot import Snapshotter, restore, store_from_url
from wasel.db.usage import SqliteUsageMeter
from wasel.ids import IdGen, UlidIds
from wasel.llm.client import build_client
from wasel.llm.prompts import PROMPT_VERSION
from wasel.outbound.make_draft import make_draft
from wasel.paths import ROOT
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
# web/public/_headers repeats these for assets served at the edge on Cloudflare; a test keeps the two equal.
SECURITY_HEADERS = {
    "Content-Security-Policy": ("default-src 'self'; script-src 'self' 'unsafe-inline'; img-src 'self' data:; "
                                "style-src 'self' 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'; "
                                "base-uri 'none'"),
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
}


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
                                tokens_per_model_day=s.live_llm_tokens_per_model_day)

    def scorer_for(self, conn):
        """A Scorer using `conn`'s extraction cache, the LLM client and a usage meter on the same connection."""
        return make_scorer(cache=SqliteExtractionCache(conn, PROMPT_VERSION), llm=self.llm,
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
        """One worker step on this thread's connection."""
        conn = self.conn()
        meter = self.meter(conn)
        scorer = make_scorer(cache=SqliteExtractionCache(conn, PROMPT_VERSION), llm=self.llm,
                             meter=meter, config=self.config)
        process_due(conn, now, scorer, self.drafter, ids=self.ids, meter=meter,
                    no_reply_s=self.no_reply_s if self.settings.no_reply_enabled else None,
                    budget_s=TICK_BUDGET_S, order_timeout_s=ORDER_TIMEOUT_S)
        if self.settings.wa_auto_send and not self.settings.is_public:
            from wasel.api.commands import auto_send_due
            auto_send_due(conn, self.ids, now, self.settings, self.sender)

    def purge(self, now) -> int:
        """Delete visitor sandbox rows older than the TTL. Returns the number of orders purged."""
        return purge_sandboxes(self.conn(), now, self.settings.sandbox_ttl_s)

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
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            restored = self.snapshot_store is not None and restore(self.snapshot_store, self.db_path)
            conn = self.conn()
            if not conn.execute("SELECT name FROM sqlite_master WHERE name='orders'").fetchone():
                create_schema(conn)
        conn.execute("UPDATE orders SET rescore_state = CASE WHEN pending_rescore_at IS NOT NULL THEN 'debouncing'"
                     " ELSE 'idle' END")
        added, changed = sync_catalog(conn, self.config.catalog)        # every mode: orders reference the catalog
        if added or changed:
            log.info("catalog: %d added %s, %d changed %s", len(added), added, len(changed), changed)
        empty = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 0
        if mode == "always" or (mode == "if_empty" and empty):
            n = seed_all(conn, self.ids, self.clock.now(), self.scorer_for(conn), self.drafter, self.config.catalog)
            log.info("seeded %d orders", n)
            self.seed_unscored = conn.execute(
                "SELECT COUNT(*) FROM orders o JOIN conversations c USING (conversation_id)"
                " WHERE c.seed_key IS NOT NULL AND o.sandbox_id IS NULL AND o.current_assessment_id IS NULL").fetchone()[0]
            if self.seed_unscored:
                log.error("seed_unscored: %d seeded orders have no assessment (check PROMPT_VERSION and make warm)",
                          self.seed_unscored)
        if restored:
            self.snapshotter.seed_digest(conn)          # what was just restored is already stored

    def snapshot(self, now, *, force: bool = False) -> bool:
        """Save the DB to the snapshot store if one is configured and a save is due (or `force`). Never raises."""
        return self.snapshotter is not None and self.snapshotter.tick(self.conn(), now, force=force)

    def reset(self) -> tuple[int, int]:
        """Delete every order and its related rows, then reseed. Returns (orders deleted, orders reseeded)."""
        conn = self.conn()
        purged = reset_all(conn)
        n = seed_all(conn, self.ids, self.clock.now(), self.scorer_for(conn), self.drafter, self.config.catalog)
        return purged, n

    def health(self, conn) -> M.HealthResponse:
        """Build the /api/health payload from settings, this DB and the worker state."""
        s, now = self.settings, self.clock.now()
        day = now.strftime("%Y-%m-%d")
        calls = conn.execute("SELECT COUNT(*) FROM llm_usage WHERE day=?", (day,)).fetchone()[0]
        recent = conn.execute("SELECT path, created_at FROM risk_assessments ORDER BY created_at DESC LIMIT 1").fetchone()
        five = utc_iso(now - timedelta(minutes=5))
        fb = conn.execute("SELECT path FROM risk_assessments WHERE created_at >= ? AND path IN"
                          " ('fallback_model','fallback_provider','rules') ORDER BY created_at DESC LIMIT 1",
                          (five,)).fetchone()
        pending = conn.execute("SELECT COUNT(*) FROM orders WHERE pending_rescore_at IS NOT NULL").fetchone()[0]
        lm = load_model(str(self.config.root / self.config.raw["model"]["file"]))
        cap = s.daily_cap
        worker_stale = s.worker_enabled and (self.last_tick_at is None or (now - self.last_tick_at).total_seconds() > 10)
        degraded = fb or worker_stale or self.seed_unscored or self.model_problem or (
            self.snapshotter is not None and self.snapshotter.failing)
        return M.HealthResponse(
            status="degraded" if degraded else "ok", mode=s.app_mode, wa_send=s.wa_send_effective,
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
                            if s.is_public else None),
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
        await asyncio.to_thread(state.snapshot, state.clock.now(), force=True)     # last write before the disk goes

    app = FastAPI(title="Wasel", lifespan=lifespan, docs_url=None if settings.is_public else "/docs",
                  redoc_url=None)
    app.state.core = state

    @app.exception_handler(ApiError)
    async def _api_error(_: Request, e: ApiError):
        return JSONResponse(e.body(), status_code=e.status)

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, e: RequestValidationError):
        message, details = validation_details(e.errors())
        err = {"code": "VALIDATION_ERROR", "message": message}
        if details:
            err["details"] = details
        return JSONResponse({"error": err}, status_code=422)

    @app.middleware("http")
    async def _limits_and_headers(request: Request, call_next):
        cl = request.headers.get("content-length")
        if cl and cl.isdigit() and int(cl) > MAX_BODY and request.url.path != "/webhook/whatsapp":   # 1 MiB there
            return JSONResponse({"error": {"code": "PAYLOAD_TOO_LARGE", "message": "body over 64 KB"}}, status_code=413)
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
        app.mount("/", StaticFiles(directory=str(dist), html=True), name="web")
    return app
