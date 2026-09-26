"""Central config. Everything a demo might want to tweak lives here, not in code paths."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_CSV = ROOT / "data" / "orders.csv"
DB_PATH = Path(os.environ.get("COD_DB_PATH", ROOT / "app.db"))
MODEL_PATH = ROOT / "model.json"
MODEL_META_PATH = ROOT / "model_meta.json"

# Bump when a prompt changes: invalidates the LLM cache cleanly, old entries stay for rollback.
PROMPT_VERSION = "extract-v1"
DRAFT_PROMPT_VERSION = "draft-v1"
JUDGE_PROMPT_VERSION = "judge-v1"

# LLM provider: "gemini", "groq", or unset (offline heuristic mode).
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "").strip().lower()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
LLM_TIMEOUT_S = 20

# Input limits and live-call caps (protect the free-tier quota on a public URL).
MAX_TEXT_CHARS = 1000
LIVE_CALLS_PER_SESSION = 5
LIVE_CALLS_PER_DAY = 150

# Rule layer. 150 TND is a placeholder; production makes it per-seller.
HIGH_VALUE_TND = 150.0
RULES = {
    ("Low", False): "ship",
    ("Low", True): "ship",
    ("Med", False): "confirm_sms",
    ("Med", True): "confirm_sms_landmark",
    ("High", False): "confirm_sms_landmark",
    ("High", True): "require_prepayment",
}
ACTION_LABELS = {
    "ship": "Ship normally",
    "confirm_sms": "Confirm via SMS",
    "confirm_sms_landmark": "Confirm via SMS + ask for landmark",
    "require_prepayment": "Require prepayment",
}

# Simulated ROI parameters. PLACEHOLDERS, not sourced figures: change them in the sidebar.
DEFAULT_TRIP_COST_TND = 7.0
DEFAULT_INTERVENTION_EFFECT = 0.4  # share of refusals an intervention prevents (assumption)
