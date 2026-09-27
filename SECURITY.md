# Security

## Reporting a problem

Do not open a public issue for a security problem. Use GitHub's private report instead: **Security → Report a vulnerability** on this repository. Include what you found, how to reproduce it, and what it exposes. We will answer there.

Things we especially want to hear about:

- a way to reach `/webhook/whatsapp` or send a WhatsApp message while the app reports `mode=public`;
- a way to read or change another visitor's sandbox rows in public mode;
- customer text that makes the extractor or a draft follow instructions (prompt injection) without the order being flagged;
- an API key or token appearing in a response, a log or a committed file.

## What the app does to stay safe

- **Public mode is the default.** A missing or unknown `APP_MODE` means `public`: the webhook is not mounted, sends are forced off, seeded rows are read-only and each visitor gets a sandbox that is purged after 2 hours. CI boots the Docker image and fails if `/api/health` reports anything else.
- **The webhook fails closed.** It is mounted only when enabled and both `WA_APP_SECRET` and `WA_VERIFY_TOKEN` are set; every POST is HMAC-checked and deduplicated.
- **The LLM cannot decide.** It returns a strict schema; every quote is checked against the original text; suspected injection sends the order to human review. A person approves every message before it is sent.
- **LLM spend is capped** per day and per visitor. Reaching a cap falls back to the rules extractor, never to an error.
- **No secrets in git.** `make hygiene` (part of `make check` and CI) fails on key-shaped strings, tracked `.env` or database files, and phone numbers outside the test allowlist.

## Data

All customer data in this repository is synthetic. Do not load real customer conversations into a public-mode deployment.

Design detail: [`docs/council-spec/04-security-public-mode.md`](docs/council-spec/04-security-public-mode.md).
