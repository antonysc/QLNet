#!/usr/bin/env python3
"""Validate the living repository-evolution document and its change coupling."""

from __future__ import annotations

import argparse
import datetime as dt
import pathlib
import re
import subprocess
import sys


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

EXEMPT_PREFIXES = (".github/", "docs/")
EXEMPT_EXACT = {
    "PROJECT_EVOLUTION.md",
    "PORTFOLIO_EVOLUTION.md",
    "AGENTS.md",
    "EVOLUTION_MAINTENANCE.snippet.md",
    "tools/check_repository_evolution.py",
}
EXEMPT_SUFFIXES = (".md", ".mdx", ".rst", ".txt")


def run_git(root: pathlib.Path, *args: str) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git command failed")
    return [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]


def changed_files(root: pathlib.Path, base: str | None) -> list[str]:
    if base:
        return run_git(root, "diff", "--name-only", f"{base}...HEAD")

    changed = set(run_git(root, "diff", "--name-only"))
    changed.update(run_git(root, "diff", "--cached", "--name-only"))
    changed.update(run_git(root, "ls-files", "--others", "--exclude-standard"))
    return sorted(changed)


def is_meaningful(path: str) -> bool:
    if path in EXEMPT_EXACT:
        return False
    if path.startswith(EXEMPT_PREFIXES):
        return False
    return not path.lower().endswith(EXEMPT_SUFFIXES)


def validate_document(document: pathlib.Path, max_age_days: int) -> list[str]:
    errors: list[str] = []
    if not document.is_file():
        return [f"missing required document: {document.name}"]

    text = document.read_text(encoding="utf-8")
    for heading in REQUIRED_HEADINGS:
        if heading not in text:
            errors.append(f"missing required heading: {heading}")

    marker = REVIEW_MARKER.search(text)
    if not marker:
        errors.append("missing or invalid evolution review marker")
        return errors

    owner = marker.group(2).strip()
    if owner in {"TEAM-OR-PERSON", "REPLACE", ""}:
        errors.append("review marker must name a real owner or team")

    try:
        reviewed = dt.date.fromisoformat(marker.group(1))
    except ValueError:
        errors.append("review marker date is invalid")
        return errors

    today = dt.datetime.now(dt.timezone.utc).date()
    age = (today - reviewed).days
    if age < 0:
        errors.append("review marker date is in the future")
    elif age > max_age_days:
        errors.append(
            f"document review is stale ({age} days; maximum is {max_age_days})"
        )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="repository root")
    parser.add_argument("--base", help="base commit for pull-request comparison")
    parser.add_argument("--max-age-days", type=int, default=45)
    args = parser.parse_args()

    root = pathlib.Path(args.root).resolve()
    document = root / "PROJECT_EVOLUTION.md"
    errors = validate_document(document, args.max_age_days)

    try:
        changed = changed_files(root, args.base)
    except RuntimeError as exc:
        errors.append(str(exc))
        changed = []

    meaningful = [path for path in changed if is_meaningful(path)]
    if meaningful and "PROJECT_EVOLUTION.md" not in changed:
        preview = ", ".join(meaningful[:8])
        if len(meaningful) > 8:
            preview += ", ..."
        errors.append(
            "meaningful repository changes require PROJECT_EVOLUTION.md in the "
            f"same change: {preview}"
        )

    if errors:
        print("Repository evolution check failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Repository evolution check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


