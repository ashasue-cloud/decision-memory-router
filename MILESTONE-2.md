# Milestone 2: Real-Shaped Extraction

Milestone 1 proves the fake-fixture loop. Milestone 2 should prove whether copied private-local notes can produce fewer, complete, reviewable decision candidates without exposing private data.

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

## Work Needed

- Add section-aware parsing for session notes instead of splitting every signal-heavy paragraph.
- Ignore headings, project lists, salience summaries, and assumption inventories unless they contain a full decision record.
- Require labeled decision fields before suggesting `promote`.
- Add candidate confidence levels: `complete`, `partial`, `noise-risk`.
- Group duplicate or related candidates from the same source.
- Keep private-local candidates blocked from public-proof promotion.
- Add an eval fixture based on sanitized real-shaped notes.

## Acceptance

- Fake-fixture eval still passes.
- Private-local candidates remain private-local.
- A copied private note produces fewer, clearer candidates.
- At least one private-local candidate can be reviewed manually and rewritten into a complete decision without touching the public package.
