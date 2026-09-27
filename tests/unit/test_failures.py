"""Hidden-failure analyzer (failures/): dataset, detectors, recoveries vs failures, grouping, the LLM language
layer (scripted backend, no network) and the app adapter + API."""
from __future__ import annotations

import json

from app.llm.base import CallMeta
from app.llm.client import ChainClient, ChainStep
from failures import dataset
from failures.detect import REPORT_AT, detect
from failures.rank import group
from failures.run import analyze, score
from failures.semantics import LLMSemantics


def test_committed_datasets_match_the_generator():
    assert dataset.load(dataset.OUT) == json.loads(json.dumps(dataset.build(dataset.SEED, "train")))
    assert dataset.load(dataset.OUT_HOLDOUT) == json.loads(json.dumps(dataset.build(dataset.SEED + 1, "holdout")))


def test_rules_on_the_train_phrasing_find_every_planted_failure_and_no_clean_session():
    sessions = dataset.load()
    rep = analyze(sessions)
    acc = score(sessions, rep["_findings"])
    assert acc["micro_precision"] >= 0.95 and acc["micro_recall"] >= 0.95
    assert acc["clean_sessions_flagged"] == 0 and acc["recoveries_flagged"] == []


def test_recoveries_are_not_failures():
    for fn in (dataset.recovery_tool_retry, dataset.recovery_search_refined, dataset.recovery_unclear_answer):
        s = fn(dataset.B("S900", "fr", dataset.CUSTOMERS[0], dataset.PRODUCTS[0], __import__("random").Random(1)))
        assert [f for f in detect(s) if f.confidence >= REPORT_AT] == [], fn.__name__


def test_ambiguous_reminder_goes_to_review_not_failure():
    s = dataset.ambiguous_reminder(dataset.B("S901", "fr", dataset.CUSTOMERS[0], dataset.PRODUCTS[0],
                                             __import__("random").Random(2)))
    fs = detect(s)
    assert fs and all(f.status == "needs_review" for f in fs)


def test_each_finding_points_at_real_events():
    for s in dataset.load()[:60]:
        idx = {e["i"]: e for e in s["events"]}
        for f in detect(s):
            assert f.evidence and all(idx[x["i"]]["type"] == x["type"] for x in f.evidence)


def test_grouping_merges_error_details_and_ranks_failures_first():
    issues = group([f for s in dataset.load() for f in detect(s)], 130)
    claims = [i for i in issues if i["type"] == "unsupported_success_claim" and i["signature"] == "confirm_order failed"]
    assert len(claims) == 1 and len(claims[0]["details"]) >= 2
    statuses = [i["status"] for i in issues]
    assert statuses == sorted(statuses, key=lambda s: s != "failure")
    assert [i["rank"] for i in issues] == list(range(1, len(issues) + 1))


class Labeler:
    """Scripted backend: labels agent texts containing 'validé'/'mriguel' as success claims."""

    def __init__(self):
        self.calls = 0

    def complete_json(self, task, model, user, timeout_s):
        self.calls += 1
        msgs = json.loads(user)["messages"]
        items = [{"id": m["id"], "hedged": "devrait" in m["text"] or "normalement" in m["text"].lower(),
                  "success_claim": m["from"] == "agent" and any(w in m["text"].lower() for w in ("validé", "mriguel")),
                  "asks": "address" if m["from"] == "agent" and "adresse" in m["text"] else "none",
                  "gives_exact_address": m["from"] == "customer" and any(c.isdigit() for c in m["text"]),
                  "confirms_or_declines": False} for m in msgs]
        return json.dumps({"items": items}), CallMeta("groq", model, 5, 10, None, 10)


def test_llm_layer_recovers_claims_the_rules_miss_on_holdout_wording():
    sessions = [s for s in dataset.load(dataset.OUT_HOLDOUT)
                if "unsupported_success_claim" in s["label"]["failures"]][:5]
    rules_hits = {f.session_id for s in sessions for f in detect(s) if f.type == "unsupported_success_claim"}
    backend = Labeler()
    sem = LLMSemantics(ChainClient([ChainStep("primary", "groq", "m", backend, 6)]), sessions)
    llm_hits = {f.session_id for s in sessions for f in detect(s, sem) if f.type == "unsupported_success_claim"
                and f.confidence >= REPORT_AT}
    assert len(llm_hits) > len(rules_hits)
    texts = sem.stats["texts"]
    assert backend.calls == -(-texts // 25)             # one call per batch of unique texts, not per message


def test_llm_layer_falls_back_to_rules_when_the_provider_fails():
    class Down:
        def complete_json(self, *a, **k):
            raise RuntimeError("down")
    sessions = dataset.load()[:20]
    sem = LLMSemantics(ChainClient([ChainStep("primary", "groq", "m", Down(), 6)]), sessions)
    assert sem.stats["labeled"] == 0
    assert [f.to_dict() for s in sessions for f in detect(s, sem)] == \
        [f.to_dict() for s in sessions for f in detect(s)]


def test_api_failures_on_synthetic_and_on_this_app(tmp_path):
    from tests.integration.conftest import make_client
    client, _, _ = make_client(tmp_path)
    with client:
        d = client.get("/api/failures").json()
        assert d["n_sessions"] == 130 and d["issues"] and d["accuracy"]["micro_recall"] >= 0.95
        top = d["issues"][0]["findings"][0]
        s = client.get(f"/api/failures/sessions/{top['session_id']}").json()
        assert s["session"]["session_id"] == top["session_id"] and s["findings"]
        app = client.get("/api/failures", params={"source": "app"}).json()
        assert app["n_sessions"] >= 9 and "accuracy" not in app
        body = json.dumps(app)
        assert "216" not in body                        # no phone numbers in the app sessions
        assert client.get("/api/failures", params={"source": "nope"}).status_code == 400
