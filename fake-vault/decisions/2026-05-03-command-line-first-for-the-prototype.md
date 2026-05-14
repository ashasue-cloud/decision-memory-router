---
id: 2026-05-03-command-line-first-for-the-prototype
title: Command Line First For The Prototype
date: 2026-05-03
status: active
source: granola-note
source_file: fake-vault/meeting-notes/2026-05-03-product-review.md
privacy_level: public-fixture
decision_type: build
reuse_for: ai-session
confidence: medium
route_category: build-path
route_confidence: high
review_trigger: if CLI usage blocks evaluation with non-technical users.
do_not_reopen_until: if CLI usage blocks evaluation with non-technical users.
---
# Decision: Command Line First For The Prototype

## Decision

We chose command line first for the prototype.

## Why

the riskiest question is whether decision records can be staged and recalled, not whether the UI looks good.

## Options Considered

- Chosen: We chose command line first for the prototype.
- Rejected: building a dashboard first.

## Tradeoff Accepted

less visual polish in exchange for faster learning.

## What This Affects

- Prototype scope.
- Manual review speed.
- Whether the team learns the decision-memory loop before designing UI.

## Assumptions

- The CLI is enough for Ashley to test source -> candidate -> recall.
- UI polish would not answer the riskiest product question.
- A visible command receipt is better than a hidden workflow for early debugging.

## Missing Data

- Whether a non-technical reviewer can judge the workflow from CLI output.
- Which CLI steps create enough friction to require a UI later.

## Future Use

- ai-session

## Related Notes

- fake-vault/meeting-notes/2026-05-03-product-review.md

## Supersedes



## Review Trigger

if CLI usage blocks evaluation with non-technical users.
