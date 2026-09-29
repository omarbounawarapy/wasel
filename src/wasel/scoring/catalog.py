"""Catalog match: product quote (or seller-entered name) -> product, RapidFuzz >= 80."""
from __future__ import annotations

from rapidfuzz import fuzz

from wasel.ml.textnorm import normalize


def match_product(text: str | None, catalog: dict, min_score: int = 80) -> tuple[dict | None, float]:
    """Best catalog match for a product quote or seller-entered name, as (product, score).

    Compares against the product name and its aliases in every language, after normalization; an exact match scores
    100, otherwise RapidFuzz token_set_ratio. Returns (None, best_score) below `min_score`, and (None, 0.0) for empty
    text.
    """
    if not text:
        return None, 0.0
    q = normalize(text)
    best, best_score = None, 0.0
    for p in catalog["products"]:
        for alias in [p["name"], *[a for v in p["aliases"].values() for a in v]]:
            a = normalize(alias)
            score = 100.0 if a == q else fuzz.token_set_ratio(q, a)
            if score > best_score:
                best, best_score = p, score
    return (best, best_score) if best_score >= min_score else (None, best_score)
