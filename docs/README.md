# Wasel documentation

Wasel scores the refusal risk of cash-on-delivery orders written in chat, explains each score with the customer's own words, and drafts the question that would reduce the risk. These pages describe the system as it is implemented: what it does, how it is put together, how to run, configure, test, evaluate, operate and extend it. The root [README](../README.md) is the short orientation.

## Reading order

1. [Getting started](getting-started.md): install, run, check, first scoring loop.
2. [Architecture overview](architecture/overview.md): components, runtime boundaries, modes, limitations.
3. [Order pipeline](architecture/order-pipeline.md): what happens to a message, scoring flow, order states.
4. [Data model](architecture/data-model.md): entities, tables, invariants, lifecycle.
5. [Configuration](configuration/README.md): what each configuration file and variable controls.
6. Then the area you need, below.

## By question

| I want to... | Read |
|---|---|
| Run it and see something | [Getting started](getting-started.md) |
| Understand how a score is produced | [Order pipeline](architecture/order-pipeline.md), [scoring](subsystems/scoring.md), [extraction](subsystems/extraction.md) |
| Understand the LLM's role and what happens when it fails | [LLM layer](subsystems/llm.md) |
| Understand what gets sent to a customer, and who approves it | [Outbound drafts](subsystems/outbound.md) |
| Connect WhatsApp | [WhatsApp](subsystems/whatsapp.md), [deployment](operations/deployment.md#connecting-whatsapp-event-mode) |
| Understand or retrain the model | [Machine learning](machine-learning.md) |
| Know what the evaluation gate proves and what a failure means | [Evaluation](evaluation.md) |
| Watch quality in production | [Monitoring](subsystems/monitoring.md), [failure analysis](subsystems/failure-analysis.md) |
| Call the API | [API](api.md), [examples](../examples/README.md) |
| Change a setting | [Configuration](configuration/README.md), [environment variables](configuration/environment.md) |
| Find what a `make` target does, or which ones overwrite files | [Commands](development/commands.md) |
| Run or write tests | [Testing](development/testing.md) |
| Change the code | [Extending](development/extending.md), [CONTRIBUTING](../CONTRIBUTING.md) |
| Know what is in `data/` | [Data directory](data.md) |
| Deploy, monitor, update, roll back | [Deployment and operations](operations/deployment.md) |
| Self-host the LLM | [Self-hosted LLM](operations/self-hosted-llm.md) |
| Diagnose a problem | [Troubleshooting](operations/troubleshooting.md) |
| Assess the security posture | [SECURITY.md](../SECURITY.md) |

## Map

```
docs/
├── getting-started.md
├── architecture/
│   ├── overview.md            components, boundaries, modes, limitations
│   ├── order-pipeline.md      message to score to draft, states
│   └── data-model.md          entities, tables, invariants
├── subsystems/
│   ├── extraction.md          window, repair, evidence, rules extractor, injection
│   ├── scoring.md             features, model, tiers, confidence, reasons
│   ├── llm.md                 client, providers, registry, caps, failure behaviour
│   ├── outbound.md            templates, rewrite, checks, routing, sending
│   ├── whatsapp.md            webhook, sending, local testing
│   ├── monitoring.md          drift and safety monitor
│   └── failure-analysis.md    hidden-failure analyzer
├── machine-learning.md
├── evaluation.md
├── api.md
├── interfaces.md              web UI and dashboard
├── data.md
├── configuration/
│   ├── README.md              every configuration file, what changes need what
│   ├── environment.md         every environment variable
│   ├── scoring.md             config/scoring.yaml
│   └── llm-registry.md        llm.yaml, prompts, schemas
├── development/
│   ├── commands.md            Makefile and scripts
│   ├── testing.md
│   └── extending.md
├── operations/
│   ├── deployment.md          hosting, running, logs, updates, backups
│   ├── self-hosted-llm.md
│   └── troubleshooting.md
└── assets/                    screenshots and social preview
```

Documentation that lives next to code: [`web/README.md`](../web/README.md), [`dashboard/README.md`](../dashboard/README.md), [`examples/README.md`](../examples/README.md), and the docstrings in `src/wasel/`, which also appear as descriptions in the generated OpenAPI schema.

## Conventions

- **The code is the source of truth.** These pages were written against the implementation and its tests. When a page and the code disagree, the code wins; please fix the page.
- **One authoritative place per topic.** Other pages link to it instead of repeating it: modes are in the [architecture overview](architecture/overview.md#modes), variables in [environment](configuration/environment.md), order states in the [order pipeline](architecture/order-pipeline.md#order-states).
- **Numbers come from committed files.** Metrics quoted here (holdout AUC, evaluation results, dataset sizes) come from `data/reports/`, the model card and the datasets. All data is synthetic, and the quoted figures are not claims about real-world performance.
- **Commands are real.** Every command shown exists in the [Makefile](../Makefile) or under `scripts/`. [Commands](development/commands.md) says which ones change committed files.
- **Update docs with code.** A change that alters behaviour, a setting or a command updates the page that describes it in the same pull request ([CONTRIBUTING.md](../CONTRIBUTING.md)).
