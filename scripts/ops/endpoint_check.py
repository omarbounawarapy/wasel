#!/usr/bin/env python3
"""Check one endpoint from config/llm.yaml on its own, with the app's real extraction request.

Sends a few golden extraction cases through that endpoint only (no backup steps), so a pass means this endpoint
accepted the strict JSON-schema request, answered in time and produced an extraction the app could validate. Use it
before a live eval on a new provider, e.g. AMD Token Factory:

  python scripts/ops/endpoint_check.py amd-tokenfactory [--cases 3]

Reads the endpoint's variables from the environment or .env. Prints no keys. Exit 0 when every case answered on
path llm, 1 when any case did not, 2 when the endpoint is not active (a variable is missing).
"""
from __future__ import annotations

import argparse
import sys
import time
from dataclasses import replace

from wasel.evaluation.run import load, score_input
from wasel.llm.client import ChainClient
from wasel.llm.prompts import registry
from wasel.llm.routes import StepSpec, build_steps, parse_endpoints, resolve
from wasel.llm.settings import LLMSettings
from wasel.scoring.score_order import score_order


class Recorder:
    """Passes calls to the endpoint's backend and keeps the last error, which the chain itself only counts."""

    def __init__(self, inner):
        self.inner, self.error = inner, None

    def complete_json(self, task, model, user, timeout_s):
        try:
            return self.inner.complete_json(task, model, user, timeout_s)
        except Exception as e:
            self.error = f"{type(e).__name__}: {str(e)[:300]}"
            raise


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("endpoint", help="an endpoint id under `endpoints:` in config/llm.yaml")
    ap.add_argument("--cases", type=int, default=3, help="golden extraction cases to send")
    ap.add_argument("--timeout", type=float, default=30.0, help="seconds per call (first calls can be slow)")
    ap.add_argument("--model", help="model name when the endpoint has no model variable (default: EXTRACT_MODEL)")
    a = ap.parse_args(argv)

    reg = registry()
    eps = parse_endpoints(reg.get("endpoints"))
    if a.endpoint not in eps:
        print(f"no endpoint {a.endpoint!r} in config/llm.yaml (have: {', '.join(eps)})", file=sys.stderr)
        return 2
    spec = eps[a.endpoint]
    cfg = LLMSettings.from_env("live", routing=reg.get("routing"))
    if resolve(spec, cfg) is None:
        names = [*spec.key_envs, spec.base_url_env, spec.model_env, spec.enabled_env]
        print(f"{a.endpoint} is not active: set {', '.join(n for n in names if n)} (environment or .env)",
              file=sys.stderr)
        return 2
    model = "endpoint" if spec.model_env else (a.model or "primary")
    steps = build_steps(cfg, eps, [StepSpec(a.endpoint, "primary", model, a.timeout, None, (), None)])
    rec = Recorder(steps[0].backend)
    llm = ChainClient([replace(steps[0], backend=rec)], deadline_s=a.timeout + 1)
    print(f"endpoint {a.endpoint}: {llm.chain_names[0]}")

    ok = 0
    rows = load("extraction.jsonl", None, a.cases)
    for r in rows:
        t0 = time.monotonic()
        res = score_order(score_input(r["input"]["messages"], r["input"]["price_tnd"]), cache=None, llm=llm,
                          meter=None)
        ms = round((time.monotonic() - t0) * 1000)
        path = res.assessment.path if res.assessment else "none"
        good = path == "llm"
        ok += good
        right = res.is_order == r["expected"]["is_order"]
        print(f"  {'OK  ' if good else 'FAIL'} {r.get('id')}: path={path} {ms} ms"
              + (f" is_order {'matches' if right else 'differs from'} the label" if good else ""))
        if not good and rec.error:
            print(f"       {rec.error}")
        rec.error = None
    print(f"{ok}/{len(rows)} cases answered by {a.endpoint}")
    return 0 if rows and ok == len(rows) else 1


if __name__ == "__main__":
    sys.exit(main())
