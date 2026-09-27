"""Provider-neutral error classes and task/meta types (02 §6)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


class LLMError(Exception):
    outcome = "down"


class RateLimited(LLMError):          # 429
    outcome = "rate_limited"

    def __init__(self, retry_after_s: float | None = None):
        super().__init__(f"rate limited (retry_after={retry_after_s})")
        self.retry_after_s = retry_after_s


class ProviderDown(LLMError):         # 5xx, connection, DNS, 401/403
    outcome = "down"


class Timeout(LLMError):
    outcome = "timeout"


class SchemaRejected(LLMError):       # 400 on schema/params
    outcome = "schema_rejected"


class ModelGone(LLMError):            # 404 model not found / decommissioned
    outcome = "schema_rejected"       # contract AttemptOutcome has no model_gone (01 §2); logged in `error`


class Truncated(LLMError):            # finish_reason != "stop" (incl. content_filter)
    outcome = "truncated"


class ParseError(LLMError):           # JSON/shape failure after repair
    outcome = "parse_error"


class InputTooLarge(LLMError):        # per-request cap: refused before any provider call
    outcome = "schema_rejected"


class FixtureMissing(LookupError):
    """NOT an LLMError: an offline test with no fixture fails loudly instead of silently going to rules."""


@dataclass(frozen=True)
class TaskSpec:
    name: Literal["extract", "rewrite", "judge"]
    schema_name: str
    schema: dict
    system_prompt: str
    few_shot: tuple[tuple[str, str], ...]
    prompt_version: str
    max_output_tokens: int
    temperature: float
    max_input_chars: int | None = None   # per-request cap (config/llm.yaml); over it -> InputTooLarge, no call
    cache: bool = False                  # in-process response cache (rewrite/judge only)


@dataclass(frozen=True)
class CallMeta:
    provider: str
    model: str
    latency_ms: int
    tokens_in: int | None = None
    tokens_cached: int | None = None
    tokens_out: int | None = None
    tokens_reasoning: int | None = None
    finish_reason: str | None = None
    ratelimit_remaining_tokens: int | None = None
    source: Literal["live", "recorded", "hand_crafted"] = "live"
    warnings: tuple[str, ...] = field(default_factory=tuple)
