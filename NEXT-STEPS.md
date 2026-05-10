---
title: Decision Memory Router Next Steps
date: 2026-05-03
status: active
tags: #build #decision-memory #handoff
---

# Decision Memory Router Next Steps

Start here when continuing the public-safe proof package.

## Current State

- Milestone 1 POC exists.
- Fake vault has six durable fake decisions.
- Unit tests pass: 10 tests.
- Eval passes 3/3.
- `review` reports no pending candidates.
- Manual E2E guide exists at `MANUAL-E2E-TEST.md`.
- Private real-shaped extraction was tested once and is not proven yet. See `MILESTONE-2.md`.

## Next Order

1. Review this branch as Milestone 1 fake-fixture proof.
2. Confirm the fake loop works all the way through reuse:
   - ingest source context
   - review inbox
   - recall decision
   - use recalled decision to improve a future task
3. Do not add private notes to this repo.
4. Decide the next build move:
   - fix any E2E failures
   - merge this public-safe proof package
   - or start Milestone 2 real-shaped extraction

## Commands

```bash
python3 -m unittest discover -s tests
python3 -m decision_memory eval
python3 -m decision_memory review
python3 -m decision_memory recall "content proof"
```

Then follow:

```bash
open MANUAL-E2E-TEST.md
```

## Do Not Do Yet

- Do not ingest the whole real vault.
- Do not promote private real decisions in this public-safe package.
- Do not push the full Obsidian vault to GitHub.
- Do not build Overnight Build Runner before this POC is manually validated.

## Success Bar

The POC is not proven because it captures decisions.

It is proven when one recalled decision changes a future task in a useful way.
