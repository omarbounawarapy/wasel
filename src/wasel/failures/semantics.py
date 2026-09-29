"""The language layer of the analyzer: what a message *says* (is it a success claim, is it hedged, what does it ask
for, does a reply answer it). The detectors in detect.py only combine these labels with the session's structure
(tool results, order of events, final status).

RuleSemantics   regexes, FR + Arabizi, zero cost; the default and the fallback.
LLMSemantics    one LLM call per batch of *unique* texts (templates repeat, so a few calls cover a whole dataset),
                through the governed client (failure-label-v1 prompt, strict schema, cache, traces). Any text the LLM
                didn't label falls back to the rules.
"""
from __future__ import annotations

import json
import re
import time

from wasel.clock import SystemClock
from wasel.llm.base import ParseError

CLAIM = re.compile(r"(est confirm[ée]e|commande (?:est )?valid[ée]e|sera livr[ée]e|tconfirmat|tconfirmet|twossl|"
                   r"تم تأكيد|تأكدت|order (?:is )?confirmed|mrigla|c'est bon)", re.I)
HEDGE = re.compile(r"(normalement|probablement|si besoin|on vous recontacte|n3awdou|ken fama|peut-?être|"
                   r"inchallah|je pense)", re.I)
APOLOGY = re.compile(r"(d[ée]sol[ée]|probl[èe]me|samahna|mochkla|sorry|erreur|souci|oups)", re.I)
CONFIRM_ANS = re.compile(r"\b(oui|ey|eyh|nconfirmi|je confirme|c'est bon|behi|confirm[ée]?)\b", re.I)
DECLINE_ANS = re.compile(r"\b(non|le|la|annul|nbatel)\b", re.I)
EXACT_ADDR = re.compile(r"(\b(rue|avenue|av\.?|nahj|boulevard|bd)\b.*\d|\d+.*\b(rue|avenue|nahj)\b|n°\s*\d)", re.I)
TOPIC = [("address", re.compile(r"(adresse|address|nahj|rue|العنوان)", re.I)),
         ("confirm", re.compile(r"(confirm|tconfirmi|تأكد)", re.I))]
BATCH = 25


def is_question(text: str) -> bool:
    return "?" in text or "؟" in text


class RuleSemantics:
    name = "rules"

    def claim(self, text: str) -> tuple[bool, bool]:
        return bool(CLAIM.search(text)), bool(HEDGE.search(text))

    def asks(self, text: str) -> str | None:
        if not is_question(text):
            return None
        return next((name for name, rx in TOPIC if rx.search(text)), None)

    def answers(self, topic: str, text: str) -> bool:
        if topic == "address":
            return bool(EXACT_ADDR.search(text))
        if topic == "confirm":
            return bool(CONFIRM_ANS.search(text) or DECLINE_ANS.search(text))
        return False

    def apology(self, text: str) -> bool:
        return bool(APOLOGY.search(text))


def parse_labels(raw: str) -> list[dict]:
    try:
        j = json.loads(raw)
    except ValueError as e:
        raise ParseError(str(e)[:120]) from e
    if not isinstance(j, dict) or not isinstance(j.get("items"), list):
        raise ParseError("labels json shape")
    return j["items"]


class LLMSemantics(RuleSemantics):
    name = "llm"

    def __init__(self, llm, sessions: list[dict]):
        from wasel.llm.prompts import task
        self.rules = RuleSemantics()
        self.labels: dict[tuple[str, str], dict] = {}
        self.stats = {"calls": 0, "failed_calls": 0, "tokens_in": 0, "tokens_out": 0, "texts": 0, "labeled": 0,
                      "seconds": 0.0, "model": None}
        texts = sorted({(e["type"], e["text"]) for s in sessions for e in s["events"]
                        if e["type"] in ("agent", "user") and e.get("text")})
        self.stats["texts"] = len(texts)
        spec = task("failure_label")
        t0 = time.perf_counter()
        for k in range(0, len(texts), BATCH):
            chunk = texts[k:k + BATCH]
            payload = {"messages": [{"id": i, "from": "agent" if who == "agent" else "customer", "text": t}
                                    for i, (who, t) in enumerate(chunk)]}
            try:
                res = llm.extract(spec, json.dumps(payload, ensure_ascii=False), parse=parse_labels, meter=None,
                                  sandbox_id=None, now=SystemClock().now(), role="failure_label")
            except Exception:                            # noqa: BLE001 - the rules cover whatever isn't labeled
                self.stats["failed_calls"] += 1
                continue
            self.stats["calls"] += 1
            self.stats["tokens_in"] += sum(u.tokens_in or 0 for u in res.usage)
            self.stats["tokens_out"] += sum(u.tokens_out or 0 for u in res.usage)
            if res.parsed is None:
                self.stats["failed_calls"] += 1
                continue
            self.stats["model"] = f"{res.provider}:{res.model}"
            for item in res.parsed:
                i = item.get("id")
                if isinstance(i, int) and 0 <= i < len(chunk):
                    self.labels[chunk[i]] = item
        self.stats["labeled"] = len(self.labels)
        self.stats["seconds"] = round(time.perf_counter() - t0, 2)

    def _get(self, who: str, text: str) -> dict | None:
        return self.labels.get((who, text))

    def claim(self, text: str) -> tuple[bool, bool]:
        lab = self._get("agent", text)
        return (bool(lab["success_claim"]), bool(lab["hedged"])) if lab else self.rules.claim(text)

    def asks(self, text: str) -> str | None:
        lab = self._get("agent", text)
        if lab is None:
            return self.rules.asks(text)
        return lab["asks"] if lab["asks"] in ("address", "confirm") else None

    def answers(self, topic: str, text: str) -> bool:
        lab = self._get("user", text)
        if lab is None:
            return self.rules.answers(topic, text)
        return bool(lab["gives_exact_address"]) if topic == "address" else \
            bool(lab["confirms_or_declines"]) if topic == "confirm" else False
