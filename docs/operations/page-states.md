# What each page shows when something is missing

A pass over every route in four states, run on 14 Oct 2026 against `make serve` with the web export, at 390 px wide, using Chrome with the API requests blocked or delayed (a throwaway script that aborts or delays every `/api/` request; the table is the result). The rule: no blank page, no spinner that never ends, no raw error text, and a retry wherever the request can be repeated.

| Route | Loading (first answer pending) | Empty (no rows) | API unreachable | API slow (more than 3 s) |
| --- | --- | --- | --- | --- |
| `/dashboard/` Orders to check | Page header and guide, "Scoring…" per row | "No orders yet" | Red notice "Could not load the orders" with **Retry**; top bar says the server cannot be reached | Top bar: "Wasel is starting up…" |
| `/dashboard/inbox/` WhatsApp messages | Header and guide, "Loading…" | "No WhatsApp messages yet" | Red notice with **Retry** | Starting-up bar |
| `/dashboard/paste/` Add an order | Form is usable at once (it needs no data) | n/a | Form stays; submit shows the server error under the button; top bar explains | Starting-up bar; submit shows "Scoring…" |
| `/dashboard/order/?id=…` | "Loading the order…" | "No order selected. Pick an order from Orders to check" | Red notice "Could not load the order" with **Retry** (was: "No order selected", which was wrong) | Starting-up bar |
| `/dashboard/impact/` | Header, "Loading…" | "No estimate yet: the impact report hasn't been generated on this server" | Red notice with **Retry** | Starting-up bar |
| `/dashboard/activity/` | Header, "Loading…" | "Nothing has happened yet" | Red notice with **Retry** (was: "refresh the page" without a button) | Starting-up bar |
| `/dashboard/quality/` | Header, "Loading…" | "No test results yet: the quality reports haven't been generated on this server" | Red notice with **Retry** | Starting-up bar |
| `/dashboard/monitor/` | Header, "Loading…" | Zero counts | Red notice with **Retry** (was: "refresh the page") | Starting-up bar |
| `/dashboard/traces/` | Header | "No AI calls yet" | Red notice with **Retry** (was: "refresh the page") | Starting-up bar |
| `/dashboard/failures/` | Header, "Loading…" | "No report yet" or "No silent failures found" | Red notice with **Retry** | Starting-up bar |
| Unknown path | n/a | n/a | Branded 404 page with a link back to the orders | n/a |

## What this does not cover

- **A sleeping Render instance.** The static pages are served by the same process as the API, so while it sleeps the browser gets Render's own waking page, not Wasel's. The "starting up" bar appears only when the page shell loaded and the API is slow (for example after a restart). The installed app, when offline, shows `/offline.html` instead of a browser error.
- **Real Render timings.** The cold-start time was not measured: the keep-alive workflow pings the demo every 10 minutes, so it never slept while this was written. Render's documentation says about a minute.
- **A native reader.** The French and Arabic text in the waking and offline messages was written by the author of this change and has not been checked by a native speaker.
