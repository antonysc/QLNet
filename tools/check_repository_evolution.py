#!/usr/bin/env python3
"""Compatibility entry point for the repository-evolution validator."""

from __future__ import annotations

import argparse

import evolution


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--base")
    parser.add_argument("--max-age-days", type=int, default=45)
    args = parser.parse_args()
    command = [
        "--root",
        args.root,
        "validate",
        "--max-age-days",
        str(args.max_age_days),
    ]
    if args.base:
        command.extend(["--range", f"{args.base}..HEAD"])
    else:
        command.append("--document-only")
    return evolution.main(command)


if __name__ == "__main__":
    raise SystemExit(main())


