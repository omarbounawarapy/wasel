"""Post-processing, in a fixed order: evidence check -> tone gate -> cross-field
rules (confirmation, exact guard) -> pin override -> dedupe_by_code -> resolve_flags -> is_order guard.
Pure: the same function runs in the golden test, the eval runner and the API."""
from __future__ import annotations

from dataclasses import dataclass, field

from wasel.extraction.evidence import EvidenceSpan, locate
from wasel.extraction.injection import injection_hit
from wasel.extraction.repair import OrderExtraction
from wasel.extraction.window import Window
from wasel.ml.features import FLAG_ORDER, VerifiedFlag, dedupe_by_code, resolve_flags, tone_gate
from wasel.ml.textnorm import passes_exact_guard


@dataclass(frozen=True)
class Processed:
    is_order: bool
    is_order_change: bool
    product_quote: str | None
    quantity: int | None
    address_quotes: list[tuple[str, int]]      # (verified quote in original text, msg_idx)
    address_level_raw: str
    address_level: str
    flags: list[VerifiedFlag]                  # surviving, FLAG_ORDER
    resolved_flags: list[str]
    tone: str
    tone_reset: bool
    tone_evidence: str | None
    confirmation: str
    language: str
    clarity: str
    dropped_flags: int
    dropped_quotes: int
    injection_suspected: bool
    spans: list[EvidenceSpan]
    warnings: list[str] = field(default_factory=list)
    verified_flags: list[VerifiedFlag] = field(default_factory=list)   # pre-dedupe/resolve (cache stage)
    address_level_evidence: str = "none"                               # after the evidence check only
    confirmation_raw: str = "none"

    @property
    def flag_codes(self) -> list[str]:
        return [f.code for f in self.flags]

    def cache_extraction(self) -> dict:
        """Stage stored in extraction_cache: after repair + evidence check + tone gate.
        Cross-field rules, the pin override and resolve_flags re-run on every hit, so they stay current."""
        return {
            "is_order": self.is_order, "is_order_change": self.is_order_change,
            "product_quote": self.product_quote, "quantity": self.quantity,
            "address_quotes": [q for q, _ in self.address_quotes],
            "address_level": self.address_level_evidence,
            "red_flags": [{"evidence": f.quote, "code": f.code, "msg_idx": f.msg_idx} for f in self.verified_flags],
            "tone_evidence": self.tone_evidence, "tone": self.tone, "confirmation": self.confirmation_raw,
            "language": self.language, "clarity": self.clarity,
        }

    def validated(self) -> dict:
        """The final 12-field extraction after every deterministic step (-> validated_json).
        Quotes are original text; evidence carries msg_idx (01 CachedExtraction)."""
        return {
            "is_order": self.is_order, "is_order_change": self.is_order_change,
            "product_quote": self.product_quote, "quantity": self.quantity,
            "address_quotes": [q for q, _ in self.address_quotes], "address_level": self.address_level,
            "red_flags": [{"evidence": f.quote, "code": f.code, "msg_idx": f.msg_idx} for f in self.flags],
            "tone_evidence": self.tone_evidence, "tone": self.tone, "confirmation": self.confirmation,
            "language": self.language, "clarity": self.clarity,
        }


def postprocess(ext: OrderExtraction, w: Window, *, prior_confirmation: str = "none",
                injection_lexicon: dict | None = None) -> Processed:
    warn: list[str] = []
    spans: list[EvidenceSpan] = []
    k = w.k
    # 1. product
    product_quote = None
    if ext.product_quote and (hit := locate(ext.product_quote, w.messages, min_chars=2)):
        s, e, m = hit
        product_quote = m.text_orig[s:e]
        spans.append(EvidenceSpan(m.message_id, m.idx, s, e, "product", None, m.text_llm[s:e]))
    # 2. address quotes (no verified quote -> level none)
    addr: list[tuple[str, int]] = []
    for q in ext.address_quotes:
        if hit := locate(q, w.messages):
            s, e, m = hit
            addr.append((m.text_orig[s:e], m.idx))
            spans.append(EvidenceSpan(m.message_id, m.idx, s, e, "address", None, m.text_llm[s:e]))
    dropped_quotes = len(ext.address_quotes) - len(addr)
    level_raw = ext.address_level
    level = ext.address_level if addr else "none"
    # 3. flags (customer lines only; a quote found only in [SELLER] is dropped)
    verified: list[VerifiedFlag] = []
    for f in ext.red_flags:
        if hit := locate(f.evidence, w.messages):
            s, e, m = hit
            verified.append(VerifiedFlag(f.code, m.idx, s, e, m.message_id, m.text_orig[s:e]))
    dropped_flags = len(ext.red_flags) - len(verified)
    # 4. tone gate: evidence taken after the seller line if there is one; no overlap with any verified flag
    tone_span = None
    tone_evidence = None
    if ext.tone != "neutral" and ext.tone_evidence:
        hit = locate(ext.tone_evidence, w.messages, after=k)
        if hit:
            s, e, m = hit
            tone_span = (m.idx, s, e)
            tone_evidence = m.text_orig[s:e]
    tone = tone_gate(ext.tone, tone_span, [(f.msg_idx, f.start, f.end) for f in verified])
    tone_reset = tone != ext.tone
    if tone_reset:
        warn.append("tone_neutralized")
        tone_evidence = None
    elif tone_span is not None:
        i, s, e = tone_span
        m = w.messages[i]
        spans.append(EvidenceSpan(m.message_id, i, s, e, "tone", None, m.text_llm[s:e]))
    # 5. cross-field: confirmation needs a seller line with a customer line after it
    conf = ext.confirmation
    seller = w.messages[k] if k is not None else None
    if seller is None or not any(m.role == "customer" and m.idx > k for m in w.messages):
        conf = "none"
    elif seller.template_id == "T_ACK":
        conf = prior_confirmation                                  # T_ACK asks nothing
    elif seller.template_id == "T_ADDRESS" and conf == "confirmed" and not any(i > k for _, i in addr) \
            and not w.has_geo_pin:
        warn.append("ack_without_address->ambiguous")
        conf = "ambiguous"
    #    exact guard (shared Arabizi-digit helper)
    if level == "exact" and not passes_exact_guard([q for q, _ in addr]):
        warn.append("exact_downgraded")
        level = "street_and_landmark"
    # 6. pin override
    if w.has_geo_pin:
        level = "exact"
    # 7. dedupe_by_code -> resolve_flags (code owns the final set; only removes; idempotent)
    kept, resolved = resolve_flags(dedupe_by_code(verified), level, conf, k)
    for f in kept:
        m = w.messages[f.msg_idx]
        spans.append(EvidenceSpan(f.message_id, f.msg_idx, f.start, f.end, "red_flag", f.code,
                                  m.text_llm[f.start:f.end]))
    if resolved:
        warn.append("flags_resolved:" + ",".join(resolved))
    # 9. is_order guard (code owns it) + injection
    inj = injection_hit(w, injection_lexicon or {})
    is_order = ext.is_order
    if not is_order and (inj or product_quote or addr):
        warn.append("is_order_overridden")
        is_order = True
    if inj:
        conf = "none"
    return Processed(
        is_order=is_order, is_order_change=ext.is_order_change, product_quote=product_quote,
        quantity=ext.quantity, address_quotes=addr, address_level_raw=level_raw, address_level=level,
        flags=sorted(kept, key=lambda f: FLAG_ORDER.index(f.code)), resolved_flags=resolved,
        tone=tone, tone_reset=tone_reset, tone_evidence=tone_evidence, confirmation=conf,
        language=ext.language, clarity=ext.clarity, dropped_flags=dropped_flags,
        dropped_quotes=dropped_quotes, injection_suspected=inj, spans=spans, warnings=warn,
        verified_flags=verified, address_level_evidence=ext.address_level if addr else "none",
        confirmation_raw=ext.confirmation)
