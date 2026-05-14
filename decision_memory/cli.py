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

LABEL_NAMES = (
    "Decision",
    "Why",
    "Rejected",
    "Tradeoff",
    "Reopen",
    "Assumptions",
    "Missing Data",
    "Missing",
)

ROUTE_RULES: Dict[str, Tuple[Tuple[str, int], ...]] = {
    "content-proof": (
        ("content proof", 4),
        ("build proof", 3),
        ("public-facing claim", 3),
        ("content", 1),
        ("post", 1),
        ("publish", 1),
        ("proof", 1),
        ("brief", 1),
        ("claim", 1),
        ("audience", 1),
        ("credibility", 1),
    ),
    "privacy-boundary": (
        ("privacy boundary", 4),
        ("private local", 4),
        ("private-local", 4),
        ("public fixture", 4),
        ("public-fixture", 4),
        ("real vault", 3),
        ("fake fixture", 3),
        ("fake fixtures", 3),
        ("public proof", 3),
        ("privacy", 2),
        ("private", 2),
        ("public", 1),
        ("fixture", 1),
        ("fixtures", 1),
        ("vault", 1),
        ("data", 1),
        ("sanitized", 1),
        ("anonymized", 1),
        ("expose", 1),
    ),
    "scope-decision": (
        ("scope decision", 4),
        ("semantic search", 4),
        ("out of scope", 4),
        ("not adding", 3),
        ("milestone", 2),
        ("defer", 2),
        ("deferred", 2),
        ("rejected", 2),
        ("roadmap", 1),
        ("strategy", 1),
        ("scope", 1),
        ("phase", 1),
        ("tradeoff", 1),
    ),
    "build-path": (
        ("build path", 4),
        ("command line", 4),
        ("github proof", 3),
        ("cli", 3),
        ("prototype", 2),
        ("implementation", 2),
        ("github", 2),
        ("router", 2),
        ("eval", 1),
        ("test", 1),
        ("build", 1),
        ("tool", 1),
        ("workflow", 1),
    ),
}

ROUTE_REASONS = {
    "content-proof": "This points to content-proof because it mentions {signals}, which usually means Ashley needs evidence for content or a public-facing claim.",
    "privacy-boundary": "This points to privacy-boundary because it mentions {signals}, which usually means the decision is about what can be public, fake, private, or exposed.",
    "scope-decision": "This points to scope-decision because it mentions {signals}, which usually means Ashley is deciding what stays in or out of the current phase.",
    "build-path": "This points to build-path because it mentions {signals}, which usually means the decision affects implementation direction or proof of build.",
}

DEFAULT_CLARIFYING_QUESTION = (
    "What decision are you trying to reuse? Add one concrete noun and choose a lane: "
    "content proof, privacy boundary, scope, or build path."
)


@dataclass
class ParsedMarkdown:
    path: Path
    frontmatter: Dict[str, str]
    body: str


@dataclass
class RouteResult:
    category: str
    reason: str
    confidence: str
    clarifying_question: str = ""


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
        candidate_confidence = parsed.frontmatter.get(
            "candidate_confidence",
            parsed.frontmatter.get("confidence", "missing"),
        )
        print(f"\n{idx}. {parsed.frontmatter.get('title', path.stem)} - {parsed.frontmatter.get('source', 'unknown')}")
        print(f"   file: {path}")
        print(f"   privacy: {parsed.frontmatter.get('privacy_level', 'missing')}")
        print(f"   candidate_confidence: {candidate_confidence}")
        print(f"   missing: {', '.join(missing) if missing else 'none'}")
        print(f"   suggested action: {candidate_action(parsed, missing)}")
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
    route = classify_route(query)
    decisions = list((vault / "decisions").glob("*.md")) if (vault / "decisions").exists() else []
    ranked = rank_decisions(query, decisions)

    print_route_result(route)
    if route.category == "needs-clarification":
        print("No route applied until the question is clarified.")
        return 0

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
        print(f"   decision: {one_line(section(parsed.body, 'Decision'), 180)}")
        print(f"   why: {one_line(section(parsed.body, 'Why'), 180)}")
        print(f"   options: {one_line(section(parsed.body, 'Options Considered'), 220)}")
        print(f"   tradeoff: {one_line(section(parsed.body, 'Tradeoff Accepted'), 180)}")
        print(f"   impact: {one_line(section(parsed.body, 'What This Affects'), 180)}")
        print(f"   assumptions: {one_line(section(parsed.body, 'Assumptions'), 180)}")
        print(f"   missing_data: {one_line(section(parsed.body, 'Missing Data'), 180)}")
        print(f"   reuse_trigger: {one_line(section(parsed.body, 'Review Trigger'), 180)}")
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
    blocks = candidate_blocks(text)
    candidates = []
    for block in blocks:
        lower = block.lower()
        if not any(signal in lower for signal in SIGNALS):
            continue
        decision = find_labeled(block, "Decision") or first_sentence(block)
        title = slug_title(decision)
        day = find_date(text) or str(date.today())
        candidate_id = f"{day}-{slugify(title)}"
        route = classify_route(block)
        why = find_labeled(block, "Why")
        rejected = find_labeled(block, "Rejected")
        tradeoff = find_labeled(block, "Tradeoff")
        reopen = find_labeled(block, "Reopen")
        assumptions = find_labeled(block, "Assumptions")
        missing_data = find_labeled(block, "Missing Data") or find_labeled(block, "Missing")
        confidence = candidate_confidence(
            decision=decision,
            why=why,
            rejected=rejected,
            tradeoff=tradeoff,
            reopen=reopen,
            assumptions=assumptions,
            missing_data=missing_data,
        )
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
                "confidence": confidence,
                "candidate_confidence": confidence,
                "route_category": route.category,
                "route_reason": route.reason,
                "route_confidence": route.confidence,
                "clarifying_question": route.clarifying_question,
                "decision": decision,
                "why": why,
                "rejected": rejected,
                "tradeoff": tradeoff,
                "reopen": reopen,
                "assumptions": assumptions,
                "missing_data": missing_data,
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
        "candidate_confidence": candidate.get("candidate_confidence", candidate["confidence"]),
        "route_category": candidate.get("route_category", "needs-clarification"),
        "route_confidence": candidate.get("route_confidence", "low"),
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

## Assumptions

{candidate.get('assumptions') or ''}

## Missing Data

{candidate.get('missing_data') or ''}

## Candidate Quality

{candidate.get('candidate_confidence') or candidate.get('confidence') or ''}

## Router Result

- route: {candidate.get('route_category') or ''}
- reason: {candidate.get('route_reason') or ''}
- confidence: {candidate.get('route_confidence') or ''}
- clarification: {candidate.get('clarifying_question') or 'none'}

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

## Assumptions

{section(parsed.body, 'Assumptions') or 'Not captured.'}

## Missing Data

{section(parsed.body, 'Missing Data') or 'Not captured.'}

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


def one_line(text: str, limit: int) -> str:
    if not text:
        return "missing"
    clean = " ".join(text.split())
    return clean[:limit]


def find_labeled(block: str, label: str) -> str:
    labels = "|".join(re.escape(name) for name in sorted(LABEL_NAMES, key=len, reverse=True))
    match = re.search(rf"{re.escape(label)}\s*:\s*(.*?)(?=\s+(?:{labels})\s*:|$)", block, flags=re.I | re.S)
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


def candidate_blocks(text: str) -> List[str]:
    decision_section = section_by_heading(text, "Decisions made") or section_by_heading(text, "Decisions")
    if decision_section:
        return bullet_blocks(decision_section)
    return [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]


def section_by_heading(text: str, heading: str) -> str:
    pattern = rf"^## {re.escape(heading)}\s*\n(.*?)(?=^## |\Z)"
    match = re.search(pattern, text, flags=re.M | re.S | re.I)
    return match.group(1).strip() if match else ""


def bullet_blocks(text: str) -> List[str]:
    blocks: List[str] = []
    current: List[str] = []
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped:
            continue
        if stripped.startswith("- "):
            if current:
                blocks.append(" ".join(current))
            current = [stripped[2:].strip()]
        elif current:
            current.append(stripped)
    if current:
        blocks.append(" ".join(current))
    if blocks:
        return blocks
    return [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]


def candidate_confidence(
    *,
    decision: str,
    why: str,
    rejected: str,
    tradeoff: str,
    reopen: str,
    assumptions: str,
    missing_data: str,
) -> str:
    if not decision:
        return "noise-risk"
    required_count = sum(bool(value) for value in (why, rejected, tradeoff, reopen))
    if required_count == 4 and assumptions and missing_data:
        return "complete"
    if required_count >= 2:
        return "partial"
    return "noise-risk"


def candidate_action(parsed: ParsedMarkdown, missing: Sequence[str]) -> str:
    privacy = parsed.frontmatter.get("privacy_level", "")
    confidence = parsed.frontmatter.get("candidate_confidence", parsed.frontmatter.get("confidence", ""))
    if privacy != "public-fixture":
        return "review-local"
    if missing or confidence != "complete":
        return "keep"
    return "promote"


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
    if "build" in lower or "phase" in lower or "prototype" in lower:
        values.append("build-session")
    if "performance review" in lower:
        values.append("performance-review")
    if "interview" in lower:
        values.append("interview-story")
    if not values:
        values.append("ai-session")
    return ",".join(values)


def classify_route(text: str) -> RouteResult:
    normalized = " ".join(text.lower().split())
    if not normalized or not query_terms(text):
        return RouteResult(
            "needs-clarification",
            "The input does not include enough route-specific language to classify.",
            "low",
            DEFAULT_CLARIFYING_QUESTION,
        )

    terms = set(re.findall(r"[a-z0-9]+", normalized))
    scores: Dict[str, int] = {}
    evidence: Dict[str, List[str]] = {}
    for category, rules in ROUTE_RULES.items():
        for signal, weight in rules:
            if route_signal_matches(signal, normalized, terms):
                scores[category] = scores.get(category, 0) + weight
                evidence.setdefault(category, []).append(signal)

    if not scores:
        return RouteResult(
            "needs-clarification",
            "The input has searchable words, but none map cleanly to a known route.",
            "low",
            DEFAULT_CLARIFYING_QUESTION,
        )

    top_score = max(scores.values())
    top_categories = [category for category, score in scores.items() if score == top_score]
    if len(top_categories) > 1:
        routes = format_route_list(top_categories)
        return RouteResult(
            "needs-clarification",
            f"The input matches {routes} with equal strength.",
            "low",
            f"Should this be routed as {routes}?",
        )

    category = top_categories[0]
    signals = format_signal_list(evidence[category])
    return RouteResult(
        category,
        ROUTE_REASONS[category].format(signals=signals),
        route_confidence(top_score),
    )


def route_signal_matches(signal: str, normalized: str, terms: set[str]) -> bool:
    if " " in signal or "-" in signal:
        return signal in normalized
    return signal in terms


def route_confidence(score: int) -> str:
    if score >= 4:
        return "high"
    if score >= 2:
        return "medium"
    return "low"


def format_signal_list(signals: Sequence[str]) -> str:
    unique = []
    for signal in signals:
        if signal not in unique:
            unique.append(signal)
    selected = unique[:3]
    if len(selected) == 1:
        return selected[0]
    if len(selected) == 2:
        return f"{selected[0]} and {selected[1]}"
    return f"{', '.join(selected[:-1])}, and {selected[-1]}"


def format_route_list(routes: Sequence[str]) -> str:
    if len(routes) == 1:
        return routes[0]
    if len(routes) == 2:
        return f"{routes[0]} or {routes[1]}"
    return f"{', '.join(routes[:-1])}, or {routes[-1]}"


def print_route_result(route: RouteResult) -> None:
    print("Router recommendation:")
    print(f"  route: {route.category}")
    print(f"  reason: {route.reason}")
    print(f"  confidence: {route.confidence}")
    if route.clarifying_question:
        print(f"  clarification: {route.clarifying_question}")


def rank_decisions(query: str, paths: Iterable[Path]) -> List[Tuple[int, ParsedMarkdown]]:
    terms = query_terms(query)
    phrases = query_phrases(query)
    route = classify_route(query)
    ranked = []
    for path in paths:
        parsed = parse_markdown(path)
        haystack = (path.stem + " " + " ".join(parsed.frontmatter.values()) + " " + parsed.body).lower()
        normalized_haystack = " ".join(haystack.split())
        haystack_terms = set(re.findall(r"[a-z0-9]+", haystack))
        score = sum(1 for term in terms if term in haystack_terms)
        score += phrase_match_score(phrases, normalized_haystack)
        score += route_match_score(route, query, normalized_haystack, haystack_terms)
        if route.category != "needs-clarification" and parsed.frontmatter.get("route_category") == route.category:
            score += 5
        if score:
            ranked.append((score, parsed))
    return sorted(ranked, key=lambda item: item[0], reverse=True)


def query_phrases(query: str) -> List[str]:
    terms = [
        term
        for term in re.findall(r"[a-z0-9]+", query.lower())
        if len(term) >= 3 and term not in STOP_TERMS
    ]
    phrases = []
    for size in (3, 2):
        for index in range(0, len(terms) - size + 1):
            phrases.append(" ".join(terms[index : index + size]))
    return phrases


def phrase_match_score(phrases: Sequence[str], normalized_haystack: str) -> int:
    score = 0
    for phrase in phrases:
        if phrase in normalized_haystack:
            score += 2 * len(phrase.split())
    return score


def route_match_score(route: RouteResult, query: str, normalized_haystack: str, haystack_terms: set[str]) -> int:
    if route.category == "needs-clarification":
        return 0

    normalized_query = " ".join(query.lower().split())
    query_term_set = set(re.findall(r"[a-z0-9]+", normalized_query))
    score = 0
    for signal, weight in ROUTE_RULES[route.category]:
        if not route_signal_matches(signal, normalized_query, query_term_set):
            continue
        if route_signal_matches(signal, normalized_haystack, haystack_terms):
            score += weight
    return score


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
    weak_endings = {"any", "before", "for", "from", "not", "the", "as", "in", "to", "of", "and"}
    while len(words) > 3 and words[-1] in weak_endings:
        words.pop()
    return words


def status_warning(status: str) -> str:
    if status in {"superseded", "reversed", "parked", "needs-review", "private-local"}:
        return f"status is {status}; verify before reuse"
    return ""
