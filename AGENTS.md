# Repository agent instructions

This legacy/default branch is not the working branch for coding agents.

Claude Code, Codex Cloud, and other coding agents must:

1. Switch to `main` before editing.
2. Sync the latest `main`.
3. Read and follow `AGENTS.md` from `main` as the authoritative agent contract, including the QLNet evolution trailers/hooks.
4. Work directly on `main`, run relevant validation, commit, and push `main` without a pull request unless the owner explicitly requests a different workflow.
5. Never modify `develop` as part of normal agent work.

Security, production approvals, CI/readiness semantics, evolution documentation, and non-destructive Git rules from `main/AGENTS.md` remain mandatory.
