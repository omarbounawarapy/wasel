"""order_extraction_v1 Pydantic mirror + lenient repair. Repair clamps and truncates,
never rejects on a fixable value; only an unusable SHAPE raises ParseError.

Out-of-range quantity -> null (an out-of-range value is not clamped to the bound)."""
from __future__ import annotations

import json
from typing import Literal, get_args

from pydantic import BaseModel, ConfigDict, ValidationError

from wasel.llm.base import ParseError
from wasel.paths import ROOT

AddressLevel = Literal["none", "city_only", "area_or_landmark", "street_and_landmark", "exact"]
FlagCode = Literal["availability_uncertain", "vague_location", "price_hesitation",
                   "third_party_recipient", "prior_refusal_mention", "pressure_or_inconsistency"]
Tone = Literal["positive", "neutral", "uncertain", "negative"]
Confirmation = Literal["none", "confirmed", "declined", "reschedule", "ambiguous"]
Language = Literal["fr", "ar", "darija_arabic_script", "arabizi", "mixed"]
Clarity = Literal["clear", "partial", "unclear"]

FIELD_ORDER = ("is_order", "is_order_change", "product_quote", "quantity", "address_quotes",
               "address_level", "red_flags", "tone_evidence", "tone", "confirmation",
               "language", "clarity")

MAX_QUOTE_CHARS = 160
MAX_PRODUCT_CHARS = 120
MAX_ADDRESS_QUOTES = 4
MAX_FLAGS = 6
QTY_MIN, QTY_MAX = 1, 50
ENUM_FALLBACK = {"tone": "neutral", "confirmation": "none", "language": "mixed", "clarity": "partial"}
SCHEMA_PATH = ROOT / "config" / "schemas" / "order_extraction_v1.json"


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class RedFlag(Strict):
    evidence: str
    code: FlagCode


class OrderExtraction(Strict):
    is_order: bool
    is_order_change: bool
    product_quote: str | None
    quantity: int | None
    address_quotes: list[str]
    address_level: AddressLevel
    red_flags: list[RedFlag]
    tone_evidence: str | None
    tone: Tone
    confirmation: Confirmation
    language: Language
    clarity: Clarity


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _s(v, max_len: int) -> str | None:
    if not isinstance(v, str):
        return None
    v = v.strip()
    if not v:
        return None
    return v[:max_len].rstrip()


def repair(raw: object) -> tuple[dict, list[str]]:
    if not isinstance(raw, dict):
        raise ParseError("not_an_object")
    missing = [k for k in FIELD_ORDER if k not in raw]
    if missing:
        raise ParseError(f"missing:{','.join(missing)}")
    w: list[str] = []
    extra = [k for k in raw if k not in FIELD_ORDER]
    if extra:
        w.append(f"extra_keys_dropped:{','.join(extra)}")
    d = {k: raw[k] for k in FIELD_ORDER}

    for k in ("is_order", "is_order_change"):
        if not isinstance(d[k], bool):
            raise ParseError(f"type:{k}")
    if d["address_level"] not in get_args(AddressLevel):
        raise ParseError("enum:address_level")          # feature 0: never guessed

    pq = _s(d["product_quote"], MAX_PRODUCT_CHARS)
    if d["product_quote"] is not None and pq != d["product_quote"]:
        w.append("product_quote_repaired")
    d["product_quote"] = pq

    q = d["quantity"]
    if isinstance(q, float) and q.is_integer():
        q = int(q)
    if q is not None and (isinstance(q, bool) or not isinstance(q, int) or not QTY_MIN <= q <= QTY_MAX):
        w.append(f"quantity_nulled:{d['quantity']!r}")
        q = None
    d["quantity"] = q

    aq_in = d["address_quotes"] if isinstance(d["address_quotes"], list) else []
    aq, seen = [], set()
    for a in aq_in:
        s = _s(a, MAX_QUOTE_CHARS)
        if s and s not in seen:
            aq.append(s)
            seen.add(s)
    if len(aq) > MAX_ADDRESS_QUOTES:
        w.append(f"address_quotes_truncated:{len(aq)}")
    if len(aq) != len(aq_in):
        w.append("address_quotes_cleaned")
    d["address_quotes"] = aq[:MAX_ADDRESS_QUOTES]

    flags_in = d["red_flags"] if isinstance(d["red_flags"], list) else []
    flags, codes = [], set()
    for f in flags_in:
        if not isinstance(f, dict):
            w.append("flag_dropped:not_object")
            continue
        ev, code = _s(f.get("evidence"), MAX_QUOTE_CHARS), f.get("code")
        if ev is None or code not in get_args(FlagCode):
            w.append(f"flag_dropped:{code!r}")
            continue
        if code in codes:
            w.append(f"flag_duplicate_dropped:{code}")
            continue
        if set(f) - {"evidence", "code"}:
            w.append("flag_extra_keys_dropped")
        flags.append({"evidence": ev, "code": code})
        codes.add(code)
    if len(flags) > MAX_FLAGS:
        w.append(f"flags_truncated:{len(flags)}")
    d["red_flags"] = flags[:MAX_FLAGS]

    te = _s(d["tone_evidence"], MAX_QUOTE_CHARS)
    if d["tone_evidence"] is not None and te != d["tone_evidence"]:
        w.append("tone_evidence_repaired")
    d["tone_evidence"] = te

    for k, fallback in ENUM_FALLBACK.items():
        allowed = get_args({"tone": Tone, "confirmation": Confirmation,
                            "language": Language, "clarity": Clarity}[k])
        if d[k] not in allowed:
            w.append(f"enum_clamped:{k}:{d[k]!r}->{fallback}")
            d[k] = fallback
    return d, w


def parse_extraction(raw_text: str) -> tuple[OrderExtraction, list[str]]:
    try:
        obj = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise ParseError(f"json:{e.msg}") from e
    d, warnings = repair(obj)
    try:
        return OrderExtraction.model_validate(d), warnings
    except ValidationError as e:          # should be unreachable after repair
        raise ParseError(f"pydantic:{e.error_count()}") from e
