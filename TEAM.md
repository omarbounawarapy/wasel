# Team

Wasel is built by Z-Team. The repository is public and MIT licensed (see [LICENSE](LICENSE)). Only team members change it; outside readers can open an issue.

## Members

| GitHub | Role | Access |
|---|---|---|
| [@omarbounawarapy](https://github.com/omarbounawarapy) | Owner and maintainer: sets scope, reviews and merges changes, owns deployment and secrets | Admin |
| [@azaizoz](https://github.com/azaizoz) | Frontend | Write |
| [@j6r-t](https://github.com/j6r-t) | Backend | Write |
| [@montaassarr](https://github.com/montaassarr) | Frontend (web UI and dashboard) | Write |
| [@fedi567](https://github.com/fedi567) | Logo, product name and synthetic data | Write |

## Decisions

- The owner decides what ships. Anything that changes the live deployment (a push to `main`, `render.yaml`, environment variables, Render settings) is agreed with the owner first. Pushes to `main` deploy the demo automatically.
- Access is granted by the owner. Never commit credentials or anything that is not synthetic.
- Security problems go to the owner privately, as described in [SECURITY.md](SECURITY.md).

## Working together

The working rules (branches, checks, tests, documentation in the same change, review) are in [docs/development/workflow.md](docs/development/workflow.md).
