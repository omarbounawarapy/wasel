# AMD ACT III facts for judges

What the organizers say about the hackathon API, and what that means for this project. The first block is the organizers' notice as shown on the Token Factory sign-in page.

## Organizers' notice (Token Factory, team API key distribution)

> Your email is not registered for API key distribution. Please contact the event organizer.
>
> ACT III is hosted on notebooks.amd.com/tokenfactory. There is no billing or credit card info needed.
>
> API key redemptions, the user manual, the model catalogue and model usage are all visible after sign-in or sign-up on notebooks.amd.com/tokenfactory.
>
> Users must create or register a team on the ACT III hackathon registration page, even if a solo member. A team registration is a must, otherwise the organizers do not receive your email for team assignment.
>
> Developers don't need the $100 credit to participate in the ACT III hackathon, only the API key from the Token Factory.

## The known snag

Many participants see "Your email is not registered for API key distribution". The cause is on the registration side: the email used to sign in to Token Factory has not been matched to a registered team. Fixes, in order:

1. Register a team on the lablab.ai ACT III page (solo entrants too), using the same email you sign in with.
2. Wait for the organizers to assign the team, then sign in again.
3. If it still shows, contact the event organizer. Nothing in this repository can fix it.

## What this means for Wasel

- **Wasel does not need the key to run.** The AMD Token Factory endpoint is off until `AMD_TOKENFACTORY_BASE_URL`, `AMD_TOKENFACTORY_API_KEY` and `AMD_TOKENFACTORY_MODEL` are all set. With none of them set, the app uses the next step in the route: hosted Groq if `GROQ_API_KEY` is set, then Gemini if enabled, then the deterministic rules path. A key alone, without the other two, also leaves it off.
- **Judges can run it without a key.** `make test`, `make eval` and `make up` need no key and no network. The rules path scores and drafts orders on its own; the language model only helps with messages the rules cannot read. See [the LLM subsystem](../subsystems/llm.md) for the route table.
- Unit tests pin this: `test_without_a_token_factory_key_the_app_runs_on_what_else_it_has` and `test_a_token_factory_key_alone_adds_no_step` in `tests/unit/test_llm_routes.py`. `make tf-check` with no variables exits with a message naming what to set.
- **What is not claimed.** No Token Factory call has been made from this project yet, so no result is reported as AMD-served. The numbers in the evaluation come from the Groq and rules paths. The status and the steps to switch on are in [AMD Token Factory](amd-tokenfactory.md).
- **Credits are a separate perk.** The $100 AMD cloud credit is not needed for ACT III. The GPU-instance runbook ([AMD instance](amd-instance.md)) stays for anyone who receives credits.
