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

For ACT III the organizers confirmed that AMD Token Factory (a hosted API at notebooks.amd.com/tokenfactory) is the AMD path and that the cloud credits are not needed. The app has a Token Factory endpoint that answers first when its variables are set; it has not been called yet because the key needs the team sign-in. Steps: [AMD Token Factory](operations/amd-tokenfactory.md). Organizer notice and the "email not registered" snag: [ACT III facts](operations/amd-act3-facts.md); the product runs without the key.

## AMD Developer Hackathon ACT III: alignment

Source: the event page (online build 12 to 18 October 2026, track Reinvent Commerce). The full Hackathon Rule Book (lablab.ai/hackathon-rules) has not been read yet (#196), so this list covers only what the event page states.

| Requirement or criterion | Where Wasel stands | Issue |
|---|---|---|
| A meaningful part of the workload runs on AMD infrastructure and is in the product shown to judges | **Not met yet.** The Token Factory endpoint and its check (`make tf-check`) are in the code; no Token Factory key yet, so nothing has run on AMD | #191, #194 |
| The serving host is visible to judges | Built: the UI and `/api/health` show the observed host and serving label | #192 |
| Results measured on the AMD endpoint | Not done; waits for the Token Factory key. `eval_live.json` now records the chain (`llm_chain`) so the report names the endpoint and model. The offline numbers come from the Groq and rules paths | #193, #195 |
| Predictions do not rely on a language model alone | Met in design: the XGBoost model and `config/scoring.yaml` set the score, the language model only extracts facts and rewords drafts | #197 |
| Team enrolled, 1 to 6 members, Discord, AMD AI Developer Program | Owner action, not recorded in the repo. A team registration on the lablab ACT III page is required even for one member | #196 |
| Submission form: title, short and long description, challenge, tags, repository, application URL, cover image, demo video, slides | Repository, URL, video and cover image exist (`docs/assets/wide-cover.png`). Slides and final descriptions are pending | #197, #198 |
| Judging: Application of Technology, Business Value, Originality, Presentation | Business value is stated with its synthetic-data limit. Originality and presentation: README opening, 30-second path, score-drop GIF | #129, #197 |
| Source access and licence acceptable to judges | The repository is public under the MIT licence | #125 to #127 |

## Licence

The repository is public and released under the MIT licence; see [LICENSE](../LICENSE).
