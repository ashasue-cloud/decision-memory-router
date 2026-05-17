---
id: 2026-05-03-fake-fixtures-for-public-proof
title: Fake Fixtures For Public Proof
date: 2026-05-03
status: active
source: sync
source_file: fake-vault/daily/2026-05-03.md
privacy_level: public-fixture
decision_type: privacy
reuse_for: github-proof,prd-spec
confidence: medium
route_category: privacy-boundary
route_confidence: high
review_trigger: if public readers cannot understand the workflow from invented data.
do_not_reopen_until: if public readers cannot understand the workflow from invented data.
---
# Decision: Fake Fixtures For Public Proof

## Decision

We chose fake fixtures for public proof.

## Why

public examples need to mirror the workflow without exposing private data.

## Options Considered

- Chosen: We chose fake fixtures for public proof.
- Rejected: sanitized real work and real public company docs.

## Tradeoff Accepted

fake examples are less emotionally specific but safer and faster.

## What This Affects

- GitHub demos and README claims.
- Public content about the router.
- Any future PRD/spec that uses repo evidence as proof.

## Assumptions

- Invented fixtures can show the workflow mechanics without leaking private context.
- Readers can still judge the product decision layer from public-safe examples.
- Privacy clarity matters more than emotional specificity for the first proof package.

## Missing Data

- Whether real-shaped private notes produce complete candidates.
- Whether recalled decisions change a future real task.
- Whether public readers understand the boundary without Ashley explaining it live.

## Future Use

- github-proof,prd-spec

## Related Notes

- fake-vault/daily/2026-05-03.md

## Supersedes



## Review Trigger

if public readers cannot understand the workflow from invented data.
