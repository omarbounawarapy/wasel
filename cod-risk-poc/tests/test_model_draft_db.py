import json

import pipeline
from pipeline import config, db
from pipeline.draft import TEMPLATES, generate, template
from pipeline.guards import check
from pipeline.llm import LLMError
from pipeline.model import load
from pipeline.schemas import Score

from conftest import FakeClient


def test_holdout_refusal_rate_is_ordered_by_tier():
    _, meta = load()
    t = meta["holdout_per_tier"]
    assert t["High"]["refusal_rate"] > t["Med"]["refusal_rate"] > t["Low"]["refusal_rate"]


def test_contributions_explain_the_score(order):
    """pred_contribs + bias must add up to the model's log-odds: the bars on screen are the real reason."""
    import math
    import numpy as np
    import xgboost as xgb
    booster, _ = load()
    s, feats = pipeline.score(order, pipeline.extract(order["address_text"], order["note_text"], None).flags)
    dm = xgb.DMatrix(np.array([[feats[k] for k in pipeline.features.FEATURES]]),
                     feature_names=pipeline.features.FEATURES)
    bias = booster.predict(dm, pred_contribs=True)[0][-1]
    logit = sum(s.contribs.values()) + bias
    assert math.isclose(1 / (1 + math.exp(-logit)), s.score, rel_tol=1e-4)


def test_every_static_template_passes_guards():
    o = {"order_id": "X", "product_category": "fashion", "value_tnd": 149.5, "item_count": 2}
    for action, regs in TEMPLATES.items():
        for reg in regs:
            assert check(template(action, reg, o), o, action).approved, (action, reg)


def _score(tier="High", action="confirm_sms_landmark"):
    return Score(score=0.8, tier=tier, contribs={}, action=action, explanation="")


APPROVE = {"checks": {"grounded": True, "register_match": True, "no_overreach": True, "actionable": True},
           "reason": "ok"}
REJECT = {"checks": {"grounded": False, "register_match": True, "no_overreach": True, "actionable": True},
          "reason": "mentions a delivery date not in the order"}


def test_no_draft_for_low_risk(order):
    assert generate(order, None, _score("Low", "ship"), None) is None


def test_offline_draft_is_static_template_and_logged(conn, order):
    d = generate(order, None, _score(), None, conn)
    assert d.source == "static_template" and d.sendable
    assert db.judge_log(conn)[0]["source"] == "static_template"


def test_llm_draft_approved_by_judge(conn, order):
    fake = FakeClient([{"message": "Aslema, commande electronics 210 DT hadhra. Ab3athelna esm el nahj, EYH?"},
                       APPROVE])
    d = generate(order, None, _score(), fake, conn)
    assert d.source == "llm" and d.verdict.approved and d.sendable and d.attempts == 1


def test_judge_rejects_twice_falls_back_to_template(conn, order):
    msg = {"message": "Commande 210 DT, livraison demain matin. OUI?"}
    fake = FakeClient([msg, REJECT, msg, REJECT])
    d = generate(order, None, _score(), fake, conn)
    assert d.source == "static_template" and d.attempts == 2
    assert "rejected twice" in d.verdict.reason
    assert json.loads(fake.calls[2][1])["previous_rejection"] == REJECT["reason"]  # reason fed back


def test_guards_catch_discount_before_the_judge(conn, order):
    fake = FakeClient([{"message": "Remise de 20% si vous confirmez!"},
                       {"message": "Commande 210 DT prête. Ab3athelna esm el nahj, EYH?"}, APPROVE])
    d = generate(order, None, _score(), fake, conn)
    assert d.source == "llm" and d.attempts == 2
    assert db.judge_log(conn)[-1]["source"] == "guards"  # oldest entry = the guard rejection


def test_judge_down_never_fails_open(conn, order):
    fake = FakeClient([{"message": "Commande 210 DT prête. EYH?"}, LLMError("timeout")])
    d = generate(order, None, _score(), fake, conn)
    assert d.source == "static_template"
    assert any(x["source"] == "unavailable" and not x["approved"] for x in db.judge_log(conn))


def test_judge_approval_comes_from_checks_not_model_claim(conn, order):
    lying = {"approved": True, **REJECT}
    msg = {"message": "Commande 210 DT prête. EYH?"}
    d = generate(order, None, _score(), FakeClient([msg, lying, msg, lying]), conn)
    assert d.source == "static_template"


def test_no_duplicate_sends(conn, order):
    assert db.send_message(conn, "T-1", "confirm_sms", "hello", "llm")
    assert not db.send_message(conn, "T-1", "confirm_sms", "hello again", "llm")
    assert len(db.sent_messages(conn, "T-1")) == 1
