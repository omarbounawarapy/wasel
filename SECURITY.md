# Security

## Reporting a problem

Do not open a public issue for a security problem. Contact the maintainer, [@omarbounawarapy](https://github.com/omarbounawarapy), through the contact details on the GitHub profile, and send only a short message at first: say that you have a security finding and what area it touches, without exploit steps. Include, once contact is made, what you found, how to reproduce it, and what it exposes.

Reports we especially want:

- a way to reach `/webhook/whatsapp` or send a WhatsApp message while the app reports `mode=public`;
- a way to read or change another visitor's sandbox rows in public mode;
- customer text that makes the extractor or a draft follow instructions (prompt injection) without the order being flagged, or that makes an order score lower than the same text without the injection;
- an API key, token or phone number appearing in a response, a log or a committed file;
- a draft that reaches a customer without a person's click while `WA_AUTO_SEND` is off.

Only the `main` branch is maintained; there are no tagged releases.

## Security model in one page

Wasel is a single-tenant application with no user accounts. It is designed to be safe when started with no configuration, and to be run with real customer data only on a host whose network access you control. What it protects, and how:

| Concern | Protection | Where |
|---|---|---|
| Accidental exposure or sending | The default `public` mode never mounts the webhook, never sends, forces `WA_AUTO_SEND` off and isolates visitors. Anything unrecognised resolves to `public`. | [modes](docs/architecture/overview.md#modes) |
| Forged webhook traffic | HMAC-SHA256 on the raw body, verify-token handshake, size cap, deduplication. It fails closed: the route does not exist unless the secrets are long enough. | [WhatsApp](docs/subsystems/whatsapp.md) |
| Hostile customer text | Never trusted by code, delimited and sanitized for the model, every model quote verified, injection lexicon, deterministic scoring. | [extraction](docs/subsystems/extraction.md) |
| Unsafe outbound messages | Deterministic prefilter, local classifier, LLM judge with approval recomputed in code, human send by default. | [outbound](docs/subsystems/outbound.md) |
| Secrets in git | `.env` and databases are ignored and `make hygiene` fails on known key prefixes and secret-name assignments, and CI scans the whole git history with gitleaks. | [configuration](docs/configuration/environment.md) |
| Cost abuse | Daily, per-visitor and per-client-address caps on LLM calls; sandbox limits per visitor and per address; a write-rate limit per address (`429 RATE_LIMITED`); request size limits. The address comes from `CLIENT_IP_HEADER` (a header the proxy overwrites), never from `X-Forwarded-For`; where it is unknown only the per-visitor limits apply. The counters are in memory and reset on restart. | [LLM layer](docs/subsystems/llm.md#caps-and-the-usage-meter) |

## Security-sensitive areas

### Secrets and environment variables

Secrets are `GROQ_API_KEY`, `GEMINI_API_KEY`, `WA_TOKEN`, `WA_APP_SECRET`, `WA_VERIFY_TOKEN`, and `ADMIN_TOKEN`. They come from the process environment or a git-ignored `.env`. `.env.example` is the only committed env file and holds empty values. `make hygiene` (part of `make check` and CI) fails on tracked `.env`, database or `node_modules` files on strings with the prefixes of Groq, Gemini, Meta, tunnel, GitHub, AWS, Slack and Stripe secrets and private-key headers, and on `SECRET`/`TOKEN`/`KEY`/`PASSWORD` names assigned a long value (known placeholders are listed in `scripts/dev/hygiene.allow`). The CI `secrets` job runs gitleaks (pinned, checksum-verified) over the full history. `GET /api/health` reveals only whether a WhatsApp token is present, never the value. Application logs do not print secrets.

Limits: `hygiene` recognises known prefixes and assignment shapes only; a secret in another shape is caught only if gitleaks' rules know it. Anyone with shell access to the host can read `.env`; protect it with file permissions.

### API exposure

There is **no authentication or authorization on `/api`**. In `public` mode, visitor isolation rests on an `X-Visitor-Id` UUID that is a scoping token, not an identity: a visitor can only see the samples and rows created under the id they send, and another visitor's rows return `404` so their existence is not confirmed, but anyone who learns an id can use it. In `dev` and `event` mode every caller sees every row.

Therefore:

- do not expose an instance that holds real customer data on the public internet without an access-control layer in front of it (for example an access-restricted tunnel or a reverse proxy with authentication);
- know that `/api/monitor`, `/api/traces`, `/api/eval`, `/api/failures`, `/api/metrics/impact` and `/openapi.json` are readable by anyone who can reach the server in every mode. They return rates, codes, identifiers and configuration versions, not message text or phone numbers. `/api/failures` with `source=app` replaces message bodies by their length;
- there is no rate limiting on the API. In public mode, orders, replies and LLM calls are capped, which bounds resource use; elsewhere put a limiter in front.

Responses carry `Content-Security-Policy` (default-src 'self', `frame-ancestors 'none'`, and `script-src 'unsafe-inline'` because the static web export needs inline bootstrap scripts), `X-Content-Type-Options: nosniff` and `Referrer-Policy: no-referrer`. Requests declaring a body over 64 KB are refused. CORS is enabled only in `dev` mode for one configured origin. The default bind address of `make serve` is `127.0.0.1`. Outside `public` mode the API also refuses a `Host` that is not in `ALLOWED_HOSTS` (DNS rebinding) and a state-changing request whose `Origin` is neither its own host nor `FRONTEND_ORIGIN` (cross-site posts); the bind address alone is not a boundary.

### Administrative endpoint

`POST /api/admin/reset` deletes every order and reseeds. It exists only when `ADMIN_TOKEN` is at least 24 characters and requires it in `X-Admin-Token` (constant-time comparison). It is the only administrative endpoint. There is no lockout or rate limit on token guesses; use a long random token and do not set one on hosts that do not need the endpoint.

### Webhook handling

The route is mounted only outside `public` mode with `WEBHOOK_ENABLED` true, `WA_APP_SECRET` of at least 16 characters and `WA_VERIFY_TOKEN` of at least 24. The body is capped at 1 MiB while streaming, the signature is verified over the raw bytes before parsing, and a bad signature returns `401` and records a `webhook.rejected` event. Messages are deduplicated by WhatsApp message id, changes for other phone-number ids are ignored, and processing errors are recorded by exception type only. There is no option to skip signature checking. The verify token is redacted from the server's access log.

Limits: signed payloads are not checked against a freshness window; replays are absorbed by deduplication and by status updates that only move forward.

### Untrusted input

All customer text is treated as hostile, including text that reaches an LLM.

- **Sanitizing for the model:** phone-like numbers are masked; brackets and braces that could forge structure become look-alike characters; control and invisible characters are replaced. Length is preserved so evidence spans stay valid.
- **Verification:** every quote the model returns must appear verbatim in a customer message, otherwise it is dropped. The model cannot introduce a fact, a price, a status or a score. Its `confirmed` or `declined` label counts only if the customer's reply after the seller line holds a matching word from the agreement lexicon; otherwise the label becomes `ambiguous` and the order goes to review. Price, zone and product come from the seller's input, the catalog and the gazetteer.
- **Injection lexicon:** phrase-level patterns (English, French, Arabic) in `config/scoring.yaml` flag an order, force human review and ignore an injected confirmation. A hit never changes the score. The evaluation gate requires injected orders to be flagged, still scored and not promoted to an exact address.
- **Drafts:** the LLM judge sees only shop text and order facts, never customer text; the local classifier cannot be prompt-injected; approval is recomputed in code.
- **Display:** the web UI renders text through React; the dashboard escapes it; bidirectional control characters are stripped from customer text in API responses.
- **Input limits:** paste text 2,000 characters, replies 600, CSV 10 rows in public mode and 200 otherwise, request bodies 64 KB.

Limits: the lexicon can miss novel phrasings, and a manipulated model can still return wrong labels for text that does exist in the conversation, which affects the score within what the checks allow. Detection is a safeguard, not a guarantee. Flagged orders are meant to be reviewed by a person.

### File handling

There are no file uploads and no user-controlled file paths. CSV import takes text in a JSON body. Paths come from operator configuration only (`DB_PATH`, `SCORING_CONFIG`, `LLM_REGISTRY`, `PROBE_FILE`, `TRACE_FILE`). The only static files served are those in `web/dist`.

### Logging and stored data

Logs carry counts and reasons only: never a message body, a sender's number or a secret. LLM trace records contain ids, versions, timing and token counts, not customer text. The database does contain customer messages, names and, for WhatsApp customers, phone numbers in plain text (`customers.phone_e164`, unique, never returned unmasked and never sent to a model). The schema has a `raw_payload` column that the current code never writes. In `public` mode, sandbox data, including the extraction-cache rows made from a visitor's text, is deleted after two hours. Where the host rebuilds the database on every start (Render) nothing survives a restart. In `event` and `dev` mode nothing is deleted automatically, and there is no encryption at rest or data-retention policy. Add both at the host level if you hold real data.

### External services and model providers

What leaves the host:

- **LLM providers (Groq, Gemini, or your own endpoint):** for extraction, the rendered conversation window: customer messages and the latest template text, with phone-like numbers masked. Customers can write personal details into messages (names, addresses); those are sent as written. For draft rewrite and judge: template text and order facts (product, price), with the customer's name replaced by a placeholder. No customer id, phone number or account data is sent. Retention and training policies are the provider's; use the self-hosted option if that matters ([self-hosted LLM](docs/operations/self-hosted-llm.md)).
- **Where keys go:** `GROQ_API_KEY` is sent as a bearer token to `GROQ_BASE_URL` or Groq, so a mistyped base URL discloses the key to that host. Calls use HTTPS with default certificate verification when the URL is `https`.
- **Meta (WhatsApp Cloud API):** outbound message text and the recipient's number, only when sending is effective.

Use provider keys with spending limits. `LIVE_LLM_DAILY_CAP` and the visitor caps bound the app's own consumption.

### Database access

All queries are parameterized; the few statements that interpolate text use constants (table names, status lists). The database is a local SQLite file protected only by operating-system permissions. Wasel supports a single API process; a second process on the same file is unsupported.

### Supply chain

Dependencies are pinned to exact versions in `requirements*.txt` and `web/package-lock.json`. `requirements.lock` pins every Python package the dev setup, the dashboard and the CI audit use, with hashes, and `make setup` installs from it with `--require-hashes` (regenerate with `make lock`). The Render image installs its own hashed lock, `deploy/render/requirements.lock`, for linux/amd64. Its base image is pinned by digest. CI actions are pinned to commit SHAs, CI runs with `contents: read` permission, and no LLM SDKs are used (providers are called with `httpx`). The CI `audit` job runs `pip-audit` over `requirements.lock` and `scripts/ops/npm_audit_gate.py` over the whole npm tree of `web/`, failing on any high or critical advisory that is not on the gate's documented allowlist. Dependabot proposes updates weekly for pip, npm, Docker and GitHub Actions. One advisory is accepted: `braces` (GHSA-vfj7-8cjw-p6xm) has no fixed release and is reached only through the linter (`eslint-config-next`), which is not in the images.

## Data

All customer data in this repository is synthetic. Do not load real customer conversations into a `public`-mode deployment, and do not run real customer data on a host without the controls above.

Design detail: [architecture overview](docs/architecture/overview.md), [extraction](docs/subsystems/extraction.md), [outbound](docs/subsystems/outbound.md), [WhatsApp](docs/subsystems/whatsapp.md), [deployment](docs/operations/deployment.md).
