"""Endpoints and routes from config/llm.yaml."""
import pytest

from wasel.llm.base import CallMeta
from wasel.llm.prompts import registry
from wasel.llm.routes import ADAPTERS, build_steps, parse_endpoints, parse_route
from wasel.llm.settings import LLMConfigError, LLMSettings

NAMES = ("GROQ_BASE_URL", "GROQ_API_KEY", "SELF_HOSTED_API_KEY", "GEMINI_API_KEY", "GEMINI_MODEL", "GEMINI_ENABLED",
         "GROQ_FALLBACK_ENABLED", "AMD2_KEY", "AMD2_URL", "AMD2_ENABLED")


@pytest.fixture
def clean(monkeypatch):
    for k in NAMES:
        monkeypatch.delenv(k, raising=False)
    return monkeypatch


class Fake:
    def __init__(self, ep):
        self.ep = ep

    def complete_json(self, task, model, user, timeout_s):
        return "{}", CallMeta(provider="groq", model=model, latency_ms=1)


def test_the_committed_config_parses_and_has_an_extract_route():
    reg = registry()
    eps = parse_endpoints(reg["endpoints"])
    route = parse_route("extract", reg["routes"]["extract"], eps)
    assert set(eps) == {"groq", "self-hosted", "gemini"}
    assert eps["self-hosted"].reasoning == "self_hosted" and eps["groq"].reasoning == "hosted_groq"
    assert [s.kind for s in route][:2] == ["primary", "fallback_model"]


def test_a_new_endpoint_is_config_only(clean, monkeypatch):
    """A second host is an endpoints entry, a route step and its key variable: no code, no schema."""
    built = []
    monkeypatch.setitem(ADAPTERS, "openai-compatible", lambda ep, cfg: built.append(ep) or Fake(ep))
    clean.setenv("AMD2_KEY", "k2")
    clean.setenv("AMD2_URL", "http://10.0.0.5:8000/v1")
    eps = parse_endpoints({
        "amd2": {"protocol": "openai-compatible", "base_url_env": "AMD2_URL", "key_env": "AMD2_KEY",
                 "reasoning": "self_hosted"}})
    route = parse_route("extract", [{"endpoint": "amd2", "kind": "primary", "model": "openai/gpt-oss-20b",
                                     "timeout_s": 4}], eps)
    steps = build_steps(LLMSettings.from_env("live"), eps, route)
    assert [(s.kind, s.endpoint, s.provider, s.model, s.timeout_s) for s in steps] == [
        ("primary", "amd2", "groq", "openai/gpt-oss-20b", 4.0)]
    assert built[0].base_url == "http://10.0.0.5:8000/v1" and built[0].key == "k2"


def test_an_endpoint_without_its_key_or_address_adds_no_step(clean):
    eps = parse_endpoints({"amd2": {"protocol": "openai-compatible", "base_url_env": "AMD2_URL",
                                    "key_env": "AMD2_KEY"}})
    route = parse_route("extract", [{"endpoint": "amd2", "kind": "primary", "model": "m", "timeout_s": 4}], eps)
    cfg = LLMSettings.from_env("live")
    assert build_steps(cfg, eps, route) == []
    clean.setenv("AMD2_KEY", "k")
    assert build_steps(LLMSettings.from_env("live"), eps, route) == []      # still no address


def test_a_flag_env_turns_the_endpoint_off(clean):
    clean.setenv("AMD2_KEY", "k")
    clean.setenv("AMD2_ENABLED", "false")
    eps = parse_endpoints({"amd2": {"protocol": "openai-compatible", "base_url": "http://h/v1", "key_env": "AMD2_KEY",
                                    "enabled_env": "AMD2_ENABLED"}})
    route = parse_route("extract", [{"endpoint": "amd2", "kind": "primary", "model": "m", "timeout_s": 4}], eps)
    assert build_steps(LLMSettings.from_env("live"), eps, route) == []


@pytest.mark.parametrize("endpoints,route,needle", [
    ({"a": {"protocol": "soap", "key_env": "K"}}, None, "protocol"),
    ({"a": {"protocol": "openai-compatible", "key_env": "K"}}, None, "base_url"),
    ({"a": {"protocol": "openai-compatible", "base_url": "http://h", "key_env": "K", "reasoning": "x"}}, None,
     "reasoning"),
    ({"a": {"protocol": "openai-compatible", "base_url": "http://h"}}, None, "key_env"),
    ({"a": {"protocol": "openai-compatible", "base_url": "http://h", "key_env": "K", "key": "sk-1"}}, None,
     "unknown field"),
    ({"a": {"protocol": "openai-compatible", "base_url": "http://h", "key_env": "K"}},
     [{"endpoint": "nope", "kind": "primary", "model": "m", "timeout_s": 1}], "no such endpoint"),
    ({"a": {"protocol": "openai-compatible", "base_url": "http://h", "key_env": "K"}},
     [{"endpoint": "a", "kind": "sideways", "model": "m", "timeout_s": 1}], "kind"),
    ({"a": {"protocol": "openai-compatible", "base_url": "http://h", "key_env": "K"}},
     [{"endpoint": "a", "kind": "primary", "model": "m", "timeout_s": 0}], "timeout_s"),
])
def test_bad_config_fails_with_the_field_named(endpoints, route, needle):
    with pytest.raises(LLMConfigError, match=needle):
        eps = parse_endpoints(endpoints)
        parse_route("extract", route, eps)


def _client_with_routes(monkeypatch, routes):
    """build_client('live') over the committed endpoints and the given routes, with fake adapters."""
    from wasel.llm import prompts
    from wasel.llm.client import build_client
    reg = dict(registry())
    reg["routes"] = routes
    monkeypatch.setattr(prompts, "registry", lambda: reg)
    monkeypatch.setitem(ADAPTERS, "openai-compatible", lambda ep, cfg: Fake(ep))
    return build_client("live", replay_dirs=[])


def test_a_role_without_a_route_walks_the_extract_route(clean):
    clean.setenv("GROQ_API_KEY", "k")
    from wasel.llm.client import build_client
    c = build_client("live", replay_dirs=[])
    assert c.steps_for("judge") is c.steps and c.chain_names_for("rewrite") == c.chain_names


def test_a_role_route_can_point_at_another_endpoint_in_config_only(clean):
    clean.setenv("GROQ_API_KEY", "k")
    clean.setenv("GROQ_BASE_URL", "http://10.0.0.5:8000/v1")
    clean.setenv("SELF_HOSTED_API_KEY", "t")
    reg_routes = registry()["routes"]
    c = _client_with_routes(clean, {
        **reg_routes,
        "judge": [{"endpoint": "groq", "kind": "primary", "model": "openai/gpt-oss-20b", "timeout_s": 7}]})
    assert c.chain_names_for("judge") == ["groq:openai/gpt-oss-20b"]
    assert c.chain_names[0].startswith("self-hosted:")          # extract is unchanged
    assert c.chain_names_for("rewrite") == c.chain_names        # no rewrite route: inherits extract


def test_an_unknown_route_role_is_a_config_error(clean):
    with pytest.raises(LLMConfigError, match="unknown role"):
        _client_with_routes(clean, {"judje": []})


def test_the_judge_route_is_the_one_that_runs(clean):
    """ChainClient._run walks the role's own steps, with the shared breaker keyed by endpoint."""
    from datetime import UTC, datetime

    from wasel.llm.base import TaskSpec
    from wasel.llm.client import ChainClient, ChainStep
    seen = []

    class Rec:
        def __init__(self, name):
            self.name = name

        def complete_json(self, task, model, user, timeout_s):
            seen.append(self.name)
            return "{}", CallMeta(provider="groq", model=model, latency_ms=1)

    c = ChainClient([ChainStep("primary", "groq", "m", Rec("extract"), 5, endpoint="a")],
                    role_steps={"judge": [ChainStep("primary", "groq", "m", Rec("judge"), 5, endpoint="b")]})
    task = TaskSpec(name="judge", schema_name="s", schema={}, system_prompt="", few_shot=(), prompt_version="v",
                    max_output_tokens=10, temperature=0.0, max_input_chars=100, cache=False)
    now = datetime(2026, 1, 1, tzinfo=UTC)
    for role in ("extract", "judge"):
        c.extract(task, "x", parse=lambda r: r, meter=None, sandbox_id=None, now=now, role=role)
    assert seen == ["extract", "judge"]
