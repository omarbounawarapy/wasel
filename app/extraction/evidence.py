"""Evidence location: every quote must be a verbatim (normalized) substring of ONE [CUSTOMER] line.
The latest occurrence wins, and spans index the ORIGINAL text through the index map."""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from app.extraction.window import WindowMsg
from ml.textnorm import normalize_with_map


@dataclass(frozen=True)
class EvidenceSpan:                 # contract type + msg_idx and the product/tone kinds
    message_id: str
    msg_idx: int
    start: int                      # code-point offset into the ORIGINAL text (== text_llm offset)
    end: int                        # exclusive
    kind: Literal["address", "red_flag", "product", "tone"]
    code: str | None
    quote: str                      # text_llm[start:end] (phones stay masked)


def locate(quote: str, msgs: Sequence[WindowMsg], *, min_chars: int = 3, after: int | None = None
           ) -> tuple[int, int, WindowMsg] | None:
    q, _ = normalize_with_map(quote.strip())
    q = q.strip()
    if len(q.replace(" ", "")) < min_chars:
        return None
    for m in reversed(msgs):
        if m.role != "customer" or m.kind == "location_pin":
            continue
        if after is not None and m.idx <= after:
            continue
        t, idx = normalize_with_map(m.text_llm)
        pos = t.find(q)
        if pos >= 0:
            return idx[pos], idx[pos + len(q) - 1] + 1, m
    return None
