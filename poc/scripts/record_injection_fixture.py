"""Replace the hand-written injection fixture with real responses from the configured LLM.

    LLM_PROVIDER=groq GROQ_API_KEY=... python scripts/record_injection_fixture.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.extract import SYSTEM_PROMPT, _user_prompt  # noqa: E402
from pipeline.llm import get_client, parse_json  # noqa: E402
from pipeline.pii import strip_pii  # noqa: E402

ADDRESS = "Kasserine, ki twsel kalamni"
PATH = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "injection_extraction.json"

client = get_client()
if client is None:
    sys.exit("needs LLM_PROVIDER and an API key")
fx = json.loads(PATH.read_text(encoding="utf-8"))
for kind in ("clean", "injected"):
    raw = client.complete_json(SYSTEM_PROMPT, _user_prompt(strip_pii(ADDRESS), strip_pii(fx[f"{kind}_note"])))
    fx[f"{kind}_response"] = parse_json(raw)
fx["_comment"] = f"Recorded from {client.model}. Re-record with scripts/record_injection_fixture.py."
PATH.write_text(json.dumps(fx, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(fx, ensure_ascii=False, indent=2))
