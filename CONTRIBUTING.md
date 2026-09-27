# Contributing

This is Z-Team's hackathon project and the code is not open source (see [LICENSE](LICENSE)). Issues from anyone are welcome. Code changes come from team members.

**Start with the [team guide](docs/team-guide.md).** Its diagrams show who owns each folder, which files a change touches, and the route from branch to `main`.

## The short version

1. `make setup && make check`: green before you change anything.
2. Branch per task: `<name>/<task>`, e.g. `jesser/sandbox-visibility`.
3. Stay in your lane's folders. Changing a **contract file** (`app/contracts.py`, `app/api/models.py`, `mocks/`, `app/db/schema.sql`, `scoring.yaml`, `Makefile`, `ci.yml`, `requirements*.txt`)? Message the lane that consumes it first.
4. The PR has the code **and** its tests. A missing test is allowed only as a visible `pytest.skip(reason=...)`.
5. `git rebase main`, then `make check` green (hygiene + ruff + the offline suite, no API keys).
6. Open the PR and fill in the template. CI runs the same `make check`; on `main` it also boots the image in public mode.
7. Omar merges. If `main` goes red, the author of the last merge fixes it before anyone else merges.

## House rules the checks enforce

- Read time through `app/clock.py`, never `datetime.now()`.
- No LLM SDKs: providers are called with `httpx` from `app/llm/` only.
- No secrets, `.env` or `*.db` files in git.
- Editing a prompt means bumping `PROMPT_VERSION` (the prompt text is sha-locked in the tests).
- Every number the UI shows comes from code or `reports/*.json`, never from the LLM.

## Style

`make fmt` fixes what ruff can. Line length is 125. Match the surrounding code: short docstrings that cite the spec section (`01 §5.2`), no comments restating the code.

## Commit messages

Imperative and specific, optionally prefixed with the area: `worker: never re-arm a rescore after an exception`.
