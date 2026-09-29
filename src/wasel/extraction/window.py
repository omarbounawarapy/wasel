"""The extraction window: customer lines + only the latest seller line, capped,
sanitized, rendered in the exact few-shot format. The [SELLER] line is the CANONICAL template text,
never a rewritten draft ."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Literal

from wasel.contracts import ScoreInput, WindowMessage
from wasel.extraction.normalize import sanitize_llm_view

MAX_MESSAGES = 12
MAX_CHARS = 2000


@dataclass(frozen=True)
class WindowMsg:
    """One line of the extraction window. `idx` is its position in Window.messages.

    `text_orig` is the stored text (for a seller line, the canonical template text) and `text_llm` is its sanitized
    view of the same length.
    """
    idx: int                                   # position in Window.messages (used as msg_idx)
    message_id: str
    role: Literal["customer", "seller"]
    kind: Literal["text", "voice", "location_pin"]
    template_id: str | None                    # seller only
    text_orig: str                             # customer: as stored; seller: canonical template text
    text_llm: str                              # sanitize_llm_view(text_orig); same length


@dataclass(frozen=True)
class Window:
    """The messages that go into one extraction: customer lines plus the latest seller line."""
    order_id: str
    messages: tuple[WindowMsg, ...]
    has_geo_pin: bool
    has_unsupported_media: bool = False

    @property
    def k(self) -> int | None:                 # index of the latest seller line
        """Index of the latest seller line, or None if there is none."""
        s = [m.idx for m in self.messages if m.role == "seller"]
        return s[-1] if s else None

    @property
    def message_ids(self) -> list[str]:
        """Message ids in window order; `msg_idx` values elsewhere index this list."""
        return [m.message_id for m in self.messages]

    def render(self) -> str:
        """The user prompt: one tagged line per message ([SELLER], [CUSTOMER], [CUSTOMER:voice],
        [CUSTOMER:location_pin]) in the format the few-shot examples use.
        """
        lines = ["<customer_messages>"]
        for m in self.messages:
            if m.role == "seller":
                lines.append(f"[SELLER] {m.text_llm}")
            elif m.kind == "location_pin":
                lines.append("[CUSTOMER:location_pin]")
            elif m.kind == "voice":
                lines.append(f"[CUSTOMER:voice] {m.text_llm}")
            else:
                lines.append(f"[CUSTOMER] {m.text_llm}")
        lines += ["</customer_messages>", "Extract order_extraction_v1 from the messages above."]
        return "\n".join(lines)

    def cache_key(self, prompt_version: str) -> str:
        """input_hash: the sanitized render, not normalized text; the model is not in it."""
        return hashlib.sha256(f"extract|{prompt_version}|order_extraction_v1|{self.render()}".encode()).hexdigest()

    def replay_key(self) -> str:
        """SHA-256 of the rendered window, the key of recorded LLM fixtures."""
        return hashlib.sha256(self.render().encode()).hexdigest()

    @property
    def is_empty(self) -> bool:
        """True if there is no customer text, transcript or location pin to extract from."""
        return not any(m.role == "customer" and (m.text_orig or m.kind == "location_pin") for m in self.messages)


def _customer_line(m: WindowMessage) -> tuple[str, str] | None:
    """(kind, text) for a customer message that enters the window, else None."""
    if m.kind == "text" and m.text:
        return "text", m.text
    if m.kind == "audio" and m.transcript:
        return "voice", m.transcript
    if m.kind == "location" or m.has_location:
        return "location_pin", ""
    return None


def build_window(inp: ScoreInput, max_messages: int = MAX_MESSAGES, max_chars: int = MAX_CHARS) -> Window:
    """Build the extraction window from a ScoreInput.

    Messages are ordered by provider timestamp. Customer text, audio transcripts and location pins are kept; only the
    latest outbound message is kept, as a [SELLER] line using the canonical template text (AI messages without one are
    skipped). When over `max_messages` or `max_chars`, the oldest customer messages before the seller line are dropped
    first. `has_unsupported_media` is set for images, interactive messages and untranscribed audio.
    """
    msgs = sorted(inp.messages, key=lambda m: m.provider_ts)
    outbound = [m for m in msgs if m.direction == "outbound"
                and not (m.author == "ai" and not m.canonical_text)]
    latest_out = outbound[-1] if outbound else None
    unsupported = any(m.direction == "inbound" and m.kind in ("image", "interactive", "unsupported")
                      or (m.kind == "audio" and not m.transcript and m.direction == "inbound") for m in msgs)
    items: list[tuple[str, str, str, str | None, str]] = []   # (message_id, role, kind, template_id, text)
    for m in msgs:
        if m.direction == "inbound":
            line = _customer_line(m)
            if line:
                items.append((m.message_id, "customer", line[0], None, line[1]))
        elif m is latest_out:
            text = m.canonical_text if m.author == "ai" else (m.text or "")
            items.append((m.message_id, "seller", "text", m.template_id, text or ""))
    # Cap: keep the seller line and every customer line after it; drop the oldest whole customer
    # messages before it; if the post-seller lines alone exceed the cap, keep the newest of them.
    seller_pos = next((i for i, it in enumerate(items) if it[1] == "seller"), None)

    def size(xs):
        return len(xs), sum(len(x[4]) for x in xs)

    if seller_pos is not None:
        before, seller, after = items[:seller_pos], [items[seller_pos]], items[seller_pos + 1:]
    else:
        before, seller, after = items, [], []
    if seller:
        while after and (size(seller + after)[0] > max_messages or size(seller + after)[1] > max_chars) \
                and len(after) > 1:
            after = after[1:]
        while before and (size(before + seller + after)[0] > max_messages
                          or size(before + seller + after)[1] > max_chars):
            before = before[1:]
    else:
        while len(before) > 1 and (size(before)[0] > max_messages or size(before)[1] > max_chars):
            before = before[1:]
    kept = before + seller + after
    wmsgs = tuple(WindowMsg(i, mid, role, kind, tid, text, sanitize_llm_view(text))
                  for i, (mid, role, kind, tid, text) in enumerate(kept))
    return Window(inp.order_id, wmsgs,
                  has_geo_pin=any(m.direction == "inbound" and (m.kind == "location" or m.has_location)
                                  for m in msgs),
                  has_unsupported_media=unsupported)
