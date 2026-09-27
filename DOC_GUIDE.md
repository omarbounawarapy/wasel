# Documentation Guide for Judges

**Start here:** [ARCHITECTURE.md](ARCHITECTURE.md) — the single source of truth for what the system is, how it works, what's built, and how it's guaranteed to be safe.

---

## For Different Audiences

### Judges and Evaluators
Read in order:
1. **[ARCHITECTURE.md](ARCHITECTURE.md)** (20 min) — Complete system, 282 tests, classifier performance, why Brev was dropped, all you need to make a decision
2. **[README.md](README.md)** (5 min) — How to run it, key features, quick demo
3. **[docs/architecture.md](docs/architecture.md)** (10 min) — Mermaid diagrams showing data flow

### Developers Working on the Codebase
Read in order:
1. **[ARCHITECTURE.md](ARCHITECTURE.md)** (understand the design)
2. **[docs/team-guide.md](docs/team-guide.md)** (who owns what folder)
3. **[CONTRIBUTING.md](CONTRIBUTING.md)** (branch, test, merge flow)
4. **[STATUS.md](STATUS.md)** (what's done, what's open)

### For Historical Context (Not Required for Evaluation)

These documents describe the design process and planning phases. They have been superseded by **ARCHITECTURE.md**, where conflicts arise.

- **PRD.md** — Product requirements, problem statement, scope (pre-build brainstorm)
- **SYSTEM_DESIGN.md** — Detailed tech spec before the council refined it (same info, now in ARCHITECTURE.md §2–11)
- **execution_plan.md** — Hour-by-hour schedule for a specific hackathon (timeline is past)
- **hackathon_playbook.md** — Research phase notes on failure patterns (context only)
- **handoff.md** — Old POC alignment notes (code has been refactored to root)
- **docs/code_handoff.md** — POC notes (superseded by current code structure)
- **docs/council-spec/*** — Design council deliberation (all decisions now in ARCHITECTURE.md)
- **docs/plan-ai-quality.md** — AI quality planning (integrated into tests + eval)
- **FEDI.md** — Language content and story (for team; not required for judges)

---

## Key Sections of ARCHITECTURE.md

| Section | What It Covers | Length |
|---|---|---|
| 1. System Overview | High-level pipeline, topology, data flow | 1 page |
| 2. LLMOps | Model chain, fallback strategy, cost control, cascade | 3 pages |
| 3. Extraction | Schema, validation, injection guard, evidence | 2 pages |
| 4. Scoring | Features, XGBoost, tiers, actions, confidence | 2 pages |
| 5. Safeguards | Prefilter, judge gate, auto-send rules, public mode, event mode | 2 pages |
| 6. What's Built | Detailed table of every component, status, test count | 4 pages |
| 7. Testing | 345 tests collected, 282 passing, by category, live LLM verified | 2 pages |
| 8. Brev Decision | Why it was dropped, time cost, no judging bonus | 1 page |
| 9. Classifier Quality | Why the score is mathematically optimal, AUC 0.784, headline metric | 1 page |
| 10. Responsible AI | Data minimization, repository hygiene, fairness, transparency | 1 page |
| 11–16 | Configuration, deployment, success metrics, known issues, decisions, contacts | 3 pages |

---

## How to Verify Key Claims

### "282 tests pass, 0 failures"
```bash
git clone https://github.com/omarbounawarapy/hackathon
cd hackathon
make setup
make check    # runs pytest, ruff, hygiene
```
Expected: "282 passed, 1 xfailed" in ~40 seconds.

### "Live LLM chain works"
See ARCHITECTURE.md §7.1 "Live LLM check (Sat 05:00)". Results:
- Groq `gpt-oss-120b`: v1 HIGH 87, v2 LOW 11 ✓
- Gemini `3.5-flash-lite`: v1 HIGH 87, v2 LOW 16 ✓
- Injection cases flagged ✓
- Fallback chain works ✓

### "Classifier is monotone and mathematically sound"
- XGBoost config: `monotone_constraints` on address feature ([ARCHITECTURE.md](ARCHITECTURE.md) §4.2)
- Training data: 10,000 synthetic rows from domain formula, no LLM (§7.2)
- Holdout AUC 0.784, calibration 2.4%: see [`reports/train_metrics.json`](reports/train_metrics.json)
- Hero fixture (v1 87→v2 16): `tests/golden/hero.json` runs in test suite

### "What's really built vs not built"
See [ARCHITECTURE.md §6](ARCHITECTURE.md#6-what-has-been-built) table. Status column shows ✅ (production-ready), 🟡 (built with deviation), ⏳ (not built), 🔑 (awaits key/human input).

---

## The Council Spec vs ARCHITECTURE.md

The council spec was a 7-member design deliberation (Architect, Oracle, Alchemist, Skeptic, Craftsman, Strategist, Advocate) resolved over 3 rounds. It is comprehensive and correct, but dense (9 files, ~250 KB).

**ARCHITECTURE.md condenses it into one document optimized for judges:**
- Removes internal deliberation context ("the council found...")
- Replaces with direct facts ("the architecture has X because Y")
- Groups related topics (LLMOps, safeguards, governance) instead of by council role
- Adds "What's Built" table with live test results
- Adds Brev decision and classifier quality proof
- Same content, clearer reading order

All council decisions are preserved and cited. Nothing was changed; only reorganized.

---

## Common Questions

### "How does it handle Darija/Arabizi?"
LLM extraction step handles three languages via strict schema + few-shots (8 examples covering Darija, Arabizi, French, mixed). See ARCHITECTURE.md §3.1 and §6.1.

### "How does it avoid hallucinating quotes?"
Evidence check step verifies every quote is a verbatim substring of the original text. Unverifiable quotes are dropped. See ARCHITECTURE.md §3.2.

### "What if the LLM is down?"
Fallback cascade: Groq 120b → Groq 20b → Gemini → rule-based extractor. No step retries; each tries once. Orders route to review if all fail. See ARCHITECTURE.md §2.1.

### "How are safeguards enforced?"
Three layers before any autonomous action:
1. Deterministic prefilter (no new numbers, no credentials, required slots present)
2. Optional LLM judge (grounding, tone, overreach, question clarity)
3. Rate-limit caps and visitor sandbox isolation in public mode
See ARCHITECTURE.md §5.

### "Is the data real?"
No. All 10,000 training rows are synthetic, rendered from phrase banks and a domain-knowledge label formula. Disclosed in every metric: "simulated AUC", "simulated impact". See ARCHITECTURE.md §4.2, §9.

### "Why is rural addressed by the score?"
Rural zones have sparser addresses, so specificity is harder to verify. High-risk (high score) orders get *confirmation*, not refusal. Prepay only for high-risk *and* high-value. Zone contribution shown in every reason. See ARCHITECTURE.md §10.3.

---

## Navigation Map

```
ARCHITECTURE.md (you are here)
├─ README.md (how to run, quick demo)
├─ docs/architecture.md (diagrams)
├─ examples/ (API scripts)
├─ tests/ (345 tests, see §7)
├─ reports/ (metrics, screenshots)
└─ (for context only)
   ├─ FEDI.md (language/story)
   ├─ STATUS.md (progress as of Sun 27 Sept)
   ├─ PRD.md, SYSTEM_DESIGN.md, etc. (planning history)
   └─ docs/council-spec/ (full design council output)
```

---

## Feedback

- Report issues: [GitHub Issues](https://github.com/omarbounawarapy/hackathon/issues)
- Security concerns: [SECURITY.md](SECURITY.md)
- Questions about specific code: see ARCHITECTURE.md §6, then grep the repo or read the team guide
