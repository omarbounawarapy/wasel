"""Runtime settings. Unknown or missing APP_MODE -> public, with a warning.
Secrets come from the host env / .env and are never committed."""
from __future__ import annotations

import logging
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

log = logging.getLogger("cod.settings")


class Settings(BaseSettings):
    """Runtime settings from environment variables and `.env` (names are case-insensitive; unknown keys are ignored).

    An unknown or missing APP_MODE resolves to 'public', the most restrictive mode. Values derived from several
    settings are properties below, so code should use those rather than combining raw values itself.
    """
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    app_mode: Literal["dev", "event", "public"] = "public"
    # secrets. Provider keys (GROQ_API_KEY, GEMINI_API_KEY) are read by wasel.envutil, not here.
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
    snapshot_url: str = ""               # file:// or http(s):// store for the DB on hosts with an ephemeral disk
    snapshot_interval_s: int = 60
    demo_mode: bool = True
    worker_enabled: bool = True
    # WhatsApp non-secret
    wa_phone_number_id: str = ""
    wa_api_version: str = ""
    # LLM
    llm_mode: Literal["live", "replay", "fail_primary", "fail_groq", "fail_all"] = "live"
    draft_llm: bool = False
    # caps and sandbox (daily_cap gives the per-mode default when live_llm_daily_cap is unset)
    live_llm_daily_cap: int | None = None
    live_llm_tokens_per_model_day: int | None = None  # None = public 120000, else no guard
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
    scoring_config: str = "config/scoring.yaml"

    @field_validator("app_mode", mode="before")
    @classmethod
    def _mode(cls, v):
        if v in ("dev", "event", "public"):
            return v
        if v not in (None, ""):
            log.warning("unknown APP_MODE %r -> public", v)
        return "public"

    @field_validator("live_llm_daily_cap", "live_llm_tokens_per_model_day", mode="before")
    @classmethod
    def _cap(cls, v):
        # .env.example ships these two caps empty (= the mode default); without this a copied example crashes
        return None if isinstance(v, str) and not v.strip() else v

    # ---- derived (never read from env directly)
    @property
    def is_public(self) -> bool:
        """True in public mode (visitor sandboxes, read-only samples, no webhook, no sending)."""
        return self.app_mode == "public"

    @property
    def wa_send_effective(self) -> bool:
        """Whether WhatsApp sends can really happen: not public mode, WA_SEND_ENABLED, and a token present."""
        return self.app_mode != "public" and self.wa_send_enabled and bool(self.wa_token)

    @property
    def webhook_mounted(self) -> bool:
        """Whether the WhatsApp webhook is served: not public mode, WEBHOOK_ENABLED, an app secret of at least 16
        characters and a verify token of at least 24.
        """
        return (self.app_mode != "public" and self.webhook_enabled and len(self.wa_app_secret) >= 16
                and len(self.wa_verify_token) >= 24)

    @property
    def admin_mounted(self) -> bool:
        """Whether the admin router is served: the admin token is at least 24 characters."""
        return len(self.admin_token) >= 24

    @property
    def daily_cap(self) -> int | None:
        """Provider calls per UTC day. 0 = no live calls; None = unlimited (dev default)."""
        if self.live_llm_daily_cap is not None:
            return self.live_llm_daily_cap
        return {"public": 80, "event": 300, "dev": None}[self.app_mode]

    @property
    def seed_mode(self) -> str:
        """Resolved seeding: SEED_ON_BOOT when set, else 'always' in public mode and 'if_empty' otherwise."""
        if self.seed_on_boot != "auto":
            return self.seed_on_boot
        return "always" if self.is_public else "if_empty"

    @property
    def no_reply_enabled(self) -> bool:
        """Whether no-reply timeouts fire: everywhere except public mode."""
        return not self.is_public
