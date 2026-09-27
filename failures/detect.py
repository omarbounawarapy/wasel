"""Deterministic detectors: one function per failure type, each returning findings with evidence pointers (event
index + the text or tool result) and a confidence. They look for what an agent run can get wrong without any
technical error, and they tell recoveries (a retry that worked, a clarification after an unclear answer) apart
from failures.

Confidence bands: >= 0.6 reported as a failure; 0.35-0.6 "needs review" (ambiguous); lower is dropped.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

from failures.semantics import RuleSemantics, is_question
from ml.textnorm import normalize

REPORT_AT, REVIEW_AT = 0.6, 0.35

DONE = {"confirmed", "ready", "ready_to_ship", "awaiting_delivery", "shipped"}
SEVERITY = {"unsupported_success_claim": 1.0, "wrong_customer_record": 1.0, "incomplete_marked_done": 0.8,
            "tool_error_ignored": 0.7, "no_progress_search": 0.5, "repeated_question": 0.4}
WHY = {"unsupported_success_claim": "The agent told the customer it succeeded, but no successful tool call backs it.",
       "wrong_customer_record": "A tool returned another customer's record and the agent kept using it.",
       "incomplete_marked_done": "The session was closed as done while something the order needs was missing.",
       "tool_error_ignored": "A tool failed and the agent carried on as if it had worked.",
       "no_progress_search": "The same search was repeated with the same input and no new result.",
       "repeated_question": "The agent asked again for something the customer had already given."}


@dataclass
class Finding:
    type: str
    session_id: str
    confidence: float
    signature: str                        # what groups findings into one issue (tool, error, topic...)
    summary: str
    evidence: list[dict] = field(default_factory=list)

    @property
    def status(self) -> str:
        return "failure" if self.confidence >= REPORT_AT else "needs_review"

    def to_dict(self) -> dict:
        return {**asdict(self), "status": self.status}


def ev(e: dict) -> dict:
    """Evidence pointer: index, kind and the part that matters (text, or tool + args/result)."""
    out = {"i": e["i"], "type": e["type"]}
    for k in ("text", "tool", "args", "result", "ok"):
        if k in e:
            out[k] = e[k]
    return out


def results(s: dict, tool: str | None = None) -> list[dict]:
    return [e for e in s["events"] if e["type"] == "tool_result" and (tool is None or e["tool"] == tool)]


# ---------------------------------------------------------------- detectors
def unsupported_success_claim(s: dict, sem) -> list[Finding]:
    out = []
    for e in s["events"]:
        if e["type"] != "agent":
            continue
        is_claim, hedged = sem.claim(e["text"])
        if not is_claim:
            continue
        before = [r for r in results(s, "confirm_order") if r["i"] < e["i"]]
        if before and before[-1]["ok"]:
            continue
        if before:                                       # the last confirm attempt failed
            err = before[-1]["result"].get("error", "error")
            out.append(Finding("unsupported_success_claim", s["session_id"], 0.45 if hedged else 0.92,
                               f"confirm_order failed ({err})", f"Claimed success after confirm_order returned {err}",
                               [ev(before[-1]), ev(e)]))
        else:
            escalated = [r for r in results(s, "escalate") if r["i"] < e["i"]]
            conf = 0.3 if (hedged and escalated) else 0.45 if hedged else 0.85
            out.append(Finding("unsupported_success_claim", s["session_id"], conf, "confirm_order never called",
                               "Claimed success without ever calling confirm_order",
                               [*(ev(r) for r in escalated), ev(e)]))
    return out


def repeated_question(s: dict, sem) -> list[Finding]:
    out, asked = [], {}
    evs = s["events"]
    for e in evs:
        if e["type"] != "agent":
            continue
        tp = sem.asks(e["text"])
        if tp is None:
            continue
        if tp in asked:
            prev = asked[tp]
            between = [x for x in evs if prev["i"] < x["i"] < e["i"] and x["type"] == "user"]
            answered = [x for x in between if sem.answers(tp, x["text"])]
            if answered:
                out.append(Finding("repeated_question", s["session_id"], 0.88, f"asked again: {tp}",
                                   f"Asked for the {tp} again after the customer had given it",
                                   [ev(prev), ev(answered[0]), ev(e)]))
            elif not between:                            # a reminder after silence: arguably fine
                gap = e["t"] - prev["t"]
                out.append(Finding("repeated_question", s["session_id"], 0.4 if gap > 3600 else 0.65,
                                   f"asked again: {tp}", f"Asked for the {tp} twice with no reply in between "
                                   f"({gap // 60} min apart)", [ev(prev), ev(e)]))
            # a user turn that doesn't answer -> re-asking is a clarification, not a failure
        asked[tp] = e
    return out


def no_progress_search(s: dict) -> list[Finding]:
    out = []
    calls = [e for e in s["events"] if e["type"] == "tool_call" and e["tool"].startswith("search")]
    runs: dict[tuple, list[dict]] = {}
    for c in calls:
        key = (c["tool"], normalize(str(sorted(c["args"].items()))))
        res = next((r for r in s["events"] if r["i"] == c["i"] + 1), None)
        empty = res is None or not res.get("ok") or not (res.get("result") or {}).get("matches")
        if empty:
            runs.setdefault(key, []).append(res or c)
        else:
            runs.pop(key, None)                          # the same query eventually worked
    for (tool, _), rs in runs.items():
        if len(rs) >= 3:
            out.append(Finding("no_progress_search", s["session_id"], min(0.95, 0.6 + 0.1 * len(rs)),
                               f"{tool}: same query, no results", f"{tool} called {len(rs)}x with the same input, "
                               "no results, nothing changed in between", [ev(r) for r in rs[:4]]))
        elif len(rs) == 2:
            out.append(Finding("no_progress_search", s["session_id"], 0.4, f"{tool}: same query, no results",
                               f"{tool} called twice with the same input and no results", [ev(r) for r in rs]))
    return out


def wrong_customer_record(s: dict) -> list[Finding]:
    phone = (s.get("context") or {}).get("channel_phone")
    out = []
    if not phone:
        return out
    for r in results(s):
        got = (r.get("result") or {})
        if r["tool"] == "lookup_customer" and got.get("phone") and got["phone"] != phone:
            wrong = got.get("customer_id")
            used = [c for c in s["events"] if c["type"] == "tool_call" and c["i"] > r["i"]
                    and wrong in {str(v) for v in c["args"].values()}]
            out.append(Finding("wrong_customer_record", s["session_id"], 0.93 if used else 0.5,
                               "lookup_customer returned another customer",
                               f"Chat is from {phone[-4:]}, lookup returned customer {wrong} ({got['phone'][-4:]})"
                               + (f", then used in {used[0]['tool']}" if used else ""),
                               [ev(r), *(ev(c) for c in used[:2])]))
    return out


def incomplete_marked_done(s: dict) -> list[Finding]:
    if s.get("final", {}).get("status_claimed") not in DONE:
        return []
    out = []
    updates = [e for e in s["events"] if e["type"] == "tool_call" and e["tool"] == "update_order"
               and "address_level" in e["args"]]
    level = updates[-1]["args"]["address_level"] if updates else None
    if level is not None and level not in ("exact", "street_and_landmark"):
        out.append(Finding("incomplete_marked_done", s["session_id"], 0.85, "closed with an imprecise address",
                           f"Closed as {s['final']['status_claimed']} with address level '{level}'",
                           [ev(updates[-1])]))
    users = [e for e in s["events"] if e["type"] == "user"]
    if users and is_question(users[-1]["text"]):
        q = users[-1]
        replies = [e for e in s["events"] if e["type"] == "agent" and e["i"] > q["i"]]
        key = [w for w in normalize(q["text"]).split() if len(w) > 4]
        if not any(any(w in normalize(r["text"]) for w in key) for r in replies):
            out.append(Finding("incomplete_marked_done", s["session_id"], 0.7, "customer question left unanswered",
                               "The customer's last question was never answered before closing",
                               [ev(q), *(ev(r) for r in replies[-1:])]))
    return out


def tool_error_ignored(s: dict, claimed: set[int], sem) -> list[Finding]:
    """`claimed`: failed results already used as evidence of an unsupported success claim (one finding per fact)."""
    out, evs = [], s["events"]
    for r in results(s):
        if r["ok"] or r["i"] in claimed:
            continue
        nxt = [e for e in evs if e["i"] > r["i"] and e["type"] in ("tool_call", "agent")][:1]
        if not nxt:
            continue
        n = nxt[0]
        handled = (n["type"] == "tool_call" and n["tool"] in (r["tool"], "escalate")) or \
                  (n["type"] == "agent" and sem.apology(n["text"]))
        if not handled:
            out.append(Finding("tool_error_ignored", s["session_id"], 0.8,
                               f"{r['tool']} failed ({(r.get('result') or {}).get('error', 'error')})",
                               f"{r['tool']} failed and the next step was {n.get('tool') or 'a message'}",
                               [ev(r), ev(n)]))
    return out


def detect(s: dict, sem=None) -> list[Finding]:
    sem = sem or RuleSemantics()
    claims = unsupported_success_claim(s, sem)
    used = {x["i"] for f in claims for x in f.evidence if x["type"] == "tool_result"}
    found = (claims + repeated_question(s, sem) + no_progress_search(s) + wrong_customer_record(s)
             + incomplete_marked_done(s) + tool_error_ignored(s, used, sem))
    return [f for f in found if f.confidence >= REVIEW_AT]
