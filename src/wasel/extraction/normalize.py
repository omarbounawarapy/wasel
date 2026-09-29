"""Length-preserving sanitize/defuse and phone masking, plus re-exports of the shared
normalizer. Every target of DEFUSE is one code point, one UTF-16 unit and NFKC-stable, so evidence spans
found on the LLM view index the original text unchanged."""
from __future__ import annotations

import re
import unicodedata

from wasel.ml.textnorm import normalize, normalize_with_map  # noqa: F401  (re-export: the one normalizer)

D = "0-9٠-٩"
PHONE = re.compile(rf"(?<!\w)(?:(?:\+|00)?216[\s.-]?)?[{D}]{{2}}[\s.-]?[{D}]{{3}}[\s.-]?[{D}]{{3}}(?!\w)")
CF_CHARS = [*range(0x200B, 0x2010), *range(0x202A, 0x202F), *range(0x2060, 0x2065), *range(0x2066, 0x206A), 0xFEFF]
DEFUSE = str.maketrans({
    "<": "‹", "＜": "‹", ">": "›", "＞": "›",                 # U+2039 / U+203A
    "[": "⟦", "［": "⟦", "]": "⟧", "］": "⟧",                 # U+27E6 / U+27E7
    "{": "⦃", "｛": "⦃", "}": "⦄", "｝": "⦄",                 # U+2983 / U+2984
    "\n": " ", "\r": " ", "\t": " ", " ": " ", " ": " ",
    **{chr(c): " " for c in CF_CHARS},
})


def mask_phones(s: str) -> str:
    return PHONE.sub(lambda m: re.sub(rf"[{D}]", "•", m.group(0)), s)


def sanitize_llm_view(s: str) -> str:
    out = mask_phones(s).translate(DEFUSE)
    assert len(out) == len(s)
    return out


def lexicon_view(s: str) -> str:
    """normalize(text) with every Unicode format character (category Cf) REMOVED, so 'ig\\u200bnore'
    can't split a lexicon word."""
    return normalize("".join(ch for ch in s if unicodedata.category(ch) != "Cf"))


def mask_phone_for_display(e164: str | None) -> str | None:
    """'+21600000001' -> '+216 •• ••• 001'."""
    if not e164:
        return None
    digits = re.sub(r"\D", "", e164)
    return f"+216 •• ••• {digits[-3:]}" if len(digits) >= 3 else "+216 •• ••• •••"
