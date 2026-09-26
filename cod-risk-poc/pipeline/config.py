"""Central config. Everything a demo might want to tweak lives here, not in code paths."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv(path: Path) -> None:
    """KEY=value lines from cod-risk-poc/.env, whatever folder the process starts in. A variable already set
    in the shell wins. Tests set COD_NO_DOTENV so a local .env can't switch them to live WhatsApp sends."""
    if os.environ.get("COD_NO_DOTENV") or not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        key, sep, val = line.strip().removeprefix("export ").partition("=")
        key, val = key.strip(), val.strip()
        if sep and key and val and not key.startswith("#"):
            os.environ.setdefault(key, val[1:-1] if len(val) > 1 and val[0] == val[-1] in "\"'" else val)


_load_dotenv(ROOT / ".env")

DATA_CSV = ROOT / "data" / "orders.csv"
DB_PATH = Path(os.environ.get("COD_DB_PATH", ROOT / "app.db"))
MODEL_PATH = ROOT / "model.json"
MODEL_META_PATH = ROOT / "model_meta.json"

# Bump when a prompt changes: invalidates the LLM cache cleanly, old entries stay for rollback.
PROMPT_VERSION = "extract-v1"
DRAFT_PROMPT_VERSION = "draft-v1"
JUDGE_PROMPT_VERSION = "judge-v1"


def secret(name: str) -> str:
    """Environment variable (or .env) first, then Streamlit secrets (Streamlit Cloud). webhook.py and the
    scripts run outside Streamlit, where st.secrets only looks in the current folder, so read our own
    .streamlit/secrets.toml directly as well."""
    val = os.environ.get(name, "")
    if val:
        return val
    try:
        import streamlit as st
        val = str(st.secrets.get(name, ""))
    except Exception:
        val = ""
    toml = ROOT / ".streamlit" / "secrets.toml"
    if val or os.environ.get("COD_NO_DOTENV") or not toml.is_file():
        return val
    try:
        import tomllib
        return str(tomllib.loads(toml.read_text(encoding="utf-8")).get(name, ""))
    except (OSError, ValueError):
        return ""


# LLM provider: "gemini", "groq", or unset (offline heuristic mode).
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "").strip().lower()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
LLM_TIMEOUT_S = 20

# WhatsApp Cloud API (Meta). Unset token or phone number ID = mock mode: nothing leaves the app.
# Meta has no endpoint to poll for inbound messages; webhook.py receives them and writes to the same
# SQLite file, and the app polls that file every WA_POLL_SECONDS.
WA_API_VERSION = os.environ.get("WHATSAPP_API_VERSION", "v25.0")
WA_TIMEOUT_S = 15
WA_POLL_SECONDS = 3
WA_SENDS_PER_DAY = 40  # real WhatsApp sends per day, across all sessions (the hosted URL is public)
WA_WINDOW_HOURS = 24   # free-form messages only within 24 h of the customer's last message

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
