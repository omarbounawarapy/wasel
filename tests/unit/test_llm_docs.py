"""docs/subsystems/llm.md stays in step with config/llm.yaml."""
import re
import sys
from pathlib import Path

import pytest
import yaml

from wasel.llm.base import CallMeta
from wasel.llm.prompts import registry
from wasel.llm.routes import ADAPTERS, build_steps, parse_endpoints, parse_route
from wasel.llm.settings import LLMSettings

ROOT = Path(__file__).resolve().parents[2]
PAGE = (ROOT / "docs" / "subsystems" / "llm.md").read_text(encoding="utf-8")


@pytest.fixture
def gen():
    sys.path.insert(0, str(ROOT / "scripts" / "dev"))
    try:
        import gen_llm_docs
        yield gen_llm_docs
    finally:
        sys.path.remove(str(ROOT / "scripts" / "dev"))


def test_generated_tables_match_the_config(gen):
    assert gen.current(PAGE) == gen.generated(), "run: python scripts/dev/gen_llm_docs.py"


class Fake:
    def complete_json(self, task, model, user, timeout_s):
        return "{}", CallMeta(provider="groq", model=model, latency_ms=1)


def test_the_add_an_endpoint_guide_runs_as_written(monkeypatch):
    """Step 1 and 2 of the guide, applied to the committed config, plus the variables from step 3."""
    guide = PAGE.split("### Add an endpoint", 1)[1].split("\n### ", 1)[0]
    blocks = re.findall(r"```yaml\n(.*?)```", guide, re.S)
    assert len(blocks) == 2
    endpoint, step = (yaml.safe_load(b) for b in blocks)
    (eid, spec), = endpoint.items()
    (step,) = step
    assert step["endpoint"] == eid

    reg = registry()
    eps = parse_endpoints({**reg["endpoints"], eid: spec})
    route = parse_route("extract", [step, *reg["routes"]["extract"]], eps)

    for k in ("GROQ_BASE_URL", "GROQ_API_KEY", "SELF_HOSTED_API_KEY", "GEMINI_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    for name, value in re.findall(r"`(AMD_B_\w+)=([^`]+)`", guide):
        monkeypatch.setenv(name, value.replace("<token>", "t"))
    built = []
    monkeypatch.setitem(ADAPTERS, "openai-compatible", lambda ep, cfg: built.append(ep) or Fake())
    steps = build_steps(LLMSettings.from_env("live"), eps, route)
    assert [(s.endpoint, s.kind) for s in steps] == [(eid, "primary")]
    assert built[0].base_url == "http://10.0.0.5:8000/v1"
