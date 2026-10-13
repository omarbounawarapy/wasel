# Team

Wasel is a private demo built by Z-Team. Only team members work in this repository, and the code is not open source (see [LICENSE](LICENSE)).

## Members

| GitHub | Role | Access |
|---|---|---|
| [@omarbounawarapy](https://github.com/omarbounawarapy) | Owner and maintainer: sets scope, reviews and merges changes, owns deployment and secrets | Admin |
| [@azaizoz](https://github.com/azaizoz) | Frontend: the web UI (`web/`) and the dashboard | Write |
| [@j6r-t](https://github.com/j6r-t) | Backend: the API, scoring pipeline, database and deployment code (`src/`) | Write |

## Decisions

- The owner decides what ships. Anything that changes the live deployment (a push to `main`, `render.yaml`, environment variables, Render settings) is agreed with the owner first. Pushes to `main` deploy the demo automatically.
- Access is granted by the owner. Do not share the repository, its screenshots or its data outside the team.
- Security problems go to the owner privately, as described in [SECURITY.md](SECURITY.md).

## Working together

The working rules (branches, checks, tests, documentation in the same change, review) are in [docs/development/workflow.md](docs/development/workflow.md).
