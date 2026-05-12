# Export Receipt

Date: 2026-05-04
Source: `brand/builds/decision-memory-router-poc/`
Export: `brand/github-ready/decision-memory-router/`

## Included

- `decision_memory/` CLI source
- `fake-vault/` invented fixture vault
- `tests/` unit tests
- `README.md`
- `MANUAL-E2E-TEST.md`
- `NEXT-STEPS.md`
- `.gitignore`
- `LICENSE`

## Excluded

- Real Obsidian vault content
- Work docs, company context, roadmap details, and internal metrics
- Family, health, financial, or personal private data
- Credentials, tokens, logs, raw exports, and `.env` files

## Privacy Boundary

This package is intended for public GitHub proof. It uses fake fixtures only. Do not copy real vault notes into this folder unless they have been explicitly sanitized and allowlisted.

## Verification

Run from this folder:

```bash
python3 -m unittest discover -s tests
python3 -m decision_memory eval
python3 -m decision_memory review
```

Last verified before GitHub publication:

```text
Ran 10 tests
OK

Eval complete:
  passed: 3/3

Review complete:
  candidates: 0
  needs-review: 0
  active missing review trigger: 0
  superseded missing successor: 0
```

## Known Boundary

This is Milestone 1 fake-fixture proof. It proves the public-safe loop, not real-vault extraction or real private reuse.
