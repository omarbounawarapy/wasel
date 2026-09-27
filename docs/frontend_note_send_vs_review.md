# Frontend note: the draft guard now names send / owner-approval / blocked

**For:** Montassar (dashboard) · **From:** Omar · **Land:** on main as of 2026-09-27 (guard-classifier change + this note) · **Gate:** `make check` green (337 passed, eval unchanged)

## What changed, one paragraph

The guard classifier (layer 2 of the 3 draft checks — the local, no-LLM one) now outputs an explicit
decision on every generated draft: **`send`** (clear to send to the client), **`review`** (goes to the
owner-approval queue), **`block`** (vetoed; the standard template is used instead). Same model, same
thresholds as before (`scoring.yaml` → `outbound.judge`: `classifier_hold_at: 0.2`, `classifier_block_at:
0.5`), so routing and the human-click rule are **unchanged**. "send" is the classifier's recommendation
only — auto-send still needs the LLM judge's approval plus the route guards, and a human clicks in this
pilot regardless.

## What's new for you (no backend work needed)

1. **Order detail** (`GET /api/orders/{order_id}` → `drafts[]`): `drafts[].judge.classifier.decision` is
   the new key — one of `"send" | "review" | "block"`. It sits next to the existing `p_unsafe`, `label`,
   `top`. Present on every draft that went through the rewrite+judge flow (`source: "llm_rewrite"`),
   including judge-unavailable ones.
2. **Activity feed** (`draft.judged` event): the payload now carries `decision` (same three values). The
   server already renders it in the detail line — *"… · classifier: clear to send / owner approval /
   blocked"* (`app/api/event_text.py`) — so the feed needs nothing from you.
3. **Nothing else moved:** `route` is still `auto_send | needs_review | blocked`; `prefilter` is
   unchanged; drafts created before this change have **no** `decision` key — treat as n/a, don't crash.

## Suggested UI (small, ~15 min)

- **`dashboard/app.py` → `draft_checks()`**, the layer-2 row (≈ line 371): put the decision in the
  Result cell — `⛔ blocked` / `🟡 owner approval` / `✅ clear to send` — and keep risk % +
  "looks like …" in Detail. Read `clf.get("decision")`.
- **Optional chip on the draft card** when `decision == "review"`: label it **"Owner approval"**. That's
  the classifier flagging doubt even when the judge approved — worth showing, it's exactly the
  grey-zone case this feature exists for.
- Optional explainer for the "How this message was checked" expander:
  *"A small local model scores how risky this message is. Below 20% it's cleared, 20–50% goes to you for
  approval, above 50% it's blocked and the standard template is used."*

## Copy (keep the verbs, no "AI-powered")

| decision | Label |
|---|---|
| `send` | Clear to send |
| `review` | Owner approval |
| `block` | Blocked |

If you also want the one-line **reason** ("risk 31% in the 20%–50% review band, most likely discount") in
the draft view: it isn't in the API yet (only the score parts are) — tell me and I'll add it to the
projection, it's one line.

## Verify (2 min)

```bash
make check                                   # gate: ends with "check: green, ok to merge"
pytest tests/unit/test_outbound_judge.py -q  # 26 passed — includes the new decision tests
```

Then `make demo` → open a sample order → the activity feed's `draft.judged` line shows
"classifier: …". Seeded/old drafts may show no decision — that's the n/a case above.
