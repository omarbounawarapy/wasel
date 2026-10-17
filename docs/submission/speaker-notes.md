# Speaker notes

Three minutes, one speaker, twelve slides. Speak slower than feels natural and pause after each slide title. Open the live demo on order #2601 before you start, and keep `video/renders/wasel-reel.mp4` ready in case Render is asleep.

| Slide | Time | Say |
|---|---|---|
| 1 | 0:00 | "Wasel helps a seller see which cash-on-delivery orders will be refused, before the courier leaves." |
| 2 | 0:15 | "In Tunisia most online orders are paid at the door. One vendor guide says 15 to 25 percent of fashion orders are refused. The seller pays for that trip." |
| 3 | 0:30 | "Customers write in Arabizi, Arabic script, French, or all three. An address is often 'near the mosque'. A seller can't read every chat closely." |
| 4 | 0:45 | "Wasel reads the chat and scores the order from 0 to 100. It highlights the customer's own words and shows each reason with its points." |
| 5 | 1:05 | "This is order 2601: 87. The address is vague, the customer sounds unsure. Wasel drafts one question, in the customer's language. The customer gives a full address, and the score drops to 16. The seller sees which reasons changed." |
| 6 | 1:30 | "In the queue, the riskiest orders come first, and each row ends in one next step. A person sends the message." |
| 7 | 1:45 | "The model reads, code scores. The model fills a schema, code checks that every quote exists in the original text, and a gradient-boosted model plus a rules file sets the score. The model never picks a number." |
| 8 | 2:05 | "We test on every change: 279 extraction cases, 165 outbound drafts, 32 injection attempts. Every quote is checked against the text, and every unsafe draft is stopped or held." |
| 9 | 2:25 | "In a simulation, 464 dinars saved per 1,000 orders, between 251 and 677 depending on how often a question works. The labels are simulated. A pilot would replace them." |
| 10 | 2:40 | "AMD Token Factory is first in the route, and tests cover it. The key is pending. Wasel keeps working with any provider missing." |
| 11 | 2:50 | "Built: the pipeline and the demo. Next: a pilot with a real seller, real refusal labels, native review, and the AMD evaluation." |
| 12 | 2:55 | "Three things: the seller sees the risk early, code checks the model, and no single provider is required. Scan the code and open order 2601." |

## Questions to expect

**Why not confirm every order by hand?** Every confirmation is a chat the seller has to write and wait on. Wasel points the seller at the few orders that need one. Use the seller's real order volume if you know it.

**Is the data real?** No. Every order is synthetic and the risk model recovers a hand-written prior. The refusal range comes from one vendor guide. Slides 9 and 11 say this.

**Why is the native holdout so low?** The rules were written against our own phrasing. Real wording is further away. The holdout is the honest measure and the next thing we fix (issue #199).

**What runs on AMD?** Nothing yet. The route and `make tf-check` are built and unit-tested; the key was not issued. If it arrives, run `make tf-check` and `make eval-live`, then say the model id and "AMD Token Factory" with the numbers.

**What if the model is wrong?** The score does not depend on the model alone. Quotes that are not in the text are dropped, and a person approves every message.

**Is WhatsApp automatic?** Only if the seller switches it on, and only for clear-cut replies that pass every check.

## Rebuild

`docs/submission/deck/build.sh` writes `docs/submission/wasel-pitch.pdf`. Open `deck/index.html` in a browser to present: arrow keys move, `f` goes full screen.
