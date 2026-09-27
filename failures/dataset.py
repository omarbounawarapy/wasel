"""Synthetic, labeled agent sessions for the hidden-failure analyzer: a COD order-confirmation agent that talks to
customers on WhatsApp and calls tools (lookup_customer, get_order, search_address, update_order, confirm_order,
send_message, escalate). Deterministic (seeded): rerunning gives a byte-identical data/agent_sessions.jsonl.

Every session is labeled with the failures planted in it, plus a `kind`:
  success    clean run, nothing to find
  recovery   a tool error or an unclear answer that the agent handled (retry, clarification): NOT a failure
  ambiguous  a judgment call (a reminder after silence, a hedged claim): may be surfaced for review, never counted
  failure    one or more planted failures
Business data only (orders, addresses, tool results). Phones are the allowlisted fakes 21600000001..9.

Two phrasings: `train` (what the detector patterns were written against) and `holdout` (different wording and
addresses, different seed, never used to write a rule) -> data/agent_sessions_holdout.jsonl. The holdout scores
are the honest estimate of how the rules generalise.

  python -m failures.dataset
"""
from __future__ import annotations

import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "agent_sessions.jsonl"
OUT_HOLDOUT = ROOT / "data" / "agent_sessions_holdout.jsonl"
SEED = 20260927

CUSTOMERS = [("C101", "Amira", "21600000001"), ("C102", "Hatem", "21600000002"), ("C103", "Salma", "21600000003"),
             ("C104", "Walid", "21600000004"), ("C105", "Ines", "21600000005"), ("C106", "Karim", "21600000006"),
             ("C107", "Nour", "21600000007"), ("C108", "Sami", "21600000008"), ("C109", "Rim", "21600000009")]
PRODUCTS = [("sac cuir", 89.0), ("montre connectée", 149.0), ("serwel jean", 59.0), ("mlehef", 79.0),
            ("casque bluetooth", 119.0), ("tablette 10 pouces", 450.0)]
EXACT = ["Rue Ibn Khaldoun n°12, Sfax", "nahj el habib bourguiba 7, Sousse", "Avenue de la Liberté 45, Tunis",
         "Rue de Marseille 3, Bizerte", "nahj 9 avril 21, Kairouan"]
VAGUE = ["Sfax", "9rib el jemaa, Sousse", "cité Ennasr", "7ay Haffouz", "Ben Arous"]

TRAIN = {
    "fr": {
        "hello": "Bonjour {name}, ici la boutique. Vous confirmez la commande de {product} à {price} DT ?",
        "ask_address": "Pouvez-vous nous donner l'adresse exacte (rue et numéro) ?",
        "ask_address2": "Merci ! Il nous manque encore l'adresse exacte, rue et numéro s'il vous plaît ?",
        "reask_confirm": "Petit rappel {name} : vous confirmez la commande de {product} ?",
        "claim": "Parfait, votre commande est confirmée et sera livrée demain.",
        "claim_hedged": "Normalement c'est bon, on vous recontacte si besoin.",
        "sorry": "Désolé, un petit problème de notre côté, on revient vers vous.",
        "confirm": ["oui je confirme", "oui c'est bon", "je confirme merci"],
        "unclear": ["ok", "d'accord ?", "c'est quoi exactement ?"],
        "question": "et la livraison c'est combien ?",
    },
    "arabizi": {
        "hello": "Aslema {name}, m3ak el boutique. Tconfirmi el commande mta3 {product} b {price} DT ?",
        "ask_address": "Ta3tina l'adresse bel dhabt (nahj w noumrou) ?",
        "ask_address2": "Y3aychek, ma zelnech na9sin l'adresse bel dhabt, nahj w noumrou ?",
        "reask_confirm": "Nfakrek {name}: tconfirmi el commande mta3 {product} ?",
        "claim": "Behi, el commande tconfirmat, twosslek ghodwa.",
        "claim_hedged": "Normalement mrigla, n3awdou nkalmouk ken fama chay.",
        "sorry": "Samahna, fama mochkla 3andna, nraj3oulek.",
        "confirm": ["ey nconfirmi", "ey behi", "nconfirmi y3aychek"],
        "unclear": ["ok", "chnowa ?", "kifech ?"],
        "question": "w el livraison 9addech ?",
    },
}
HOLDOUT = {
    "fr": {
        "hello": "Salut {name} ! On a bien reçu votre demande pour {product} ({price} DT). On la valide ?",
        "ask_address": "Vous pouvez m'envoyer votre adresse complète ?",
        "ask_address2": "Je n'ai pas bien noté, c'est quoi votre adresse complète ?",
        "reask_confirm": "Toujours partant pour {product} ?",
        "claim": "C'est validé ✅ votre colis part demain matin.",
        "claim_hedged": "Ça devrait être bon, je vérifie et je reviens vers vous.",
        "sorry": "Oups, souci technique, je regarde.",
        "confirm": ["ok ça marche", "oui parfait", "yes"],
        "unclear": ["hmm", "c'est pour quand ?"],
        "question": "vous livrez le samedi ?",
    },
    "arabizi": {
        "hello": "Ahla {name}! Wselna talab mta3ek {product} ({price} DT). Nvalidiwha ?",
        "ask_address": "Ab3athli l'adresse kemla ?",
        "ask_address2": "Ma fhemtch, l'adresse kemla chnowa ?",
        "reask_confirm": "Mazelt t7eb {product} ?",
        "claim": "Mriguel, el colis yo5rej ghodwa sbe7.",
        "claim_hedged": "Normalement mriguel, nthabet w nraja3lek.",
        "sorry": "Famma souci, nchouf.",
        "confirm": ["ey mriguel", "ok ey", "sa7a"],
        "unclear": ["hmm", "emta ?"],
        "question": "tlivriw nhar sebt ?",
    },
}
PHRASES = {"train": (TRAIN, EXACT, VAGUE),
           "holdout": (HOLDOUT, ["12 rue de Rome, Tunis", "cité el khadra bloc 4 app 12", "35 avenue Farhat Hached, Sfax",
                                 "immeuble Yasmine 2e étage, Lac 2", "route de Gabès km 4, Sfax"],
                       ["Tunis", "Lac 2", "près de la poste, Nabeul", "Menzah", "Monastir"])}


class B:
    """Session builder: turns and tool calls on one timeline."""

    def __init__(self, sid: str, lang: str, cust, product, rng: random.Random, phrasing: str = "train"):
        self.rng, self.lang = rng, lang
        table, self.exact, self.vague = PHRASES[phrasing]
        self.T = table[lang]
        self.cid, self.name, self.phone = cust
        self.product, self.price = product
        self.order_id = f"O{sid[1:]}"
        self.t = 0
        self.s = {"session_id": sid, "source": "synthetic", "language": lang,
                  "context": {"channel_phone": self.phone, "order_id": self.order_id},
                  "events": [], "final": {}, "label": {"kind": "success", "failures": []}}

    def _ev(self, **e):
        self.t += self.rng.randint(5, 90)
        e["i"], e["t"] = len(self.s["events"]), self.t
        self.s["events"].append(e)
        return e

    def say(self, key: str, **kw):
        txt = self.T[key]
        return self._ev(type="agent", text=txt.format(name=self.name, product=self.product, price=int(self.price),
                                                      **kw))

    def user(self, text: str):
        return self._ev(type="user", text=text)

    def tool(self, name: str, args: dict, result: dict, ok: bool = True):
        self._ev(type="tool_call", tool=name, args=args)
        return self._ev(type="tool_result", tool=name, ok=ok, result=result)

    def wait(self, seconds: int):
        self.t += seconds

    # common steps ------------------------------------------------------------------------------------
    def start(self, cust=None):
        c = cust or (self.cid, self.name, self.phone)
        self.tool("lookup_customer", {"phone": self.phone},
                  {"customer_id": c[0], "name": c[1], "phone": c[2], "past_orders": self.rng.randint(0, 4)})
        self.tool("get_order", {"order_id": self.order_id},
                  {"order_id": self.order_id, "customer_id": c[0], "product": self.product, "price_tnd": self.price,
                   "address": None})
        self.say("hello")

    def confirm_answer(self):
        self.user(self.rng.choice(self.T["confirm"]))

    def address_exchange(self, address: str):
        self.say("ask_address")
        self.user(address)
        self.tool("search_address", {"query": address}, {"matches": 1, "level": "exact", "normalized": address})
        self.tool("update_order", {"order_id": self.order_id, "customer_id": self.cid, "address": address,
                                   "address_level": "exact"}, {"updated": True})

    def confirm(self, ok: bool = True, error: str | None = None):
        return self.tool("confirm_order", {"order_id": self.order_id},
                         {"status": "confirmed"} if ok else {"error": error or "timeout"}, ok=ok)

    def end(self, status: str, kind: str, failures: list[str] | None = None):
        self.s["final"] = {"status_claimed": status}
        self.s["label"] = {"kind": kind, "failures": sorted(failures or [])}
        return self.s


# ---------------------------------------------------------------- scenarios
def success(b: B):
    b.start()
    b.confirm_answer()
    b.address_exchange(b.rng.choice(b.exact))
    b.confirm()
    b.say("claim")
    return b.end("confirmed", "success")


def success_escalated(b: B):
    """Customer declines a prepayment question -> handed to a person: a correct non-success outcome."""
    b.start()
    b.user("non merci j'annule" if b.lang == "fr" else "le, nbatel")
    b.tool("escalate", {"order_id": b.order_id, "reason": "customer_declined"}, {"ticket": f"TK{b.order_id[1:]}"})
    return b.end("escalated", "success")


def recovery_tool_retry(b: B):
    b.start()
    b.confirm_answer()
    b.address_exchange(b.rng.choice(b.exact))
    b.confirm(ok=False, error="timeout")
    b.confirm()
    b.say("claim")
    return b.end("confirmed", "recovery")


def recovery_search_refined(b: B):
    """Search finds nothing, the agent asks for more, the new query works: progress, not a loop."""
    b.start()
    b.confirm_answer()
    b.say("ask_address")
    vague = b.rng.choice(b.vague)
    b.user(vague)
    b.tool("search_address", {"query": vague}, {"matches": 0}, ok=True)
    b.say("ask_address2")
    exact = b.rng.choice(b.exact)
    b.user(exact)
    b.tool("search_address", {"query": exact}, {"matches": 1, "level": "exact", "normalized": exact})
    b.tool("update_order", {"order_id": b.order_id, "customer_id": b.cid, "address": exact,
                            "address_level": "exact"}, {"updated": True})
    b.confirm()
    b.say("claim")
    return b.end("confirmed", "recovery")


def recovery_unclear_answer(b: B):
    """The customer's reply doesn't answer; re-asking is right."""
    b.start()
    b.user(b.rng.choice(b.T["unclear"]))
    b.say("reask_confirm")
    b.confirm_answer()
    b.address_exchange(b.rng.choice(b.exact))
    b.confirm()
    b.say("claim")
    return b.end("confirmed", "recovery")


def ambiguous_reminder(b: B):
    """No reply for hours, the agent asks again: a reminder, arguably fine."""
    b.start()
    b.wait(6 * 3600)
    b.say("reask_confirm")
    b.confirm_answer()
    b.address_exchange(b.rng.choice(b.exact))
    b.confirm()
    b.say("claim")
    return b.end("confirmed", "ambiguous")


def ambiguous_hedged(b: B):
    """Hedged wording after an escalation: not a success claim, but a reader could take it as one."""
    b.start()
    b.confirm_answer()
    b.address_exchange(b.rng.choice(b.exact))
    b.tool("escalate", {"order_id": b.order_id, "reason": "stock_check"}, {"ticket": f"TK{b.order_id[1:]}"})
    b.say("claim_hedged")
    return b.end("pending", "ambiguous")


def f_unsupported_claim_failed_tool(b: B):
    b.start()
    b.confirm_answer()
    b.address_exchange(b.rng.choice(b.exact))
    b.confirm(ok=False, error=b.rng.choice(["out_of_stock", "timeout", "payment_rule_violation"]))
    b.say("claim")
    return b.end("confirmed", "failure", ["unsupported_success_claim"])


def f_unsupported_claim_no_tool(b: B):
    b.start()
    b.confirm_answer()
    b.address_exchange(b.rng.choice(b.exact))
    b.say("claim")
    return b.end("confirmed", "failure", ["unsupported_success_claim"])


def f_repeated_question(b: B):
    b.start()
    b.confirm_answer()
    addr = b.rng.choice(b.exact)
    b.say("ask_address")
    b.user(addr)
    b.say("ask_address2")                        # the customer already gave street + number
    b.user(addr)
    b.tool("search_address", {"query": addr}, {"matches": 1, "level": "exact", "normalized": addr})
    b.tool("update_order", {"order_id": b.order_id, "customer_id": b.cid, "address": addr, "address_level": "exact"},
           {"updated": True})
    b.confirm()
    b.say("claim")
    return b.end("confirmed", "failure", ["repeated_question"])


def f_no_progress_search(b: B, then_claim: bool = False):
    b.start()
    b.confirm_answer()
    b.say("ask_address")
    vague = b.rng.choice(b.vague)
    b.user(vague)
    for _ in range(b.rng.randint(3, 5)):
        b.tool("search_address", {"query": vague}, {"matches": 0})
    fails = ["no_progress_search"]
    if then_claim:
        b.tool("update_order", {"order_id": b.order_id, "customer_id": b.cid, "address": vague,
                                "address_level": "city_only"}, {"updated": True})
        b.confirm()
        b.say("claim")
        fails.append("incomplete_marked_done")
        return b.end("confirmed", "failure", fails)
    b.tool("escalate", {"order_id": b.order_id, "reason": "address_not_found"}, {"ticket": f"TK{b.order_id[1:]}"})
    return b.end("escalated", "failure", fails)


def f_wrong_customer(b: B):
    other = b.rng.choice([c for c in CUSTOMERS if c[0] != b.cid])
    b.start(cust=other)                           # lookup returned someone else's record; the agent used it
    b.confirm_answer()
    addr = b.rng.choice(b.exact)
    b.say("ask_address")
    b.user(addr)
    b.tool("search_address", {"query": addr}, {"matches": 1, "level": "exact", "normalized": addr})
    b.tool("update_order", {"order_id": b.order_id, "customer_id": other[0], "address": addr,
                            "address_level": "exact"}, {"updated": True})
    b.confirm()
    b.say("claim")
    return b.end("confirmed", "failure", ["wrong_customer_record"])


def f_incomplete_vague_address(b: B):
    b.start()
    b.confirm_answer()
    b.say("ask_address")
    vague = b.rng.choice(b.vague)
    b.user(vague)
    b.tool("search_address", {"query": vague}, {"matches": 3, "level": "city_only", "normalized": vague})
    b.tool("update_order", {"order_id": b.order_id, "customer_id": b.cid, "address": vague,
                            "address_level": "city_only"}, {"updated": True})
    b.confirm()
    b.say("claim")
    return b.end("confirmed", "failure", ["incomplete_marked_done"])


def f_incomplete_unanswered_question(b: B):
    b.start()
    b.confirm_answer()
    addr = b.rng.choice(b.exact)
    b.say("ask_address")
    b.user(addr + ". " + b.T["question"])
    b.tool("search_address", {"query": addr}, {"matches": 1, "level": "exact", "normalized": addr})
    b.tool("update_order", {"order_id": b.order_id, "customer_id": b.cid, "address": addr, "address_level": "exact"},
           {"updated": True})
    b.confirm()
    b.say("claim")                                # never answered the delivery-fee question
    return b.end("confirmed", "failure", ["incomplete_marked_done"])


def f_tool_error_ignored(b: B):
    b.start()
    b.confirm_answer()
    addr = b.rng.choice(b.exact)
    b.say("ask_address")
    b.user(addr)
    b.tool("search_address", {"query": addr}, {"matches": 1, "level": "exact", "normalized": addr})
    b.tool("update_order", {"order_id": b.order_id, "customer_id": b.cid, "address": addr, "address_level": "exact"},
           {"error": "db_locked"}, ok=False)      # the address was never saved
    b.tool("send_message", {"to": b.phone, "template": "T_ACK"}, {"sent": True})
    return b.end("awaiting_delivery", "failure", ["tool_error_ignored"])


def f_claim_and_repeat(b: B):
    """Two failures in one session."""
    b.start()
    b.confirm_answer()
    addr = b.rng.choice(b.exact)
    b.say("ask_address")
    b.user(addr)
    b.say("ask_address2")
    b.user(addr)
    b.say("claim")
    return b.end("confirmed", "failure", ["repeated_question", "unsupported_success_claim"])


PLAN = [(success, 30), (success_escalated, 6), (recovery_tool_retry, 10), (recovery_search_refined, 8),
        (recovery_unclear_answer, 8), (ambiguous_reminder, 7), (ambiguous_hedged, 5),
        (f_unsupported_claim_failed_tool, 8), (f_unsupported_claim_no_tool, 5), (f_repeated_question, 8),
        (f_no_progress_search, 6), (lambda b: f_no_progress_search(b, then_claim=True), 3), (f_wrong_customer, 6),
        (f_incomplete_vague_address, 6), (f_incomplete_unanswered_question, 4), (f_tool_error_ignored, 6),
        (f_claim_and_repeat, 4)]


def build(seed: int = SEED, phrasing: str = "train") -> list[dict]:
    rng = random.Random(seed)
    jobs = [fn for fn, n in PLAN for _ in range(n)]
    rng.shuffle(jobs)
    out = []
    for k, fn in enumerate(jobs, start=1):
        sid = f"{'S' if phrasing == 'train' else 'H'}{k:03d}"
        b = B(sid, rng.choice(["fr", "arabizi"]), rng.choice(CUSTOMERS), rng.choice(PRODUCTS),
              random.Random(seed * 1000 + k), phrasing)
        out.append(fn(b))
    return out


def write(path: Path = OUT, phrasing: str = "train", seed: int = SEED) -> int:
    rows = build(seed, phrasing)
    path.write_text("".join(json.dumps(s, ensure_ascii=False, sort_keys=True) + "\n" for s in rows), encoding="utf-8")
    return len(rows)


def load(path: Path = OUT) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


if __name__ == "__main__":
    for path, phrasing, seed in ((OUT, "train", SEED), (OUT_HOLDOUT, "holdout", SEED + 1)):
        print(f"wrote {write(path, phrasing, seed)} sessions -> {path.relative_to(ROOT)}")
