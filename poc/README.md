# COD Risk — reference prototype (`poc/`)

This folder mirrors the repo tree in `docs/council-spec/01-architecture-contracts.md` §1, so any file here can be
promoted to the repo root by its owner with `git mv poc/<path> <path>`. The council spec is canonical; where this
code deviates, `handoff.md` says where and why.

**Status and phase plan: see [`handoff.md`](handoff.md).**

```bash
cd poc
pip install -r requirements.txt -r requirements-dev.txt
python -m ml.generate      # 10,000 synthetic rows, zero LLM calls, lints 1–8
python -m ml.train         # monotone XGBoost + card + reports + tests/golden/hero.json (gates enforced)
python -m pytest           # offline, keyless
```

Synthetic data only. No real customer data is in this folder.
