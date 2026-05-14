# Phase 2 Review Packet

Review date: 2026-05-15

This packet is for Ashley's manual review. The build can be review-ready without being approved.

## What Was Built

Phase 1.1 makes recalled decisions easier to judge.

When recall finds a decision, it now prints:

- decision
- why
- options considered
- tradeoff
- impact
- assumptions
- missing data
- reuse trigger
- reuse_for

When a query is too vague, the router now asks for the missing decision context instead of guessing.

Phase 2 adds a safe real-shaped session-note fixture and tests whether the router can stage a small set of useful decision candidates from it.

## Why This Exists

The last private-shaped trial was safe but too noisy. It staged 19 weak candidates and created zero durable decisions.

This slice tests whether a real-shaped note can produce fewer, better candidates without touching Ashley's real vault.

## What Passed Tonight

Expected verification:

```text
python3 -m unittest discover -s tests
Ran 20 tests
OK

python3 -m decision_memory eval
Eval complete:
  passed: 3/3

python3 -m decision_memory review
Review complete:
  candidates: 0
  needs-review: 0
  active missing review trigger: 0
  superseded missing successor: 0
```

Manual-style private-local review against the safe fixture:

```text
python3 -m decision_memory --vault /private/tmp/dmr-phase2-review-v2/private-test-vault ingest /private/tmp/dmr-phase2-review-v2/private-test-vault/daily/2026-05-14-session-note.md

Ingest complete:
  candidates created: 3
```

Inbox result:

```text
Candidate decisions:

1. Keep Phase 2 As A Review Slice
   privacy: private-local
   candidate_confidence: complete
   missing: none
   suggested action: review-local

2. Keep Tomorrow S Approved Post Separate
   privacy: private-local
   candidate_confidence: partial
   missing: Reopen When
   suggested action: review-local

3. Use A Safe Real Shaped Fixture
   privacy: private-local
   candidate_confidence: complete
   missing: none
   suggested action: review-local
```

## Commands To Review Tomorrow

From the repo root:

```bash
python3 -m unittest discover -s tests
python3 -m decision_memory eval
python3 -m decision_memory review
python3 -m decision_memory recall "private vault public proof"
python3 -m decision_memory recall "should semantic search stay out of scope"
python3 -m decision_memory recall "can we do this thing soon"
```

Then create a safe private-local review copy:

```bash
mkdir -p /private/tmp/dmr-phase2-review/private-test-vault/daily
cp fake-vault/real-shaped/2026-05-14-session-note.md /private/tmp/dmr-phase2-review/private-test-vault/daily/2026-05-14-session-note.md
python3 -m decision_memory --vault /private/tmp/dmr-phase2-review/private-test-vault ingest /private/tmp/dmr-phase2-review/private-test-vault/daily/2026-05-14-session-note.md
python3 -m decision_memory --vault /private/tmp/dmr-phase2-review/private-test-vault review
python3 -m decision_memory --vault /private/tmp/dmr-phase2-review/private-test-vault inbox
```

Open one complete candidate:

```bash
sed -n '1,220p' /private/tmp/dmr-phase2-review/private-test-vault/decision-inbox/2026-05-14-keep-phase-2-as-a-review-slice.md
```

## How To Judge It

Mark Phase 1.1 green if:

- vague queries refuse to guess and ask a useful follow-up
- recalled decisions show enough context to reuse or correct them

Mark Phase 2 green if:

- the safe session note produces 3 to 7 candidates
- at least one candidate is complete enough to review seriously
- incomplete candidates are labeled clearly
- all candidates remain private-local in the review copy
- nothing is automatically promoted

Mark yellow if:

- the shape is right but the wording, labels, or fields need cleanup

Mark red if:

- extraction is still noisy
- candidates overclaim confidence
- the privacy boundary is unclear
- the output would make you reopen the whole discussion anyway

## Safe Claim If Green

The router can stage reviewable decision candidates from a real-shaped safe fixture without touching private data.

## Blocked Claims

Do not claim:

- the real vault works
- real private reuse is proven
- memory storage is complete
- Phase 2 is approved before Ashley reviews it
- tomorrow's post should be a Phase 2 proof post before review

## Posting Note

Use the already-approved Visible Assumptions post for Friday, May 15, 2026.

The Decision Memory Router post should wait until Ashley reviews this packet.
