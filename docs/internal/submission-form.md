# Submission form text

Paste-ready answers for the lablab.ai ACT III submission form. Everything here matches what the repository does today; the AMD text does not claim a result that has not been measured.

## Basic information

**Project title**

Wasel

**Short description** (156 characters)

Wasel reads cash-on-delivery orders from chat, scores the refusal risk from 0 to 100, quotes the reasons, and drafts the one question that lowers the risk.

**Long description**

Sellers in Tunisia take orders in chat and get paid in cash on delivery. When a customer refuses the parcel, the seller has paid for a wasted courier trip. One vendor guide puts refusals at 15 to 25 % for fashion orders; we found no independent national figure. Customers write in Darija (Arabic script or Arabizi), French or a mix, and give addresses like "near the mosque".

Wasel reads the conversation, extracts the order, and scores the refusal risk from 0 to 100. The score comes with a reason built from the customer's own words, for example `3 warning signs ("9rib el jemaa", "mouch dima fi dar", "ghali chwaya") +17`. It then drafts the one question that would reduce the risk: confirm, complete the address, or pay first. When the customer answers, the order is rescored and the page shows which reasons changed. Our hero order #2601 goes from High 87 to Low 16 once the customer gives a full address.

The language model never picks a number. It fills a 12-field schema; code checks every quote against the original text, and an XGBoost model plus the rules in `config/scoring.yaml` compute the score. Drafts come from approved templates in the customer's language. Any model rewrite has to pass a prefilter, a local classifier and a model judge, or it is held for a person. Text hidden in a customer message is flagged and cannot raise the address to exact. A person sends the message unless automatic sending is switched on.

Measured offline on 279 extraction cases: order recognised 96.1 %, address level within one step 97.1 %, no quote missing from the source text. 165 outbound drafts: every unsafe one blocked. 32 injection attempts: all flagged. The 737 tests and the evaluation gate run without keys or network.

Scope: the demo runs on synthetic data, and the 464 TND saved per 1,000 orders is a simulation with its assumptions shown. The next step is a pilot with a real seller, real refusal labels and a native review of the Darija wording.

AMD: the extraction call goes through a configurable route that tries AMD Token Factory first when its key, address and model are set, then hosted Groq, then Gemini, then rules. The route and its check (`make tf-check`) are built and unit-tested, and the Token Factory key is pending. The live demo runs on Groq and rules, and the product works without the key. Once the key is in, `make eval-live` measures it and the numbers go in the repository with the model id.

**Technology and category tags**

Technology: Python, FastAPI, XGBoost, SQLite, Next.js, React, Streamlit, Groq, gpt-oss, AMD Token Factory, WhatsApp Cloud API

Category: Reinvent Commerce (track), e-commerce, cash on delivery, risk scoring, Arabic NLP, Darija

## Cover image and presentation

**Cover image**

`docs/assets/wide-cover.png` (1280 x 640, rendered from `docs/assets/wide-cover.svg`). Upload as is.

**Video presentation**

`video/renders/wasel-reel.mp4` (48-second reel with voice-over, no third-party clip). `video/renders/wasel-usage-demo.mp4` shows a full use of the app if a longer clip is allowed.

**Slide presentation**

`docs/submission/wasel-pitch.pdf` (12 slides, 16:9). Source: `docs/submission/deck/index.html`; rebuild with `docs/submission/deck/build.sh`. Talk track and expected questions: `docs/internal/speaker-notes.md`.

## App hosting and repository

**Public GitHub repository**

https://github.com/omarbounawarapy/wasel

**Demo application platform**

Render (free web service, one container serving the API and the built web UI), behind the runs-on.dev subdomain.

**Application URL**

https://wasel.runs-on.dev

The free tier sleeps and may take about a minute to wake. Open it 15 minutes before judges arrive: [Render guide](../operations/render.md).

## Before submitting

- Slide 10 and the long description say the Token Factory key is pending. If it arrives first, run `make tf-check` and `make eval-live`, then update both.
- Check the live demo shows order #2601 at High 87.
- The repository is MIT licensed. Check the lablab Rule Book for anything else it asks of a submission.
