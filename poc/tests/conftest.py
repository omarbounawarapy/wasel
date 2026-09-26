import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline import db  # noqa: E402
from pipeline.llm import LLMError  # noqa: E402


class FakeClient:
    """Stands in for Gemini/Groq. `script` is a list of str responses or exceptions, consumed in order."""
    model = "fake-model"

    def __init__(self, script):
        self.script = list(script)
        self.calls = []

    def complete_json(self, system, user, temperature=0.0):
        self.calls.append((system, user))
        if not self.script:
            raise LLMError("script exhausted")
        nxt = self.script.pop(0)
        if isinstance(nxt, Exception):
            raise nxt
        return nxt if isinstance(nxt, str) else json.dumps(nxt)


@pytest.fixture
def conn(tmp_path):
    c = db.connect(tmp_path / "test.db")
    yield c
    c.close()


@pytest.fixture
def order():
    return dict(order_id="T-1", created_at="2026-09-01T21:30", governorate="Kasserine", zone_tier="remote",
                address_text="Kasserine, ki twsel kalamni", note_text="nchouf ken ynasebni",
                product_category="electronics", value_tnd=210.0, item_count=1, channel="facebook",
                is_first_order=True, prior_orders=0, prior_refusals=0)
