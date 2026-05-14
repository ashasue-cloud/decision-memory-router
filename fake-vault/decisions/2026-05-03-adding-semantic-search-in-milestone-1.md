---
id: 2026-05-03-adding-semantic-search-in-milestone-1
title: Adding Semantic Search In Milestone 1
date: 2026-05-03
status: active
source: downloaded-context
source_file: fake-vault/downloads/weekend-context-file.md
privacy_level: public-fixture
decision_type: product
reuse_for: ai-session
confidence: medium
route_category: scope-decision
route_confidence: high
review_trigger: if rule-based recall fails the fixture eval.
do_not_reopen_until: if rule-based recall fails the fixture eval.
---
# Decision: Adding Semantic Search In Milestone 1

## Decision

We are not adding semantic search in Milestone 1.

## Why

structured decisions need to prove value before embeddings add complexity.

## Options Considered

- Chosen: We are not adding semantic search in Milestone 1.
- Rejected: starting with Chroma or LlamaIndex.

## Tradeoff Accepted

keyword recall may miss fuzzy matches, but debugging stays simple.

## What This Affects

- Milestone 1 scope.
- Recall quality expectations.
- Any future proposal to add embeddings before structured decisions prove value.

## Assumptions

- Keyword recall is good enough to test whether decision records are reusable.
- Adding embeddings now would make failures harder to debug.
- The first risk is decision quality, not fuzzy retrieval.

## Missing Data

- How often real user queries need semantic matching.
- Whether structured route labels reduce the need for embeddings.
- What recall misses look like after private-local trials.

## Future Use

- ai-session

## Related Notes

- fake-vault/downloads/weekend-context-file.md

## Supersedes



## Review Trigger

if rule-based recall fails the fixture eval.
