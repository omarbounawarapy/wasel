"""Inline highlighting of flagged phrases. Escapes the raw text itself, so customer text can't inject HTML."""
import html

from .schemas import RedFlag

COLORS = {
    "vague_location": "#f6c34d", "reschedule": "#8ab4f8", "hesitation": "#f28b82",
    "third_party_receiver": "#c58af9", "other": "#d0d0d0",
}


def highlight(text: str, flags: list[RedFlag]) -> str:
    if not text:
        return "<em>(empty)</em>"
    spans: list[tuple[int, int, str]] = []
    for f in flags:
        start = text.find(f.text)
        while start != -1:
            end = start + len(f.text)
            if not any(s < end and start < e for s, e, _ in spans):
                spans.append((start, end, f.type))
            start = text.find(f.text, end)
    spans.sort()
    out, pos = [], 0
    for s, e, t in spans:
        out.append(html.escape(text[pos:s]))
        out.append(f'<mark style="background:{COLORS[t]};color:#111;border-radius:3px;padding:0 2px" '
                   f'title="{t}">{html.escape(text[s:e])}</mark>')
        pos = e
    out.append(html.escape(text[pos:]))
    return "".join(out)
