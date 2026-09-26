"""Tier + order value -> recommended action. A lookup table in config, not a model."""
from . import config


def action_for(tier: str, value_tnd: float) -> str:
    return config.RULES[(tier, value_tnd >= config.HIGH_VALUE_TND)]
