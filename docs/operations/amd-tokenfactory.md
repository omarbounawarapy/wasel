# AMD Token Factory (ACT III)

The AMD ACT III hackathon runs on AMD Token Factory, a hosted model API at [notebooks.amd.com/tokenfactory](https://notebooks.amd.com/tokenfactory). It needs no billing details, no GPU instance and no AMD Developer Cloud credit. Those credits are a separate perk; the [AMD instance runbook](amd-instance.md) covers that path if they arrive.

## Status

- The app can call Token Factory: the `amd-tokenfactory` endpoint in `config/llm.yaml`, its route steps, `make tf-check` and the variables below, tested against local stand-in servers.
- The key is pending. Once it is set, `make tf-check` confirms four things against the real API: that it is OpenAI-compatible, its base URL, which models the catalogue lists, and that it accepts the strict JSON-schema `response_format` the extractor sends.
- The live demo uses Token Factory once the variables are set on Render. Call the demo AMD-served when `/api/health` shows `last_endpoint: amd-tokenfactory`.

## 1. Register and get a key

The app runs without a key; see [ACT III notes](amd-act3-facts.md).

1. Register a team on the lablab.ai ACT III page. A team is required even for a solo entrant.
2. Sign up or sign in at notebooks.amd.com/tokenfactory. Redeem the API key there. The user manual, model catalogue and usage page are on the same site.
3. From the manual, note the base URL. From the catalogue, pick a model id. Prefer a gpt-oss model if one is listed, since the prompts and the evaluation were built on gpt-oss; otherwise pick the largest instruction model that supports JSON output.

## 2. Point the app at it

Copy the lines from `config/amd-tokenfactory.env.example` into `.env` and fill them in:

```bash
AMD_TOKENFACTORY_BASE_URL=<base URL from the manual, ending in /v1>
AMD_TOKENFACTORY_API_KEY=<your key>
AMD_TOKENFACTORY_MODEL=<model id from the catalogue>
```

All three must be set; with any one missing the endpoint stays off and the app behaves as before. When they are set, the extract route is Token Factory first, then hosted Groq (if `GROQ_API_KEY` is set), then Gemini (if enabled), then rules. The generated route table is in [the LLM subsystem page](../subsystems/llm.md).

## 3. Check it on its own

```bash
make tf-check
```

It sends three golden extraction cases to Token Factory only, with the app's real request, and prints the path, latency and any provider error for each. Every line must say `OK` and `path=llm`.

Common failures:

- `SchemaRejected` naming `response_format` or `json_schema`: the API does not accept strict structured output. Check with the team before changing the extractor; it is a request-shape change, not a setting.
- `SchemaRejected` naming `reasoning_effort` (gpt-oss models only): set `reasoning:` on the `amd-tokenfactory` endpoint in `config/llm.yaml` to a profile without it.
- `ModelGone`: the model id does not match the catalogue spelling.
- `ProviderDown` or `Timeout`: wrong base URL, or the service is busy. Raise `--timeout` with `python scripts/ops/endpoint_check.py amd-tokenfactory --timeout 60`.

## 4. Live evaluation

```bash
make eval-live
```

`data/reports/eval_live.json` records `llm_chain` (each step as `endpoint:model`) and, per set, `paths`. Answers from Token Factory count under `paths.llm`; answers from the hosted backup count under `fallback_provider`. To measure Token Factory alone, empty `GROQ_API_KEY` in `.env` for the run. Report the model id and "AMD Token Factory" with the numbers, never "MI300X" or other hardware, since the hosted API does not tell us what it runs on.

## 5. The demo

To serve the Render demo from Token Factory, add the three variables in the Render dashboard (not in `render.yaml`) and redeploy. The Monitor page then names AMD Token Factory as the source of the last AI answer. The privacy page lists Groq as the model provider; add AMD as a recipient of message text before switching the public demo.
