# Submission form text

Paste-ready answers for the lablab.ai ACT III submission form. The Rule Book says to follow the character limits shown on the form, which are not visible outside it: if the long description is too long, drop the last paragraph first, then the testing sentence. Everything here matches what the repository does today; the AMD text does not claim a result that has not been measured.

## Basic information

**Project title**

Wasel

**Short description** (155 characters)

Wasel reads cash-on-delivery orders from chat, scores the refusal risk from 0 to 100, quotes the reasons, and drafts the one question that lowers the risk.

**Long description** (2637 characters, 451 words)

Sellers in Tunisia take orders in chat and are paid in cash on delivery. When a customer refuses the parcel, the seller has paid for a wasted courier trip. One vendor guide puts refusals at 15 to 25 % for fashion orders; we found no independent national figure. Customers write in Darija (Arabic script or Arabizi), French or a mix, and give addresses like "near the mosque".

Wasel reads the conversation, extracts the order, and scores the refusal risk from 0 to 100. The score comes with reasons built from the customer's own words, for example `3 warning signs ("9rib el jemaa", "mouch dima fi dar", "ghali chwaya") +17`. It then drafts the one question that would reduce the risk: confirm, complete the address, or pay first. When the customer answers, the order is rescored and the page shows which reasons changed. Order #2601 goes from High 87 to Low 16 once the customer gives a full address. The seller sees the riskiest orders first, and a person approves what is sent.

The language model never picks a number. It fills a 12-field schema, code checks every quote against the original text, and an XGBoost model plus the rules in `config/scoring.yaml` compute the score. Drafts come from approved templates in the customer's language, and any model rewrite must pass a prefilter, a local classifier and a model judge. Text hidden in a customer message is flagged and cannot raise the address to exact.

Business value: in a simulation on 2,001 held-out orders, confirmation and prepayment questions cut refusals from 30.0 % to 23.6 %, worth 464 TND per 1,000 orders (251 to 677 depending on how often a question works). The labels are simulated and the assumptions are shown in the app. Tested on every change: 279 extraction cases (96.1 % of orders recognised, no quote missing from the source text), 165 outbound drafts, 32 injection attempts, and 737 tests that run without keys or network.

AMD: the language-model call goes through a configurable route. AMD Token Factory (Gemma-4-31B-IT) answers first, then hosted Groq (gpt-oss-120b) as a fast backup, then Gemini if enabled, then rules. On 40 extraction cases `make eval-live` recognised 92.5 % of orders through Token Factory against 87.5 % through Groq (one run, synthetic data). Token Factory takes 7 to 13 s per call, so the route allows it 16 s before falling back, and the product still works with any provider missing. The hosted API does not report its hardware, so we make no claim about the GPU.

The demo uses synthetic data. Next: a pilot with a real seller, real refusal labels and a native review of the Darija wording. Open source under the MIT licence.

**Technology and category tags**

Technology: Python, FastAPI, XGBoost, SQLite, Next.js, React, Streamlit, Groq, gpt-oss, AMD Token Factory, WhatsApp Cloud API, MIT

Category: Reinvent Commerce (track), e-commerce, cash on delivery, risk scoring, Arabic NLP, Darija

## Cover image and presentation

**Cover image**

`docs/assets/wide-cover-16x9.png` (1920 x 1080; the Rule Book asks for 16:9). Source: `docs/assets/wide-cover-16x9.svg`; the PNG is git-ignored, so re-export it from the SVG if it is missing.

**Video presentation**

`video/renders/wasel-reel.mp4` (MP4) (48-second reel with voice-over, no third-party clip). `video/renders/wasel-usage-demo.mp4` shows a full use of the app if a longer clip is allowed.

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

- Slide 10 and the AMD paragraph describe Token Factory as the primary route. That is only true on the live demo once the three `AMD_TOKENFACTORY_*` variables are set on Render (dashboard, not render.yaml; steps in docs/operations/amd-tokenfactory.md section 5) and `/api/health` shows `last_endpoint: amd-tokenfactory` after one pasted order. If that has not happened by submission time, replace the AMD paragraph's first sentence with: "The route tries AMD Token Factory first when its key, address and model are set; the live demo currently runs on Groq and rules." and set slide 10 step 1 chip back to Optional.
- Re-export `docs/submission/wasel-pitch.pdf` from the deck (`docs/submission/deck/build.sh`) after the slide 10 change.
- Check the live demo shows order #2601 at High 87.
- The Rule Book (read 17 Oct) asks for: slides as PDF, video as MP4 or MOV, cover cropped to 16:9, a public repository, a demo platform and an application URL. Submissions close at the event deadline plus a 5-minute grace period; for a technical problem, contact the organizers before the deadline.
