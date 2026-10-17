"""Endpoints and routes from config/llm.yaml, and the builder that turns them into ChainSteps.

An endpoint is one deployment (URL, key, request profile); a route is the ordered steps a role tries. The builder
holds no per-provider branches: adding an endpoint is a yaml entry plus its key variable, and a new protocol is one
entry in ADAPTERS. Values come from LLMSettings.lookup, so this
module never reads the environment itself.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from wasel.llm.settings import LLMConfigError, LLMSettings

PROTOCOLS = {"openai-compatible": "groq", "gemini": "gemini"}   # protocol -> the stored `provider` value
REASONING = {"hosted_groq", "self_hosted"}
ROLE_ROUTES = ("extract", "rewrite", "judge")   # a role without a route walks the extract route
KINDS = ("primary", "fallback_model", "fallback_provider")
_ENDPOINT_KEYS = {"protocol", "provider", "base_url", "base_url_env", "key_env", "reasoning", "model_env",
                  "enabled_env", "enabled_default"}
_STEP_KEYS = {"endpoint", "kind", "model", "timeout_s", "flag_env", "unless_active", "requires_active",
              "requires_env"}


@dataclass(frozen=True)
class EndpointSpec:
    id: str
    protocol: str
    provider: str
    base_url: str | None
    base_url_env: str | None
    key_envs: tuple[str, ...]
    reasoning: str | None
    model_env: str | None
    enabled_env: str | None
    enabled_default: bool


@dataclass(frozen=True)
class StepSpec:
    endpoint: str
    kind: str
    model: str
    timeout_s: float
    flag_env: str | None
    unless_active: tuple[str, ...]    # skip the step when any of these endpoints is active
    requires_env: str | None
    requires_active: tuple[str, ...] = ()   # skip the step unless every one of these endpoints is active


@dataclass(frozen=True)
class ResolvedEndpoint:
    spec: EndpointSpec
    base_url: str | None
    key: str
    model: str | None                 # from model_env, when the endpoint names one


def _unknown(where: str, got: dict, allowed: set[str]) -> None:
    extra = sorted(set(got) - allowed)
    if extra:
        raise LLMConfigError(f"config/llm.yaml {where}: unknown field(s) {extra}")


def parse_endpoints(raw: dict | None) -> dict[str, EndpointSpec]:
    out: dict[str, EndpointSpec] = {}
    for eid, e in (raw or {}).items():
        where = f"endpoints.{eid}"
        if not isinstance(e, dict):
            raise LLMConfigError(f"config/llm.yaml {where}: expected a mapping")
        _unknown(where, e, _ENDPOINT_KEYS)
        proto = e.get("protocol")
        if proto not in PROTOCOLS:
            raise LLMConfigError(f"config/llm.yaml {where}.protocol={proto!r}: expected one of {sorted(PROTOCOLS)}")
        if e.get("reasoning") not in (None, *REASONING):
            raise LLMConfigError(f"config/llm.yaml {where}.reasoning={e['reasoning']!r}: expected one of "
                                 f"{sorted(REASONING)}")
        keys = e.get("key_env") or []
        keys = (keys,) if isinstance(keys, str) else tuple(keys)
        if not keys:
            raise LLMConfigError(f"config/llm.yaml {where}: key_env is required (the variable that holds the key)")
        if proto == "openai-compatible" and not (e.get("base_url") or e.get("base_url_env")):
            raise LLMConfigError(f"config/llm.yaml {where}: openai-compatible needs base_url or base_url_env")
        out[eid] = EndpointSpec(eid, proto, e.get("provider") or PROTOCOLS[proto], e.get("base_url"),
                                e.get("base_url_env"), keys, e.get("reasoning"), e.get("model_env"),
                                e.get("enabled_env"), bool(e.get("enabled_default", True)))
    return out


def _names(raw: str | list | None) -> tuple[str, ...]:
    """One endpoint id or a list of them."""
    return (raw,) if isinstance(raw, str) else tuple(raw or ())


def parse_route(role: str, raw: list | None, endpoints: dict[str, EndpointSpec]) -> list[StepSpec]:
    steps = []
    for i, s in enumerate(raw or []):
        where = f"routes.{role}[{i}]"
        if not isinstance(s, dict):
            raise LLMConfigError(f"config/llm.yaml {where}: expected a mapping")
        _unknown(where, s, _STEP_KEYS)
        unless, needs = (_names(s.get(f)) for f in ("unless_active", "requires_active"))
        for field, ids in (("endpoint", (s.get("endpoint"),) if s.get("endpoint") is not None else ()),
                           ("unless_active", unless), ("requires_active", needs)):
            for eid in ids:
                if eid not in endpoints:
                    raise LLMConfigError(f"config/llm.yaml {where}.{field}={eid!r}: no such endpoint")
        if s.get("endpoint") is None:
            raise LLMConfigError(f"config/llm.yaml {where}: endpoint is required")
        if s.get("kind") not in KINDS:
            raise LLMConfigError(f"config/llm.yaml {where}.kind={s.get('kind')!r}: expected one of {KINDS}")
        try:
            timeout = float(s["timeout_s"])
        except (KeyError, TypeError, ValueError):
            raise LLMConfigError(f"config/llm.yaml {where}.timeout_s: expected a number of seconds") from None
        if timeout <= 0 or not s.get("model"):
            raise LLMConfigError(f"config/llm.yaml {where}: timeout_s must be above 0 and model is required")
        steps.append(StepSpec(s["endpoint"], s["kind"], str(s["model"]), timeout, s.get("flag_env"),
                              unless, s.get("requires_env"), needs))
    return steps


def resolve(spec: EndpointSpec, cfg: LLMSettings) -> ResolvedEndpoint | None:
    """The endpoint with its address, key and model filled in, or None when it is not active in this environment."""
    if spec.enabled_env and not cfg.flag(spec.enabled_env, spec.enabled_default):
        return None
    base = spec.base_url
    if spec.base_url_env:
        base = cfg.lookup(spec.base_url_env)
        if not base:
            return None
    key = next((v for v in (cfg.lookup(k) for k in spec.key_envs) if v), None)
    if not key:
        return None
    model = cfg.lookup(spec.model_env) if spec.model_env else None
    if spec.model_env and not model:
        return None
    return ResolvedEndpoint(spec, base, key, model)


# ---------------------------------------------------------------- adapters, one per protocol
def _openai_compatible(ep: ResolvedEndpoint, cfg: LLMSettings):
    from wasel.llm import groq_backend as gb
    return gb.groq_backend(ep.key, base_url=ep.base_url, reasoning=ep.spec.reasoning)


def _gemini(ep: ResolvedEndpoint, cfg: LLMSettings):
    from wasel.llm.gemini_backend import gemini_backend, load_probe
    return gemini_backend(ep.key, ep.model, load_probe(cfg.probe_file))


ADAPTERS: dict[str, Callable] = {"openai-compatible": _openai_compatible, "gemini": _gemini}


def build_steps(cfg: LLMSettings, endpoints: dict[str, EndpointSpec], route: list[StepSpec]):
    """ChainSteps for `route` in this environment. Inactive endpoints and skipped steps add nothing."""
    from wasel.llm.client import ChainStep
    resolved = {eid: resolve(spec, cfg) for eid, spec in endpoints.items()}
    backends: dict[str, object] = {}
    steps = []
    for s in route:
        ep = resolved[s.endpoint]
        if ep is None:
            continue
        if any(resolved[eid] is not None for eid in s.unless_active):
            continue
        if any(resolved[eid] is None for eid in s.requires_active):
            continue
        if s.requires_env and not cfg.lookup(s.requires_env):
            continue
        if s.flag_env and not cfg.flag(s.flag_env, True):
            continue
        model = {"primary": cfg.primary_model, "fallback": cfg.fallback_model, "endpoint": ep.model}.get(s.model,
                                                                                                        s.model)
        if s.endpoint not in backends:
            backends[s.endpoint] = ADAPTERS[ep.spec.protocol](ep, cfg)
        steps.append(ChainStep(s.kind, ep.spec.provider, model, backends[s.endpoint], s.timeout_s,
                               endpoint=s.endpoint))
    return steps


# ---------------------------------------------------------------- docs generated from the config
def docs_tables(endpoints: dict[str, EndpointSpec], routes: dict[str, list[StepSpec]]) -> str:
    """Markdown for the endpoint and route tables in docs/subsystems/llm.md (a test fails if the page drifts)."""
    def names(*vals: str | None) -> str:
        return ", ".join(f"`{v}`" for v in vals if v) or "none"

    lines = ["| Endpoint | Protocol | Address | Key variable | Reasoning | Active when |", "|---|---|---|---|---|---|"]
    for e in endpoints.values():
        addr = f"`{e.base_url}`" if e.base_url else (f"`{e.base_url_env}`" if e.base_url_env else "built in")
        when = ["its key is set"]
        if e.base_url_env:
            when.append(f"`{e.base_url_env}` is set")
        if e.model_env:
            when.append(f"`{e.model_env}` is set")
        if e.enabled_env:
            when.append(f"`{e.enabled_env}` is true" + ("" if e.enabled_default else " (off by default)"))
        lines.append(f"| `{e.id}` | {e.protocol} | {addr} | {names(*e.key_envs)} | {e.reasoning or 'none'} | "
                     f"{', '.join(when)} |")
    lines += ["", "| Route | Step | Endpoint | Kind | Model | Timeout | Skipped when |", "|---|---|---|---|---|---|---|"]
    for role, steps in routes.items():
        for i, s in enumerate(steps, 1):
            skip = []
            if s.flag_env:
                skip.append(f"`{s.flag_env}` is false")
            if s.unless_active:
                skip.append(" or ".join(f"`{eid}`" for eid in s.unless_active) + " is active")
            if s.requires_active:
                skip.append(" or ".join(f"`{eid}`" for eid in s.requires_active) + " is inactive")
            if s.requires_env:
                skip.append(f"`{s.requires_env}` is unset")
            lines.append(f"| `{role}` | {i} | `{s.endpoint}` | `{s.kind}` | `{s.model}` | {s.timeout_s:g}s | "
                         f"{', '.join(skip) or 'never'} |")
    return "\n".join(lines)
