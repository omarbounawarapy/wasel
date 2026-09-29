"""ScoringConfig = config/scoring.yaml + data/zones.yaml + data/catalog.yaml, loaded once.

config_hash = sha256(config/scoring.yaml + b"\\0" + zones.yaml + b"\\0" + catalog.yaml), shown as 8 hex chars.
"""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

from wasel.paths import ROOT


@dataclass(frozen=True)
class ScoringConfig:
    raw: dict
    zones: dict
    catalog: dict
    templates: dict
    banks: dict                 # phrase banks (rules_v1 flag matching); not hashed
    config_hash: str            # full hex
    root: Path

    @property
    def short_hash(self) -> str:
        return self.config_hash[:8]

    def __getitem__(self, key):
        return self.raw[key]


def _read(p: Path) -> bytes:
    return p.read_bytes()


def load_config(scoring_path: str | Path | None = None, root: Path = ROOT) -> ScoringConfig:
    scoring_path = Path(scoring_path or os.environ.get("SCORING_CONFIG") or root / "config/scoring.yaml")
    if not scoring_path.is_absolute():
        scoring_path = root / scoring_path
    zones_p, catalog_p = root / "data" / "zones.yaml", root / "data" / "catalog.yaml"
    b_s, b_z, b_c = _read(scoring_path), _read(zones_p), _read(catalog_p)
    raw = yaml.safe_load(b_s)
    for key in ("tiers", "confidence", "actions", "reply_adjustments", "lexicons", "prefilter", "roi"):
        if key not in raw:
            raise ValueError(f"config/scoring.yaml: missing section '{key}'")
    if not raw["tiers"]["low_max"] < raw["tiers"]["medium_max"]:
        raise ValueError("config/scoring.yaml: tiers.low_max must be < tiers.medium_max")
    h = hashlib.sha256(b_s + b"\0" + b_z + b"\0" + b_c).hexdigest()
    templates = yaml.safe_load((root / "data" / "templates" / "outbound.yaml").read_text(encoding="utf-8"))
    banks = yaml.safe_load((root / "data" / "phrase_banks.yaml").read_text(encoding="utf-8"))
    return ScoringConfig(raw=raw, zones=yaml.safe_load(b_z), catalog=yaml.safe_load(b_c),
                         templates=templates, banks=banks, config_hash=h, root=root)


@lru_cache(maxsize=1)
def default_config() -> ScoringConfig:
    return load_config()
