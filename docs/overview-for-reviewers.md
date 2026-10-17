# Overview for reviewers

What Wasel is, where to see it, how AMD is used, and what is built. Built for the AMD Developer Hackathon ACT III, track Reinvent Commerce.

## Where to look

| What | Where |
|---|---|
| Live demo (public mode, synthetic data, read-only samples) | https://wasel.runs-on.dev (the free tier may take about a minute to wake) |
| 48-second reel | [`video/renders/wasel-reel.mp4`](../video/renders/wasel-reel.mp4) |
| Pitch slides (12) | [`docs/submission/wasel-pitch.pdf`](submission/wasel-pitch.pdf), source in [`docs/submission/deck`](submission/deck/index.html) |
| Full usage walkthrough (83 s) | [`video/renders/wasel-usage-demo.mp4`](../video/renders/wasel-usage-demo.mp4) |
| Run it yourself, no keys | `make setup && make demo`, then open http://localhost:8000 ([getting started](getting-started.md)) |
| 30-second path | [README: Try it in 30 seconds](../README.md#try-it-in-30-seconds) |
| How a score is produced | [order pipeline](architecture/order-pipeline.md), [scoring](subsystems/scoring.md) |
| How it is tested | [evaluation](evaluation.md), `make check` (offline, about a minute) |

## What it does

Wasel reads a cash-on-delivery order written in chat (Tunisian Darija, Arabizi, Arabic or French), scores the refusal risk from 0 to 100 in code, explains the score with the customer's own words, and drafts the one question that would reduce the risk. When the customer answers, the order is rescored and the reasons that changed are shown. The hero order #2601 goes from HIGH 87 to LOW 16 after the customer gives a full address.

## What is built, and what comes next

- **Built:** the pipeline (ingestion, extraction with quote verification, scoring, drafts with three safety layers, rescoring), the signed WhatsApp webhook path, an optional `API_TOKEN` gate on `/api`, the offline evaluation gate on every change and the live demo.
- **Data:** every order, conversation and training row is synthetic. The risk model recovers a hand-written prior, and the impact figures are a simulation with its assumptions shown.
- **Next:** a pilot with one real seller to replace the simulated labels, native review of the Darija wording in templates and the French and Arabic interface text, and the Token Factory evaluation below.
- **Sourcing:** the refusal range cited in the README comes from one vendor guide; no independent national figure was found.

## How AMD is used

The language-model step (reading a chat into a 12-field schema) goes through a configurable route. When its variables are set, **AMD Token Factory** (notebooks.amd.com/tokenfactory, the ACT III hosted API) is tried first. Hosted Groq (`gpt-oss-120b`), then Gemini if enabled, then the rules extractor follow, so the product keeps working with any provider missing.

- The route, `make tf-check` (sends real extraction cases to Token Factory alone) and the fallback chain are built and covered by unit tests, with and without the key.
- `data/reports/eval_live.json` records the chain (`llm_chain`, each step as `endpoint:model`), so a live evaluation names the endpoint and model that answered.
- The Token Factory key is pending, so the live demo currently runs on Groq and the rules path. The score never depends on the model alone: the model fills fields, code verifies the quotes, and an XGBoost model plus `config/scoring.yaml` sets the number.
- An optional GPU path (vLLM on ROCm) is described in the [AMD instance runbook](operations/amd-instance.md).

Steps and checks: [AMD Token Factory](operations/amd-tokenfactory.md). Organizer notice and the no-key behaviour: [ACT III notes](operations/amd-act3-facts.md).

## Licence

The repository is public and released under the MIT licence; see [LICENSE](../LICENSE).
