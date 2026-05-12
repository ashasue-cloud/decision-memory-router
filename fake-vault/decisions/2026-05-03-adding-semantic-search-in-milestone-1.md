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

- ai-session

## Future Use

- ai-session

## Related Notes

- fake-vault/downloads/weekend-context-file.md

## Supersedes



## Review Trigger

if rule-based recall fails the fixture eval.
