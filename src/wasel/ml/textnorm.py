"""Shared text normalization and the Arabizi-digit number helper.

One implementation, imported by the serve evidence check, the exact guard, the generator lints,
the prefilter and the tests. Normalization is per character with an index map back to the
original string, so evidence spans always land on the original text.
"""
from __future__ import annotations

import re
import unicodedata

ARABIC_DIACRITICS = {chr(c) for c in range(0x064B, 0x0653)} | {"ٰ"}
TATWEEL = "ـ"
LETTER_MAP = {"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي", "ة": "ه",
              "،": ",", "؛": ";", "’": "'", "‘": "'", "«": '"', "»": '"',
              **{chr(0x0660 + i): str(i) for i in range(10)},       # Arabic-Indic digits → ASCII
              **{chr(0x06F0 + i): str(i) for i in range(10)}}       # Extended Arabic-Indic digits → ASCII


def normalize_with_map(s: str) -> tuple[str, list[int]]:
    """Per-character normalization; idx[j] = index in s of normalized char j."""
    out: list[str] = []
    idx: list[int] = []
    for i, ch in enumerate(s):
        for c in unicodedata.normalize("NFKC", ch).casefold():
            if c in ARABIC_DIACRITICS or c == TATWEEL:
                continue
            c = LETTER_MAP.get(c, c)
            if c.isspace():
                if out and out[-1] == " ":
                    continue
                c = " "
            out.append(c)
            idx.append(i)
    return "".join(out), idx


def normalize(s: str) -> str:
    return normalize_with_map(s)[0].strip()


def find_span(text: str, phrase: str) -> tuple[int, int] | None:
    """(start, end) of `phrase` inside `text`, in ORIGINAL code points, matched after normalization."""
    q = normalize(phrase)
    if not q:
        return None
    t, idx = normalize_with_map(text)
    pos = t.find(q)
    if pos < 0:
        return None
    return idx[pos], idx[pos + len(q) - 1] + 1


# ---------------------------------------------------------------- numbers
LATIN = r"A-Za-zÀ-ɏ"
DIGITS = r"0-9٠-٩۰-۹"
NUM_RE = re.compile(rf"(?<![{LATIN}{DIGITS}])[{DIGITS}]{{1,3}}(?![{LATIN}{DIGITS}])")
# "dar 14", "dar n°14", "دار 14". "dar14" deliberately does NOT match (known gap).
DAR_N_RE = re.compile(rf"\b(dar|دار)(?:\s+(?:n?°?|عدد|رقم)\s*|\s+n°\s*)[{DIGITS}]{{1,3}}(?![{LATIN}{DIGITS}])")
BUILDING_TOKENS_RAW = ("imm", "immeuble", "immeubles", "apt", "app", "appartement", "etage", "étage",
                       "bloc", "block", "residence", "résidence", "villa", "maison",
                       "عمارة", "شقة", "طابق", "إقامة", "اقامة", "بلوك")
BUILDING_TOKENS = frozenset(normalize(t) for t in BUILDING_TOKENS_RAW)
_TOKEN_RE = re.compile(r"[^\W_]+")
_AR_PREFIXES = ("وال", "ال", "و")


def standalone_numbers(text: str) -> list[str]:
    """Digit runs of 1–3 not glued to a Latin letter (Arabizi digits are letters). Returned in the
    original script ("٣٤", not "34")."""
    t, idx = normalize_with_map(text)
    return [text[idx[m.start()]: idx[m.end() - 1] + 1] for m in NUM_RE.finditer(t)]


def tokens(text: str) -> list[str]:
    """Normalized word tokens, Arabic prefixes ال / و stripped."""
    out = []
    for tok in _TOKEN_RE.findall(normalize(text)):
        for p in _AR_PREFIXES:
            if tok.startswith(p) and len(tok) > len(p) + 1 and not tok.isascii():
                tok = tok[len(p):]
                break
        out.append(tok)
    return out


def has_token(text: str, vocab) -> bool:
    vocab = {normalize(v) for v in vocab}
    return any(t in vocab for t in tokens(text))


def has_building_token(text: str) -> bool:
    return any(t in BUILDING_TOKENS for t in tokens(text)) or bool(DAR_N_RE.search(normalize(text)))


def passes_exact_guard(quotes: list[str]) -> bool:
    return any(standalone_numbers(q) or has_building_token(q) for q in quotes)


def has_phrase(text: str, phrase: str) -> bool:
    """Whole-token phrase match on normalized token sequences, so '9rib' never matches 'rib'."""
    p = tokens(phrase)
    if not p:
        return False
    t = tokens(text)
    n = len(p)
    return any(t[i:i + n] == p for i in range(len(t) - n + 1))
