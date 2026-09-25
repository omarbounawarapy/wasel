# Hackathon Playbook — GoMyCode "Come Build With AI", 27 Sept 2026

Source: official participant guide (read 25 Sept 2026). This file distills that guide into decisions, not a copy of the guide itself — re-check the official guide for exact deadlines/links.

## Why "sellable" beats "technically impressive" here

Judging rubric (100 pts):
- Problem + user value — 20
- Functional execution (works live) — 20
- Quality of AI use (tool-neutral, no Brev bonus) — 20
- Testing + reliability — 15
- Experience + demo (90-second video) — 15
- Responsible AI + data — 10

Problem+Value, Functional Execution, and Experience/Demo together = 55/100. All three are about "is this real, does it run live, is it clear fast" — not about model sophistication. AI Quality is scored the same regardless of provider/compute. This is the structural reason to optimize for a credible business problem with a working demo over a flashier but less-grounded AI pipeline.

## Prize-stacking (the actual lever)

Every submission is automatically considered for its country's 3-tier podium regardless of prize choice. On top of that, these confirmed partner awards are open to all countries and reward the same "real operations/business problem solved with data or AI" theme:

| Award | Prize | Theme fit |
|---|---|---|
| SupplyzPro Smart Operations | TND 1,000 | procurement / supply chain / logistics / SME ops |
| Artefact Data & AI | ~$1,040 voucher | data → actionable insight for a real business/societal challenge |
| Guepard AI Automation | $500 AI credits | AI-powered workflow/agent/automation with productivity value |
| GOMYCODE × NVIDIA Real-World AI Impact | 3rd-place country podium | strongest practical AI for businesses/communities |
| Kredete Financial Inclusion | $500 cash | fintech / payments / credit / financial literacy |

One well-chosen SME-operations idea can qualify for several of these in a single build. Name the relevant ones explicitly in the submission form's "evidence of award fit" field — free additional prize surface for no extra build cost.

## Other operating constraints from the guide

- **Brev is a non-factor**: optional, zero judging bonus, request deadline already passed for this cycle, teams of 2-5 only. Don't spend build time chasing GPU compute — free-tier APIs (Gemini/Groq) are fully competitive.
- **The deliverable is the artifact, not the model.** Judging runs off submitted materials only: working prototype, source link, presentation, 90-second video (problem → product → proof → next step). If it isn't demonstrable in that format, model sophistication doesn't matter.
- **Responsible AI (10 pts) favors business data over personal data.** Orders/transactions/logistics data scores cleaner than anything touching sensitive personal records.
- **Timing**: final team confirmation due 26 Sept, event 27 Sept, build happens across 3 sprints in one day. Scope must be MVP-tight.

## Current pick: COD refusal-risk scoring (Tunisian e-commerce)

Scored against the framework above:
- **Problem+Value**: sellers already track refusal rate as a cost metric — real payer, real number.
- **Demo (90s)**: queue → red order → the "why" → ROI stat is a clean, fast narrative.
- **Prize stack**: SupplyzPro (SME ops) + Artefact (data→insight) + Guepard (the drafted-message/judge-in-the-loop automation) + Real-World AI Impact. Four named prizes from one build.
- **Responsible AI**: business data (addresses/notes/order history), not sensitive personal data — cleaner story here.
- **Compute**: LLM extraction + light classifier runs fine on free-tier APIs, no Brev needed.

**Recommendation: keep this as the primary submission.** See `handoff.md` in this repo for the product/pipeline design (web app not mobile, PWA wrapper, risk queue + detail + ingest + impact screens, extraction→classifier→rule pipeline, drafted customer message with judge-in-the-loop gating before autonomous send).

## Backup ideas considered, and why they rank lower

1. **Micro-merchant creditworthiness scoring** (mobile-money/transaction patterns) — best fit for Kredete's confirmed $500 cash, plus Artefact and Real-World AI Impact. Weaker fit for SupplyzPro. Worth switching to only if the team's strength is fintech/data analysis over NLP.
2. **Youth job-skills matcher** (CV/skills gap, Arabic/French) — fits GOMYCODE's own Future of Learning Award (the actual 1st-place podium prize) plus Brightest and CompTIA. Higher thematic alignment with the host, but "AI resume tool" is a more commoditized pitch and harder to make feel novel to judges than a regional operations pain point.

Neither backup stacks as many named prizes as the COD project, and switching now means starting from zero instead of building on an already-designed pipeline.
