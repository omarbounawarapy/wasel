"""Runtime settings. Unknown or missing APP_MODE -> public, with a warning.
Secrets come from the host env / .env and are never committed."""
from __future__ import annotations

import logging
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

log = logging.getLogger("cod.settings")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    app_mode: Literal["dev", "event", "public"] = "public"
    # secrets
    groq_api_key: str = ""
    gemini_api_key: str = ""
    wa_token: str = ""
    wa_app_secret: str = ""
    wa_verify_token: str = ""
    admin_token: str = ""
    # mode and safety
    wa_send_enabled: bool = False
    wa_auto_send: bool = False           # auto_send drafts go out without a click (never in public mode)
    webhook_enabled: bool = False
    seed_on_boot: Literal["auto", "always", "if_empty", "never"] = "auto"
    db_path: str = "var/app.db"
    demo_mode: bool = True
    worker_enabled: bool = True
    debug_raw: bool = False
    # WhatsApp non-secret
    wa_phone_number_id: str = ""
    wa_api_version: str = ""
    # LLM
    llm_mode: Literal["live", "replay", "fail_primary", "fail_groq", "fail_all"] = "live"
    llm_deadline_s: float = 20.0
    prompt_version: str = "extract-v1"
    draft_llm: bool = False
    cascade_enabled: bool = False
    gemini_enabled: bool = False
    # caps and sandbox (R6: public 80/day)
    live_llm_daily_cap: int | None = None
    visitor_llm_cap_10min: int = 6
    visitor_llm_cap_day: int = 20
    sandbox_ttl_s: int = 7200
    sandbox_max_orders: int = 15
    sandbox_global_max: int = 500
    purge_interval_s: int = 600
    reply_limit: int = 5
    # runtime
    git_sha: str = "dev"
    frontend_origin: str = "http://localhost:5173"
    tz_display: str = "Africa/Tunis"
    scoring_config: str = "scoring.yaml"

    @field_validator("app_mode", mode="before")
    @classmethod
    def _mode(cls, v):
        if v in ("dev", "event", "public"):
            return v
        if v not in (None, ""):
            log.warning("unknown APP_MODE %r -> public", v)
        return "public"

    @field_validator("live_llm_daily_cap", mode="before")
    @classmethod
    def _cap(cls, v):
        # .env.example ships `LIVE_LLM_DAILY_CAP=` (empty = the mode default); without this a copied example crashes
        return None if isinstance(v, str) and not v.strip() else v

    # ---- derived (never read from env directly)
    @property
    def is_public(self) -> bool:
        return self.app_mode == "public"

    @property
    def wa_send_effective(self) -> bool:
        return self.app_mode != "public" and self.wa_send_enabled and bool(self.wa_token)

    @property
    def webhook_mounted(self) -> bool:
        return (self.app_mode != "public" and self.webhook_enabled and len(self.wa_app_secret) >= 16
                and len(self.wa_verify_token) >= 24)

    @property
    def admin_mounted(self) -> bool:
        return len(self.admin_token) >= 24

    @property
    def daily_cap(self) -> int | None:
        """Provider calls per UTC day. 0 = no live calls; None = unlimited (dev default)."""
        if self.live_llm_daily_cap is not None:
            return self.live_llm_daily_cap
        return {"public": 80, "event": 300, "dev": None}[self.app_mode]

    @property
    def seed_mode(self) -> str:
        if self.seed_on_boot != "auto":
            return self.seed_on_boot
        return "always" if self.is_public else "if_empty"

    @property
    def no_reply_enabled(self) -> bool:
        return not self.is_public
