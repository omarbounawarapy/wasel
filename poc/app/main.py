"""create_app(): FastAPI factory (01 §6, 05 §2). A zero-arg call works (uvicorn --factory).
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

from app.api import models as M
from app.api.errors import ApiError
from app.api.routes import admin, router
from app.clock import Clock, SystemClock, utc_iso
from app.db.cache import SqliteExtractionCache
from app.db.conn import connect, create_schema, fresh_db
from app.db.purge import purge_sandboxes, reset_all
from app.db.seed import load_seed, seed_all
from app.db.usage import SqliteUsageMeter
from app.ids import IdGen, UlidIds
from app.llm.client import build_client
from app.outbound.make_draft import make_draft
from app.scoring.config import ROOT, load_config
from app.scoring.model import load_model
from app.scoring.score_order import make_scorer
from app.settings import Settings
from app.worker import drain, process_due, run_loop

log = logging.getLogger("cod.main")
MAX_BODY = 64 * 1024


class AppState:
    def __init__(self, settings: Settings, clock: Clock, ids: IdGen, llm):
        self.settings, self.clock, self.ids, self.llm = settings, clock, ids, llm
        self.config = load_config(settings.scoring_config)
        self.db_path = str(ROOT / settings.db_path) if not Path(settings.db_path).is_absolute() else settings.db_path
        self._local = threading.local()
        self.started_at = clock.now()
        self.last_tick_at = None
        self.last_purge_at = None
        self.no_reply_s = self.config.raw["timeouts"]["no_reply_s"]["demo" if settings.demo_mode else "prod"]

    # one connection per thread (01 §1 conn.py)
    def conn(self):
        c = getattr(self._local, "conn", None)
        if c is None:
            c = self._local.conn = connect(self.db_path)
        return c

    def meter(self, conn=None):
        s = self.settings
        return SqliteUsageMeter(conn or self.conn(), daily_cap=s.daily_cap, public=s.is_public,
                                visitor_10min=s.visitor_llm_cap_10min, visitor_day=s.visitor_llm_cap_day)

    def scorer_for(self, conn):
        return make_scorer(cache=SqliteExtractionCache(conn, self.settings.prompt_version), llm=self.llm,
                           meter=self.meter(conn), config=self.config)

    def drafter(self, req):
        return make_draft(req, llm=None, config=self.config)          # DRAFT_LLM=false: static only (S-3 not built)

    def tick(self, now) -> None:
        """One worker step on this thread's connection (01 §5.3)."""
        conn = self.conn()
        meter = self.meter(conn)
        scorer = make_scorer(cache=SqliteExtractionCache(conn, self.settings.prompt_version), llm=self.llm,
                             meter=meter, config=self.config)
        process_due(conn, now, scorer, self.drafter, ids=self.ids, meter=meter,
                    no_reply_s=self.no_reply_s if self.settings.no_reply_enabled else None)

    def purge(self, now) -> int:
        return purge_sandboxes(self.conn(), now, self.settings.sandbox_ttl_s)

    def drain(self, conn=None):
        conn = conn or self.conn()
        return drain(conn, self.clock.now(), self.scorer_for(conn), self.drafter, ids=self.ids)

    def boot(self) -> None:
        mode = self.settings.seed_mode
        if mode == "always":
            conn = fresh_db(self.db_path)
            self._local.conn = conn
        else:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            conn = self.conn()
            if not conn.execute("SELECT name FROM sqlite_master WHERE name='orders'").fetchone():
                create_schema(conn)
        conn.execute("UPDATE orders SET rescore_state = CASE WHEN pending_rescore_at IS NOT NULL THEN 'debouncing'"
                     " ELSE 'idle' END")
        empty = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 0
        if mode == "always" or (mode == "if_empty" and empty):
            n = seed_all(conn, self.ids, self.clock.now(), self.scorer_for(conn), self.drafter, self.config.catalog)
            log.info("seeded %d orders", n)

    def reset(self) -> tuple[int, int]:
        conn = self.conn()
        purged = reset_all(conn)
        n = seed_all(conn, self.ids, self.clock.now(), self.scorer_for(conn), self.drafter, self.config.catalog)
        return purged, n

    def health(self, conn) -> M.HealthResponse:
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
        return M.HealthResponse(
            status="degraded" if (fb or worker_stale) else "ok", mode=s.app_mode, wa_send=s.wa_send_effective,
            webhook="enabled" if s.webhook_mounted else "disabled", db=True, demo_mode=s.demo_mode,
            build=M.HealthBuild(git_sha=s.git_sha, started_at=utc_iso(self.started_at)),
            config=M.HealthConfig(config_hash=self.config.short_hash, prompt_version=s.prompt_version,
                                  classifier_version=lm.classifier_version if lm else "none",
                                  seed_version=load_seed()["version"]),
            llm=M.HealthLLM(llm_mode=s.llm_mode, chain_extract=getattr(self.llm, "chain_names", []), chain_judge=[],
                            primary=getattr(self.llm, "primary", "rules"), fallback_active=fb is not None,
                            fallback_reason=f"recent path {fb['path']}" if fb else None,
                            last_path=recent["path"] if recent else None,
                            last_call_at=None, remaining_tokens=None, live_calls_today=calls, live_call_cap=cap,
                            cap_reached=cap is not None and calls >= cap,
                            visitor_cap={"per_10min": s.visitor_llm_cap_10min, "per_day": s.visitor_llm_cap_day}
                            if s.is_public else None),
            whatsapp=M.HealthWhatsApp(last_webhook_at=None),
            worker=M.HealthWorker(last_tick_at=utc_iso(self.last_tick_at) if self.last_tick_at else None,
                                  pending=pending,
                                  last_purge_at=utc_iso(self.last_purge_at) if self.last_purge_at else None),
            wa_token_present=bool(s.wa_token),
            real_rows=conn.execute("SELECT COUNT(*) FROM conversations WHERE channel='whatsapp'").fetchone()[0],
            sandbox_orders=conn.execute("SELECT COUNT(*) FROM orders WHERE sandbox_id IS NOT NULL").fetchone()[0])


def create_app(settings: Settings | None = None, *, clock: Clock | None = None, llm=None,
               ids: IdGen | None = None, worker_enabled: bool | None = None) -> FastAPI:
    settings = settings or Settings()
    if settings.is_public and settings.debug_raw:
        log.warning("DEBUG_RAW refused in public mode")
    if llm is None:
        llm = build_client(settings.llm_mode, replay_dirs=[ROOT / "data" / "llm_replay"])
    state = AppState(settings, clock or SystemClock(), ids or UlidIds(), llm)
    run_worker = settings.worker_enabled if worker_enabled is None else worker_enabled

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        state.boot()
        task = asyncio.create_task(run_loop(state)) if run_worker else None
        yield
        if task:
            task.cancel()

    app = FastAPI(title="COD Risk", lifespan=lifespan, docs_url=None if settings.is_public else "/docs",
                  redoc_url=None)
    app.state.core = state

    @app.exception_handler(ApiError)
    async def _api_error(_: Request, e: ApiError):
        return JSONResponse(e.body(), status_code=e.status)

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, e: RequestValidationError):
        details: dict[str, list[str]] = {}
        for err in e.errors():
            details.setdefault(".".join(str(x) for x in err["loc"][1:]) or "body", []).append(err["msg"])
        return JSONResponse({"error": {"code": "VALIDATION_ERROR", "message": "invalid request", "details": details}},
                            status_code=422)

    @app.middleware("http")
    async def _limits_and_headers(request: Request, call_next):
        cl = request.headers.get("content-length")
        if cl and cl.isdigit() and int(cl) > MAX_BODY:
            return JSONResponse({"error": {"code": "PAYLOAD_TOO_LARGE", "message": "body over 64 KB"}}, status_code=413)
        resp = await call_next(request)
        resp.headers["Content-Security-Policy"] = ("default-src 'self'; img-src 'self' data:; style-src 'self' "
                                                   "'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'; "
                                                   "base-uri 'none'")
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["Referrer-Policy"] = "no-referrer"
        return resp

    if settings.app_mode == "dev":
        from fastapi.middleware.cors import CORSMiddleware
        app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_origin], allow_methods=["*"],
                           allow_headers=["*"])
    app.include_router(router)
    if settings.admin_mounted:
        app.include_router(admin)
    dist = ROOT / "web" / "dist"
    if dist.exists():
        app.mount("/", StaticFiles(directory=str(dist), html=True), name="web")
    return app
