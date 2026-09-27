# NVIDIA Brev $100 credit — utilization plan

Status: proposal (not yet executed). Written 2026-09-27, demo day.
Credit: ~$100 on NVIDIA Brev (brev.nvidia.com). Brev rates are dynamic (shown per
instance card before launch); market benchmarks used below: L4/A10G ≈ $0.2–1.0/hr,
A100-80GB ≈ $0.8–3.7/hr, H100 ≈ $1.4+/hr.

## TL;DR

The repo has **zero native GPU work** — its models are a tiny CPU XGBoost and a
TF-IDF guard; everything "AI" is remote Groq/Gemini. That is exactly why the credit
is useful: **host the LLM layer ourselves on a Brev GPU** and four real problems
fall at once:

1. **P0 — demo-day insurance + unthrottled evals** (gpt-oss-20b on L4/A10G, ~$5–12).
2. **P1 — model/prompt sweeps at full speed** (gpt-oss-120b on A100/H100, ~$12–30).
3. **P2a — fix the one red gate with a fine-tune** (extractor LoRA or distillation,
   ~$18–35). This is the "use another model" direction, and it is the right one —
   but aimed at the *extractor*, not the XGBoost.
4. **P2b/P3 — richer simulator + Darija phrase-bank v3** (LLM-generated data
   diversity, ~$10–25).

**Checked and rejected: GPU XGBoost fine-tuning.** Receipts in §P2b — the model is
already at its theoretical ceiling (`reports/train_metrics.json`: AUC 0.7844 ≥
oracle AUC 0.7832) and trains in seconds on CPU. There is no headroom to buy.

The constraint is our time, not the credit: $100 at L4 rates is >100 GPU-hours.
Plan lands at roughly $60–100 with teardown discipline; leftover rolls into the
post-hackathon hosted stack.

---

## Why GPU at all (grounded in today's repo state)

| Pain | Evidence | GPU fix |
|---|---|---|
| `make eval-live` takes ~1 h, throttled by Groq free tier | `reports/eval_live.json`: 3566 s, 72 extract + 75 judge requests, code sleeps via `paced()` in `eval/run.py` | Self-hosted vLLM batches the same ~372K tokens in minutes, no pace limit |
| Groq daily caps threaten the live demo | 1,000 req/day, 8K tok/min per model (STATUS.md) | Flip `GROQ_BASE_URL` to the Brev endpoint → same request shape, no quota |
| One red gate: `extraction.is_order_acc` 0.875 < 0.95 | `reports/eval_live.json` | Only fixable by prompt/model/data work → needs many cheap eval runs → GPU |
| Judge false-blocked 3 safe drafts | `reports/eval_live.json` | Judge threshold/prompt sweep, minutes per iteration on GPU vs 1 h on Groq |
| No hosting (STATUS O-3 open) | demo runs locally via cloudflared tunnel | The P0 box can also run the demo container → one instance closes O-3 |

Integration is a ~3-line patch, not a rewrite: `app/llm/groq_backend.py` is already
an OpenAI-compatible httpx client; `GROQ_BASE_URL` is a module constant
(`app/llm/groq_backend.py:27`) and the model is already env-overridable
(`EXTRACT_MODEL`, `app/llm/client.py:265`; also `config/llm.yaml` routing).

---

## P0 — Demo insurance + unthrottled evals (today, ~$5–12)

**Instance:** L4 or A10G 24 GB (gpt-oss-20b is MXFP4, ~12 GB weights — fits with
room for KV cache). Rate ≈ $0.4–1.0/hr.

```bash
vllm serve openai/gpt-oss-20b --port 8001        # keep 8000 free for uvicorn
```

Uses, in order of value:

1. **Demo insurance.** If Groq hits its daily cap mid-demo (judges like clicking),
   set `GROQ_BASE_URL=http://<brev-host>:8001/v1` and `EXTRACT_MODEL=openai/gpt-oss-20b`.
   Same model family as the Groq primary → prompts behave the same. No code rewrite.
2. **Fast eval-live.** Same golden sets, no `--pace`, run in minutes → iterate.
3. **Optional:** run the demo stack (uvicorn + dashboard Docker + cloudflared) on the
   same box → closes STATUS O-3 with hours that are already burning.

Security: start vLLM with `--api-key <token>` and never expose it keyless via the
tunnel; reuse the cloudflared pattern from `scripts/wa_webhook_up.sh`.

## P1 — Prompt/model sweeps at full speed (~$12–30)

**Instance:** A100-80GB (tight, ~63 GB weights, `--gpu-memory-utilization 0.95`) or
H100 (comfortable). Rate ≈ $1.5–3.5/hr.

```bash
vllm serve openai/gpt-oss-120b --port 8001
# then: EXTRACT_MODEL=openai/gpt-oss-120b make eval-live   (no --pace)
```

Sweep `prompts/extract_v1` variants (5–10 candidates × 476 golden cases + the 24
`eval/sets/g1.jsonl` conversations) and the judge threshold grid
(`app/outbound/judge.py`) in an afternoon instead of one throttled run per day.
Promote winners as sha256-locked `extract_v2` / `judge_v3`.

## P2a — "Another model" done right: fix the extraction gate (~$18–35)

The red gate is **upstream of the XGBoost**: `extraction.is_order_acc` 0.875 vs
0.95 gate. Extraction errors poison every downstream feature, so this is the
highest-leverage model upgrade in the product. Two GPU shapes:

- **LoRA fine-tune gpt-oss-20b for Darija extraction** (TRL/PEFT or Unsloth; LoRA
  on the MXFP4 base fits 24 GB; use A100 for comfort). Train on the deterministic
  generator's own output (`data/phrase_banks.yaml` + `eval/sets/g1.jsonl` +
  `eval/build_golden.py`), serve the merged adapter with vLLM on the P0 box.
- **Distill to a small student**: teacher = GPU-hosted gpt-oss-120b labeling a large
  synthetic message set; student = compact encoder fine-tuned on GPU that emits the
  extracted fields directly from text. Payoff beyond the gate: scoring-path latency
  drops from p95 ≈ 1.8 s (LLM) to milliseconds, and the demo no longer depends on
  any API.

**Artifact discipline — fine-tune once on Brev, serve the artifact everywhere:**

- Fine-tuning is a one-time job, rerun only when data/prompts change (e.g., new phrase-bank
  cells land). It never happens at deploy time.
- The output is an artifact: a LoRA adapter (tens of MB on the unchanged base
  `openai/gpt-oss-20b`) or, for simplicity, the adapter merged into full weights.
- Every host serves the same artifact. With vLLM:
  `vllm serve openai/gpt-oss-20b --api-key $TOKEN --enable-lora
  --lora-modules extract-v1=/path/to/adapter` — or serve the merged directory like
  any model. Via the run kit: `VLLM_ARGS="--enable-lora
  --lora-modules extract-v1=$PWD/models/extract_lora_v1" bash scripts/brev_llm_up.sh serve`
  (20b + adapter still fits a 24 GB L4), then `EXTRACT_MODEL=extract-v1` on the app side.
- Per host, the only things that ever change: the GPU/VRAM class and the env vars
  (`GROQ_BASE_URL`, `EXTRACT_MODEL`) — the app side is env-driven since P1.
- Provenance: commit the adapter (or attach as a release asset if too big) with a model
  card + sha256 — same discipline as `models/risk_xgb_v1.json` + `.card.json`. Version it
  (`extract_lora_v1` → `v2`), keep the previous version for rollback.
- After swapping the served artifact, re-record the extraction cache
  (`scripts/warm_cache.py`, `LIVE=1`, against the fine-tuned server) so offline replay
  matches live behavior.

Methodological trap to avoid (we are judgeable on this): the training text is
generated from the same phrase bank as the eval cases, so a fine-tune can
regurgitate surface forms. Mitigate by paraphrase-expanding the phrase bank with the
GPU model (see P3) and holding out whole bank cells before training. Measure with
the unchanged `eval/` gates — same thresholds, same golden sets.

## P2b — Checked and rejected: GPU XGBoost fine-tuning (and the legit version)

**Why it's a dead end (receipts):**

- `reports/train_metrics.json`: **AUC 0.7844, oracle AUC 0.7832; Brier 0.1619 vs
  oracle 0.1623.** The model already matches or beats the Bayes-optimal score
  attainable from its 6 features (`ml/features.py`: address_specificity,
  red_flag_count, tone_score, price_tnd, zone_encoded, customer_refusal_rate).
- The model card says it outright: *"The model class matches the prior (additive in
  log-odds), so depth 2 and no tuning."*
- `make train` fits 400 depth-2 trees on 8,000 rows in seconds on CPU
  (`tree_method="hist"`, `n_jobs=1`). A full Optuna sweep is CPU-minutes.

So more compute buys exactly nothing: the ceiling is the **information content of
the features + the label prior**, not the model class, and not the hardware. Same
conclusion for CatBoost/LightGBM swaps.

**The legitimate version of the same instinct — change the information, not the
solver:**

1. **Simulator v2 (CPU + a little GPU):** the current labels come from an additive
   logistic prior (`ml/features.py` `S()`, `p_true()`). Add documented interaction
   terms / segment heterogeneity, regenerate `synth_v2.csv` — *then* model class and
   tuning start to matter again, and the `auc ≥ oracle − 0.03` gate becomes a real
   test. Note honestly: the tuning itself is still CPU work; GPU only helps generate
   the more diverse text.
2. **Text→risk side-feature (the GPU part):** fine-tune a small Darija/Arabic
   encoder (candidates to check on HF: XLM-R as the safe default; DarijaBERT is
   Moroccan — look for TunBERT-class Tunisian models) on synthetic message→refusal
   pairs and feed its score into the XGBoost as a 7th feature. On purely synthetic
   text it will partially saturate at the same prior — its real value is robustness
   to upstream extraction errors and to real Darija phrasing, which is the post-
   hackathon story to tell.

## P3 — Data expansion + judge sweep (~$5–12)

- **Phrase bank v3:** batch-generate Darija/Arabizi/French paraphrases per cell of
  `data/phrase_banks.yaml` (14 cells × 3 langs) with the hosted 120b — minutes of
  GPU, zero Groq tokens → `make generate` → retrain guard + XGBoost offline →
  `make eval`. Feeds P2a's anti-regurgitation holdout too.
- **Judge sweep** from P1 if not already done: `judge_v2` false-blocked 3 safe
  drafts; grid prompt × threshold against golden `outbound.jsonl`.

## What NOT to spend on

- **GPU XGBoost / GBM swaps** — §P2b: at oracle ceiling, CPU-seconds.
- **Hosting Streamlit/uvicorn on a dedicated Brev box** — CPU-idle burns the same
  credit as GPU-idle; only host on Brev as the P0 combo box.
- **Embeddings / vector DB** — no retrieval anywhere in the design; scope creep.
- **`make generate` on GPU** — it is deterministic seeded rendering, CPU by design.

---

## Budget

| Track | Instance | Est. rate | Hours | Cost |
|---|---|---|---|---|
| P0 demo insurance + fast evals | L4/A10G 24 GB | $0.4–1.0 | 8–12 | $5–12 |
| P1 120b prompt/judge sweeps | A100-80GB / H100 | $1.5–3.5 | 6–10 | $12–30 |
| P2a extractor LoRA / distill | A100/H100 train + L4 serve | — | 8–14 | $18–35 |
| P2b simulator v2 + text encoder (opt.) | L4 + A100 | — | 4–8 | $5–15 |
| P3 phrase bank v3 + judge sweep | L4 | $0.4–1.0 | 6–12 | $5–12 |
| Buffer (warm-up, failed launches) | | | | $5–10 |

Drops if time runs short, in order: P2b → P3 → P1. Keep to the end: P0, P2a.
Leftover credit rolls into the post-hackathon hosted stack (one L4 running vLLM
+ the demo container is the whole product, self-hosted).

## Phases on branch `brev` (execution order)

**Phase 0 — self-hosted backend switch — DONE (committed)**
`GROQ_BASE_URL` env override (explicit arg > env > Groq, read at call time), the Groq-only
`reasoning_format` field dropped automatically for self-hosted endpoints, routing unit
tests (`tests/unit/test_groq_backend_routing.py`), `.env.example` documented. Nothing in
`app/` hardcodes Groq anymore.

**Phase 1 — instance tooling — CODED, commit pending (working tree of `brev`)**
`scripts/brev_llm_up.sh` (`serve` / `check` / `stop`), `make brev-serve` / `make
brev-check`, teammate guide `docs/brev-live-test.md`. Exit criteria: one 24 GB instance
up, `make brev-check` green from the laptop, one unpaced `eval.run --live` baseline on
20b recorded next to `reports/eval_live.json`. Cost ≈ $5–12.

**Phase 2 — extraction fix factory (G3b / O-14) — NOT STARTED ($10–25)**
1. Phrase-bank cells for the failure class: availability / delivery-window replies
   ("ghodwa ba3d 17h nkoun fi dar"), price-hesitation variants — plus held-out cells so
   eval cases never double as training text.
2. 120b on an 80 GB card paraphrase-expands those cells into training-scale data.
3. Unpaced prompt sweeps → `extract_v2`; LoRA on 20b only if prompts plateau.
Exit: `extraction.is_order_acc ≥ 0.95`, the hero lands 11–16 and quotes the v2 address.

**Phase 3 — fine-tune once, ship the artifact — follows Phase 2 if needed ($18–35)**
Train the LoRA once on Brev; export the adapter with a model card + sha256 (same
discipline as `models/risk_xgb_v1.json.card.json`); every host afterwards serves the
artifact (`vllm serve … --lora-modules extract=…`, or merged weights). Never retrain
per host — retraining happens only when phrase-bank/prompt data changes, always on
Brev, and bumps the artifact version with the previous one kept for rollback.
Re-record the extraction cache from the fine-tuned server (closes O-6 with correct
provenance).

**Phase 4 — optional spend — ONLY IF CREDIT AND TIME REMAIN ($10–20)**
S-11 text baseline (Darija encoder fine-tune), S-6 cascade test locally (20b first,
escalate on uncertainty), O-11 seed conversations drafted on-GPU for human curation.
Explicitly excluded: O-1 fairness XFAIL (a decision, not compute — never tune the model
to pass it) and O-2 spec conflicts (13 decisions, not workloads).

Teardown discipline applies to every phase: `bash scripts/brev_llm_up.sh stop` on the
instance, then `brev stop` in the console — credit burns only while the instance runs.

## Runbook

1. **Launch:** brev.nvidia.com (launchables) or Brev CLI; pick the GPU, note the
   card rate. On Blackwell GPUs use the official vLLM container (correct kernels);
   on L4/A100 plain `pip install vllm` is fine.
2. **Serve:** `vllm serve openai/gpt-oss-20b|120b --port 8001 --api-key $TOKEN`.
3. ~~**3-line app patch**~~ **done (P1)**: `groq_backend()` now resolves explicit arg >
   `GROQ_BASE_URL` env > Groq default, read at call time; unit-tested in
   `tests/unit/test_groq_backend_routing.py`. Model already env-driven via
   `EXTRACT_MODEL` / `config/llm.yaml`.
4. ~~**[VERIFY] reasoning kwargs**~~ **handled (P1)**: for self-hosted URLs the Groq-only
   `reasoning_format` field is dropped automatically (`SELFHOST_REASONING_KWARGS`);
   `reasoning_effort=low` is kept (vLLM honors it for gpt-oss).
5. **Eval:** `GROQ_BASE_URL=… EXTRACT_MODEL=openai/gpt-oss-20b .venv/bin/python -m
   eval.run --live` without pacing (add `--sample 279` for the full extraction set);
   compare against `reports/eval_live.json` baselines. Instance/laptop runbook:
   `docs/brev-live-test.md` (`make brev-serve` / `make brev-check`).
6. **Teardown discipline:** `brev stop` the instance the moment a session ends —
   credit burns while running, not while stopped. The planned spend assumes ~40
   running GPU-hours total; leaving one H100 idling over a weekend burns a third of
   the credit.

## Sources

- NVIDIA Brev launchables: https://brev.nvidia.com (e.g. Nemotron vLLM deploy
  launchable: https://brev.nvidia.com/launchable/deploy?launchableID=env-386KFyCvmg3y22JIf0q8BUh6jia)
- vLLM gpt-oss serving recipe: https://docs.vllm.ai/projects/recipes/en/stable/OpenAI/GPT-OSS.html
- Brev pricing model (dynamic, per-card): https://miamimike.ai , https://www.oreppo.com
- Market GPU rates: https://computecomparison.com (Brev vs RunPod live rates)
