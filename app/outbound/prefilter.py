"""Deterministic draft prefilter (02 §8.1, SD §8.3). A draft is rejected if ANY rule fails. Runs on the
static templates in CI (12/12) and on every rewritten draft. Numbers use the Arabizi-digit exception:
a digit touching a letter is a letter (3andek, 9rib, ta3tina yield no numbers)."""
from __future__ import annotations

import re
import unicodedata
from decimal import Decimal, InvalidOperation

from app.extraction.injection import injection_hit_text
from app.extraction.normalize import PHONE, sanitize_llm_view
from ml.textnorm import has_phrase

# SPEC FIX: 02 §8.1 bounds these with (?<![^\W\d_]) / (?![^\W\d_]) (letters only), which backtracks
# into "89DT" -> "8" and "10h30" -> "0", "1". Bounding on any word char (digits included) fixes it.
NUM = re.compile(r"(?<![^\W_])[0-9٠-٩]+(?:[.,][0-9٠-٩]+)?(?![^\W_])")
NUM_UNIT = re.compile(r"(?<![^\W_])([0-9٠-٩]+(?:[.,][0-9٠-٩]+)?)\s?"
                      r"(?:h|dt|tnd|dinars?|d|%|د\.?ت|دينار|دنانير)(?:[0-9٠-٩]{2})?(?![^\W\d_])", re.I)
URL = re.compile(r"(https?://|www\.|wa\.me/|bit\.ly/|\b[\w-]+\.(?:com|tn|net|org|io|me|ly)\b)", re.I)
_AR_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")


def numbers_in(text: str) -> set[Decimal]:
    vals = {m.group(0) for m in NUM.finditer(text)} | {m.group(1) for m in NUM_UNIT.finditer(text)}
    out = set()
    for v in vals:
        try:
            out.add(Decimal(v.translate(_AR_DIGITS).replace(",", ".")))
        except InvalidOperation:
            pass
    return out


def prefilter(draft: str, template_text: str, slots: dict[str, str | None], expected_questions: str,
              lexicons: dict, injection_lexicon: dict | None = None) -> list[str]:
    fails: list[str] = []
    for k, v in slots.items():
        if v and unicodedata.normalize("NFC", v) not in unicodedata.normalize("NFC", draft):
            fails.append(f"slot_missing:{k}")
    allowed = numbers_in(template_text)
    if slots.get("price_tnd"):
        allowed |= numbers_in(str(slots["price_tnd"]))
    if extra := numbers_in(draft) - allowed:
        fails.append(f"number_not_allowed:{sorted(str(x) for x in extra)}")
    if URL.search(draft):
        fails.append("url")
    if PHONE.search(draft):
        fails.append("phone")
    allow = [a for a in lexicons.get("allowlist", [])]
    probe = draft
    for a in allow:                                   # F16: "code postal" is not a payment term
        probe = re.sub(re.escape(a), " ", probe, flags=re.I)
    for group in ("payment", "discount", "promise"):
        for t in lexicons.get(group, []):
            if has_phrase(probe, t) and not has_phrase(template_text, t):
                fails.append(f"{group}:{t}")
    if injection_lexicon and injection_hit_text(draft, sanitize_llm_view(draft), injection_lexicon):
        fails.append("instructions_in_draft")
    nq = draft.count("?") + draft.count("؟")
    if (expected_questions == "none" and nq > 0) or (expected_questions == "one" and nq > 1):
        fails.append(f"question_count:{nq}")
    if len(draft) > lexicons.get("max_chars", 400):
        fails.append("too_long")
    return fails
