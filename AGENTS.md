# Repository agent instructions

This legacy/default branch is not the working branch for coding agents.

Claude Code, Codex Cloud, and other coding agents must:

1. Switch to `main` before editing.
2. Sync the latest `main`.
3. Read and follow `AGENTS.md` from `main` as the authoritative agent contract, including the QLNet evolution trailers/hooks.
4. Work directly on `main`, run relevant validation, commit, and push `main` without a pull request unless the owner explicitly requests a different workflow.
5. Never modify `develop` as part of normal agent work.

Security, production approvals, CI/readiness semantics, evolution documentation, and non-destructive Git rules from `main/AGENTS.md` remain mandatory.

<!-- COEVOL-MODULE-CONTRACT-V1:BEGIN -->
## Versioned replaceable-module contract

Every external provider, repository subsystem, and internal component is a replaceable module behind a versioned contract.

- Depend on contracts, never directly on provider implementations.
- Keep provider-specific behavior behind adapters.
- Declare provided and required interfaces, implementation status, parameters, exposed calls, dependencies, compatibility, and a concise internal design summary in `module.yaml`.
- Update `module.yaml`, interface documentation, implementation evidence, and relevant contract tests in the same commit whenever code changes those facts.
- A change is incomplete when implementation, tests, documentation, and the module catalog disagree.
- Breaking changes require a new contract version plus an explicit migration and rollback path.
- Keep dependency and call metadata explicit so repository-wide and internal graphs can be generated automatically.
- Never place secret values in the repository or module catalog.

The same boundary rule applies inside the repository: internal components communicate through explicit, testable interfaces.
<!-- COEVOL-MODULE-CONTRACT-V1:END -->
