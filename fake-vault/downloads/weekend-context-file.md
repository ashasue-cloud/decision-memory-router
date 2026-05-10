# Weekend Claude Research Context

I researched whether semantic search should be part of the first build.

Decision: We are not adding semantic search in Milestone 1. Why: structured decisions need to prove value before embeddings add complexity. Rejected: starting with Chroma or LlamaIndex. Tradeoff: keyword recall may miss fuzzy matches, but debugging stays simple. Reopen: if rule-based recall fails the fixture eval.

Research note: semantic search may become useful after the decision schema proves itself.
