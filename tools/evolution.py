#!/usr/bin/env python3
"""Generate and validate deterministic repository-evolution records.

The tool intentionally uses only the Python standard library and Git.  A
meaningful source commit declares intent through Git trailers.  The generator
then writes one immutable Markdown record per source commit and rebuilds the
machine-managed blocks in PROJECT_EVOLUTION.md.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re
import subprocess
import sys
from collections.abc import Iterable, Sequence


ROOT_DOCUMENT = "PROJECT_EVOLUTION.md"
EVENT_DIRECTORY = pathlib.Path("evolution/commits")
EVENT_START = "<!-- evolution:event:start -->"
EVENT_END = "<!-- evolution:event:end -->"
AUTO_TRAILER = "evolution-auto"

ALLOWED_TYPES = {
    "planned",
    "started",
    "expected",
    "done",
    "fixed",
    "decision",
    "rollout",
    "rollback",
    "verified",
    "blocked",
    "unblocked",
    "superseded",
}

REQUIRED_TRAILERS = (
    "evolution-type",
    "evolution-refs",
    "evolution-expected",
    "evolution-why",
    "evolution-rollout",
    "evolution-rollback",
    "evolution-next",
)

REQUIRED_HEADINGS = (
    "## Start Here",
    "## Evolving Goal",
    "## Repository Cartography",
    "## Roadmap",
    "## Change Records",
    "## Decisions",
    "## Fix Ledger",
    "## Rollout and Rollback",
    "## Risks, Blockers, and Unknowns",
    "## Timeline",
    "## Maintenance Contract",
)

REVIEW_MARKER = re.compile(
    r"<!--\s*evolution:reviewed=(\d{4}-\d{2}-\d{2});\s*owner=([^>]+?)\s*-->"
)

EXEMPT_PREFIXES = (
    ".github/",
    ".githooks/",
    "docs/",
    "evolution/commits/",
)
EXEMPT_EXACT = {
    ROOT_DOCUMENT,
    "PORTFOLIO_EVOLUTION.md",
    "AGENTS.md",
    "EVOLUTION_MAINTENANCE.snippet.md",
    ".gitmessage-evolution.txt",
    "tools/check_repository_evolution.py",
    "tools/evolution.py",
    "tests/test_evolution_tool.py",
}
EXEMPT_SUFFIXES = (".md", ".mdx", ".rst", ".txt")

AUTO_SECTIONS = {
    "Start Here": "current",
    "Roadmap": "roadmap",
    "Change Records": "changes",
    "Fix Ledger": "fixes",
    "Rollout and Rollback": "release",
    "Timeline": "timeline",
}

STATUS_BY_TYPE = {
    "planned": "planned",
    "started": "active",
    "expected": "active",
    "done": "shipped",
    "fixed": "fixed",
    "decision": "active",
    "rollout": "active",
    "rollback": "rolled-back",
    "verified": "verified",
    "blocked": "blocked",
    "unblocked": "active",
    "superseded": "superseded",
}


class EvolutionError(RuntimeError):
    """Expected validation or generation failure."""


def git(root: pathlib.Path, *args: str, input_text: str | None = None) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        input=input_text,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise EvolutionError(result.stderr.strip() or "git command failed")
    return result.stdout


def repository_root(root: str | pathlib.Path) -> pathlib.Path:
    candidate = pathlib.Path(root).resolve()
    top = git(candidate, "rev-parse", "--show-toplevel").strip()
    return pathlib.Path(top).resolve()


def normalize_path(value: str) -> str:
    return value.strip().replace("\\", "/")


def is_meaningful_path(path: str) -> bool:
    normalized = normalize_path(path)
    if normalized in EXEMPT_EXACT:
        return False
    if normalized.startswith(EXEMPT_PREFIXES):
        return False
    return not normalized.lower().endswith(EXEMPT_SUFFIXES)


def staged_files(root: pathlib.Path) -> list[str]:
    return [
        normalize_path(line)
        for line in git(root, "diff", "--cached", "--name-only").splitlines()
        if line.strip()
    ]


def commit_files(root: pathlib.Path, sha: str) -> list[str]:
    return [
        normalize_path(line)
        for line in git(
            root,
            "diff-tree",
            "--root",
            "--no-commit-id",
            "--name-only",
            "-r",
            sha,
        ).splitlines()
        if line.strip()
    ]


def is_merge_commit(root: pathlib.Path, sha: str) -> bool:
    parents = git(root, "show", "-s", "--format=%P", sha).strip().split()
    return len(parents) > 1


def parse_trailers(message: str) -> dict[str, str]:
    parsed = git(
        pathlib.Path.cwd(),
        "interpret-trailers",
        "--parse",
        input_text=message,
    )
    trailers: dict[str, str] = {}
    for line in parsed.splitlines():
        key, separator, value = line.partition(":")
        if separator:
            trailers[key.strip().lower()] = value.strip()
    return trailers


def parse_trailers_at(root: pathlib.Path, sha: str) -> dict[str, str]:
    message = git(root, "show", "-s", "--format=%B", sha)
    parsed = git(root, "interpret-trailers", "--parse", input_text=message)
    trailers: dict[str, str] = {}
    for line in parsed.splitlines():
        key, separator, value = line.partition(":")
        if separator:
            trailers[key.strip().lower()] = value.strip()
    return trailers


def truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def validate_trailers(trailers: dict[str, str]) -> list[str]:
    if truthy(trailers.get(AUTO_TRAILER)):
        return []

    errors = [
        f"missing required trailer: {name}"
        for name in REQUIRED_TRAILERS
        if not trailers.get(name, "").strip()
    ]
    event_type = trailers.get("evolution-type", "").strip().lower()
    if event_type and event_type not in ALLOWED_TYPES:
        errors.append(
            "invalid evolution-type: "
            f"{event_type} (allowed: {', '.join(sorted(ALLOWED_TYPES))})"
        )
    if event_type == "fixed" and not trailers.get("evolution-root-cause", "").strip():
        errors.append("fixed commits require evolution-root-cause")
    if event_type == "decision" and not trailers.get("evolution-choice", "").strip():
        errors.append("decision commits require evolution-choice")
    return errors


def meaningful(files: Iterable[str]) -> bool:
    return any(is_meaningful_path(path) for path in files)


def revisions(root: pathlib.Path, range_spec: str) -> list[str]:
    return [
        line.strip()
        for line in git(root, "rev-list", "--reverse", range_spec).splitlines()
        if line.strip()
    ]


def refs_from_trailer(value: str, sha: str) -> list[str]:
    if value.strip().lower() == "auto":
        return [f"CHG-{sha[:8].upper()}"]
    refs = [item.strip() for item in value.split(",") if item.strip()]
    return refs or [f"CHG-{sha[:8].upper()}"]


def event_for_commit(
    root: pathlib.Path, sha: str, trailers: dict[str, str], files: Sequence[str]
) -> dict[str, object]:
    fields = git(
        root,
        "show",
        "-s",
        "--format=%H%x00%h%x00%aI%x00%an%x00%ae%x00%s",
        sha,
    ).rstrip("\n").split("\x00")
    if len(fields) != 6:
        raise EvolutionError(f"cannot read commit metadata for {sha}")
    full_sha, short_sha, committed_at, author, email, subject = fields
    event_type = trailers["evolution-type"].strip().lower()
    parents = git(root, "show", "-s", "--format=%P", sha).strip().split()
    return {
        "schema": 1,
        "sha": full_sha,
        "short_sha": short_sha,
        "committed_at": committed_at,
        "author": author,
        "author_email": email,
        "subject": subject,
        "parents": parents,
        "type": event_type,
        "status": STATUS_BY_TYPE[event_type],
        "refs": refs_from_trailer(trailers["evolution-refs"], full_sha),
        "expected": trailers["evolution-expected"],
        "why": trailers["evolution-why"],
        "rollout": trailers["evolution-rollout"],
        "rollback": trailers["evolution-rollback"],
        "next": trailers["evolution-next"],
        "root_cause": trailers.get("evolution-root-cause", ""),
        "choice": trailers.get("evolution-choice", ""),
        "files": list(files),
    }


def record_path(root: pathlib.Path, sha: str) -> pathlib.Path:
    return root / EVENT_DIRECTORY / f"{sha}.md"


def markdown_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def record_markdown(event: dict[str, object]) -> str:
    files = "\n".join(f"- `{path}`" for path in event["files"]) or "- none"
    refs = ", ".join(f"`{item}`" for item in event["refs"])
    extra = ""
    if event.get("root_cause"):
        extra += f"\n| Root cause | {markdown_cell(event['root_cause'])} |"
    if event.get("choice"):
        extra += f"\n| Choice | {markdown_cell(event['choice'])} |"
    encoded = json.dumps(event, ensure_ascii=False, sort_keys=True, indent=2)
    return f"""# Evolution record — `{event['short_sha']}`

| Field | Value |
|---|---|
| Source commit | `{event['sha']}` |
| Date | `{event['committed_at']}` |
| Author | {markdown_cell(event['author'])} |
| Type | `{event['type']}` |
| Status | `{event['status']}` |
| References | {refs} |
| Subject | {markdown_cell(event['subject'])} |
| Expected | {markdown_cell(event['expected'])} |
| Why | {markdown_cell(event['why'])} |
| Rollout | {markdown_cell(event['rollout'])} |
| Rollback | {markdown_cell(event['rollback'])} |
| Next | {markdown_cell(event['next'])} |{extra}

## Changed files

{files}

{EVENT_START}
```json
{encoded}
```
{EVENT_END}
"""


def load_event(path: pathlib.Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    start = text.find(EVENT_START)
    end = text.find(EVENT_END)
    if start < 0 or end < 0 or end <= start:
        raise EvolutionError(f"invalid event record markers: {path}")
    block = text[start + len(EVENT_START) : end].strip()
    if not block.startswith("```json") or not block.endswith("```"):
        raise EvolutionError(f"invalid event JSON block: {path}")
    payload = block[len("```json") : -len("```")].strip()
    event = json.loads(payload)
    if event.get("sha") != path.stem:
        raise EvolutionError(f"event SHA does not match filename: {path}")
    return event


def load_events(root: pathlib.Path) -> list[dict[str, object]]:
    directory = root / EVENT_DIRECTORY
    if not directory.exists():
        return []
    events = [load_event(path) for path in sorted(directory.glob("*.md"))]
    by_sha = {str(event["sha"]): event for event in events}
    children: dict[str, list[str]] = {sha: [] for sha in by_sha}
    indegree: dict[str, int] = {sha: 0 for sha in by_sha}
    for sha, event in by_sha.items():
        for parent in event.get("parents", []):
            parent_sha = str(parent)
            if parent_sha in by_sha:
                children[parent_sha].append(sha)
                indegree[sha] += 1
    ready = sorted(
        (sha for sha, degree in indegree.items() if degree == 0),
        key=lambda sha: (str(by_sha[sha]["committed_at"]), sha),
    )
    ordered: list[dict[str, object]] = []
    while ready:
        sha = ready.pop(0)
        ordered.append(by_sha[sha])
        for child in sorted(children[sha]):
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
                ready.sort(key=lambda item: (str(by_sha[item]["committed_at"]), item))
    if len(ordered) != len(events):
        raise EvolutionError("evolution event ancestry contains a cycle")
    return ordered


def marker(name: str, edge: str) -> str:
    return f"<!-- evolution:auto:{name}:{edge} -->"


def replace_managed_block(text: str, heading: str, name: str, content: str) -> str:
    heading_token = f"## {heading}"
    heading_at = text.find(heading_token)
    if heading_at < 0:
        raise EvolutionError(f"missing required heading: {heading_token}")
    next_heading = text.find("\n## ", heading_at + len(heading_token))
    if next_heading < 0:
        next_heading = len(text)
    start_token = marker(name, "start")
    end_token = marker(name, "end")
    start = text.find(start_token, heading_at, next_heading)
    end = text.find(end_token, heading_at, next_heading)
    block = f"{start_token}\n{content.rstrip()}\n{end_token}"
    if start >= 0 and end >= start:
        return text[:start] + block + text[end + len(end_token) :]
    insertion = "\n\n" + block + "\n"
    return text[:next_heading].rstrip() + insertion + text[next_heading:]


def event_link(event: dict[str, object]) -> str:
    return f"[record](evolution/commits/{event['sha']}.md)"


def render_blocks(events: Sequence[dict[str, object]]) -> dict[str, str]:
    if not events:
        empty = "_No automated source-commit records yet._"
        return {name: empty for name in AUTO_SECTIONS.values()}

    latest = events[-1]
    current = "\n".join(
        [
            "### Automated current state",
            "",
            "| Field | Recorded value |",
            "|---|---|",
            f"| Source | `{latest['short_sha']}` — {markdown_cell(latest['subject'])} |",
            f"| Type/status | `{latest['type']}` / `{latest['status']}` |",
            f"| Expected | {markdown_cell(latest['expected'])} |",
            f"| Next | {markdown_cell(latest['next'])} |",
            f"| Record | {event_link(latest)} |",
        ]
    )

    reference_state: dict[str, dict[str, object]] = {}
    for event in events:
        for reference in event["refs"]:
            reference_state[str(reference)] = event
    roadmap_rows = [
        f"| `{reference}` | `{event['status']}` | {markdown_cell(event['expected'])} | "
        f"`{event['short_sha']}` | {event_link(event)} |"
        for reference, event in sorted(reference_state.items())
    ]
    roadmap = "\n".join(
        [
            "### Automated reference state",
            "",
            "| Reference | Status | Expected | Last source | Evidence |",
            "|---|---|---|---|---|",
            *(roadmap_rows or ["| — | — | — | — | — |"]),
        ]
    )

    change_rows = [
        f"| `{event['short_sha']}` | `{event['type']}` | {markdown_cell(event['subject'])} | "
        f"{markdown_cell(event['why'])} | {event_link(event)} |"
        for event in events
    ]
    changes = "\n".join(
        [
            "### Automated commit records",
            "",
            "| Source | Type | Change | Why | Record |",
            "|---|---|---|---|---|",
            *change_rows,
        ]
    )

    fixed_events = [event for event in events if event["type"] == "fixed"]
    fix_rows = [
        f"| `{event['short_sha']}` | {markdown_cell(event['subject'])} | "
        f"{markdown_cell(event['root_cause'])} | {markdown_cell(event['expected'])} | "
        f"{event_link(event)} |"
        for event in fixed_events
    ]
    fixes = "\n".join(
        [
            "### Automated fixes",
            "",
            "| Source | Fix | Root cause | Expected correction | Evidence |",
            "|---|---|---|---|---|",
            *(fix_rows or ["| — | No automated fix recorded | — | — | — |"]),
        ]
    )

    release_events = [
        event for event in events if event["type"] in {"rollout", "rollback", "verified"}
    ]
    release_rows = [
        f"| `{event['short_sha']}` | `{event['type']}` | {markdown_cell(event['rollout'])} | "
        f"{markdown_cell(event['rollback'])} | {event_link(event)} |"
        for event in release_events
    ]
    release = "\n".join(
        [
            "### Automated release signals",
            "",
            "| Source | Type | Rollout | Rollback | Evidence |",
            "|---|---|---|---|---|",
            *(release_rows or ["| — | — | No automated release signal | — | — |"]),
        ]
    )

    timeline_rows = [
        f"| `{event['committed_at']}` | `{event['short_sha']}` | `{event['type']}` | "
        f"{markdown_cell(event['subject'])} | {markdown_cell(event['next'])} | {event_link(event)} |"
        for event in events
    ]
    timeline = "\n".join(
        [
            "### Automated commit timeline",
            "",
            "| Date | Source | Type | Change | Next | Evidence |",
            "|---|---|---|---|---|---|",
            *timeline_rows,
        ]
    )
    return {
        "current": current,
        "roadmap": roadmap,
        "changes": changes,
        "fixes": fixes,
        "release": release,
        "timeline": timeline,
    }


def rendered_document(root: pathlib.Path) -> str:
    document = root / ROOT_DOCUMENT
    if not document.is_file():
        raise EvolutionError(f"missing required document: {ROOT_DOCUMENT}")
    text = document.read_text(encoding="utf-8")
    blocks = render_blocks(load_events(root))
    for heading, name in AUTO_SECTIONS.items():
        text = replace_managed_block(text, heading, name, blocks[name])
    return text.rstrip() + "\n"


def render(root: pathlib.Path, check: bool) -> bool:
    document = root / ROOT_DOCUMENT
    current = document.read_text(encoding="utf-8") if document.exists() else ""
    expected = rendered_document(root)
    if current == expected:
        return False
    if check:
        raise EvolutionError(
            f"{ROOT_DOCUMENT} generated blocks are stale; run: "
            "python tools/evolution.py render"
        )
    document.write_text(expected, encoding="utf-8", newline="\n")
    return True


def generate(root: pathlib.Path, shas: Sequence[str]) -> list[pathlib.Path]:
    candidates: list[tuple[str, dict[str, str], list[str]]] = []
    failures: list[str] = []
    for sha in shas:
        if is_merge_commit(root, sha):
            continue
        files = commit_files(root, sha)
        if not meaningful(files):
            continue
        trailers = parse_trailers_at(root, sha)
        if truthy(trailers.get(AUTO_TRAILER)):
            continue
        errors = validate_trailers(trailers)
        if errors:
            failures.append(f"{sha[:12]}: " + "; ".join(errors))
            continue
        candidates.append((sha, trailers, files))
    if failures:
        raise EvolutionError("\n".join(failures))

    created: list[pathlib.Path] = []
    for sha, trailers, files in candidates:
        path = record_path(root, sha)
        if path.exists():
            continue
        event = event_for_commit(root, sha, trailers, files)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(record_markdown(event), encoding="utf-8", newline="\n")
        created.append(path)
    render(root, check=False)
    return created


def validate_document(root: pathlib.Path, max_age_days: int = 45) -> list[str]:
    errors: list[str] = []
    document = root / ROOT_DOCUMENT
    if not document.is_file():
        return [f"missing required document: {ROOT_DOCUMENT}"]
    text = document.read_text(encoding="utf-8")
    for heading in REQUIRED_HEADINGS:
        if heading not in text:
            errors.append(f"missing required heading: {heading}")
    review = REVIEW_MARKER.search(text)
    if not review:
        errors.append("missing or invalid evolution review marker")
    else:
        owner = review.group(2).strip()
        if owner in {"", "REPLACE", "TEAM-OR-PERSON"}:
            errors.append("review marker must name a real owner or team")
        try:
            reviewed = dt.date.fromisoformat(review.group(1))
            age = (dt.datetime.now(dt.timezone.utc).date() - reviewed).days
            if age < 0:
                errors.append("review marker date is in the future")
            elif age > max_age_days:
                errors.append(
                    f"document review is stale ({age} days; maximum is {max_age_days})"
                )
        except ValueError:
            errors.append("review marker date is invalid")
    try:
        render(root, check=True)
    except EvolutionError as exc:
        errors.append(str(exc))
    return errors


def validate_commits(root: pathlib.Path, shas: Sequence[str]) -> list[str]:
    errors: list[str] = []
    for sha in shas:
        if is_merge_commit(root, sha):
            continue
        files = commit_files(root, sha)
        if not meaningful(files):
            continue
        trailers = parse_trailers_at(root, sha)
        if truthy(trailers.get(AUTO_TRAILER)):
            continue
        trailer_errors = validate_trailers(trailers)
        if trailer_errors:
            errors.append(f"{sha[:12]}: " + "; ".join(trailer_errors))
            continue
        path = record_path(root, sha)
        if not path.is_file():
            errors.append(
                f"{sha[:12]}: missing {path.relative_to(root).as_posix()}; run: "
                "python tools/evolution.py generate --commit HEAD"
            )
            continue
        try:
            expected = record_markdown(event_for_commit(root, sha, trailers, files))
            actual = path.read_text(encoding="utf-8")
            if actual != expected:
                errors.append(
                    f"{sha[:12]}: {path.relative_to(root).as_posix()} was altered or is stale; "
                    f"remove it and run: python tools/evolution.py generate --commit {sha}"
                )
        except (EvolutionError, OSError, json.JSONDecodeError) as exc:
            errors.append(f"{sha[:12]}: invalid evolution record: {exc}")
    return errors


def install_hooks(root: pathlib.Path) -> None:
    hooks = root / ".githooks"
    if not hooks.is_dir():
        raise EvolutionError("missing .githooks directory")
    git(root, "config", "core.hooksPath", ".githooks")
    template = root / ".gitmessage-evolution.txt"
    if template.is_file():
        git(root, "config", "commit.template", ".gitmessage-evolution.txt")


def select_shas(root: pathlib.Path, commit: list[str] | None, range_spec: str | None) -> list[str]:
    if commit:
        return [git(root, "rev-parse", sha).strip() for sha in commit]
    if range_spec:
        return revisions(root, range_spec)
    return [git(root, "rev-parse", "HEAD").strip()]


def print_errors(errors: Sequence[str]) -> None:
    print("Repository evolution check failed:", file=sys.stderr)
    for error in errors:
        for line in str(error).splitlines():
            print(f"- {line}", file=sys.stderr)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="repository root")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser("generate")
    generate_parser.add_argument("--commit", action="append")
    generate_parser.add_argument("--range", dest="range_spec")

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--commit", action="append")
    validate_parser.add_argument("--range", dest="range_spec")
    validate_parser.add_argument("--document-only", action="store_true")
    validate_parser.add_argument("--max-age-days", type=int, default=45)

    render_parser = subparsers.add_parser("render")
    render_parser.add_argument("--check", action="store_true")

    subparsers.add_parser("install-hooks")

    message_parser = subparsers.add_parser("validate-message")
    message_parser.add_argument("--message-file", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        root = repository_root(args.root)
        if args.command == "generate":
            shas = select_shas(root, args.commit, args.range_spec)
            created = generate(root, shas)
            print(f"Repository evolution generated ({len(created)} new record(s)).")
            return 0
        if args.command == "validate":
            errors = validate_document(root, args.max_age_days)
            if not args.document_only:
                shas = select_shas(root, args.commit, args.range_spec)
                errors.extend(validate_commits(root, shas))
            if errors:
                print_errors(errors)
                return 1
            print("Repository evolution check passed.")
            return 0
        if args.command == "render":
            changed = render(root, args.check)
            print("Repository evolution render is current." if not changed else "Repository evolution rendered.")
            return 0
        if args.command == "install-hooks":
            install_hooks(root)
            print("Evolution Git hooks installed.")
            return 0
        if args.command == "validate-message":
            files = staged_files(root)
            if not meaningful(files):
                return 0
            message = pathlib.Path(args.message_file).read_text(encoding="utf-8")
            errors = validate_trailers(parse_trailers(message))
            if errors:
                print_errors(errors)
                return 1
            return 0
        raise EvolutionError(f"unknown command: {args.command}")
    except (EvolutionError, OSError, json.JSONDecodeError) as exc:
        print_errors([str(exc)])
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

