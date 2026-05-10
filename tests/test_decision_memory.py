import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from decision_memory.cli import (
    candidate_already_recorded,
    cmd_ingest,
    cmd_promote,
    extract_candidates,
    infer_privacy_level,
    infer_source,
    parse_query_file,
    query_terms,
    rank_decisions,
    slug_title,
)


class DecisionMemoryTests(unittest.TestCase):
    def test_extract_candidates_finds_decision_language(self):
        source = Path("fake-vault/daily/2026-05-03.md")
        text = "Decision: We chose fake fixtures. Why: safer. Rejected: real data. Tradeoff: less realism. Reopen: if unclear."
        candidates = extract_candidates(text, source)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["privacy_level"], "public-fixture")

    def test_ingest_creates_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vault = root / "fake-vault"
            daily = vault / "daily"
            daily.mkdir(parents=True)
            source = daily / "2026-05-03.md"
            source.write_text(
                "Date: 2026-05-03\n\nDecision: We chose fake fixtures. Why: safer. Rejected: real data. Tradeoff: less realism. Reopen: if unclear.",
                encoding="utf-8",
            )
            with redirect_stdout(StringIO()):
                code = cmd_ingest(vault, [str(source)])
            self.assertEqual(code, 0)
            self.assertEqual(len(list((vault / "decision-inbox").glob("*.md"))), 1)

    def test_ingest_marks_non_fake_vault_private_local(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vault = root / "private-test-vault"
            daily = vault / "daily"
            daily.mkdir(parents=True)
            source = daily / "2026-05-03.md"
            source.write_text(
                "Date: 2026-05-03\n\nDecision: We chose fake fixtures. Why: safer. Rejected: real data. Tradeoff: less realism. Reopen: if unclear.",
                encoding="utf-8",
            )
            with redirect_stdout(StringIO()):
                code = cmd_ingest(vault, [str(source)])
            self.assertEqual(code, 0)
            candidate = next((vault / "decision-inbox").glob("*.md"))
            self.assertIn("privacy_level: private-local", candidate.read_text(encoding="utf-8"))
            self.assertEqual(infer_privacy_level(vault), "private-local")

    def test_ingest_skips_already_promoted_decision(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vault = root / "fake-vault"
            daily = vault / "daily"
            decisions = vault / "decisions"
            daily.mkdir(parents=True)
            decisions.mkdir(parents=True)
            source = daily / "2026-05-03.md"
            source.write_text(
                "Date: 2026-05-03\n\nDecision: We chose fake fixtures. Why: safer. Rejected: real data. Tradeoff: less realism. Reopen: if unclear.",
                encoding="utf-8",
            )
            existing = decisions / "2026-05-03-fake-fixtures.md"
            existing.write_text("# Decision\n\nExisting durable decision.", encoding="utf-8")
            self.assertTrue(candidate_already_recorded(vault, "2026-05-03-fake-fixtures"))
            with redirect_stdout(StringIO()) as output:
                code = cmd_ingest(vault, [str(source)])
            self.assertEqual(code, 0)
            self.assertIn("No new candidate decisions found.", output.getvalue())
            self.assertIn("source type: sync", output.getvalue())
            self.assertEqual(len(list((vault / "decision-inbox").glob("*.md"))), 0)

    def test_promote_requires_complete_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vault = root / "fake-vault"
            inbox = vault / "decision-inbox"
            inbox.mkdir(parents=True)
            candidate = inbox / "2026-05-03-incomplete.md"
            candidate.write_text(
                """---
id: 2026-05-03-incomplete
title: Incomplete
date: 2026-05-03
status: candidate
source: sync
source_file: fake
privacy_level: public-fixture
decision_type: build
reuse_for: ai-session
confidence: medium
---
# Candidate Decision: Incomplete

## Decision

We chose the thing.
""",
                encoding="utf-8",
            )
            with redirect_stdout(StringIO()):
                code = cmd_promote(vault, [str(candidate)])
            self.assertEqual(code, 1)
            self.assertFalse((vault / "decisions" / candidate.name).exists())

    def test_promote_blocks_private_local_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vault = root / "private-test-vault"
            inbox = vault / "decision-inbox"
            inbox.mkdir(parents=True)
            candidate = inbox / "2026-05-03-private.md"
            candidate.write_text(
                """---
id: 2026-05-03-private
title: Private
date: 2026-05-03
status: candidate
source: sync
source_file: private
privacy_level: private-local
decision_type: build
reuse_for: ai-session
confidence: medium
---
# Candidate Decision: Private

## Decision

We chose the thing.

## Why

Because it matters.

## Rejected Alternative

The other thing.

## Tradeoff

More review.

## Reuse For

ai-session

## Status

active

## Privacy

private-local

## Reopen When

When the boundary changes.
""",
                encoding="utf-8",
            )
            with redirect_stdout(StringIO()) as output:
                code = cmd_promote(vault, [str(candidate)])
            self.assertEqual(code, 1)
            self.assertIn("privacy_level: public-fixture", output.getvalue())
            self.assertFalse((vault / "decisions" / candidate.name).exists())

    def test_slug_title_drops_leading_and_trailing_fragments(self):
        self.assertEqual(slug_title("We chose command line first for the prototype."), "Command Line First For The Prototype")
        self.assertEqual(slug_title("We are not adding semantic search in Milestone 1."), "Adding Semantic Search In Milestone 1")

    def test_infer_source_for_content_session(self):
        self.assertEqual(infer_source(Path("fake-vault/briefs/2026-05-03-content-session.md")), "content-session")

    def test_parse_query_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "queries.yml"
            path.write_text('- query: "content proof"\n  expected:\n    - decision-one\n', encoding="utf-8")
            cases = parse_query_file(path)
            self.assertEqual(cases[0]["query"], "content proof")
            self.assertEqual(cases[0]["expected"], ["decision-one"])

    def test_recall_ignores_short_stop_terms_and_substrings(self):
        self.assertEqual(query_terms("zzzz-no-match"), {"zzzz", "match"})
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            decision = root / "2026-05-03-semantic-search.md"
            decision.write_text(
                """---
id: 2026-05-03-semantic-search
title: Semantic Search
status: active
privacy_level: public-fixture
---
# Decision

We are not adding semantic search in Milestone 1.
""",
                encoding="utf-8",
            )
            self.assertEqual(rank_decisions("zzzz-no-match", [decision]), [])


if __name__ == "__main__":
    unittest.main()
