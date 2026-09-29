"""Deterministic injection lexicon. The patterns live in config/scoring.yaml: lexicons.injection.
Runs on every [CUSTOMER] / [CUSTOMER:voice] line, never on [SELLER]. A hit sets injection_suspected
(-> confidence low, needs_review, forced is_order=true, confirmation ignored). It NEVER changes the score."""
from __future__ import annotations

import re
from functools import lru_cache

from wasel.extraction.normalize import lexicon_view
from wasel.extraction.window import Window


@lru_cache(maxsize=8)
def _compile(normalized: tuple[str, ...], defused: tuple[str, ...]):
    return ([re.compile(p, re.IGNORECASE) for p in normalized],
            [re.compile(p, re.IGNORECASE) for p in defused])


def injection_hit_text(text_orig: str, text_llm: str, lexicon: dict) -> bool:
    norm, defu = _compile(tuple(lexicon.get("normalized", [])), tuple(lexicon.get("defused", [])))
    view = lexicon_view(text_orig)
    return any(p.search(view) for p in norm) or any(p.search(text_llm) for p in defu)


def injection_hit(w: Window, lexicon: dict) -> bool:
    return any(injection_hit_text(m.text_orig, m.text_llm, lexicon)
               for m in w.messages if m.role == "customer" and m.kind in ("text", "voice"))
