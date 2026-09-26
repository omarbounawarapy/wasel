"""rules_v1: the last-resort extractor (02 §6), also used at the LLM cap. Output goes through the same
postprocess as an LLM result; the run is recorded valid=0, path 'rules', confidence low, needs_review.

- address_level: pin -> exact; number/building token + street token -> exact; street token ->
  street_and_landmark; area/landmark token -> area_or_landmark; gazetteer place -> city_only; else none.
- flags: substring match of the non-eval_only bank phrases (slots expanded).
- tone: neutral. confirmation: ack/decline lexicon at the start of a customer line after the seller line.
- product_quote: a catalog alias found in the text.
"""
from __future__ import annotations

import re
from itertools import product as cartesian

from app.extraction.repair import OrderExtraction
from app.extraction.window import Window
from ml.textnorm import find_span, has_phrase, normalize, passes_exact_guard, tokens

STREET = ("rue", "avenue", "av", "nahj", "ne7j", "شارع", "نهج", "زنقة",
          "triq", "طريق")                                    # triq/طريق: ADDITIVE (hero v2 uses "triq")
AREA = ("cité", "cite", "hay", "7ay", "حي", "douar", "دوار", "9rib", "قريب", "à côté", "près", "9odem", "قدام",
        "jemaa", "جامع", "pharmacie", "صيدلية", "poste", "quartier")
_SENT = re.compile(r"[^.\n!?؟]+")
_SLOT = re.compile(r"\{(\w+)\}")


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENT.findall(text) if s.strip()]


def _bank_phrases(banks: dict) -> list[tuple[str, str]]:
    """(code, phrase) for every non-eval_only flag phrase, slots expanded with the slot lists."""
    out = []
    slots = banks.get("slots", {})
    for code, by_lang in banks.get("flags", {}).items():
        for lang, cell in by_lang.items():
            for ph in cell.get("train", []):
                names = _SLOT.findall(ph)
                if not names:
                    out.append((code, ph))
                    continue
                choices = [slots.get(n, {}).get(lang, []) for n in names]
                for combo in cartesian(*choices):
                    s = ph
                    for n, v in zip(names, combo, strict=True):
                        s = s.replace("{" + n + "}", v, 1)
                    out.append((code, s))
    return out


def _language(texts: list[str]) -> str:
    joined = " ".join(texts)
    ar = sum(1 for c in joined if "؀" <= c <= "ۿ")
    lat = sum(1 for c in joined if c.isalpha() and c.isascii())
    arabizi = bool(re.search(r"[a-z][2356789]|[2356789][a-z]", joined.lower())) or \
        any(t in ("nheb", "ena", "famma", "chwaya", "behi", "ya3tik") for t in tokens(joined))
    if ar and lat:
        return "mixed"
    if ar:
        return "darija_arabic_script"
    return "arabizi" if arabizi else "fr"


def rules_extract(w: Window, *, banks: dict, catalog: dict, zones: dict, lexicons: dict) -> OrderExtraction:
    cust = [m for m in w.messages if m.role == "customer" and m.kind != "location_pin" and m.text_orig]
    texts = [m.text_orig for m in cust]
    # product
    product_quote = None
    for m in reversed(cust):
        for p in catalog["products"]:
            for alias in [p["name"], *[a for v in p["aliases"].values() for a in v]]:
                if (sp := find_span(m.text_orig, alias)) is not None:
                    product_quote = m.text_orig[sp[0]:sp[1]]
                    break
            if product_quote:
                break
        if product_quote:
            break
    # address
    places = [a for e in zones["entries"] for a in [e["name"], e.get("name_ar", ""), *e.get("aliases", [])] if a]
    quotes: list[str] = []
    level_rank = 0
    ranks = {0: "none", 1: "city_only", 2: "area_or_landmark", 3: "street_and_landmark", 4: "exact"}
    for t in texts:
        for sent in _sentences(t):
            has_street = any(has_phrase(sent, s) for s in STREET)
            has_area = any(has_phrase(sent, a) for a in AREA)
            has_city = any(has_phrase(sent, p) for p in places)
            r = 0
            if has_street and passes_exact_guard([sent]):
                r = 4
            elif has_street:
                r = 3
            elif has_area:
                r = 2
            elif has_city:
                r = 1
            if r:
                quotes.append(sent[:160])
                level_rank = max(level_rank, r)
    if w.has_geo_pin:
        level_rank = 4
    # flags
    flags, seen = [], set()
    for code, ph in _bank_phrases(banks):
        if code in seen:
            continue
        for t in reversed(texts):
            if (sp := find_span(t, ph)) is not None:
                flags.append({"evidence": t[sp[0]:sp[1]], "code": code})
                seen.add(code)
                break
    # confirmation (customer lines after the seller line)
    conf = "none"
    k = w.k
    if k is not None:
        after = [m.text_orig for m in cust if m.idx > k]
        for t in after:
            head = normalize(t)
            if any(head.startswith(normalize(d)) and has_phrase(t[:40], d) for d in lexicons.get("decline", [])):
                conf = "declined"
            elif any(head.startswith(normalize(a)) for a in lexicons.get("ack", [])):
                conf = "confirmed"
    is_order = bool(product_quote or quotes or flags)
    return OrderExtraction(
        is_order=is_order, is_order_change=False, product_quote=product_quote, quantity=None,
        address_quotes=list(dict.fromkeys(quotes))[:4], address_level=ranks[level_rank],
        red_flags=flags[:6], tone_evidence=None, tone="neutral", confirmation=conf,
        language=_language(texts) if texts else "mixed", clarity="partial")
