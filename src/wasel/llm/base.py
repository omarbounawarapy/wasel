"""Provider-neutral error classes and task/meta types."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


class LLMError(Exception):
    """A failed provider call. `outcome` is the AttemptOutcome recorded for the attempt.

    ChainClient treats every LLMError as a failed attempt and moves on to the next step; it never propagates out of the
    chain.
    """
    outcome = "down"


class RateLimited(LLMError):          # 429
    """HTTP 429. `retry_after_s` is the provider's Retry-After value, or None when it sent none."""
    outcome = "rate_limited"

    def __init__(self, retry_after_s: float | None = None):
        super().__init__(f"rate limited (retry_after={retry_after_s})")
        self.retry_after_s = retry_after_s


class ProviderDown(LLMError):         # 5xx, connection, DNS, 401/403
    """The provider could not be used: 5xx, connection or DNS failure, or a 401/403. Opens the chain's circuit breaker
    for that provider.
    """
    outcome = "down"


class Timeout(LLMError):
    """The call exceeded its per-step timeout."""
    outcome = "timeout"


class SchemaRejected(LLMError):       # 400 on schema/params
    """HTTP 400: the provider refused the request, typically the response schema or parameters."""
    outcome = "schema_rejected"


class ModelGone(LLMError):            # 404 model not found / decommissioned
    """HTTP 404: the model does not exist or was decommissioned. Recorded with outcome 'schema_rejected', since
    AttemptOutcome has no separate value for it.
    """
    outcome = "schema_rejected"       # contract AttemptOutcome has no model_gone; logged in `error`


class Truncated(LLMError):            # finish_reason != "stop" (incl. content_filter)
    """The response ended for a reason other than a normal stop (length limit, content filter)."""
    outcome = "truncated"


class ParseError(LLMError):           # JSON/shape failure after repair
    """The response was not usable JSON of the expected shape, or was empty."""
    outcome = "parse_error"


class InputTooLarge(LLMError):        # per-request cap: refused before any provider call
    """The request exceeded TaskSpec.max_input_chars. Defined for that cap; ChainClient currently enforces the cap
    itself and returns a 'rules' result without raising it.
    """
    outcome = "schema_rejected"


class FixtureMissing(LookupError):
    """NOT an LLMError: an offline test with no fixture fails loudly instead of silently going to rules."""


@dataclass(frozen=True)
class TaskSpec:
    """Everything that defines one LLM role's request: prompts, response schema and limits (built by prompts.task).

    `schema` is the strict JSON schema sent as response_format. `few_shot` holds (user, assistant) example pairs. With
    `cache`, ChainClient keeps an in-process response cache for the task (used for rewrite and judge, not extract).
    """
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
    """Metadata of one successful provider call. Token counts are None when the provider did not report them.

    `source` is 'live' for a real call and 'recorded' or 'hand_crafted' for replayed fixtures.
    """
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
