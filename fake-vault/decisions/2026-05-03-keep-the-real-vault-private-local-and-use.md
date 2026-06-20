---
id: 2026-05-03-keep-the-real-vault-private-local-and-use
title: Keep The Real Vault Private Local And Use
date: 2026-05-03
status: active
source: slack-summary
source_file: fake-vault/slack-summaries/2026-05-03-followup.md
privacy_level: public-fixture
decision_type: privacy
reuse_for: performance-review
confidence: medium
route_category: privacy-boundary
route_confidence: high
review_trigger: if we create a formal anonymization process and review it separately.
do_not_reopen_until: if we create a formal anonymization process and review it separately.
---
# Decision: Keep The Real Vault Private Local And Use

## Decision

We will keep the real vault private-local and use public-fixture data for demos.

## Why

decision context is sensitive even when the tool is public.

## Options Considered

- Chosen: We will keep the real vault private-local and use public-fixture data for demos.
- Rejected: pointing the public repo at a scrubbed copy of the real vault.

## Tradeoff Accepted

more fixture-writing work, less privacy risk.

## What This Affects

- Demo data policy.
- Public repo boundaries.
- Any future private-local trial or anonymization process.

## Assumptions

- Decision context is sensitive even after obvious names and details are removed.
- Public proof should not depend on sanitizing real vault content.
- A separate anonymization process needs its own review before real data leaves local storage.

## Missing Data

- Whether an anonymization process can preserve decision usefulness without exposing private context.
- Whether private-local trials need different review fields than public fixtures.

## Future Use

- performance-review

## Related Notes

- fake-vault/slack-summaries/2026-05-03-followup.md

## Supersedes



## Review Trigger

if we create a formal anonymization process and review it separately.
