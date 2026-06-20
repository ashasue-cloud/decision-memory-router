# Milestone 2: Real-Shaped Extraction

Milestone 1 proves the fake-fixture loop. Milestone 2 should prove whether copied private-local notes can produce fewer, complete, reviewable decision candidates without exposing private data.

Phase 2 is a review slice, not a memory-store launch.

The review packet for Ashley is `PHASE-2-REVIEW-PACKET.md`.

## Current Failure

Private trial input:

```text
agent-memory/daily/claude-code/2026-05-03.md
```

Result:

```text
Candidates staged: 19
Privacy: private-local
Suggested action: keep for all 19
Durable decisions created: 0
```

The system did the safe thing by blocking promotion, but extraction was too noisy to prove reuse.

## Goal

Turn real-shaped private notes into a small set of complete candidate decisions.

Target:

```text
1 copied private-local source file
3-7 staged candidates
at least 1 complete candidate
0 public-fixture leakage
0 automatic promotion
```

## Current Review Slice

This branch adds:

- richer recall receipts so decisions show why, options, tradeoff, impact, assumptions, missing data, and reuse trigger
- clearer vague-query clarification
- one public-safe real-shaped session-note fixture at `fake-vault/real-shaped/2026-05-14-session-note.md`
- section-aware extraction from `## Decisions made`
- candidate confidence labels: `complete`, `partial`, and `noise-risk`
- private-local candidates that stay review-only instead of promotion-ready

Expected safe-fixture output:

```text
3 staged candidates
2 complete
1 partial
0 automatic promotions
0 private data
```

## Phase 2.1 Yellow-Review Cleanup

Manual review found the slice useful but not ready for private-local reuse proof because the partial candidate was under-explained.

This cleanup adds:

- readable possessive titles, for example `Keep Tomorrow's Approved Post Separate`
- slug cleanup for possessives, for example `keep-tomorrows-approved-post-separate`
- missing-field reporting for every blocker before promotion: `Reopen When`, `Assumptions`, and `Missing Data`
- tests that preserve the safe real-shaped fixture output while making the partial candidate easier to judge

## Phase 2.2 Recall Review Cleanup

Manual review found the recall receipt technically correct but too verbose to understand quickly.

This cleanup adds:

- concise recall output by default: route, confidence, top decisions, decision, and why
- full diagnostic recall output behind `--verbose`
- parser support for `python3 -m decision_memory recall --verbose "<query>"`
- tests for both concise recall and verbose recall

## Work Covered In This Branch

- Add section-aware parsing for session notes instead of splitting every signal-heavy paragraph.
- Ignore headings, project lists, salience summaries, and assumption inventories unless they contain a full decision record.
- Require labeled decision fields before suggesting `promote`.
- Add candidate confidence levels: `complete`, `partial`, `noise-risk`.
- Improve partial-candidate missing-field reporting.
- Improve generated title formatting for possessives and capped titles.
- Make recall reviewer-friendly by default and keep full detail behind `--verbose`.
- Keep private-local candidates blocked from public-proof promotion.

## Remaining Work Before Private-Local Reuse Proof

- Decide whether duplicate or related candidates from the same source need grouping.
- Add more sanitized real-shaped fixtures if one note is not enough coverage.

## Acceptance

- Fake-fixture eval still passes.
- Private-local candidates remain private-local.
- A copied private note produces fewer, clearer candidates.
- At least one private-local candidate can be reviewed manually and rewritten into a complete decision without touching the public package.
