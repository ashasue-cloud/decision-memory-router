import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from decision_memory.cli import (
    candidate_already_recorded,
    classify_route,
    cmd_ingest,
    cmd_inbox,
    cmd_promote,
    cmd_recall,
    extract_candidates,
    infer_privacy_level,
    infer_source,
    parse_query_file,
    query_terms,
    rank_decisions,
    slugify,
    slug_title,
)


class DecisionMemoryTests(unittest.TestCase):
    def test_extract_candidates_finds_decision_language(self):
        source = Path("fake-vault/daily/2026-05-03.md")
        text = "Decision: We chose fake fixtures. Why: safer. Rejected: real data. Tradeoff: less realism. Reopen: if unclear."
        candidates = extract_candidates(text, source)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["privacy_level"], "public-fixture")
        self.assertEqual(candidates[0]["candidate_confidence"], "partial")
        self.assertEqual(candidates[0]["route_category"], "privacy-boundary")
        self.assertEqual(candidates[0]["route_confidence"], "high")

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
        self.assertEqual(slug_title("Keep tomorrow's approved post separate from the Phase 2 build receipt."), "Keep Tomorrow's Approved Post Separate")
        self.assertEqual(slugify("Keep tomorrow's approved post separate."), "keep-tomorrows-approved-post-separate")

    def test_infer_source_for_content_session(self):
        self.assertEqual(infer_source(Path("fake-vault/briefs/2026-05-03-content-session.md")), "content-session")

    def test_parse_query_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "queries.yml"
            path.write_text('- query: "content proof"\n  expected:\n    - decision-one\n', encoding="utf-8")
            cases = parse_query_file(path)
            self.assertEqual(cases[0]["query"], "content proof")
            self.assertEqual(cases[0]["expected"], ["decision-one"])

    def test_classify_route_content_proof(self):
        route = classify_route("What decisions affect content proof for a post?")
        self.assertEqual(route.category, "content-proof")
        self.assertEqual(route.confidence, "high")
        self.assertIn("content", route.reason)
        self.assertEqual(route.clarifying_question, "")

    def test_classify_route_scope_decision(self):
        route = classify_route("Should semantic search stay out of scope for this milestone?")
        self.assertEqual(route.category, "scope-decision")
        self.assertEqual(route.confidence, "high")
        self.assertIn("scope", route.reason)
        self.assertEqual(route.clarifying_question, "")

    def test_classify_route_privacy_boundary(self):
        route = classify_route("Use fake fixtures so the real vault stays private-local.")
        self.assertEqual(route.category, "privacy-boundary")
        self.assertEqual(route.confidence, "high")
        self.assertIn("privacy-boundary", route.reason)
        self.assertEqual(route.clarifying_question, "")

    def test_classify_route_build_path(self):
        route = classify_route("Keep the command line prototype as the build path.")
        self.assertEqual(route.category, "build-path")
        self.assertEqual(route.confidence, "high")
        self.assertIn("build-path", route.reason)
        self.assertEqual(route.clarifying_question, "")

    def test_real_shaped_session_extracts_fewer_reviewable_candidates(self):
        source = Path("fake-vault/real-shaped/2026-05-14-session-note.md")
        candidates = extract_candidates(source.read_text(encoding="utf-8"), source)

        self.assertEqual(len(candidates), 3)
        self.assertEqual(
            [candidate["candidate_confidence"] for candidate in candidates],
            ["complete", "complete", "partial"],
        )
        self.assertEqual(candidates[0]["title"], "Keep Phase 2 As A Review Slice")
        self.assertEqual(candidates[1]["title"], "Use A Safe Real Shaped Fixture")
        self.assertEqual(candidates[2]["title"], "Keep Tomorrow's Approved Post Separate")
        self.assertNotIn("Passing Tests", {candidate["title"] for candidate in candidates})
        self.assertNotIn("Energy Note", {candidate["title"] for candidate in candidates})

    def test_real_shaped_private_local_ingest_stays_review_only(self):
        source = Path("fake-vault/real-shaped/2026-05-14-session-note.md")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vault = root / "private-test-vault"
            daily = vault / "daily"
            daily.mkdir(parents=True)
            private_source = daily / source.name
            private_source.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

            with redirect_stdout(StringIO()):
                code = cmd_ingest(vault, [str(private_source)])
            self.assertEqual(code, 0)

            candidates = sorted((vault / "decision-inbox").glob("*.md"))
            self.assertEqual(len(candidates), 3)
            self.assertFalse((vault / "decisions").exists())
            for candidate in candidates:
                text = candidate.read_text(encoding="utf-8")
                self.assertIn("privacy_level: private-local", text)
                self.assertIn("candidate_confidence:", text)

            with redirect_stdout(StringIO()) as output:
                inbox_code = cmd_inbox(vault)
            self.assertEqual(inbox_code, 0)
            inbox_text = output.getvalue()
            self.assertIn("candidate_confidence: complete", inbox_text)
            self.assertIn("candidate_confidence: partial", inbox_text)
            self.assertIn("missing: Reopen When, Assumptions, Missing Data", inbox_text)
            self.assertIn("suggested action: review-local", inbox_text)

    def test_classify_route_unclear_input_needs_clarification(self):
        route = classify_route("Can we do this thing soon?")
        self.assertEqual(route.category, "needs-clarification")
        self.assertEqual(route.confidence, "low")
        self.assertIn("none map cleanly", route.reason)
        self.assertIn("What decision are you trying to reuse?", route.clarifying_question)
        self.assertIn("Add one concrete noun", route.clarifying_question)

    def test_recall_prints_router_recommendation(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp) / "fake-vault"
            decisions = vault / "decisions"
            decisions.mkdir(parents=True)
            decision = decisions / "2026-05-03-content-proof.md"
            decision.write_text(
                """---
id: 2026-05-03-content-proof
title: Content Proof
status: active
privacy_level: public-fixture
reuse_for: content-brief,github-proof
---
# Decision

We decided to block content until build proof exists.

## Tradeoff Accepted

Slower posting cadence.
""",
                encoding="utf-8",
            )

            with redirect_stdout(StringIO()) as output:
                code = cmd_recall(vault, ["content", "proof"])

            text = output.getvalue()
            self.assertEqual(code, 0)
            self.assertIn("Router recommendation:", text)
            self.assertIn("route: content-proof", text)
            self.assertIn("confidence: high", text)
            self.assertIn("Top decisions:", text)
            self.assertIn("Content Proof", text)
            self.assertIn("For the full receipt, rerun with --verbose.", text)
            self.assertNotIn("reason:", text)
            self.assertNotIn("options:", text)

    def test_recall_verbose_prints_full_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp) / "fake-vault"
            decisions = vault / "decisions"
            decisions.mkdir(parents=True)
            decision = decisions / "2026-05-03-content-proof.md"
            decision.write_text(
                """---
id: 2026-05-03-content-proof
title: Content Proof
status: active
privacy_level: public-fixture
reuse_for: content-brief,github-proof
---
# Decision

We decided to block content until build proof exists.

## Tradeoff Accepted

Slower posting cadence.
""",
                encoding="utf-8",
            )

            with redirect_stdout(StringIO()) as output:
                code = cmd_recall(vault, ["--verbose", "content", "proof"])

            text = output.getvalue()
            self.assertEqual(code, 0)
            self.assertIn("Router recommendation:", text)
            self.assertIn("route: content-proof", text)
            self.assertIn("reason:", text)
            self.assertIn("Relevant decisions:", text)
            self.assertIn("why:", text)
            self.assertIn("options:", text)
            self.assertIn("impact:", text)
            self.assertIn("assumptions:", text)
            self.assertIn("missing_data:", text)
            self.assertIn("reuse_trigger:", text)

    def test_recall_unclear_query_asks_for_clarification(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp) / "fake-vault"
            (vault / "decisions").mkdir(parents=True)

            with redirect_stdout(StringIO()) as output:
                code = cmd_recall(vault, ["Can", "we", "do", "this", "thing", "soon?"])

            text = output.getvalue()
            self.assertEqual(code, 0)
            self.assertIn("route: needs-clarification", text)
            self.assertIn("clarification: What decision are you trying to reuse?", text)
            self.assertIn("No route applied until the question is clarified.", text)

    def test_rank_decisions_prioritizes_exact_route_phrase(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            incidental = root / "2026-05-03-post-frame.md"
            incidental.write_text(
                """---
id: 2026-05-03-post-frame
title: The Post Should Frame The Build As Decision
status: active
privacy_level: public-fixture
---
# Decision

The post should frame the build as decision memory, not note search.

## Tradeoff Accepted

Narrower technical scope, stronger product point of view.
""",
                encoding="utf-8",
            )
            semantic = root / "2026-05-03-adding-semantic-search-in-milestone-1.md"
            semantic.write_text(
                """---
id: 2026-05-03-adding-semantic-search-in-milestone-1
title: Adding Semantic Search In Milestone 1
status: active
privacy_level: public-fixture
---
# Decision

We are not adding semantic search in Milestone 1.

## Tradeoff Accepted

Keyword recall may miss fuzzy matches, but debugging stays simple.
""",
                encoding="utf-8",
            )

            ranked = rank_decisions("should semantic search stay out of scope", [incidental, semantic])

            self.assertEqual(ranked[0][1].path.stem, "2026-05-03-adding-semantic-search-in-milestone-1")

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
