# Submission overview

A short page for reviewers: what Wasel is, where to see it, what is real, and what is not.

## Where to look

| What | Where |
|---|---|
| Live demo (public mode, synthetic data, read-only samples) | https://wasel.runs-on.dev (the free tier may take about a minute to wake) |
| 48-second reel | [`video/renders/wasel-reel.mp4`](../video/renders/wasel-reel.mp4) |
| Run it yourself, no keys | `make setup && make demo`, then open http://localhost:8000 ([getting started](getting-started.md)) |
| 30-second path | [README: Try it in 30 seconds](../README.md#try-it-in-30-seconds) |
| How a score is produced | [order pipeline](architecture/order-pipeline.md), [scoring](subsystems/scoring.md) |
| How it is tested | [evaluation](evaluation.md), `make check` (offline, about a minute) |

## What it does

Wasel reads a cash-on-delivery order written in chat (Tunisian Darija, Arabizi, Arabic or French), scores the refusal risk from 0 to 100 in code, explains the score with the customer's own words, and drafts the one question that would reduce the risk. When the customer answers, the order is rescored and the reasons that changed are shown. The hero order #2601 goes from HIGH 87 to LOW 16 after the customer gives a full address.

## What is real and what is not

- **Real:** the pipeline (ingestion, extraction with quote verification, scoring, drafts with three safety layers, rescoring), the signed WhatsApp webhook path, the offline evaluation gate and the live demo.
- **Synthetic:** every order, conversation and training row. The risk model recovers a hand-written prior and is not validated against real refusals. The impact figures are a simulation.
- **Not checked by a native reader:** Darija wording in templates and the French and Arabic interface text.
- **Not independent data:** the refusal range cited in the README comes from a vendor guide; no national figure was found.
- **Not built:** authentication on `/api` (access control belongs in front of the app, see [SECURITY.md](../SECURITY.md)) and WhatsApp use with real customers.

## AMD hardware

The extraction model can be served from an AMD GPU with vLLM on ROCm, and the app has a fallback chain (self-hosted first, hosted second, rules last). **No AMD credits were received, so no AMD GPU serves the live demo today and the AMD path has only been tested against a stand-in endpoint.** Status and runbook: [AMD instance](operations/amd-instance.md).

## Licence

The source is public for viewing and the code is not open source; see [LICENSE](../LICENSE).
