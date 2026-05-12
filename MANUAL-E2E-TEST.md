# Manual End-to-End Test: Decision Memory Router

This checklist proves the full product loop:

```text
source context -> candidate decision -> promoted decision -> recall -> reuse in a future task
```

The test is not complete until a recalled decision changes a later task.

## Test Rules

- Use fake vault first.
- Do not point this repo at the full real vault.
- Do not promote real/private decisions in this public package.
- Stop if any command writes somewhere unexpected.
- Every command should print a clear receipt.

## Baseline Fake-Vault Test

Run from the repo root.

### 1. Confirm the command is discoverable

```bash
python3 -m decision_memory
```

Pass if help text prints, commands are visible, fallback paths are visible, and no error appears.

### 2. Confirm tests pass

```bash
python3 -m unittest discover -s tests
```

Pass if:

```text
Ran 10 tests
OK
```

### 3. Confirm eval passes

```bash
python3 -m decision_memory eval
```

Pass if:

```text
Eval complete:
  passed: 3/3
```

### 4. Confirm review is clean

```bash
python3 -m decision_memory review
```

Pass if:

```text
candidates: 0
```

This means the fixture decisions are already durable and there are no pending inbox items.

## Entry Point Coverage

Each command should print a receipt and should not fail silently.

```bash
python3 -m decision_memory ingest fake-vault/daily/2026-05-03.md
python3 -m decision_memory ingest fake-vault/meeting-notes/2026-05-03-product-review.md
python3 -m decision_memory ingest fake-vault/slack-summaries/2026-05-03-followup.md
python3 -m decision_memory ingest fake-vault/downloads/weekend-context-file.md
python3 -m decision_memory ingest fake-vault/briefs/2026-05-03-content-session.md
python3 -m decision_memory inbox
```

Pass if each command prints either a new candidate receipt, a clear no-new-candidates receipt, or an empty inbox receipt.

## Loud Failure Tests

These intentionally run bad commands. They should fail clearly and safely.

```bash
python3 -m decision_memory ingest fake-vault/missing.md
python3 -m decision_memory promote fake-vault/decision-inbox/missing.md
python3 -m decision_memory recall "zzzz-no-match"
python3 -m decision_memory eval fake-vault/fixtures/missing.yml
```

Pass if each command names the missing input or no-match condition, gives a next step, and does not create unexpected files.

## Reuse Test

Pretend you are about to write a README or content brief about public proof.

```bash
python3 -m decision_memory recall "private vault public proof"
```

Pass if the output returns decisions like:

- `Fake Fixtures For Public Proof`
- `Keep The Real Vault Private Local And Use`
- `Block Content Until Build Proof Exists`

Then write:

```text
Future task:
I am writing a README or LinkedIn post about the Decision Memory Router.

Reused decision:
[paste one recalled decision title]

How it changes the task:
[write one sentence explaining what this decision prevents, clarifies, or constrains]
```

Pass if the recalled decision changes the task in a concrete way.

Examples:

- It prevents using real vault data in GitHub proof.
- It blocks content claims that the tool works on the real vault.
- It reminds you that semantic search is intentionally out of scope.
- It gives the README a clearer privacy boundary.

Fail if the recalled decision is interesting but does not change the task.

## ROI Pass/Fail

The end-to-end test passes only if:

- fake-vault eval passes
- recall returns a relevant durable decision
- the decision is reused in a future task
- reuse creates measurable value

Minimum ROI threshold for the public proof package:

```text
1 recalled fixture decision -> 1 reused fake future task -> 1 artifact improved
```

If that does not happen, the public package proves capture but not reuse.
