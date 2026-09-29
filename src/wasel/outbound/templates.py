"""Static outbound templates: choice by rule, language routing, slot rendering."""
from __future__ import annotations

import re

TEMPLATE_LANGS = ("fr", "darija_arabic_script", "arabizi")
_ARABIZI_MARK = re.compile(r"[a-z][2356789]|[2356789][a-z]|\b(nheb|ena|famma|chwaya|behi|ya3tik)\b", re.I)
_NAME_OK = re.compile(r"^[A-Za-zÀ-ɏ؀-ۿ \-]{1,20}$")


def choose_template(tier: str, action: str, address_level_final: str) -> str | None:
    """Prepay first, then an imprecise address, else confirm. Low tier -> no message."""
    if tier not in ("medium", "high") or action in ("cancelled", "review"):
        return None
    if action == "prepay":
        return "T_PREPAY"
    if address_level_final in ("none", "city_only", "area_or_landmark"):
        return "T_ADDRESS"
    return "T_CONFIRM"


def template_language(language: str | None, last_customer_text: str | None = None) -> str:
    """Language routing: fr -> fr, arabizi -> arabizi, ar/darija -> darija_arabic_script, mixed -> script of
    the last customer message."""
    if language in ("fr", "arabizi"):
        return language
    if language in ("ar", "darija_arabic_script"):
        return "darija_arabic_script"
    t = last_customer_text or ""
    letters = [c for c in t if c.isalpha()]
    if letters and sum("؀" <= c <= "ۿ" for c in letters) / len(letters) > 0.5:
        return "darija_arabic_script"
    if _ARABIZI_MARK.search(t):
        return "arabizi"
    return "fr"


def sanitize_first_name(display_name: str | None) -> str | None:
    if not display_name:
        return None
    first = display_name.strip().split()[0] if display_name.strip() else ""
    return first if _NAME_OK.match(first) else None


def format_price(price: float | None) -> str | None:
    return None if price is None else f"{price:g}"


def template_slots(templates: dict, template_id: str, lang: str, slots: dict[str, str | None]) -> dict[str, str]:
    """The slot values the chosen variant actually uses (the required slots): only these are checked."""
    t = templates["templates"][template_id][lang]
    body = t["text"] if slots.get("first_name") else t["no_name"]
    return {k: v for k, v in slots.items() if v and "{" + k + "}" in body}


def render_template(templates: dict, template_id: str, lang: str, slots: dict[str, str | None]) -> str:
    t = templates["templates"][template_id][lang]
    body = t["text"] if slots.get("first_name") else t["no_name"]
    return body.format(**{k: (v if v is not None else "") for k, v in slots.items()})


def expected_questions(templates: dict, template_id: str) -> str:
    return templates["expected_questions"][template_id]
