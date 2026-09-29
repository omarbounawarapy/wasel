"""Canonical (Groq strict) schema -> what Gemini's OpenAI-compat response_format accepts.
The style is chosen by a probe of the account's model and written to config/probe.json."""
from __future__ import annotations


def to_gemini_compat_schema(s: dict, *, nullable: str = "type_array",
                            strip_additional: bool = False, property_ordering: bool = False) -> dict:
    def rec(x):
        return to_gemini_compat_schema(x, nullable=nullable, strip_additional=strip_additional,
                                       property_ordering=property_ordering)
    t = s.get("type")
    if isinstance(t, list):
        base = next(x for x in t if x != "null")
        if nullable == "any_of":
            return {"anyOf": [rec({**s, "type": base}), {"type": "null"}]}
        out = {"type": list(t)} if nullable == "type_array" else {"type": base, "nullable": True}
    else:
        out = {"type": t} if t else {}
    if "enum" in s:
        out["enum"] = list(s["enum"])
    if "items" in s:
        out["items"] = rec(s["items"])
    if "properties" in s:
        out["properties"] = {k: rec(v) for k, v in s["properties"].items()}     # dict order kept
        out["required"] = list(s["required"])
        if property_ordering:
            out["propertyOrdering"] = list(s["properties"])
    if "additionalProperties" in s and not strip_additional:
        out["additionalProperties"] = s["additionalProperties"]
    return out
