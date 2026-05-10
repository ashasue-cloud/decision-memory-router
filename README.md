# Decision Memory Router POC

This is a local, privacy-first proof of concept for a decision memory layer over an Obsidian-style vault.

Milestone 1 proves the loop on invented, public-safe fixtures. It does not claim real-vault extraction is ready.

The product decision is **sync/context-file first**, not manual capture first. Ashley already closes loops through `/sync`, meeting notes, Slack follow-ups, and downloaded context files. The POC stages candidate decisions from those source files, then promotes only confirmed decisions into durable memory.

## First Use Case

The first user is an AI PM who works across chats, meeting notes, build specs, and Obsidian. The first job is not whole-vault search. The first job is to preserve decisions so future work does not re-litigate the same tradeoffs.

## Why This Exists

AI-assisted work resets when decisions do not carry forward. Notes preserve what happened. Decisions preserve what should shape future work.

## Rejected Alternatives

| Alternative | Why rejected |
|---|---|
| Manual capture as primary workflow | Too easy to forget; does not match Ashley's real habits. |
| Real public data | Time-consuming and not shaped like Ashley's workflow. |
| Sanitized real work | Too risky for public proof. |
| Semantic search in Milestone 1 | Adds complexity before structured decisions prove value. |
| Slack, Granola, or email integrations | Too much auth/privacy surface for MVP. |

## Privacy Boundary

The fake vault uses invented public-safe data only. Do not add private, identifiable, work, family, health, or financial data.

Before publishing or extending this package, read `PRIVACY-CHECK.md` and `EXPORT-RECEIPT.md`.

## Run

From this folder:

```bash
python3 -m decision_memory
python3 -m decision_memory ingest fake-vault/daily/2026-05-03.md
python3 -m decision_memory inbox
python3 -m decision_memory promote fake-vault/decision-inbox/2026-05-03-block-content-until-build-proof-exists.md
python3 -m decision_memory recall "content proof"
python3 -m decision_memory review
python3 -m decision_memory eval
```

## Manual End-to-End Test

Use `MANUAL-E2E-TEST.md` to test the full loop:

```text
source context -> candidate decision -> promoted decision -> recall -> reuse in a future task
```

The build does not prove ROI until a recalled decision improves a later task.

## What This Proves

- Can rule-based ingest stage candidate decisions from fake source files?
- Can strict promotion prevent weak records from becoming durable memory?
- Can recall find decisions later for build/content work?
- Can review surface unpromoted candidates and stale records?
- Can a fixture eval catch whether recall returns expected decisions?

## Current Proof Output

After ingesting the fake `/sync`, meeting note, Slack summary, weekend context file, and content-session note:

```text
Review complete:
  candidates: 0
  needs-review: 0
  active missing review trigger: 0
  superseded missing successor: 0
```

Recall example:

```bash
python3 -m decision_memory recall "private vault public proof"
```

Returns:

```text
1. Fake Fixtures For Public Proof
2. Keep The Real Vault Private Local And Use
3. Block Content Until Build Proof Exists
```

Eval result:

```text
Decision memory eval:
  cases: 3
  decisions indexed: 6

Eval complete:
  passed: 3/3
```

Tests:

```text
Ran 10 tests
OK
```

## Private Trial Result

A copied private daily capture was tested outside this public package.

Result:

```text
Candidates staged: 19
Privacy: private-local
Suggested action: keep for all 19
Durable decisions created: 0
```

Conclusion: the fake-fixture loop passes, but real-shaped extraction is not proven yet. The safety boundary behaved correctly: private candidates were marked `private-local` and promotion stayed blocked.

## What Broke During Build

1. The parser initially pulled `Why:` into the decision title.

Fix: labeled fields now stop at the next label, such as `Why:`, `Rejected:`, `Tradeoff:`, or `Reopen:`.

Product lesson: extraction is not memory. Candidate decisions need review before durable promotion.

2. Promoted candidate archives were still counted as pending inbox items.

Fix: inbox/review ignore `.promoted.md` files.

Product lesson: lifecycle has to be machine-visible, not just human-visible.

3. Eval expected IDs broke after title cleanup improved filenames.

Fix: fixture expectations now match generated decision IDs.

Product lesson: eval fixtures are part of the product contract. When naming behavior changes, expected outputs should change intentionally.

4. Real-shaped private notes produced too many incomplete candidates.

Fix: no fix yet. Milestone 2 needs better section-aware extraction and confidence filtering before private reuse can be trusted.

Product lesson: staging is not success. A good memory tool should prefer fewer complete candidate decisions over many plausible fragments.

## Milestone 1 Acceptance

- No silent failures.
- Every command prints a receipt.
- No private fixture leakage.
- `promote` is strict.
- Markdown remains useful without the CLI.
- Fixture eval passes.
- Private-local candidates are not treated as public proof.

## Limitations

- Rule-based extraction only.
- Fake-fixture proof only.
- Real-vault extraction is not proven.
- No whole-vault ingestion.
- No semantic search yet.
- No Slack, email, Granola, or calendar integrations.
- ROI is not proven until a recalled decision improves a later real task.

## License

MIT.
