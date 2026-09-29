"""Repository layout: the one place that knows where the checkout's config/, data/ and models/ live.

The app runs from a checkout (`make serve`, `pip install -e .`), not from an installed wheel.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
