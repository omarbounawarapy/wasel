"""Dashboard tests import dashboard/api_client.py the same way `streamlit run dashboard/app.py` does (as a top-level
module), so the test's OVERRIDE and the app's client are the same object."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "dashboard"))
