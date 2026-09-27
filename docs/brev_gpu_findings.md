# Brev GPU session findings — 2026-09-27 (branch `brev`)

Record for the final repo-cleaning phase. Everything below was measured this session,
not assumed. Numbers live in `reports/eval_live.json` (committed) — regenerate any time
with a serving instance and `eval.run --live`.

## What ran

| step | box | result |
|---|---|---|
| serve gpt-oss-20b + `brev-check` | A6000 48 GB | OK: model listed, JSON completion, 756 ms round-trip through the tunnel |
| extraction probe (hero-class message) | A6000 | correct: "…2 pizzas… ghodwa ba3d 17h nkoun fi dar" → order/qty=2/time/place, 1.3 s |
| `eval.run --live` unpaced | A6000 | 6.5 min, 104 extract + 114 judge requests, cache_hits 0 — fully live |
| serve gpt-oss-120b | denvr A100-SXM4-80G | **blocked** — see F4 (disk), never served; 120b self-hosted is UNTESTED |

## Measured: live vLLM-20b vs offline seed cache (cached Groq-120b outputs)

| metric | offline (n=279, 120b cache) | live 20b (n=40) | gate (live) |
|---|---|---|---|
| extraction.is_order_acc | 0.961 | 0.875 | 0.95 |
| extraction.address_exact_acc | 0.907 | **0.650** | — |
| extraction.address_within1_acc | 0.971 | 0.775 | 0.85 |
| extraction.flag_f1 | 0.964 | 0.833 | — |
| g3_injection.labels_preserved | **0.250** | 0.875 | 0.9 |
| outbound.safe_passed | 1.000 (no judge layer offline) | 0.920 | 0.95 |

## Findings

- **F1 — the 20b is_order gate miss is chain fall-through, not model capability.**
  Per-case rerun: on the 40-case sample, every LLM-answered case was correct on
  is_order (35/35 in the eval window); the misses were cases where the LLM layer
  failed and the chain fell to `rules`/`none` — and rules marks intent-question cases
  (`ext-00760`: "3andkom serwel jean?. 9rib el pharmacie. 3ayetli ki tousel") as
  is_order=False. The 6 s step deadline vs measured p95 3.6 s is thin margin.
  **Action (app, not GPU):** look at `OpenAICompatBackend` deadline/parse behavior;
  consider deadline headroom and a "degraded but flagged" path instead of a silent
  is_order=False. The real 20b weakness is **address_exact** (0.650 vs 0.907).
- **F2 — model size matters for extraction; 120b is the production brain.** The
  offline cache is real Groq-120b output: 0.961 is_order, 0.907 address_exact. 20b
  drops address fields hardest. P5 LoRA (on 20b, for address quality) stays
  conditional on how much demo-day latency/insurance is worth; the 0.95 is_order
  gate is met by 120b-shaped extraction, not by 20b.
- **F3 — stale g3 seed cache.** Offline `g3_injection.labels_preserved` = 0.250 vs
  live 0.875: the seed cache predates the F7 g3 injection set. **Action before demo
  day:** `scripts/warm_cache.py` with `LIVE=1` against Groq to re-record extraction.
- **F4 — infra receipts (all hit this session):**
  - `denvr_A100_sxm4_80G` advertises 2 TB disk in `brev search`; the box has a
    **92 GB** root volume. 120b = 63 GB weights + ~10 GB image + system ⇒ does not
    fit. Pick instances with verified ≥ 200 GB free (`df -h` on the box, not search).
  - `vllm/vllm-openai:latest` ships torch/cu13 → "NVIDIA driver too old (found
    12040)" on 12.4-driver hosts. `VLLM_IMAGE=vllm/vllm-openai:v0.10.1` boots and
    resolves gpt-oss MXFP4 on Ampere ("not fully optimized", Triton backend).
  - **`brev create` can provision while reporting failure**: the first H100 create
    printed "Only created 0/1 instances" yet `riskini-120b` existed RUNNING and
    billed ~50 min. Always `brev ls` after create and delete phantoms.
  - Shadeform-backed instances **do not support `brev stop`** — `brev delete` is the
    only way off the meter. Budget discipline = delete when done.
  - `brev port-forward`/`exec`/`copy` share one multiplexed SSH connection: running
    eval while other brev commands are in flight stalls the tunnel past the step
    deadline and mis-measures the model (36/40 fall-throughs observed once).
- **F5 — script hardening landed on `brev` (keep, no reverts needed):** `cfg()` no
  longer dies under `set -u` (d332b08); check uses 512 tokens + `reasoning_content`
  fallback (0ee34c5); `VLLM_ARGS` is actually read from env/.env (844475f);
  `VLLM_IMAGE` knob for cu12 drivers (see `scripts/brev_llm_up.sh`); `.env` values
  with spaces must be quoted (loader is name-rewrite only).

## Spend

~1 h55 m A6000 @ $0.68 ≈ $1.3; ~1 h25 m A100 @ $1.80 ≈ $2.6; ~50 min phantom H100 @
$3.00 ≈ $2.5 (F4). **Total ≈ $6.4 of the $100 credit.** Wall clock ~2 h vs the 1 h
budget — most of the overrun was 120b infra dead-ends (driver, disk), not eval time.

## Cleanup checklist for the final repo-cleaning phase

- [x] All three instances deleted (`brev ls` empty) — nothing billing.
- [x] Local tunnels killed; `/tmp/brev*.env` token files removed; token never entered
      the repo (instance-side `~/.env` died with the disks).
- [x] `reports/eval_live.json` committed as the session's evidence.
- [ ] Before demo day: `warm_cache.py LIVE=1` vs Groq (F3), then `make test` + `make eval`.
- [ ] Decide: retry 120b self-hosted on a verified-≥200 GB box (P0 demo insurance per
      `docs/brev_gpu_plan.md`), or accept Groq-120b primary + rerun the A6000 20b box
      as the flip target (`make brev-serve` rebuilds it in ~15 min).
- [ ] P5 LoRA only if 20b insurance quality matters (address_exact 0.650 is the gap).
- [ ] Human gates unchanged: Fedi native pass on the P3a bank lines; Omar's O-1 call.
