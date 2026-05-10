import argparse
import re
import shutil
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


SIGNALS = [
    "decided",
    "chose",
    "rejected",
    "we will",
    "we are not",
    "tradeoff",
    "blocked until",
    "revisit when",
    "do not reopen",
    "proof",
    "privacy boundary",
]

REQUIRED_PROMOTION_SECTIONS = [
    "Decision",
    "Why",
    "Rejected Alternative",
    "Tradeoff",
    "Reuse For",
    "Status",
    "Privacy",
    "Reopen When",
]

REQUIRED_DURABLE_FIELDS = [
    "id",
    "title",
    "date",
    "status",
    "area",
    "project",
    "privacy_level",
    "decision_type",
    "reuse_for",
    "source",
    "confidence",
]

STOP_TERMS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "if",
    "in",
    "is",
    "it",
    "no",
    "not",
    "of",
    "on",
    "or",
    "the",
    "to",
    "we",
    "what",
    "with",
}


@dataclass
class ParsedMarkdown:
    path: Path
    frontmatter: Dict[str, str]
    body: str


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="decision-memory",
        description="Decision Memory Router POC",
        add_help=False,
    )
    parser.add_argument("command", nargs="?")
    parser.add_argument("args", nargs="*")
    parser.add_argument("--vault", default="fake-vault")
    parser.add_argument("-h", "--help", action="store_true")
    ns = parser.parse_args(argv)

    if ns.help or not ns.command:
        print_help()
        return 0

    vault = Path(ns.vault)
    try:
        if ns.command == "ingest":
            return cmd_ingest(vault, ns.args)
        if ns.command == "inbox":
            return cmd_inbox(vault)
        if ns.command == "promote":
            return cmd_promote(vault, ns.args)
        if ns.command == "recall":
            return cmd_recall(vault, ns.args)
        if ns.command == "review":
            return cmd_review(vault)
        if ns.command == "eval":
            return cmd_eval(vault, ns.args)
        if ns.command == "capture":
            print("Manual capture is a fallback in this POC.")
            print("Next step: create a candidate file in fake-vault/decision-inbox/ and run promote.")
            return 0
        print(f"Unknown command: {ns.command}")
        print("Next step: run python -m decision_memory")
        return 2
    except DecisionMemoryError as exc:
        print(str(exc))
        return exc.code
    except Exception as exc:  # visible failure, not silent
        print("Command failed.")
        print(f"Reason: {exc}")
        print("Next step: check the file path and rerun the command.")
        return 1


class DecisionMemoryError(Exception):
    def __init__(self, message: str, code: int = 1):
        super().__init__(message)
        self.code = code


def print_help() -> None:
    print(
        """Decision Memory

Use:
  python -m decision_memory ingest <file>     Find candidate decisions in a note/context file
  python -m decision_memory inbox             Review candidate decisions
  python -m decision_memory promote <file>    Promote candidate to durable decision
  python -m decision_memory recall "<query>"  Find decisions for current work
  python -m decision_memory review            Check active/stale/unresolved decisions
  python -m decision_memory eval              Run fixture query eval
  python -m decision_memory capture           Manual fallback

Fallback:
  open fake-vault/decision-inbox/
  open fake-vault/decisions/
  rg "<term>" fake-vault/
"""
    )


def cmd_ingest(vault: Path, args: List[str]) -> int:
    if not args:
        raise DecisionMemoryError(
            "No input file provided.\nNext step: python -m decision_memory ingest fake-vault/daily/2026-05-03.md",
            2,
        )
    source = Path(args[0])
    if not source.exists():
        raise DecisionMemoryError(f"Input file not found: {source}\nNext step: check the path and rerun ingest.", 2)

    text = source.read_text(encoding="utf-8")
    candidates = extract_candidates(text, source)
    privacy_level = infer_privacy_level(vault)
    inbox = vault / "decision-inbox"
    inbox.mkdir(parents=True, exist_ok=True)

    created = []
    skipped = 0
    for candidate in candidates:
        out = inbox / f"{candidate['id']}.md"
        if candidate_already_recorded(vault, candidate["id"]):
            skipped += 1
            continue
        candidate["privacy_level"] = privacy_level
        out.write_text(render_candidate(candidate), encoding="utf-8")
        created.append(out)

    if created:
        print("Ingest complete:")
        print(f"  input: {source}")
        print(f"  candidates created: {len(created)}")
        print(f"  inbox: {inbox}")
        for path in created:
            print(f"  - {path}")
        return 0

    if skipped:
        print("No new candidate decisions found.")
        print("Inputs checked:")
        print(f"  input file: {source}")
        print(f"  source type: {infer_source(source)}")
        print(f"  already recorded: {skipped}")
        print("Next step: run recall or review if you need existing decisions.")
        return 0

    print("No candidate decisions found.")
    print("Inputs checked:")
    print(f"  input file: {source}")
    print("  decision language: checked")
    print("Next step: run recall or create a manual candidate if a decision was missed.")
    return 0


def candidate_already_recorded(vault: Path, candidate_id: str) -> bool:
    inbox = vault / "decision-inbox"
    decisions = vault / "decisions"
    return any(
        path.exists()
        for path in (
            inbox / f"{candidate_id}.md",
            inbox / f"{candidate_id}.promoted.md",
            decisions / f"{candidate_id}.md",
        )
    )


def infer_privacy_level(vault: Path) -> str:
    if vault.name == "fake-vault":
        return "public-fixture"
    return "private-local"


def cmd_inbox(vault: Path) -> int:
    inbox = vault / "decision-inbox"
    candidates = pending_candidates(inbox)
    if not candidates:
        print("Decision inbox is empty.")
        print(f"Checked: {inbox}")
        return 0

    print("Candidate decisions:")
    for idx, path in enumerate(candidates, 1):
        parsed = parse_markdown(path)
        missing = missing_promotion_sections(parsed.body)
        print(f"\n{idx}. {parsed.frontmatter.get('title', path.stem)} - {parsed.frontmatter.get('source', 'unknown')}")
        print(f"   file: {path}")
        print(f"   privacy: {parsed.frontmatter.get('privacy_level', 'missing')}")
        print(f"   missing: {', '.join(missing) if missing else 'none'}")
        print(f"   suggested action: {'promote' if not missing else 'keep'}")
    return 0


def cmd_promote(vault: Path, args: List[str]) -> int:
    if not args:
        raise DecisionMemoryError(
            "No candidate file provided.\nNext step: python -m decision_memory promote fake-vault/decision-inbox/<file>.md",
            2,
        )
    candidate_path = Path(args[0])
    if not candidate_path.exists():
        raise DecisionMemoryError(f"Candidate file not found: {candidate_path}", 2)

    parsed = parse_markdown(candidate_path)
    missing = missing_promotion_sections(parsed.body)
    privacy = parsed.frontmatter.get("privacy_level", "")
    if privacy != "public-fixture":
        missing.append("privacy_level: public-fixture")

    if missing:
        print("Decision not promoted.")
        print(f"Candidate: {candidate_path}")
        print(f"Missing: {', '.join(missing)}")
        print("Next step: complete the candidate or leave it in decision-inbox/.")
        return 1

    decisions = vault / "decisions"
    decisions.mkdir(parents=True, exist_ok=True)
    out = decisions / candidate_path.name
    if out.exists():
        raise DecisionMemoryError(
            f"Decision already exists: {out}\nNo file written.\nNext step: rename the candidate or review the existing decision.",
            1,
        )

    durable = render_durable(parsed)
    out.write_text(durable, encoding="utf-8")
    archive = candidate_path.with_suffix(".promoted.md")
    shutil.move(str(candidate_path), str(archive))

    print("Decision promoted:")
    print(f"  from: {candidate_path}")
    print(f"  to: {out}")
    print(f"  archived candidate: {archive}")
    print(f"  status: {parse_markdown(out).frontmatter.get('status', 'active')}")
    print(f"  privacy: {privacy}")
    return 0


def cmd_recall(vault: Path, args: List[str]) -> int:
    if not args:
        raise DecisionMemoryError(
            'No query provided.\nNext step: python -m decision_memory recall "content proof"',
            2,
        )
    query = " ".join(args)
    decisions = list((vault / "decisions").glob("*.md")) if (vault / "decisions").exists() else []
    ranked = rank_decisions(query, decisions)
    if not ranked:
        print("No decisions matched.")
        print(f'Fallback: try broader terms or run rg "{query}" {vault}/')
        return 0

    print("Relevant decisions:")
    for idx, (score, parsed) in enumerate(ranked[:3], 1):
        warning = status_warning(parsed.frontmatter.get("status", ""))
        print(f"\n{idx}. {parsed.frontmatter.get('title', parsed.path.stem)} - {parsed.frontmatter.get('status', 'missing')} - matched score {score}")
        print(f"   file: {parsed.path}")
        print(f"   privacy: {parsed.frontmatter.get('privacy_level', 'missing')}")
        print(f"   decision: {section(parsed.body, 'Decision')[:160]}")
        print(f"   tradeoff: {section(parsed.body, 'Tradeoff Accepted')[:160]}")
        print(f"   reuse_for: {parsed.frontmatter.get('reuse_for', 'missing')}")
        if warning:
            print(f"   warning: {warning}")
    return 0


def cmd_review(vault: Path) -> int:
    inbox = pending_candidates(vault / "decision-inbox")
    decisions = [parse_markdown(path) for path in (vault / "decisions").glob("*.md")] if (vault / "decisions").exists() else []
    needs_review = [d for d in decisions if d.frontmatter.get("status") == "needs-review"]
    missing_review = [d for d in decisions if d.frontmatter.get("status") == "active" and not d.frontmatter.get("review_trigger")]
    superseded_missing = [d for d in decisions if d.frontmatter.get("status") == "superseded" and not d.frontmatter.get("supersedes")]

    print("Review complete:")
    print(f"  candidates: {len(inbox)}")
    print(f"  needs-review: {len(needs_review)}")
    print(f"  active missing review trigger: {len(missing_review)}")
    print(f"  superseded missing successor: {len(superseded_missing)}")
    if inbox:
        print("Next step: run python -m decision_memory inbox")
    return 0


def cmd_eval(vault: Path, args: List[str]) -> int:
    query_path = Path(args[0]) if args else vault / "fixtures" / "queries.yml"
    if not query_path.exists():
        raise DecisionMemoryError(
            f"Eval file not found: {query_path}\nNext step: create fake-vault/fixtures/queries.yml or pass a query file path.",
            2,
        )
    cases = parse_query_file(query_path)
    if not cases:
        raise DecisionMemoryError(f"No eval cases found in: {query_path}", 1)

    decisions = list((vault / "decisions").glob("*.md")) if (vault / "decisions").exists() else []
    passed = 0
    print("Decision memory eval:")
    print(f"  cases: {len(cases)}")
    print(f"  decisions indexed: {len(decisions)}")
    for case in cases:
        ranked = rank_decisions(case["query"], decisions)
        top_ids = [parsed.path.stem for _, parsed in ranked[:3]]
        expected = case["expected"]
        matched = [item for item in expected if item in top_ids]
        ok = bool(matched)
        if ok:
            passed += 1
        print(f"\n- query: {case['query']}")
        print(f"  expected: {', '.join(expected)}")
        print(f"  top3: {', '.join(top_ids) if top_ids else 'none'}")
        print(f"  result: {'PASS' if ok else 'FAIL'}")

    print("\nEval complete:")
    print(f"  passed: {passed}/{len(cases)}")
    if passed != len(cases):
        print("Next step: promote expected decisions or improve recall matching.")
        return 1
    return 0


def extract_candidates(text: str, source: Path) -> List[Dict[str, str]]:
    blocks = [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]
    candidates = []
    for block in blocks:
        lower = block.lower()
        if not any(signal in lower for signal in SIGNALS):
            continue
        decision = find_labeled(block, "Decision") or first_sentence(block)
        title = slug_title(decision)
        day = find_date(text) or str(date.today())
        candidate_id = f"{day}-{slugify(title)}"
        candidates.append(
            {
                "id": candidate_id,
                "title": title,
                "date": day,
                "source": infer_source(source),
                "source_file": str(source),
                "privacy_level": "public-fixture",
                "decision_type": infer_type(block),
                "reuse_for": infer_reuse(block),
                "confidence": "medium",
                "decision": decision,
                "why": find_labeled(block, "Why"),
                "rejected": find_labeled(block, "Rejected"),
                "tradeoff": find_labeled(block, "Tradeoff"),
                "reopen": find_labeled(block, "Reopen"),
                "evidence": block,
            }
        )
    return candidates


def render_candidate(candidate: Dict[str, str]) -> str:
    fm = {
        "id": candidate["id"],
        "title": candidate["title"],
        "date": candidate["date"],
        "status": "candidate",
        "source": candidate["source"],
        "source_file": candidate["source_file"],
        "privacy_level": candidate["privacy_level"],
        "decision_type": candidate["decision_type"],
        "reuse_for": candidate["reuse_for"],
        "confidence": candidate["confidence"],
    }
    missing = []
    if not candidate.get("why"):
        missing.append("Why")
    if not candidate.get("rejected"):
        missing.append("Rejected Alternative")
    if not candidate.get("tradeoff"):
        missing.append("Tradeoff")
    if not candidate.get("reopen"):
        missing.append("Reopen When")
    missing_text = "\n".join(f"- {item}" for item in missing) or "- none"
    return f"""---
{dump_frontmatter(fm)}---
# Candidate Decision: {candidate['title']}

## Decision

{candidate.get('decision') or ''}

## Why

{candidate.get('why') or ''}

## Rejected Alternative

{candidate.get('rejected') or ''}

## Tradeoff

{candidate.get('tradeoff') or ''}

## Reuse For

{candidate.get('reuse_for') or ''}

## Status

active

## Privacy

{candidate.get('privacy_level')}

## Reopen When

{candidate.get('reopen') or ''}

## Evidence

{candidate.get('evidence')}

## Missing Before Promotion

{missing_text}
"""


def render_durable(parsed: ParsedMarkdown) -> str:
    fm = dict(parsed.frontmatter)
    fm["status"] = section(parsed.body, "Status") or "active"
    fm["review_trigger"] = section(parsed.body, "Reopen When")
    fm["do_not_reopen_until"] = section(parsed.body, "Reopen When")
    body = f"""# Decision: {fm.get('title', parsed.path.stem)}

## Decision

{section(parsed.body, 'Decision')}

## Why

{section(parsed.body, 'Why')}

## Options Considered

- Chosen: {section(parsed.body, 'Decision')}
- Rejected: {section(parsed.body, 'Rejected Alternative')}

## Tradeoff Accepted

{section(parsed.body, 'Tradeoff')}

## What This Affects

- {fm.get('reuse_for', 'future work')}

## Future Use

- {section(parsed.body, 'Reuse For')}

## Related Notes

- {fm.get('source_file', '')}

## Supersedes

{fm.get('supersedes', '')}

## Review Trigger

{section(parsed.body, 'Reopen When')}
"""
    return f"---\n{dump_frontmatter(fm)}---\n{body}"


def parse_markdown(path: Path) -> ParsedMarkdown:
    text = path.read_text(encoding="utf-8")
    if text.startswith("---\n"):
        _, fm_text, body = text.split("---", 2)
        frontmatter = parse_frontmatter(fm_text)
        return ParsedMarkdown(path=path, frontmatter=frontmatter, body=body.strip())
    return ParsedMarkdown(path=path, frontmatter={}, body=text)


def parse_frontmatter(text: str) -> Dict[str, str]:
    data: Dict[str, str] = {}
    for line in text.splitlines():
        if not line.strip() or ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"')
    return data


def dump_frontmatter(data: Dict[str, str]) -> str:
    return "".join(f"{key}: {value}\n" for key, value in data.items())


def missing_promotion_sections(body: str) -> List[str]:
    return [name for name in REQUIRED_PROMOTION_SECTIONS if not section(body, name)]


def section(body: str, heading: str) -> str:
    pattern = rf"^## {re.escape(heading)}\s*\n(.*?)(?=^## |\Z)"
    match = re.search(pattern, body, flags=re.M | re.S)
    return match.group(1).strip() if match else ""


def find_labeled(block: str, label: str) -> str:
    labels = "Decision|Why|Rejected|Tradeoff|Reopen"
    match = re.search(rf"{label}\s*:\s*(.*?)(?=\s+(?:{labels})\s*:|$)", block, flags=re.I | re.S)
    return match.group(1).strip() if match else ""


def first_sentence(block: str) -> str:
    clean = " ".join(block.split())
    parts = re.split(r"(?<=[.!?])\s+", clean)
    return parts[0][:180]


def find_date(text: str) -> str:
    match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", text)
    return match.group(1) if match else ""


def slug_title(text: str) -> str:
    text = re.sub(
        r"^(we decided to|we decided|decided to|we chose|we will|we are not|decision:)\s+",
        "",
        text.strip(),
        flags=re.I,
    )
    words = re.findall(r"[A-Za-z0-9]+", text.lower())[:8]
    if len(words) >= 8:
        words = trim_trailing_fragments(words)
    return " ".join(words).title() if words else "Untitled Decision"


def slugify(text: str) -> str:
    return "-".join(re.findall(r"[a-z0-9]+", text.lower()))[:80] or "decision"


def infer_source(path: Path) -> str:
    parts = set(path.parts)
    if "daily" in parts:
        return "sync"
    if "meeting-notes" in parts:
        return "granola-note"
    if "slack-summaries" in parts:
        return "slack-summary"
    if "downloads" in parts:
        return "downloaded-context"
    if "briefs" in parts:
        return "content-session"
    if "projects" in parts:
        return "build-session"
    return "manual"


def infer_type(block: str) -> str:
    lower = block.lower()
    if "content" in lower or "brief" in lower or "post" in lower:
        return "content"
    if "privacy" in lower or "public" in lower:
        return "privacy"
    if "build" in lower or "github" in lower:
        return "build"
    if "roadmap" in lower or "strategy" in lower:
        return "strategy"
    return "product"


def infer_reuse(block: str) -> str:
    lower = block.lower()
    values = []
    if "content" in lower or "brief" in lower or "post" in lower:
        values.append("content-brief")
    if "github" in lower or "proof" in lower:
        values.append("github-proof")
    if "spec" in lower or "prd" in lower:
        values.append("prd-spec")
    if "review" in lower:
        values.append("performance-review")
    if "interview" in lower:
        values.append("interview-story")
    if not values:
        values.append("ai-session")
    return ",".join(values)


def rank_decisions(query: str, paths: Iterable[Path]) -> List[Tuple[int, ParsedMarkdown]]:
    terms = query_terms(query)
    ranked = []
    for path in paths:
        parsed = parse_markdown(path)
        haystack = (path.stem + " " + " ".join(parsed.frontmatter.values()) + " " + parsed.body).lower()
        haystack_terms = set(re.findall(r"[a-z0-9]+", haystack))
        score = sum(1 for term in terms if term in haystack_terms)
        if score:
            ranked.append((score, parsed))
    return sorted(ranked, key=lambda item: item[0], reverse=True)


def query_terms(query: str) -> set[str]:
    return {
        term
        for term in re.findall(r"[a-z0-9]+", query.lower())
        if len(term) >= 3 and term not in STOP_TERMS
    }


def pending_candidates(inbox: Path) -> List[Path]:
    if not inbox.exists():
        return []
    return sorted(path for path in inbox.glob("*.md") if not path.name.endswith(".promoted.md"))


def parse_query_file(path: Path) -> List[Dict[str, Sequence[str]]]:
    cases: List[Dict[str, Sequence[str]]] = []
    current: Dict[str, object] = {}
    expected: List[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("- query:"):
            if current:
                current["expected"] = expected
                cases.append(current)  # type: ignore[arg-type]
            current = {"query": stripped.split(":", 1)[1].strip().strip('"')}
            expected = []
        elif stripped.startswith("expected:"):
            continue
        elif stripped.startswith("- ") and current:
            expected.append(stripped[2:].strip())
    if current:
        current["expected"] = expected
        cases.append(current)  # type: ignore[arg-type]
    return cases


def trim_trailing_fragments(words: List[str]) -> List[str]:
    weak_endings = {"for", "the", "as", "in", "to", "of", "and"}
    while len(words) > 3 and words[-1] in weak_endings:
        words.pop()
    return words


def status_warning(status: str) -> str:
    if status in {"superseded", "reversed", "parked", "needs-review", "private-local"}:
        return f"status is {status}; verify before reuse"
    return ""
