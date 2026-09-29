"""Evidence location: every quote must be a verbatim (normalized) substring of ONE [CUSTOMER] line.
The latest occurrence wins, and spans index the ORIGINAL text through the index map."""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from wasel.extraction.window import WindowMsg
from wasel.ml.textnorm import normalize_with_map


@dataclass(frozen=True)
class EvidenceSpan:                 # contract type + msg_idx and the product/tone kinds
    """A verified span of a customer message, with the message's position in the window.

    Offsets index the original text; the LLM view has the same length, so they apply to it unchanged. `quote` comes
    from the LLM view, so phone numbers stay masked.
    """
    message_id: str
    msg_idx: int
    start: int                      # code-point offset into the ORIGINAL text (== text_llm offset)
    end: int                        # exclusive
    kind: Literal["address", "red_flag", "product", "tone"]
    code: str | None
    quote: str                      # text_llm[start:end] (phones stay masked)


def locate(quote: str, msgs: Sequence[WindowMsg], *, min_chars: int = 3, after: int | None = None
           ) -> tuple[int, int, WindowMsg] | None:
    """Find `quote` in the customer lines of `msgs`; returns (start, end, message) or None.

    Matching ignores case, diacritics and spacing variants (see normalize), searches the newest message first and
    returns offsets in the original text. Quotes shorter than `min_chars` (spaces ignored) never match. With `after`,
    only messages whose idx is greater than it are searched. Seller lines and location pins are never searched.
    """
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
